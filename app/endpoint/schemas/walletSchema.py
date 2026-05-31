from decimal import Decimal

from sqlmodel import SQLModel


class WalletShow(SQLModel):
    balance: Decimal | None = None


class DepositPayload(SQLModel):
    amount: Decimal
