import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.reviewFactory import ReviewFactory
from app.endpoint.models.CustomerTitleModel import CustomerTitle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_reviews(session: Session, count: int):
    reviews = []
    customers_titles = session.exec(select(CustomerTitle.id)).all()

    if not customers_titles:
        logger.info("No encontramos customers_titles")
        return

    for _ in range(count):
        customer_title = secrets.choice(customers_titles)

        review = ReviewFactory.build()
        review.customer_title_id=customer_title
        reviews.append(review)

    session.add_all(reviews)
    logger.info(f"{count} reviews preparados.")
