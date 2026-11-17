"""Proxy MTProto personal por cliente.

Cada cliente con plan de 6 meses o mas recibe su propio proxy: un puerto y una
clave solo para el. Asi se puede limitar a 2 dispositivos y revocarlo cuando
caduca el plan.

En el servidor hace falta la plantilla systemd `mtg-user@.service` y la carpeta
`/etc/mtg/users` (las crea servidor/proxy-multiusuario.sh).
"""

import logging
import os
import subprocess
import time
from pathlib import Path

import config

log = logging.getLogger("geoid")

CARPETA = Path("/etc/mtg/users")
BIN = "/usr/local/bin/mtg"
PUERTO_BASE = 20000
PUERTO_TOPE = 40000


def disponible() -> bool:
    return Path(BIN).exists() and Path("/etc/systemd/system/mtg-user@.service").exists()


def puerto_de(tg_id: int, numero: int = 1) -> int:
    """Puerto propio. El segundo proxy usa otro puerto para el mismo cliente."""
    hueco = tg_id % ((PUERTO_TOPE - PUERTO_BASE) // 2)
    return PUERTO_BASE + hueco * 2 + (numero - 1)


def _nombre(tg_id: int, numero: int = 1) -> str:
    """Nombre del servicio: 123 para el primero, 123b para el segundo."""
    return str(tg_id) if numero <= 1 else f"{tg_id}b"


def _ruta(tg_id: int, numero: int = 1) -> Path:
    return CARPETA / f"{_nombre(tg_id, numero)}.toml"


def _systemctl(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["systemctl", *args], capture_output=True, text=True, timeout=30
    )


def _generar_clave() -> str:
    dominio = config.PROXY_DOMINIO or "www.cloudflare.com"
    salida = subprocess.run(
        [BIN, "generate-secret", "--hex", dominio],
        capture_output=True, text=True, timeout=20, check=True,
    )
    return salida.stdout.strip()


def crear(tg_id: int, clave: str | None = None, numero: int = 1) -> dict:
    """Crea (o reutiliza) el proxy personal de un cliente."""
    CARPETA.mkdir(parents=True, exist_ok=True)
    puerto = puerto_de(tg_id, numero)
    clave = clave or _generar_clave()
    nombre = _nombre(tg_id, numero)

    _ruta(tg_id, numero).write_text(
        "# Proxy personal de GeoiD\n"
        f'secret = "{clave}"\n'
        f'bind-to = "0.0.0.0:{puerto}"\n',
        encoding="utf-8",
    )
    os.chmod(_ruta(tg_id, numero), 0o600)

    _systemctl("daemon-reload")
    _systemctl("enable", f"mtg-user@{nombre}")
    _systemctl("restart", f"mtg-user@{nombre}")
    time.sleep(1)

    return {"puerto": puerto, "secreto": clave}


def eliminar(tg_id: int, numero: int = 1) -> None:
    _systemctl("disable", "--now", f"mtg-user@{_nombre(tg_id, numero)}")
    try:
        _ruta(tg_id, numero).unlink(missing_ok=True)
    except Exception:  # noqa: BLE001
        log.warning("no se pudo borrar la config del proxy %s", tg_id)


def activo(tg_id: int, numero: int = 1) -> bool:
    resultado = _systemctl("is-active", f"mtg-user@{_nombre(tg_id, numero)}")
    return resultado.stdout.strip() == "active"


def ips_conectadas(tg_id: int, numero: int = 1) -> list[str]:
    """IPs publicas conectadas a ese proxy (una por dispositivo, normalmente)."""
    puerto = puerto_de(tg_id, numero)
    try:
        salida = subprocess.run(
            ["ss", "-tn", "state", "established"],
            capture_output=True, text=True, timeout=15,
        ).stdout
    except Exception:  # noqa: BLE001
        return []

    ips: list[str] = []
    for linea in salida.splitlines():
        partes = linea.split()
        if len(partes) < 5:
            continue
        # ss: State Recv-Q Send-Q Local:Port Peer:Port
        local, remoto = partes[3], partes[4]
        if not local.endswith(f":{puerto}"):
            continue
        ip = remoto.rsplit(":", 1)[0]
        ip = ip.strip("[]")
        if ip and ip not in ips:
            ips.append(ip)
    return ips


def enlace(tg_id: int, secreto: str, numero: int = 1) -> str:
    return (
        f"tg://proxy?server={config.PROXY_SERVIDOR}"
        f"&port={puerto_de(tg_id, numero)}&secret={secreto}"
    )
