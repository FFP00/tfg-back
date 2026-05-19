import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.friendshipFactory import FriendshipFactory
from app.endpoint.models.CustomerModel import Customer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_friendships(session: Session, count: int):
    customers = session.exec(select(Customer.id)).all()

    if not customers:
        logger.info("No encontramos usuarios")
        return

    amistades_unicas = set()

    while len(amistades_unicas) < count:
        customer_1 = secrets.choice(customers)
        customer_2 = secrets.choice(customers)

        if customer_1 == customer_2:
            continue

        pequeño= min(customer_1,customer_2)
        grande = max(customer_1,customer_2)

        amistad = (pequeño,grande)

        amistades_unicas.add(amistad)


    friendships = []

    for pequeño, grande in amistades_unicas:

        friendship = FriendshipFactory.build()
        friendship.customer_id_1=pequeño
        friendship.customer_id_2=grande
        friendships.append(friendship)

    session.add_all(friendships)
    logger.info(f"{count} amistades preparados.")
