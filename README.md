# URL Shortener

Anonymous URL shortener built with a Python REST API.


## Low-Level Design

```text
app/
  main.py                  FastAPI app creation, router registration, health check
  database.py              SQLAlchemy engine, session factory, database dependency
  models.py                Database table definitions
  schemas.py               Pydantic request and response schemas
  routers/
    urls.py                HTTP endpoints and HTTP error mapping
  services/
    url_service.py         Business rules for creation, lookup, expiry, redirects
  utils/
    code_generator.py      Random short-code generation
tests/
  test_urls.py             API behavior tests
```

## Data Model

```text
urls
----
id            integer primary key
short_code    unique string
long_url      string
created_at    datetime
expires_at    datetime
click_count   integer
```

## API

### Web UI

```http
GET /
```

Serves a browser UI for entering a long URL, creating a short URL, and copying the result.

### Create a short URL

```http
POST /api/urls
Content-Type: application/json

{
  "long_url": "https://example.com/some/long/path"
}
```

Response:

```json
{
  "short_code": "aB92xK",
  "short_url": "http://localhost:8000/aB92xK",
  "long_url": "https://example.com/some/long/path",
  "expires_at": "2026-05-24T10:30:00Z"
}
```

### Redirect

```http
GET /{short_code}
```

Responses:

```text
302 Found       Redirects to original URL
404 Not Found   Short code does not exist
410 Gone        Short URL expired
```

### Get details

```http
GET /api/urls/{short_code}
```

Response:

```json
{
  "short_code": "aB92xK",
  "long_url": "https://example.com/some/long/path",
  "created_at": "2026-05-23T10:30:00Z",
  "expires_at": "2026-05-24T10:30:00Z",
  "click_count": 7,
  "is_expired": false
}
```

## Setup

Create and activate a virtual environment:

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```
pip install -r requirements.txt
```

Run the API:

```
uvicorn app.main:app --reload
```

Open Swagger docs:

```text
http://localhost:8000/docs
```

Run tests:

```powershell
pytest
```

## Test Coverage

The default test suite includes 49 Pytest unit/integration tests covering:

- URL creation and validation
- 24-hour expiry behavior
- redirect behavior and click tracking
- not-found and expired-link error handling
- service-layer collision handling
- database engine configuration
- UTC response serialization
- short-code generation
- web UI and health routes

Run it with:

```
pytest
```

## Load Testing

The repo includes an explicit high-concurrency load-test runner at:

```text
load_tests/url_shortener_load_test.py
```

Latest recorded result:

```text
Read scenario:  1,000 requests, 1,000 concurrency, 1,000 successes, 0 failures
Write scenario: 1,000 create requests, 1,000 concurrency, 1,000 successes, 0 failures
```

See `docs/load-test-results.md` for the command output.

Run the default in-process ASGI load test:

```
python load_tests/url_shortener_load_test.py --requests 1000 --concurrency 1000
```

This drives the real FastAPI routes without depending on local socket or server-process behavior.

To test a running server, start the API:

```
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

You can also stress concurrent writes explicitly:

```
python load_tests/url_shortener_load_test.py --scenario create --requests 1000 --concurrency 1000 --timeout 120
```

SQLite is the default no-setup database for local development, but it is not designed for 1,000 simultaneous writes. For the 1,000-concurrent write scenario, use a server database such as SQL Server or PostgreSQL.

### Non-Docker SQL Server Write Test

If SQL Server is installed locally, create the database:

```powershell
sqlcmd -S localhost -E -C -Q "IF DB_ID('url_shortener') IS NULL CREATE DATABASE url_shortener;"
```

Run the write-heavy load test:

```powershell
$env:DATABASE_URL="mssql+pyodbc://@localhost/url_shortener?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes"
$env:DB_POOL_SIZE="100"
$env:DB_MAX_OVERFLOW="200"
python load_tests/url_shortener_load_test.py --scenario create --requests 1000 --concurrency 1000 --timeout 120
```

Latest local SQL Server write result:

```text
scenario: create
transport: asgi
requests: 1000
successes: 1000
failures: 0
concurrency: 1000
```

