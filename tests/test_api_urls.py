from datetime import UTC, datetime, timedelta

from app.models import URLMapping


def test_health_check_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_page_serves_url_shortener_ui(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "URL Shortener" in response.text
    assert "/api/urls" in response.text


def test_openapi_docs_are_available(client):
    response = client.get("/docs")

    assert response.status_code == 200
    assert "swagger" in response.text.lower()


def test_create_short_url_returns_expected_payload(client):
    response = client.post("/api/urls", json={"long_url": "https://example.com/articles/fastapi"})

    body = response.json()
    assert response.status_code == 201
    assert len(body["short_code"]) == 6
    assert body["short_code"].isalnum()
    assert body["short_url"].endswith(f"/{body['short_code']}")
    assert body["long_url"] == "https://example.com/articles/fastapi"
    assert body["expires_at"].endswith("Z")


def test_create_short_url_uses_request_host(client):
    response = client.post("/api/urls", json={"long_url": "https://example.com/host-check"})

    assert response.json()["short_url"].startswith("http://testserver/")


def test_create_short_url_sets_expiry_about_24_hours_from_creation(client):
    before = datetime.now(UTC) + timedelta(hours=23, minutes=59)
    response = client.post("/api/urls", json={"long_url": "https://example.com/expiry-window"})
    after = datetime.now(UTC) + timedelta(hours=24, minutes=1)

    expires_at = datetime.fromisoformat(response.json()["expires_at"].replace("Z", "+00:00"))
    assert before <= expires_at <= after


def test_create_short_url_rejects_invalid_url(client):
    response = client.post("/api/urls", json={"long_url": "not-a-valid-url"})

    assert response.status_code == 422


def test_create_short_url_rejects_missing_url(client):
    response = client.post("/api/urls", json={})

    assert response.status_code == 422


def test_create_short_url_rejects_non_json_body(client):
    response = client.post("/api/urls", content="long_url=https://example.com")

    assert response.status_code == 422


def test_create_short_url_allows_duplicate_long_urls_with_new_codes(client):
    first = client.post("/api/urls", json={"long_url": "https://example.com/same"})
    second = client.post("/api/urls", json={"long_url": "https://example.com/same"})

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["short_code"] != second.json()["short_code"]


def test_redirect_returns_302_to_original_url(client):
    created = client.post("/api/urls", json={"long_url": "https://example.com/docs"}).json()

    response = client.get(f"/{created['short_code']}", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/docs"


def test_redirect_increments_click_count(client):
    created = client.post("/api/urls", json={"long_url": "https://example.com/clicks"}).json()

    client.get(f"/{created['short_code']}", follow_redirects=False)
    details = client.get(f"/api/urls/{created['short_code']}").json()

    assert details["click_count"] == 1


def test_multiple_redirects_increment_click_count(client):
    created = client.post("/api/urls", json={"long_url": "https://example.com/many-clicks"}).json()

    for _ in range(3):
        client.get(f"/{created['short_code']}", follow_redirects=False)

    details = client.get(f"/api/urls/{created['short_code']}").json()
    assert details["click_count"] == 3


def test_details_do_not_increment_click_count(client):
    created = client.post("/api/urls", json={"long_url": "https://example.com/details-no-click"}).json()

    client.get(f"/api/urls/{created['short_code']}")
    client.get(f"/api/urls/{created['short_code']}")
    details = client.get(f"/api/urls/{created['short_code']}").json()

    assert details["click_count"] == 0


def test_details_returns_non_expired_metadata(client):
    created = client.post("/api/urls", json={"long_url": "https://example.com/details"}).json()

    response = client.get(f"/api/urls/{created['short_code']}")
    body = response.json()

    assert response.status_code == 200
    assert body["short_code"] == created["short_code"]
    assert body["long_url"] == "https://example.com/details"
    assert body["is_expired"] is False
    assert body["created_at"].endswith("Z")
    assert body["expires_at"].endswith("Z")


def test_unknown_redirect_returns_404(client):
    response = client.get("/missing-code", follow_redirects=False)

    assert response.status_code == 404
    assert response.json()["detail"] == "Short URL not found."


def test_unknown_details_returns_404(client):
    response = client.get("/api/urls/missing-code")

    assert response.status_code == 404
    assert response.json()["detail"] == "Short URL not found."


def test_expired_redirect_returns_410(client, db_session):
    db_session.add(
        URLMapping(
            short_code="expired",
            long_url="https://example.com/old",
            created_at=datetime.now(UTC) - timedelta(days=2),
            expires_at=datetime.now(UTC) - timedelta(days=1),
            click_count=0,
        )
    )
    db_session.commit()

    response = client.get("/expired", follow_redirects=False)

    assert response.status_code == 410
    assert response.json()["detail"] == "Short URL has expired."


def test_expired_redirect_does_not_increment_click_count(client, db_session):
    db_session.add(
        URLMapping(
            short_code="oldurl",
            long_url="https://example.com/old-click",
            created_at=datetime.now(UTC) - timedelta(days=2),
            expires_at=datetime.now(UTC) - timedelta(days=1),
            click_count=5,
        )
    )
    db_session.commit()

    client.get("/oldurl", follow_redirects=False)
    body = client.get("/api/urls/oldurl").json()

    assert body["click_count"] == 5


def test_expired_details_marks_url_as_expired(client, db_session):
    db_session.add(
        URLMapping(
            short_code="gone",
            long_url="https://example.com/gone",
            created_at=datetime.now(UTC) - timedelta(days=2),
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
            click_count=2,
        )
    )
    db_session.commit()

    response = client.get("/api/urls/gone")

    assert response.status_code == 200
    assert response.json()["is_expired"] is True


def test_health_route_is_not_captured_by_short_code_route(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

