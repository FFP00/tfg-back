from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.database.models.ReviewModel import Review

fake = Faker(['es_ES'])

class ReviewFactory(SQLAlchemyFactory[Review]):
    __model__ = Review
    __set_relationships__ = False

    id          = Use(lambda: None)
    content     = Use(fake.paragraph)
    votes       = Use(lambda: fake.random_int(min=0, max=1000))
    recommends  = Use(fake.boolean)
    status      = Use(lambda: False)

    created_at  = Use(lambda: None)
    updated_at  = Use(lambda: None)
