from app.database import build_engine_kwargs


def test_sqlite_engine_kwargs_disable_same_thread_check():
    kwargs = build_engine_kwargs("sqlite:///./url_shortener.db")

    assert kwargs == {"connect_args": {"check_same_thread": False}}


def test_postgresql_engine_kwargs_use_connection_pool(monkeypatch):
    monkeypatch.setenv("DB_POOL_SIZE", "25")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "75")

    kwargs = build_engine_kwargs("postgresql+psycopg://user:pass@localhost:5432/url_shortener")

    assert kwargs["pool_size"] == 25
    assert kwargs["max_overflow"] == 75
    assert kwargs["pool_pre_ping"] is True
