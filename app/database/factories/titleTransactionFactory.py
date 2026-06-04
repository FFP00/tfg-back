import secrets
from decimal import Decimal

from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.database.models.TitleTransactionModel import TitleTransaction

_DISCOUNTS = list(range(0, 55, 5))


class TitleTransactionFactory(SQLAlchemyFactory[TitleTransaction]):
    __model__ = TitleTransaction
    __set_relationships__ = False

    id       = Use(lambda: None)
    price    = Use(lambda: Decimal("0.00"))
    discount = Use(lambda: secrets.choice(_DISCOUNTS))

    created_at = Use(lambda: None)
    updated_at = Use(lambda: None)
