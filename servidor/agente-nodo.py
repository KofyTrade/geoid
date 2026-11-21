#!/usr/bin/env python3
"""Agente de nodo de GeoiD.

Permite al bot crear y borrar perfiles en este servidor sin usar SSH.
Escucha en un puerto local y solo responde a quien traiga el token correcto.

Variables de entorno:
  GEOID_NODO_NOMBRE      nombre visible del nodo (Finlandia, Suecia...)
  GEOID_NODO_INTERFAZ    interfaz awg (por defecto awg0)
  GEOID_NODO_CONF        ruta del .conf del servidor
  GEOID_NODO_PUERTO      puerto UDP del VPN (para el Endpoint del cliente)
  GEOID_NODO_PREFIJO     prefijo de subred (10.9.10)
  GEOID_NODO_DNS         DNS que se pone al cliente
  GEOID_NODO_MTU         MTU del cliente
  GEOID_NODO_TOKEN       clave compartida con el bot
  GEOID_NODO_IP_PUBLICA  IP publica (si no se indica, se detecta)
  GEOID_NODO_WEB_PUERTO  puerto de escucha del agente (8443)
  GEOID_NODO_PERMITIDOS  IPs autorizadas separadas por comas (opcional)
"""

import json
import os
import pathlib
import subprocess
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

NOMBRE = os.environ.get("GEOID_NODO_NOMBRE", "Nodo")
INTERFAZ = os.environ.get("GEOID_NODO_INTERFAZ", "awg0")
CONF = pathlib.Path(os.environ.get("GEOID_NODO_CONF", f"/etc/amnezia/amneziawg/{INTERFAZ}.conf"))
PUERTO_VPN = os.environ.get("GEOID_NODO_PUERTO", "21766")
PREFIJO = os.environ.get("GEOID_NODO_PREFIJO", "10.9.10")
DNS = os.environ.get("GEOID_NODO_DNS", f"{PREFIJO}.1")
MTU = os.environ.get("GEOID_NODO_MTU", "1280")
TOKEN = os.environ.get("GEOID_NODO_TOKEN", "").strip()
IP_PUBLICA = os.environ.get("GEOID_NODO_IP_PUBLICA", "").strip()
PUERTO_WEB = int(os.environ.get("GEOID_NODO_WEB_PUERTO", "8443"))
PERMITIDOS = [x.strip() for x in os.environ.get("GEOID_NODO_PERMITIDOS", "").split(",") if x.strip()]

# Parametros de ofuscacion que se copian del servidor al cliente.
CLAVES_OFUSCACION = [
    "Jc", "Jmin", "Jmax", "S1", "S2", "S3", "S4",
    "H1", "H2", "H3", "H4", "I1", "I2", "I3", "I4", "I5",
]


def ejecutar(*args: str, entrada: str | None = None) -> str:
    resultado = subprocess.run(
        args, input=entrada, capture_output=True, text=True, timeout=30, check=False,
    )
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr.strip() or f"fallo: {' '.join(args)}")
    return resultado.stdout.strip()


def parametros_servidor() -> dict[str, str]:
    texto = CONF.read_text(encoding="utf-8")
    interfaz = texto.split("[Peer]")[0]
    datos: dict[str, str] = {}
    for linea in interfaz.splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or linea.startswith("[") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        datos[clave.strip()] = valor.strip()
    return datos


def clave_publica_servidor() -> str:
    return ejecutar("awg", "pubkey", entrada=parametros_servidor()["PrivateKey"] + "\n")


def ip_publica() -> str:
    global IP_PUBLICA
    if IP_PUBLICA:
        return IP_PUBLICA
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=8) as r:
            IP_PUBLICA = r.read().decode().strip()
    except Exception:
        IP_PUBLICA = "IP_DEL_SERVIDOR"
    return IP_PUBLICA


def ips_usadas() -> set[str]:
    salida = ejecutar("awg", "show", INTERFAZ, "allowed-ips")
    usadas: set[str] = set()
    for linea in salida.splitlines():
        partes = linea.split()
        if len(partes) >= 2:
            usadas.add(partes[1].split("/")[0])
    return usadas


def siguiente_ip() -> str:
    usadas = ips_usadas()
    for n in range(2, 250):
        candidata = f"{PREFIJO}.{n}"
        if candidata not in usadas:
            return candidata
    raise RuntimeError("no quedan IPs libres en este nodo")


def crear_cliente(nombre: str) -> dict:
    ip = siguiente_ip()
    privada = ejecutar("awg", "genkey")
    publica = ejecutar("awg", "pubkey", entrada=privada + "\n")
    psk = ejecutar("awg", "genpsk")

    ruta_psk = pathlib.Path("/tmp") / f"psk-{publica[:12]}"
    ruta_psk.write_text(psk, encoding="utf-8")
    os.chmod(ruta_psk, 0o600)
    try:
        ejecutar(
            "awg", "set", INTERFAZ, "peer", publica,
            "preshared-key", str(ruta_psk), "allowed-ips", f"{ip}/32",
        )
    finally:
        ruta_psk.unlink(missing_ok=True)

    with CONF.open("a", encoding="utf-8") as f:
        f.write(
            f"\n[Peer]\n# {nombre}\nPublicKey = {publica}\n"
            f"PresharedKey = {psk}\nAllowedIPs = {ip}/32\n"
        )

    params = parametros_servidor()
    lineas = [
        "# GeoiD-vpn",
        "# plan=pago",
        f"# servidor={NOMBRE}",
        "[Interface]",
        f"PrivateKey = {privada}",
        f"Address = {ip}/32",
        f"DNS = {DNS}",
        f"MTU = {MTU}",
    ]
    for clave in CLAVES_OFUSCACION:
        if clave in params:
            lineas.append(f"{clave} = {params[clave]}")
    lineas += [
        "",
        "[Peer]",
        f"PublicKey = {clave_publica_servidor()}",
        f"PresharedKey = {psk}",
        f"Endpoint = {ip_publica()}:{PUERTO_VPN}",
        "AllowedIPs = 0.0.0.0/0",
        "PersistentKeepalive = 25",
        "",
    ]
    return {"ip": ip, "publica": publica, "conf": "\n".join(lineas)}


def borrar_cliente(ip: str) -> bool:
    salida = ejecutar("awg", "show", INTERFAZ, "dump")
    publica = ""
    for linea in salida.splitlines()[1:]:
        partes = linea.split("\t")
        if len(partes) >= 4 and partes[3].split(",")[0] == f"{ip}/32":
            publica = partes[0]
            break
    if not publica:
        return False
    ejecutar("awg", "set", INTERFAZ, "peer", publica, "remove")

    texto = CONF.read_text(encoding="utf-8")
    bloques = texto.split("[Peer]")
    quedan = [b for b in bloques[1:] if publica not in b]
    CONF.write_text(bloques[0] + "".join("[Peer]" + b for b in quedan), encoding="utf-8")
    return True


def listar_clientes() -> list[dict]:
    salida = ejecutar("awg", "show", INTERFAZ, "dump")
    ahora = __import__("time").time()
    lista = []
    for linea in salida.splitlines()[1:]:
        partes = linea.split("\t")
        if len(partes) < 8:
            continue
        handshake = int(partes[4] or 0)
        lista.append({
            "ip": partes[3].split(",")[0].split("/")[0],
            "handshake": handshake,
            "conectado": bool(handshake and (ahora - handshake) < 180),
            "recibido": int(partes[5] or 0),
            "enviado": int(partes[6] or 0),
        })
    return lista


class Manejador(BaseHTTPRequestHandler):
    server_version = "GeoiDAgente/1"

    def _autorizado(self) -> bool:
        # La propia maquina siempre puede consultarse (comprobaciones locales).
        origen = self.client_address[0]
        locales = {"127.0.0.1", "::1", "localhost"}
        if PERMITIDOS and origen not in PERMITIDOS and origen not in locales:
            return False
        cabecera = self.headers.get("Authorization", "")
        return TOKEN and cabecera == f"Bearer {TOKEN}"

    def _responder(self, datos: dict, codigo: int = 200) -> None:
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self) -> None:  # noqa: N802
        if not self._autorizado():
            return self._responder({"error": "no autorizado"}, 401)
        if self.path == "/salud":
            try:
                cuantos = len(listar_clientes())
                return self._responder({
                    "nodo": NOMBRE,
                    "interfaz": INTERFAZ,
                    "ip_publica": ip_publica(),
                    "clientes": cuantos,
                    "ok": True,
                })
            except Exception as error:  # noqa: BLE001
                return self._responder({
                    "nodo": NOMBRE, "ok": False, "error": str(error),
                }, 500)
        if self.path == "/clientes":
            try:
                return self._responder({"nodo": NOMBRE, "clientes": listar_clientes()})
            except Exception as error:  # noqa: BLE001
                return self._responder({"nodo": NOMBRE, "error": str(error)}, 500)
        self._responder({"error": "no encontrado"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        if not self._autorizado():
            return self._responder({"error": "no autorizado"}, 401)
        largo = int(self.headers.get("Content-Length", "0") or 0)
        try:
            datos = json.loads(self.rfile.read(largo) or b"{}")
        except json.JSONDecodeError:
            return self._responder({"error": "json invalido"}, 400)

        try:
            if self.path == "/cliente":
                nombre = str(datos.get("nombre") or "cliente")[:40]
                return self._responder({"ok": True, **crear_cliente(nombre)})
            if self.path == "/borrar":
                ip = str(datos.get("ip") or "")
                hecho = borrar_cliente(ip)
                return self._responder({"ok": hecho, "ip": ip}, 200 if hecho else 404)
        except Exception as error:  # noqa: BLE001
            return self._responder({"error": str(error)}, 500)
        self._responder({"error": "no encontrado"}, 404)

    def log_message(self, formato: str, *args) -> None:
        return


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("falta GEOID_NODO_TOKEN")
    print(f"agente de {NOMBRE} escuchando en 0.0.0.0:{PUERTO_WEB}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PUERTO_WEB), Manejador).serve_forever()
