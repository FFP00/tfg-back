from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

from app.database.models.DeveloperModel import Developer


class Title(SQLModel, table=True):

    __tablename__ = "title"

    id:               int      | None = Field(default=None, primary_key=True)
    name:             str             = Field(unique=True, nullable=False)
    status:           bool            = Field(default=False, nullable=False)
    actual_discount:  int             = Field(nullable=False, default=0)
    release_date:     date            = Field(nullable=False)
    release_price:    Decimal         = Field(nullable=False, decimal_places=2, max_digits=10)

    developer_id:     int             = Field(foreign_key="developer.id", nullable=False)
    created_at:       datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:       datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))

    developer:        Developer | None = Relationship(sa_relationship_kwargs={"lazy": "joined"})
