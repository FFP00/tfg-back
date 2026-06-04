from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

from app.database.models.UserModel import User


class Customer(SQLModel, table=True):

    __tablename__ = "customer"

    user_id:    int             = Field(primary_key=True, foreign_key="user.id", nullable=False)
    status:     bool            = Field(default=True, nullable=False)

    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))

    user:       User     | None = Relationship(sa_relationship_kwargs={"lazy": "joined"})
