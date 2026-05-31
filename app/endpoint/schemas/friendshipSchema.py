from datetime import datetime
from typing import Literal

from sqlmodel import SQLModel


class FriendshipShow(SQLModel):
    status:     str
    from_name:  str      | None = None
    created_at: datetime | None = None


class FriendshipPatch(SQLModel):
    status: Literal["accepted", "rejected", "blocked"]
