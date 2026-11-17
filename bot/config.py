"""Configuración del bot. Todo se puede sobreescribir con variables de entorno."""

import os

# --- Telegram ---
TOKEN = os.environ.get("GEOID_TOKEN", "")

# --- Servidor AmneziaWG ---
# Interfaz y ficheros del servidor (donde corre el bot).
AWG_INTERFAZ = os.environ.get("GEOID_AWG_IF", "awg0")
AWG_CONF = os.environ.get("GEOID_AWG_CONF", f"/etc/amnezia/amneziawg/{AWG_INTERFAZ}.conf")
ENDPOINT = os.environ.get("GEOID_ENDPOINT", "193.29.224.164:21766")
DNS = os.environ.get("GEOID_DNS", "10.9.9.1")
MTU = int(os.environ.get("GEOID_MTU", "1280"))

# Rango de direcciones para los clientes.
RED = os.environ.get("GEOID_RED", "10.9.9.")
IP_MIN = int(os.environ.get("GEOID_IP_MIN", "10"))
IP_MAX = int(os.environ.get("GEOID_IP_MAX", "250"))

# --- Producto ---
DIAS_PRUEBA = int(os.environ.get("GEOID_DIAS_PRUEBA", "3"))
DIAS_INVITADO = int(os.environ.get("GEOID_DIAS_INVITADO", "7"))

# Premios por amigos que COMPRAN (la prueba gratis no cuenta):
# (amigos necesarios, dias de regalo)
NIVELES_INVITACION = [(3, 7), (10, 15), (20, 30)]  # bonus por invitar

# Precios en estrellas de Telegram (XTR). 1 estrella ~ 0,013 $.
PRECIOS = {
    1: int(os.environ.get("GEOID_PRECIO_1M", "115")),
    3: int(os.environ.get("GEOID_PRECIO_3M", "300")),
    6: int(os.environ.get("GEOID_PRECIO_6M", "520")),
}

# --- Ficheros ---
DIR_DATOS = os.environ.get("GEOID_DATOS", "/var/lib/geoid-bot")
DB = os.path.join(DIR_DATOS, "bot.sqlite")

# Chat donde llegan los avisos de pago: un grupo o canal privado.
# Vacio = se mandan al privado del administrador.
AVISOS_ID = os.environ.get("GEOID_AVISOS_ID", "").strip()

# Enlaces de la aplicación (los releases del repositorio).
URL_APP = "https://github.com/KofyTrade/geoid/releases/latest"
URL_ANDROID = (
    "https://github.com/KofyTrade/geoid/releases/latest/download/"
    "GeoiD-vpn-Android-arm64-v8a.apk"
)
URL_WINDOWS = (
    "https://github.com/KofyTrade/geoid/releases/latest/download/GeoiD-vpn-Windows.zip"
)


# --- Cripto (Crypto Pay de @CryptoBot) ---
# Token de la app: @CryptoBot -> Crypto Pay -> Create App
CRYPTO_TOKEN = os.environ.get("GEOID_CRYPTO_TOKEN", "")
CRYPTO_MONEDA = os.environ.get("GEOID_CRYPTO_MONEDA", "USDT")

# Precios en dolares para cripto (los de estrellas son aparte).
PRECIOS_USD = {
    1: float(os.environ.get("GEOID_USD_1M", "1.9")),
    3: float(os.environ.get("GEOID_USD_3M", "4.8")),
    6: float(os.environ.get("GEOID_USD_6M", "8")),
}

# --- Pago con SBP / tarjeta rusa (manual) ---
# Se activa solo con poner tu telefono. Es la via mas facil para el cliente
# ruso: abre su banco, escanea el QR y paga.
SBP_TELEFONO = os.environ.get("GEOID_SBP_TELEFONO", "").strip()
SBP_TITULAR = os.environ.get("GEOID_SBP_TITULAR", "").strip()
SBP_QR_URL = os.environ.get("GEOID_SBP_QR_URL", "").strip()   # imagen opcional

# Precios en rublos para este metodo.
PRECIOS_RUB = {
    1: int(os.environ.get("GEOID_RUB_1M", "150")),
    3: int(os.environ.get("GEOID_RUB_3M", "399")),
    6: int(os.environ.get("GEOID_RUB_6M", "699")),
}

# Texto libre por si algun dia quieres otro metodo (vacio = no se muestra).
PAGO_MANUAL = os.environ.get("GEOID_PAGO_MANUAL", "").strip()


def pago_manual_activo() -> bool:
    return bool(SBP_TELEFONO or PAGO_MANUAL)
# Nombre comercial
MARCA = os.environ.get("GEOID_MARCA", "GeoiD VPN")

# --- Regalo del proxy de Telegram para planes largos ---
# Meses minimos para llevarse el proxy de regalo.
MIN_MESES_PROXY = int(os.environ.get("GEOID_PROXY_MESES", "3"))
# Dispositivos (IPs distintas) que puede usar a la vez cada proxy personal.
PROXY_DISPOSITIVOS = int(os.environ.get("GEOID_PROXY_DISPOSITIVOS", "2"))

PROXY_DOMINIO = os.environ.get("GEOID_PROXY_DOMINIO", "geoidvpn.duckdns.org")
PROXY_SERVIDOR = os.environ.get("GEOID_PROXY_SERVIDOR", "193.29.224.164")
PROXY_PUERTO = os.environ.get("GEOID_PROXY_PUERTO", "443")
PROXY_SECRETO = os.environ.get(
    "GEOID_PROXY_SECRETO",
    "ee2aafaaad9922e542f900a1fb25c68cfc67656f696476706e2e6475636b646e732e6f7267",
)


def enlace_proxy() -> str:
    """Enlace tg:// listo para tocar en el movil."""
    if not PROXY_SECRETO:
        return ""
    return (
        f"tg://proxy?server={PROXY_SERVIDOR}&port={PROXY_PUERTO}"
        f"&secret={PROXY_SECRETO}"
    )

# --- Paises disponibles ---------------------------------------------------
# Con un solo pais, el boton "Cambiar pais" no se muestra.
PAISES = [
    p.strip()
    for p in os.environ.get("GEOID_PAISES", "Finlandia").split(",")
    if p.strip()
]

# --- Idioma ---------------------------------------------------------------
# Idioma con el que empieza un cliente nuevo. Cada uno puede cambiarlo con
# el boton de idioma del menu.
IDIOMA_DEFECTO = os.environ.get("GEOID_IDIOMA", "ru").strip().lower() or "ru"

# Cuantos proxies de regalo segun los meses comprados.
PROXY_POR_MESES = {
    3: 1,
    6: 2,
}

# Dias extra de regalo segun los meses comprados.
REGALO_DIAS = {
    6: 20,
}


def proxies_de_regalo(meses: int) -> int:
    """Proxies que le corresponden a un plan."""
    return PROXY_POR_MESES.get(meses, 1 if meses >= MIN_MESES_PROXY else 0)


def dias_de_regalo(meses: int) -> int:
    """Dias extra que se suman al plan."""
    return REGALO_DIAS.get(meses, 0)

# --- Recarga de estrellas con rublos (servicio externo) -------------------
# Al cliente ruso no le deja Telegram comprar estrellas; se le manda a este
# servicio, que las vende cobrando por SBP y las entrega como regalo.
ESTRELLAS_URL = os.environ.get(
    "GEOID_ESTRELLAS_URL", "https://t.me/krabggbot"
).strip()
ESTRELLAS_SERVICIO = os.environ.get(
    "GEOID_ESTRELLAS_SERVICIO", "krab.gg bot"
).strip()

# --- Página de pagos fuera de Telegram ------------------------------------
# Telegram solo permite cobrar con estrellas dentro de los bots, así que la
# tarjeta rusa y el SBP se cobran en una página web propia.
WEB_PAGOS = os.environ.get("GEOID_WEB_PAGOS", "").strip()
