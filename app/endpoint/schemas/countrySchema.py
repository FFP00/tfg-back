from sqlmodel import SQLModel

from app.endpoint.schemas.currencySchema import CurrencyShow


class CountryCreate(SQLModel):
    name:           str
    code:           str
    currency_id:    int


class CountryShow(SQLModel):
    name:           str
    code:           str

    currency:       CurrencyShow | None = None


class CountryPatch(SQLModel):
    name:           str | None = None
    code:           str | None = None
    currency_id:    int | None = None
