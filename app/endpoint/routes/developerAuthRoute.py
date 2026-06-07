import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Response
from pwdlib import PasswordHash
from sqlmodel import Session, or_, select

from app.config.auth import create_access_token, oauth2_developer, revoke_token
from app.config.database import get_session
from app.config.mail import send_admin_developer_pending, send_otp_code
from app.database.models.CountryModel import Country
from app.database.models.DeveloperModel import Developer
from app.database.models.OtpModel import Otp
from app.database.models.UserModel import User
from app.endpoint.schemas.authSchema import LoginForm
from app.endpoint.schemas.countrySchema import CountryShow
from app.endpoint.schemas.developerSchema import DeveloperCreate as CreateValidation
from app.endpoint.schemas.developerSchema import DeveloperShow as ShowValidation
from app.endpoint.schemas.developerSchema import LoginDeveloperResponse
from app.endpoint.schemas.otpSchema import OtpPending, OtpVerify

_OTP_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

hasher = PasswordHash.recommended()
router = APIRouter()


def _build_show(developer: Developer) -> ShowValidation:
    u = developer.user
    return ShowValidation(
        name          = u.name          if u else "",
        email         = u.email         if u else "",
        support_email = developer.support_email,
        website_url   = developer.website_url,
        status        = developer.status,
        country       = CountryShow.model_validate(u.country, from_attributes=True) if u and u.country else None,
        created_at    = developer.created_at,
        updated_at    = developer.updated_at,
    )


def _generate_otp(user_id: int, session: Session) -> str:
    code     = "".join(secrets.choice(_OTP_CHARS) for _ in range(4))
    existing = session.get(Otp, user_id)
    if existing:
        existing.code = code
        session.add(existing)
    else:
        session.add(Otp(user_id=user_id, code=code))
    session.commit()
    return code


@router.post("/register", status_code=201)
def register(payload: CreateValidation, session: Session = Depends(get_session)) -> Response:
    if session.exec(
        select(User).where(or_(User.email == payload.email, User.name == payload.name))
    ).first():
        raise HTTPException(status_code=409, detail="Email o nombre ya registrado")
    if session.exec(
        select(Developer).where(Developer.support_email == payload.support_email)
    ).first():
        raise HTTPException(status_code=409, detail="Support email ya registrado")
    if payload.website_url and session.exec(
        select(Developer).where(Developer.website_url == payload.website_url)
    ).first():
        raise HTTPException(status_code=409, detail="Website URL ya registrada")
    country = session.exec(select(Country).where(Country.code == payload.country_code)).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country no encontrado")
    user = User(
        name=payload.name,
        email=payload.email,
        password=hasher.hash(payload.password),
        country_id=country.id,
        type="DEV",
    )
    session.add(user)
    session.flush()
    session.add(Developer(user_id=user.id, support_email=payload.support_email, website_url=payload.website_url))
    session.commit()
    try:
        send_admin_developer_pending(payload.name, payload.support_email)
    except Exception:  # noqa: BLE001, S110
        pass
    return Response(status_code=201)


@router.post("/login", status_code=202, response_model=OtpPending)
def login(
    form: Annotated[LoginForm, Form()], session: Session = Depends(get_session)
) -> OtpPending:
    user      = session.exec(select(User).where(or_(User.email == form.username, User.name == form.username), User.type == "DEV")).first()
    developer = session.get(Developer, user.id) if user else None
    if not user or not developer or not developer.status or not hasher.verify(form.password, user.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    code = _generate_otp(user.id, session)
    try:
        send_otp_code(user.email, code)
    except Exception:  # noqa: BLE001
        pass
    return OtpPending()


@router.post("/verify", response_model=LoginDeveloperResponse)
def verify(payload: OtpVerify, session: Session = Depends(get_session)) -> LoginDeveloperResponse:
    user = session.exec(
        select(User).where(
            or_(User.email == payload.email, User.name == payload.email),
            User.type == "DEV",
        )
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    otp = session.exec(
        select(Otp).where(Otp.user_id == user.id, Otp.code == payload.code.upper())
    ).first()
    if not otp:
        raise HTTPException(status_code=400, detail="Código inválido")

    session.delete(otp)

    developer = session.get(Developer, user.id)
    token     = create_access_token({"sub": str(user.id), "role": "developer"}, user.id, session)

    return LoginDeveloperResponse(
        access_token = token,
        developer    = _build_show(developer),
    )


@router.post("/logout", status_code=204)
def logout(
    token: str = Depends(oauth2_developer), session: Session = Depends(get_session)
) -> Response:
    revoke_token(token, session)
    return Response(status_code=204)
