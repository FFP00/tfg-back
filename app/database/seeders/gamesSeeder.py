import json
import logging
from datetime import date
from decimal import Decimal
from pathlib import Path

from pwdlib import PasswordHash
from sqlmodel import Session, select

from app.database.models.DeveloperModel import Developer
from app.database.models.GenreModel import Genre
from app.database.models.GenreTitleModel import GenreTitle
from app.database.models.MediaModel import Media
from app.database.models.TitleModel import Title

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

hasher = PasswordHash.recommended()
GAMES_JSON = Path("/workdir/app/public/data/games.json")


def _read_file(path: str) -> bytes | None:
    p = Path(path)
    if p.exists():
        return p.read_bytes()
    logger.info(f"Archivo no encontrado: {path}")
    return None


def seed_games(session: Session) -> None:
    with open(GAMES_JSON, encoding="utf-8") as f:
        games = json.load(f)

    # ── Géneros ───────────────────────────────────────────────────────────────

    nombres_generos: set[str] = set()
    for game in games:
        nombres_generos.update(game["genres"])

    generos_nuevos = []
    for nombre in sorted(nombres_generos):
        if not session.exec(select(Genre).where(Genre.name == nombre)).first():
            generos_nuevos.append(Genre(name=nombre))

    session.add_all(generos_nuevos)
    session.flush()

    mapa_generos: dict[str, int] = {}
    for genero in session.exec(select(Genre)).all():
        if genero.id is not None:
            mapa_generos[genero.name] = genero.id

    logger.info(f"{len(mapa_generos)} géneros preparados.")

    # ── Desarrolladores ───────────────────────────────────────────────────────

    mapa_developers: dict[str, int] = {}
    emails_vistos: dict[str, int] = {}
    support_emails_vistos: dict[str, int] = {}

    for game in games:
        datos_dev = game["developer"]
        nombre_dev = datos_dev["name"]
        email_dev = datos_dev["email"]
        support_dev = datos_dev["support_email"]

        if nombre_dev in mapa_developers:
            continue

        if email_dev in emails_vistos:
            mapa_developers[nombre_dev] = emails_vistos[email_dev]
            continue

        if support_dev in support_emails_vistos:
            mapa_developers[nombre_dev] = support_emails_vistos[support_dev]
            continue

        existente = (
            session.exec(select(Developer).where(Developer.email == email_dev)).first()
            or session.exec(
                select(Developer).where(Developer.name == nombre_dev)
            ).first()
            or session.exec(
                select(Developer).where(Developer.support_email == support_dev)
            ).first()
        )

        if existente:
            if existente.id is None:
                logger.info(f"No encontramos id del developer {nombre_dev!r}")
                return
            mapa_developers[nombre_dev] = existente.id
            emails_vistos[email_dev] = existente.id
            support_emails_vistos[support_dev] = existente.id
            continue

        developer = Developer(
            name=nombre_dev,
            email=email_dev,
            support_email=support_dev,
            website_url=datos_dev.get("website_url"),
            password=hasher.hash("password123"),
            status=True,
        )
        session.add(developer)
        session.flush()

        if developer.id is None:
            logger.info(f"No encontramos id del developer {nombre_dev!r}")
            return

        mapa_developers[nombre_dev] = developer.id
        emails_vistos[email_dev] = developer.id
        support_emails_vistos[support_dev] = developer.id

    logger.info(f"{len(mapa_developers)} desarrolladores preparados.")

    # ── Títulos ───────────────────────────────────────────────────────────────

    titulos_nuevos = 0

    for game in games:
        nombre_juego = game["name"]

        if session.exec(select(Title).where(Title.name == nombre_juego)).first():
            continue

        nombre_dev = game["developer"]["name"]
        developer_id = mapa_developers.get(nombre_dev)
        if not developer_id:
            logger.info(f"No encontramos developer para {nombre_juego!r}")
            continue

        imagenes = game["images"]
        store = imagenes.get("store", [])

        capsule = _read_file(imagenes["library_capsule"])
        header = _read_file(imagenes["library_header"])
        store_1 = _read_file(store[0]) if len(store) > 0 else None

        if not capsule or not header or not store_1:
            logger.info(f"Faltan imágenes requeridas para {nombre_juego!r}")
            continue

        title = Title(
            name=nombre_juego,
            release_date=date.fromisoformat(game["release_date"]),
            release_price=Decimal(str(game["release_price"])),
            actual_discount=0,
            developer_id=developer_id,
            status=True,
        )
        session.add(title)
        session.flush()

        if not title.id:
            logger.info(f"No se pudo crear título {nombre_juego!r}")
            continue

        media = session.exec(select(Media).where(Media.title_id == title.id)).first()
        if not media:
            logger.info(f"No se pudo crear media para {nombre_juego!r}")
            continue

        media.capsule = capsule
        media.header  = header
        media.store_1 = store_1
        media.store_2 = _read_file(store[1]) if len(store) > 1 else None
        media.store_3 = _read_file(store[2]) if len(store) > 2 else None
        media.store_4 = _read_file(store[3]) if len(store) > 3 else None
        media.store_5 = _read_file(store[4]) if len(store) > 4 else None
        media.store_6 = _read_file(store[5]) if len(store) > 5 else None
        media.trailer = _read_file(imagenes["trailer"]) if "trailer" in imagenes else None
        session.add(media)

        for nombre_genero in game.get("genres", []):
            genre_id = mapa_generos.get(nombre_genero)
            if genre_id:
                session.add(GenreTitle(title_id=title.id, genre_id=genre_id))

        titulos_nuevos += 1

    logger.info(f"{titulos_nuevos} títulos preparados.")
