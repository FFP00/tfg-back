import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.customerTitleFactory import CustomerTitleFactory
from app.endpoint.models.CustomerModel import Customer
from app.endpoint.models.TitleModel import Title

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_customers_titles(session: Session, count: int):
    customer_titles = []
    customers = session.exec(select(Customer.id)).all()
    titles = session.exec(select(Title.id)).all()

    if not customers:
        logger.info("No encontramos usuarios")
        return

    if not titles:
        logger.info("No encontramos juegos")
        return

    for _ in range(count):
        customer = secrets.choice(customers)
        title = secrets.choice(titles)

        customer_title = CustomerTitleFactory.build()
        customer_title.customer_id = customer
        customer_title.title_id=title
        customer_titles.append(customer_title)

    session.add_all(customer_titles)
    logger.info(f"{count} customer_title preparados.")
