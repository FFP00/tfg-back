from datetime import datetime

from sqlmodel import Field, SQLModel


class Users(SQLModel, table=True):

    __tablename__ = "users"

    id:             int      | None = Field(default=None, primary_key=True)
    name:           str             = Field(nullable=False)
    lastname:       str             = Field(nullable=False)
    dni:            str             = Field(unique=True, nullable=False)
    email:          str             = Field(unique=True, nullable=False)
    password:       str             = Field(nullable=False)
    status:         bool            = Field(default=False, nullable=False)

    role_id:        int             = Field(foreign_key="roles.id", nullable=False)
    created_at:     datetime | None = Field(default=None)
    updated_at:     datetime | None = Field(default=None)
