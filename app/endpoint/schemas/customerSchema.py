from datetime import datetime

from sqlmodel import SQLModel

from app.endpoint.schemas.countrySchema import CountryShow
from app.endpoint.schemas.imageSchema import ImageShow


class CustomerCreate(SQLModel):
    name:           str
    email:          str
    password:       str
    country_id:     int
    image_id:       int


class CustomerShow(SQLModel):
    name:           str
    email:          str
    status:         bool

    country:        CountryShow | None = None
    image:          ImageShow   | None = None
    created_at:     datetime    | None = None
    updated_at:     datetime    | None = None


class CustomerPatch(SQLModel):
    name:           str | None = None
    email:          str | None = None
    password:       str | None = None
    country_id:     int | None = None
    image_id:       int | None = None
