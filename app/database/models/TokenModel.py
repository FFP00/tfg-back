from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class Token(SQLModel, table=True):

    __tablename__ = "token"

    id:         int      | None = Field(default=None, primary_key=True)
    token:      str             = Field(nullable=False, unique=True)

    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
