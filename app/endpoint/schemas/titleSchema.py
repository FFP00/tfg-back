from datetime import date, datetime
from decimal import Decimal

from sqlmodel import SQLModel

from app.endpoint.schemas.developerSchema import DeveloperShow
from app.endpoint.schemas.mediaSchema import MediaShowLite


class TitleCreate(SQLModel):
    name:             str
    actual_discount:  int
    release_date:     date
    release_price:    Decimal
    developer_id:     int
    media_id:         int


class TitleShow(SQLModel):
    id:               int | None = None
    name:             str
    status:           bool
    actual_discount:  int
    release_date:     date
    release_price:    Decimal

    developer:        DeveloperShow | None = None
    media:            MediaShowLite | None = None
    created_at:       datetime      | None = None
    updated_at:       datetime      | None = None


class TitleStoreItem(SQLModel):
    id:               int
    name:             str
    actual_discount:  int
    release_price:    Decimal
    developer_name:   str | None = None
    media_id:         int | None = None
    genres:           list[str] = []


class TitlePatch(SQLModel):
    name:             str     | None = None
    actual_discount:  int     | None = None
    release_date:     date    | None = None
    release_price:    Decimal | None = None
    developer_id:     int     | None = None
    media_id:         int     | None = None
