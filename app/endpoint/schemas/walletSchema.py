from datetime import datetime
from decimal import Decimal

from sqlmodel import SQLModel

from app.endpoint.schemas.customerSchema import CustomerShow


class WalletCreate(SQLModel):
    customer_id:    int
    balance:        Decimal | None = None


class WalletShow(SQLModel):
    balance:        Decimal | None = None

    customer:       CustomerShow | None = None
    created_at:     datetime     | None = None
    updated_at:     datetime     | None = None


class WalletPatch(SQLModel):
    balance:        Decimal | None = None
