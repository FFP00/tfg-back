from datetime import datetime

from sqlalchemy import Column, DateTime, LargeBinary, func
from sqlmodel import Field, SQLModel


class Media(SQLModel, table=True):
    __tablename__ = "media"

    title_id: int = Field(primary_key=True, foreign_key="title.id")

    capsule: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    header:  bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    store_1: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))

    store_2: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    store_3: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    store_4: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    store_5: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    store_6: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    trailer: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))

    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
