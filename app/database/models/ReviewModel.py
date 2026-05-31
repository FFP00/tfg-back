from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class Review(SQLModel, table=True):

    __tablename__ = "review"

    id:                 int      | None = Field(default=None, primary_key=True)
    content:            str      | None = Field(default=None, nullable=True)
    votes:              int      | None = Field(default=None, nullable=True)
    recommends:         bool     | None = Field(default=None, nullable=True)
    status:             bool     | None = Field(default=False, nullable=True)

    customer_title_id:  int             = Field(foreign_key="customer_title.id", nullable=False)
    created_at:         datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:         datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
