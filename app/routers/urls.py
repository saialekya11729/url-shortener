from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import URLCreate, URLCreated, URLDetails
from app.services.url_service import (
    ShortCodeCollisionError,
    URLExpiredError,
    URLNotFoundError,
    create_short_url,
    get_url_details,
    resolve_redirect_url,
)


router = APIRouter()


@router.post("/api/urls", response_model=URLCreated, status_code=status.HTTP_201_CREATED)
def create_url(payload: URLCreate, request: Request, db: Session = Depends(get_db)) -> URLCreated:
    try:
        url_mapping = create_short_url(db, long_url=str(payload.long_url))
    except ShortCodeCollisionError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate a unique short URL. Please try again.",
        ) from exc

    short_url = str(request.url_for("redirect_short_url", short_code=url_mapping.short_code))
    return URLCreated(
        short_code=url_mapping.short_code,
        short_url=short_url,
        long_url=url_mapping.long_url,
        expires_at=url_mapping.expires_at,
    )


@router.get("/api/urls/{short_code}", response_model=URLDetails)
def read_url_details(short_code: str, db: Session = Depends(get_db)) -> URLDetails:
    try:
        url_mapping, expired = get_url_details(db, short_code)
    except URLNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found.") from exc

    return URLDetails(
        short_code=url_mapping.short_code,
        long_url=url_mapping.long_url,
        created_at=url_mapping.created_at,
        expires_at=url_mapping.expires_at,
        click_count=url_mapping.click_count,
        is_expired=expired,
    )


@router.get("/{short_code}", name="redirect_short_url")
def redirect_short_url(short_code: str, db: Session = Depends(get_db)) -> RedirectResponse:
    try:
        long_url = resolve_redirect_url(db, short_code)
    except URLNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found.") from exc
    except URLExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Short URL has expired.") from exc

    return RedirectResponse(url=long_url, status_code=status.HTTP_302_FOUND)

