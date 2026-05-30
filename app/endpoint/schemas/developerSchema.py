from datetime import datetime

from sqlmodel import SQLModel

from app.endpoint.schemas.imageSchema import ImageShow


class DeveloperCreate(SQLModel):
    name:           str
    email:          str
    support_email:  str
    password:       str
    website_url:    str | None = None
    image_id:       int


class DeveloperShow(SQLModel):
    id:             int | None = None
    name:           str
    email:          str
    support_email:  str
    website_url:    str | None = None
    status:         bool

    image:          ImageShow | None = None
    created_at:     datetime  | None = None
    updated_at:     datetime  | None = None


class DeveloperPatch(SQLModel):
    name:           str  | None = None
    email:          str  | None = None
    support_email:  str  | None = None
    password:       str  | None = None
    website_url:    str  | None = None
    image_id:       int  | None = None
