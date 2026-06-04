from datetime import datetime

from sqlalchemy import Column, DateTime, LargeBinary, func
from sqlmodel import Field, SQLModel


class Image(SQLModel, table=True):

    __tablename__ = "image"

    user_id:    int             = Field(primary_key=True, foreign_key="user.id", nullable=False)
    profile:    bytes    | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    banner:     bytes    | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))

    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
