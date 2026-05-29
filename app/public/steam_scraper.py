"""Steam Games Data Scraper.

Obtiene los juegos más populares de Steam y genera un JSON con imágenes
y trailer (vídeo + audio) descargados localmente.

Uso:
    python steam_scraper.py -n 100
    python steam_scraper.py -n 500 -o out.json --quality min -j 20
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import struct
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from http import HTTPStatus
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── Configuración ──────────────────────────────────────────────────────────────

STORE_SEARCH_URL = "https://store.steampowered.com/search/results/"
APP_DETAIL_URL = "https://store.steampowered.com/api/appdetails"
APP_LIST_URLS = [
    "https://api.steampowered.com/ISteamApps/GetAppList/v2/",
    "https://store.steampowered.com/api/applist/v2/",
]
FASTLY_CDN = "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps"
IMG_DIR = Path("image")

DEFAULT_COUNT = 1000
DEFAULT_CONCURRENCY = 10
DEFAULT_OUTPUT = "data/games.json"
DEFAULT_QUALITY = "max"

# Delay entre peticiones a la API de Steam.
# Probado sin rate-limit hasta 0.05 s; 0.5 s deja margen holgado en sesiones largas.
DELAY = 0.5

MATURE_AGE_LIMIT = 18
MIN_SCREENSHOTS = 6
_DATE_FORMATS = ("%b %d, %Y", "%d %b, %Y", "%b %Y", "%Y")

NON_LATIN = re.compile(
    r"[Ѐ-ӿ؀-ۿऀ-ॿ"
    r"　-鿿가-힯豈-﫿]"
)

# Seed de último recurso: juegos de Valve con trailer conocido.
SEED_APPIDS = [
    570,
    730,
    440,
    620,
    550,
    400,
    500,  # Dota2, CS2, TF2, Portal2, L4D2, Portal, L4D
    1250410,
    1902490,
    450390,
    1046930,
    4000,  # Alyx, ApertureJob, TheLab, Underlords, Garry
    220,  # Half-Life 2
]

# ── Logging ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("steam")

# ── HTTP ───────────────────────────────────────────────────────────────────────


def build_session() -> requests.Session:
    s = requests.Session()
    s.mount(
        "https://",
        HTTPAdapter(
            max_retries=Retry(
                total=2,
                backoff_factor=1.5,
                status_forcelist=[
                    HTTPStatus.TOO_MANY_REQUESTS,
                    HTTPStatus.SERVICE_UNAVAILABLE,
                ],
                allowed_methods=["GET"],
                raise_on_status=False,
            )
        ),
    )
    s.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    return s


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
            if r.status_code == HTTPStatus.OK:
                return r.json()
            if r.status_code in (
                HTTPStatus.TOO_MANY_REQUESTS,
                HTTPStatus.BAD_GATEWAY,
                HTTPStatus.SERVICE_UNAVAILABLE,
            ):
                wait = 2**attempt
                log.warning(
                    "HTTP %s — esperando %ss (%s/%s)",
                    r.status_code,
                    wait,
                    attempt,
                    max_attempts,
                )
                time.sleep(wait)
                continue
            return None
        except (requests.ConnectionError, requests.Timeout) as exc:
            wait = 2**attempt
            log.warning("Conexión fallida (%s) — reintentando en %ss", exc, wait)
            time.sleep(wait)
    return None


# ── Lista de apps ──────────────────────────────────────────────────────────────


def load_app_list(session: requests.Session, needed: int = 1000) -> list[dict]:
    """Lista de apps ordenada por popularidad."""
    apps: list[dict] = []
    start = 0
    log.info("Descargando lista vía Store Search…")
    target = max(needed * 4, 2000)
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
        if not data or not (items := data.get("items", [])):
            break
        for item in items:
            if m := re.search(r"/apps/(\d+)/", item.get("logo", "") or ""):
                apps.append({"appid": int(m.group(1)), "name": item.get("name", "")})
        start += 100
        log.info("  %s IDs recogidos…", len(apps))
        time.sleep(0.5)

    if not apps:
        for url in APP_LIST_URLS:
            if data := get_json(session, url, timeout=30, max_attempts=3):
                apps = [
                    a
                    for a in data.get("applist", {}).get("apps", [])
                    if a.get("name", "").strip()
                ]
                if apps:
                    break

    if apps:
        return apps

    log.warning("Todos los endpoints fallaron — usando seed estático")
    return [{"appid": aid, "name": ""} for aid in SEED_APPIDS]


# ── Detalles y esquema de salida ───────────────────────────────────────────────


def fetch_details(session: requests.Session, appid: int) -> dict | None:
    data = get_json(
        session, APP_DETAIL_URL, params={"appids": appid, "cc": "us", "l": "english"}
    )
    if not data:
        return None
    payload = data.get(str(appid), {})
    if not payload.get("success"):
        return None
    d = payload["data"]
    if d.get("type") != "game":
        return None
    if int(d.get("required_age", 0) or 0) >= MATURE_AGE_LIMIT:
        return None
    if not d.get("developers"):
        return None
    if NON_LATIN.search(d.get("name", "")) or NON_LATIN.search(d["developers"][0]):
        return None
    if not d.get("movies"):
        return None
    return d


def _parse_date(raw: str) -> str | None:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def to_entry(appid: int, raw: dict, quality: str) -> dict:
    dev = raw["developers"][0]
    slug = re.sub(r"[^a-z0-9]", "", dev.lower())
    si = raw.get("support_info") or {}
    po = raw.get("price_overview") or {}
    rd = raw.get("release_date") or {}
    ss = "path_thumbnail" if quality == "min" else "path_full"
    movies = raw.get("movies", [])
    src = next((m for m in movies if m.get("highlight")), movies[0]) if movies else {}
    return {
        "name": raw["name"],
        "description": raw.get("short_description")
        or raw.get("about_the_game")
        or None,
        "release_date": _parse_date(rd.get("date", "")),
        "release_price": round(po.get("initial", 0) / 100, 2),
        "images": {
            "library_header": raw.get("header_image")
            or f"{FASTLY_CDN}/{appid}/library_hero_2x.jpg",
            "library_capsule": f"{FASTLY_CDN}/{appid}/library_600x900.jpg",
            "store": [s[ss] for s in raw.get("screenshots", []) if s.get(ss)],
            "trailer_url": src.get("hls_h264")
            or src.get("dash_h264")
            or src.get("dash_av1"),
        },
        "genres": [
            g["description"] for g in raw.get("genres", []) if g.get("description")
        ],
        "developer": {
            "name": dev,
            "email": si.get("email") or None,
            "website_url": raw.get("website") or f"https://www.{slug}.com",
            "support_email": f"support@{slug}.com",
        },
    }


# ── fMP4 mux — Python puro ─────────────────────────────────────────────────────


def _mp4_iter(data: bytes):
    """Genera (name, start, end) para cada box de nivel superior."""
    pos = 0
    while pos + 8 <= len(data):
        size = struct.unpack_from(">I", data, pos)[0]
        name = data[pos + 4 : pos + 8].decode("latin-1")
        if size == 0:
            yield name, pos, len(data)
            break
        if size < 8:
            break
        yield name, pos, pos + size
        pos += size


def _mp4_u32(data: bytes, offset: int, val: int) -> bytes:
    return data[:offset] + struct.pack(">I", val) + data[offset + 4 :]


def _mp4_patch(box: bytes, patches: dict[str, Callable[[bytes], bytes]]) -> bytes:
    """Reconstruye un container box aplicando transforms a los hijos indicados."""
    body = box[8:]
    new_body = b"".join(
        patches[n](body[s:e]) if n in patches else body[s:e]
        for n, s, e in _mp4_iter(body)
    )
    return struct.pack(">I", len(new_body) + 8) + box[4:8] + new_body


def _patch_tkhd(b: bytes) -> bytes:
    return _mp4_u32(b, 20 if b[8] == 0 else 28, 2)


def _patch_id(b: bytes) -> bytes:  # trex y tfhd: version(4) + track_ID(4) a offset 12
    return _mp4_u32(b, 12, 2)


def _patch_moof(b: bytes) -> bytes:
    return _mp4_patch(b, {"traf": lambda t: _mp4_patch(t, {"tfhd": _patch_id})})


def _mux_mp4(video: Path, audio: Path, dest: Path) -> bool:
    """Fusiona vídeo-only y audio-only fMP4 en dest usando solo stdlib."""
    try:
        vdata, adata = video.read_bytes(), audio.read_bytes()
    except OSError:
        return False

    def first(data: bytes, name: str) -> tuple[int, int] | None:
        return next(((s, e) for n, s, e in _mp4_iter(data) if n == name), None)

    v_se, a_se = first(vdata, "moov"), first(adata, "moov")
    if not v_se or not a_se:
        return False

    a_body = adata[a_se[0] : a_se[1]][8:]
    a_trak = next((a_body[s:e] for n, s, e in _mp4_iter(a_body) if n == "trak"), None)
    a_mvex = next((a_body[s:e] for n, s, e in _mp4_iter(a_body) if n == "mvex"), b"")[
        8:
    ]
    a_trex = next((a_mvex[s:e] for n, s, e in _mp4_iter(a_mvex) if n == "trex"), None)
    if not a_trak or not a_trex:
        return False

    p_trak, p_trex = _mp4_patch(a_trak, {"tkhd": _patch_tkhd}), _patch_id(a_trex)

    # Moov fusionado: inserta trak y trex del audio con track_ID=2
    v_body, new_body, trak_done = vdata[v_se[0] : v_se[1]][8:], b"", False
    for name, s, e in _mp4_iter(v_body):
        child = v_body[s:e]
        if name == "trak" and not trak_done:
            new_body += child + p_trak
            trak_done = True
        elif name == "mvex":
            c = child[8:] + p_trex
            new_body += struct.pack(">I", len(c) + 8) + b"mvex" + c
        else:
            new_body += child
    merged_moov = struct.pack(">I", len(new_body) + 8) + b"moov" + new_body

    # Parchear track_ID en los moof del audio y concatenar tras el vídeo
    def patch_audio(data: bytes) -> bytes:
        out, pos = b"", 0
        while pos + 8 <= len(data):
            size = struct.unpack_from(">I", data, pos)[0]
            if size < 8:
                break
            box = data[pos : pos + size]
            out += _patch_moof(box) if data[pos + 4 : pos + 8] == b"moof" else box
            pos += size
        return out

    v_ftyp = next((vdata[s:e] for n, s, e in _mp4_iter(vdata) if n == "ftyp"), b"")
    try:
        dest.write_bytes(
            v_ftyp + merged_moov + vdata[v_se[1] :] + patch_audio(adata[a_se[1] :])
        )
        return True
    except OSError:
        return False


# ── Descarga de assets ─────────────────────────────────────────────────────────


def _fetch_image(session: requests.Session, url: str, dest: Path) -> bool:
    if dest.exists():
        return True
    try:
        r = session.get(url, timeout=15)
        if r.status_code == HTTPStatus.OK:
            dest.write_bytes(r.content)
            return True
    except requests.RequestException:
        pass
    return False


def _download_hls_segments(
    session: requests.Session, playlist_url: str, out: Path
) -> bool:
    """Descarga init + segmentos de una playlist HLS fMP4."""
    r = session.get(playlist_url, timeout=15)
    if r.status_code != HTTPStatus.OK:
        return False
    pbase = playlist_url.rsplit("/", 1)[0]

    def abs_url(u: str) -> str:
        return u if u.startswith("http") else f"{pbase}/{u}"

    lines = r.text.splitlines()
    init = next(
        (
            abs_url(ln.split('URI="')[1].split('"')[0])
            for ln in lines
            if ln.startswith("#EXT-X-MAP") and 'URI="' in ln
        ),
        None,
    )
    segs = [
        abs_url(ln.strip()) for ln in lines if ln.strip() and not ln.startswith("#")
    ]
    if not segs:
        return False
    with out.open("wb") as f:
        if init:
            ir = session.get(init, timeout=15)
            if ir.status_code == HTTPStatus.OK:
                f.write(ir.content)
        for su in segs:
            seg = session.get(su, timeout=20)
            if seg.status_code == HTTPStatus.OK:
                f.write(seg.content)
    return out.stat().st_size > 0


def _fetch_video(
    session: requests.Session, url: str | None, dest: Path, quality: str
) -> bool:
    """Descarga un trailer HLS con audio (mux Python puro) o solo vídeo como fallback."""
    if not url or dest.exists():
        return dest.exists()

    tmp_v, tmp_a = dest.with_suffix(".tmp_v.mp4"), dest.with_suffix(".tmp_a.mp4")
    try:
        r = session.get(url, timeout=15)
        if r.status_code != HTTPStatus.OK:
            return False
        base, lines = url.rsplit("/", 1)[0], r.text.splitlines()

        audio_groups = {}
        for line in lines:
            if line.startswith("#EXT-X-MEDIA") and "TYPE=AUDIO" in line:
                if (gid := re.search(r'GROUP-ID="([^"]+)"', line)) and (
                    uri := re.search(r'URI="([^"]+)"', line)
                ):
                    u = uri.group(1)
                    audio_groups[gid.group(1)] = (
                        u if u.startswith("http") else f"{base}/{u}"
                    )

        variants: list[tuple[int, str, str | None]] = []
        for i, line in enumerate(lines):
            if line.startswith("#EXT-X-STREAM-INF") and i + 1 < len(lines):
                bw = int(
                    next(
                        (
                            p.split("=")[1]
                            for p in line.split(",")
                            if p.startswith("BANDWIDTH=")
                        ),
                        "0",
                    )
                )
                nxt = lines[i + 1].strip()
                m = re.search(r'AUDIO="([^"]+)"', line)
                variants.append(
                    (
                        bw,
                        nxt if nxt.startswith("http") else f"{base}/{nxt}",
                        m.group(1) if m else None,
                    )
                )

        if variants:
            variants.sort(key=lambda v: v[0], reverse=(quality == "max"))
            _, stream_url, audio_group = variants[0]
        else:
            stream_url, audio_group = url, None

        if not _download_hls_segments(session, stream_url, tmp_v):
            return False

        audio_url = audio_groups.get(audio_group) if audio_group else None
        if (
            audio_url
            and _download_hls_segments(session, audio_url, tmp_a)
            and _mux_mp4(tmp_v, tmp_a, dest)
        ):
            return True

        log.debug("sin audio — guardando solo vídeo para '%s'", dest.parent.name)
        tmp_v.rename(dest)
        return True

    except (requests.RequestException, OSError, ValueError, IndexError) as exc:
        log.warning("error al procesar trailer: %s", exc)
        dest.unlink(missing_ok=True)
        return False
    finally:
        tmp_v.unlink(missing_ok=True)
        tmp_a.unlink(missing_ok=True)


def download_assets(
    session: requests.Session, entry: dict, quality: str
) -> dict | None:
    """Descarga header, capsule, trailer y 6 screenshots en img/{slug}/."""
    game_dir = IMG_DIR / slugify(entry["name"])
    game_dir.mkdir(parents=True, exist_ok=True)
    raw, local = entry["images"], {}

    def abort() -> None:
        for p in local.values():
            Path(p).unlink(missing_ok=True)
        if game_dir.exists() and not any(game_dir.iterdir()):
            game_dir.rmdir()

    for key, fname in (
        ("library_header", "header.jpg"),
        ("library_capsule", "capsule.jpg"),
    ):
        dest = game_dir / fname
        if _fetch_image(session, raw[key], dest):
            local[key] = str(dest.resolve())
        else:
            log.warning("✗  %-42s falta %s → saltado", f'"{entry["name"]}"', key)
            return abort() or None

    trailer = game_dir / "trailer.mp4"
    if _fetch_video(session, raw.get("trailer_url"), trailer, quality):
        local["trailer"] = str(trailer.resolve())
    else:
        log.warning("✗  %-42s sin trailer → saltado", f'"{entry["name"]}"')
        return abort() or None

    urls = raw.get("store", [])[:MIN_SCREENSHOTS]
    if len(urls) < MIN_SCREENSHOTS:
        log.warning(
            "✗  %-42s solo %s screenshots → saltado", f'"{entry["name"]}"', len(urls)
        )
        return abort() or None

    store = []
    for i, url in enumerate(urls, 1):
        dest = game_dir / f"store_{i}.jpg"
        if _fetch_image(session, url, dest):
            store.append(str(dest.resolve()))
        else:
            log.warning("✗  %-42s falla store_%s → saltado", f'"{entry["name"]}"', i)
            return abort() or None

    return {**local, "store": store}


# ── Scrape ─────────────────────────────────────────────────────────────────────


def scrape(*, count: int, output: str, quality: str) -> None:
    session = build_session()
    candidates = load_app_list(session, needed=count)[: count * 6]
    if not candidates:
        log.error("Sin candidatos.")
        raise SystemExit(1)

    # Fase 1: metadatos (secuencial, respeta rate-limit)
    log.info("Fase 1: metadatos (calidad=%s)…", quality)
    entries: list[dict] = []
    target = count + max(count // 2, 20)
    for app in candidates:
        if len(entries) >= target:
            break
        if raw := fetch_details(session, app["appid"]):
            entries.append(to_entry(app["appid"], raw, quality))
            log.info("  [%s/%s] %s", len(entries), target, raw["name"])
            time.sleep(DELAY)
        else:
            time.sleep(DELAY * 0.25)

    if not entries:
        log.error("Ningún juego pasó los filtros.")
        raise SystemExit(1)

    # Fase 2: assets en paralelo
    workers = min(DEFAULT_CONCURRENCY, len(entries))
    log.info("Fase 2: assets (%s juegos, %s workers)…", len(entries), workers)
    stop = threading.Event()

    def _worker(entry: dict) -> dict | None:
        if stop.is_set():
            return None
        assets = download_assets(build_session(), entry, quality)
        return {**entry, "images": assets} if assets else None

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {}
        for i, e in enumerate(entries):
            futs[pool.submit(_worker, e)] = e
            if 0 < i < workers:
                time.sleep(0.3)
        for future in as_completed(futs):
            if result := future.result():
                results.append(result)
                log.info("  [%s/%s] ✓ %s", len(results), count, result["name"])
            if len(results) >= count:
                stop.set()
                break

    results = results[:count]
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    log.info(
        "✓ %s  (%.2f MB, %s juegos)", out, out.stat().st_size / 1_048_576, len(results)
    )


# ── CLI ────────────────────────────────────────────────────────────────────────


def main() -> None:
    p = argparse.ArgumentParser(description="Steam scraper → JSON con assets locales")
    p.add_argument(
        "-n",
        "--count",
        type=int,
        default=DEFAULT_COUNT,
        metavar="N",
        help=f"Nº de juegos (default: {DEFAULT_COUNT})",
    )
    p.add_argument(
        "-o",
        "--output",
        type=str,
        default=DEFAULT_OUTPUT,
        metavar="FILE",
        help=f"JSON de salida (default: {DEFAULT_OUTPUT})",
    )
    p.add_argument(
        "-q",
        "--quality",
        choices=("max", "min"),
        default=DEFAULT_QUALITY,
        help="Calidad de assets: max/min (default: max)",
    )
    args = p.parse_args()

    if args.count < 1:
        log.error("--count debe ser >= 1")
        raise SystemExit(1)

    scrape(count=args.count, output=args.output, quality=args.quality)


if __name__ == "__main__":
    main()
