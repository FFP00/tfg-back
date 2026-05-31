from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config.database import get_session
from app.database.models.CountryModel import Country
from app.endpoint.schemas.countrySchema import CountryShow

router = APIRouter()


@router.get("/", response_model=list[CountryShow])
def index(session: Session = Depends(get_session)) -> list[Country]:
    return list(session.exec(select(Country)).all())


@router.get("/{code}", response_model=CountryShow)
def show(code: str, session: Session = Depends(get_session)) -> Country:
    country = session.exec(select(Country).where(Country.code == code)).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country no encontrado")
    return country
