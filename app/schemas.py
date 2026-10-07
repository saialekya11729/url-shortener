from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, HttpUrl, field_serializer


def serialize_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class URLCreate(BaseModel):
    long_url: HttpUrl


class URLCreated(BaseModel):
    short_code: str
    short_url: str
    long_url: str
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("expires_at")
    def serialize_expires_at(self, value: datetime) -> str:
        return serialize_utc(value)


class URLDetails(BaseModel):
    short_code: str
    long_url: str
    created_at: datetime
    expires_at: datetime
    click_count: int
    is_expired: bool

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "expires_at")
    def serialize_datetime_fields(self, value: datetime) -> str:
        return serialize_utc(value)

