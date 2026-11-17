#!/usr/bin/env python3
"""Página de pago de GeoiD (fuera de Telegram).

Se instala en el servidor y atiende en un puerto local; Caddy le pone HTTPS.
El cliente paga por SBP viendo el QR, pulsa «Ya he pagado» y al dueño le llega
el aviso con el botón de activar (igual que antes, pero cobrando fuera del bot,
que es lo que Telegram permite).

URL:  https://<dominio>/?p=<meses>&u=<telegram_id>
"""

import html
import os
import pathlib
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = pathlib.Path(__file__).resolve().parent
QR = BASE / "qr.png"

TOKEN = os.environ.get("GEOID_TOKEN", "").strip()
ADMIN = os.environ.get("GEOID_ADMIN", "").strip()
AVISOS = os.environ.get("GEOID_AVISOS_ID", "").strip()
SBP = os.environ.get("GEOID_SBP_TELEFONO", "").strip()
TITULAR = os.environ.get("GEOID_SBP_TITULAR", "").strip()

PRECIOS = {
    1: int(os.environ.get("GEOID_RUB_1M", "150")),
    3: int(os.environ.get("GEOID_RUB_3M", "399")),
    6: int(os.environ.get("GEOID_RUB_6M", "699")),
}

DIAS = {1: 30, 3: 90, 6: 120}   # 6 meses llevan 20 días de regalo
PROXIS = {1: 0, 3: 1, 6: 2}

ESTILO = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#05161a;color:#e8fbf7;font-family:-apple-system,Segoe UI,Roboto,sans-serif;
     padding:20px 14px;min-height:100vh;overflow-x:hidden}
.caja{width:100%;max-width:400px;margin:0 auto;background:#0b2429;border:1px solid #1e5a58;
      border-radius:22px;padding:22px}
h1{font-size:15px;letter-spacing:2px;color:#5fd9c8;font-weight:500;text-align:center;margin-bottom:4px}
h2{font-size:13px;color:#7fa8a4;font-weight:400;text-align:center;margin-bottom:20px}
.plan{background:#13333a;border-radius:14px;padding:14px 16px;margin-bottom:16px}
.plan .fila{display:flex;justify-content:space-between;font-size:14px;padding:3px 0}
.plan .fila b{color:#2ee6c5}
.qr{background:#fff;border-radius:16px;padding:10px;text-align:center;margin-bottom:16px}
.qr img{width:100%;max-width:280px;display:block;margin:0 auto}
.telefono{font-size:13px;color:#7fa8a4;text-align:center;margin-bottom:16px}
.telefono code{color:#e8fbf7;font-size:14px}
button{width:100%;padding:15px;border:none;border-radius:16px;background:#2ee6c5;
       color:#05161a;font-size:15px;font-weight:600;cursor:pointer}
button:active{transform:scale(.99)}
.pasos{font-size:12px;color:#4e7c79;line-height:1.5;margin-top:14px}
.aviso{font-size:11px;color:#4e7c79;text-align:center;margin-top:16px;line-height:1.4}
.ok{text-align:center;font-size:15px;line-height:1.5}
.ok b{color:#2ee6c5}
.boton-telegram{display:block;text-align:center;margin-top:18px;padding:14px;
  border-radius:16px;background:#13333a;color:#9be8dc;text-decoration:none;font-size:14px}
"""


def pagina_pago(meses: int, uid: str) -> str:
    precio = PRECIOS.get(meses, PRECIOS[1])
    dias = DIAS.get(meses, 30)
    proxis = PROXIS.get(meses, 0)
    regalo = ""
    if proxis:
        regalo = f" + {proxis} proxy(s) de Telegram"
    if meses == 6:
        regalo += " + 20 días extra"

    tiene_qr = QR.exists()
    bloque_qr = (
        f'<div class="qr"><img src="/qr.png" alt="QR de pago"></div>'
        if tiene_qr
        else '<div class="plan"><div class="fila"><span>QR no configurado</span></div></div>'
    )
    # Solo el QR: el número y el titular no se muestran en la página.

    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GeoiD VPN · pago</title><style>{ESTILO}</style></head><body><div class="caja">
<h1>GEOID-VPN</h1><h2>Pago de la suscripción</h2>
<div class="plan">
  <div class="fila"><span>Plan</span><b>{'1 mes' if meses == 1 else str(meses) + ' meses'}</b></div>
  <div class="fila"><span>Acceso</span><b>{dias} días</b></div>
  <div class="fila"><span>Importe</span><b>{precio} ₽</b></div>
</div>
{bloque_qr}
<form method="post" action="/paguei">
  <input type="hidden" name="p" value="{meses}">
  <input type="hidden" name="u" value="{html.escape(uid)}">
  <button type="submit">Ya he pagado {precio} ₽</button>
</form>
<div class="pasos">
  1. Escanea el QR con tu banco.<br>
  2. Envía <b>{precio} ₽</b> y confirma.<br>
  3. Vuelve aquí y pulsa el botón.
</div>
<div class="aviso">Tu acceso se activa en minutos{(' · ' + regalo) if regalo else ''}.<br>
Recibirás la configuración en Telegram.</div>
</div></body></html>"""


def pagina_ok(meses: int) -> str:
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GeoiD VPN · gracias</title><style>{ESTILO}</style></head><body><div class="caja">
<h1>GEOID-VPN</h1><h2>Pago recibido</h2>
<div class="ok">Hemos recibido tu aviso.<br>
En cuanto se confirme el ingreso, tu suscripción de
<b>{'1 mes' if meses == 1 else str(meses) + ' meses'}</b> se activa sola y
recibes la configuración en <b>Telegram</b>.</div>
<a class="boton-telegram" href="https://t.me/geoidvpn_bot">Volver a mi bot de Telegram</a>
<div class="aviso">Si tienes cualquier duda, escribe al bot y te contestamos.</div>
</div></body></html>"""


def avisar_telegram(meses: int, uid: str) -> None:
    """Manda el aviso al dueño con el botón de activar."""
    destino = AVISOS or ADMIN
    if not (TOKEN and destino):
        return

    precio = PRECIOS.get(meses, 0)
    texto = (
        f"💰 <b>PAGO {precio} ₽ · {meses} mes(es)</b>\n\n"
        f"Cliente: ID <code>{html.escape(uid)}</code>\n"
        "Pagó por la web (tarjeta/SBP).\n\n"
        "Pulsa el botón cuando veas el ingreso en el banco:"
    )
    teclado = {
        "inline_keyboard": [[{
            "text": f"✅ Activar {meses} mes(es)",
            "callback_data": f"act:{uid}:{meses}",
        }]]
    }
    datos = urllib.parse.urlencode({
        "chat_id": destino,
        "text": texto,
        "parse_mode": "HTML",
        "reply_markup": __import__("json").dumps(teclado),
    }).encode()
    try:
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data=datos,
            timeout=15,
        ).read()
    except Exception:  # noqa: BLE001
        pass


class Manejador(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        ruta = urllib.parse.urlparse(self.path)
        if ruta.path == "/qr.png":
            return self.servir_qr()
        if ruta.path in ("/", "/pagar"):
            consulta = urllib.parse.parse_qs(ruta.query)
            try:
                meses = int(consulta.get("p", ["1"])[0])
            except ValueError:
                meses = 1
            uid = consulta.get("u", ["0"])[0]
            return self.enviar(pagina_pago(meses if meses in PRECIOS else 1, uid))
        self.enviar("<h1>No encontrado</h1>", 404)

    def do_POST(self) -> None:  # noqa: N802
        largo = int(self.headers.get("Content-Length", "0") or 0)
        datos = urllib.parse.parse_qs(self.rfile.read(largo).decode())
        try:
            meses = int(datos.get("p", ["1"])[0])
        except ValueError:
            meses = 1
        uid = datos.get("u", ["0"])[0]
        avisar_telegram(meses, uid)
        self.enviar(pagina_ok(meses))

    def servir_qr(self) -> None:
        if not QR.exists():
            self.enviar("<h1>Sin QR</h1>", 404)
            return
        contenido = QR.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(contenido)))
        self.send_header("Cache-Control", "public, max-age=600")
        self.end_headers()
        self.wfile.write(contenido)

    def enviar(self, cuerpo: str, codigo: int = 200) -> None:
        datos = cuerpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def log_message(self, formato: str, *args) -> None:  # silencio
        return


if __name__ == "__main__":
    puerto = int(os.environ.get("GEOID_WEB_PUERTO", "8099"))
    direccion = os.environ.get("GEOID_WEB_BIND", "127.0.0.1").strip() or "127.0.0.1"
    print(f"página de pagos escuchando en {direccion}:{puerto}", flush=True)
    ThreadingHTTPServer((direccion, puerto), Manejador).serve_forever()
