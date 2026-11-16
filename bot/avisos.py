"""Avisos por correo.

Sirve como canal independiente de Telegram: si Telegram esta bloqueado o el
proxy falla, los avisos llegan igual al movil (notificacion del correo).

Configuracion en /etc/geoid-bot.env:

    GEOID_SMTP_HOST=smtp.yandex.ru
    GEOID_SMTP_PORT=465
    GEOID_SMTP_USER=tu@yandex.ru
    GEOID_SMTP_PASS=contraseña-de-aplicacion
    GEOID_CORREO_DESTINO=tu@yandex.ru

Con Yandex, Gmail o Mail.ru hay que crear una "contraseña de aplicacion"
(no vale la normal). El puerto 465 usa SSL; el 587 usa STARTTLS.
"""

import asyncio
import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

log = logging.getLogger("geoid")

HOST = os.environ.get("GEOID_SMTP_HOST", "").strip()
PUERTO = int(os.environ.get("GEOID_SMTP_PORT", "465"))
USUARIO = os.environ.get("GEOID_SMTP_USER", "").strip()
CLAVE = os.environ.get("GEOID_SMTP_PASS", "").strip()
DESTINO = os.environ.get("GEOID_CORREO_DESTINO", "").strip()


def disponible() -> bool:
    return bool(HOST and USUARIO and CLAVE and DESTINO)


def _enviar_de_verdad(asunto: str, cuerpo: str) -> None:
    mensaje = EmailMessage()
    mensaje["From"] = USUARIO
    mensaje["To"] = DESTINO
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)

    contexto = ssl.create_default_context()
    if PUERTO == 465:
        with smtplib.SMTP_SSL(HOST, PUERTO, context=contexto, timeout=20) as smtp:
            smtp.login(USUARIO, CLAVE)
            smtp.send_message(mensaje)
    else:
        with smtplib.SMTP(HOST, PUERTO, timeout=20) as smtp:
            smtp.starttls(context=contexto)
            smtp.login(USUARIO, CLAVE)
            smtp.send_message(mensaje)


async def avisar(asunto: str, cuerpo: str) -> None:
    """Manda el correo sin bloquear el bot. Nunca lanza excepcion."""
    if not disponible():
        return
    try:
        await asyncio.to_thread(_enviar_de_verdad, asunto, cuerpo)
        log.info("aviso enviado por correo: %s", asunto)
    except Exception:  # noqa: BLE001
        log.exception("no se pudo enviar el correo")
