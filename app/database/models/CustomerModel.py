from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

from app.database.models.CountryModel import Country
from app.database.models.ImageModel import Image


class Customer(SQLModel, table=True):

    __tablename__ = "customer"

    id:             int      | None = Field(default=None, primary_key=True)
    name:           str             = Field(unique=True, nullable=False)
    email:          str             = Field(unique=True, nullable=False)
    password:       str             = Field(nullable=False)
    status:         bool            = Field(default=True, nullable=False)

    country_id:     int             = Field(foreign_key="country.id", nullable=False)
    image_id:       int      | None = Field(default=None, foreign_key="image.id",   nullable=False)
    created_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))

    country:        Country  | None = Relationship(sa_relationship_kwargs={"lazy": "joined"})
    image:          Image    | None = Relationship(sa_relationship_kwargs={"lazy": "joined"})
