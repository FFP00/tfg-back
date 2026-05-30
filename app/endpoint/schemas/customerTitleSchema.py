from datetime import datetime

from sqlmodel import SQLModel

from app.endpoint.schemas.customerSchema import CustomerShow
from app.endpoint.schemas.titleSchema import TitleShow


class CustomerTitleCreate(SQLModel):
    title_id:       int
    customer_id:    int
    playtime:       int | None = None


class CustomerTitleShow(SQLModel):
    playtime:       int | None = None

    title:          TitleShow    | None = None
    customer:       CustomerShow | None = None
    created_at:     datetime     | None = None
    updated_at:     datetime     | None = None


class CustomerTitlePatch(SQLModel):
    playtime:       int | None = None
