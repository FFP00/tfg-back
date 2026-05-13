# `database/model/` — Modelos SQLAlchemy / SQLModel

Este directorio contiene los **modelos ORM** que representan las tablas de la base de datos. Se usa **SQLModel**, que unifica SQLAlchemy y Pydantic en una sola clase.

## Convenciones

- Un archivo por entidad o grupo de entidades relacionadas (p. ej. `user.py`, `item.py`).
- Cada modelo hereda de `SQLModel` con `table=True` para que Alembic lo detecte en las migraciones.
- Importar todos los modelos en `__init__.py` para que `alembic/env.py` los registre en `metadata`.
- **No incluir** lógica de negocio ni validaciones de endpoint aquí.

## Ejemplo

```python
# database/model/user.py
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = True
```

## `__init__.py`

Re-exportar todos los modelos para que Alembic los encuentre:

```python
from app.database.model.user import User  # noqa: F401
```
