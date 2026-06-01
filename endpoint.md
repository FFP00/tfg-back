# API Endpoints — Guía de uso para el frontend

> **Reglas globales:**
> - Todos los precios y balances en **USD**. Mostrar en local con `currency.symbol` + tipo de cambio externo.
> - **No se expone `id`** en ninguna respuesta pública. Identificadores: `name`, `email`, `code`.
> - Rutas protegidas requieren `Authorization: Bearer <token>` en la cabecera.
> - `customer` y `developer` tienen tokens separados (bearers distintos).
> - Imágenes se sirven como `image/jpeg` — usar directamente como `src` de `<img>`.
> - Las reviews son moderadas: solo las aprobadas por el admin (`status=true`) aparecen en respuestas públicas.

---

## Auth — `/auth`

### POST `/auth/customer/register`
Crear cuenta de cliente. Público.

```js
fetch('/auth/customer/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'johndoe', email: 'john@example.com', password: 'Pass123!' }),
})
// 201 vacío → redirigir a login
```

### POST `/auth/customer/login`
Login con `name` o `email` + contraseña. Devuelve token + perfil completo + wallet.

```js
const res = await fetch('/auth/customer/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({ username: 'johndoe', password: 'Pass123!' }),
})
const { access_token, customer, wallet } = await res.json()
// customer: { name, email, status, country, created_at, updated_at }
// wallet:   { balance }
localStorage.setItem('token', access_token)
```

### POST `/auth/customer/logout`
Revoca el token. Requiere token de customer.

```js
fetch('/auth/customer/logout', { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
// 204 vacío
```

### POST `/auth/developer/register`
Crear cuenta de developer. Público. La cuenta empieza inactiva hasta que el admin la aprueba.

```js
fetch('/auth/developer/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'MiEstudio',
    email: 'contacto@miestudio.com',
    support_email: 'soporte@miestudio.com',
    password: 'Pass123!',
    website_url: 'https://miestudio.com',  // opcional
  }),
})
// 201 vacío
```

### POST `/auth/developer/login`
Login solo por email. Solo developers activos.

```js
const res = await fetch('/auth/developer/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({ username: 'contacto@miestudio.com', password: 'Pass123!' }),
})
const { access_token, developer } = await res.json()
// developer: { name, email, support_email, website_url, status, created_at, updated_at }
```

### POST `/auth/developer/logout`
Revoca el token de developer.

---

## Clientes — `/api/customer`

### GET `/api/customer/me`
Perfil completo del cliente autenticado + wallet. Requiere token de customer.

```js
const { customer, wallet } = await fetch('/api/customer/me', {
  headers: { Authorization: `Bearer ${token}` },
}).then(r => r.json())
// customer: { name, email, status, country, created_at, updated_at }
// wallet:   { balance }
```

### GET `/api/customer/`
Listado de clientes activos. Búsqueda opcional por `name` o `email`. Público. El email NO se expone.

```js
fetch('/api/customer/?search=john')
// [{ name, country, created_at, updated_at }, ...]
```

### PATCH `/api/customer/me`
Actualizar perfil propio. Enviar solo los campos a cambiar. Requiere token de customer.

```js
fetch('/api/customer/me', {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify({
    name: 'nuevo_nombre',      // opcional
    email: 'nuevo@mail.com',  // opcional
    password: 'NuevaPass1!',  // opcional
    country_code: 'ES',       // opcional — código ISO del país
  }),
})
// { name, email, status, country, created_at, updated_at }
```

### POST `/api/customer/me/deposit`
Añadir saldo al wallet. Requiere token de customer.

```js
fetch('/api/customer/me/deposit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify({ amount: '10.00' }),
})
// { balance: '25.50' }
```

### PATCH `/api/customer/me/image`
Subir/actualizar imagen de perfil o banner. Multipart. Requiere token.

```js
const form = new FormData()
form.append('profile', fileInput.files[0])   // opcional
form.append('banner', bannerInput.files[0])  // opcional — al menos uno requerido
fetch('/api/customer/me/image', {
  method: 'PATCH',
  headers: { Authorization: `Bearer ${token}` },
  body: form,
})
// 204 vacío
```

### GET `/api/customer/{name}/image/{field}`
Imagen del cliente. `field`: `profile` o `banner`. Público.

```html
<img src="/api/customer/johndoe/image/profile" />
<img src="/api/customer/johndoe/image/banner" />
```

### GET `/api/customer/{name}`
Perfil público. Sin email. Público.

```js
fetch('/api/customer/johndoe')
// { name, country, created_at, updated_at }
```

### GET `/api/customer/{name}/library`
Biblioteca de juegos del cliente. Público.

```js
fetch('/api/customer/johndoe/library')
// [{ name }, ...]
```

### GET `/api/customer/{name}/friends`
Amigos aceptados. Público.

```js
fetch('/api/customer/johndoe/friends')
// [{ name }, ...]
```

### GET `/api/customer/{name}/reviews`
Reviews aprobadas del cliente. Incluye `title_name`. Público.

```js
fetch('/api/customer/johndoe/reviews')
// [{ content, recommends, votes, customer_name, created_at, title_name }, ...]
```

---

## Developers — `/api/developer`

### GET `/api/developer/me`
Perfil completo del developer autenticado. Requiere token de developer.

```js
const { developer } = await fetch('/api/developer/me', {
  headers: { Authorization: `Bearer ${devToken}` },
}).then(r => r.json())
// { name, email, support_email, website_url, status, created_at, updated_at }
```

### GET `/api/developer/`
Listado de developers activos. Búsqueda por nombre. Público. El email privado NO se expone.

```js
fetch('/api/developer/?search=indie')
// [{ name, support_email, website_url, created_at, updated_at }, ...]
```

### PATCH `/api/developer/me`
Actualizar perfil. Requiere token de developer.

```js
fetch('/api/developer/me', {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${devToken}` },
  body: JSON.stringify({
    name: 'NuevoEstudio',
    support_email: 'nuevo@studio.com',
    website_url: 'https://nuevo.com',
    password: 'NuevaPass1!',
  }),
})
// { name, email, support_email, website_url, status, created_at, updated_at }
```

### PATCH `/api/developer/me/image`
Subir imagen de perfil/banner. Multipart. Requiere token de developer.

```js
const form = new FormData()
form.append('profile', file)
form.append('banner', banner)
fetch('/api/developer/me/image', {
  method: 'PATCH',
  headers: { Authorization: `Bearer ${devToken}` },
  body: form,
})
// 204 vacío
```

### GET `/api/developer/{name}/image/{field}`
Imagen del developer. `field`: `profile` o `banner`. Público.

```html
<img src="/api/developer/MiEstudio/image/profile" />
```

### GET `/api/developer/{name}`
Perfil público del developer. Sin email privado. Público.

```js
fetch('/api/developer/MiEstudio')
// { name, support_email, website_url, created_at, updated_at }
```

---

## Títulos — `/api/title`

### GET `/api/title/random`
Un título aleatorio activo. Público.

```js
fetch('/api/title/random')
// { name, release_price, actual_discount, genres, developer_name }
```

### GET `/api/title/me`
Todos los títulos del developer autenticado, incluyendo pendientes (`status=false`). Requiere token de developer.

```js
fetch('/api/title/me', { headers: { Authorization: `Bearer ${devToken}` } })
// [{ name, status, actual_discount, release_date, release_price, genres, developer, ... }, ...]
```

### GET `/api/title/`
Catálogo de títulos activos. Filtros opcionales. Público.

```js
fetch('/api/title/?search=zelda&genre=RPG&developer=Nintendo')
// [{ name, release_price, actual_discount, genres, developer_name }, ...]
```

### POST `/api/title/`
Crear título. Requiere token de developer. Queda en `status=false` hasta aprobación del admin.

```js
fetch('/api/title/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${devToken}` },
  body: JSON.stringify({
    name: 'Mi Juego',
    release_date: '2025-06-01',
    release_price: '29.99',
    actual_discount: 0,
  }),
})
// 201 → { name, status, actual_discount, release_date, release_price, genres, developer, ... }
```

### POST `/api/title/{name}/media`
Subir media del juego por primera vez. Requiere token del developer propietario.
- Solo disponible si el juego **no tiene media aún**. Una vez subida, contactar al admin para cambios.
- `capsule`, `header` y `store_1` son obligatorios. El resto opcional.

```js
const form = new FormData()
form.append('capsule', capsuleFile)   // obligatorio
form.append('header', headerFile)     // obligatorio
form.append('store_1', store1File)    // obligatorio
form.append('store_2', store2File)    // opcional
form.append('trailer', trailerFile)   // opcional (mp4)
fetch(`/api/title/${encodeURIComponent(name)}/media`, {
  method: 'POST',
  headers: { Authorization: `Bearer ${devToken}` },
  body: form,
})
// 204 vacío
// 403 si ya existe media → contactar al administrador
```

### GET `/api/title/{name}/media/{field}`
Archivo del título. `field`: `capsule`, `header`, `store_1`–`store_6`, `trailer`. Público.
- Imágenes: respuesta directa `image/jpeg`.
- `trailer`: streaming con soporte de `Range` para HTML5 `<video>`.

```html
<img src="/api/title/Mi%20Juego/media/capsule" />
<img src="/api/title/Mi%20Juego/media/header" />

<video controls>
  <source src="/api/title/Mi%20Juego/media/trailer" type="video/mp4" />
</video>
```

### GET `/api/title/{name}/reviews`
Reviews aprobadas del título. Público.

```js
fetch('/api/title/Mi%20Juego/reviews')
// [{ content, recommends, votes, customer_name, created_at }, ...]
```

### POST `/api/title/{name}/reviews`
Publicar review. El cliente debe tener el juego. Queda pendiente de aprobación. Requiere token de customer.

```js
fetch('/api/title/Mi%20Juego/reviews', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify({ content: 'Muy buen juego', recommends: true }),
})
// 201 → { content, recommends, votes, customer_name, created_at }
```

### PATCH `/api/title/{name}/reviews/me`
Editar tu propia review. Requiere token de customer.

```js
fetch('/api/title/Mi%20Juego/reviews/me', {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify({ content: 'Actualizo mi opinión', recommends: false }),
})
// { content, recommends, votes, customer_name, created_at }
```

### POST `/api/title/{name}/reviews/{customer_name}/vote`
Votar la review de otro cliente. No puedes votar la tuya. Requiere token de customer.

```js
fetch('/api/title/Mi%20Juego/reviews/johndoe/vote', {
  method: 'POST',
  headers: { Authorization: `Bearer ${token}` },
})
// { votes: 5 }
```

### PATCH `/api/title/{name}`
Actualizar discount y/o géneros. Requiere token del developer propietario.

```js
fetch('/api/title/Mi%20Juego', {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${devToken}` },
  body: JSON.stringify({
    actual_discount: 20,            // opcional
    genres: ['RPG', 'Aventura'],   // opcional — reemplaza todos los géneros
  }),
})
// { name, status, actual_discount, release_date, release_price, genres, developer, ... }
```

### GET `/api/title/{name}`
Detalle completo del título. Público.

```js
fetch('/api/title/Mi%20Juego')
// {
//   name, status, actual_discount, release_date, release_price,
//   genres: [{ name }],
//   developer: { name, support_email, website_url, created_at, updated_at },
//   created_at, updated_at
// }
```

---

## Transacciones — `/api/transaction`

### POST `/api/transaction/`
Compra atómica de uno o varios títulos. Requiere token de customer.
- `402` → balance insuficiente
- `409` → título ya en biblioteca
- `404` → título no existe o no activo

```js
fetch('/api/transaction/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify({ titles: ['Mi Juego', 'Otro Juego'] }),
})
// 201 → { titles_purchased: 2, total_spent: '39.98', wallet_balance: '10.02' }
```

### GET `/api/transaction/me`
Historial de compras. Requiere token de customer.

```js
fetch('/api/transaction/me', { headers: { Authorization: `Bearer ${token}` } })
// [{ created_at: '2025-01-15T10:30:00Z', titles: [{ name, price_paid, discount_applied }] }, ...]
```

---

## Amistades — `/api/friendship`

### GET `/api/friendship/pending`
Solicitudes recibidas pendientes. Requiere token de customer.

```js
fetch('/api/friendship/pending', { headers: { Authorization: `Bearer ${token}` } })
// [{ status: 'pending', from_name: 'johndoe', created_at }, ...]
```

### POST `/api/friendship/{name}`
Enviar solicitud. Requiere token de customer.

```js
fetch('/api/friendship/johndoe', {
  method: 'POST',
  headers: { Authorization: `Bearer ${token}` },
})
// 201 → { status: 'pending', from_name: 'mi_nombre', created_at }
```

### PATCH `/api/friendship/{name}`
Responder solicitud. Solo el **receptor** puede aceptar o rechazar. Cualquiera puede bloquear. Requiere token de customer.

```js
fetch('/api/friendship/johndoe', {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify({ status: 'accepted' }),  // 'accepted' | 'rejected' | 'blocked'
})
// { status, from_name, created_at }
// rejected → registro eliminado (from_name sin created_at)
```

### DELETE `/api/friendship/{name}`
Eliminar amistad o cancelar solicitud. Cualquier estado. Requiere token de customer.

```js
fetch('/api/friendship/johndoe', {
  method: 'DELETE',
  headers: { Authorization: `Bearer ${token}` },
})
// 204 vacío
```

---

## Géneros — `/api/genre`

### GET `/api/genre/`
Listado completo de géneros. Cargar una vez y filtrar client-side. Público.

```js
fetch('/api/genre/')
// [{ name }, ...]
```

> Para cargar títulos de un género concreto usa el filtro de título: `GET /api/title/?genre=RPG`

---

## Países — `/api/country`

### GET `/api/country/`
Todos los países con su moneda. Público.

```js
fetch('/api/country/')
// [{ name, en_name, code, currency: { name, code, symbol } }, ...]
```

### GET `/api/country/{code}`
País por código ISO. Público.

```js
fetch('/api/country/ES')
// { name, en_name, code, currency: { name, code, symbol } }
```

---

## Monedas — `/api/currency`

### GET `/api/currency/`
Listado de monedas. Público. Las monedas también vienen embebidas en cada país.

```js
fetch('/api/currency/')
// [{ name, code, symbol }, ...]
```

---

## Flujos habituales

### Arranque de la app
```js
// Cargar catálogos una sola vez al iniciar
const [genres, countries, currencies] = await Promise.all([
  fetch('/api/genre/').then(r => r.json()),
  fetch('/api/country/').then(r => r.json()),
  fetch('/api/currency/').then(r => r.json()),
])
```

### Login y perfil propio
```js
const { access_token, customer, wallet } = await fetch('/auth/customer/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({ username: 'johndoe', password: 'Pass123!' }),
}).then(r => r.json())
localStorage.setItem('token', access_token)

// Refrescar perfil en cualquier momento
const me = await fetch('/api/customer/me', {
  headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
}).then(r => r.json())
// me.customer.email disponible (solo en /me, no en endpoints públicos)
// me.wallet.balance disponible
```

### Comprar juegos
```js
// 1. Comprobar saldo
const { wallet } = await fetch('/api/customer/me', { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json())

// 2. Recargar si falta saldo
if (wallet.balance < totalNeeded) {
  await fetch('/api/customer/me/deposit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ amount: '20.00' }),
  })
}

// 3. Comprar
const receipt = await fetch('/api/transaction/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify({ titles: ['Mi Juego'] }),
}).then(r => r.json())
// { titles_purchased, total_spent, wallet_balance }
```

### Perfil público de un usuario
```js
const [profile, library, friends, reviews] = await Promise.all([
  fetch(`/api/customer/${name}`).then(r => r.json()),
  fetch(`/api/customer/${name}/library`).then(r => r.json()),
  fetch(`/api/customer/${name}/friends`).then(r => r.json()),
  fetch(`/api/customer/${name}/reviews`).then(r => r.json()),
])
// reviews[i].title_name → nombre del juego de cada review
```

### Panel del developer
```js
// Mis títulos (incluyendo pendientes)
const myTitles = await fetch('/api/title/me', {
  headers: { Authorization: `Bearer ${devToken}` },
}).then(r => r.json())
// title.status === false → pendiente de aprobación admin

// Crear título
await fetch('/api/title/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${devToken}` },
  body: JSON.stringify({ name, release_date, release_price }),
})

// Subir media (solo primera vez — capsule, header y store_1 obligatorios)
const form = new FormData()
form.append('capsule', capsuleFile)
form.append('header', headerFile)
form.append('store_1', store1File)
await fetch(`/api/title/${encodeURIComponent(name)}/media`, {
  method: 'POST',
  headers: { Authorization: `Bearer ${devToken}` },
  body: form,
})
// 403 si ya existe media → contactar al administrador
```

### Gestión de amistades
```js
// Solicitudes recibidas
const pending = await fetch('/api/friendship/pending', {
  headers: { Authorization: `Bearer ${token}` },
}).then(r => r.json())

// Aceptar solicitud
await fetch(`/api/friendship/${pending[0].from_name}`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify({ status: 'accepted' }),
})

// Eliminar / cancelar
await fetch(`/api/friendship/${name}`, {
  method: 'DELETE',
  headers: { Authorization: `Bearer ${token}` },
})
```
