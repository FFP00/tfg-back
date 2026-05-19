from datetime import datetime

from sqlmodel import SQLModel


class ReviewCreate(SQLModel):
    content:            str  | None = None
    votes:              int  | None = None
    recommends:         bool | None = None
    customer_title_id:  int


class ReviewShow(SQLModel):
    content:            str  | None = None
    votes:              int  | None = None
    recommends:         bool | None = None
    status:             bool | None = None

    created_at:         datetime | None = None
    updated_at:         datetime | None = None


class ReviewPatch(SQLModel):
    content:            str  | None = None
    votes:              int  | None = None
    recommends:         bool | None = None
    status:             bool | None = None
