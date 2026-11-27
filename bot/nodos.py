"""Clientes de nodo: crea y borra perfiles en Finlandia (local) o Suecia (agente)."""

import json
import re
import urllib.error
import urllib.request

import config
import provision

_CABECERA = re.compile(r"^#\s*(GeoiD-vpn|plan|expira|servidor)=", re.IGNORECASE)


def lista() -> list[dict]:
    """Nodos disponibles. Finlandia siempre; Suecia si esta configurada."""
    nodos = [{
        "id": getattr(config, "NODO_ID", "fi"),
        "nombre": getattr(config, "NODO_NOMBRE", "Finlandia"),
        "bandera": getattr(config, "NODO_BANDERA", "🌍"),
        "local": True,
        "endpoint": config.ENDPOINT or f"{getattr(config, 'SERVIDOR', '')}:{getattr(config, 'PUERTO', '')}",
        "dns": config.DNS,
        "mtu": config.MTU,
    }]
    url = getattr(config, "NODO_SE_URL", "")
    token = getattr(config, "NODO_SE_TOKEN", "")
    if url and token:
        nodos.append({
            "id": "se",
            "nombre": getattr(config, "NODO_SE_NOMBRE", "Suecia"),
            "bandera": "🇸🇪",
            "local": False,
            "url": url.rstrip("/"),
            "token": token,
            "endpoint": getattr(config, "NODO_SE_ENDPOINT", ""),
            "dns": getattr(config, "NODO_SE_DNS", "10.9.10.1"),
            "mtu": getattr(config, "NODO_SE_MTU", 1280),
        })
    return nodos


def por_id(nodo_id: str | None) -> dict:
    """Devuelve el nodo pedido; si no existe, el primero (Finlandia)."""
    nodos = lista()
    for nodo in nodos:
        if nodo["id"] == (nodo_id or ""):
            return nodo
    return nodos[0]


def existe(nodo_id: str) -> bool:
    return any(nodo["id"] == nodo_id for nodo in lista())


def endpoint_de(nodo: dict) -> str:
    """Endpoint del nodo; si falta, se lo pregunta al agente."""
    if nodo.get("endpoint"):
        return nodo["endpoint"]
    if nodo["local"]:
        return config.ENDPOINT
    try:
        salud = _pedir(nodo, "/salud")
        ip = salud.get("ip_publica") or ""
        puerto = getattr(config, "NODO_SE_PUERTO", 21766)
        return f"{ip}:{puerto}" if ip else ""
    except Exception:  # noqa: BLE001
        return ""


def _pedir(nodo: dict, ruta: str, datos: dict | None = None) -> dict:
    """Llamada al agente de un nodo remoto."""
    cuerpo = None
    cabeceras = {"Authorization": f"Bearer {nodo['token']}"}
    if datos is not None:
        cuerpo = json.dumps(datos).encode("utf-8")
        cabeceras["Content-Type"] = "application/json"
    peticion = urllib.request.Request(
        f"{nodo['url']}{ruta}", data=cuerpo, headers=cabeceras, method="POST" if cuerpo else "GET",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=25) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", "ignore")
        raise RuntimeError(f"{nodo['nombre']}: HTTP {error.code} {detalle}") from error
    except Exception as error:  # noqa: BLE001
        raise RuntimeError(f"{nodo['nombre']}: {error}") from error


def _leer_conf(texto: str, campo: str) -> str:
    """Saca un valor del .conf que devuelve el agente."""
    patron = re.compile(rf"^{campo}\s*=\s*(.+)$", re.MULTILINE)
    encontrado = patron.search(texto)
    return encontrado.group(1).strip() if encontrado else ""


def crear(nodo: dict, nombre: str = "cliente") -> dict:
    """Crea un cliente en el nodo y devuelve sus claves y parametros."""
    if nodo["local"]:
        datos = provision.crear_cliente()
        return {
            "ip": datos["ip"],
            "privada": datos["privada"],
            "preshared": datos["preshared"],
            "publica": datos["publica"],
            "endpoint": nodo["endpoint"],
            "dns": nodo["dns"],
            "mtu": nodo["mtu"],
            "servidor": nodo["id"],
        }

    respuesta = _pedir(nodo, "/cliente", {"nombre": nombre})
    if not respuesta.get("ok"):
        raise RuntimeError(f"{nodo['nombre']}: {respuesta.get('error', 'sin respuesta')}")

    conf = respuesta.get("conf", "")
    endpoint = _leer_conf(conf, "Endpoint") or nodo["endpoint"]
    return {
        "ip": respuesta.get("ip") or _leer_conf(conf, "Address").split("/")[0],
        "privada": _leer_conf(conf, "PrivateKey"),
        "preshared": _leer_conf(conf, "PresharedKey"),
        "publica": respuesta.get("publica", ""),
        "endpoint": endpoint,
        "dns": _leer_conf(conf, "DNS") or nodo["dns"],
        "mtu": int(_leer_conf(conf, "MTU") or nodo["mtu"]),
        "servidor": nodo["id"],
        "conf": conf,
    }


def borrar(nodo: dict, ip: str) -> bool:
    """Elimina el cliente del nodo indicado."""
    if not ip:
        return False
    if nodo["local"]:
        usuario = None
        try:
            datos = provision._ejecutar("awg", "show", config.AWG_INTERFAZ, "dump")
            for linea in datos.splitlines()[1:]:
                partes = linea.split("\t")
                if len(partes) >= 4 and partes[3].split(",")[0] == f"{ip}/32":
                    provision.eliminar_cliente(partes[0])
                    return True
        except Exception:  # noqa: BLE001
            return False
        return False
    try:
        respuesta = _pedir(nodo, "/borrar", {"ip": ip})
        return bool(respuesta.get("ok"))
    except Exception:  # noqa: BLE001
        return False


def salud(nodo: dict) -> dict:
    if nodo["local"]:
        return {"nodo": nodo["nombre"], "local": True, "ok": True}
    try:
        return _pedir(nodo, "/salud")
    except Exception as error:  # noqa: BLE001
        return {"nodo": nodo["nombre"], "ok": False, "error": str(error)}
