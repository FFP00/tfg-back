import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.customerTitleFactory import CustomerTitleFactory
from app.database.models.CustomerModel import Customer
from app.database.models.TitleModel import Title

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_customers_titles(session: Session, count: int):
    customers = session.exec(select(Customer.id)).all()
    titles    = session.exec(select(Title.id)).all()

    if not customers:
        logger.info("No encontramos usuarios")
        return

    if not titles:
        logger.info("No encontramos juegos")
        return

    used: set[tuple[int, int]] = set()
    customer_titles = []

    while len(customer_titles) < count:
        customer = secrets.choice(customers)
        title    = secrets.choice(titles)
        if (customer, title) in used:
            continue
        used.add((customer, title))
        ct = CustomerTitleFactory.build()
        ct.customer_id = customer
        ct.title_id    = title
        customer_titles.append(ct)

    session.add_all(customer_titles)
    logger.info(f"{count} customer_title preparados.")
