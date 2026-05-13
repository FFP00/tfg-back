# `endpoint/route/` — Routers de FastAPI

Este directorio contiene los **routers de FastAPI** (`APIRouter`). Cada archivo agrupa los endpoints relacionados con un recurso o dominio concreto.

## Convenciones

- Un archivo por recurso (p. ej. `users.py`, `items.py`, `auth.py`).
- Cada archivo define un `APIRouter` y lo exporta para que `main.py` lo incluya con `app.include_router(...)`.
- Los routers **no contienen lógica de negocio**: delegan en las funciones CRUD de `database/crud/`.
- Las entradas y salidas se validan mediante los modelos Pydantic definidos en `endpoint/validation/`.

## Ejemplo

```python
# endpoint/route/users.py
from fastapi import APIRouter
from app.endpoint.validation.users import UserCreate, UserRead
from app.database.crud import users as crud

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int):
    return crud.get_user(user_id)
```

## Registro en `main.py`

```python
from app.endpoint.route import users
app.include_router(users.router)
```
