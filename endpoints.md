# API Endpoints Reference

Backend FastAPI. Base URL: `http://localhost:8000`

All endpoints return JSON. Binary fields (images, video) are **base64-encoded strings** in JSON responses; send them the same way in requests.

Soft-delete is used for `Customer`, `Developer`, and `Title` — a `DELETE` sets `status = false` instead of removing the row. All `GET` endpoints for those entities filter by `status = true` automatically.

---

## Auth `/auth`

Token JWT sin expiración almacenado en la tabla `token` de la BD. El logout lo **elimina del servidor** — el token queda inválido inmediatamente sin necesidad de expiración.

El login devuelve `{ access_token, token_type, role }`. El campo `role` (`"customer"` | `"developer"`) indica el tipo de sesión — el frontend lo guarda al hacer login y no necesita decodificar el JWT.

Todos los endpoints protegidos requieren el header:
```
Authorization: Bearer <access_token>
```

### Customer

| Method | Path | Body | Returns | Auth |
|--------|------|------|---------|------|
| POST | `/auth/customer/register` | `CustomerCreate` | `CustomerShow` | — |
| POST | `/auth/customer/login` | form `username` + `password` | `TokenResponse` | — |
| GET | `/auth/customer/me` | — | `CustomerShow` | ✅ customer |
| POST | `/auth/customer/logout` | — | `{"detail":"…"}` | ✅ customer |

### Developer

| Method | Path | Body | Returns | Auth |
|--------|------|------|---------|------|
| POST | `/auth/developer/register` | `DeveloperCreate` | `DeveloperShow` | — |
| POST | `/auth/developer/login` | form `username` + `password` | `TokenResponse` | — |
| GET | `/auth/developer/me` | — | `DeveloperShow` | ✅ developer |
| POST | `/auth/developer/logout` | — | `{"detail":"…"}` | ✅ developer |

### TokenResponse
```json
{ "access_token": "<jwt>", "token_type": "bearer", "role": "customer" }
```

> **Login usa `application/x-www-form-urlencoded`**, no JSON. En Swagger aparece como formulario automáticamente. Con `fetch`:
> ```js
> fetch("/auth/customer/login", {
>   method: "POST",
>   headers: { "Content-Type": "application/x-www-form-urlencoded" },
>   body: new URLSearchParams({ username: "email@example.com", password: "secret" })
> })
> ```

---

## Data Model Overview

```
Currency ──< Country ──< Customer >── Image (avatar)
                           │
                           ├──< Wallet ──< Transaction >──< TitleTransaction >── Title
                           │                                                        │
                           ├──< Friendship                                          ├── Media (binary)
                           │                                                        ├── Developer >── Image (avatar)
                           └──< CustomerTitle >── Title                             └──< GenreTitle >── Genre
                                      │
                                      └──< Review
```

---

## Currency `/api/currency`

Stores currency codes (EUR, USD, …).

| Method | Path | Body | Returns | Status |
|--------|------|------|---------|--------|
| POST | `/` | `CurrencyCreate` | `CurrencyShow` | 201 |
| GET | `/` | — | `CurrencyShow[]` | 200 |
| GET | `/{id}` | — | `CurrencyShow` | 200 / 404 |
| GET | `/name/{name}` | — | `CurrencyShow` | 200 / 404 |
| GET | `/code/{code}` | — | `CurrencyShow` | 200 / 404 |
| PATCH | `/{id}` | `CurrencyPatch` | `CurrencyShow` | 200 / 404 |
| PATCH | `/name/{name}` | `CurrencyPatch` | `CurrencyShow` | 200 / 404 |
| PATCH | `/code/{code}` | `CurrencyPatch` | `CurrencyShow` | 200 / 404 |
| DELETE | `/{id}` | — | `{"status":"ok"}` | 200 / 404 |

### CurrencyCreate / CurrencyPatch
```json
{ "name": "Euro", "code": "EUR" }
```

### CurrencyShow
```json
{ "name": "Euro", "code": "EUR" }
```

---

## Country `/api/country`

Stores countries linked to a currency.

| Method | Path | Body | Returns | Status |
|--------|------|------|---------|--------|
| POST | `/` | `CountryCreate` | `CountryShow` | 201 |
| GET | `/` | — | `CountryShow[]` | 200 |
| GET | `/{id}` | — | `CountryShow` | 200 / 404 |
| GET | `/name/{name}` | — | `CountryShow` | 200 / 404 |
| GET | `/code/{code}` | — | `CountryShow` | 200 / 404 |
| PATCH | `/{id}` | `CountryPatch` | `CountryShow` | 200 / 404 |
| PATCH | `/name/{name}` | `CountryPatch` | `CountryShow` | 200 / 404 |
| PATCH | `/code/{code}` | `CountryPatch` | `CountryShow` | 200 / 404 |
| DELETE | `/{id}` | — | `{"status":"ok"}` | 200 / 404 |

### CountryCreate
```json
{ "name": "España", "code": "ES", "currency_id": 1 }
```

### CountryShow
```json
{
  "name": "España",
  "code": "ES",
  "currency": { "name": "Euro", "code": "EUR" }
}
```

---

## Image `/api/image`

Avatar images for customers and developers. Stores URL paths (not binary — see Media for binary game images).

| Method | Path | Body | Returns | Status |
|--------|------|------|---------|--------|
| POST | `/` | `ImageCreate` | `ImageShow` | 201 |
| GET | `/` | — | `ImageShow[]` | 200 |
| GET | `/{id}` | — | `ImageShow` | 200 / 404 |
| PATCH | `/{id}` | `ImagePatch` | `ImageShow` | 200 / 404 |
| DELETE | `/{id}` | — | `{"status":"ok"}` | 200 / 404 |

### ImageCreate / ImagePatch
```json
{ "path_256x256": "https://example.com/avatar_256.jpg", "path_512x512": "https://example.com/avatar_512.jpg" }
```

### ImageShow
```json
{ "path_256x256": "https://...", "path_512x512": "https://..." }
```

---

## Media `/api/media`

Binary game media (capsule, header, screenshots, trailer). `store_2`–`store_6` and `trailer` are nullable.

Two ways to consume media:

- **JSON** (`GET /api/media/{id}`) — all binary fields as base64 strings. Good for images, not recommended for trailers (100 MB+).
- **Streaming** — dedicated endpoints that serve raw bytes with proper `Content-Type`. Use these for `<img src>` and `<video src>` directly.

| Method | Path | Body | Returns | Status |
|--------|------|------|---------|--------|
| POST | `/` | `MediaCreate` | `MediaShow` | 201 |
| GET | `/` | — | `MediaShow[]` | 200 |
| GET | `/{id}` | — | `MediaShow` (base64 JSON) | 200 / 404 |
| GET | `/{id}/image/{field}` | — | `image/jpeg` bytes | 200 / 400 / 404 |
| GET | `/{id}/trailer` | — | `video/mp4` stream | 200 / 206 / 404 |
| PATCH | `/{id}` | `MediaPatch` | `MediaShow` | 200 / 404 |
| DELETE | `/{id}` | — | `{"status":"ok"}` | 200 / 404 |

**`GET /{id}/image/{field}`** — valid `field` values: `capsule`, `header`, `store_1`–`store_6`. Returns raw JPEG bytes.

**`GET /{id}/trailer`** — supports HTTP `Range` header for partial content (status 206). The browser's `<video>` element sends Range requests automatically.

```html
<!-- Images: use the /image/{field} endpoint directly -->
<img src="/api/media/1/image/capsule" />
<img src="/api/media/1/image/header" />

<!-- Trailer: browser sends Range requests, streams efficiently -->
<video controls src="/api/media/1/trailer"></video>
```

### MediaCreate (all values are base64 strings)
```json
{
  "capsule": "<base64>",
  "header": "<base64>",
  "store_1": "<base64>",
  "store_2": "<base64>",
  "store_3": "<base64>",
  "store_4": "<base64>",
  "store_5": "<base64>",
  "store_6": "<base64>",
  "trailer": "<base64>"
}
```

### MediaShow (same structure, all values are base64 strings)

**Frontend usage:**
```js
// Mostrar imagen
<img src={`data:image/jpeg;base64,${media.capsule}`} />
// Mostrar video
<video src={`data:video/mp4;base64,${media.trailer}`} />
```

---

## Genre `/api/genre`

Game genres (Action, Indie, Strategy, …).

| Method | Path | Body | Returns | Status |
|--------|------|------|---------|--------|
| POST | `/` | `GenreCreate` | `GenreShow` | 201 |
| GET | `/` | — | `GenreShow[]` | 200 |
| GET | `/{id}` | — | `GenreShow` | 200 / 404 |
| GET | `/name/{name}` | — | `GenreShow` | 200 / 404 |
| PATCH | `/{id}` | `GenrePatch` | `GenreShow` | 200 / 404 |
| PATCH | `/name/{name}` | `GenrePatch` | `GenreShow` | 200 / 404 |
| DELETE | `/{id}` | — | `{"status":"ok"}` | 200 / 404 |

### GenreCreate / GenrePatch
```json
{ "name": "Action" }
```

### GenreShow
```json
{ "name": "Action" }
```

---

## Developer `/api/developer`

Game studios / developers. Soft-delete (DELETE sets `status = false`). Password is hashed server-side; never returned.
**Registro solo a través de `/api/auth/developer/register`.**

| Method | Path | Body | Returns | Status |
|--------|------|------|---------|--------|
| GET | `/` | — | `DeveloperShow[]` | 200 |
| GET | `/{id}` | — | `DeveloperShow` | 200 / 404 |
| GET | `/name/{name}` | — | `DeveloperShow` | 200 / 404 |
| GET | `/email/{email}` | — | `DeveloperShow` | 200 / 404 |
| GET | `/support_email/{support_email}` | — | `DeveloperShow` | 200 / 404 |
| PATCH | `/{id}` | `DeveloperPatch` | `DeveloperShow` | 200 / 404 |
| PATCH | `/name/{name}` | `DeveloperPatch` | `DeveloperShow` | 200 / 404 |
| PATCH | `/email/{email}` | `DeveloperPatch` | `DeveloperShow` | 200 / 404 |
| PATCH | `/support_email/{support_email}` | `DeveloperPatch` | `DeveloperShow` | 200 / 404 |
| DELETE | `/{id}` | — | `{"status":"ok"}` | 200 / 404 |

### DeveloperCreate
```json
{
  "name": "Valve",
  "email": "contact@valve.com",
  "support_email": "support@valve.com",
  "password": "secret",
  "website_url": "https://valve.com",
  "image_id": 1
}
```

### DeveloperShow
```json
{
  "name": "Valve",
  "email": "contact@valve.com",
  "support_email": "support@valve.com",
  "website_url": "https://valve.com",
  "status": true,
  "image": { "path_256x256": "...", "path_512x512": "..." },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

## Customer `/api/customer`

Platform users. Soft-delete. Password is hashed server-side; never returned.
**Registro solo a través de `/api/auth/customer/register`.**

| Method | Path | Body | Returns | Status |
|--------|------|------|---------|--------|
| GET | `/` | — | `CustomerShow[]` | 200 |
| GET | `/{id}` | — | `CustomerShow` | 200 / 404 |
| GET | `/name/{name}` | — | `CustomerShow` | 200 / 404 |
| GET | `/email/{email}` | — | `CustomerShow` | 200 / 404 |
| PATCH | `/{id}` | `CustomerPatch` | `CustomerShow` | 200 / 404 |
| PATCH | `/name/{name}` | `CustomerPatch` | `CustomerShow` | 200 / 404 |
| PATCH | `/email/{email}` | `CustomerPatch` | `CustomerShow` | 200 / 404 |
| DELETE | `/{id}` | — | `{"status":"ok"}` | 200 / 404 |

### CustomerCreate
```json
{
  "name": "alice99",
  "email": "alice@example.com",
  "password": "secret",
  "country_id": 1,
  "image_id": 5
}
```

### CustomerShow
```json
{
  "name": "alice99",
  "email": "alice@example.com",
  "status": true,
  "country": { "name": "España", "code": "ES", "currency": { "name": "Euro", "code": "EUR" } },
  "image": { "path_256x256": "...", "path_512x512": "..." },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

## Title `/api/title`

Games / titles. Soft-delete. `actual_discount` is an integer (0–100). `release_price` is a decimal string.

| Method | Path | Body | Returns | Status |
|--------|------|------|---------|--------|
| POST | `/` | `TitleCreate` | `TitleShow` | 201 |
| GET | `/` | — | `TitleShow[]` | 200 |
| GET | `/{id}` | — | `TitleShow` | 200 / 404 |
| GET | `/name/{name}` | — | `TitleShow` | 200 / 404 |
| PATCH | `/{id}` | `TitlePatch` | `TitleShow` | 200 / 404 |
| PATCH | `/name/{name}` | `TitlePatch` | `TitleShow` | 200 / 404 |
| DELETE | `/{id}` | — | `{"status":"ok"}` | 200 / 404 |

### TitleCreate
```json
{
  "name": "Half-Life: Alyx",
  "actual_discount": 0,
  "release_date": "2020-03-23",
  "release_price": "59.99",
  "developer_id": 1,
  "media_id": 1
}
```

### TitleShow
```json
{
  "name": "Half-Life: Alyx",
  "status": true,
  "actual_discount": 0,
  "release_date": "2020-03-23",
  "release_price": "59.99",
  "developer": {
    "name": "Valve",
    "email": "contact@valve.com",
    "support_email": "support@valve.com",
    "website_url": "https://valve.com",
    "status": true,
    "image": { "path_256x256": "...", "path_512x512": "..." },
    "created_at": "...", "updated_at": "..."
  },
  "media": {
    "capsule": "<base64>",
    "header": "<base64>",
    "store_1": "<base64>",
    "store_2": "<base64>",
    "store_3": null,
    "store_4": null,
    "store_5": null,
    "store_6": null,
    "trailer": "<base64>"
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

## GenreTitle `/api/genre_title`

Many-to-many link between Genre and Title.

| Method | Path | Body | Returns | Status |
|--------|------|------|---------|--------|
| POST | `/` | `GenreTitleCreate` | `GenreTitleShow` | 201 |
| GET | `/` | — | `GenreTitleShow[]` | 200 |
| GET | `/{id}` | — | `GenreTitleShow` | 200 / 404 |
| PATCH | `/{id}` | `GenreTitlePatch` | `GenreTitleShow` | 200 / 404 |
| DELETE | `/{id}` | — | `{"status":"ok"}` | 200 / 404 |

### GenreTitleCreate
```json
{ "title_id": 1, "genre_id": 3 }
```

### GenreTitleShow
```json
{
  "title_id": 1,
  "genre_id": 3,
  "title": { "name": "Half-Life: Alyx", "status": true, "actual_discount": 0, "release_date": "...", "release_price": "...", "developer": {...}, "media": {...}, "created_at": "...", "updated_at": "..." },
  "genre": { "name": "Action" }
}
```

---

## Wallet `/api/wallet`

One wallet per customer. PK is `customer_id` (not `id`). `balance` is a nullable decimal string.

| Method | Path | Body | Returns | Status |
|--------|------|------|---------|--------|
| POST | `/` | `WalletCreate` | `WalletShow` | 201 |
| GET | `/` | — | `WalletShow[]` | 200 |
| GET | `/{customer_id}` | — | `WalletShow` | 200 / 404 |
| PATCH | `/{customer_id}` | `WalletPatch` | `WalletShow` | 200 / 404 |
| DELETE | `/{customer_id}` | — | `{"status":"ok"}` | 200 / 404 |

### WalletCreate
```json
{ "customer_id": 1, "balance": "150.00" }
```

### WalletShow
```json
{
  "balance": "150.00",
  "customer": { "name": "alice99", "email": "...", "status": true, "country": {...}, "image": {...}, "created_at": "...", "updated_at": "..." },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

## Friendship `/api/friendship`

Friendship between two customers. `status = false` means pending; `status = true` means accepted.

| Method | Path | Body | Returns | Status |
|--------|------|------|---------|--------|
| POST | `/` | `FriendshipCreate` | `FriendshipShow` | 201 |
| GET | `/` | — | `FriendshipShow[]` | 200 |
| GET | `/{id}` | — | `FriendshipShow` | 200 / 404 |
| PATCH | `/{id}` | `FriendshipPatch` | `FriendshipShow` | 200 / 404 |
| DELETE | `/{id}` | — | `{"status":"ok"}` | 200 / 404 |

### FriendshipCreate
```json
{ "customer_id_1": 1, "customer_id_2": 2 }
```

### FriendshipPatch
```json
{ "status": true }
```

### FriendshipShow
```json
{
  "customer_id_1": 1,
  "customer_id_2": 2,
  "status": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

## CustomerTitle `/api/customer_title`

Records that a customer owns a title. `playtime` is in minutes (nullable).

| Method | Path | Body | Returns | Status |
|--------|------|------|---------|--------|
| POST | `/` | `CustomerTitleCreate` | `CustomerTitleShow` | 201 |
| GET | `/` | — | `CustomerTitleShow[]` | 200 |
| GET | `/{id}` | — | `CustomerTitleShow` | 200 / 404 |
| PATCH | `/{id}` | `CustomerTitlePatch` | `CustomerTitleShow` | 200 / 404 |
| DELETE | `/{id}` | — | `{"status":"ok"}` | 200 / 404 |

### CustomerTitleCreate
```json
{ "title_id": 1, "customer_id": 3, "playtime": 120 }
```

### CustomerTitlePatch
```json
{ "playtime": 360 }
```

### CustomerTitleShow
```json
{
  "playtime": 360,
  "title": { "name": "Half-Life: Alyx", ... },
  "customer": { "name": "alice99", ... },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

## Review `/api/review`

Review tied to a `CustomerTitle` (a customer can only review a title they own). `status = false` means pending moderation; `status = true` means published. `recommends` is boolean.

| Method | Path | Body | Returns | Status |
|--------|------|------|---------|--------|
| POST | `/` | `ReviewCreate` | `ReviewShow` | 201 |
| GET | `/` | — | `ReviewShow[]` | 200 |
| GET | `/{id}` | — | `ReviewShow` | 200 / 404 |
| PATCH | `/{id}` | `ReviewPatch` | `ReviewShow` | 200 / 404 |
| DELETE | `/{id}` | — | `{"status":"ok"}` | 200 / 404 |

### ReviewCreate
```json
{
  "customer_title_id": 7,
  "content": "Amazing game!",
  "votes": 0,
  "recommends": true
}
```

### ReviewPatch
```json
{ "content": "Updated review", "recommends": true, "status": true }
```

### ReviewShow
```json
{
  "content": "Amazing game!",
  "votes": 42,
  "recommends": true,
  "status": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

## Transaction `/api/transaction`

A purchase event linked to a wallet (by `wallet_customer_id`). Items bought are in `TitleTransaction`.

| Method | Path | Body | Returns | Status |
|--------|------|------|---------|--------|
| POST | `/` | `TransactionCreate` | `TransactionShow` | 201 |
| GET | `/` | — | `TransactionShow[]` | 200 |
| GET | `/{id}` | — | `TransactionShow` | 200 / 404 |
| PATCH | `/{id}` | `TransactionPatch` | `TransactionShow` | 200 / 404 |
| DELETE | `/{id}` | — | `{"status":"ok"}` | 200 / 404 |

### TransactionCreate
```json
{ "wallet_customer_id": 1 }
```

### TransactionShow
```json
{
  "wallet": { "balance": "150.00", "customer": {...}, "created_at": "...", "updated_at": "..." },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

## TitleTransaction `/api/title_transaction`

Line items of a transaction. Records which title was bought, at what price and with what discount.

| Method | Path | Body | Returns | Status |
|--------|------|------|---------|--------|
| POST | `/` | `TitleTransactionCreate` | `TitleTransactionShow` | 201 |
| GET | `/` | — | `TitleTransactionShow[]` | 200 |
| GET | `/{id}` | — | `TitleTransactionShow` | 200 / 404 |
| PATCH | `/{id}` | `TitleTransactionPatch` | `TitleTransactionShow` | 200 / 404 |
| DELETE | `/{id}` | — | `{"status":"ok"}` | 200 / 404 |

### TitleTransactionCreate
```json
{
  "title_id": 1,
  "transaction_id": 5,
  "price": "49.99",
  "discount": 10
}
```

### TitleTransactionPatch
```json
{ "price": "39.99", "discount": 20 }
```

### TitleTransactionShow
```json
{
  "price": "49.99",
  "discount": 10,
  "title": { "name": "Half-Life: Alyx", ... },
  "transaction": { "wallet": {...}, "created_at": "...", "updated_at": "..." }
}
```

---

## Common Patterns

### Soft-delete entities
`Customer`, `Developer`, `Title` use soft-delete. A `DELETE` request sets `status = false` and returns `{"status": "ok"}`. These records are invisible to all `GET` endpoints but still exist in the database.

### Hard-delete entities
`Currency`, `Country`, `Image`, `Media`, `Genre`, `GenreTitle`, `Wallet`, `Friendship`, `CustomerTitle`, `Review`, `Transaction`, `TitleTransaction` are permanently deleted.

### 404 errors
```json
{ "detail": "Entity with specified ID doesn't exist" }
```

### PATCH semantics
All PATCH endpoints use partial update — only send the fields you want to change. Unset fields are ignored (`exclude_unset=True`).

### Purchase flow (typical sequence)
1. `POST /api/transaction` → create transaction for a customer's wallet
2. `POST /api/title_transaction` × N → attach each title to the transaction
3. `POST /api/customer_title` × N → record ownership
4. `PATCH /api/wallet/{customer_id}` → deduct balance

### Review flow
1. Customer must own the title first (`customer_title` must exist)
2. `POST /api/review` with `customer_title_id`
3. Review starts with `status = false` (pending moderation)
4. `PATCH /api/review/{id}` with `{"status": true}` to publish
