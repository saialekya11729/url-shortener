from datetime import UTC, datetime

from app.schemas import URLCreated, URLDetails, serialize_utc


def test_serialize_utc_adds_z_suffix_for_aware_datetime():
    value = datetime(2026, 5, 23, 12, 0, tzinfo=UTC)

    assert serialize_utc(value) == "2026-05-23T12:00:00Z"


def test_serialize_utc_treats_naive_datetime_as_utc():
    value = datetime(2026, 5, 23, 12, 0)

    assert serialize_utc(value) == "2026-05-23T12:00:00Z"


def test_url_created_serializes_expiry_as_utc_z():
    payload = URLCreated(
        short_code="abc123",
        short_url="http://testserver/abc123",
        long_url="https://example.com",
        expires_at=datetime(2026, 5, 24, 12, 0, tzinfo=UTC),
    )

    assert payload.model_dump(mode="json")["expires_at"] == "2026-05-24T12:00:00Z"


def test_url_details_serializes_datetime_fields_as_utc_z():
    payload = URLDetails(
        short_code="abc123",
        long_url="https://example.com",
        created_at=datetime(2026, 5, 23, 12, 0, tzinfo=UTC),
        expires_at=datetime(2026, 5, 24, 12, 0, tzinfo=UTC),
        click_count=4,
        is_expired=False,
    )

    body = payload.model_dump(mode="json")
    assert body["created_at"] == "2026-05-23T12:00:00Z"
    assert body["expires_at"] == "2026-05-24T12:00:00Z"

