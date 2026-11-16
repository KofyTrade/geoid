"""Aprovisionamiento de clientes AmneziaWG en el servidor.

Todo se hace con la propia herramienta `awg` y leyendo el fichero de
configuración del servidor, así que funciona con la instalación que ya existe.
"""

import os
import re
import subprocess
import tempfile

import config
import db


def _ejecutar(*args: str, entrada: str | None = None) -> str:
    resultado = subprocess.run(
        args,
        input=entrada,
        capture_output=True,
        text=True,
        check=False,
    )
    if resultado.returncode != 0:
        raise RuntimeError(
            f"{' '.join(args)}: {resultado.stderr.strip() or resultado.returncode}"
        )
    return resultado.stdout.strip()


def _parametros_interfaz() -> dict[str, str]:
    """Lee del .conf del servidor los parámetros de ofuscación."""
    with open(config.AWG_CONF, "r", encoding="utf-8") as f:
        texto = f.read()

    interfaz = texto.split("[Peer]")[0]
    parametros: dict[str, str] = {}
    for linea in interfaz.splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or linea.startswith("["):
            continue
        if "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        parametros[clave.strip()] = valor.strip()

    if "PrivateKey" not in parametros:
        raise RuntimeError("el .conf del servidor no tiene PrivateKey")
    return parametros


def _clave_publica_servidor() -> str:
    """Clave pública del servidor a partir de su clave privada."""
    parametros = _parametros_interfaz()
    return _ejecutar("awg", "pubkey", entrada=parametros["PrivateKey"] + "\n")


def _siguiente_ip(usadas: set[str]) -> str:
    for n in range(config.IP_MIN, config.IP_MAX + 1):
        candidata = f"{config.RED}{n}"
        if candidata not in usadas:
            return candidata
    raise RuntimeError("no quedan direcciones libres")


def _anadir_al_fichero(publica: str, preshared: str, ip: str):
    """Deja el peer escrito para que sobreviva a un reinicio."""
    with open(config.AWG_CONF, "a", encoding="utf-8") as f:
        f.write(
            "\n[Peer]\n"
            f"PublicKey = {publica}\n"
            f"PresharedKey = {preshared}\n"
            f"AllowedIPs = {ip}/32\n"
        )


def _quitar_del_fichero(publica: str) -> None:
    with open(config.AWG_CONF, "r", encoding="utf-8") as f:
        bloques = f.read().split("\n[Peer]")

    if not bloques:
        return

    cabecera, peers = bloques[0], bloques[1:]
    conservados = [p for p in peers if publica not in p]

    with open(config.AWG_CONF, "w", encoding="utf-8") as f:
        f.write(cabecera)
        for p in conservados:
            f.write("\n[Peer]" + p)


def crear_cliente() -> dict:
    """Genera claves, registra el peer en el servidor y devuelve los datos."""
    usadas = db.ips_en_uso()
    ip = _siguiente_ip(usadas)

    privada = _ejecutar("awg", "genkey")
    publica = _ejecutar("awg", "pubkey", entrada=privada + "\n")
    preshared = _ejecutar("awg", "genpsk")

    # El peer en caliente (sin reiniciar el servicio).
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(preshared)
        ruta_psk = tmp.name
    try:
        os.chmod(ruta_psk, 0o600)
        _ejecutar(
            "awg", "set", config.AWG_INTERFAZ,
            "peer", publica,
            "preshared-key", ruta_psk,
            "allowed-ips", f"{ip}/32",
        )
    finally:
        os.unlink(ruta_psk)

    _anadir_al_fichero(publica, preshared, ip)

    return {
        "ip": ip,
        "privada": privada,
        "publica": publica,
        "preshared": preshared,
    }


def eliminar_cliente(publica: str) -> None:
    try:
        _ejecutar(
            "awg", "set", config.AWG_INTERFAZ,
            "peer", publica, "remove",
        )
    except RuntimeError:
        pass  # ya no estaba
    try:
        _quitar_del_fichero(publica)
    except OSError:
        pass


def generar_conf(privada: str, preshared: str, ip: str) -> str:
    """Devuelve el fichero .conf listo para el cliente."""
    parametros = _parametros_interfaz()
    servidor = _clave_publica_servidor()

    # Claves de ofuscación que deben ir también en el cliente.
    ofuscacion = [
        "Jc", "Jmin", "Jmax",
        "S1", "S2", "S3", "S4",
        "H1", "H2", "H3", "H4",
        "I1", "I2", "I3", "I4", "I5",
        "HeaderProtectionKey", "ContentPaddingAddition",
        "RandomTrailers", "DisableCookies",
    ]

    lineas = [
        "[Interface]",
        f"PrivateKey = {privada}",
        f"Address = {ip}/32",
        f"DNS = {config.DNS}",
        f"MTU = {config.MTU}",
    ]
    for clave in ofuscacion:
        if clave in parametros:
            lineas.append(f"{clave} = {parametros[clave]}")

    lineas += [
        "",
        "[Peer]",
        f"PublicKey = {servidor}",
        f"PresharedKey = {preshared}",
        f"Endpoint = {config.ENDPOINT}",
        "AllowedIPs = 0.0.0.0/0",
        "PersistentKeepalive = 25",
        "",
    ]
    return "\n".join(lineas)


def revisar_servidor() -> list[str]:
    """Comprobaciones rápidas para el comando /estado del administrador."""
    avisos: list[str] = []
    if not os.path.exists(config.AWG_CONF):
        avisos.append(f"no existe {config.AWG_CONF}")
    try:
        salida = _ejecutar("awg", "show", config.AWG_INTERFAZ)
        if not re.search(r"peer:", salida):
            avisos.append("la interfaz no tiene peers")
    except RuntimeError as e:
        avisos.append(f"awg no responde: {e}")
    return avisos

def endpoints() -> dict[str, str]:
    """IP publica de cada peer conectado: {clave_publica: ip}."""
    try:
        salida = _ejecutar("awg", "show", config.AWG_INTERFAZ, "dump")
    except Exception:  # noqa: BLE001
        return {}

    salida = (salida or "").strip()
    if not salida:
        return {}

    ip_por_clave: dict[str, str] = {}
    for numero, linea in enumerate(salida.splitlines()):
        if numero == 0:
            continue  # primera linea = interfaz
        partes = linea.split("\t")
        if len(partes) < 3:
            continue
        clave, endpoint = partes[0], partes[2]
        if not endpoint or endpoint == "(none)":
            continue
        # endpoint viene como 1.2.3.4:56789 o [2001:db8::1]:56789
        if endpoint.startswith("["):
            ip = endpoint[1:endpoint.find("]")]
        else:
            ip = endpoint.rsplit(":", 1)[0]
        if ip:
            ip_por_clave[clave] = ip

    return ip_por_clave
