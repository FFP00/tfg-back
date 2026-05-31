from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import Response
from pwdlib import PasswordHash
from sqlmodel import Session, col, or_, select

from app.config.auth import get_current_customer, oauth2_customer
from app.config.database import get_session
from app.database.models.CountryModel import Country
from app.database.models.CustomerModel import Customer
from app.database.models.CustomerTitleModel import CustomerTitle
from app.database.models.FriendshipModel import Friendship
from app.database.models.ImageModel import Image
from app.database.models.ReviewModel import Review
from app.database.models.TitleModel import Title
from app.database.models.WalletModel import Wallet
from app.endpoint.schemas.customerSchema import (
    CustomerImageUpload,
    CustomerPatch,
    CustomerPublic,
    CustomerShow,
    FriendItem,
    LibraryItem,
    LoginCustomerResponse,
)
from app.endpoint.schemas.titleSchema import ReviewShow
from app.endpoint.schemas.walletSchema import DepositPayload, WalletShow

hasher = PasswordHash.recommended()
router = APIRouter()

_IMAGE_FIELDS = ("profile", "banner")


# ── Static routes first (before /{name}) ─────────────────────────────────────


@router.get("/me", response_model=LoginCustomerResponse)
def me(
    token: str = Depends(oauth2_customer),
    current: Customer = Depends(get_current_customer),
    session: Session = Depends(get_session),
) -> LoginCustomerResponse:
    wallet = session.exec(
        select(Wallet).where(Wallet.customer_id == current.id)
    ).first()
    return LoginCustomerResponse(
        access_token=token,
        customer=CustomerShow.model_validate(current, from_attributes=True),
        wallet=WalletShow.model_validate(wallet, from_attributes=True)
        if wallet
        else None,
    )


@router.get("/", response_model=list[CustomerPublic])
def index(search: str = "", session: Session = Depends(get_session)) -> list[Customer]:
    q = select(Customer).where(Customer.status)
    if search:
        q = q.where(
            or_(
                col(Customer.name).ilike(f"%{search}%"),
                col(Customer.email).ilike(f"%{search}%"),
            )
        )
    return list(session.exec(q).all())


@router.patch("/me", response_model=CustomerShow)
def update_me(
    payload: CustomerPatch,
    current: Customer = Depends(get_current_customer),
    session: Session = Depends(get_session),
) -> Customer:
    data = payload.model_dump(exclude_unset=True)

    if (
        "name" in data
        and session.exec(
            select(Customer).where(
                Customer.name == data["name"], Customer.id != current.id
            )
        ).first()
    ):
        raise HTTPException(status_code=409, detail="Nombre ya en uso")

    if (
        "email" in data
        and session.exec(
            select(Customer).where(
                Customer.email == data["email"], Customer.id != current.id
            )
        ).first()
    ):
        raise HTTPException(status_code=409, detail="Email ya en uso")

    if "country_code" in data:
        country = session.exec(
            select(Country).where(Country.code == data.pop("country_code"))
        ).first()
        if not country:
            raise HTTPException(status_code=404, detail="Country no encontrado")
        current.country_id = country.id

    if "password" in data:
        current.password = hasher.hash(data.pop("password"))

    current.sqlmodel_update(data)
    session.add(current)
    session.commit()
    session.refresh(current)
    return current


@router.post("/me/deposit", response_model=WalletShow)
def deposit(
    payload: DepositPayload,
    current: Customer = Depends(get_current_customer),
    session: Session = Depends(get_session),
) -> Wallet:
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="El importe debe ser positivo")
    wallet = session.exec(
        select(Wallet).where(Wallet.customer_id == current.id)
    ).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet no encontrada")
    wallet.balance = (wallet.balance or 0) + payload.amount
    session.add(wallet)
    session.commit()
    session.refresh(wallet)
    return wallet


@router.patch("/me/image", status_code=204)
async def upload_image(
    body:    Annotated[CustomerImageUpload, Form()],
    current: Customer = Depends(get_current_customer),
    session: Session  = Depends(get_session),
) -> Response:
    if not body.profile and not body.banner:
        raise HTTPException(
            status_code=400, detail="Se requiere al menos un campo: profile o banner"
        )

    if current.image_id:
        image = session.get(Image, current.image_id)
        if not image:
            raise HTTPException(status_code=404, detail="Imagen no encontrada")
    else:
        image = Image()
        session.add(image)
        session.flush()
        current.image_id = image.id
        session.add(current)

    if body.profile:
        image.profile = await body.profile.read()
    if body.banner:
        image.banner = await body.banner.read()

    session.add(image)
    session.commit()
    return Response(status_code=204)


# ── Dynamic routes ────────────────────────────────────────────────────────────


@router.get("/{name}/image/{field}")
def get_image(
    name: str, field: str, session: Session = Depends(get_session)
) -> Response:
    if field not in _IMAGE_FIELDS:
        raise HTTPException(
            status_code=400, detail=f"Campo inválido. Válidos: {list(_IMAGE_FIELDS)}"
        )
    customer = session.exec(
        select(Customer).where(Customer.name == name, Customer.status)
    ).first()
    if not customer or not customer.image_id:
        raise HTTPException(status_code=404, detail="Customer o imagen no encontrada")
    image = session.get(Image, customer.image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    data: bytes | None = getattr(image, field, None)
    if not data:
        raise HTTPException(status_code=404, detail=f"Campo '{field}' vacío")
    return Response(content=data, media_type="image/jpeg")


@router.get("/{name}/library", response_model=list[LibraryItem])
def get_library(
    name: str, session: Session = Depends(get_session)
) -> list[LibraryItem]:
    customer = session.exec(
        select(Customer).where(Customer.name == name, Customer.status)
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer no encontrado")
    entries = session.exec(
        select(CustomerTitle).where(CustomerTitle.customer_id == customer.id)
    ).all()
    result = []
    for entry in entries:
        title = session.get(Title, entry.title_id)
        if title:
            result.append(LibraryItem(name=title.name))
    return result


@router.get("/{name}/friends", response_model=list[FriendItem])
def get_friends(name: str, session: Session = Depends(get_session)) -> list[FriendItem]:
    customer = session.exec(
        select(Customer).where(Customer.name == name, Customer.status)
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer no encontrado")
    friendships = session.exec(
        select(Friendship).where(
            or_(
                Friendship.customer_id_1 == customer.id,
                Friendship.customer_id_2 == customer.id,
            ),
            Friendship.status == "accepted",
        )
    ).all()
    result = []
    for f in friendships:
        friend_id = (
            f.customer_id_2 if f.customer_id_1 == customer.id else f.customer_id_1
        )
        friend = session.get(Customer, friend_id)
        if friend and friend.status:
            result.append(FriendItem(name=friend.name))
    return result


@router.get("/{name}/reviews", response_model=list[ReviewShow])
def get_reviews(name: str, session: Session = Depends(get_session)) -> list[ReviewShow]:
    customer = session.exec(
        select(Customer).where(Customer.name == name, Customer.status)
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer no encontrado")
    customer_titles = session.exec(
        select(CustomerTitle).where(CustomerTitle.customer_id == customer.id)
    ).all()
    if not customer_titles:
        return []
    ct_map = {ct.id: ct for ct in customer_titles}
    reviews = session.exec(
        select(Review).where(
            col(Review.customer_title_id).in_(list(ct_map.keys())),
            Review.status,
        )
    ).all()
    result = []
    for r in reviews:
        ct = ct_map.get(r.customer_title_id)
        title = session.get(Title, ct.title_id) if ct else None
        result.append(
            ReviewShow(
                content=r.content,
                recommends=r.recommends,
                votes=r.votes,
                customer_name=name,
                title_name=title.name if title else None,
                created_at=r.created_at,
            )
        )
    return result


@router.get("/{name}", response_model=CustomerPublic)
def show(name: str, session: Session = Depends(get_session)) -> Customer:
    customer = session.exec(
        select(Customer).where(Customer.name == name, Customer.status)
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer no encontrado")
    return customer
