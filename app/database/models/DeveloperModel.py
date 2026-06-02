from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

from app.database.models.ImageModel import Image


class Developer(SQLModel, table=True):

    __tablename__ = "developer"

    id:             int      | None = Field(default=None, primary_key=True)
    name:           str             = Field(unique=True, nullable=False)
    email:          str             = Field(unique=True, nullable=False)
    support_email:  str             = Field(unique=True, nullable=False)
    password:       str             = Field(nullable=False)
    website_url:    str      | None = Field(default=None, nullable=True, unique=True)
    status:         bool            = Field(default=False, nullable=False)

    image_id:       int      | None = Field(default=None, foreign_key="image.id", nullable=False)
    created_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))

    image:          Image    | None = Relationship(sa_relationship_kwargs={"lazy": "joined"})
