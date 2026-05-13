# `endpoint/validation/` — Modelos Pydantic

Este directorio contiene los **modelos Pydantic** usados para validar y serializar los datos que entran y salen de la API.

## Convenciones

- Un archivo por recurso, en paralelo con `endpoint/route/` (p. ej. `users.py`, `items.py`).
- Separar claramente los esquemas según su propósito:
  - `*Create` — payload de creación (POST).
  - `*Update` — payload de actualización parcial (PATCH/PUT).
  - `*Read` / `*Public` — respuesta devuelta al cliente.
- **No importar** modelos SQLAlchemy aquí; este directorio es independiente de la capa de base de datos.

## Ejemplo

```python
# endpoint/validation/users.py
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: int
    email: EmailStr

    model_config = {"from_attributes": True}
```
