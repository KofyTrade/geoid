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


def puerto_de(tg_id: int) -> int:
    return PUERTO_BASE + (tg_id % (PUERTO_TOPE - PUERTO_BASE))


def _ruta(tg_id: int) -> Path:
    return CARPETA / f"{tg_id}.toml"


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


def crear(tg_id: int, clave: str | None = None) -> dict:
    """Crea (o reutiliza) el proxy personal de un cliente."""
    CARPETA.mkdir(parents=True, exist_ok=True)
    puerto = puerto_de(tg_id)
    clave = clave or _generar_clave()

    _ruta(tg_id).write_text(
        "# Proxy personal de GeoiD\n"
        f'secret = "{clave}"\n'
        f'bind-to = "0.0.0.0:{puerto}"\n',
        encoding="utf-8",
    )
    os.chmod(_ruta(tg_id), 0o600)

    _systemctl("daemon-reload")
    _systemctl("enable", f"mtg-user@{tg_id}")
    _systemctl("restart", f"mtg-user@{tg_id}")
    time.sleep(1)

    return {"puerto": puerto, "secreto": clave}


def eliminar(tg_id: int) -> None:
    _systemctl("disable", "--now", f"mtg-user@{tg_id}")
    try:
        _ruta(tg_id).unlink(missing_ok=True)
    except Exception:  # noqa: BLE001
        log.warning("no se pudo borrar la config del proxy %s", tg_id)


def activo(tg_id: int) -> bool:
    resultado = _systemctl("is-active", f"mtg-user@{tg_id}")
    return resultado.stdout.strip() == "active"


def ips_conectadas(tg_id: int) -> list[str]:
    """IPs publicas conectadas a ese proxy (una por dispositivo, normalmente)."""
    puerto = puerto_de(tg_id)
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


def enlace(tg_id: int, secreto: str) -> str:
    return (
        f"tg://proxy?server={config.PROXY_SERVIDOR}"
        f"&port={puerto_de(tg_id)}&secret={secreto}"
    )
