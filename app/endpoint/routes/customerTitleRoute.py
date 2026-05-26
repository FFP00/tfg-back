from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config.database import get_session
from app.endpoint.models.CustomerTitleModel import CustomerTitle
from app.endpoint.schemas.customerTitleSchema import (
    CustomerTitleCreate as CreateValidation,
)
from app.endpoint.schemas.customerTitleSchema import (
    CustomerTitlePatch as PatchValidation,
)
from app.endpoint.schemas.customerTitleSchema import CustomerTitleShow as ShowValidation

router = APIRouter()

@router.post("/", response_model=ShowValidation, status_code=201)
def create(payload: CreateValidation, session: Session = Depends(get_session)):
    customer_title = CustomerTitle.model_validate(payload)
    session.add(customer_title)
    session.commit()
    session.refresh(customer_title)
    return customer_title



@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
    customer_titles = session.exec(select(CustomerTitle)).all()
    return customer_titles



@router.get("/{id}", response_model=ShowValidation, status_code=200)
def show_by_id(id: int, session: Session = Depends(get_session)):
    customer_title = session.exec(select(CustomerTitle).where(CustomerTitle.id == id)).first()
    if not customer_title:
        raise HTTPException(status_code=404, detail="CustomerTitle with specified ID doesn't exist")
    return customer_title



@router.patch("/{id}", response_model=ShowValidation)
def update(id: int, payload: PatchValidation, session: Session = Depends(get_session)):
    customer_title = session.exec(select(CustomerTitle).where(CustomerTitle.id == id)).first()
    if not customer_title:
        raise HTTPException(status_code=404, detail="CustomerTitle with specified ID doesn't exist")

    customer_title.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(customer_title)
    session.commit()
    session.refresh(customer_title)
    return customer_title



@router.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
    customer_title = session.exec(select(CustomerTitle).where(CustomerTitle.id == id)).first()

    if not customer_title:
        raise HTTPException(status_code=404, detail="CustomerTitle with specified ID doesn't exist")

    session.delete(customer_title)
    session.commit()

    return {"status": "ok"}
