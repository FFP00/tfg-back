from sqlmodel import SQLModel

from app.endpoint.schemas.currencySchema import CurrencyShow


class CountryShow(SQLModel):
    name:     str
    en_name:  str
    code:     str

    currency: CurrencyShow | None = None
