from datetime import datetime

from sqlmodel import Field, SQLModel


class Role(SQLModel, table=True):

    __tablename__ = "roles"

    id:             int      | None = Field(default=None, primary_key=True)
    name:           str             = Field(nullable=False)

    created_at:     datetime | None = Field(default=None)
    updated_at:     datetime | None = Field(default=None)
