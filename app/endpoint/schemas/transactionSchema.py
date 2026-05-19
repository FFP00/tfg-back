from datetime import datetime

from sqlmodel import SQLModel

from app.endpoint.schemas.walletSchema import WalletShow


class TransactionCreate(SQLModel):
    wallet_customer_id: int


class TransactionShow(SQLModel):
    wallet:             WalletShow | None = None
    created_at:         datetime   | None = None
    updated_at:         datetime   | None = None


class TransactionPatch(SQLModel):
    wallet_customer_id: int | None = None
