from sqlmodel import SQLModel


class TokenResponse(SQLModel):
    access_token: str
    token_type:   str = "bearer"  # noqa: S105
    role:         str
