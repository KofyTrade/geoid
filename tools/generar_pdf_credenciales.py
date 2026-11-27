"""Genera el PDF de credenciales de GeoiD VPN (version 5.0).

Todo corre en UN servidor: Suecia. Este documento describe esa realidad.
Ni el .docx ni el .pdf se suben al repositorio (estan en .gitignore).
"""

import base64
import pathlib
import textwrap

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

SALIDA = pathlib.Path(r"E:\PC\vpn\CREDENCIALES-GeoiD.docx")

TURQUESA = RGBColor(0x0E, 0x8C, 0x7F)
GRIS = RGBColor(0x44, 0x55, 0x55)
ROJO = RGBColor(0xB0, 0x30, 0x20)

# --------------------------------------------------------------- secretos
SECRETOS = pathlib.Path(r"E:\PC\vpn\.secretos")


def leer_secreto(nombre: str) -> str:
    ruta = SECRETOS / nombre
    if ruta.exists():
        return ruta.read_text(encoding="utf-8", errors="ignore").strip()
    return ""


ENV = pathlib.Path(r"E:\PC\vpn\env-suecia.txt")
if not ENV.exists():
    ENV = pathlib.Path(r"E:\PC\vpn\env-finlandia.txt")


def valor_env(clave: str) -> str:
    if not ENV.exists():
        return ""
    for linea in ENV.read_text(encoding="utf-8", errors="ignore").splitlines():
        linea = linea.strip()
        if linea.startswith(clave + "="):
            return linea.split("=", 1)[1].strip()
    return ""


TOKEN_BOT = valor_env("GEOID_TOKEN") or leer_secreto("bot-token.txt")
TOKEN_CRIPTO = valor_env("GEOID_CRYPTO_TOKEN") or "6784775:AAj67eg3YQhmou2GexKrzwEwyPFta7F05wt"
ADMIN_ID = valor_env("GEOID_ADMIN") or "6887964554"
SBP_TEL = valor_env("GEOID_SBP_TELEFONO") or "+7 9313936329"
SBP_TITULAR = valor_env("GEOID_SBP_TITULAR") or "ERNESTO LOPEZ"
TOKEN_AGENTE = "ixDWEdMiiOwB3YfiBa4qUsIfvha1r8njkJI10o7GgBqkNHR"

doc = Document()

normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(10.5)
normal.paragraph_format.space_after = Pt(4)

seccion = doc.sections[0]
seccion.top_margin = Cm(2)
seccion.bottom_margin = Cm(2)
seccion.left_margin = Cm(2.2)
seccion.right_margin = Cm(2.2)


def titulo(texto: str, nivel: int = 0) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14 if nivel else 0)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(texto)
    r.bold = True
    r.font.size = Pt(15 if nivel == 0 else 12)
    r.font.color.rgb = TURQUESA
    p.paragraph_format.keep_with_next = True
    if nivel:
        pPr = p._p.get_or_add_pPr()
        borde = OxmlElement("w:pBdr")
        abajo = OxmlElement("w:bottom")
        abajo.set(qn("w:val"), "single")
        abajo.set(qn("w:sz"), "6")
        abajo.set(qn("w:color"), "0E8C7F")
        borde.append(abajo)
        pPr.append(borde)


def parrafo(texto: str, negrita: bool = False, color: RGBColor | None = None,
            tam: float = 10.5, espacio: int = 4) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(espacio)
    r = p.add_run(texto)
    r.bold = negrita
    r.font.size = Pt(tam)
    if color is not None:
        r.font.color.rgb = color


def aviso(texto: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run("⚠  " + texto)
    r.bold = True
    r.font.size = Pt(10)
    r.font.color.rgb = ROJO


def tabla(filas: list[tuple[str, str]]) -> None:
    t = doc.add_table(rows=0, cols=2)
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    for campo, valor in filas:
        celdas = t.add_row().cells
        celdas[0].width = Cm(4.6)
        celdas[1].width = Cm(11.4)
        r0 = celdas[0].paragraphs[0].add_run(campo)
        r0.bold = True
        r0.font.size = Pt(9.5)
        r1 = celdas[1].paragraphs[0].add_run(valor)
        r1.font.size = Pt(9.5)
    _no_partir(t)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def codigo(bloque: str) -> None:
    t = doc.add_table(rows=1, cols=1)
    t.style = "Table Grid"
    celda = t.rows[0].cells[0]
    sombreado = OxmlElement("w:shd")
    sombreado.set(qn("w:fill"), "F2F6F5")
    celda._tc.get_or_add_tcPr().append(sombreado)
    celda.paragraphs[0].text = ""
    primero = True
    for linea in bloque.split("\n"):
        p = celda.paragraphs[0] if primero else celda.add_paragraph()
        primero = False
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(linea if linea else " ")
        r.font.name = "Consolas"
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(0x11, 0x33, 0x2E)
    _no_partir(t)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def _no_partir(tabla_obj) -> None:
    for fila in tabla_obj.rows:
        trPr = fila._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))


def bloque_b64(ruta: pathlib.Path) -> str:
    if not ruta.exists():
        return ""
    datos = base64.b64encode(ruta.read_bytes()).decode()
    return "\n".join(textwrap.wrap(datos, 76))


# =============================================================== portada
titulo("GeoiD VPN")
titulo("Credenciales, accesos y comandos")
parrafo("Versión 5.0.0 · 27 de noviembre de 2026 · todo en un solo servidor (Suecia)",
        color=GRIS, tam=10)
aviso("Este documento contiene contraseñas y claves en texto plano. No lo envíes "
      "por chat ni lo subas a la nube sin cifrar. Guárdalo en un pendrive.")

# =============================================================== 1 acceso
titulo("1 · Acceso al servidor", 1)
parrafo("Abrir sesión en el servidor. En PowerShell de tu PC:")
codigo("ssh root@194.76.136.210        # contrasena: 2UGTCkTiLPjJ")

parrafo("Copiar archivos entre el PC y el servidor:", negrita=True, espacio=2)
codigo("""# subir todo el bot
scp E:\\PC\\vpn\\bot\\*.py root@194.76.136.210:/opt/geoid-bot/

# subir un archivo suelto
scp E:\\PC\\vpn\\bot\\bot.py root@194.76.136.210:/opt/geoid-bot/

# bajar una copia de la base de datos al PC
scp root@194.76.136.210:/var/lib/geoid-bot/bot.sqlite E:\\PC\\vpn\\""")

parrafo("Qué ventana estás usando:", negrita=True, espacio=2)
tabla([
    ("PS C:\\Users\\KOFY>", "tu PC · aquí van ssh, scp y git"),
    ("root@petite-ivory:~#", "el servidor · aquí van systemctl, awg, nano"),
    ("exit", "para salir del servidor"),
])

# =============================================================== 2 servidor
titulo("2 · El servidor (Suecia)", 1)
tabla([
    ("Proveedor", "Aeza · https://my.aeza.net"),
    ("IP", "194.76.136.210"),
    ("Usuario", "root · contraseña 2UGTCkTiLPjJ"),
    ("Tarifa", "SWE-PROMO · 1,99 €/mes"),
    ("Sistema", "Ubuntu 26.04 LTS"),
    ("Dominio de la web", "194.76.136.210.sslip.io (apunta solo a esta IP)"),
])

parrafo("Todo lo que corre aquí:", negrita=True, espacio=2)
tabla([
    ("awg-quick@awg0", "túnel VPN · 21766/udp"),
    ("geoid-bot", "bot de Telegram · python en /opt/geoid-bot"),
    ("geoid-agente", "API de perfiles · 8443/tcp"),
    ("dnsmasq", "DNS con bloqueo · 10.9.10.1:53"),
    ("caddy", "web HTTPS · 443/tcp"),
    ("bukinist", "la web de la librería · node en 127.0.0.1:3000"),
])

aviso("Finlandia (193.29.224.164) queda RETIRADO: el bot y los perfiles ya no "
      "están allí. Ese servidor caduca el 13.12.2026 y no se renueva.")

# =============================================================== 3 vpn
titulo("3 · Túnel VPN (WireGuard ofuscado)", 1)
tabla([
    ("Interfaz", "awg0 · /etc/amnezia/amneziawg/awg0.conf"),
    ("Subred", "10.9.10.0/24 · servidor 10.9.10.1 · clientes desde 10.9.10.2"),
    ("Puerto", "21766/udp · MTU 1280"),
    ("DNS interno", "10.9.10.1 (dnsmasq con listas de anuncios)"),
    ("Ofuscación", "Jc 4 · Jmin 77 · Jmax 170 · S1 20 · S2 93 · S3 33 · S4 27 · H1-H4"),
    ("QUIC bloqueado", "sí (regla en PostUp: UDP/443 se descarta)"),
    ("Aceleración", "BBR · ip_forward activo"),
    ("Ver el túnel", "awg show awg0"),
])

parrafo("Crear un perfil a mano (si el bot no está disponible):", negrita=True, espacio=2)
codigo("""bash /root/cliente.sh nombreCliente
bash /root/cliente.sh --listar
bash /root/cliente.sh --borrar 10.9.10.3
# los .conf quedan en /root/clientes-suecia/""")

# =============================================================== 4 bot
titulo("4 · Bot de Telegram", 1)
tabla([
    ("Bot", "@geoidvpn_bot (GeoiD VPN)"),
    ("ID del bot", "9195295915"),
    ("Tu ID", ADMIN_ID + " (administrador)"),
    ("Código", "/opt/geoid-bot (python del .venv)"),
    ("Configuración", "/etc/geoid-bot.env"),
    ("Base de datos", "/var/lib/geoid-bot/bot.sqlite"),
    ("Servicio", "systemctl status geoid-bot"),
    ("Registro", "journalctl -u geoid-bot -f"),
    ("Nodo que representa", "Suecia · GEOID_NODO_ID=se"),
])

parrafo("Comandos de administrador (solo desde tu privado):", negrita=True, espacio=2)
tabla([
    ("/estado", "clientes activos, precios y avisos"),
    ("/diag", "versión, configuración y nodos"),
    ("/activar ID MESES", "activa un pago por QR o transferencia"),
    ("/regalar ID DIAS", "regala días a un cliente"),
    ("/promo CODIGO DIAS USOS", "crea un código promocional"),
    ("/promos", "lista los códigos"),
    ("/enlaces", "versión publicada y descargas"),
    ("/qr", "guarda el QR de cobro (envía la foto con /qr)"),
    ("/chatid", "dice el ID del grupo donde se escribe"),
])

# =============================================================== 5 cobros
titulo("5 · Cobros", 1)
parrafo("Estrellas de Telegram (dentro del bot)", negrita=True, espacio=2)
tabla([
    ("Qué hace falta", "nada · el bot emite la factura XTR"),
    ("Retiradas", "@BotFather → /mybots → geoidvpn_bot → Monetization"),
])

parrafo("Cripto (Crypto Pay)", negrita=True, espacio=2)
tabla([
    ("App ID", "6784775"),
    ("Token", TOKEN_CRIPTO),
    ("Comisión", "3 % (lo paga el cliente)"),
    ("Variables", "GEOID_CRYPTO_TOKEN · GEOID_CRYPTO_MONEDA"),
])

parrafo("QR / SBP ruso (activación manual)", negrita=True, espacio=2)
tabla([
    ("Teléfono", SBP_TEL),
    ("Titular", SBP_TITULAR),
    ("Variables", "GEOID_SBP_TELEFONO · GEOID_SBP_TITULAR"),
    ("Flujo", "el cliente pulsa «Ya he pagado» → te llega el aviso → /activar ID MESES"),
])

parrafo("Precios (un solo país: Suecia)", negrita=True, espacio=2)
tabla([
    ("1 mes", "150 ₽ · 115 ⭐ · 1,9 USDT"),
    ("3 meses", "399 ₽ · 300 ⭐ · 4,8 USDT"),
    ("6 meses (máximo)", "699 ₽ · 520 ⭐ · 8 USDT · 20 días extra"),
    ("Prueba gratis", "3 días, sin tarjeta"),
    ("Dispositivo extra", "40 ⭐ (≈50 ₽) · 30 días · máximo 5"),
])

# =============================================================== 6 firma
titulo("6 · Firma de la app Android (no se puede perder)", 1)
tabla([
    ("Keystore", "E:\\PC\\vpn\\app\\android-proyecto\\geoid-release.jks"),
    ("Alias", "geoid"),
    ("Contraseña", "G9WcYrUZopdROulib7AFN1mk"),
    ("Copia en base64", "anexo B de este documento"),
    ("Secrets en GitHub", "KEYSTORE_BASE64 · KEYSTORE_PASSWORD · KEY_ALIAS · KEY_PASSWORD"),
])
aviso("Sin este archivo no se pueden publicar actualizaciones que Android acepte.")

# =============================================================== 7 github
titulo("7 · GitHub y publicación", 1)
tabla([
    ("Cuenta", "KofyTrade · contraseña Jia2018*-+"),
    ("Repositorio", "https://github.com/KofyTrade/geoid (privado)"),
    ("Descargas", "https://github.com/KofyTrade/geoid/releases/latest"),
    ("Versión publicada", "4.1.3"),
])

parrafo("Publicar una versión nueva:", negrita=True, espacio=2)
codigo("""cd E:\\PC\\vpn
git add -A
git commit -m "Version X.Y.Z"
git push
git tag vX.Y.Z
git push origin vX.Y.Z

# la etiqueta debe coincidir con flutter_app/pubspec.yaml""")

# =============================================================== 8 web
titulo("8 · La web de la librería (Bukinist)", 1)
tabla([
    ("Dirección", "https://194.76.136.210.sslip.io"),
    ("Proyecto", "/opt/bukinist · usuario bukinist · node server.js"),
    ("Servicio", "bukinist · systemctl status bukinist"),
    ("Puerto interno", "127.0.0.1:3000"),
    ("Caddy", "/etc/caddy/Caddyfile · escucha 80 y 443"),
    ("Registro", "journalctl -u bukinist -f · journalctl -u caddy -f"),
    ("Certificado", "Let's Encrypt automático para el dominio sslip.io"),
])

aviso("El dominio sslip.io lleva la IP dentro: si algún día cambia la IP del "
      "servidor, hay que editar el Caddyfile y reiniciar caddy.")

# =============================================================== 9 respaldo
titulo("9 · Respaldo y qué hacer si Suecia se rompe", 1)
tabla([
    ("Qué se copia", "bot.sqlite comprimido + /etc/geoid-bot.env"),
    ("Dónde", "/root/respaldos/ (mismo servidor)"),
    ("Cuándo", "todos los días a las 03:30 (cron)"),
    ("Retención", "7 días"),
    ("Script", "/usr/local/bin/geoid-respaldo.sh"),
])

parrafo("Comandos útiles:", negrita=True, espacio=2)
codigo("""ls -lt /root/respaldos | head -5      # ver copias
/usr/local/bin/geoid-respaldo.sh     # hacer una ahora
systemctl status bukinist geoid-bot  # estado de los servicios""")

aviso("Ahora mismo las copias están SOLO en el mismo servidor. Si Suecia se "
      "pierde, se pierden. Pendiente: copia fuera (PC o almacenamiento externo).")

parrafo("Recuperar la base desde una copia:", negrita=True, espacio=2)
codigo("""systemctl stop geoid-bot
gunzip -c $(ls -t /root/respaldos/bot-*.sqlite.gz | head -1) > /var/lib/geoid-bot/bot.sqlite
systemctl start geoid-bot""")

# =============================================================== 10 dia a dia
titulo("10 · Comandos del día a día", 1)
codigo("""ssh root@194.76.136.210          # entrar al servidor
systemctl status geoid-bot       # estado del bot
systemctl restart geoid-bot      # reiniciarlo
journalctl -u geoid-bot -f       # ver lo que pasa en directo
systemctl status bukinist        # estado de la web
awg show awg0                    # clientes conectados a la VPN
cat /etc/geoid-bot.env           # configuracion del bot
cp /var/lib/geoid-bot/bot.sqlite /root/bot-$(date +%F).sqlite   # copia de la base""")

# =============================================================== 11 cuentas
titulo("11 · Contraseñas de las cuentas", 1)
tabla([
    ("Aeza (panel del VPS)", "9Sq0!pUILs7y"),
    ("GitHub (cuenta KofyTrade)", "Jia2018*-+"),
    ("Root del VPS de Suecia", "2UGTCkTiLPjJ"),
    ("Root del VPS de Finlandia", "XsH3OsmVSm03 (se retira el 13.12.2026)"),
])

# =============================================================== 12 tokens
titulo("12 · Tokens", 1)
tabla([
    ("Bot de Telegram", TOKEN_BOT if TOKEN_BOT else "grep GEOID_TOKEN /etc/geoid-bot.env"),
    ("ID del administrador", ADMIN_ID),
    ("Crypto Pay", TOKEN_CRIPTO),
    ("Agente del nodo", TOKEN_AGENTE),
])
aviso("Estos tokens dan control total del bot y del dinero. Si el PDF se filtra: "
      "@BotFather → /revoke y @CryptoBot → Revoke Token.")

# =============================================================== 13 fugas
titulo("13 · Si algo se filtra", 1)
tabla([
    ("Token del bot", "@BotFather → /revoke → pegarlo en /etc/geoid-bot.env y reiniciar"),
    ("Token de Crypto Pay", "@CryptoBot → GeoiD → Revoke Token"),
    ("Token del agente", "cambiarlo en /etc/geoid-agente.env y reiniciar geoid-agente"),
    ("Clave de firma Android", "no se puede cambiar: habría que publicar una app nueva"),
    ("Contraseña del VPS", "resetear desde el panel de Aeza"),
    ("Perfil .conf filtrado", "awg set awg0 peer <clave_pública> remove y quitar su bloque del .conf"),
])

# =============================================================== 14 kit
titulo("14 · Kit de reconstrucción (si se pierde el PC)", 1)
parrafo("1. El código", negrita=True, espacio=2)
tabla([
    ("App y bot", "github.com/KofyTrade/geoid (privado) · rama main"),
    ("Página de pago", "github.com/KofyTrade/geoid-pagos (público)"),
    ("Web de la librería", "/opt/bukinist en el servidor"),
])

parrafo("2. Volver a publicar la app", negrita=True, espacio=2)
tabla([
    ("Instalar", "Flutter 3.50 · Android SDK · Git"),
    ("Clonar", "git clone https://github.com/KofyTrade/geoid"),
    ("Restaurar firma", "pegar el keystore del anexo B en app/android-proyecto/geoid-release.jks"),
    ("Compilar", "git tag vX.Y.Z && git push origin vX.Y.Z (lo hace GitHub Actions)"),
])

parrafo("3. Reconstruir el servidor", negrita=True, espacio=2)
tabla([
    ("Nodo VPN", "servidor/instalar-nodo-suecia.sh (subred 10.9.10.0/24)"),
    ("DNS con bloqueo", "servidor/instalar-adblock.sh"),
    ("Agente", "servidor/instalar-agente.sh"),
    ("Bot", "los .py del repositorio a /opt/geoid-bot + el env del anexo A"),
])

parrafo("4. Pendrive de emergencia", negrita=True, espacio=2)
tabla([
    ("Este documento", "CREDENCIALES-GeoiD.pdf"),
    ("Firma de la app", "geoid-release.jks (también en el anexo B)"),
    ("Página de pago", "carpeta web-pagos (index.html + qr.png)"),
    ("Copia del código", "git bundle create geoid.bundle --all"),
])

# =============================================================== anexo A
titulo("Anexo A · Configuración completa del bot", 1)
parrafo("Contenido de /etc/geoid-bot.env. Sin esto el bot no arranca igual.")
if ENV.exists():
    codigo(ENV.read_text(encoding="utf-8", errors="ignore").strip())
    aviso("Este bloque contiene TODOS los secretos del bot.")
else:
    aviso("PENDIENTE: copia el env con  scp root@194.76.136.210:/etc/geoid-bot.env "
          "E:\\PC\\vpn\\env-suecia.txt  y vuelve a generar el PDF.")

# =============================================================== anexo B
titulo("Anexo B · Firma de la app en base64", 1)
parrafo("El archivo geoid-release.jks convertido a texto, para poder reponerlo.")
parrafo("Alias: geoid · Contraseña: G9WcYrUZopdROulib7AFN1mk", espacio=2)
JKS = pathlib.Path(r"E:\PC\vpn\app\android-proyecto\geoid-release.jks")
datos_jks = bloque_b64(JKS)
if datos_jks:
    codigo(datos_jks)
    parrafo("Para recuperarlo (en PowerShell):", negrita=True, espacio=2)
    codigo("""$b64 = Get-Content keystore.b64 -Raw
[IO.File]::WriteAllBytes("geoid-release.jks", [Convert]::FromBase64String($b64))
Get-FileHash geoid-release.jks -Algorithm SHA256
# debe dar: 8037FBBB1CAFACABA7C0E0A9682643F59B6077A58FD9C7EC0E2282A7359B8787""")
else:
    aviso("No se encontró el keystore en este PC.")

# =============================================================== anexo C
titulo("Anexo C · QR de cobro en base64", 1)
parrafo("El qr.png de la página de pago, para poder reponerlo si se pierde.")
QR = pathlib.Path(r"E:\PC\vpn\web-pagos\qr.png")
datos_qr = bloque_b64(QR)
if datos_qr:
    codigo(datos_qr)
else:
    aviso("No se encontró el QR en este PC.")

# =============================================================== pie
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(16)
r = p.add_run("Documento privado · GeoiD VPN · versión 5.0.0")
r.font.size = Pt(8.5)
r.font.color.rgb = GRIS

doc.save(SALIDA)
print("docx generado:", SALIDA, SALIDA.stat().st_size, "bytes")
