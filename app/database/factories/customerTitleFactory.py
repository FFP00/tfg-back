from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.database.models.CustomerTitleModel import CustomerTitle


class CustomerTitleFactory(SQLAlchemyFactory[CustomerTitle]):
    __model__ = CustomerTitle
    __set_relationships__ = False

    id                = Use(lambda: None)
    title_id          = Use(lambda: None)
    customer_user_id  = Use(lambda: None)
    playtime          = Use(lambda: 0)

    created_at        = Use(lambda: None)
    updated_at        = Use(lambda: None)
