"""Pagos con criptomonedas mediante Crypto Pay (@CryptoBot).

No necesita servidor web: se consulta la lista de facturas pagadas cada poco
tiempo. Solo hay que crear una app en @CryptoBot -> Crypto Pay y copiar el token.
"""

import logging

import aiohttp

import config

log = logging.getLogger("geoid.crypto")

BASE = "https://pay.crypt.bot/api"


def _cabeceras() -> dict:
    return {"Crypto-Pay-API-Token": config.CRYPTO_TOKEN}


def disponible() -> bool:
    return bool(config.CRYPTO_TOKEN)


async def crear_factura(meses: int, tg_id: int) -> dict | None:
    """Crea una factura y devuelve {url, id} o None si falla."""
    if not disponible():
        return None

    monto = config.PRECIOS_USD.get(meses)
    if not monto:
        return None

    datos = {
        "currency_type": "crypto",
        "asset": config.CRYPTO_MONEDA,
        "amount": f"{monto:.2f}",
        "description": f"{config.MARCA} · {meses} mes(es)",
        "payload": f"geoid:{tg_id}:{meses}",
        "allow_comments": False,
        "allow_anonymous": True,
        "expires_in": 3600,
    }

    try:
        async with aiohttp.ClientSession() as sesion:
            async with sesion.post(
                f"{BASE}/createInvoice", json=datos, headers=_cabeceras(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as respuesta:
                cuerpo = await respuesta.json(content_type=None)
    except Exception as e:  # noqa: BLE001
        log.warning("no se pudo crear la factura: %s", e)
        return None

    if not cuerpo.get("ok"):
        log.warning("Crypto Pay rechazó la factura: %s", cuerpo)
        return None

    factura = cuerpo["result"]
    return {
        "id": factura.get("invoice_id"),
        "url": factura.get("bot_invoice_url") or factura.get("mini_app_invoice_url"),
        "monto": monto,
    }


async def facturas_pagadas(limite: int = 50) -> list[dict]:
    """Devuelve las facturas en estado 'paid'."""
    if not disponible():
        return []

    try:
        async with aiohttp.ClientSession() as sesion:
            async with sesion.get(
                f"{BASE}/getInvoices",
                params={"status": "paid", "count": limite},
                headers=_cabeceras(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as respuesta:
                cuerpo = await respuesta.json(content_type=None)
    except Exception as e:  # noqa: BLE001
        log.warning("no se pudo consultar las facturas: %s", e)
        return []

    if not cuerpo.get("ok"):
        return []
    return cuerpo["result"].get("items") or []


def leer_payload(payload: str) -> tuple[int, int] | None:
    """'geoid:123456:3' -> (123456, 3)."""
    partes = (payload or "").split(":")
    if len(partes) != 3 or partes[0] != "geoid":
        return None
    try:
        return int(partes[1]), int(partes[2])
    except ValueError:
        return None
