import argparse
import asyncio
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_REQUESTS = 1000
DEFAULT_CONCURRENCY = 1000


@dataclass(frozen=True)
class RequestResult:
    ok: bool
    status_code: int
    elapsed_ms: float
    error: str | None = None


async def create_short_url(client: httpx.AsyncClient, index: int) -> RequestResult:
    started = time.perf_counter()
    try:
        response = await client.post(
            "/api/urls",
            json={"long_url": f"https://example.com/load-test/{index}?q={time.time_ns()}"},
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        return RequestResult(response.status_code == 201, response.status_code, elapsed_ms)
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        return RequestResult(False, 0, elapsed_ms, str(exc))


async def fetch_url_details(client: httpx.AsyncClient, short_code: str) -> RequestResult:
    started = time.perf_counter()
    try:
        response = await client.get(f"/api/urls/{short_code}")
        elapsed_ms = (time.perf_counter() - started) * 1000
        return RequestResult(response.status_code == 200, response.status_code, elapsed_ms)
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        return RequestResult(False, 0, elapsed_ms, str(exc))


async def create_seed_codes(client: httpx.AsyncClient, count: int) -> list[str]:
    codes: list[str] = []
    for index in range(count):
        response = await client.post(
            "/api/urls",
            json={"long_url": f"https://example.com/load-seed/{index}?q={time.time_ns()}"},
        )
        response.raise_for_status()
        codes.append(response.json()["short_code"])
    return codes


async def run_load_test(
    base_url: str,
    total_requests: int,
    concurrency: int,
    timeout: float,
    scenario: str,
    transport: str,
) -> list[RequestResult]:
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    timeout_config = httpx.Timeout(timeout)
    client_kwargs: dict[str, object] = {
        "base_url": base_url,
        "limits": limits,
        "timeout": timeout_config,
    }

    if transport == "asgi":
        from app.main import app

        client_kwargs["transport"] = httpx.ASGITransport(app=app)
        client_kwargs["base_url"] = "http://loadtest.local"

    async with httpx.AsyncClient(**client_kwargs) as client:
        health = await client.get("/health")
        health.raise_for_status()

        semaphore = asyncio.Semaphore(concurrency)

        async def bounded_create(index: int) -> RequestResult:
            async with semaphore:
                return await create_short_url(client, index)

        if scenario == "create":
            return await asyncio.gather(*(bounded_create(index) for index in range(total_requests)))

        seed_codes = await create_seed_codes(client, count=50)

        async def bounded_details(index: int) -> RequestResult:
            async with semaphore:
                return await fetch_url_details(client, seed_codes[index % len(seed_codes)])

        return await asyncio.gather(*(bounded_details(index) for index in range(total_requests)))


def summarize(results: list[RequestResult], started: float, concurrency: int) -> dict[str, float | int]:
    elapsed = time.perf_counter() - started
    latencies = [result.elapsed_ms for result in results]
    successes = sum(1 for result in results if result.ok)
    failures = len(results) - successes
    return {
        "requests": len(results),
        "successes": successes,
        "failures": failures,
        "concurrency": concurrency,
        "total_seconds": round(elapsed, 3),
        "requests_per_second": round(len(results) / elapsed, 2) if elapsed else 0,
        "p50_ms": round(statistics.median(latencies), 2),
        "p95_ms": round(statistics.quantiles(latencies, n=20)[18], 2) if len(latencies) >= 20 else round(max(latencies), 2),
        "max_ms": round(max(latencies), 2),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run 1,000+ concurrent URL shortener load test requests.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=DEFAULT_REQUESTS)
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--scenario",
        choices=["details", "create"],
        default="details",
        help="details runs 1,000+ concurrent metadata reads after seeding URLs; create runs 1,000+ concurrent writes.",
    )
    parser.add_argument(
        "--transport",
        choices=["asgi", "network"],
        default="asgi",
        help="asgi runs against the FastAPI app in-process; network runs against --base-url.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.requests < 1000 or args.concurrency < 1000:
        raise SystemExit("--requests and --concurrency must both be at least 1000 for the resume load-test claim.")

    started = time.perf_counter()
    results = asyncio.run(
        run_load_test(args.base_url, args.requests, args.concurrency, args.timeout, args.scenario, args.transport)
    )
    summary = summarize(results, started, args.concurrency)

    print(f"scenario: {args.scenario}")
    print(f"transport: {args.transport}")
    for key, value in summary.items():
        print(f"{key}: {value}")

    if summary["failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
