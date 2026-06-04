from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, func
from sqlmodel import Field, Relationship, SQLModel

from app.database.models.CountryModel import Country

_USER_TYPE = Enum("CUS", "DEV", "ADM", native_enum=False)


class User(SQLModel, table=True):

    __tablename__ = "user"

    id:         int      | None = Field(default=None, primary_key=True)
    name:       str             = Field(unique=True, nullable=False, max_length=50)
    email:      str             = Field(unique=True, nullable=False, max_length=50)
    password:   str             = Field(nullable=False, max_length=255)
    type:       str             = Field(sa_column=Column("type", _USER_TYPE, nullable=False))

    country_id: int             = Field(foreign_key="country.id", nullable=False)
    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))

    country:    Country  | None = Relationship(sa_relationship_kwargs={"lazy": "joined"})
