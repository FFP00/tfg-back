from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class Image(SQLModel, table=True):

    __tablename__ = "image"

    id:             int      | None = Field(default=None, primary_key=True)
    path_256x256:   str             = Field(nullable=False)
    path_512x512:   str             = Field(nullable=False)

    created_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
