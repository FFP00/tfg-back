from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DateTime, UniqueConstraint, func
from sqlmodel import Field, SQLModel


class Friendship(SQLModel, table=True):

    __tablename__ = "friendship"
    __table_args__ = (
        CheckConstraint("customer_user_id_1 < customer_user_id_2",                               name="ck_friendship_order"),
        CheckConstraint("initiator_id = customer_user_id_1 OR initiator_id = customer_user_id_2", name="ck_friendship_initiator"),
        UniqueConstraint("customer_user_id_1", "customer_user_id_2",                             name="uq_friendship_pair"),
    )

    id:                   int      | None = Field(default=None, primary_key=True)
    status:               str             = Field(default="pending", nullable=False, max_length=10)

    customer_user_id_1:   int             = Field(foreign_key="customer.user_id", nullable=False)
    customer_user_id_2:   int             = Field(foreign_key="customer.user_id", nullable=False)
    initiator_id:         int             = Field(foreign_key="customer.user_id", nullable=False)

    created_at:           datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at:           datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
