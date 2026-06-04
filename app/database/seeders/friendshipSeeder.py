import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.friendshipFactory import FriendshipFactory
from app.database.models.CustomerModel import Customer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_friendships(session: Session, count: int) -> None:
    customers = session.exec(select(Customer.user_id)).all()

    if not customers:
        logger.info("No encontramos usuarios")
        return

    amistades_unicas: set[tuple[int, int]] = set()

    while len(amistades_unicas) < count:
        c1 = secrets.choice(customers)
        c2 = secrets.choice(customers)
        if c1 == c2:
            continue
        amistades_unicas.add((min(c1, c2), max(c1, c2)))

    friendships = []
    for pequeño, grande in amistades_unicas:
        friendship = FriendshipFactory.build()
        friendship.customer_user_id_1 = pequeño
        friendship.customer_user_id_2 = grande
        friendship.status             = "accepted"
        friendships.append(friendship)

    session.add_all(friendships)
    logger.info(f"{count} amistades preparados.")
