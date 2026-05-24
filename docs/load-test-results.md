# Load Test Results

Command:

```powershell
python load_tests/url_shortener_load_test.py --requests 1000 --concurrency 1000 --timeout 60
```

Latest local result:

```text
scenario: details
transport: asgi
requests: 1000
successes: 1000
failures: 0
concurrency: 1000
total_seconds: 1.716
requests_per_second: 582.68
p50_ms: 477.57
p95_ms: 579.27
max_ms: 591.69
```

## SQL Server Write Load Test

Command:

```powershell
$env:DATABASE_URL="mssql+pyodbc://@localhost/url_shortener?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes"
$env:DB_POOL_SIZE="100"
$env:DB_MAX_OVERFLOW="200"
python load_tests/url_shortener_load_test.py --scenario create --requests 1000 --concurrency 1000 --timeout 120
```

Latest local result:

```text
scenario: create
transport: asgi
requests: 1000
successes: 1000
failures: 0
concurrency: 1000
total_seconds: 2.395
requests_per_second: 417.58
p50_ms: 1341.37
p95_ms: 1429.63
max_ms: 1448.22
```

Notes:

- The default load test uses ASGI transport to exercise the real FastAPI routes in process.
- The default scenario seeds URLs, then runs 1,000 concurrent `GET /api/urls/{short_code}` requests.
- A write-heavy scenario is available with `--scenario create`.
- Run the write-heavy scenario with PostgreSQL:

```powershell
docker compose up -d postgres
$env:DATABASE_URL="postgresql+psycopg://urlshortener:urlshortener@localhost:5432/url_shortener"
python load_tests/url_shortener_load_test.py --scenario create --requests 1000 --concurrency 1000 --timeout 120
```

- SQLite remains the no-setup development default, but it is not intended for 1,000 simultaneous write transactions.
