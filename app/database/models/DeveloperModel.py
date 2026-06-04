from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

from app.database.models.UserModel import User


class Developer(SQLModel, table=True):

    __tablename__ = "developer"

    user_id:        int             = Field(primary_key=True, foreign_key="user.id", nullable=False)
    support_email:  str             = Field(unique=True, nullable=False, max_length=50)
    website_url:    str      | None = Field(default=None, nullable=True, unique=True, max_length=255)
    status:         bool            = Field(default=False, nullable=False)

    created_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))

    user:           User     | None = Relationship(sa_relationship_kwargs={"lazy": "joined"})
