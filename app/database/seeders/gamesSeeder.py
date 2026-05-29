import json
import logging
from datetime import date
from decimal import Decimal
from pathlib import Path

from pwdlib import PasswordHash
from sqlmodel import Session, select

from app.database.factories.imageFactory import ImageFactory
from app.endpoint.models.DeveloperModel import Developer
from app.endpoint.models.GenreModel import Genre
from app.endpoint.models.GenreTitleModel import GenreTitle
from app.endpoint.models.MediaModel import Media
from app.endpoint.models.TitleModel import Title

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

hasher      = PasswordHash.recommended()
GAMES_JSON  = Path("/workdir/app/public/data/games.json")
PUBLIC_PATH = Path("/workdir/app/public")


def seed_games(session: Session):
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
    emails_vistos:   dict[str, int] = {}

    for game in games:
        datos_dev  = game["developer"]
        nombre_dev = datos_dev["name"]
        email_dev  = datos_dev["email"]

        if nombre_dev in mapa_developers:
            continue

        if email_dev in emails_vistos:
            mapa_developers[nombre_dev] = emails_vistos[email_dev]
            continue

        existente = session.exec(
            select(Developer).where(Developer.email == email_dev)
        ).first() or session.exec(
            select(Developer).where(Developer.name == nombre_dev)
        ).first()

        if existente:
            if existente.id is None:
                logger.info(f"No encontramos id del developer {nombre_dev!r}")
                return
            mapa_developers[nombre_dev] = existente.id
            emails_vistos[email_dev]    = existente.id
            continue

        imagen = ImageFactory.build()
        session.add(imagen)
        session.flush()

        if imagen.id is None:
            logger.info(f"No encontramos id de imagen para developer {nombre_dev!r}")
            return

        developer = Developer(
            name          = nombre_dev,
            email         = email_dev,
            support_email = datos_dev["support_email"],
            website_url   = datos_dev.get("website_url"),
            password      = hasher.hash("password123"),
            status        = True,
            image_id      = imagen.id,
        )
        session.add(developer)
        session.flush()

        if developer.id is None:
            logger.info(f"No encontramos id del developer {nombre_dev!r}")
            return

        mapa_developers[nombre_dev] = developer.id
        emails_vistos[email_dev]    = developer.id

    logger.info(f"{len(mapa_developers)} desarrolladores preparados.")

    # ── Títulos, media y relaciones género-título ─────────────────────────────

    count_titulos = 0

    for game in games:
        if session.exec(select(Title).where(Title.name == game["name"])).first():
            continue

        imgs  = game["images"]
        store = imgs["store"]

        def leer(ruta: str) -> bytes:
            with open(PUBLIC_PATH / ruta, "rb") as f:
                return f.read()

        media = Media(
            capsule = leer(imgs["library_capsule"]),
            header  = leer(imgs["library_header"]),
            store_1 = leer(store[0]),
            store_2 = leer(store[1]) if len(store) > 1 else None,
            store_3 = leer(store[2]) if len(store) > 2 else None,
            store_4 = leer(store[3]) if len(store) > 3 else None,
            store_5 = leer(store[4]) if len(store) > 4 else None,
            store_6 = leer(store[5]) if len(store) > 5 else None,
            trailer = leer(imgs["trailer"]) if imgs.get("trailer") else None,
        )
        session.add(media)
        session.flush()

        if media.id is None:
            logger.info(f"No encontramos id de media para {game['name']!r}")
            continue

        titulo = Title(
            name             = game["name"],
            status           = True,
            actual_discount  = 0,
            release_date     = date.fromisoformat(game["release_date"]),
            release_price    = Decimal(str(game["release_price"])),
            developer_id     = mapa_developers[game["developer"]["name"]],
            media_id         = media.id,
        )
        session.add(titulo)
        session.flush()

        if titulo.id is None:
            logger.info(f"No encontramos id del título {game['name']!r}")
            continue

        for nombre_genero in game["genres"]:
            session.add(GenreTitle(title_id=titulo.id, genre_id=mapa_generos[nombre_genero]))

        session.flush()
        count_titulos += 1

    logger.info(f"{count_titulos} títulos preparados.")
