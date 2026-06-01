import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.reviewFactory import NEGATIVE_REVIEWS, POSITIVE_REVIEWS, ReviewFactory
from app.database.models.CustomerTitleModel import CustomerTitle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_reviews(session: Session, count: int):
    available = list(set(session.exec(select(CustomerTitle.id)).all()))

    if not available:
        logger.info("No encontramos customers_titles")
        return

    secrets.SystemRandom().shuffle(available)
    selected = available[: min(count, len(available))]

    reviews = []
    for ct_id in selected:
        review                   = ReviewFactory.build()
        review.customer_title_id = ct_id
        review.recommends        = secrets.choice([True, False])
        review.content           = secrets.choice(
            POSITIVE_REVIEWS if review.recommends else NEGATIVE_REVIEWS
        )
        reviews.append(review)

    session.add_all(reviews)
    logger.info(f"{len(reviews)} reviews preparados.")
