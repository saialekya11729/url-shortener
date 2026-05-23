# URL Shortener

Anonymous URL shortener built with a Python REST API.

## MVP Decisions

- No login or user accounts.
- Users cannot choose custom short codes.
- Every short URL expires after 24 hours.
- Expired URLs are kept in the database and return `410 Gone`.
- Successful redirects increment `click_count`.

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

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the API:

```powershell
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
