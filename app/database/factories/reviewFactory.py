import secrets

from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.database.models.ReviewModel import Review

POSITIVE_REVIEWS = [
    "One of the best games I've played this year. Absolutely worth every penny.",
    "Incredibly polished from start to finish. The gameplay loop is addictive.",
    "A masterpiece. The story kept me hooked for 60+ hours.",
    "Best purchase of the year. I've already recommended it to everyone I know.",
    "Tight mechanics, stunning visuals, and a soundtrack I still listen to.",
    "Genuinely surprised by how good this is. A hidden gem.",
    "The devs clearly care about their game. Updates are consistent and meaningful.",
    "Challenging but fair. Every death feels like a learning opportunity.",
    "One of those rare games that actually delivers on its promises.",
    "Strong recommend. The first two hours alone are worth the price.",
    "Runs great, looks stunning, and plays even better. Just buy it.",
    "Cozy, charming, and surprisingly deep. Loved every single minute.",
    "I came for the gameplay, stayed for the world-building. Incredible.",
    "Plays like a dream. Smooth performance across the board.",
    "The attention to detail here is insane. You can tell this was made with love.",
    "Picked this up on a whim and it became my game of the year.",
    "Exactly what I was looking for. Satisfying, replayable, and well-priced.",
    "The combat system alone makes this worth playing. Absolutely crisp.",
    "I don't write reviews often but this one deserves it. Buy it now.",
    "100 hours in and I'm still finding new things. Exceptional game.",
]

NEGATIVE_REVIEWS = [
    "Disappointing. The controls feel clunky and unresponsive throughout.",
    "Not worth the full price. Too many bugs that break the experience.",
    "Crashes every 30 minutes. I gave up after losing progress three times.",
    "The concept is great but the execution is all over the place.",
    "Boring after the first hour. There's just no depth to the gameplay.",
    "Feels unfinished. Several core features are simply missing.",
    "Way too short for the asking price. Done in under three hours.",
    "The AI is terrible and the difficulty scaling makes absolutely no sense.",
    "Needed way more polish. Too many rough edges to recommend this.",
    "Lots of potential completely wasted. Maybe in a year it'll be worth it.",
    "The story had me interested but the gameplay is just tedious.",
    "Looked great in the trailer. Reality is much less exciting.",
    "Serious performance issues on every machine I tried. Not optimized at all.",
    "Repetitive to a fault. The same content recycled over and over again.",
    "Wait for a deep sale. At full price this is a hard pass.",
    "The monetization model ruins what could have been a great game.",
    "Promised features that were never delivered. False advertising.",
    "The servers are constantly down. Can't even play what I paid for.",
    "Controls that felt designed for another platform entirely. Just bad.",
    "I wanted to love this but the devs abandoned it after launch.",
]


def _votes() -> int:
    if secrets.randbelow(10) < 7:
        return secrets.randbelow(30)
    return 30 + secrets.randbelow(970)


class ReviewFactory(SQLAlchemyFactory[Review]):
    __model__              = Review
    __set_relationships__  = False

    customer_title_id  = Use(lambda: None)
    content            = Use(lambda: secrets.choice(POSITIVE_REVIEWS))
    recommends         = Use(lambda: True)
    votes              = Use(_votes)
    status             = Use(lambda: True)
    created_at         = Use(lambda: None)
    updated_at         = Use(lambda: None)
