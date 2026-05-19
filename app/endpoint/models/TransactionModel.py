from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

from app.endpoint.models.WalletModel import Wallet


class Transaction(SQLModel, table=True):

    __tablename__ = "transaction"

    id:                 int      | None = Field(default=None, primary_key=True)

    wallet_customer_id: int             = Field(foreign_key="wallet.customer_id", nullable=False)
    created_at:         datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:         datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))

    wallet:             Wallet   | None = Relationship(sa_relationship_kwargs={"lazy": "joined"})
