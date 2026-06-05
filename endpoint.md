# API Endpoints — Referencia completa para generación de frontend

## ¿Qué es este proyecto?

**GameStore (Burnt)** es una plataforma de distribución digital de videojuegos inspirada en Steam/GOG.

- **Customers** crean cuentas, recargan su wallet, compran juegos, escriben reviews y agregan amigos.
- **Developers** publican títulos, suben imágenes/trailers y gestionan precios.
- Un **admin** aprueba developers, títulos y reviews desde un panel HTML interno (`/views/`).

---

## Recursos creados automáticamente (triggers PostgreSQL)

Al insertar un `user` → se crea automáticamente `image` (profile y banner vacíos).
Al insertar un `customer` → se crea automáticamente `wallet` (balance = 0.00).
Al insertar un `title` → se crea automáticamente `media` (todos los campos vacíos).

---

## Sistema de autenticación

- Dos tokens **completamente separados**: `customer` y `developer`. No son intercambiables.
- Enviar siempre como `Authorization: Bearer <token>`.
- Usar token equivocado → **403 Forbidden**.
- Usar token revocado (después de logout) → **401 Unauthorized**.
- El logout revoca el token en DB — no basta con borrarlo del cliente.

---

## Reglas globales

- Precios y balances en **USD** como `string (Decimal)` — ej. `"29.99"`. Nunca como número flotante.
- Ninguna respuesta pública expone `id`. Los identificadores son `name`, `email`, `code`.
- Imágenes → `Content-Type: image/jpeg`, usar como `<img src="...">`.
- Trailers → `Content-Type: video/mp4` con soporte `Range`, usar como `<video><source>`.
- Solo las reviews con `status=true` (aprobadas por admin) aparecen en respuestas públicas.
- Títulos con `status=false` (pendientes) no aparecen en el catálogo público.
- `GET /api/title/{name}` y similares devuelven **404** tanto si el título no existe como si está inactivo.

---

## Schemas reutilizables

### `CurrencyShow`
```json
{ "name": "Euro", "code": "EUR", "symbol": "€" }
```

### `CountryShow`
```json
{
  "native_name":  "España",
  "english_name": "Spain",
  "code":         "ES",
  "currency":     "CurrencyShow | null"
}
```

### `WalletShow`
```json
{ "balance": "42.50" }
```
> Siempre existe para customers registrados. Balance inicial: `"0.00"`.

### `CustomerShow` _(privado — solo para el propio customer autenticado)_
```json
{
  "name":       "johndoe",
  "email":      "john@example.com",
  "status":     true,
  "country":    "CountryShow | null",
  "created_at": "2025-01-15T10:30:00+00:00 | null",
  "updated_at": "2025-01-15T10:30:00+00:00 | null"
}
```

### `CustomerPublic` _(perfil público — sin email)_
```json
{
  "name":       "johndoe",
  "country":    "CountryShow | null",
  "created_at": "2025-01-15T10:30:00+00:00 | null",
  "updated_at": "2025-01-15T10:30:00+00:00 | null"
}
```

### `DeveloperShow` _(privado — solo para el propio developer autenticado)_
```json
{
  "name":          "MiEstudio",
  "email":         "acceso@miestudio.com",
  "support_email": "soporte@miestudio.com",
  "website_url":   "https://miestudio.com | null",
  "status":        true,
  "country":       "CountryShow | null",
  "created_at":    "... | null",
  "updated_at":    "... | null"
}
```

### `DeveloperPublic` _(perfil público — sin email privado)_
```json
{
  "name":          "MiEstudio",
  "support_email": "soporte@miestudio.com",
  "website_url":   "https://miestudio.com | null",
  "country":       "CountryShow | null",
  "created_at":    "... | null",
  "updated_at":    "... | null"
}
```

### `GenreShow`
```json
{ "name": "RPG" }
```

### `TitleCard` _(resumen para listados)_
```json
{
  "name":            "A Short Hike",
  "release_price":   "7.99",
  "actual_discount": 20,
  "genres":          [{ "name": "Indie" }],
  "developer_name":  "adamgryu | null"
}
```
> `release_price` es el precio **base sin descuento**. Para el precio final: `release_price × (1 - actual_discount / 100)`.

### `TitleShow` _(detalle completo)_
```json
{
  "name":            "A Short Hike",
  "status":          true,
  "actual_discount": 0,
  "release_date":    "2019-07-30",
  "release_price":   "7.99",
  "genres":          [{ "name": "Adventure" }, { "name": "Indie" }],
  "developer":       "DeveloperPublic | null",
  "owner_count":     42,
  "created_at":      "... | null",
  "updated_at":      "... | null"
}
```
> `release_price` es siempre el precio **base sin descuento** en todos los endpoints. Para mostrar el precio final: `release_price × (1 - actual_discount / 100)`.
> En `GET /api/title/me` (developer): `owner_count` indica cuántos customers tienen el juego. En `GET /api/title/{name}` (público): `owner_count` es `null`.

### `ReviewShow`
```json
{
  "content":       "Juego increíble, muy relajante",
  "recommends":    true,
  "votes":         5,
  "customer_name": "johndoe",
  "title_name":    "A Short Hike",
  "created_at":    "2025-01-15T10:30:00+00:00"
}
```
> `title_name` siempre está presente en todas las respuestas de reviews.

### `FriendshipShow`
```json
{
  "status":     "pending | accepted",
  "from_name":  "johndoe | null",
  "created_at": "... | null"
}
```

---

## Auth — `/auth`

### `POST /auth/customer/register`
**Público.** Crear cuenta de customer.

**Body (`application/json`):**
```json
{
  "name":         "johndoe",
  "email":        "john@example.com",
  "password":     "Pass123!",
  "country_code": "ES"
}
```
> Password: mín. 8 chars, 1 mayúscula, 1 minúscula, 1 número, 1 especial.
> `country_code`: código ISO alpha-2, obtener de `GET /api/country/`.

**Respuesta:** `201` vacío.

**Errores:** `404` país no existe · `409` nombre o email duplicado · `422` validación.

---

### `POST /auth/customer/login`
**Público.** `application/x-www-form-urlencoded`

```
username=johndoe&password=Pass123!
```
> `username` acepta tanto `name` como `email`.

**Respuesta `202`:**
```json
{ "detail": "Código de verificación enviado a tu email" }
```
> No devuelve token. El token se obtiene en `/auth/customer/verify` tras introducir el código recibido por email.

**Errores:** `401` credenciales incorrectas / cuenta inactiva.

---

### `POST /auth/customer/verify`
**Público.** Segundo paso del login — verificar el código OTP recibido por email.

**Body (`application/json`):**
```json
{ "email": "john@example.com", "code": "A3BX" }
```
> `code` es insensible a mayúsculas. Si el código es incorrecto se elimina la sesión OTP y hay que volver a hacer login.

**Respuesta `200`:**
```json
{
  "access_token": "eyJ...",
  "token_type":   "bearer",
  "customer":     "CustomerShow",
  "wallet":       "WalletShow"
}
```
> El código se consume al usarse (se elimina de DB). Para obtener uno nuevo, repetir `POST /auth/customer/login`.

**Errores:** `400` código inválido · `404` usuario no encontrado.

---

### `POST /auth/customer/logout`
**Token de customer.** Revoca el token en DB.

**Respuesta:** `204` vacío.

**Flujo frontend:**
```js
await fetch('/auth/customer/logout', { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
localStorage.removeItem('token')
```

---

### `POST /auth/developer/register`
**Público.**

**Body (`application/json`):**
```json
{
  "name":          "MiEstudio",
  "email":         "acceso@miestudio.com",
  "support_email": "soporte@miestudio.com",
  "password":      "Pass123!",
  "country_code":  "ES",
  "website_url":   "https://miestudio.com"
}
```
> `website_url` es opcional. La cuenta queda `status=false` hasta aprobación del admin.
> Se envía email al admin notificando el nuevo developer.

**Respuesta:** `201` vacío.

**Errores:** `404` país · `409` nombre/email/support_email/website_url duplicados · `422` validación.

---

### `POST /auth/developer/login`
**Público.** `application/x-www-form-urlencoded`

```
username=acceso@miestudio.com&password=Pass123!
```
> Acepta `name` o `email` (no `support_email`). Solo developers con `status=true` pueden entrar.

**Respuesta `202`:**
```json
{ "detail": "Código de verificación enviado a tu email" }
```
> Igual que customer login — el token se obtiene en `/auth/developer/verify`.

**Errores:** `401` credenciales incorrectas / cuenta pendiente de aprobación.

---

### `POST /auth/developer/verify`
**Público.** Segundo paso del login de developer.

**Body (`application/json`):**
```json
{ "email": "acceso@miestudio.com", "code": "A3BX" }
```

**Respuesta `200`:**
```json
{
  "access_token": "eyJ...",
  "token_type":   "bearer",
  "developer":    "DeveloperShow"
}
```

**Errores:** `400` código inválido · `404` usuario no encontrado.

---

### `POST /auth/developer/logout`
**Token de developer.** Igual que customer logout. `204` vacío.

---

## Customers — `/api/customer`

### `GET /api/customer/me`
**Token de customer.** Perfil completo + wallet.

**Respuesta `200`:**
```json
{
  "access_token": "eyJ...",
  "token_type":   "bearer",
  "customer":     "CustomerShow",
  "wallet":       "WalletShow | null"
}
```

---

### `GET /api/customer/`
**Público.** Lista customers activos.

**Query:** `?search=texto` → filtra por `name` o `email` (case-insensitive, parcial).

**Respuesta `200`:** `[CustomerPublic, ...]`

---

### `DELETE /api/customer/me`
**Token de customer.** Desactiva la propia cuenta (`status=false`). El customer deja de aparecer en listados públicos y no puede volver a hacer login hasta que el admin reactive la cuenta.

**Respuesta:** `204` vacío.

---

### `PATCH /api/customer/me`
**Token de customer.** Actualización parcial — enviar solo campos a cambiar.

**Body (`application/json`):**
```json
{
  "name":         "nuevo_nombre | null",
  "email":        "nuevo@email.com | null",
  "password":     "NuevoPass123! | null",
  "country_code": "US | null"
}
```

**Respuesta `200`:** `CustomerShow`

**Errores:** `404` país · `409` nombre/email duplicado · `422` contraseña débil.

---

### `POST /api/customer/me/deposit`
**Token de customer.** Añadir saldo al wallet.

**Body (`application/json`):**
```json
{ "amount": "20.00" }
```

**Respuesta `200`:** `WalletShow`

**Errores:** `400` importe no positivo · `404` wallet no encontrada.

---

### `PATCH /api/customer/me/image`
**Token de customer.** `multipart/form-data`. Al menos uno de los dos campos.

| Campo | Tipo | |
|-------|------|-|
| `profile` | `file` | opcional |
| `banner` | `file` | opcional |

**Respuesta:** `204` vacío.

**Errores:** `400` sin campos · `404` imagen no encontrada.

---

### `GET /api/customer/{name}/image/{field}`
**Público.** Bytes de imagen. `field`: `profile` o `banner`.

**Respuesta:** `200` `image/jpeg` — usar como `<img src="/api/customer/{name}/image/profile">`.

**Errores:** `400` campo inválido · `404` customer no existe/inactivo · `404` campo vacío.

---

### `GET /api/customer/{name}`
**Público.** Perfil público. **Respuesta `200`:** `CustomerPublic`.

---

### `GET /api/customer/{name}/library`
**Público.** Juegos del customer.

**Respuesta `200`:** `[{ "name": "A Short Hike" }, ...]`

> Para mostrar datos extra por juego (si tiene review, si recomienda), cruzar en el front con `GET /api/customer/{name}/reviews` usando `title_name` como clave:
> ```js
> const [library, reviews] = await Promise.all([
>   fetch(`/api/customer/${name}/library`).then(r => r.json()),
>   fetch(`/api/customer/${name}/reviews`).then(r => r.json()),
> ])
> const reviewMap = Object.fromEntries(reviews.map(r => [r.title_name, r]))
> const enriched = library.map(g => ({ ...g, review: reviewMap[g.name] ?? null }))
> // enriched[i].review → { recommends, votes, content, ... } o null si no hay review aprobada
> ```

---

### `GET /api/customer/{name}/friends`
**Público.** Amigos aceptados.

**Respuesta `200`:** `[{ "name": "amigo1" }, ...]`

---

### `GET /api/customer/{name}/reviews`
**Público.** Reviews aprobadas del customer (con `title_name`).

**Respuesta `200`:** `[ReviewShow, ...]` — `title_name` siempre presente.

---

## Developers — `/api/developer`

### `GET /api/developer/me`
**Token de developer.**

**Respuesta `200`:**
```json
{
  "access_token": "eyJ...",
  "token_type":   "bearer",
  "developer":    "DeveloperShow"
}
```

---

### `GET /api/developer/`
**Público.** Lista developers activos.

**Query:** `?search=texto` → filtra por `name` (case-insensitive, parcial).

**Respuesta `200`:** `[DeveloperPublic, ...]`

---

### `PATCH /api/developer/me`
**Token de developer.** Actualización parcial.

**Body (`application/json`):**
```json
{
  "name":          "NuevoNombre | null",
  "email":         "nuevo@acceso.com | null",
  "support_email": "nuevo@soporte.com | null",
  "password":      "NuevoPass123! | null",
  "website_url":   "https://nueva-web.com | null",
  "country_code":  "US | null"
}
```

**Respuesta `200`:** `DeveloperShow`

**Errores:** `404` país · `409` nombre/email/support_email/website_url duplicados.

---

### `PATCH /api/developer/me/image`
**Token de developer.** `multipart/form-data`. Igual que customer image. `204` vacío.

---

### `GET /api/developer/{name}/image/{field}`
**Público.** Igual que customer image. `field`: `profile` o `banner`.

---

### `GET /api/developer/{name}`
**Público.** **Respuesta `200`:** `DeveloperPublic`.

---

## Títulos — `/api/title`

### `GET /api/title/random`
**Público.** Un título activo aleatorio.

**Respuesta `200`:** `TitleCard`

**Errores:** `404` no hay títulos activos.

---

### `GET /api/title/me`
**Token de developer.** Todos los títulos del developer, **incluyendo `status=false`** (pendientes).

**Respuesta `200`:** `[TitleShow, ...]`
> `release_price` es el precio **base sin descuento**. `owner_count` es el número de customers que tienen el juego.

---

### `GET /api/title/`
**Público.** Catálogo activo. Filtros combinables.

**Query:**
| Param | Descripción |
|-------|-------------|
| `search` | Coincidencia parcial en `name` |
| `genre` | Nombre exacto de género, ej. `"RPG"` |
| `developer` | Nombre exacto del developer, ej. `"adamgryu"` |

> Si `genre` o `developer` no existen → devuelve `[]`, no 404.

**Respuesta `200`:** `[TitleCard, ...]`
> `release_price` es el precio **base sin descuento**. El front calcula el precio final con `actual_discount`.

---

### `POST /api/title/`
**Token de developer.** Crear título. El admin debe aprobarlo.

**Body (`application/json`):**
```json
{
  "name":            "Mi Juego",
  "release_date":    "2025-06-01",
  "release_price":   "29.99",
  "actual_discount": 0
}
```
> Se crea con `status=false`. Se envía email al admin. El registro de `media` se crea vacío automáticamente.

**Respuesta `201`:** `TitleShow` con `genres: []`.

---

### `PATCH /api/title/{name}/media`
**Token del developer propietario.** `multipart/form-data`. Sube o actualiza archivos multimedia.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `capsule` | `file` | Miniatura principal (usada en listados) |
| `header` | `file` | Cabecera de la página del juego |
| `store_1`–`store_6` | `file` | Screenshots de la tienda |
| `trailer` | `file` | Video trailer (mp4) |

> Al menos un campo requerido. Reemplaza solo los campos enviados.
> En el frontend, hacer obligatorios `capsule`, `header` y `store_1` en el primer envío.

**Respuesta:** `204` vacío.

**Errores:** `400` sin campos · `404` título no encontrado o no es propietario.

---

### `GET /api/title/{name}/media/{field}`
**Público.** Obtener archivo multimedia de un título activo.

`field`: `capsule` `header` `store_1` `store_2` `store_3` `store_4` `store_5` `store_6` `trailer`

**Respuesta:**
- Imágenes → `200` `image/jpeg`
- Trailer sin `Range` → `200` `video/mp4` con `Accept-Ranges: bytes`
- Trailer con `Range: bytes=0-1048575` → `206` con `Content-Range`, `Content-Length`

```html
<!-- Imágenes -->
<img src="/api/title/{name}/media/capsule">
<!-- Trailer -->
<video><source src="/api/title/{name}/media/trailer" type="video/mp4"></video>
```

**Errores:** `400` campo inválido · `404` título inactivo o campo vacío · `416` range inválido.

---

### `GET /api/title/{name}/reviews`
**Público.** Reviews aprobadas de un título.

**Respuesta `200`:** `[ReviewShow, ...]` — `title_name` siempre presente (igual al nombre del título).

---

### `POST /api/title/{name}/reviews`
**Token de customer.** El customer debe poseer el juego. Se envía email al admin.

**Body (`application/json`):**
```json
{ "content": "Juego increíble", "recommends": true }
```

**Respuesta `201`:** `ReviewShow` — la review queda `status=false` hasta aprobación del admin.

**Errores:** `403` no tienes el juego · `404` título no encontrado · `409` ya tienes una review.

---

### `PATCH /api/title/{name}/reviews/me`
**Token de customer.** Editar propia review.

**Body (`application/json`):**
```json
{ "content": "Actualizado | null", "recommends": true | false | null }
```

**Respuesta `200`:** `ReviewShow`

---

### `POST /api/title/{name}/reviews/{customer_name}/vote`
**Token de customer.** Votar review de otro usuario como útil. No se puede votar la propia.

**Respuesta `200`:** `{ "votes": 6 }`

**Errores:** `400` propia review · `404` título/autor/review no encontrado.

---

### `PATCH /api/title/{name}`
**Token del developer propietario.** Actualizar descuento y/o géneros.

**Body (`application/json`):**
```json
{
  "actual_discount": 20,
  "genres":          ["RPG", "Aventura"]
}
```
> `genres` **reemplaza completamente** los géneros actuales. Enviar `[]` elimina todos.

**Respuesta `200`:** `TitleShow`

**Errores:** `404` título no encontrado o no propietario · `404` género no existe.

---

### `GET /api/title/{name}`
**Público.** Detalle de un título activo.

**Respuesta `200`:** `TitleShow`
> `release_price` es el precio **base sin descuento**. Para el precio final: `release_price × (1 - actual_discount / 100)`.

---

## Transacciones — `/api/transaction`

### `POST /api/transaction/`
**Token de customer.** Compra atómica de uno o varios títulos. Si algo falla, **toda la compra se cancela**.

**Body (`application/json`):**
```json
{ "titles": ["A Short Hike", "Sheepy: A Short Adventure"] }
```

**Respuesta `201`:**
```json
{
  "titles_purchased": 2,
  "total_spent":      "7.99",
  "wallet_balance":   "42.01"
}
```

**Errores:**
| Código | `detail` |
|--------|----------|
| 400 | `"Lista de títulos vacía"` |
| 402 | `"Balance insuficiente"` |
| 404 | `"Wallet no encontrada"` |
| 404 | `"Título 'X' no encontrado o no disponible"` |
| 409 | `"Ya tienes 'X' en tu biblioteca"` |

---

### `GET /api/transaction/me`
**Token de customer.** Historial de compras.

**Respuesta `200`:**
```json
[
  {
    "created_at": "2025-01-15T10:30:00+00:00",
    "titles": [
      { "name": "A Short Hike", "price_paid": "7.99", "discount_applied": 0 }
    ]
  }
]
```

---

## Amistades — `/api/friendship`

### Modelo de amistad

- Solo dos estados: `pending` y `accepted`.
- Para rechazar o bloquear: usar `DELETE` (elimina la relación).
- Solo el **receptor** (no el emisor) puede aceptar.
- Internamente se almacena el `user_id` menor en `customer_user_id_1` y el mayor en `customer_user_id_2`. El emisor se registra en `initiator_id`.

---

### `GET /api/friendship/pending`
**Token de customer.** Solicitudes **recibidas** pendientes.

**Respuesta `200`:** `[FriendshipShow, ...]` — `status` siempre `"pending"`.

---

### `POST /api/friendship/{name}`
**Token de customer.** Enviar solicitud al customer `{name}`.

**Respuesta `201`:** `FriendshipShow` con `status: "pending"`.

**Errores:** `400` a sí mismo · `404` usuario no existe · `409` ya existe relación.

---

### `PATCH /api/friendship/{name}`
**Token de customer.** Aceptar una solicitud recibida. Solo el receptor puede usar este endpoint.

**Body (`application/json`):**
```json
{ "status": "accepted" }
```
> Solo `"accepted"` es válido. Para rechazar, usar `DELETE`.

**Respuesta `200`:** `FriendshipShow`

**Errores:** `403` eres el emisor, no puedes aceptar · `404` solicitud no encontrada · `409` ya procesada.

---

### `DELETE /api/friendship/{name}`
**Token de customer.** Elimina la relación en cualquier estado (cancela solicitudes, elimina amistades).

**Respuesta:** `204` vacío.

**Errores:** `404` relación no encontrada.

---

## Contacto — `/api/contact`

### `POST /api/contact/`
**Token de customer o developer.** Envía un mensaje al admin. El remitente se identifica automáticamente por nombre y rol.

**Body (`application/json`):**
```json
{ "textarea": "Hola, tengo un problema con..." }
```

**Respuesta `201`:**
```json
{ "detail": "Mensaje enviado correctamente" }
```

> El email llega al admin con el formato: `De: johndoe (customer)\n\nMensaje:\n...`

**Errores:** `401` sin token / token inválido / token revocado.

---

## Géneros — `/api/genre`

### `GET /api/genre/`
**Público.** Lista completa de géneros.

**Respuesta `200`:** `[{ "name": "Action" }, { "name": "RPG" }, ...]`

> Cargar una vez al iniciar la app para poblar filtros.

---

## Países — `/api/country`

### `GET /api/country/`
**Público.** Todos los países con su moneda.

**Respuesta `200`:**
```json
[
  {
    "native_name":  "España",
    "english_name": "Spain",
    "code":         "ES",
    "currency":     { "name": "Euro", "code": "EUR", "symbol": "€" }
  }
]
```

### `GET /api/country/{code}`
**Público.** País por código ISO. Mismo objeto. **Errores:** `404`.

---

## Monedas — `/api/currency`

### `GET /api/currency/`
**Público.**

**Respuesta `200`:** `[{ "name": "Euro", "code": "EUR", "symbol": "€" }, ...]`

---

## Stripe — Depósito de saldo — `/api/stripe`

> **Requiere** `STRIPE_SECRET_KEY` en `.env`. Para desarrollo usar una clave de test de Stripe (`sk_test_...`).
> Tarjeta de prueba: `4242 4242 4242 4242` · cualquier fecha futura (ej. `12/34`) · cualquier CVC (ej. `123`).

### `POST /api/stripe/checkout`
**Token de customer.** Inicia una sesión de pago en Stripe Checkout.

**Body (`application/json`):**
```json
{ "amount": "20.00" }
```

**Respuesta `200`:**
```json
{ "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_..." }
```
> El frontend redirige al usuario a `checkout_url`. Stripe muestra la página de pago hosteada.

**Errores:** `400` importe no positivo · `503` Stripe no configurado (falta `STRIPE_SECRET_KEY`).

---

### `GET /api/stripe/success?session_id=cs_test_...`
**Token de customer.** Verificar el pago y acreditar el saldo. Llamar desde el `success_url` configurado.

**Query param:** `session_id` — el ID de sesión de Stripe que llega en la URL de retorno.

**Respuesta `200`:** `WalletShow`
```json
{ "balance": "42.00" }
```
> Verifica con la API de Stripe que `payment_status == "paid"` y que la sesión pertenece al customer autenticado antes de acreditar.

**Errores:** `400` sesión inválida o no verificable · `402` pago no completado · `403` sesión de otro usuario · `404` wallet no encontrada · `503` Stripe no configurado.

---

### Flujo completo de recarga con Stripe (frontend)
```js
// 1. Crear sesión de checkout
const { checkout_url } = await fetch('/api/stripe/checkout', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify({ amount: '20.00' }),
}).then(r => r.json())

// 2. Redirigir al usuario a la página de pago de Stripe
window.location.href = checkout_url
// El usuario paga con la tarjeta de prueba: 4242 4242 4242 4242

// 3. Stripe redirige al success_url configurado, ej:
//    https://tu-front.com/deposit/success?session_id=cs_test_...

// 4. Desde la página de éxito, confirmar con el back:
const wallet = await fetch(`/api/stripe/success?session_id=${sessionId}`, {
  headers: { Authorization: `Bearer ${token}` },
}).then(r => r.json())
// wallet.balance → saldo actualizado tras el pago
```

### Variables de entorno necesarias para Stripe
```env
STRIPE_SECRET_KEY=sk_test_...         # Clave secreta de Stripe (panel Stripe → Developers → API keys)
STRIPE_PUBLISHABLE_KEY=pk_test_...    # Clave pública (para uso futuro en frontend si se usan Stripe Elements)
STRIPE_SUCCESS_URL=http://localhost:3000/deposit/success
STRIPE_CANCEL_URL=http://localhost:3000/deposit/cancel
```

---

## Flujos de frontend

### Arranque de la app
```js
const [genres, countries] = await Promise.all([
  fetch('/api/genre/').then(r => r.json()),
  fetch('/api/country/').then(r => r.json()),
])
// Usar countries[i].code como valor en selects de registro
// Usar countries[i].english_name / native_name para mostrar al usuario
```

### Registro + login de customer (flujo 2FA)
```js
// Registrar
await fetch('/auth/customer/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'johndoe', email: 'john@example.com', password: 'Pass123!', country_code: 'ES' }),
})

// Paso 1 — Login: envía credenciales, recibe 202 (no hay token todavía)
await fetch('/auth/customer/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({ username: 'johndoe', password: 'Pass123!' }),
})
// → el usuario recibe un email con el código de 4 caracteres

// Paso 2 — Verify: envía el código recibido por email
const res = await fetch('/auth/customer/verify', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'john@example.com', code: 'A3BX' }),
})
const { access_token, customer, wallet } = await res.json()
localStorage.setItem('token', access_token)
// customer.name, customer.email, customer.country.english_name
// wallet.balance → "0.00" al inicio
```

### Refrescar sesión
```js
const me = await fetch('/api/customer/me', {
  headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
}).then(r => r.json())
// me.customer.name, me.customer.email, me.wallet.balance
```

### Comprar juegos
```js
// 1a. Recargar saldo con Stripe Checkout (recomendado)
const { checkout_url } = await fetch('/api/stripe/checkout', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify({ amount: '20.00' }),
}).then(r => r.json())
window.location.href = checkout_url   // → el usuario paga → Stripe redirige al success_url

// 1b. Recargar saldo sin Stripe (solo dev/testing)
await fetch('/api/customer/me/deposit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify({ amount: '20.00' }),
})

// 2. Compra atómica
const receipt = await fetch('/api/transaction/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify({ titles: ['A Short Hike', 'Sheepy: A Short Adventure'] }),
}).then(r => r.json())
// receipt.titles_purchased, receipt.total_spent, receipt.wallet_balance
```

### Perfil público de un customer
```js
const [profile, library, friends, reviews] = await Promise.all([
  fetch(`/api/customer/${name}`).then(r => r.json()),         // CustomerPublic
  fetch(`/api/customer/${name}/library`).then(r => r.json()), // [{ name }]
  fetch(`/api/customer/${name}/friends`).then(r => r.json()), // [{ name }]
  fetch(`/api/customer/${name}/reviews`).then(r => r.json()), // ReviewShow[] con title_name
])
// Imagen: <img src={`/api/customer/${name}/image/profile`} />
// Banner: <img src={`/api/customer/${name}/image/banner`} />
```

### Panel del developer
```js
// Mis títulos (incluyendo pendientes status=false)
const myTitles = await fetch('/api/title/me', {
  headers: { Authorization: `Bearer ${devToken}` },
}).then(r => r.json())

// Crear título
const title = await fetch('/api/title/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${devToken}` },
  body: JSON.stringify({ name: 'Mi Juego', release_date: '2025-06-01', release_price: '29.99' }),
}).then(r => r.json())

// Subir media (usar PATCH, hacer capsule/header/store_1 required en el form del frontend)
const form = new FormData()
form.append('capsule', capsuleFile)
form.append('header', headerFile)
form.append('store_1', store1File)
await fetch(`/api/title/${encodeURIComponent(title.name)}/media`, {
  method: 'PATCH',
  headers: { Authorization: `Bearer ${devToken}` },
  body: form,
})
```

### Página de detalle de un juego
```js
const [title, reviews] = await Promise.all([
  fetch(`/api/title/${encodeURIComponent(name)}`).then(r => r.json()),         // TitleShow
  fetch(`/api/title/${encodeURIComponent(name)}/reviews`).then(r => r.json()), // [ReviewShow]
])
// title.release_price → precio base; precio final = release_price * (1 - actual_discount / 100)
// title.developer.name, title.developer.support_email

// Imágenes:
// <img src={`/api/title/${name}/media/capsule`} />
// <img src={`/api/title/${name}/media/header`} />
// store_1 a store_6 → manejar 404 si el campo está vacío

// Trailer:
// <video><source src={`/api/title/${name}/media/trailer`} type="video/mp4" /></video>
```

### Gestión de amistades
```js
// Ver solicitudes recibidas
const pending = await fetch('/api/friendship/pending', {
  headers: { Authorization: `Bearer ${token}` },
}).then(r => r.json())
// [{ status: "pending", from_name: "johndoe", created_at }]

// Aceptar
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

// Eliminar / rechazar
await fetch(`/api/friendship/${name}`, {
  method: 'DELETE',
  headers: { Authorization: `Bearer ${token}` },
})
```

---

## Stripe — Depósito de saldo

> **Pendiente de implementación.** El endpoint `/api/customer/me/deposit` actual acepta directamente un importe sin verificación de pago. Se reemplazará por un flujo Stripe Checkout en modo test.

Flujo previsto:
1. `POST /api/customer/me/deposit/checkout` → crea una Stripe Checkout Session, devuelve `{ checkout_url }`.
2. Frontend redirige a `checkout_url` (página hosteada por Stripe en modo test).
3. Stripe redirige al `success_url` tras el pago.
4. El backend verifica la sesión con la API de Stripe y acredita el balance.

Tarjeta de prueba Stripe: `4242 4242 4242 4242` · cualquier fecha futura · cualquier CVC.
