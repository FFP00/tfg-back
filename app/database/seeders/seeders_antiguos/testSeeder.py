import logging
import os

from sqlmodel import Session

from app.endpoint.models.MediaModel import Media

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_test(session: Session):

    # 1. Rutas de los archivos reales (Corregida la coma al final de capsule_path)
    header_path  = "/workdir/app/public/image/picayune_dreams/header.jpg"
    capsule_path = "/workdir/app/public/image/picayune_dreams/capsule.jpg"
    trailer_path = "/workdir/app/public/image/picayune_dreams/trailer.mp4"

    # 2. Validar que todos los archivos existan antes de continuar
    rutas = [header_path, capsule_path, trailer_path]
    for ruta in rutas:
        if not os.path.exists(ruta):
            logger.error(f"❌ No se encontró el archivo de prueba en '{ruta}'. Verifica la ruta.")
            return

    logger.info("📖 Leyendo archivos multimedia...")

    with open(header_path, "rb") as f:
        header_bytes = f.read()

    with open(capsule_path, "rb") as f:
        capsule_bytes = f.read()

    with open(trailer_path, "rb") as f:
        trailer_bytes = f.read()

    medias = []



    media = Media(
        capsule=capsule_bytes,
        header=header_bytes,
        store_1=capsule_bytes,
        trailer=trailer_bytes
    )
    medias.append(media)

    try:
        session.add_all(medias)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error al seedear la base de datos: {e}")
