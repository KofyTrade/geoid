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
    1: float(os.environ.get("GEOID_USD_1M", "2.5")),
    3: float(os.environ.get("GEOID_USD_3M", "6.5")),
    12: float(os.environ.get("GEOID_USD_12M", "21")),
}

# --- Pago con SBP / tarjeta rusa (manual) ---
# Se activa solo con poner tu telefono. Es la via mas facil para el cliente
# ruso: abre su banco, escanea el QR y paga.
SBP_TELEFONO = os.environ.get("GEOID_SBP_TELEFONO", "").strip()
SBP_TITULAR = os.environ.get("GEOID_SBP_TITULAR", "").strip()
SBP_QR_URL = os.environ.get("GEOID_SBP_QR_URL", "").strip()   # imagen opcional

# Precios en rublos para este metodo.
PRECIOS_RUB = {
    1: int(os.environ.get("GEOID_RUB_1M", "199")),
    3: int(os.environ.get("GEOID_RUB_3M", "539")),
    12: int(os.environ.get("GEOID_RUB_12M", "1690")),
}

# Texto libre por si algun dia quieres otro metodo (vacio = no se muestra).
PAGO_MANUAL = os.environ.get("GEOID_PAGO_MANUAL", "").strip()


def pago_manual_activo() -> bool:
    return bool(SBP_TELEFONO or PAGO_MANUAL)
# Nombre comercial
MARCA = os.environ.get("GEOID_MARCA", "GeoiD VPN")
