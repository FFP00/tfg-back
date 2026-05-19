from sqlmodel import SQLModel


class CurrencyCreate(SQLModel):
    name:   str
    code:   str


class CurrencyShow(SQLModel):
    name:   str
    code:   str


class CurrencyPatch(SQLModel):
    name:   str | None = None
    code:   str | None = None
