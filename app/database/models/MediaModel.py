from datetime import datetime

from sqlalchemy import Column, DateTime, LargeBinary, func
from sqlmodel import Field, SQLModel


class Media(SQLModel, table=True):
    __tablename__ = "media"

    id: int | None = Field(default=None, primary_key=True)

    capsule: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    header: bytes  = Field(sa_column=Column(LargeBinary, nullable=False))
    store_1: bytes = Field(sa_column=Column(LargeBinary, nullable=False))

    store_2: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    store_3: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    store_4: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    store_5: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    store_6: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    trailer: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))

    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
