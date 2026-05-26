#!/usr/bin/env python3
"""
Steam Games Data Scraper
========================
Obtiene los juegos más populares de Steam y genera un JSON estructurado
con imágenes descargadas localmente.

Uso:
    python steam_scraper.py                  # 1000 juegos
    python steam_scraper.py -n 100
    python steam_scraper.py -n 500 -o out.json
    python steam_scraper.py --resume         # continúa si se cortó
    python steam_scraper.py --clear-cache    # regenera la lista de apps
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── Constantes ────────────────────────────────────────────────────────────────

STORE_SEARCH_URL = "https://store.steampowered.com/search/results/"
APP_DETAIL_URL   = "https://store.steampowered.com/api/appdetails"
APP_LIST_URLS    = [
    "https://api.steampowered.com/ISteamApps/GetAppList/v2/",
    "https://store.steampowered.com/api/applist/v2/",
]
FASTLY_CDN = "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps"

CACHE_FILE      = Path("steam_applist_cache.json")
CHECKPOINT_FILE = Path("steam_checkpoint.json")
IMG_DIR         = Path("img")

DEFAULT_COUNT  = 1000
DEFAULT_DELAY  = 1.2
DEFAULT_OUTPUT = "steam_games.json"

# Juegos con nombre de juego o developer en estos rangos Unicode son descartados
NON_LATIN = re.compile(
    r"[\u0400-\u04FF"  # cirílico
    r"\u0600-\u06FF"   # árabe
    r"\u0900-\u097F"   # devanagari
    r"\u3000-\u9FFF"   # CJK / japonés
    r"\uAC00-\uD7AF"   # hangul
    r"\uF900-\uFAFF]"  # CJK compatibilidad
)

# Seed de appids populares — último recurso si todos los endpoints fallan
SEED_APPIDS = [
    10, 20, 30, 40, 50, 60, 70, 80, 100, 130, 220, 240, 300, 320, 340, 360,
    380, 400, 420, 440, 500, 550, 570, 620, 630, 730, 750, 1000, 1250, 1500,
    2200, 2280, 2300, 2320, 2400, 2430, 2450, 3830, 4000, 4540, 7600, 7670,
    8190, 8980, 9420, 10090, 10180, 10500, 12120, 12150, 12200, 12210, 12250,
    13140, 13200, 17300, 17390, 17450, 17480, 17500, 17520, 17540, 17560,
    18010, 19900, 20920, 21000, 22200, 22300, 22330, 22350, 22380, 22490,
    33230, 34010, 35140, 35720, 36120, 38400, 39140, 40700, 41070, 42690,
    49520, 55230, 57690, 63380, 65800, 72850, 76600, 91310, 92100, 93200,
    105450, 107200, 113020, 201810, 211820, 218620, 221100, 224260, 226560,
    231430, 232050, 233450, 234140, 238010, 238430, 239140, 240720, 242530,
    248820, 250600, 252490, 252770, 253230, 257350, 258980, 261030, 263730,
    264710, 266210, 271590, 273110, 275390, 282070, 282900, 287120, 292030,
    299740, 304930, 311120, 316010, 317400, 320760, 322330, 326460, 328080,
    332800, 335300, 346110, 359550, 362300, 362930, 363970, 365450, 374320,
    381210, 383120, 386360, 387290, 391220, 394360, 404920, 410900, 413150,
    418370, 427520, 431240, 431960, 435150, 438100, 444090, 454650, 457140,
    460790, 462310, 466240, 475190, 476600, 489520, 489830, 494840, 495570,
    517630, 526870, 534380, 548430, 553850, 559100, 562100, 570940, 578080,
    582010, 588650, 594570, 601150, 606470, 611500, 614910, 632360, 640820,
    644930, 648010, 651670, 658920, 703080, 730, 739630, 742420, 752590,
    762960, 787420, 794600, 812140, 813780, 822690, 837470, 863550, 872500,
    892970, 906850, 920210, 945360, 976310, 1085660, 1091500, 1110560,
    1144200, 1161580, 1172380, 1174180, 1182480, 1203220, 1245620, 1282080,
    1325200, 1332010, 1343400, 1361210, 1382330, 1426210, 1449560, 1466060,
    1476210, 1493710, 1502590, 1517290, 1551360, 1557740, 1568590, 1593500,
    1604030, 1659420, 1672970, 1680880, 1690800, 1817070, 1839880, 1880700,
    1904540, 1938090, 1971460, 2000300, 2050650, 2138710, 2183900, 2217000,
    2358720, 2379780, 2399830, 2456290, 2480740, 2519060, 2623190, 2677660,
]

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("steam")

# ── HTTP ──────────────────────────────────────────────────────────────────────

def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=2,
        backoff_factor=1.5,
        status_forcelist=[429, 503],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    })
    return session


def get_json(
    session: requests.Session,
    url: str,
    params: dict | None = None,
    timeout: int = 20,
    max_attempts: int = 5,
) -> dict | None:
    """GET con backoff exponencial para 429 / 502 / 503."""
    for attempt in range(1, max_attempts + 1):
        try:
            r = session.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 502, 503):
                wait = 2**attempt
                log.warning("HTTP %s — esperando %ss (intento %s/%s)", r.status_code, wait, attempt, max_attempts)
                time.sleep(wait)
                continue
            return None
        except (requests.ConnectionError, requests.Timeout) as exc:
            wait = 2**attempt
            log.warning("Conexión fallida (%s) — reintentando en %ss", exc, wait)
            time.sleep(wait)
    return None

# ── Lista de apps ─────────────────────────────────────────────────────────────

def _search_app_list(session: requests.Session, target: int) -> list[dict]:
    """Steam Store Search ordenada por Reviews_DESC (más populares primero)."""
    apps, start = [], 0
    log.info("Descargando lista vía Store Search (objetivo: ~%s)…", target)
    while len(apps) < target:
        data = get_json(
            session,
            STORE_SEARCH_URL,
            params={
                "json": "1",
                "filter": "games",
                "sort_by": "Reviews_DESC",
                "maxprice": "99999",
                "mature_content": "0",
                "start": start,
                "count": 100,
            },
            max_attempts=3,
        )
        if not data:
            break
        items = data.get("items", [])
        if not items:
            break
        for item in items:
            if m := re.search(r"/apps/(\d+)/", item.get("logo", "") or ""):
                apps.append({"appid": int(m.group(1)), "name": item.get("name", "")})
        start += 100
        log.info("  %s IDs recogidos…", len(apps))
        time.sleep(0.5)
    return apps


def load_app_list(session: requests.Session, needed: int = 1000, force_refresh: bool = False) -> list[dict]:
    """Devuelve lista de apps ordenada por popularidad, con caché de 24 h."""
    if not force_refresh and CACHE_FILE.exists():
        age_h = (time.time() - CACHE_FILE.stat().st_mtime) / 3600
        cached = json.loads(CACHE_FILE.read_text())
        if age_h < 24 and len(cached) >= needed:
            log.info("Lista desde caché (%s apps, %.1fh)", len(cached), age_h)
            return cached

    # Fuente primaria: Store Search (ordenada por popularidad)
    apps = _search_app_list(session, target=max(needed * 4, 2000))
    if apps:
        CACHE_FILE.write_text(json.dumps(apps))
        log.info("Lista guardada en caché (%s apps)", len(apps))
        return apps

    # Fallback: GetAppList (sin orden de popularidad)
    for url in APP_LIST_URLS:
        data = get_json(session, url, timeout=30, max_attempts=3)
        if data:
            apps = [a for a in data.get("applist", {}).get("apps", []) if a.get("name", "").strip()]
            if apps:
                CACHE_FILE.write_text(json.dumps(apps))
                log.info("Lista desde GetAppList guardada en caché (%s apps)", len(apps))
                return apps

    # Último recurso: seed estático
    log.warning("Todos los endpoints fallaron — usando seed estático (%s appids)", len(SEED_APPIDS))
    return [{"appid": aid, "name": ""} for aid in SEED_APPIDS]

# ── Detalles de un juego ──────────────────────────────────────────────────────

def fetch_details(session: requests.Session, appid: int) -> dict | None:
    """Devuelve los datos de un juego si pasa todos los filtros, o None."""
    data = get_json(session, APP_DETAIL_URL, params={"appids": appid, "cc": "us", "l": "english"})
    if not data:
        return None

    payload = data.get(str(appid), {})
    if not payload.get("success"):
        return None

    d = payload.get("data", {})

    if d.get("type") != "game":
        return None
    if int(d.get("required_age", 0) or 0) >= 18:
        return None
    if not d.get("developers"):
        return None
    if NON_LATIN.search(d.get("name", "")):
        return None
    if NON_LATIN.search(d["developers"][0]):
        return None

    return d

# ── Mapeo al esquema de salida ────────────────────────────────────────────────

DATE_FORMATS = ("%b %d, %Y", "%d %b, %Y", "%b %Y", "%Y")


def _parse_date(raw: str) -> str | None:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _dev_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def to_entry(appid: int, raw: dict) -> dict:
    dev_name     = raw["developers"][0]
    support_info = raw.get("support_info") or {}
    price_ov     = raw.get("price_overview") or {}
    release      = raw.get("release_date") or {}

    slug        = _dev_slug(dev_name)
    website_url = raw.get("website") or f"https://www.{slug}.com"

    return {
        "name":          raw["name"],
        "description":   raw.get("short_description") or raw.get("about_the_game") or None,
        "release_date":  _parse_date(release.get("date", "")),
        "release_price": round(price_ov.get("initial", 0) / 100, 2),
        "images": {
            "library_header":  f"{FASTLY_CDN}/{appid}/library_hero_2x.jpg",
            "library_capsule": f"{FASTLY_CDN}/{appid}/library_600x900.jpg",
            "store":           [s["path_full"] for s in raw.get("screenshots", []) if s.get("path_full")],
        },
        "genres":    [g["description"] for g in raw.get("genres", []) if g.get("description")],
        "developer": {
            "name":          dev_name,
            "email":         support_info.get("email") or None,
            "website_url":   website_url,
            "support_email": f"support@{slug}.com",
        },
    }

# ── Descarga de imágenes ──────────────────────────────────────────────────────

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _fetch_image(session: requests.Session, url: str, dest: Path) -> bool:
    if dest.exists():
        return True
    try:
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            dest.write_bytes(r.content)
            return True
    except requests.RequestException:
        pass
    return False


def download_images(session: requests.Session, appid: int, entry: dict) -> dict | None:  # noqa: ARG001
    """
    Descarga imágenes en img/{slug}/.
    Devuelve el dict de imágenes con rutas locales, o None si falta header o capsule.
    """
    slug     = slugify(entry["name"])
    game_dir = IMG_DIR / slug
    game_dir.mkdir(parents=True, exist_ok=True)

    raw_images = entry["images"]
    local      = {}

    # Obligatorias: header y capsule
    required = {
        "library_header":  f"{slug}_header.jpg",
        "library_capsule": f"{slug}_capsule.jpg",
    }
    for key, filename in required.items():
        dest = game_dir / filename
        if _fetch_image(session, raw_images[key], dest):
            local[key] = str(dest)
        else:
            log.warning("✗  %-42s falta %s → saltado", f'"{entry["name"]}"', key)
            for path in local.values():
                Path(path).unlink(missing_ok=True)
            if not any(game_dir.iterdir()):
                game_dir.rmdir()
            return None

    # Opcionales: screenshots de la store
    store = []
    for i, url in enumerate(raw_images.get("store", []), start=1):
        dest = game_dir / f"store_{i}.jpg"
        if _fetch_image(session, url, dest):
            store.append(str(dest))

    return {**local, "store": store}

# ── Checkpoint ────────────────────────────────────────────────────────────────

def save_checkpoint(results: list, processed_ids: set) -> None:
    CHECKPOINT_FILE.write_text(json.dumps({"results": results, "processed_ids": list(processed_ids)}))


def load_checkpoint() -> tuple[list, set]:
    if not CHECKPOINT_FILE.exists():
        return [], set()
    data = json.loads(CHECKPOINT_FILE.read_text())
    log.info("Checkpoint cargado: %s juegos", len(data["results"]))
    return data["results"], set(data["processed_ids"])

# ── Scrape ────────────────────────────────────────────────────────────────────

def scrape(*, count: int, offset: int, delay: float, output: str, resume: bool, clear_cache: bool) -> None:
    if clear_cache and CACHE_FILE.exists():
        CACHE_FILE.unlink()
        log.info("Caché borrada.")

    session  = build_session()
    all_apps = load_app_list(session, needed=count)

    results, processed_ids = load_checkpoint() if resume else ([], set())

    candidates = [a for a in all_apps[offset:] if a["appid"] not in processed_ids][: count * 6]
    if not candidates:
        log.error("Sin candidatos. Prueba --offset menor o --clear-cache.")
        sys.exit(1)

    log.info("Objetivo: %s | obtenidos: %s | candidatos: %s", count, len(results), len(candidates))
    skipped = attempted = 0

    for app in candidates:
        if len(results) >= count:
            break

        appid      = app["appid"]
        attempted += 1
        processed_ids.add(appid)

        raw = fetch_details(session, appid)
        if not raw:
            skipped += 1
            time.sleep(delay * 0.25)
            continue

        entry        = to_entry(appid, raw)
        local_images = download_images(session, appid, entry)
        if local_images is None:
            skipped += 1
            continue

        entry["images"] = local_images
        results.append(entry)

        n = len(results)
        if n % 25 == 0:
            save_checkpoint(results, processed_ids)
            log.info("  [%s/%s] checkpoint  intentos=%s  saltados=%s", n, count, attempted, skipped)
        elif n % 10 == 0:
            log.info("  [%s/%s]  intentos=%s  saltados=%s", n, count, attempted, skipped)

        time.sleep(delay)

    out = Path(output)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    log.info("✓ %s  (%.2f MB, %s juegos)", out, out.stat().st_size / 1_048_576, len(results))

    if len(results) >= count and CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()

# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(
        description="Steam scraper → JSON estructurado con imágenes locales",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  python steam_scraper.py -n 100\n"
            "  python steam_scraper.py -n 500 -o datos.json\n"
            "  python steam_scraper.py --resume\n"
            "  python steam_scraper.py --clear-cache -n 1000\n"
        ),
    )
    p.add_argument("-n", "--count",       type=int,   default=DEFAULT_COUNT,  metavar="N",    help="Nº de juegos (default: 1000)")
    p.add_argument("-s", "--offset",      type=int,   default=0,              metavar="N",    help="Saltar los primeros N de la lista")
    p.add_argument("-d", "--delay",       type=float, default=DEFAULT_DELAY,  metavar="S",    help="Segundos entre requests (default: 1.2)")
    p.add_argument("-o", "--output",      type=str,   default=DEFAULT_OUTPUT, metavar="FILE", help="Archivo JSON de salida")
    p.add_argument("--resume",            action="store_true", help="Continuar desde el último checkpoint")
    p.add_argument("--clear-cache",       action="store_true", help="Regenerar la lista de apps")
    args = p.parse_args()

    if args.count < 1:
        log.error("--count debe ser >= 1")
        sys.exit(1)
    if args.delay < 0.5:
        log.warning("Delay < 0.5s aumenta el riesgo de rate-limit.")

    scrape(
        count=args.count,
        offset=args.offset,
        delay=args.delay,
        output=args.output,
        resume=args.resume,
        clear_cache=args.clear_cache,
    )


if __name__ == "__main__":
    main()
