from decimal import Decimal

from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.endpoint.models.WalletModel import Wallet

fake = Faker(['es_ES'])

class WalletFactory(SQLAlchemyFactory[Wallet]):
    __model__ = Wallet
    __set_relationships__ = False

    balance     = Use(lambda: Decimal(str(round(fake.random_number(digits=3) + fake.random.random(), 2))))

    created_at  = Use(lambda: None)
    updated_at  = Use(lambda: None)
