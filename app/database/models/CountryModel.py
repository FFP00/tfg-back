from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

from app.database.models.CurrencyModel import Currency


class Country(SQLModel, table=True):

    __tablename__ = "country"

    id:             int      | None = Field(default=None, primary_key=True)
    name:           str             = Field(unique=True, nullable=False)
    en_name:        str             = Field(unique=True, nullable=False)
    code:           str             = Field(unique=True, nullable=False)

    currency_id:    int             = Field(foreign_key="currency.id", nullable=False)
    created_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))

    currency:       Currency | None = Relationship(sa_relationship_kwargs={"lazy": "joined"})
