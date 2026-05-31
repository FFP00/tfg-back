from decimal import Decimal

from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.database.models.TitleTransactionModel import TitleTransaction

fake = Faker(['es_ES'])

class TitleTransactionFactory(SQLAlchemyFactory[TitleTransaction]):
    __model__ = TitleTransaction
    __set_relationships__ = False

    id          = Use(lambda: None)
    price       = Use(lambda: Decimal(str(round(fake.random_number(digits=2) + fake.random.random(), 2))))
    discount    = Use(lambda: fake.random_int(min=0, max=90))

    created_at  = Use(lambda: None)
    updated_at  = Use(lambda: None)
