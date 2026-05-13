# app/database/connection.py
from sqlmodel import Session, create_engine

from app.settings.config import settings

# Usamos la property que definiste en tu clase Settings
engine = create_engine(settings.DATABASE_URL)

def get_session():
    with Session(engine) as session:
        yield session
