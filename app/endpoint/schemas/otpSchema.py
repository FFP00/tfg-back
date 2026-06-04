from sqlmodel import SQLModel


class OtpVerify(SQLModel):
    email: str
    code:  str


class OtpPending(SQLModel):
    detail: str = "Código de verificación enviado a tu email"
