"""Genera el PDF de credenciales de GeoiD VPN.

No guarda secretos en el repositorio: el .docx y el .pdf se crean en la raiz
del proyecto, que esta en .gitignore para estos archivos.
"""

import pathlib

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

SALIDA = pathlib.Path(r"E:\PC\vpn\CREDENCIALES-GeoiD.docx")

TURQUESA = RGBColor(0x0E, 0x8C, 0x7F)
GRIS = RGBColor(0x44, 0x55, 0x55)
ROJO = RGBColor(0xB0, 0x30, 0x20)

doc = Document()

# ---------------------------------------------------------------- estilos base
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
        # linea fina debajo del subtitulo
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
    """Caja gris con comandos, en fuente monoespaciada."""
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
    """Impide que una fila se corte entre paginas."""
    for fila in tabla_obj.rows:
        trPr = fila._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        trPr.append(cant)

# ---------------------------------------------------------------- portada
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("GEoiD VPN")
r.bold = True
r.font.size = Pt(30)
r.font.color.rgb = TURQUESA

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Credenciales, accesos y comandos")
r.font.size = Pt(13)
r.font.color.rgb = GRIS

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Versión del proyecto 4.0.0 · 17 de noviembre de 2026")
r.font.size = Pt(9.5)
r.font.color.rgb = GRIS

aviso(
    "Este documento contiene contraseñas y claves en texto plano. "
    "No lo envíes por chat ni lo subas a la nube sin cifrar. "
    "Guárdalo en un pendrive o en un gestor de contraseñas."
)

parrafo(
    "Los campos marcados como [FALTA] no aparecen en la conversación: son datos "
    "que solo tienes tú (contraseñas de cuentas propias). Al lado pone dónde "
    "conseguirlos.",
    color=GRIS, tam=9.5,
)

# ---------------------------------------------------------------- 1. servidor
titulo("1 · Acceso al servidor (SSH y SCP)", 1)

parrafo("Abrir una sesión en el servidor. En PowerShell de tu PC:")
codigo(
    "ssh root@193.29.224.164\n"
    "\n"
    "Password: la de Aeza (al escribir NO se ve nada)\n"
    "\n"
    "Al entrar verás:  root@sophisticated-la:~#"
)

parrafo("Copiar archivos del PC al servidor. Siempre desde PowerShell, nunca dentro de la sesión SSH:")
codigo(
    "# subir todo el bot\n"
    "scp E:\\PC\\vpn\\bot\\*.py root@193.29.224.164:/opt/geoid-bot/\n"
    "\n"
    "# subir un archivo suelto\n"
    "scp E:\\PC\\vpn\\bot\\bot.py root@193.29.224.164:/opt/geoid-bot/\n"
    "\n"
    "# descargar una copia de la base de datos al PC\n"
    "scp root@193.29.224.164:/var/lib/geoid-bot/bot.sqlite E:\\PC\\vpn\\"
)

parrafo("Qué prompt estás usando:", negrita=True)
tabla([
    ("PS C:\\Users\\KOFY>", "tu PC · aquí van ssh, scp y git"),
    ("root@sophisticated-la:~#", "el servidor · aquí van systemctl, awg, nano"),
    ("exit", "para salir del servidor"),
])

parrafo("Si la conexión falla:", negrita=True)
tabla([
    ("Connection timed out", "desconecta la VPN o cambia de red y reintenta"),
    ("Permission denied", "contraseña incorrecta · cópiala del panel de Aeza"),
    ("Host key verification failed", "ssh-keygen -R 193.29.224.164 y reintenta"),
    ("ssh no se reconoce", "no estás en PowerShell"),
])

# ---------------------------------------------------------------- 2. datos
titulo("2 · Servidor", 1)
tabla([
    ("Proveedor", "Aeza · https://my.aeza.net"),
    ("IP", "193.29.224.164"),
    ("Usuario SSH", "root"),
    ("Contraseña SSH", "[FALTA] → en el panel de Aeza (se muestra una vez; se puede resetear)"),
    ("Puerto SSH", "22"),
    ("Sistema", "Ubuntu 26.04 LTS · 1 vCPU · ~2 GB RAM · 29 GB"),
])

titulo("3 · Túnel VPN (WireGuard ofuscado)", 1)
tabla([
    ("Interfaz", "awg0"),
    ("Puerto UDP", "21766"),
    ("DNS interno", "10.9.9.1 (dnsmasq con bloqueo de anuncios)"),
    ("MTU", "1280"),
    ("Aceleración", "BBR activado"),
    ("Config del servidor", "/etc/amnezia/amneziawg/awg0.conf"),
    ("Perfiles propios", "E:\\PC\\vpn\\awg\\ · móvil 10.9.9.2 · portátil 10.9.9.3"),
    ("Ver el túnel", "awg show awg0"),
])

# ---------------------------------------------------------------- 4. bot
titulo("4 · Bot de Telegram", 1)
tabla([
    ("Bot", "@geoidvpn_bot (GEOID-VPN Bot)"),
    ("ID del bot", "9195295915"),
    ("Token", "[NO INCLUIDO] → en el servidor: grep GEOID_TOKEN /etc/geoid-bot.env"),
    ("Tu ID de Telegram", "6887964554 (administrador del bot)"),
    ("Código", "/opt/geoid-bot"),
    ("Configuración", "/etc/geoid-bot.env"),
    ("Base de datos", "/var/lib/geoid-bot/bot.sqlite"),
    ("Servicio", "systemctl status geoid-bot"),
    ("Registro", "journalctl -u geoid-bot -f"),
])

parrafo("Comandos de administrador (solo desde tu privado):", negrita=True)
tabla([
    ("/estado", "clientes activos, precios y avisos del servidor"),
    ("/enlaces", "versión publicada y enlaces de descarga"),
    ("/promo CODIGO DIAS USOS [dd.mm.aaaa]", "crea un código promocional"),
    ("/promos", "lista los códigos y sus usos restantes"),
    ("/promo borrar CODIGO", "elimina un código"),
    ("/activar ID MESES", "activa un pago recibido por QR o transferencia"),
    ("/regalar ID DIAS", "regala días a un cliente"),
    ("/ticket", "genera un ticket de prueba del soporte"),
    ("/qr", "guarda el QR de pago (envía la foto con /qr)"),
    ("/chatid", "dice el ID del grupo donde se escribe"),
])

# ---------------------------------------------------------------- 5. cobros
titulo("5 · Cobros", 1)

parrafo("Estrellas de Telegram", negrita=True)
tabla([
    ("Qué hace falta", "nada · el bot emite la factura (XTR)"),
    ("Retiradas", "@BotFather → /mybots → geoidvpn_bot → Monetization"),
])

parrafo("Cripto (Crypto Pay de @CryptoBot)", negrita=True)
tabla([
    ("App", "GeoiD"),
    ("App ID", "6784775"),
    ("Token de API", "6784775:AAj67eg3YQhmou2GexKrzwEwyPFta7F05wt"),
    ("Comisión", "3 % (lo descuenta al cliente; tú recibes el 97 %)"),
    ("Retiradas", "@CryptoBot → Crypto Pay → GeoiD → Transfer Coins to Wallet"),
    ("Variables", "GEOID_CRYPTO_TOKEN · GEOID_CRYPTO_MONEDA en /etc/geoid-bot.env"),
])
aviso("Ese token apareció en un chat. Revócalo en @CryptoBot → GeoiD → Revoke Token y guarda el nuevo solo en el servidor.")

parrafo("QR / SBP ruso (se activa a mano)", negrita=True)
tabla([
    ("Teléfono de cobro", "+7 9313936329"),
    ("Titular", "ERNESTO LOPEZ"),
    ("Variables", "GEOID_SBP_TELEFONO · GEOID_SBP_TITULAR · GEOID_RUB_*"),
    ("Activación", "el cliente pulsa «Ya he pagado» → te llega el aviso → /activar ID MESES"),
])

parrafo("Promoción por tramos: el proxy de Telegram es de regalo desde 3 meses.", negrita=True)
tabla([
    ("1 mes", "150 ₽ · 115 ⭐ · 1,9 USDT"),
    ("3 meses", "399 ₽ · 300 ⭐ · 4,8 USDT · 1 proxy de regalo"),
    ("6 meses (máximo)", "699 ₽ · 520 ⭐ · 8 USDT · 2 proxies + 20 días extra"),
    ("Prueba gratis", "3 días, sin tarjeta"),
])

# ---------------------------------------------------------------- 6. proxy
titulo("6 · Proxy de Telegram propio", 1)
tabla([
    ("Para qué", "usar Telegram sin encender la VPN"),
    ("Servicio", "mtg · systemctl status mtg"),
    ("Puerto", "443/tcp"),
    ("Configuración", "/etc/mtg.toml · clave en /etc/mtg.secret"),
    ("Disfraz", "geoidvpn.duckdns.org (crear en duckdns.org → 193.29.224.164)"),
    ("Instalador", "/root/instalar-proxy-telegram.sh"),
])
parrafo("Clave del proxy:", negrita=True)
codigo("ee2aafaaad9922e542f900a1fb25c68cfc67656f696476706e2e6475636b646e732e6f7267")
parrafo("Enlace para el móvil (tocar con Telegram instalado):", negrita=True)
codigo("tg://proxy?server=193.29.224.164&port=443&secret=ee2aafaaad9922e542f900a1fb25c68cfc67656f696476706e2e6475636b646e732e6f7267")
parrafo(
    "En Telegram: Ajustes → Datos y almacenamiento → Proxy → Usar proxy → "
    "Añadir proxy → MTPROTO.",
    color=GRIS, tam=9.5,
)

# ---------------------------------------------------------------- 7. firma
titulo("7 · Firma de la app Android (no se puede perder)", 1)
tabla([
    ("Keystore", "E:\\PC\\vpn\\app\\android-proyecto\\geoid-release.jks"),
    ("Alias", "geoid"),
    ("Contraseña", "G9WcYrUZopdROulib7AFN1mk"),
    ("Archivo de apoyo", "E:\\PC\\vpn\\firma-geoid.txt"),
    ("Secrets en GitHub", "KEYSTORE_BASE64 · KEYSTORE_PASSWORD · KEY_ALIAS · KEY_PASSWORD"),
])
aviso("Sin este archivo no se pueden publicar actualizaciones que Android acepte. Cópialo a un pendrive.")

# ---------------------------------------------------------------- 8. github
titulo("8 · GitHub y publicación", 1)
tabla([
    ("Cuenta", "KofyTrade"),
    ("Correo en commits", "133810404+KofyTrade@users.noreply.github.com"),
    ("Repositorio", "https://github.com/KofyTrade/geoid (privado)"),
    ("Contraseña", "[FALTA] (la tuya, no está en el proyecto)"),
    ("Descargas", "https://github.com/KofyTrade/geoid/releases/latest"),
])

parrafo("Publicar una versión nueva:", negrita=True)
codigo(
    "cd E:\\PC\\vpn\n"
    "git add -A\n"
    "git commit -m \"Version X.Y.Z\"\n"
    "git push\n"
    "git tag vX.Y.Z\n"
    "git push origin vX.Y.Z\n"
    "\n"
    "# la etiqueta debe coincidir con flutter_app/pubspec.yaml"
)

parrafo("Enlaces de descarga fijos (no caducan nunca):", negrita=True)
codigo(
    "https://github.com/KofyTrade/geoid/releases/latest/download/GeoiD-vpn-Android-arm64-v8a.apk\n"
    "https://github.com/KofyTrade/geoid/releases/latest/download/GeoiD-vpn-Android-armeabi-v7a.apk\n"
    "https://github.com/KofyTrade/geoid/releases/latest/download/GeoiD-vpn-Android-x86_64.apk\n"
    "https://github.com/KofyTrade/geoid/releases/latest/download/GeoiD-vpn-Windows.zip"
)

# ---------------------------------------------------------------- 9. rutina
titulo("9 · Comandos del día a día", 1)
codigo(
    "ssh root@193.29.224.164          # entrar al servidor\n"
    "systemctl status geoid-bot       # estado del bot\n"
    "systemctl restart geoid-bot      # reiniciarlo\n"
    "journalctl -u geoid-bot -f       # ver lo que pasa en directo\n"
    "systemctl status mtg             # estado del proxy\n"
    "systemctl status mtg-user@<ID>   # proxy personal de un cliente\n"
    "awg show awg0                    # clientes conectados a la VPN\n"
    "cat /etc/geoid-bot.env           # configuración del bot\n"
    "cp /var/lib/geoid-bot/bot.sqlite /root/bot-$(date +%F).sqlite   # copia de la base"
)

# ---------------------------------------------------------------- 10. pendientes
titulo("10 · Datos que faltan en este documento", 1)
parrafo("Son datos solo tuyos; apúntalos a mano cuando los tengas:", color=GRIS, tam=9.5)
tabla([
    ("Contraseña del VPS", "panel de Aeza (se puede resetear)"),
    ("Correo y contraseña de Aeza", "con los que creaste la cuenta"),
    ("Token del bot de Telegram", "grep GEOID_TOKEN /etc/geoid-bot.env"),
    ("Contraseña de GitHub", "la tuya"),
    ("Correo del proyecto", "el que usaste para Aeza y el bot"),
])

# ---------------------------------------------------------------- 11. fugas
titulo("11 · Si algo se filtra", 1)
tabla([
    ("Token del bot", "@BotFather → /revoke → pegarlo en /etc/geoid-bot.env y reiniciar"),
    ("Token de Crypto Pay", "@CryptoBot → GeoiD → Revoke Token (igual)"),
    ("Clave de firma Android", "no se puede cambiar: habría que publicar una app nueva"),
    ("Contraseña del VPS", "resetear desde el panel de Aeza"),
    ("Perfil .conf filtrado", "awg set awg0 peer <clave_pública> remove y quitar su bloque del .conf"),
    ("Clave del proxy", "rm -f /etc/mtg.secret && bash /root/instalar-proxy-telegram.sh 443"),
])

# ---------------------------------------------------------------- pie
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(16)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Documento privado · GeoiD VPN · versión 4.0.0")
r.font.size = Pt(8.5)
r.font.color.rgb = GRIS

doc.save(SALIDA)
print("docx generado:", SALIDA, SALIDA.stat().st_size, "bytes")
