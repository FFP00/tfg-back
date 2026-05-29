from fastapi import APIRouter, Depends, HTTPException
from pwdlib import PasswordHash
from sqlmodel import Session, select

from app.config.database import get_session
from app.endpoint.models.CustomerModel import Customer
from app.endpoint.schemas.customerSchema import CustomerPatch as PatchValidation
from app.endpoint.schemas.customerSchema import CustomerShow as ShowValidation

# Argon2 es el estándar de oro actual para contraseñas
hasher = PasswordHash.recommended()
router = APIRouter()


@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
    customers = session.exec(select(Customer).where(Customer.status)).all()
    return customers


@router.get("/{id}", response_model=ShowValidation, status_code=200)
def show_by_id(id: int, session: Session = Depends(get_session)):
    customer = session.exec(
        select(Customer).where(Customer.id == id, Customer.status)
    ).first()
    if not customer:
        raise HTTPException(
            status_code=404, detail="Customer with specified ID doesn't exist"
        )
    return customer


@router.get("/name/{name}", response_model=ShowValidation, status_code=200)
def show_by_name(name: str, session: Session = Depends(get_session)):
    customer = session.exec(
        select(Customer).where(Customer.name == name, Customer.status)
    ).first()
    if not customer:
        raise HTTPException(
            status_code=404, detail="Customer with specified NAME doesn't exist"
        )
    return customer


@router.get("/email/{email}", response_model=ShowValidation, status_code=200)
def show_by_email(email: str, session: Session = Depends(get_session)):
    customer = session.exec(
        select(Customer).where(Customer.email == email, Customer.status)
    ).first()
    if not customer:
        raise HTTPException(
            status_code=404, detail="Customer with specified EMAIL doesn't exist"
        )
    return customer


@router.patch("/{id}", response_model=ShowValidation)
def update(id: int, payload: PatchValidation, session: Session = Depends(get_session)):
    customer = session.exec(
        select(Customer).where(Customer.id == id, Customer.status)
    ).first()
    if not customer:
        raise HTTPException(
            status_code=404, detail="Customer with specified ID doesn't exist"
        )

    customer.sqlmodel_update(payload.model_dump(exclude_unset=True))

    if payload.password is not None:
        customer.password = hasher.hash(customer.password)
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


@router.patch("/name/{name}", response_model=ShowValidation)
def update_by_name(
    name: str, payload: PatchValidation, session: Session = Depends(get_session)
):
    customer = session.exec(
        select(Customer).where(Customer.name == name, Customer.status)
    ).first()
    if not customer:
        raise HTTPException(
            status_code=404, detail="Customer with specified NAME doesn't exist"
        )

    customer.sqlmodel_update(payload.model_dump(exclude_unset=True))

    if payload.password is not None:
        customer.password = hasher.hash(customer.password)
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


@router.patch("/email/{email}", response_model=ShowValidation)
def update_by_email(
    email: str, payload: PatchValidation, session: Session = Depends(get_session)
):
    customer = session.exec(
        select(Customer).where(Customer.email == email, Customer.status)
    ).first()
    if not customer:
        raise HTTPException(
            status_code=404, detail="Customer with specified EMAIL doesn't exist"
        )

    customer.sqlmodel_update(payload.model_dump(exclude_unset=True))

    if payload.password is not None:
        customer.password = hasher.hash(customer.password)
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


@router.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
    customer = session.exec(
        select(Customer).where(Customer.id == id, Customer.status)
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404, detail="Customer with specified ID doesn't exist"
        )

    customer.status = False

    session.add(customer)
    session.commit()
    session.refresh(customer)

    return {"status": "ok"}
