from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class GenreTitle(SQLModel, table=True):

    __tablename__ = "genre_title"

    id:             int      | None = Field(default=None, primary_key=True)

    title_id:       int             = Field(foreign_key="title.id", nullable=False)
    genre_id:       int             = Field(foreign_key="genre.id", nullable=False)
    created_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
