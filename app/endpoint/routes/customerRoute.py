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
from app.database.models.UserModel import User
from app.database.models.WalletModel import Wallet
from app.endpoint.schemas.countrySchema import CountryShow
from app.endpoint.schemas.customerSchema import (
    CustomerImageUpload,
    FriendItem,
    LibraryItem,
    LoginCustomerResponse,
)
from app.endpoint.schemas.customerSchema import CustomerPatch as PatchValidation
from app.endpoint.schemas.customerSchema import CustomerPublic as PublicValidation
from app.endpoint.schemas.customerSchema import CustomerShow as ShowValidation
from app.endpoint.schemas.titleSchema import ReviewShow
from app.endpoint.schemas.walletSchema import DepositPayload, WalletShow

hasher = PasswordHash.recommended()
router = APIRouter()

_IMAGE_FIELDS = ("profile", "banner")


def _build_public(customer: Customer) -> PublicValidation:
    u = customer.user
    return PublicValidation(
        name       = u.name if u else "",
        country    = CountryShow.model_validate(u.country, from_attributes=True) if u and u.country else None,
        created_at = customer.created_at,
        updated_at = customer.updated_at,
    )


def _build_show(customer: Customer) -> ShowValidation:
    u = customer.user
    return ShowValidation(
        name       = u.name    if u else "",
        email      = u.email   if u else "",
        status     = customer.status,
        country    = CountryShow.model_validate(u.country, from_attributes=True) if u and u.country else None,
        created_at = customer.created_at,
        updated_at = customer.updated_at,
    )


def _customer_by_name(name: str, session: Session) -> Customer:
    user     = session.exec(select(User).where(User.name == name)).first()
    customer = session.get(Customer, user.id) if user else None
    if not customer or not customer.status:
        raise HTTPException(status_code=404, detail="Customer no encontrado")
    return customer


# ── Static routes first (before /{name}) ─────────────────────────────────────


@router.get("/me", response_model=LoginCustomerResponse)
def me(
    token:   str      = Depends(oauth2_customer),
    current: Customer = Depends(get_current_customer),
    session: Session  = Depends(get_session),
) -> LoginCustomerResponse:
    wallet = session.get(Wallet, current.user_id)
    return LoginCustomerResponse(
        access_token = token,
        customer     = _build_show(current),
        wallet       = WalletShow.model_validate(wallet, from_attributes=True) if wallet else None,
    )


@router.get("/", response_model=list[PublicValidation])
def index(search: str = "", session: Session = Depends(get_session)) -> list[PublicValidation]:
    q = select(Customer).join(User, Customer.user_id == User.id).where(Customer.status)
    if search:
        q = q.where(
            or_(col(User.name).ilike(f"%{search}%"), col(User.email).ilike(f"%{search}%"))
        )
    return [_build_public(c) for c in session.exec(q).all()]


@router.patch("/me", response_model=ShowValidation)
def update_me(
    payload: PatchValidation,
    current: Customer = Depends(get_current_customer),
    session: Session  = Depends(get_session),
) -> ShowValidation:
    data = payload.model_dump(exclude_unset=True)
    user = current.user

    if "name" in data and session.exec(
        select(User).where(User.name == data["name"], User.id != user.id)
    ).first():
        raise HTTPException(status_code=409, detail="Nombre ya en uso")

    if "email" in data and session.exec(
        select(User).where(User.email == data["email"], User.id != user.id)
    ).first():
        raise HTTPException(status_code=409, detail="Email ya en uso")

    if "country_code" in data:
        country = session.exec(select(Country).where(Country.code == data.pop("country_code"))).first()
        if not country:
            raise HTTPException(status_code=404, detail="Country no encontrado")
        user.country_id = country.id

    if "password" in data:
        user.password = hasher.hash(data.pop("password"))

    user.sqlmodel_update(data)
    session.add(user)
    session.commit()
    session.refresh(current)
    return _build_show(current)


@router.post("/me/deposit", response_model=WalletShow)
def deposit(
    payload: DepositPayload,
    current: Customer = Depends(get_current_customer),
    session: Session  = Depends(get_session),
) -> Wallet:
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="El importe debe ser positivo")
    wallet = session.get(Wallet, current.user_id)
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
        raise HTTPException(status_code=400, detail="Se requiere al menos un campo: profile o banner")
    image = session.get(Image, current.user_id)
    if not image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    if body.profile:
        image.profile = await body.profile.read()
    if body.banner:
        image.banner = await body.banner.read()
    session.add(image)
    session.commit()
    return Response(status_code=204)


# ── Dynamic routes ────────────────────────────────────────────────────────────


@router.get("/{name}/image/{field}")
def get_image(name: str, field: str, session: Session = Depends(get_session)) -> Response:
    if field not in _IMAGE_FIELDS:
        raise HTTPException(status_code=400, detail=f"Campo inválido. Válidos: {list(_IMAGE_FIELDS)}")
    customer = _customer_by_name(name, session)
    image    = session.get(Image, customer.user_id)
    if not image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    data: bytes | None = getattr(image, field, None)
    if not data:
        raise HTTPException(status_code=404, detail=f"Campo '{field}' vacío")
    return Response(content=data, media_type="image/jpeg")


@router.get("/{name}/library", response_model=list[LibraryItem])
def get_library(name: str, session: Session = Depends(get_session)) -> list[LibraryItem]:
    customer = _customer_by_name(name, session)
    entries  = session.exec(
        select(CustomerTitle).where(CustomerTitle.customer_user_id == customer.user_id)
    ).all()
    result = []
    for entry in entries:
        title = session.get(Title, entry.title_id)
        if title:
            result.append(LibraryItem(name=title.name))
    return result


@router.get("/{name}/friends", response_model=list[FriendItem])
def get_friends(name: str, session: Session = Depends(get_session)) -> list[FriendItem]:
    customer    = _customer_by_name(name, session)
    friendships = session.exec(
        select(Friendship).where(
            or_(
                Friendship.customer_user_id_1 == customer.user_id,
                Friendship.customer_user_id_2 == customer.user_id,
            ),
            Friendship.status == "accepted",
        )
    ).all()
    result = []
    for f in friendships:
        friend_id = (
            f.customer_user_id_2
            if f.customer_user_id_1 == customer.user_id
            else f.customer_user_id_1
        )
        friend = session.get(Customer, friend_id)
        if friend and friend.status and friend.user:
            result.append(FriendItem(name=friend.user.name))
    return result


@router.get("/{name}/reviews", response_model=list[ReviewShow])
def get_reviews(name: str, session: Session = Depends(get_session)) -> list[ReviewShow]:
    customer        = _customer_by_name(name, session)
    customer_titles = session.exec(
        select(CustomerTitle).where(CustomerTitle.customer_user_id == customer.user_id)
    ).all()
    if not customer_titles:
        return []
    ct_map  = {ct.id: ct for ct in customer_titles}
    reviews = session.exec(
        select(Review).where(col(Review.customer_title_id).in_(list(ct_map.keys())), Review.status)
    ).all()
    result = []
    for r in reviews:
        ct    = ct_map.get(r.customer_title_id) if r.customer_title_id else None
        title = session.get(Title, ct.title_id) if ct else None
        result.append(ReviewShow(
            content       = r.content,
            recommends    = r.recommends,
            votes         = r.votes,
            customer_name = customer.user.name if customer.user else name,
            title_name    = title.name if title else None,
            created_at    = r.created_at,
        ))
    return result


@router.get("/{name}", response_model=PublicValidation)
def show(name: str, session: Session = Depends(get_session)) -> PublicValidation:
    return _build_public(_customer_by_name(name, session))
