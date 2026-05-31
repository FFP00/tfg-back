from datetime import date, datetime
from decimal import Decimal

from fastapi import UploadFile
from sqlmodel import SQLModel

from app.endpoint.schemas.developerSchema import DeveloperPublic
from app.endpoint.schemas.genreSchema import GenreShow


class TitleCreate(SQLModel):
    name:            str
    release_date:    date
    release_price:   Decimal
    actual_discount: int = 0


class TitleCard(SQLModel):
    name:            str
    release_price:   Decimal
    actual_discount: int
    genres:          list[GenreShow] = []
    developer_name:  str | None = None


class TitleShow(SQLModel):
    name:            str
    status:          bool
    actual_discount: int
    release_date:    date
    release_price:   Decimal

    genres:          list[GenreShow]  = []
    developer:       DeveloperPublic | None = None
    created_at:      datetime        | None = None
    updated_at:      datetime        | None = None


class TitlePatch(SQLModel):
    actual_discount: int       | None = None
    genres:          list[str] | None = None


class ReviewCreate(SQLModel):
    content:    str
    recommends: bool


class ReviewShow(SQLModel):
    content:       str
    recommends:    bool
    votes:         int
    customer_name: str
    created_at:    datetime
    title_name:    str | None = None


class ReviewPatch(SQLModel):
    content:    str  | None = None
    recommends: bool | None = None


class VoteResponse(SQLModel):
    votes: int


class TitleMediaUpload(SQLModel):
    capsule: UploadFile | None = None
    header:  UploadFile | None = None
    store_1: UploadFile | None = None
    store_2: UploadFile | None = None
    store_3: UploadFile | None = None
    store_4: UploadFile | None = None
    store_5: UploadFile | None = None
    store_6: UploadFile | None = None
    trailer: UploadFile | None = None
