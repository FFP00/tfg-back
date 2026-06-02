from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class Review(SQLModel, table=True):

    __tablename__ = "review"

    customer_title_id:  int             = Field(primary_key=True, foreign_key="customer_title.id")

    content:            str             = Field(nullable=False)
    votes:              int             = Field(default=0, nullable=False)
    recommends:         bool            = Field(nullable=False)
    status:             bool            = Field(default=False, nullable=False)
    created_at:         datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:         datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
