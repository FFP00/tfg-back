# API Endpoints — Referencia completa

## ¿Qué es este proyecto?

**GameStore** es una plataforma de distribución digital de videojuegos de código abierto, inspirada en Steam y GOG. Funciona como un marketplace donde:

- **Customers** (usuarios/jugadores) crean cuentas, recargan su wallet en USD, compran juegos, escriben reviews y se agregan como amigos.
- **Developers** (estudios/desarrolladores) publican juegos (títulos), suben sus imágenes y trailers, y gestionan precios y descuentos.
- Un **administrador** aprueba tanto cuentas de developers como títulos antes de que sean visibles públicamente.

### Modelo de dominio

```
Developer ──publica──► Title (juego)
                         │
                         ├── Media (capsule, header, store_1–6, trailer)
                         ├── Genre[] (etiquetas: RPG, Aventura, etc.)
                         └── Review[] (escritas por customers que lo compraron)

Customer ──tiene──► Wallet (saldo en USD)
Customer ──compra──► Transaction ──contiene──► TitleTransaction (precio pagado, descuento aplicado)
Customer ──posee──► CustomerTitle (biblioteca: lista de juegos comprados)
Customer ──escribe──► Review (requiere tener el juego; moderada por admin)
Customer ──tiene──► Friendship (pending → accepted | rejected | blocked)
```

### Flujo de vida de un título

1. Developer se registra → `status=false` (pendiente de aprobación admin)
2. Admin aprueba → `status=true` → developer puede hacer login
3. Developer crea título → `status=false` (pendiente de aprobación admin)
4. Developer sube media del título (capsule, header, store_1 mínimo)
5. Admin aprueba → `status=true` → título visible en el catálogo público
6. Customer compra el título mediante una transacción atómica
7. Customer puede escribir una review → `status=false` hasta que admin la aprueba

### Flujo de precios

```
precio_final = release_price × (1 - actual_discount / 100)
```

`actual_discount` es un entero 0–100. Ejemplo: precio base `$29.99`, descuento `20` → precio final `$23.99`.

### Sistema de autenticación

- Hay dos tipos de token **completamente separados**: `customer` y `developer`. No son intercambiables.
- Todos los tokens son JWT Bearer. Se envían como `Authorization: Bearer <token>`.
- El logout revoca el token en base de datos (no basta con eliminarlo del cliente).

---

## Reglas globales

- Todos los precios y balances están en **USD** (Decimal serializado como string para evitar pérdida de precisión flotante).
- **No se expone `id`** en ninguna respuesta pública. Identificadores únicos: `name`, `email`, `code`.
- Rutas protegidas requieren `Authorization: Bearer <token>`.
- Imágenes se sirven como `Content-Type: image/jpeg` — usar directamente como `src` de `<img>`.
- El `trailer` se sirve como `Content-Type: video/mp4` con soporte de `Range` para HTML5 `<video>`.
- Las reviews son moderadas: solo las aprobadas por el admin (`status=true`) aparecen en respuestas públicas.
- Los campos marcados `| null` pueden llegar como `null` en el JSON — manejar con optional chaining.

---

## Tipos reutilizables (schemas)

Estos objetos aparecen anidados en múltiples respuestas.

### `CurrencyShow`
```json
{
  "name":   "string",
  "code":   "string  — código ISO 4217, ej. 'EUR'",
  "symbol": "string  — símbolo visual, ej. '€'"
}
```

### `CountryShow`
```json
{
  "name":     "string  — nombre local del país",
  "en_name":  "string  — nombre en inglés",
  "code":     "string  — código ISO 3166-1 alpha-2, ej. 'ES'",
  "currency": "CurrencyShow | null"
}
```

### `WalletShow`
```json
{
  "balance": "string (Decimal) | null  — saldo en USD, ej. '25.50'"
}
```

### `CustomerShow`  _(privado — solo visible para el propio customer autenticado)_
```json
{
  "name":       "string",
  "email":      "string",
  "status":     "boolean  — false = cuenta desactivada",
  "country":    "CountryShow | null",
  "created_at": "string ISO8601 | null  — ej. '2025-01-15T10:30:00Z'",
  "updated_at": "string ISO8601 | null"
}
```

### `CustomerPublic`  _(perfil público — sin email)_
```json
{
  "name":       "string",
  "country":    "CountryShow | null",
  "created_at": "string ISO8601 | null",
  "updated_at": "string ISO8601 | null"
}
```

### `DeveloperShow`  _(privado — solo visible para el propio developer autenticado)_
```json
{
  "name":          "string",
  "email":         "string  — email privado de acceso",
  "support_email": "string  — email público de soporte",
  "website_url":   "string | null",
  "status":        "boolean  — false = pendiente de aprobación admin",
  "created_at":    "string ISO8601 | null",
  "updated_at":    "string ISO8601 | null"
}
```

### `DeveloperPublic`  _(perfil público — sin email privado)_
```json
{
  "name":          "string",
  "support_email": "string",
  "website_url":   "string | null",
  "created_at":    "string ISO8601 | null",
  "updated_at":    "string ISO8601 | null"
}
```

### `GenreShow`
```json
{
  "name": "string"
}
```

### `TitleCard`  _(resumen para listados y home)_
```json
{
  "name":            "string",
  "release_price":   "string (Decimal)  — precio base en USD, ej. '29.99'",
  "actual_discount": "integer (0–100)  — porcentaje de descuento actual",
  "genres":          "[GenreShow]  — puede ser []",
  "developer_name":  "string | null"
}
```
> Precio final = `release_price × (1 - actual_discount / 100)`

### `TitleShow`  _(detalle completo)_
```json
{
  "name":            "string",
  "status":          "boolean  — false = pendiente de aprobación admin",
  "actual_discount": "integer (0–100)",
  "release_date":    "string YYYY-MM-DD",
  "release_price":   "string (Decimal)",
  "genres":          "[GenreShow]  — puede ser []",
  "developer":       "DeveloperPublic | null",
  "created_at":      "string ISO8601 | null",
  "updated_at":      "string ISO8601 | null"
}
```

### `ReviewShow`
```json
{
  "content":       "string  — texto de la review",
  "recommends":    "boolean  — true = recomienda el juego",
  "votes":         "integer  — número de votos útiles recibidos",
  "customer_name": "string",
  "created_at":    "string ISO8601",
  "title_name":    "string | null  — solo presente en /api/customer/{name}/reviews; null en /api/title/{name}/reviews"
}
```

### `FriendshipShow`
```json
{
  "status":     "string  — 'pending' | 'accepted' | 'blocked' | 'rejected'",
  "from_name":  "string | null  — nombre del remitente original",
  "created_at": "string ISO8601 | null  — null cuando status='rejected' (registro eliminado)"
}
```

---

## Auth — `/auth`

### `POST /auth/customer/register`
Crear cuenta de cliente. **Público.**

**Body (`application/json`):**
```json
{
  "name":         "string  — nombre único de usuario",
  "email":        "string  — formato válido de email",
  "password":     "string  — mín. 8 chars, 1 mayúscula, 1 minúscula, 1 número, 1 carácter especial",
  "country_code": "string  — código ISO 3166-1 alpha-2, ej. 'ES' (obtener de GET /api/country/)"
}
```

**Respuesta exitosa:** `201` — cuerpo vacío.

**Errores:**
| Código | `detail` |
|--------|----------|
| 404 | `"Country no encontrado"` (si `country_code` no existe) |
| 409 | `"Email o nombre ya registrado"` |
| 422 | Error de validación de Pydantic (email inválido, contraseña débil, etc.) |

---

### `POST /auth/customer/login`
Login con `name` o `email` + contraseña. Solo customers con `status=true`. **Público.**

**Body (`application/x-www-form-urlencoded`):**
```
username=johndoe&password=Pass123!
```
> `username` acepta tanto el `name` como el `email` del customer.

**Respuesta exitosa:** `200`
```json
{
  "access_token": "string  — JWT Bearer token",
  "token_type":   "bearer",
  "customer":     "CustomerShow",
  "wallet":       "WalletShow | null  — null si el wallet no existe aún"
}
```

**Errores:**
| Código | `detail` |
|--------|----------|
| 401 | `"Credenciales incorrectas"` (usuario no existe, contraseña errónea, o cuenta inactiva) |
| 422 | Campos faltantes en el form |

---

### `POST /auth/customer/logout`
Revoca el token del customer en base de datos. **Requiere token de customer.**

**Respuesta exitosa:** `204` — cuerpo vacío.

**Errores:**
| Código | `detail` |
|--------|----------|
| 401 | Token inválido o expirado |

---

### `POST /auth/developer/register`
Crear cuenta de developer. La cuenta empieza con `status=false` hasta aprobación del admin. **Público.**

**Body (`application/json`):**
```json
{
  "name":          "string  — nombre único del estudio/developer",
  "email":         "string  — email privado de acceso (no se expone públicamente)",
  "support_email": "string  — email público de soporte para usuarios",
  "password":      "string  — mín. 8 chars, 1 mayúscula, 1 minúscula, 1 número, 1 carácter especial",
  "website_url":   "string | null  — opcional; si se envía debe ser único"
}
```

**Respuesta exitosa:** `201` — cuerpo vacío.

**Errores:**
| Código | `detail` |
|--------|----------|
| 409 | `"Email ya registrado"` |
| 409 | `"Nombre ya registrado"` |
| 409 | `"Support email ya registrado"` |
| 409 | `"Website URL ya registrada"` (si se envía `website_url` y ya existe) |
| 422 | Error de validación (email inválido, contraseña débil) |

---

### `POST /auth/developer/login`
Login por email. Solo developers con `status=true`. **Público.**

**Body (`application/x-www-form-urlencoded`):**
```
username=contacto@miestudio.com&password=Pass123!
```
> A diferencia del customer, `username` **solo acepta email** (no `name`).

**Respuesta exitosa:** `200`
```json
{
  "access_token": "string  — JWT Bearer token",
  "token_type":   "bearer",
  "developer":    "DeveloperShow"
}
```

**Errores:**
| Código | `detail` |
|--------|----------|
| 401 | `"Credenciales incorrectas"` (email no existe, contraseña errónea, o cuenta inactiva/pendiente) |
| 422 | Campos faltantes en el form |

---

### `POST /auth/developer/logout`
Revoca el token del developer en base de datos. **Requiere token de developer.**

**Respuesta exitosa:** `204` — cuerpo vacío.

**Errores:**
| Código | `detail` |
|--------|----------|
| 401 | Token inválido o expirado |

---

## Clientes — `/api/customer`

### `GET /api/customer/me`
Perfil completo del customer autenticado, incluyendo wallet. **Requiere token de customer.**

**Respuesta exitosa:** `200`
```json
{
  "access_token": "string  — el mismo token recibido en el header (útil para renovar referencias en cliente)",
  "token_type":   "bearer",
  "customer":     "CustomerShow",
  "wallet":       "WalletShow | null"
}
```

**Errores:**
| Código | `detail` |
|--------|----------|
| 401 | Token inválido o expirado |

---

### `GET /api/customer/`
Listado de todos los customers activos. Búsqueda opcional por `name` o `email`. **Público.**

**Query params:**
| Param | Tipo | Descripción |
|-------|------|-------------|
| `search` | `string` (opcional) | Filtra por coincidencia parcial en `name` o `email` (case-insensitive) |

**Respuesta exitosa:** `200`
```json
[
  "CustomerPublic",
  "..."
]
```
> El email **no** se incluye en `CustomerPublic` — es un listado completamente público.

---

### `PATCH /api/customer/me`
Actualizar perfil propio. Enviar solo los campos a modificar. **Requiere token de customer.**

**Body (`application/json`):** _(todos los campos son opcionales)_
```json
{
  "name":         "string | null  — nuevo nombre único",
  "email":        "string | null  — nuevo email",
  "password":     "string | null  — nueva contraseña (mín. 8 chars, 1 mayús, 1 minús, 1 número, 1 especial)",
  "country_code": "string | null  — código ISO del país, ej. 'ES'"
}
```

**Respuesta exitosa:** `200` → `CustomerShow`

**Errores:**
| Código | `detail` |
|--------|----------|
| 401 | Token inválido |
| 404 | `"Country no encontrado"` (si `country_code` no existe) |
| 409 | `"Nombre ya en uso"` |
| 409 | `"Email ya en uso"` |
| 422 | Contraseña no cumple requisitos |

---

### `POST /api/customer/me/deposit`
Añadir saldo al wallet del customer. **Requiere token de customer.**

**Body (`application/json`):**
```json
{
  "amount": "string (Decimal)  — importe positivo a añadir en USD, ej. '10.00'"
}
```

**Respuesta exitosa:** `200` → `WalletShow`
```json
{
  "balance": "string (Decimal)  — nuevo saldo total tras el depósito"
}
```

**Errores:**
| Código | `detail` |
|--------|----------|
| 400 | `"El importe debe ser positivo"` |
| 401 | Token inválido |
| 404 | `"Wallet no encontrada"` |

---

### `PATCH /api/customer/me/image`
Subir o reemplazar imagen de perfil y/o banner. **Requiere token de customer.**

**Body (`multipart/form-data`):** _(al menos uno de los dos es obligatorio)_
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `profile` | `file` (opcional) | Imagen de perfil (se almacena como JPEG) |
| `banner` | `file` (opcional) | Imagen de banner (se almacena como JPEG) |

**Respuesta exitosa:** `204` — cuerpo vacío.

**Errores:**
| Código | `detail` |
|--------|----------|
| 400 | `"Se requiere al menos un campo: profile o banner"` |
| 401 | Token inválido |
| 404 | `"Imagen no encontrada"` (inconsistencia interna) |

---

### `GET /api/customer/{name}/image/{field}`
Obtener imagen de un customer activo. **Público.**

**Path params:**
| Param | Valores válidos |
|-------|----------------|
| `name` | Nombre del customer |
| `field` | `"profile"` o `"banner"` |

**Respuesta exitosa:** `200` — bytes de imagen con `Content-Type: image/jpeg`.
> Usar directamente como `src` de `<img>`.

**Errores:**
| Código | `detail` |
|--------|----------|
| 400 | `"Campo inválido. Válidos: ['profile', 'banner']"` |
| 404 | `"Customer no encontrado"` (customer no existe o está inactivo) |
| 404 | `"Imagen no encontrada"` (inconsistencia interna) |
| 404 | `"Campo 'profile' vacío"` o `"Campo 'banner' vacío"` (imagen no subida para ese campo) |

---

### `GET /api/customer/{name}`
Perfil público de un customer activo. **Público.**

**Respuesta exitosa:** `200` → `CustomerPublic`

**Errores:**
| Código | `detail` |
|--------|----------|
| 404 | `"Customer no encontrado"` |

---

### `GET /api/customer/{name}/library`
Biblioteca de juegos del customer (todos los títulos que posee). **Público.**

**Respuesta exitosa:** `200`
```json
[
  { "name": "string  — nombre del título" },
  "..."
]
```

**Errores:**
| Código | `detail` |
|--------|----------|
| 404 | `"Customer no encontrado"` |

---

### `GET /api/customer/{name}/friends`
Lista de amigos aceptados del customer. Solo muestra amigos activos. **Público.**

**Respuesta exitosa:** `200`
```json
[
  { "name": "string  — nombre del customer amigo" },
  "..."
]
```

**Errores:**
| Código | `detail` |
|--------|----------|
| 404 | `"Customer no encontrado"` |

---

### `GET /api/customer/{name}/reviews`
Reviews aprobadas escritas por el customer. Incluye el nombre del juego reseñado. **Público.**

**Respuesta exitosa:** `200`
```json
[
  {
    "content":       "string",
    "recommends":    "boolean",
    "votes":         "integer",
    "customer_name": "string",
    "created_at":    "string ISO8601",
    "title_name":    "string | null  — nombre del juego reseñado"
  },
  "..."
]
```

**Errores:**
| Código | `detail` |
|--------|----------|
| 404 | `"Customer no encontrado"` |

---

## Developers — `/api/developer`

### `GET /api/developer/me`
Perfil completo del developer autenticado. **Requiere token de developer.**

**Respuesta exitosa:** `200`
```json
{
  "access_token": "string",
  "token_type":   "bearer",
  "developer":    "DeveloperShow"
}
```

**Errores:**
| Código | `detail` |
|--------|----------|
| 401 | Token inválido |

---

### `GET /api/developer/`
Listado de developers activos. Búsqueda por nombre. El email privado nunca se expone. **Público.**

**Query params:**
| Param | Tipo | Descripción |
|-------|------|-------------|
| `search` | `string` (opcional) | Filtra por coincidencia parcial en `name` (case-insensitive) |

**Respuesta exitosa:** `200`
```json
[
  "DeveloperPublic",
  "..."
]
```

---

### `PATCH /api/developer/me`
Actualizar perfil del developer. Enviar solo los campos a modificar. **Requiere token de developer.**

**Body (`application/json`):** _(todos opcionales)_
```json
{
  "name":          "string | null",
  "email":         "string | null  — email privado de acceso",
  "support_email": "string | null  — email público de soporte",
  "password":      "string | null",
  "website_url":   "string | null"
}
```

**Respuesta exitosa:** `200` → `DeveloperShow`

**Errores:**
| Código | `detail` |
|--------|----------|
| 401 | Token inválido |
| 409 | `"Nombre ya en uso"` |
| 409 | `"Email ya en uso"` |
| 409 | `"Support email ya en uso"` |
| 409 | `"Website URL ya en uso"` (si se envía `website_url` no nulo y ya existe) |
| 422 | Contraseña no cumple requisitos |

---

### `PATCH /api/developer/me/image`
Subir o reemplazar imagen de perfil y/o banner. **Requiere token de developer.**

**Body (`multipart/form-data`):** _(al menos uno requerido)_
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `profile` | `file` (opcional) | Imagen de perfil |
| `banner` | `file` (opcional) | Imagen de banner |

**Respuesta exitosa:** `204` — cuerpo vacío.

**Errores:**
| Código | `detail` |
|--------|----------|
| 400 | `"Se requiere al menos un campo: profile o banner"` |
| 401 | Token inválido |
| 404 | `"Imagen no encontrada"` |

---

### `GET /api/developer/{name}/image/{field}`
Obtener imagen de un developer activo. **Público.**

**Path params:**
| Param | Valores válidos |
|-------|----------------|
| `name` | Nombre del developer |
| `field` | `"profile"` o `"banner"` |

**Respuesta exitosa:** `200` — bytes con `Content-Type: image/jpeg`.

**Errores:**
| Código | `detail` |
|--------|----------|
| 400 | `"Campo inválido. Válidos: ['profile', 'banner']"` |
| 404 | `"Developer no encontrado"` |
| 404 | `"Imagen no encontrada"` |
| 404 | `"Campo 'X' vacío"` |

---

### `GET /api/developer/{name}`
Perfil público de un developer activo. Sin email privado. **Público.**

**Respuesta exitosa:** `200` → `DeveloperPublic`

**Errores:**
| Código | `detail` |
|--------|----------|
| 404 | `"Developer no encontrado"` |

---

## Títulos — `/api/title`

### `GET /api/title/random`
Un título aleatorio activo del catálogo. Útil para secciones tipo "juego destacado". **Público.**

**Respuesta exitosa:** `200` → `TitleCard`

**Errores:**
| Código | `detail` |
|--------|----------|
| 404 | `"No hay títulos disponibles"` |

---

### `GET /api/title/me`
Todos los títulos del developer autenticado, **incluyendo los pendientes de aprobación** (`status=false`). **Requiere token de developer.**

**Respuesta exitosa:** `200`
```json
[
  "TitleShow",
  "..."
]
```
> A diferencia del catálogo público, aquí aparecen los títulos con `status=false`. Útil para el panel del developer.

**Errores:**
| Código | `detail` |
|--------|----------|
| 401 | Token inválido |

---

### `GET /api/title/`
Catálogo de títulos activos (`status=true`). Filtros opcionales combinables. **Público.**

**Query params:**
| Param | Tipo | Descripción |
|-------|------|-------------|
| `search` | `string` (opcional) | Coincidencia parcial en `name` (case-insensitive) |
| `genre` | `string` (opcional) | Filtrar por nombre exacto de género (ej. `"RPG"`) |
| `developer` | `string` (opcional) | Filtrar por nombre exacto del developer |

**Respuesta exitosa:** `200`
```json
[
  "TitleCard",
  "..."
]
```
> Si `genre` o `developer` no existen, devuelve `[]` (no 404).

---

### `POST /api/title/`
Crear un nuevo título. Queda con `status=false` hasta aprobación del admin. **Requiere token de developer.**

**Body (`application/json`):**
```json
{
  "name":            "string  — nombre único del título",
  "release_date":    "string YYYY-MM-DD  — fecha de lanzamiento",
  "release_price":   "string (Decimal)  — precio base en USD",
  "actual_discount": "integer (0–100)  — opcional, por defecto 0"
}
```

**Respuesta exitosa:** `201` → `TitleShow`
> El título recién creado tendrá `status=false`, `genres=[]` y `developer` con los datos del developer autenticado.

**Errores:**
| Código | `detail` |
|--------|----------|
| 401 | Token inválido |
| 422 | Campos inválidos o faltantes |

---

### `POST /api/title/{name}/media`
Subir los archivos multimedia del título **por primera vez**. Solo disponible si `capsule` aún no tiene contenido. **Requiere token del developer propietario.**

**Path params:** `name` = nombre del título.

**Body (`multipart/form-data`):**
| Campo | Obligatorio | Descripción |
|-------|-------------|-------------|
| `capsule` | Sí | Imagen cápsula (miniatura principal, usada en listados) |
| `header` | Sí | Imagen cabecera de la página del juego |
| `store_1` | Sí | Primera imagen de la tienda (screenshots) |
| `store_2` | No | Segunda imagen |
| `store_3` | No | Tercera imagen |
| `store_4` | No | Cuarta imagen |
| `store_5` | No | Quinta imagen |
| `store_6` | No | Sexta imagen |
| `trailer` | No | Video trailer (mp4) |

**Respuesta exitosa:** `204` — cuerpo vacío.

**Errores:**
| Código | `detail` |
|--------|----------|
| 400 | `"Se requieren al menos: capsule, header y store_1"` |
| 401 | Token inválido |
| 403 | `"La media ya existe. Contacta al administrador para modificarla"` |
| 404 | `"Título no encontrado o no eres el propietario"` |

---

### `PATCH /api/title/{name}/media`
Actualizar uno o varios archivos multimedia de un título. Reemplaza solo los campos enviados. **Requiere token del developer propietario.**

**Path params:** `name` = nombre del título.

**Body (`multipart/form-data`):** _(todos opcionales, al menos uno requerido)_
| Campo | Descripción |
|-------|-------------|
| `capsule` | Imagen cápsula |
| `header` | Imagen cabecera |
| `store_1` – `store_6` | Imágenes de tienda |
| `trailer` | Video trailer (mp4) |

**Respuesta exitosa:** `204` — cuerpo vacío.

**Errores:**
| Código | `detail` |
|--------|----------|
| 400 | `"Se requiere al menos un campo"` |
| 401 | Token inválido |
| 404 | `"Título no encontrado o no eres el propietario"` |
| 404 | `"Media no encontrada"` |

---

### `GET /api/title/{name}/media/{field}`
Obtener un archivo multimedia de un título activo. **Público.**

**Path params:**
| Param | Valores válidos |
|-------|----------------|
| `name` | Nombre del título |
| `field` | `capsule`, `header`, `store_1`, `store_2`, `store_3`, `store_4`, `store_5`, `store_6`, `trailer` |

**Respuesta exitosa:**
- Para campos de imagen: `200` — bytes con `Content-Type: image/jpeg`.
- Para `trailer` sin header `Range`: `200` — stream completo con `Content-Type: video/mp4` y `Accept-Ranges: bytes`.
- Para `trailer` con header `Range: bytes=0-1048575`: `206 Partial Content` con `Content-Range`, `Content-Length` y `Accept-Ranges`.

> Usar `<img src="/api/title/{name}/media/capsule">` para imágenes.
> Usar `<video><source src="/api/title/{name}/media/trailer" type="video/mp4"></video>` para el trailer.

**Errores:**
| Código | `detail` |
|--------|----------|
| 400 | `"Campo inválido. Válidos: [...]"` |
| 404 | `"Título no encontrado"` (título inactivo o inexistente) |
| 404 | `"Media no encontrada"` |
| 404 | `"Campo 'X' vacío"` (campo no subido aún) |
| 416 | `"Range header inválido"` o `"Range Not Satisfiable"` |

---

### `GET /api/title/{name}/reviews`
Reviews aprobadas de un título. **Público.**

**Respuesta exitosa:** `200`
```json
[
  {
    "content":       "string",
    "recommends":    "boolean",
    "votes":         "integer",
    "customer_name": "string",
    "created_at":    "string ISO8601",
    "title_name":    null
  },
  "..."
]
```
> `title_name` siempre es `null` en este endpoint (el título ya es conocido por el contexto de la ruta).

**Errores:**
| Código | `detail` |
|--------|----------|
| 404 | `"Título no encontrado"` |

---

### `POST /api/title/{name}/reviews`
Publicar una review. El customer debe tener el título en su biblioteca. La review queda pendiente de aprobación del admin (`status=false`). **Requiere token de customer.**

**Body (`application/json`):**
```json
{
  "content":    "string  — texto de la review",
  "recommends": "boolean  — true si recomienda el juego"
}
```

**Respuesta exitosa:** `201`
```json
{
  "content":       "string",
  "recommends":    "boolean",
  "votes":         0,
  "customer_name": "string",
  "created_at":    "string ISO8601",
  "title_name":    null
}
```

**Errores:**
| Código | `detail` |
|--------|----------|
| 401 | Token inválido |
| 403 | `"Debes tener el juego para reseñarlo"` |
| 404 | `"Título no encontrado"` |
| 409 | `"Ya tienes una reseña para este juego"` |

---

### `PATCH /api/title/{name}/reviews/me`
Editar la propia review de un título. Solo campos a modificar. **Requiere token de customer.**

**Body (`application/json`):** _(ambos opcionales)_
```json
{
  "content":    "string | null",
  "recommends": "boolean | null"
}
```

**Respuesta exitosa:** `200` → `ReviewShow` (con `title_name: null`)

**Errores:**
| Código | `detail` |
|--------|----------|
| 401 | Token inválido |
| 403 | `"No tienes este juego"` |
| 404 | `"Título no encontrado"` |
| 404 | `"No tienes reseña para este juego"` |

---

### `POST /api/title/{name}/reviews/{customer_name}/vote`
Votar la review de otro customer como útil. No se puede votar la propia review. **Requiere token de customer.**

**Respuesta exitosa:** `200`
```json
{
  "votes": "integer  — nuevo total de votos de la review"
}
```

**Errores:**
| Código | `detail` |
|--------|----------|
| 400 | `"No puedes votar tu propia reseña"` |
| 401 | Token inválido |
| 404 | `"Título no encontrado"` |
| 404 | `"Autor de la reseña no encontrado"` |
| 404 | `"Reseña no encontrada"` |

---

### `PATCH /api/title/{name}`
Actualizar descuento y/o géneros de un título propio. **Requiere token del developer propietario.**

**Body (`application/json`):** _(ambos opcionales)_
```json
{
  "actual_discount": "integer (0–100) | null  — nuevo porcentaje de descuento",
  "genres":          "[string] | null  — lista de nombres de géneros; reemplaza completamente los géneros actuales"
}
```
> Enviar `"genres": []` elimina todos los géneros del título.

**Respuesta exitosa:** `200` → `TitleShow`

**Errores:**
| Código | `detail` |
|--------|----------|
| 401 | Token inválido |
| 404 | `"Título no encontrado o no eres el propietario"` |
| 404 | `"Genre 'X' no encontrado"` |

---

### `GET /api/title/{name}`
Detalle completo de un título activo. **Público.**

**Respuesta exitosa:** `200` → `TitleShow`

**Errores:**
| Código | `detail` |
|--------|----------|
| 404 | `"Título no encontrado"` |

---

## Transacciones — `/api/transaction`

### `POST /api/transaction/`
Compra atómica de uno o varios títulos. Si algún título falla (ya poseído, no disponible, saldo insuficiente), **toda la transacción se cancela**. **Requiere token de customer.**

**Body (`application/json`):**
```json
{
  "titles": "[string]  — lista de nombres de títulos a comprar (mín. 1)"
}
```

**Respuesta exitosa:** `201`
```json
{
  "titles_purchased": "integer  — cantidad de títulos comprados",
  "total_spent":      "string (Decimal)  — total descontado del wallet en USD",
  "wallet_balance":   "string (Decimal)  — saldo restante en el wallet tras la compra"
}
```

**Errores:**
| Código | `detail` |
|--------|----------|
| 400 | `"Lista de títulos vacía"` |
| 401 | Token inválido |
| 402 | `"Balance insuficiente"` |
| 404 | `"Wallet no encontrada"` |
| 404 | `"Título 'X' no encontrado o no disponible"` (título inactivo o inexistente) |
| 409 | `"Ya tienes 'X' en tu biblioteca"` |

---

### `GET /api/transaction/me`
Historial completo de compras del customer autenticado. **Requiere token de customer.**

**Respuesta exitosa:** `200`
```json
[
  {
    "created_at": "string ISO8601  — fecha y hora de la transacción",
    "titles": [
      {
        "name":             "string  — nombre del título",
        "price_paid":       "string (Decimal)  — precio pagado tras descuento",
        "discount_applied": "integer (0–100)  — descuento que tenía el título en el momento de la compra"
      }
    ]
  },
  "..."
]
```

**Errores:**
| Código | `detail` |
|--------|----------|
| 401 | Token inválido |

---

## Amistades — `/api/friendship`

### `GET /api/friendship/pending`
Solicitudes de amistad **recibidas** y pendientes de respuesta. **Requiere token de customer.**

**Respuesta exitosa:** `200`
```json
[
  {
    "status":     "pending",
    "from_name":  "string | null  — nombre del customer que envió la solicitud",
    "created_at": "string ISO8601 | null"
  },
  "..."
]
```

**Errores:**
| Código | `detail` |
|--------|----------|
| 401 | Token inválido |

---

### `POST /api/friendship/{name}`
Enviar solicitud de amistad a un customer. **Requiere token de customer.**

**Path params:** `name` = nombre del customer destinatario.

**Respuesta exitosa:** `201`
```json
{
  "status":     "pending",
  "from_name":  "string  — nombre del customer que envía (el autenticado)",
  "created_at": "string ISO8601"
}
```

**Errores:**
| Código | `detail` |
|--------|----------|
| 400 | `"No puedes enviarte una solicitud a ti mismo"` |
| 401 | Token inválido |
| 404 | `"Usuario no encontrado"` |
| 409 | `"Ya existe una relación con este usuario"` |

---

### `PATCH /api/friendship/{name}`
Responder o modificar una solicitud de amistad. **Requiere token de customer.**

**Path params:** `name` = nombre del customer con quien existe la relación.

**Body (`application/json`):**
```json
{
  "status": "string  — 'accepted' | 'rejected' | 'blocked'"
}
```

> **Reglas de negocio:**
> - `accepted` y `rejected`: solo el **receptor** de la solicitud puede usarlos.
> - `blocked`: cualquiera de los dos puede bloquear al otro.
> - `rejected` elimina el registro — la respuesta tendrá `created_at: null`.

**Respuesta exitosa:** `200` → `FriendshipShow`
```json
{
  "status":     "string  — el nuevo estado",
  "from_name":  "string | null",
  "created_at": "string ISO8601 | null  — null si status='rejected'"
}
```

**Errores:**
| Código | `detail` |
|--------|----------|
| 401 | Token inválido |
| 404 | `"Usuario no encontrado"` |
| 404 | `"Solicitud de amistad no encontrada"` |
| 422 | `status` no es uno de los valores permitidos |

---

### `DELETE /api/friendship/{name}`
Eliminar una amistad o cancelar una solicitud pendiente, en cualquier estado. **Requiere token de customer.**

**Respuesta exitosa:** `204` — cuerpo vacío.

**Errores:**
| Código | `detail` |
|--------|----------|
| 401 | Token inválido |
| 404 | `"Usuario no encontrado"` |
| 404 | `"Relación no encontrada"` |

---

## Géneros — `/api/genre`

### `GET /api/genre/`
Listado completo de géneros disponibles. **Público.**

**Respuesta exitosa:** `200`
```json
[
  { "name": "string" },
  "..."
]
```
> Cargar una sola vez al iniciar la app y filtrar client-side. Para listar títulos de un género usar `GET /api/title/?genre=RPG`.

---

## Países — `/api/country`

### `GET /api/country/`
Todos los países con su moneda asociada. **Público.** Usar para poblar el selector de país en el registro.

**Respuesta exitosa:** `200`
```json
[
  {
    "name":     "string",
    "en_name":  "string",
    "code":     "string  — código ISO 3166-1 alpha-2",
    "currency": "CurrencyShow | null"
  },
  "..."
]
```

---

### `GET /api/country/{code}`
País por código ISO. **Público.**

**Path params:** `code` = código ISO del país (ej. `ES`, `US`).

**Respuesta exitosa:** `200`
```json
{
  "name":     "string",
  "en_name":  "string",
  "code":     "string",
  "currency": "CurrencyShow | null"
}
```

**Errores:**
| Código | `detail` |
|--------|----------|
| 404 | `"Country no encontrado"` |

---

## Monedas — `/api/currency`

### `GET /api/currency/`
Listado de todas las monedas. **Público.** Las monedas también vienen embebidas en cada `CountryShow`.

**Respuesta exitosa:** `200`
```json
[
  {
    "name":   "string",
    "code":   "string  — código ISO 4217",
    "symbol": "string"
  },
  "..."
]
```

---

## Flujos habituales

### Arranque de la app
```js
// Cargar catálogos estáticos una sola vez al iniciar
const [genres, countries] = await Promise.all([
  fetch('/api/genre/').then(r => r.json()),
  fetch('/api/country/').then(r => r.json()),
])
// Usar countries para el selector de país en registro
// Usar genres para el filtro de catálogo
```

### Registro y login de customer
```js
// 1. Registrar (country_code es OBLIGATORIO)
await fetch('/auth/customer/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'johndoe',
    email: 'john@example.com',
    password: 'Pass123!',
    country_code: 'ES',  // requerido
  }),
})
// 201 → OK | 404 → país no existe | 409 → nombre/email duplicado

// 2. Login
const res = await fetch('/auth/customer/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({ username: 'johndoe', password: 'Pass123!' }),
})
const { access_token, customer, wallet } = await res.json()
localStorage.setItem('token', access_token)
```

### Refrescar sesión de customer
```js
const me = await fetch('/api/customer/me', {
  headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
}).then(r => r.json())
// me.customer: CustomerShow — incluye email y status
// me.wallet:   WalletShow | null — balance en USD
```

### Comprar juegos
```js
// 1. Verificar saldo
const { wallet } = await fetch('/api/customer/me', {
  headers: { Authorization: `Bearer ${token}` },
}).then(r => r.json())

// 2. Recargar si hace falta
await fetch('/api/customer/me/deposit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify({ amount: '20.00' }),
})

// 3. Comprar (transacción atómica — todo o nada)
const receipt = await fetch('/api/transaction/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify({ titles: ['Mi Juego', 'Otro Juego'] }),
}).then(r => r.json())
// { titles_purchased: 2, total_spent: '39.98', wallet_balance: '10.02' }
```

### Perfil público completo de un customer
```js
const [profile, library, friends, reviews] = await Promise.all([
  fetch(`/api/customer/${name}`).then(r => r.json()),           // CustomerPublic
  fetch(`/api/customer/${name}/library`).then(r => r.json()),   // [{ name }]
  fetch(`/api/customer/${name}/friends`).then(r => r.json()),   // [{ name }]
  fetch(`/api/customer/${name}/reviews`).then(r => r.json()),   // ReviewShow[] (con title_name)
])
// Imagen de perfil: <img src={`/api/customer/${name}/image/profile`} />
// Banner:           <img src={`/api/customer/${name}/image/banner`} />
```

### Panel del developer
```js
// Mis títulos (incluyendo pendientes de aprobación)
const myTitles = await fetch('/api/title/me', {
  headers: { Authorization: `Bearer ${devToken}` },
}).then(r => r.json())
// myTitles[i].status === false → pendiente de aprobación admin

// Crear título
const newTitle = await fetch('/api/title/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${devToken}` },
  body: JSON.stringify({
    name: 'Mi Juego',
    release_date: '2025-06-01',
    release_price: '29.99',
    actual_discount: 0,
  }),
}).then(r => r.json())

// Subir media (solo primera vez — capsule, header y store_1 obligatorios)
const form = new FormData()
form.append('capsule', capsuleFile)
form.append('header', headerFile)
form.append('store_1', store1File)
form.append('trailer', trailerFile)  // opcional
await fetch(`/api/title/${encodeURIComponent(newTitle.name)}/media`, {
  method: 'POST',
  headers: { Authorization: `Bearer ${devToken}` },
  body: form,
})
// 204 → OK | 403 → ya existe media, contactar admin

// Actualizar descuento y géneros (reemplaza géneros completos)
await fetch(`/api/title/${encodeURIComponent(newTitle.name)}`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${devToken}` },
  body: JSON.stringify({ actual_discount: 20, genres: ['RPG', 'Aventura'] }),
})
```

### Página de detalle de un juego
```js
const [title, reviews] = await Promise.all([
  fetch(`/api/title/${encodeURIComponent(name)}`).then(r => r.json()),         // TitleShow
  fetch(`/api/title/${encodeURIComponent(name)}/reviews`).then(r => r.json()), // ReviewShow[]
])
// Capsule:   <img src={`/api/title/${name}/media/capsule`} />
// Header:    <img src={`/api/title/${name}/media/header`} />
// Trailer:   <video><source src={`/api/title/${name}/media/trailer`} type="video/mp4" /></video>
// Tienda:    store_1 a store_6 (solo los que existen — manejar 404 en campo vacío)
```

### Gestión de amistades
```js
// Ver solicitudes recibidas
const pending = await fetch('/api/friendship/pending', {
  headers: { Authorization: `Bearer ${token}` },
}).then(r => r.json())
// [{ status: 'pending', from_name: 'johndoe', created_at }]

// Aceptar solicitud
await fetch(`/api/friendship/${pending[0].from_name}`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify({ status: 'accepted' }),
})

// Enviar solicitud
await fetch('/api/friendship/otro_usuario', {
  method: 'POST',
  headers: { Authorization: `Bearer ${token}` },
})

// Eliminar amistad o cancelar solicitud
await fetch(`/api/friendship/${name}`, {
  method: 'DELETE',
  headers: { Authorization: `Bearer ${token}` },
})
```
