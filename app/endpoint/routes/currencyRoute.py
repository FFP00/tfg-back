from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config.database import get_session
from app.endpoint.models.CurrencyModel import Currency
from app.endpoint.schemas.currencySchema import CurrencyCreate as CreateValidation
from app.endpoint.schemas.currencySchema import CurrencyPatch as PatchValidation
from app.endpoint.schemas.currencySchema import CurrencyShow as ShowValidation

router = APIRouter()

@router.post("/", response_model=ShowValidation, status_code=201)
def create(payload: CreateValidation, session: Session = Depends(get_session)):
    currency = Currency.model_validate(payload)
    session.add(currency)
    session.commit()
    session.refresh(currency)
    return currency



@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
    currencies = session.exec(select(Currency)).all()
    return currencies



@router.get("/{id}", response_model=ShowValidation, status_code=200)
def show_by_id(id: int, session: Session = Depends(get_session)):
    currency = session.exec(select(Currency).where(Currency.id == id)).first()
    if not currency:
        raise HTTPException(status_code=404, detail="Currency with specified ID doesn't exist")
    return currency



@router.get("/name/{name}", response_model=ShowValidation, status_code=200)
def show_by_name(name: str, session: Session = Depends(get_session)):
    currency = session.exec(select(Currency).where(Currency.name == name)).first()
    if not currency:
        raise HTTPException(status_code=404, detail="Currency with specified NAME doesn't exist")
    return currency



@router.get("/code/{code}", response_model=ShowValidation, status_code=200)
def show_by_code(code: str, session: Session = Depends(get_session)):
    currency = session.exec(select(Currency).where(Currency.code == code)).first()
    if not currency:
        raise HTTPException(status_code=404, detail="Currency with specified CODE doesn't exist")
    return currency



@router.patch("/{id}", response_model=ShowValidation)
def update(id: int, payload: PatchValidation, session: Session = Depends(get_session)):
    currency = session.exec(select(Currency).where(Currency.id == id)).first()
    if not currency:
        raise HTTPException(status_code=404, detail="Currency with specified ID doesn't exist")

    currency.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(currency)
    session.commit()
    session.refresh(currency)
    return currency



@router.patch("/name/{name}", response_model=ShowValidation)
def update_by_name(name: str, payload: PatchValidation, session: Session = Depends(get_session)):
    currency = session.exec(select(Currency).where(Currency.name == name)).first()
    if not currency:
        raise HTTPException(status_code=404, detail="Currency with specified NAME doesn't exist")

    currency.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(currency)
    session.commit()
    session.refresh(currency)
    return currency



@router.patch("/code/{code}", response_model=ShowValidation)
def update_by_code(code: str, payload: PatchValidation, session: Session = Depends(get_session)):
    currency = session.exec(select(Currency).where(Currency.code == code)).first()
    if not currency:
        raise HTTPException(status_code=404, detail="Currency with specified CODE doesn't exist")

    currency.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(currency)
    session.commit()
    session.refresh(currency)
    return currency



@router.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
    currency = session.exec(select(Currency).where(Currency.id == id)).first()

    if not currency:
        raise HTTPException(status_code=404, detail="Currency with specified ID doesn't exist")

    session.delete(currency)
    session.commit()

    return {"status": "ok"}
