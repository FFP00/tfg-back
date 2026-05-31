from sqlmodel import SQLModel


class CurrencyShow(SQLModel):
    name:   str
    code:   str
    symbol: str
