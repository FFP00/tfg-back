from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME:               str | None = None
    POSTGRES_SERVER:            str | None = None
    POSTGRES_USER:              str | None = None
    POSTGRES_PASSWORD:          str | None = None
    POSTGRES_DB:                str | None = None
    POSTGRES_PORT:              int | None = None
    FIRST_SUPERUSER:            str | None = None
    FIRST_SUPERUSER_PASSWORD:   str | None = None

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
