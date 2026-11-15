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
DIAS_INVITADO = int(os.environ.get("GEOID_DIAS_INVITADO", "7"))  # bonus por invitar

# Precios en estrellas de Telegram (XTR). 1 estrella ~ 0,013 $.
PRECIOS = {
    1: int(os.environ.get("GEOID_PRECIO_1M", "150")),
    3: int(os.environ.get("GEOID_PRECIO_3M", "400")),
    12: int(os.environ.get("GEOID_PRECIO_12M", "1200")),
}

# --- Ficheros ---
DIR_DATOS = os.environ.get("GEOID_DATOS", "/var/lib/geoid-bot")
DB = os.path.join(DIR_DATOS, "bot.sqlite")

# Enlaces de la aplicación (los releases del repositorio).
URL_APP = "https://github.com/KofyTrade/geoid/releases/latest"
URL_ANDROID = (
    "https://github.com/KofyTrade/geoid/releases/latest/download/"
    "GeoiD-vpn-Android-3.0.3-arm64-v8a.apk"
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
    1: float(os.environ.get("GEOID_USD_1M", "3.5")),
    3: float(os.environ.get("GEOID_USD_3M", "9")),
    12: float(os.environ.get("GEOID_USD_12M", "30")),
}

# --- Pago manual (transferencia rusa / tarjeta) ---
# Texto que se muestra al cliente. Pon tus datos reales.
PAGO_MANUAL = os.environ.get(
    "GEOID_PAGO_MANUAL",
    "Transferencia a la tarjeta 0000 0000 0000 0000 (nombre) o por SBP al "
    "telefono +7 000 000 00 00. En el comentario escribe tu ID de Telegram.",
)
# Nombre comercial
MARCA = os.environ.get("GEOID_MARCA", "GeoiD VPN")
