from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

from app.database.models.CustomerModel import Customer


class Wallet(SQLModel, table=True):

    __tablename__ = "wallet"

    customer_id:    int             = Field(foreign_key="customer.id", primary_key=True, nullable=False)
    balance:        Decimal  | None = Field(default=None, nullable=True, decimal_places=2, max_digits=10)

    created_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))

    customer:       Customer | None = Relationship(sa_relationship_kwargs={"lazy": "joined"})
