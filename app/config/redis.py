from collections.abc import Generator

from redis import Redis

from app.config.settings import settings


def get_redis() -> Generator[Redis, None, None]:
    r: Redis = Redis.from_url(settings.REDIS_URL)
    try:
        yield r
    finally:
        r.close()
