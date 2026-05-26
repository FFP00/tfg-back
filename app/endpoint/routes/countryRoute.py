from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config.database import get_session
from app.endpoint.models.CountryModel import Country
from app.endpoint.schemas.countrySchema import CountryCreate as CreateValidation
from app.endpoint.schemas.countrySchema import CountryPatch as PatchValidation
from app.endpoint.schemas.countrySchema import CountryShow as ShowValidation

router = APIRouter()

@router.post("/", response_model=ShowValidation, status_code=201)
def create(payload: CreateValidation, session: Session = Depends(get_session)):
    country = Country.model_validate(payload)
    session.add(country)
    session.commit()
    session.refresh(country)
    return country



@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
    countries = session.exec(select(Country)).all()
    return countries



@router.get("/{id}", response_model=ShowValidation, status_code=200)
def show_by_id(id: int, session: Session = Depends(get_session)):
    country = session.exec(select(Country).where(Country.id == id)).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country with specified ID doesn't exist")
    return country



@router.get("/name/{name}", response_model=ShowValidation, status_code=200)
def show_by_name(name: str, session: Session = Depends(get_session)):
    country = session.exec(select(Country).where(Country.name == name)).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country with specified NAME doesn't exist")
    return country



@router.get("/code/{code}", response_model=ShowValidation, status_code=200)
def show_by_code(code: str, session: Session = Depends(get_session)):
    country = session.exec(select(Country).where(Country.code == code)).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country with specified CODE doesn't exist")
    return country



@router.patch("/{id}", response_model=ShowValidation)
def update(id: int, payload: PatchValidation, session: Session = Depends(get_session)):
    country = session.exec(select(Country).where(Country.id == id)).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country with specified ID doesn't exist")

    country.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(country)
    session.commit()
    session.refresh(country)
    return country



@router.patch("/name/{name}", response_model=ShowValidation)
def update_by_name(name: str, payload: PatchValidation, session: Session = Depends(get_session)):
    country = session.exec(select(Country).where(Country.name == name)).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country with specified NAME doesn't exist")

    country.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(country)
    session.commit()
    session.refresh(country)
    return country



@router.patch("/code/{code}", response_model=ShowValidation)
def update_by_code(code: str, payload: PatchValidation, session: Session = Depends(get_session)):
    country = session.exec(select(Country).where(Country.code == code)).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country with specified CODE doesn't exist")

    country.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(country)
    session.commit()
    session.refresh(country)
    return country



@router.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
    country = session.exec(select(Country).where(Country.id == id)).first()

    if not country:
        raise HTTPException(status_code=404, detail="Country with specified ID doesn't exist")

    session.delete(country)
    session.commit()

    return {"status": "ok"}
