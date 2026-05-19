from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class Friendship(SQLModel, table=True):

    __tablename__ = "friendship"

    id:             int      | None = Field(default=None, primary_key=True)
    status:         bool            = Field(nullable=False)

    customer_id_1:  int             = Field(foreign_key="customer.id", nullable=False)
    customer_id_2:  int             = Field(foreign_key="customer.id", nullable=False)
    created_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
