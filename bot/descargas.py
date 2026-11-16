"""Mantiene al día los enlaces de descarga de la app.

Cada pocas horas el bot pregunta a GitHub por la última versión publicada y
guarda los enlaces reales en la base de datos. Si un archivo cambia de nombre
o se publica una versión nueva, el bot se adapta solo y no reparte enlaces
rotos.
"""

import logging
from datetime import datetime, timezone

import aiohttp

import db

log = logging.getLogger("geoid")

API = "https://api.github.com/repos/KofyTrade/geoid/releases/latest"
TIEMPO = aiohttp.ClientTimeout(total=25)


def _elegir_apk(activos: list[dict]) -> str:
    """APK para móviles modernos: nombre fijo primero, luego cualquiera."""
    fijo = [a for a in activos if a["name"] == "GeoiD-vpn-Android-arm64-v8a.apk"]
    if fijo:
        return fijo[0]["browser_download_url"]
    con_abi = [
        a for a in activos
        if a["name"].lower().endswith(".apk") and "arm64" in a["name"].lower()
    ]
    if con_abi:
        return con_abi[0]["browser_download_url"]
    cualquiera = [a for a in activos if a["name"].lower().endswith(".apk")]
    return cualquiera[0]["browser_download_url"] if cualquiera else ""


def _elegir_windows(activos: list[dict]) -> str:
    fijo = [a for a in activos if a["name"] == "GeoiD-vpn-Windows.zip"]
    if fijo:
        return fijo[0]["browser_download_url"]
    zips = [a for a in activos if a["name"].lower().endswith(".zip")]
    return zips[0]["browser_download_url"] if zips else ""


async def consultar() -> dict | None:
    """Pregunta a GitHub por la última versión. None si no se puede."""
    try:
        async with aiohttp.ClientSession(timeout=TIEMPO) as sesion:
            async with sesion.get(
                API, headers={"Accept": "application/vnd.github+json"}
            ) as respuesta:
                if respuesta.status != 200:
                    log.warning("GitHub respondió %s al pedir la versión",
                                respuesta.status)
                    return None
                datos = await respuesta.json()
    except Exception:  # noqa: BLE001
        log.exception("no se pudo consultar la última versión")
        return None

    activos = datos.get("assets") or []
    version = (datos.get("tag_name") or "").lstrip("vV")
    android = _elegir_apk(activos)
    windows = _elegir_windows(activos)

    if not android and not windows:
        log.warning("la última versión no tiene archivos descargables")
        return None

    return {
        "version": version,
        "android": android,
        "windows": windows,
        "publicada": datos.get("published_at") or "",
    }


async def actualizar(avisar=None) -> dict | None:
    """Consulta y guarda. Si la versión cambió, llama a `avisar(version)`."""
    datos = await consultar()
    if not datos:
        return None

    anterior = db.leer_ajuste("descarga_version")
    db.guardar_ajuste("descarga_version", datos["version"])
    db.guardar_ajuste("descarga_android", datos["android"])
    db.guardar_ajuste("descarga_windows", datos["windows"])
    db.guardar_ajuste(
        "descarga_revisado",
        datetime.now(tz=timezone.utc).strftime("%d.%m.%Y %H:%M UTC"),
    )

    if datos["version"] and datos["version"] != anterior:
        log.info("versión publicada detectada: %s", datos["version"])
        if avisar is not None:
            await avisar(datos["version"])

    return datos


def enlaces(android_defecto: str, windows_defecto: str) -> tuple[str, str]:
    """Enlaces guardados; si aún no hay, los de la configuración."""
    android = db.leer_ajuste("descarga_android") or android_defecto
    windows = db.leer_ajuste("descarga_windows") or windows_defecto
    return android, windows


def version_actual() -> str:
    return db.leer_ajuste("descarga_version") or ""


def ultima_revision() -> str:
    return db.leer_ajuste("descarga_revisado") or "nunca"
