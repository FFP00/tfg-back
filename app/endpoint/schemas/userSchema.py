from datetime import datetime

from sqlmodel import SQLModel

from app.endpoint.schemas.roleSchema import RoleShow


class UserCreate(SQLModel):
    name:       str
    lastname:   str
    dni:        str
    email:      str
    password:   str


class UserShow(SQLModel):
    name:       str
    lastname:   str
    dni:        str
    email:      str
    status:     bool

    role:       RoleShow | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None



class UserPatch(SQLModel):
    name:       str | None = None
    lastname:   str | None = None
    dni:        str | None = None
    email:      str | None = None
    password:   str | None = None

    role_id:     int | None = None
