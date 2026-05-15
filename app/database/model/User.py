from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

from app.database.model.Role import Role


class User(SQLModel, table=True):

    __tablename__ = "users"

    id:             int      | None = Field(default=None, primary_key=True)
    name:           str             = Field(nullable=False)
    lastname:       str             = Field(nullable=False)
    dni:            str             = Field(unique=True, nullable=False)
    email:          str             = Field(unique=True, nullable=False)
    password:       str             = Field(nullable=False)
    status:         bool            = Field(default=True, nullable=False)

    role_id:        int      | None = Field(default=None, foreign_key="roles.id", nullable=True)
    created_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:     datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False, default=None))

    role:           Role     | None = Relationship(sa_relationship_kwargs={"lazy": "joined"})
