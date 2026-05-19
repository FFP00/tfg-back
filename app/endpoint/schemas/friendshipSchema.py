from datetime import datetime

from sqlmodel import SQLModel


class FriendshipCreate(SQLModel):
    customer_id_1:  int
    customer_id_2:  int


class FriendshipShow(SQLModel):
    customer_id_1:  int
    customer_id_2:  int
    status:         bool

    created_at:     datetime | None = None
    updated_at:     datetime | None = None


class FriendshipPatch(SQLModel):
    status:         bool | None = None
