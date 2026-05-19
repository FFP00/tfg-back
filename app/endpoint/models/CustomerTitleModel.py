from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class CustomerTitle(SQLModel, table=True):

    __tablename__ = "customer_title"

    id:             int      | None = Field(default=None, primary_key=True)
    playtime:       int      | None = Field(default=None, nullable=True)

    title_id:       int             = Field(foreign_key="title.id", nullable=False)
    customer_id:    int             = Field(foreign_key="customer.id", nullable=False)
    created_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
