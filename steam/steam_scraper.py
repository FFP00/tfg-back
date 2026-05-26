#!/usr/bin/env python3
"""
Steam Games Data Scraper  v2
=============================
Uso:
    python steam_scraper.py                      # 1000 juegos
    python steam_scraper.py --count 500
    python steam_scraper.py --count 100 --output datos.json
    python steam_scraper.py --resume             # continúa si se cortó
    python steam_scraper.py --clear-cache        # borra caché de lista

Estrategia de resiliencia:
  1. App-list → intenta 3 endpoints distintos de Steam, con caché en disco.
  2. App-details → store.steampowered.com (más estable que api.steampowered.com).
  3. Checkpoint → guarda progreso cada 25 juegos; --resume lo recupera.
  4. Backoff exponencial en 429/502/503.
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── URLs ──────────────────────────────────────────────────────────────────────
# Lista de apps: varios endpoints, se prueban en orden
APP_LIST_URLS = [
    "https://api.steampowered.com/ISteamApps/GetAppList/v2/",
    "https://store.steampowered.com/api/applist/v2/",          # mismo datos, distinto host
    # Fallback: IDs de los ~1 000 juegos más jugados por historia (seed estático)
]

APP_DETAIL_URL = "https://store.steampowered.com/api/appdetails"
STEAM_CDN      = "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps"

CDN = {
    # Campos solicitados
    "library_capsule_image2x": "{base}/{id}/library_600x900.jpg",    # library_capsule → image2x
    "library_header_image2x":  "{base}/{id}/library_hero_2x.jpg",    # library_header  → image2x
    # Extras para columnas de BD (image / media)
    "capsule_sm":              "{base}/{id}/capsule_231x87.jpg",
    "capsule_lg":              "{base}/{id}/capsule_616x353.jpg",
    "library_600x900":         "{base}/{id}/library_600x900.jpg",
}

# Archivos locales
CACHE_FILE      = Path("steam_applist_cache.json")
CHECKPOINT_FILE = Path("steam_checkpoint.json")

DEFAULT_COUNT  = 1000
DEFAULT_DELAY  = 1.2
DEFAULT_OUTPUT = "steam_games.json"

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("steam")


# ── Seed estático de appids populares (fallback si la API de lista falla) ─────
# Top juegos por jugadores históricos — suficiente para arrancar
SEED_APPIDS = [
    10, 20, 30, 40, 50, 60, 70, 80, 100, 130, 220, 240, 300, 320, 340, 360,
    380, 400, 420, 440, 500, 550, 570, 620, 630, 730, 750, 1000, 1250, 1500,
    2200, 2280, 2300, 2320, 2400, 2430, 2450, 3830, 4000, 4540, 7600, 7670,
    8190, 8980, 9420, 10090, 10180, 10500, 12110, 12120, 12150, 12200, 12210,
    12220, 12250, 13140, 13180, 13200, 13210, 14700, 15100, 17300, 17390,
    17410, 17450, 17480, 17500, 17510, 17520, 17530, 17540, 17550, 17560,
    17570, 17580, 18010, 18020, 19900, 20920, 21000, 22200, 22300, 22330,
    22350, 22370, 22380, 22490, 22600, 33230, 34010, 35140, 35720, 36120,
    38400, 39140, 39210, 40700, 41070, 41080, 42690, 42700, 42710, 42720,
    42730, 42750, 42760, 42780, 42800, 43100, 43110, 43120, 43130, 49520,
    55230, 55240, 57690, 63380, 65800, 65810, 72850, 76600, 91310, 92100,
    93200, 96500, 105450, 107200, 113020, 113400, 116600, 201810, 203160,
    205100, 206480, 208090, 211820, 218620, 219150, 219990, 221100, 221540,
    222480, 224260, 224760, 225140, 226560, 230230, 231430, 232050, 233450,
    234140, 234390, 238010, 238430, 239140, 239160, 240720, 242530, 242760,
    248820, 250180, 250600, 250760, 251150, 252490, 252770, 253230, 255710,
    257350, 257420, 258980, 261030, 261210, 263730, 264710, 266210, 267500,
    271590, 273110, 275390, 277850, 282070, 282900, 287120, 291480, 292030,
    295110, 299740, 301520, 304930, 304050, 311120, 316010, 317400, 320760,
    321360, 322330, 326460, 327800, 328080, 329500, 332800, 335300, 337000,
    346110, 347170, 359550, 362300, 362930, 363970, 365450, 367500, 374320,
    378648, 381210, 383120, 386360, 387290, 391540, 391220, 393380, 394360,
    404920, 410900, 413150, 413410, 418370, 427520, 431240, 431960, 435150,
    437220, 438100, 444090, 444200, 454650, 457140, 460790, 462310, 465700,
    466240, 475190, 476600, 489520, 489830, 494840, 495570, 497010, 517630,
    526870, 534380, 534480, 548430, 548580, 553850, 559100, 562100, 570940,
    578080, 582010, 588650, 588870, 594570, 601150, 606470, 611500, 614910,
    620, 632360, 632470, 640820, 644930, 648010, 651670, 652390, 658920,
    703080, 703090, 730, 739630, 742420, 752590, 762960, 787420, 794600,
    812140, 813780, 822690, 837470, 846470, 863550, 872500, 892970, 906850,
    920210, 945360, 976310, 1085660, 1091500, 1110560, 1118310, 1144200,
    1161580, 1172380, 1174180, 1174490, 1182480, 1203220, 1245620, 1250410,
    1282080, 1325200, 1332010, 1336490, 1343400, 1361210, 1382330, 1426210,
    1449560, 1449570, 1449580, 1466060, 1468010, 1476210, 1493710, 1502590,
    1517290, 1551360, 1557740, 1568590, 1593500, 1604030, 1659420, 1672970,
    1680880, 1687950, 1690800, 1817070, 1818450, 1839880, 1840080, 1880700,
    1904540, 1938090, 1971460, 2000300, 2050650, 2138710, 2183900, 2217000,
    2358720, 2379780, 2399830, 2456290, 2480740, 2519060, 2623190, 2677660,
]


# ── HTTP Session ──────────────────────────────────────────────────────────────
def build_session() -> requests.Session:
    session = requests.Session()
    # NO ponemos 502 en status_forcelist — lo manejamos nosotros con backoff
    retry = Retry(
        total=2,
        backoff_factor=1.5,
        status_forcelist=[429, 503],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    })
    return session


def get_json(session: requests.Session, url: str, params: dict = None,
             timeout: int = 20, max_attempts: int = 5) -> dict | None:
    """GET con backoff exponencial manual para 502/503/429."""
    for attempt in range(1, max_attempts + 1):
        try:
            r = session.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 502, 503):
                wait = 2 ** attempt          # 2, 4, 8, 16, 32 s
                log.warning("HTTP %s → esperando %ss (intento %s/%s)",
                            r.status_code, wait, attempt, max_attempts)
                time.sleep(wait)
                continue
            # 404, 400, etc. → no reintenta
            log.debug("HTTP %s para %s", r.status_code, url)
            return None
        except (requests.ConnectionError, requests.Timeout) as e:
            wait = 2 ** attempt
            log.warning("Conexión fallida (%s) → reintentando en %ss", e, wait)
            time.sleep(wait)
    return None


# ── App list con caché y múltiples fuentes ────────────────────────────────────
STORE_SEARCH_URL = "https://store.steampowered.com/search/results/"

def fetch_app_list_via_search(session: requests.Session, target: int = 2000) -> list[dict]:
    """
    Obtiene juegos populares de la Steam Store ordenados por nº de reviews.
    - sort_by=Reviews_DESC  → los más valorados/conocidos primero
    - maxprice=99999        → incluye free-to-play y de pago
    - mature_content=0      → excluye contenido +18
    """
    apps  = []
    start = 0
    log.info("Obteniendo lista vía Steam Store Search (objetivo: ~%s)…", target)
    while len(apps) < target:
        params = {
            "json":           "1",
            "filter":         "games",
            "sort_by":        "Reviews_DESC",   # más conocidos primero
            "maxprice":       "99999",
            "mature_content": "0",              # sin +18
            "start":          start,
            "count":          100,
        }
        data = get_json(session, STORE_SEARCH_URL, params=params, timeout=20, max_attempts=3)
        if not data:
            log.warning("Store search no respondió en start=%s", start)
            break
        items = data.get("items", [])
        if not items:
            break
        for item in items:
            logo = item.get("logo", "") or ""
            m = re.search(r"/apps/(\d+)/", logo)
            if m:
                apps.append({"appid": int(m.group(1)), "name": item.get("name", "")})
        start += 100
        log.info("  Store search: %s IDs recogidos…", len(apps))
        time.sleep(0.5)
    return apps


def load_app_list(session: requests.Session, force_refresh: bool = False, needed: int = 1000) -> list[dict]:
    # 1) Caché en disco (la lista ya viene ordenada por popularidad)
    if not force_refresh and CACHE_FILE.exists():
        age_h = (time.time() - CACHE_FILE.stat().st_mtime) / 3600
        cached = json.loads(CACHE_FILE.read_text())
        if age_h < 24 and len(cached) >= needed:
            log.info("Lista cargada desde caché (%s apps, %.1fh de antigüedad)", len(cached), age_h)
            return cached
        log.info("Caché insuficiente o expirada, actualizando…")

    # 2) Steam Store Search ordenada por Reviews_DESC (más populares primero) — fuente primaria
    apps = fetch_app_list_via_search(session, target=max(needed * 4, 2000))
    if apps:
        CACHE_FILE.write_text(json.dumps(apps))
        log.info("Lista vía Store Search: %s apps → guardada en caché", len(apps))
        return apps

    # 3) Fallback: endpoints GetAppList (sin orden de popularidad)
    for url in APP_LIST_URLS:
        log.info("Probando fuente de lista: %s", url)
        data = get_json(session, url, timeout=30, max_attempts=3)
        if data:
            apps = data.get("applist", {}).get("apps", [])
            if apps:
                apps = [a for a in apps if a.get("name", "").strip()]
                CACHE_FILE.write_text(json.dumps(apps))
                log.info("Lista obtenida: %s apps → guardada en caché", f"{len(apps):,}")
                return apps

    # 4) Último recurso: seed estático
    log.warning("Todos los endpoints fallaron → seed estático (%s appids)", len(SEED_APPIDS))
    return [{"appid": aid, "name": ""} for aid in SEED_APPIDS]


# ── Detalles de una app ───────────────────────────────────────────────────────
def fetch_details(session: requests.Session, appid: int) -> dict | None:
    # Sin "filters" para recibir la respuesta completa incluyendo "icon"
    data = get_json(
        session, APP_DETAIL_URL,
        params={"appids": appid, "cc": "us", "l": "english"},
    )
    if not data:
        return None
    app_data = data.get(str(appid), {})
    if not app_data.get("success"):
        return None
    d = app_data.get("data", {})

    if d.get("type") != "game":
        return None
    # Sin contenido +18 (el campo puede ser int o string)
    if int(d.get("required_age", 0) or 0) >= 18:
        return None
    # Debe tener desarrollador
    if not d.get("developers"):
        return None
    # Filtra juegos y developers con caracteres no latinos
    # (cirílico, árabe, devanagari, CJK, hangul, etc.)
    _NON_LATIN = re.compile(
        r"[\u0400-\u04FF\u0600-\u06FF\u0900-\u097F\u3000-\u9FFF\uAC00-\uD7AF\uF900-\uFAFF]"
    )
    if _NON_LATIN.search(d.get("name", "")):
        log.debug("Skipped appid=%s (juego no latino: %s)", appid, d.get("name"))
        return None
    dev_name = d.get("developers", [""])[0]
    if _NON_LATIN.search(dev_name):
        log.debug("Skipped appid=%s (developer no latino: %s)", appid, dev_name)
        return None

    return d


# ── CDN helpers ───────────────────────────────────────────────────────────────
FASTLY = "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps"
COMMUNITY_CDN = "https://cdn.akamai.steamstatic.com/steamcommunity/public/images/apps"

def cdn(key: str, appid: int) -> str:
    return CDN[key].format(base=STEAM_CDN, id=appid)

def icon_url(appid: int, icon_hash: str) -> str | None:
    """Icono cuadrado del juego (32x32 → se sirve en varios tamaños vía CDN)."""
    if not icon_hash:
        return None
    return f"{COMMUNITY_CDN}/{appid}/{icon_hash}.jpg"


# ── Mapeo al output final ─────────────────────────────────────────────────────
def to_entry(appid: int, raw: dict) -> dict:
    devs         = raw.get("developers", [])
    support_info = raw.get("support_info", {})
    price_ov     = raw.get("price_overview", {})
    release      = raw.get("release_date", {})

    # Fecha de lanzamiento
    release_date = None
    for fmt in ("%b %d, %Y", "%d %b, %Y", "%b %Y", "%Y"):
        try:
            release_date = datetime.strptime(release.get("date", ""), fmt).date().isoformat()
            break
        except ValueError:
            pass

    # Precio sin descuento (initial = precio original en centavos)
    release_price = round(price_ov.get("initial", 0) / 100, 2) if price_ov else 0.0

    # URLs de imagen (se descargarán localmente en scrape())
    screenshot_urls = [s["path_full"] for s in raw.get("screenshots", []) if s.get("path_full")]
    images = {
        "library_header":  f"{FASTLY}/{appid}/library_hero_2x.jpg",
        "library_capsule": f"{FASTLY}/{appid}/library_600x900.jpg",
        "store":           screenshot_urls,
    }

    # Géneros: array de nombres
    genres = [g["description"] for g in raw.get("genres", []) if g.get("description")]

    dev_name    = devs[0] if devs else None
    raw_website = raw.get("website") or None
    if not raw_website and dev_name:
        # Fallback: nombre del estudio en minúsculas sin espacios ni símbolos + .com
        slug = re.sub(r"[^a-z0-9]", "", dev_name.lower())
        raw_website = f"https://www.{slug}.com"

    slug          = re.sub(r"[^a-z0-9]", "", dev_name.lower()) if dev_name else ""
    support_email = f"support@{slug}.com" if slug else None

    developer = {
        "name":          dev_name,
        "email":         support_info.get("email") or None,
        "website_url":   raw_website,
        "support_email": support_email,
    }

    return {
        "name":          raw.get("name", ""),
        "description":   raw.get("short_description") or raw.get("about_the_game") or None,
        "release_date":  release_date,
        "release_price": release_price,
        "images":        images,
        "genres":        genres,
        "developer":     developer,
    }



# ── Descarga de imágenes ──────────────────────────────────────────────────────
IMG_DIR = Path("img")

def slugify(name: str) -> str:
    """Convierte un nombre en slug válido para carpeta/archivo."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def fetch_image(session: requests.Session, url: str, dest: Path) -> bool:
    """Descarga url → dest. Devuelve True si OK."""
    try:
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            dest.write_bytes(r.content)
            return True
    except requests.RequestException:
        pass
    return False


def download_images(session: requests.Session, appid: int, game_name: str, images: dict) -> dict | None:
    """
    Crea img/{game_slug}/ y descarga:
      - {game_slug}_header.jpg
      - {game_slug}_capsule.jpg   (obligatorias; si falta alguna → None)
      - store_1.jpg, store_2.jpg… (screenshots de la store, opcionales)
    """
    slug     = slugify(game_name)
    game_dir = IMG_DIR / slug
    game_dir.mkdir(parents=True, exist_ok=True)

    local = {}

    # ── Imágenes obligatorias ─────────────────────────────────────
    required = {
        "library_header":  f"{slug}_header.jpg",
        "library_capsule": f"{slug}_capsule.jpg",
    }
    for key, filename in required.items():
        dest = game_dir / filename
        if dest.exists():
            local[key] = str(dest)
            continue
        ok = fetch_image(session, images[key], dest)
        if ok:
            local[key] = str(dest)
        else:
            log.warning("✗  %-40s sin %-20s → juego saltado", f'"{game_name}"', key)
            # Limpia lo ya descargado
            for p in local.values():
                Path(p).unlink(missing_ok=True)
            game_dir.rmdir() if not any(game_dir.iterdir()) else None
            return None

    # ── Screenshots de la store (opcionales) ─────────────────────
    store_paths = []
    for i, url in enumerate(images.get("store", []), start=1):
        dest = game_dir / f"store_{i}.jpg"
        if dest.exists():
            store_paths.append(str(dest))
            continue
        if fetch_image(session, url, dest):
            store_paths.append(str(dest))
        else:
            log.debug("Screenshot %s no disponible para %s", i, game_name)

    local["store"] = store_paths
    return local


# ── Checkpoint ────────────────────────────────────────────────────────────────
def save_checkpoint(results: list, processed_ids: set) -> None:
    CHECKPOINT_FILE.write_text(json.dumps({
        "results":      results,
        "processed_ids": list(processed_ids),
    }))


def load_checkpoint() -> tuple[list, set]:
    if not CHECKPOINT_FILE.exists():
        return [], set()
    data = json.loads(CHECKPOINT_FILE.read_text())
    log.info("Checkpoint cargado: %s juegos ya obtenidos", len(data["results"]))
    return data["results"], set(data["processed_ids"])


# ── Scrape principal ──────────────────────────────────────────────────────────
def scrape(count: int, offset: int, delay: float, output: str,
           resume: bool, clear_cache: bool) -> None:

    if clear_cache and CACHE_FILE.exists():
        CACHE_FILE.unlink()
        log.info("Caché borrada.")

    session  = build_session()
    all_apps = load_app_list(session, needed=count)

    results, processed_ids = load_checkpoint() if resume else ([], set())

    # Aplica offset sobre los apps no procesados aún
    candidates = [a for a in all_apps[offset:] if a["appid"] not in processed_ids]
    # Margen extra porque muchos no son type=game
    candidates = candidates[: count * 6]

    if not candidates:
        log.error("No quedan apps candidatas. Prueba con --offset menor o --clear-cache.")
        sys.exit(1)

    log.info("Objetivo: %s juegos | ya obtenidos: %s | candidatos: %s",
             count, len(results), len(candidates))

    skipped   = 0
    attempted = 0

    for app in candidates:
        if len(results) >= count:
            break

        appid     = app["appid"]
        attempted += 1
        processed_ids.add(appid)

        details = fetch_details(session, appid)
        if not details:
            skipped += 1
            time.sleep(delay * 0.25)
            continue

        entry = to_entry(appid, details)
        local_images = download_images(session, appid, entry["name"], entry["images"])
        if local_images is None:
            skipped += 1
            continue
        entry["images"] = local_images
        results.append(entry)

        n = len(results)
        if n % 25 == 0:
            save_checkpoint(results, processed_ids)
            log.info("  [%s/%s] checkpoint guardado  (intentos=%s, omitidos=%s)",
                     n, count, attempted, skipped)
        elif n % 10 == 0:
            log.info("  [%s/%s]  intentos=%s  omitidos=%s", n, count, attempted, skipped)

        time.sleep(delay)

    # Guardar JSON final — array plano, sin meta
    out = Path(output)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    size_mb = out.stat().st_size / 1_048_576

    # Limpia checkpoint si completamos
    if len(results) >= count and CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()

    log.info("✓ Guardado: %s  (%.2f MB, %s juegos)", out, size_mb, len(results))


# ── CLI ───────────────────────────────────────────────────────────────────────
def cli() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Steam data scraper → JSON estructurado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python steam_scraper.py                          # 1 000 juegos
  python steam_scraper.py -n 200 -o datos.json
  python steam_scraper.py -n 500 --offset 1000
  python steam_scraper.py --resume                 # continúa si se cortó
  python steam_scraper.py -n 50  -d 2.0            # más lento / más seguro
  python steam_scraper.py --clear-cache            # fuerza refrescar lista
        """,
    )
    p.add_argument("--count",       "-n", type=int,   default=DEFAULT_COUNT,  metavar="N")
    p.add_argument("--offset",      "-s", type=int,   default=0,              metavar="N")
    p.add_argument("--delay",       "-d", type=float, default=DEFAULT_DELAY,  metavar="S")
    p.add_argument("--output",      "-o", type=str,   default=DEFAULT_OUTPUT, metavar="FILE")
    p.add_argument("--resume",            action="store_true",
                   help="Continuar desde el checkpoint guardado")
    p.add_argument("--clear-cache",       action="store_true",
                   help="Borrar caché de lista de apps y descargar de nuevo")
    return p.parse_args()


if __name__ == "__main__":
    args = cli()
    if args.count < 1:
        log.error("--count debe ser >= 1")
        sys.exit(1)
    if args.delay < 0.5:
        log.warning("Delay < 0.5s aumenta el riesgo de rate-limit (429).")
    scrape(
        count=args.count,
        offset=args.offset,
        delay=args.delay,
        output=args.output,
        resume=args.resume,
        clear_cache=args.clear_cache,
    )
