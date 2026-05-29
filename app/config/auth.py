import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.settings import settings
from app.endpoint.models.CustomerModel import Customer
from app.endpoint.models.DeveloperModel import Developer
from app.endpoint.models.TokenModel import Token

_ALGORITHM = "HS256"

oauth2_customer  = OAuth2PasswordBearer(tokenUrl="/auth/customer/login",  scheme_name="CustomerBearer")
oauth2_developer = OAuth2PasswordBearer(tokenUrl="/auth/developer/login", scheme_name="DeveloperBearer")


def create_access_token(data: dict, session: Session) -> str:
    token = jwt.encode({"token": str(uuid.uuid4()), **data}, settings.JWT_SECRET_KEY, algorithm=_ALGORITHM)
    session.add(Token(token=token, user_id=data["sub"]))
    session.commit()
    return token


def _decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[_ALGORITHM])
    except jwt.InvalidTokenError as err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from err


def revoke_token(token: str, session: Session) -> None:
    record = session.exec(select(Token).where(Token.token == token)).first()
    if record:
        session.delete(record)
        session.commit()


def _check_active(token: str, session: Session) -> None:
    if not session.exec(select(Token).where(Token.token == token)).first():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión no activa o ya cerrada")


def get_current_customer(token: str = Depends(oauth2_customer), session: Session = Depends(get_session)) -> Customer:
    payload = _decode_jwt(token)
    if payload.get("role") != "customer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    _check_active(token, session)
    customer = session.exec(select(Customer).where(Customer.id == payload["sub"], Customer.status)).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    return customer


def get_current_developer(token: str = Depends(oauth2_developer), session: Session = Depends(get_session)) -> Developer:
    payload = _decode_jwt(token)
    if payload.get("role") != "developer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    _check_active(token, session)
    developer = session.exec(select(Developer).where(Developer.id == payload["sub"], Developer.status)).first()
    if not developer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Developer no encontrado")
    return developer
