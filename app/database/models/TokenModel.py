from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

from app.database.models.UserModel import User


class Token(SQLModel, table=True):

    __tablename__ = "token"

    id:         int      | None = Field(default=None, primary_key=True)
    token:      str             = Field(nullable=False, unique=True, max_length=255)

    user_id:    int             = Field(foreign_key="user.id", nullable=False)

    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))

    user:       User     | None = Relationship(sa_relationship_kwargs={"lazy": "joined"})
