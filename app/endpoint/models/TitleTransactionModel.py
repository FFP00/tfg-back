from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class TitleTransaction(SQLModel, table=True):

    __tablename__ = "title_transaction"

    id:             int      | None = Field(default=None, primary_key=True)
    price:          Decimal         = Field(nullable=False, decimal_places=2, max_digits=10)
    discount:       int             = Field(nullable=False)

    title_id:       int             = Field(foreign_key="title.id", nullable=False)
    transaction_id: int             = Field(foreign_key="transaction.id", nullable=False)
    created_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
