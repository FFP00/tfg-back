from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.config.database import get_session
from app.database.models.CurrencyModel import Currency
from app.endpoint.schemas.currencySchema import CurrencyShow

router = APIRouter()


@router.get("/", response_model=list[CurrencyShow])
def index(session: Session = Depends(get_session)) -> list[Currency]:
    return list(session.exec(select(Currency)).all())
