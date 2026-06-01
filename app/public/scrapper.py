from __future__ import annotations

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
APP_DETAIL_URL   = "https://store.steampowered.com/api/appdetails"
APP_LIST_URLS    = [
    "https://api.steampowered.com/ISteamApps/GetAppList/v2/",
    "https://store.steampowered.com/api/applist/v2/",
]
FASTLY_CDN = "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps"

_HERE = Path(__file__).parent

COUNT:       int  = 100
CONCURRENCY: int  = 10
OUTPUT:      Path = _HERE / "data/games.json"
IMAGE_DIR:   Path = _HERE / "image"
QUALITY:     str  = "min"   # "max" | "min"

# Delay entre peticiones a la API de Steam.
# Probado sin rate-limit hasta 0.05 s; 0.5 s deja margen holgado en sesiones largas.
DELAY = 0.5

MATURE_AGE_LIMIT = 18
MIN_SCREENSHOTS  = 6
_DATE_FORMATS    = ("%b %d, %Y", "%d %b, %Y", "%b %Y", "%Y")

NON_LATIN = re.compile(
    r"[Ѐ-ӿ؀-ۿऀ-ॿ"
    r"　-鿿가-힯豈-﫿]"
)

# Seed de último recurso: juegos de Valve con trailer conocido.
SEED_APPIDS = [
    570, 730, 440, 620, 550, 400, 500,
    1250410, 1902490, 450390, 1046930, 4000, 220,
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
                    r.status_code, wait, attempt, max_attempts,
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


def load_app_list(session: requests.Session) -> list[dict]:
    apps: list[dict] = []
    start = 0
    log.info("Descargando lista vía Store Search…")
    target = max(COUNT * 4, 2000)
    while len(apps) < target:
        data = get_json(
            session,
            STORE_SEARCH_URL,
            params={
                "json":           "1",
                "filter":         "games",
                "sort_by":        "Reviews_DESC",
                "maxprice":       "99999",
                "mature_content": "0",
                "start":          start,
                "count":          100,
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


def to_entry(appid: int, raw: dict) -> dict:
    dev  = raw["developers"][0]
    slug = re.sub(r"[^a-z0-9]", "", dev.lower())
    si   = raw.get("support_info") or {}
    po   = raw.get("price_overview") or {}
    rd   = raw.get("release_date") or {}
    ss   = "path_thumbnail" if QUALITY == "min" else "path_full"
    movies = raw.get("movies", [])
    src    = next((m for m in movies if m.get("highlight")), movies[0]) if movies else {}
    return {
        "name": raw["name"],
        "description": raw.get("short_description") or raw.get("about_the_game") or None,
        "release_date":  _parse_date(rd.get("date", "")),
        "release_price": round(po.get("initial", 0) / 100, 2),
        "images": {
            "library_header":  raw.get("header_image") or f"{FASTLY_CDN}/{appid}/library_hero_2x.jpg",
            "library_capsule": f"{FASTLY_CDN}/{appid}/library_600x900.jpg",
            "store":       [s[ss] for s in raw.get("screenshots", []) if s.get(ss)],
            "trailer_url": src.get("hls_h264") or src.get("dash_h264") or src.get("dash_av1"),
        },
        "genres": [g["description"] for g in raw.get("genres", []) if g.get("description")],
        "developer": {
            "name":          dev,
            "email":         si.get("email") or f"{slug}@{slug}.com",
            "website_url":   raw.get("website") or f"https://www.{slug}.com",
            "support_email": f"support@{slug}.com",
        },
    }


# ── fMP4 mux — Python puro ─────────────────────────────────────────────────────


def _mp4_iter(data: bytes):
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
    body = box[8:]
    new_body = b"".join(
        patches[n](body[s:e]) if n in patches else body[s:e]
        for n, s, e in _mp4_iter(body)
    )
    return struct.pack(">I", len(new_body) + 8) + box[4:8] + new_body


def _patch_tkhd(b: bytes) -> bytes:
    return _mp4_u32(b, 20 if b[8] == 0 else 28, 2)


def _patch_id(b: bytes) -> bytes:
    return _mp4_u32(b, 12, 2)


def _patch_moof(b: bytes) -> bytes:
    return _mp4_patch(b, {"traf": lambda t: _mp4_patch(t, {"tfhd": _patch_id})})


def _mux_mp4(video: Path, audio: Path, dest: Path) -> bool:
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
    a_mvex = next((a_body[s:e] for n, s, e in _mp4_iter(a_body) if n == "mvex"), b"")[8:]
    a_trex = next((a_mvex[s:e] for n, s, e in _mp4_iter(a_mvex) if n == "trex"), None)
    if not a_trak or not a_trex:
        return False

    p_trak = _mp4_patch(a_trak, {"tkhd": _patch_tkhd})
    p_trex = _patch_id(a_trex)

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

    def patch_audio(data: bytes) -> bytes:
        out, pos = b"", 0
        while pos + 8 <= len(data):
            size = struct.unpack_from(">I", data, pos)[0]
            if size < 8:
                break
            box  = data[pos : pos + size]
            out += _patch_moof(box) if data[pos + 4 : pos + 8] == b"moof" else box
            pos += size
        return out

    v_ftyp = next((vdata[s:e] for n, s, e in _mp4_iter(vdata) if n == "ftyp"), b"")
    try:
        dest.write_bytes(v_ftyp + merged_moov + vdata[v_se[1] :] + patch_audio(adata[a_se[1] :]))
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


def _download_hls_segments(session: requests.Session, playlist_url: str, out: Path) -> bool:
    r = session.get(playlist_url, timeout=15)
    if r.status_code != HTTPStatus.OK:
        return False
    pbase = playlist_url.rsplit("/", 1)[0]

    def abs_url(u: str) -> str:
        return u if u.startswith("http") else f"{pbase}/{u}"

    lines = r.text.splitlines()
    init  = next(
        (
            abs_url(ln.split('URI="')[1].split('"')[0])
            for ln in lines
            if ln.startswith("#EXT-X-MAP") and 'URI="' in ln
        ),
        None,
    )
    segs = [abs_url(ln.strip()) for ln in lines if ln.strip() and not ln.startswith("#")]
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


def _fetch_video(session: requests.Session, url: str | None, dest: Path) -> bool:
    if not url or dest.exists():
        return dest.exists()

    tmp_v = dest.with_suffix(".tmp_v.mp4")
    tmp_a = dest.with_suffix(".tmp_a.mp4")
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
                    audio_groups[gid.group(1)] = u if u.startswith("http") else f"{base}/{u}"

        variants: list[tuple[int, str, str | None]] = []
        for i, line in enumerate(lines):
            if line.startswith("#EXT-X-STREAM-INF") and i + 1 < len(lines):
                bw  = int(next((p.split("=")[1] for p in line.split(",") if p.startswith("BANDWIDTH=")), "0"))
                nxt = lines[i + 1].strip()
                m   = re.search(r'AUDIO="([^"]+)"', line)
                variants.append((bw, nxt if nxt.startswith("http") else f"{base}/{nxt}", m.group(1) if m else None))

        if variants:
            variants.sort(key=lambda v: v[0], reverse=(QUALITY == "max"))
            _, stream_url, audio_group = variants[0]
        else:
            stream_url, audio_group = url, None

        if not _download_hls_segments(session, stream_url, tmp_v):
            return False

        audio_url = audio_groups.get(audio_group) if audio_group else None
        if audio_url and _download_hls_segments(session, audio_url, tmp_a) and _mux_mp4(tmp_v, tmp_a, dest):
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


def download_assets(session: requests.Session, entry: dict) -> dict | None:
    game_dir = IMAGE_DIR / slugify(entry["name"])
    game_dir.mkdir(parents=True, exist_ok=True)
    raw, local = entry["images"], {}

    def abort() -> None:
        for p in local.values():
            Path(p).unlink(missing_ok=True)
        if game_dir.exists() and not any(game_dir.iterdir()):
            game_dir.rmdir()

    for key, fname in (("library_header", "header.jpg"), ("library_capsule", "capsule.jpg")):
        dest = game_dir / fname
        if _fetch_image(session, raw[key], dest):
            local[key] = str(dest.resolve())
        else:
            log.warning("✗  %-42s falta %s → saltado", f'"{entry["name"]}"', key)
            return abort() or None

    trailer = game_dir / "trailer.mp4"
    if _fetch_video(session, raw.get("trailer_url"), trailer):
        local["trailer"] = str(trailer.resolve())
    else:
        log.warning("✗  %-42s sin trailer → saltado", f'"{entry["name"]}"')
        return abort() or None

    urls = raw.get("store", [])[:MIN_SCREENSHOTS]
    if len(urls) < MIN_SCREENSHOTS:
        log.warning("✗  %-42s solo %s screenshots → saltado", f'"{entry["name"]}"', len(urls))
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


def scrape() -> None:
    session    = build_session()
    candidates = load_app_list(session)[: COUNT * 6]
    if not candidates:
        log.error("Sin candidatos.")
        raise SystemExit(1)

    log.info("Fase 1: metadatos (calidad=%s)…", QUALITY)
    entries: list[dict] = []
    target = COUNT + max(COUNT // 2, 20)
    for app in candidates:
        if len(entries) >= target:
            break
        if raw := fetch_details(session, app["appid"]):
            entries.append(to_entry(app["appid"], raw))
            log.info("  [%s/%s] %s", len(entries), target, raw["name"])
            time.sleep(DELAY)
        else:
            time.sleep(DELAY * 0.25)

    if not entries:
        log.error("Ningún juego pasó los filtros.")
        raise SystemExit(1)

    workers = min(CONCURRENCY, len(entries))
    log.info("Fase 2: assets (%s juegos, %s workers)…", len(entries), workers)
    stop = threading.Event()

    def _worker(entry: dict) -> dict | None:
        if stop.is_set():
            return None
        assets = download_assets(build_session(), entry)
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
                log.info("  [%s/%s] ✓ %s", len(results), COUNT, result["name"])
            if len(results) >= COUNT:
                stop.set()
                break

    results = results[:COUNT]
    out = OUTPUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    log.info("✓ %s  (%.2f MB, %s juegos)", out, out.stat().st_size / 1_048_576, len(results))


if __name__ == "__main__":
    scrape()
