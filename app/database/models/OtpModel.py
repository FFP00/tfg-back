from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class Otp(SQLModel, table=True):

    __tablename__ = "otp"

    user_id:    int             = Field(primary_key=True, foreign_key="user.id", nullable=False)
    code:       str             = Field(nullable=False, max_length=4)

    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
