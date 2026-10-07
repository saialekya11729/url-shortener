from datetime import UTC, datetime, timedelta
from threading import RLock

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import URLMapping
from app.utils.code_generator import generate_short_code


DEFAULT_EXPIRY_HOURS = 24
MAX_CODE_GENERATION_ATTEMPTS = 5
_CACHE_LOCK = RLock()
_URL_CACHE: dict[str, dict[str, object]] = {}


class URLNotFoundError(Exception):
    pass


class URLExpiredError(Exception):
    pass


class ShortCodeCollisionError(Exception):
    pass


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def is_expired(url_mapping: URLMapping) -> bool:
    return ensure_aware_utc(url_mapping.expires_at) <= utc_now()


def cache_url_mapping(url_mapping: URLMapping) -> None:
    with _CACHE_LOCK:
        _URL_CACHE[url_mapping.short_code] = {
            "id": url_mapping.id,
            "short_code": url_mapping.short_code,
            "long_url": url_mapping.long_url,
            "created_at": url_mapping.created_at,
            "expires_at": url_mapping.expires_at,
            "click_count": url_mapping.click_count,
        }


def get_cached_url_mapping(short_code: str) -> URLMapping | None:
    with _CACHE_LOCK:
        cached = _URL_CACHE.get(short_code)

    if cached is None:
        return None

    return URLMapping(
        id=cached["id"],
        short_code=cached["short_code"],
        long_url=cached["long_url"],
        created_at=cached["created_at"],
        expires_at=cached["expires_at"],
        click_count=cached["click_count"],
    )


def clear_url_cache() -> None:
    with _CACHE_LOCK:
        _URL_CACHE.clear()


def create_short_url(db: Session, long_url: str) -> URLMapping:
    now = utc_now()
    expires_at = now + timedelta(hours=DEFAULT_EXPIRY_HOURS)

    for _ in range(MAX_CODE_GENERATION_ATTEMPTS):
        short_code = generate_short_code()
        url_mapping = URLMapping(
            short_code=short_code,
            long_url=long_url,
            created_at=now,
            expires_at=expires_at,
            click_count=0,
        )
        db.add(url_mapping)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue

        cache_url_mapping(url_mapping)
        return url_mapping

    raise ShortCodeCollisionError("Could not generate a unique short code.")


def get_url_by_code(db: Session, short_code: str, use_cache: bool = True) -> URLMapping:
    if use_cache:
        cached = get_cached_url_mapping(short_code)
        if cached is not None:
            return cached

    url_mapping = db.query(URLMapping).filter(URLMapping.short_code == short_code).first()
    if url_mapping is None:
        raise URLNotFoundError("Short URL was not found.")
    cache_url_mapping(url_mapping)
    return url_mapping


def get_url_details(db: Session, short_code: str) -> tuple[URLMapping, bool]:
    url_mapping = get_url_by_code(db, short_code)
    return url_mapping, is_expired(url_mapping)


def resolve_redirect_url(db: Session, short_code: str) -> str:
    url_mapping = get_url_by_code(db, short_code, use_cache=False)
    if is_expired(url_mapping):
        raise URLExpiredError("Short URL has expired.")

    url_mapping.click_count += 1
    db.commit()
    cache_url_mapping(url_mapping)
    return url_mapping.long_url
