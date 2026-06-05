from sqlmodel import SQLModel


class ContactPayload(SQLModel):
    textarea: str


class ContactResponse(SQLModel):
    detail: str
