from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME:           str = ""
    POSTGRES_SERVER:        str = ""
    POSTGRES_USER:          str = ""
    POSTGRES_PASSWORD:      str = ""
    POSTGRES_DB:            str = ""
    POSTGRES_PORT:          int = 0

    JWT_SECRET_KEY:         str = ""
    JWT_EXPIRATION:         int = 0

    MAIL_HOST:              str = ""
    MAIL_PORT:              int = 0
    MAIL_FROM:              str = ""

    STRIPE_SECRET_KEY:      str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_SUCCESS_URL:     str = ""
    STRIPE_CANCEL_URL:      str = ""

    REDIS_HOST:             str = "redis"
    REDIS_PORT:             int = 6379

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
