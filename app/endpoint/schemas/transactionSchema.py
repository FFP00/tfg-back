from datetime import datetime
from decimal import Decimal

from sqlmodel import SQLModel


class PurchasePayload(SQLModel):
    titles: list[str]


class PurchasedTitleItem(SQLModel):
    name:             str
    price_paid:       Decimal
    discount_applied: int


class TransactionHistoryItem(SQLModel):
    created_at: datetime
    titles:     list[PurchasedTitleItem] = []


class PurchaseResponse(SQLModel):
    titles_purchased: int
    total_spent:      Decimal
    wallet_balance:   Decimal
