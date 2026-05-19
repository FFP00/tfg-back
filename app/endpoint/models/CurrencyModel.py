from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class Currency(SQLModel, table=True):

    __tablename__ = "currency"

    id:             int      | None = Field(default=None, primary_key=True)
    name:           str             = Field(unique=True, nullable=False)
    code:           str             = Field(unique=True, nullable=False)

    created_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
