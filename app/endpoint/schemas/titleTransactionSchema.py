from decimal import Decimal

from sqlmodel import SQLModel

from app.endpoint.schemas.titleSchema import TitleShow
from app.endpoint.schemas.transactionSchema import TransactionShow


class TitleTransactionCreate(SQLModel):
    price:          Decimal
    discount:       int
    title_id:       int
    transaction_id: int


class TitleTransactionShow(SQLModel):
    price:          Decimal
    discount:       int

    title:          TitleShow       | None = None
    transaction:    TransactionShow | None = None


class TitleTransactionPatch(SQLModel):
    price:          Decimal | None = None
    discount:       int     | None = None
