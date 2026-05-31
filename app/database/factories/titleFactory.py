from decimal import Decimal

from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.database.models.TitleModel import Title

fake = Faker(['es_ES'])

class TitleFactory(SQLAlchemyFactory[Title]):
    __model__ = Title
    __set_relationships__ = False

    id              = Use(lambda: None)
    status          = Use(lambda: True)

    name            = Use(fake.unique.catch_phrase)
    actual_discount = Use(lambda: fake.random_int(min=0, max=90))
    release_date    = Use(fake.date_object)
    release_price   = Use(lambda: Decimal(str(round(fake.random_number(digits=2) + fake.random.random(), 2))))

    created_at      = Use(lambda: None)
    updated_at      = Use(lambda: None)
