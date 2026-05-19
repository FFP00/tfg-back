from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class Media(SQLModel, table=True):

    __tablename__ = "media"

    id:             int      | None = Field(default=None, primary_key=True)
    path_300x450:   str             = Field(nullable=False)
    path_600x900:   str             = Field(nullable=False)

    created_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
