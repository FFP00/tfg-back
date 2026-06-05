# Contexto — Debate Redis cache para imágenes (GameStore Burnt)

## El problema
Cada `GET /api/title/{name}/media/header` (y similares) hace una query a PostgreSQL,
deserializa el bytea y transfiere los bytes. Con usuarios concurrentes = N queries idénticas.

## Endpoints candidatos a cachear
- `GET /api/title/{name}/media/{field}` — capsule, header, store_1..6, trailer
- `GET /api/customer/{name}/image/{field}` — profile, banner
- `GET /api/developer/{name}/image/{field}` — profile, banner

## Decisión ya tomada
- **Redis puro cache, sin persistencia** — si cae, las imágenes se recachean solas en el siguiente request. Sin volumen en Docker.
- En docker-compose: `image: redis:7-alpine`, sin volumen, `restart: unless-stopped`
- Variable de entorno: `REDIS_URL=redis://redis:6379`

## Las 4 opciones debatidas (pendiente elegir)

### A — Redis como Depends (patrón del proyecto)
Crea `get_redis()` en `app/config/redis.py` igual que `get_session()`.
Cada ruta de imagen busca en Redis → miss → DB → guarda en Redis.
Invalidación explícita (`r.delete(key)`) en los PATCH de media/image.
**~60-80 líneas, ~2h. Recomendada.**

### B — fastapi-cache2 con @cache()
Decorador encima de cada endpoint. Mínimo código pero abstracción opaca.
Tiene quirks con `StreamingResponse` (el trailer de vídeo).
**~20 líneas, 30min.**

### C — Solo HTTP headers (ETag / Cache-Control)
Sin Redis. El navegador cachea por cliente. 304 si el recurso no cambió.
No resuelve carga concurrente entre usuarios distintos (todos golpean DB la primera vez).
**~30 líneas, 1h. Zero infraestructura.**

### D — Redis + HTTP headers
Opción A + cabeceras ETag. Redis cross-user, ETag evita retransferencia al navegador.
**~80-100 líneas, ~2.5h. La más completa.**

## Estado
Conversación pausada antes de elegir opción e implementar.
Al retomar: elegir A/B/C/D y arrancar implementación.
