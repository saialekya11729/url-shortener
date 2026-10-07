from datetime import UTC, datetime, timedelta

import pytest

from app.models import URLMapping
from app.services import url_service
from app.services.url_service import (
    ShortCodeCollisionError,
    URLExpiredError,
    URLNotFoundError,
    clear_url_cache,
    create_short_url,
    ensure_aware_utc,
    get_url_by_code,
    get_url_details,
    is_expired,
    resolve_redirect_url,
)


def test_create_short_url_persists_mapping(db_session):
    mapping = create_short_url(db_session, "https://example.com/persist")

    saved = db_session.query(URLMapping).filter_by(short_code=mapping.short_code).one()
    assert saved.long_url == "https://example.com/persist"
    assert saved.click_count == 0


def test_create_short_url_sets_default_24_hour_expiry(db_session):
    before = datetime.now(UTC) + timedelta(hours=23, minutes=59)
    mapping = create_short_url(db_session, "https://example.com/expiry")
    after = datetime.now(UTC) + timedelta(hours=24, minutes=1)

    assert before <= ensure_aware_utc(mapping.expires_at) <= after


def test_create_short_url_retries_when_generated_code_exists(db_session, monkeypatch):
    db_session.add(
        URLMapping(
            short_code="taken1",
            long_url="https://example.com/existing",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            click_count=0,
        )
    )
    db_session.commit()
    codes = iter(["taken1", "fresh2"])
    monkeypatch.setattr(url_service, "generate_short_code", lambda: next(codes))

    mapping = create_short_url(db_session, "https://example.com/new")

    assert mapping.short_code == "fresh2"


def test_create_short_url_raises_after_repeated_collisions(db_session, monkeypatch):
    db_session.add(
        URLMapping(
            short_code="repeat",
            long_url="https://example.com/existing",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            click_count=0,
        )
    )
    db_session.commit()
    monkeypatch.setattr(url_service, "generate_short_code", lambda: "repeat")

    with pytest.raises(ShortCodeCollisionError):
        create_short_url(db_session, "https://example.com/new")


def test_get_url_by_code_returns_mapping(db_session):
    mapping = create_short_url(db_session, "https://example.com/lookup")

    found = get_url_by_code(db_session, mapping.short_code)

    assert found.id == mapping.id


def test_get_url_by_code_can_return_cached_mapping_after_create(db_session):
    mapping = create_short_url(db_session, "https://example.com/cached")

    found = get_url_by_code(db_session, mapping.short_code)

    assert found.short_code == mapping.short_code
    assert found.long_url == "https://example.com/cached"


def test_get_url_by_code_falls_back_to_database_when_cache_is_empty(db_session):
    mapping = create_short_url(db_session, "https://example.com/fallback")
    clear_url_cache()

    found = get_url_by_code(db_session, mapping.short_code)

    assert found.short_code == mapping.short_code


def test_get_url_by_code_raises_for_missing_code(db_session):
    with pytest.raises(URLNotFoundError):
        get_url_by_code(db_session, "missing")


def test_get_url_details_returns_mapping_and_expiry_flag(db_session):
    mapping = create_short_url(db_session, "https://example.com/details")

    found, expired = get_url_details(db_session, mapping.short_code)

    assert found.id == mapping.id
    assert expired is False


def test_resolve_redirect_url_returns_long_url(db_session):
    mapping = create_short_url(db_session, "https://example.com/redirect")

    long_url = resolve_redirect_url(db_session, mapping.short_code)

    assert long_url == "https://example.com/redirect"


def test_resolve_redirect_url_increments_click_count(db_session):
    mapping = create_short_url(db_session, "https://example.com/click")

    resolve_redirect_url(db_session, mapping.short_code)

    assert get_url_by_code(db_session, mapping.short_code).click_count == 1


def test_resolve_redirect_url_raises_for_missing_code(db_session):
    with pytest.raises(URLNotFoundError):
        resolve_redirect_url(db_session, "missing")


def test_resolve_redirect_url_raises_for_expired_code(db_session):
    db_session.add(
        URLMapping(
            short_code="expired",
            long_url="https://example.com/expired",
            created_at=datetime.now(UTC) - timedelta(days=2),
            expires_at=datetime.now(UTC) - timedelta(days=1),
            click_count=0,
        )
    )
    db_session.commit()

    with pytest.raises(URLExpiredError):
        resolve_redirect_url(db_session, "expired")


def test_is_expired_returns_false_for_future_expiry():
    mapping = URLMapping(
        short_code="future",
        long_url="https://example.com/future",
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(seconds=30),
        click_count=0,
    )

    assert is_expired(mapping) is False


def test_is_expired_returns_true_for_past_expiry():
    mapping = URLMapping(
        short_code="past",
        long_url="https://example.com/past",
        created_at=datetime.now(UTC) - timedelta(hours=2),
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
        click_count=0,
    )

    assert is_expired(mapping) is True


def test_ensure_aware_utc_preserves_aware_utc_datetime():
    value = datetime(2026, 5, 23, 10, 0, tzinfo=UTC)

    assert ensure_aware_utc(value) == value


def test_ensure_aware_utc_adds_utc_to_naive_datetime():
    value = datetime(2026, 5, 23, 10, 0)

    assert ensure_aware_utc(value).tzinfo == UTC
