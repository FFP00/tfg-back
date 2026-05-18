from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME:               str = ""
    POSTGRES_SERVER:            str = ""
    POSTGRES_USER:              str = ""
    POSTGRES_PASSWORD:          str = ""
    POSTGRES_DB:                str = ""
    POSTGRES_PORT:              int = 0

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
