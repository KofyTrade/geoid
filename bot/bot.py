"""Bot de Telegram de GeoiD VPN.

Menú fijo en la parte inferior (teclado persistente): al pulsar una opción el
teclado sigue ahí, así siempre se puede volver.

Arranque:  python3 bot.py
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    BotCommand,
    BotCommandScopeChat,
    BufferedInputFile,
    CallbackQuery,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
    ReplyKeyboardMarkup,
)

import config
import db

try:  # opcional
    import descargas
except Exception:  # noqa: BLE001
    descargas = None  # type: ignore[assignment]
import pagos
try:  # opcional: si falta el archivo, el bot sigue funcionando
    import proxy as proxy_personal
except Exception:  # noqa: BLE001
    proxy_personal = None  # type: ignore[assignment]

try:  # opcional: avisos por correo
    import avisos
except Exception:  # noqa: BLE001
    avisos = None  # type: ignore[assignment]

import nodos
import provision
from textos import IDIOMAS, t

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
log = logging.getLogger("geoid")

router = Router()

# Clientes que han pulsado "Canjear codigo" y su siguiente mensaje es el codigo.
ESPERANDO_PROMO: dict[int, float] = {}
MINUTOS_PROMO = 10
DIA = 86400
ADMIN = 0


def _admin() -> int:
    """El id de administrador es opcional: si falta o no es un número, se ignora."""
    try:
        return int(os.environ.get("GEOID_ADMIN", "0") or 0)
    except ValueError:
        return 0


ADMIN = _admin()


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def _regalo_dias(meses: int) -> int:
    """Días extra del plan; 0 si el config.py es antiguo."""
    funcion = getattr(config, "dias_de_regalo", None)
    return funcion(meses) if callable(funcion) else 0


def _regalo_proxies(meses: int) -> int:
    """Proxies de regalo; cálculo de reserva si el config.py es antiguo."""
    funcion = getattr(config, "proxies_de_regalo", None)
    if callable(funcion):
        return funcion(meses)
    minimo = getattr(config, "MIN_MESES_PROXY", 3)
    if meses < minimo:
        return 0
    return 2 if meses >= 6 else 1


def _web_pagos() -> str:
    """URL de la página de pago (vacía si no está configurada)."""
    return (getattr(config, "WEB_PAGOS", "") or "").strip()


def idioma(tg_id: int) -> str:
    usuario = db.obtener(tg_id)
    return (usuario or {}).get("idioma") or getattr(config, "IDIOMA_DEFECTO", "ru")


def fecha(instante: int) -> str:
    return datetime.fromtimestamp(instante, tz=timezone.utc).strftime("%d.%m.%Y %H:%M UTC")


def dias_restantes(instante: int) -> int:
    return max(0, (instante - int(time.time()) + DIA - 1) // DIA)


def teclado_fijo(tg_id: int) -> ReplyKeyboardMarkup:
    """Menú de abajo: se queda siempre visible."""
    idi = idioma(tg_id)

    botones = [
        t(idi, "menu_prueba"),
        t(idi, "menu_comprar"),
        t(idi, "menu_mi_vpn"),
    ]
    # El país solo tiene sentido con varios servidores.
    if len(config.PAISES) > 1:
        botones.append(t(idi, "menu_pais"))
    botones += [
        t(idi, "menu_invitar"),
        t(idi, "menu_promo"),
        t(idi, "menu_ayuda"),
        t(idi, "menu_idioma"),
    ]

    filas = [botones[i:i + 2] for i in range(0, len(botones), 2)]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=x) for x in fila] for fila in filas],
        resize_keyboard=True,
        is_persistent=True,
    )


def teclado_planes(tg_id: int) -> InlineKeyboardMarkup:
    """Botones con los meses y el precio en estrellas."""
    idi = idioma(tg_id)
    filas = []
    for meses in config.PRECIOS:
        duracion = _duracion(meses, idi)
        estrellas = config.PRECIOS[meses]
        regalo = " 🎁" if meses >= getattr(config, "MIN_MESES_PROXY", 3) else ""
        filas.append([InlineKeyboardButton(
            text=f"{duracion} · {estrellas} ⭐{regalo}",
            callback_data=f"plan:{meses}",
        )])
    return InlineKeyboardMarkup(inline_keyboard=filas)


def teclado_volver(tg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="◀️", callback_data="menu")
    ]])


def proxies_ok() -> bool:
    """True solo si el modulo de proxies existe y el servidor esta listo."""
    return proxy_personal is not None and proxy_personal.disponible()


def _dias(cantidad: int, idi: str) -> str:
    """Como se dicen los dias en cada idioma."""
    if idi == "ru":
        return f"{cantidad} дн."
    if idi == "en":
        return f"{cantidad} day" + ("" if cantidad == 1 else "s")
    return f"{cantidad} día" + ("" if cantidad == 1 else "s")


def _duracion(meses: int, idi: str) -> str:
    """Como se dice la duracion en cada idioma."""
    if idi == "ru":
        return f"{meses} мес."
    if idi == "en":
        return f"{meses} month" + ("" if meses == 1 else "s")
    return f"{meses} mes" + ("" if meses == 1 else "es")


def _descripcion_plan(meses: int, idi: str) -> str:
    clave = {
        1: "plan_mes",
        3: "plan_3meses",
        6: "plan_6meses",
        12: "plan_anio",
    }.get(meses, "plan_mes")
    return t(idi, clave)


def hay_qr() -> bool:
    """El pago por QR solo existe si hay un QR guardado."""
    return bool(db.leer_ajuste("qr_sbp") or config.SBP_QR_URL)


def _destino(evento: Message | CallbackQuery) -> int:
    return evento.message.chat.id if isinstance(evento, CallbackQuery) else evento.chat.id


# --------------------------------------------------------------------------- #
# Accesos
# --------------------------------------------------------------------------- #
def activar(tg_id: int, dias: int) -> dict:
    """Da de alta los perfiles que falten y extiende la caducidad."""
    usuario = db.obtener(tg_id) or {}
    ahora = int(time.time())

    if not usuario.get("ip"):
        db.guardar(tg_id, ip="pendiente",
                   dispositivos=max(1, int(usuario.get("dispositivos") or 1)))

    crear_perfiles_faltantes(tg_id)

    lista = db.perfiles(tg_id)
    principal = next((f for f in lista if int(f["dispositivo"]) == 1 and f["nodo"] == "fi"),
                     lista[0] if lista else None)

    if principal:
        db.guardar(
            tg_id,
            ip=principal["ip"],
            privada=principal["privada"],
            publica=principal["publica"],
            preshared=principal["preshared"],
            servidor=principal["nodo"],
            expira=max(ahora, int(usuario.get("expira") or 0)) + dias * DIA,
            pais_compra=None,
        )
    elif usuario.get("ip"):
        db.guardar(
            tg_id,
            expira=max(ahora, int(usuario.get("expira") or 0)) + dias * DIA,
            pais_compra=None,
        )
    return db.obtener(tg_id)
async def enviar_conf(bot: Bot, tg_id: int, usuario: dict, texto: str,
                     dispositivo: int | None = None):
    """Manda un .conf por pais (y por dispositivo si tiene varios)."""
    plan = "pago" if db.ha_pagado(tg_id) else "prueba"
    expira = int(usuario.get("expira") or 0)
    lista = db.perfiles(tg_id)

    if not lista and usuario.get("ip"):
        lista = [{
            "nodo": usuario.get("servidor") or "fi",
            "dispositivo": 1,
            "ip": usuario["ip"],
            "privada": usuario.get("privada"),
            "preshared": usuario.get("preshared"),
        }]

    if dispositivo is not None:
        lista = [f for f in lista if int(f.get("dispositivo") or 1) == dispositivo]

    total = int(usuario.get("dispositivos") or 1)
    enviados = 0
    for fila in lista:
        nodo = nodos.por_id(fila["nodo"])
        endpoint = nodos.endpoint_de(nodo)
        if not endpoint:
            log.error("el nodo %s no tiene endpoint; no se envia su configuracion", nodo["nombre"])
            continue

        contenido = provision.generar_conf(
            fila["privada"], fila["preshared"], fila["ip"],
            plan=plan, expira=expira,
            endpoint=endpoint, dns=nodo["dns"], mtu=nodo["mtu"],
        )

        numero = int(fila.get("dispositivo") or 1)
        sufijo = "" if total <= 1 else f"-{numero}"
        archivo = BufferedInputFile(
            contenido.encode("utf-8"),
            filename=f"GeoiD-{nodo['nombre']}{sufijo}.conf",
        )
        leyenda = f"{nodo['bandera']} <b>{nodo['nombre']}</b>"
        if total > 1:
            leyenda += f" · dispositivo {numero}"
        pie = f"{texto}\n\n{leyenda}" if enviados == 0 else leyenda
        await bot.send_document(
            chat_id=tg_id,
            document=archivo,
            caption=pie,
            parse_mode=ParseMode.HTML,
        )
        enviados += 1

    return enviados
async def accion_prueba(bot: Bot, tg_id: int) -> None:
    usuario = db.obtener(tg_id) or {}
    idi = usuario.get("idioma") or "es"
    ahora = int(time.time())

    teclado = teclado_fijo(tg_id)

    if usuario.get("expira", 0) > ahora:
        await bot.send_message(
            tg_id, t(idi, "prueba_cabecera", fecha=fecha(usuario["expira"])),
            reply_markup=teclado,
        )
        return

    if usuario.get("prueba_usada"):
        await bot.send_message(tg_id, t(idi, "prueba_ya_usada"), reply_markup=teclado)
        return

    try:
        actualizado = activar(tg_id, config.DIAS_PRUEBA)
        db.guardar(tg_id, prueba_usada=1)
    except Exception:  # noqa: BLE001
        log.exception("fallo creando la prueba")
        await bot.send_message(tg_id, t(idi, "error_generico"))
        return

    await bot.send_message(
        tg_id,
        t(idi, "prueba_lista",
          dias=config.DIAS_PRUEBA,
          pais=t(idi, "pais"),
          ip=actualizado["ip"],
          fecha=fecha(actualizado["expira"])),
        parse_mode=ParseMode.HTML,
        reply_markup=teclado,
    )
    await enviar_conf(bot, tg_id, actualizado, t(idi, "pais"))


def _teclado_paises(prefijo: str) -> InlineKeyboardMarkup:
    """Botones con los paises disponibles."""
    filas = []
    for nodo in nodos.lista():
        filas.append([InlineKeyboardButton(
            text=f"{nodo['bandera']} {nodo['nombre']}",
            callback_data=f"{prefijo}:{nodo['id']}",
        )])
    return InlineKeyboardMarkup(inline_keyboard=filas)


async def accion_comprar(bot: Bot, tg_id: int) -> None:
    idi = idioma(tg_id)
    await bot.send_message(
        tg_id, t(idi, "comprar_titulo"),
        reply_markup=teclado_planes(tg_id),
        parse_mode=ParseMode.HTML,
    )


def crear_perfiles_faltantes(tg_id: int, dispositivo: int | None = None) -> int:
    """Crea los perfiles que falten (de un dispositivo concreto o de todos)."""
    usuario = db.obtener(tg_id) or {}
    if not usuario.get("ip"):
        return 0

    existentes = {(f["nodo"], int(f["dispositivo"])) for f in db.perfiles(tg_id)}
    total = int(usuario.get("dispositivos") or 1)
    numeros = [dispositivo] if dispositivo else list(range(1, total + 1))
    creados = 0

    for numero in numeros:
        for nodo in nodos.lista():
            if (nodo["id"], numero) in existentes:
                continue
            try:
                cliente = nodos.crear(nodo, usuario.get("usuario") or str(tg_id))
            except Exception:  # noqa: BLE001
                log.exception("no se pudo crear %s (dispositivo %s) para %s",
                              nodo["nombre"], numero, tg_id)
                continue
            db.guardar_perfil(
                tg_id, nodo["id"], cliente["ip"],
                cliente["privada"], cliente["publica"], cliente["preshared"],
                dispositivo=numero,
            )
            creados += 1
    return creados
async def accion_mi_vpn(bot: Bot, tg_id: int) -> None:
    usuario = db.obtener(tg_id) or {}
    idi = usuario.get("idioma") or "es"
    ahora = int(time.time())

    if not usuario.get("ip") or usuario.get("expira", 0) <= ahora:
        texto = t(idi, "mi_vpn_sin") if not usuario.get("ip") else t(idi, "caducado")
        await bot.send_message(tg_id, texto, reply_markup=teclado_fijo(tg_id))
        return

    crear_perfiles_faltantes(tg_id)

    filas = []
    if int(usuario.get("dispositivos") or 1) < config.MAX_DISPOSITIVOS:
        filas.append([InlineKeyboardButton(
            text=t(idi, "mas_dispositivo",
                   estrellas=config.PRECIO_DISPOSITIVO_ESTRELLAS),
            callback_data="dispositivo")])
    if usuario.get("proxy"):
        filas.append([InlineKeyboardButton(
            text=t(idi, "proxy_boton"), callback_data="proxy")])
    teclado = InlineKeyboardMarkup(inline_keyboard=filas) if filas else None

    lista = db.perfiles(tg_id)
    lineas_pais = "\n".join(
        f"{nodos.por_id(f['nodo'])['bandera']} {nodos.por_id(f['nodo'])['nombre']}"
        + (f" · {f['dispositivo']}" if int(f["dispositivo"]) > 1 else "")
        + f": <code>{f['ip']}</code>"
        for f in lista
    )

    await bot.send_message(
        tg_id,
        t(idi, "mi_vpn_activo",
          pais="", ip="",
          fecha=fecha(usuario["expira"]),
          dias=dias_restantes(usuario["expira"]),
          enlace=lineas_pais),
        reply_markup=teclado,
        parse_mode=ParseMode.HTML,
    )

    await enviar_conf(bot, tg_id, usuario, t(idi, "reenvio_texto"))
async def accion_pais(bot: Bot, tg_id: int) -> None:
    idi = idioma(tg_id)
    texto = t(idi, "pais_unico")
    if len(config.PAISES) > 1:
        texto = " · ".join(config.PAISES)
    await bot.send_message(tg_id, texto, reply_markup=teclado_fijo(tg_id))


async def accion_invitar(bot: Bot, tg_id: int) -> None:
    usuario = db.obtener(tg_id) or {}
    idi = usuario.get("idioma") or "es"
    me = await bot.get_me()
    enlace = f"https://t.me/{me.username}?start={usuario.get('codigo_ref') or 'r'}"
    cuantos = db.referidos_pagados(tg_id)

    texto = t(idi, "invitar_texto", enlace=enlace, cuantos=cuantos)

    # progreso hacia el siguiente premio
    siguiente = None
    for amigos, premio in config.NIVELES_INVITACION:
        if cuantos < amigos:
            siguiente = (amigos, premio)
            break

    if siguiente:
        faltan = siguiente[0] - cuantos
        texto += "\n\n" + t(
            idi, "invitar_siguiente",
            faltan=faltan,
            premio=_dias(siguiente[1], idi),
        )
    else:
        texto += "\n\n" + t(idi, "invitar_maximo")

    await bot.send_message(
        tg_id,
        texto,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=teclado_fijo(tg_id),
    )


async def accion_promo(bot: Bot, tg_id: int) -> None:
    ESPERANDO_PROMO[tg_id] = time.time()
    await bot.send_message(
        tg_id, t(idioma(tg_id), "promo_pedir"), reply_markup=teclado_fijo(tg_id)
    )


async def accion_ayuda(bot: Bot, tg_id: int) -> None:
    idi = idioma(tg_id)
    android, windows = config.URL_ANDROID, config.URL_WINDOWS
    if descargas is not None:
        android, windows = descargas.enlaces(android, windows)
    await bot.send_message(
        tg_id,
        t(idi, "ayuda", android=android, windows=windows)
        + "\n\n"
        + t(idi, "soporte_invita"),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


async def accion_idioma(bot: Bot, tg_id: int) -> None:
    filas = [
        [InlineKeyboardButton(text=n, callback_data=f"idi:{c}")]
        for c, n in IDIOMAS.items()
    ]
    await bot.send_message(
        tg_id,
        t(idioma(tg_id), "idioma_pedir"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=filas),
    )


# Etiquetas del teclado fijo en los tres idiomas -> acción
ACCIONES: dict[str, str] = {}
for _idi in ("es", "ru", "en"):
    ACCIONES[t(_idi, "menu_prueba")] = "prueba"
    ACCIONES[t(_idi, "menu_comprar")] = "comprar"
    ACCIONES[t(_idi, "menu_mi_vpn")] = "mi_vpn"
    ACCIONES[t(_idi, "menu_pais")] = "pais"
    ACCIONES[t(_idi, "menu_invitar")] = "invitar"
    ACCIONES[t(_idi, "menu_promo")] = "promo"
    ACCIONES[t(_idi, "menu_ayuda")] = "ayuda"
    ACCIONES[t(_idi, "menu_idioma")] = "idioma"

REPARTIDOR = {
    "prueba": accion_prueba,
    "comprar": accion_comprar,
    "mi_vpn": accion_mi_vpn,
    "pais": accion_pais,
    "invitar": accion_invitar,
    "promo": accion_promo,
    "ayuda": accion_ayuda,
    "idioma": accion_idioma,
}


# --------------------------------------------------------------------------- #
# Comandos
# --------------------------------------------------------------------------- #
async def recompensar_padrino(bot: Bot, comprador: int) -> None:
    """Si el amigo ha comprado, mira los niveles del padrino y premia."""
    usuario = db.obtener(comprador) or {}
    padrino = usuario.get("referido")
    if not padrino:
        return

    datos = db.obtener(padrino) or {}
    nivel_previo = int(datos.get("nivel_ref") or 0)
    cuantos = db.referidos_pagados(padrino)

    nivel_nuevo = 0
    for numero, (amigos, _dias) in enumerate(config.NIVELES_INVITACION, start=1):
        if cuantos >= amigos:
            nivel_nuevo = numero

    if nivel_nuevo <= nivel_previo:
        return

    dias = sum(
        premio
        for numero, (_amigos, premio) in enumerate(config.NIVELES_INVITACION, start=1)
        if nivel_previo < numero <= nivel_nuevo
    )
    if dias <= 0:
        return

    db.crear_si_falta(padrino, None)
    actualizado = activar(padrino, dias)
    db.guardar(padrino, nivel_ref=nivel_nuevo)

    try:
        await bot.send_message(
            padrino,
            t(idioma(padrino), "premio_invitacion",
              cuantos=cuantos, dias=dias, fecha=fecha(actualizado["expira"])),
            parse_mode=ParseMode.HTML,
            reply_markup=teclado_fijo(padrino),
        )
    except Exception:  # noqa: BLE001
        log.warning("no se pudo avisar del premio a %s", padrino)

    log.info("premio nivel %s (%s dias) para %s", nivel_nuevo, dias, padrino)


def activar_plan(tg_id: int, meses: int) -> dict:
    """Activa un plan: los meses comprados más los días de regalo."""
    dias = 30 * meses + _regalo_dias(meses)
    return activar(tg_id, dias)


async def entregar_proxy(bot: Bot, tg_id: int, meses: int) -> None:
    """Crea y entrega los proxies de regalo que toquen (1 o 2)."""
    cantidad = _regalo_proxies(meses)
    if cantidad <= 0:
        return

    # Los clientes NUNCA usan el proxy del dueño (puerto 443).
    if not proxies_ok():
        log.warning(
            "proxy personal no disponible: falta ejecutar proxy-multiusuario.sh"
        )
        return

    usuario = db.obtener(tg_id) or {}
    idi = usuario.get("idioma") or getattr(config, "IDIOMA_DEFECTO", "ru")

    for numero in (1, 2):
        if numero > cantidad:
            break

        if numero == 1:
            puerto, secreto = usuario.get("proxy_puerto"), usuario.get("proxy_secreto")
        else:
            puerto, secreto = usuario.get("proxy2_puerto"), usuario.get("proxy2_secreto")

        if not (puerto and secreto):
            datos = proxy_personal.crear(tg_id, numero=numero)
            puerto, secreto = datos["puerto"], datos["secreto"]
            if numero == 1:
                db.guardar(tg_id, proxy=1, proxy_puerto=puerto, proxy_secreto=secreto)
            else:
                db.guardar(tg_id, proxy2_puerto=puerto, proxy2_secreto=secreto)
        elif not proxy_personal.activo(tg_id, numero):
            datos = proxy_personal.crear(tg_id, secreto, numero=numero)
            puerto = datos["puerto"]

        enlace = (
            f"tg://proxy?server={config.PROXY_SERVIDOR}"
            f"&port={puerto}&secret={secreto}"
        )
        texto = t(idi, "proxy_regalo",
                  enlace=enlace,
                  servidor=config.PROXY_SERVIDOR,
                  puerto=puerto,
                  secreto=secreto)
        if cantidad > 1:
            texto = t(idi, "proxy_cual", numero=numero, total=cantidad) + "\n\n" + texto

        try:
            await bot.send_message(
                tg_id, texto,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except Exception:  # noqa: BLE001
            log.warning("no se pudo entregar el proxy %s a %s", numero, tg_id)


async def recompensar_padrino(bot: Bot, comprador: int) -> None:
    """Si el amigo ha comprado, mira los niveles del padrino y premia."""
    usuario = db.obtener(comprador) or {}
    padrino = usuario.get("referido")
    if not padrino:
        return

    datos = db.obtener(padrino) or {}
    nivel_previo = int(datos.get("nivel_ref") or 0)
    cuantos = db.referidos_pagados(padrino)

    nivel_nuevo = 0
    for numero, (amigos, _dias) in enumerate(config.NIVELES_INVITACION, start=1):
        if cuantos >= amigos:
            nivel_nuevo = numero

    if nivel_nuevo <= nivel_previo:
        return

    dias = sum(
        premio
        for numero, (_amigos, premio) in enumerate(config.NIVELES_INVITACION, start=1)
        if nivel_previo < numero <= nivel_nuevo
    )
    if dias <= 0:
        return

    db.crear_si_falta(padrino, None)
    actualizado = activar(padrino, dias)
    db.guardar(padrino, nivel_ref=nivel_nuevo)

    try:
        await bot.send_message(
            padrino,
            t(idioma(padrino), "premio_invitacion",
              cuantos=cuantos, dias=dias, fecha=fecha(actualizado["expira"])),
            parse_mode=ParseMode.HTML,
            reply_markup=teclado_fijo(padrino),
        )
    except Exception:  # noqa: BLE001
        log.warning("no se pudo avisar del premio a %s", padrino)

    log.info("premio nivel %s (%s dias) para %s", nivel_nuevo, dias, padrino)


@router.message(CommandStart())
async def start(mensaje: Message, bot: Bot, command: CommandObject):
    argumento = (command.args or "").strip().lower()

    referido = None
    if argumento.startswith("r"):
        padrino = db.por_codigo(command.args)
        if padrino and padrino["tg_id"] != mensaje.from_user.id:
            referido = padrino["tg_id"]

    usuario = db.crear_si_falta(mensaje.from_user.id, mensaje.from_user.username, referido)
    idi = usuario["idioma"] or "es"

    await mensaje.answer(
        t(idi, "bienvenida", marca=config.MARCA, dias=config.DIAS_PRUEBA),
        reply_markup=teclado_fijo(mensaje.from_user.id),
        parse_mode=ParseMode.HTML,
    )

    if referido:
        await mensaje.answer(t(idi, "invitar_bienvenida"))

    # Enlaces que llegan desde la página de pago: /start pagado_1 | pagado_3 | pagado_6
    if argumento.startswith("pagado_"):
        trozo = argumento.split("_", 1)[1]
        meses_pagados = int(trozo) if trozo.isdigit() else 1
        if meses_pagados not in config.PRECIOS_RUB:
            meses_pagados = 1
        await avisar_pago(bot, mensaje.from_user.id, meses_pagados)
        await mensaje.answer(
            t(idi, "manual_aviso"),
            reply_markup=teclado_volver(mensaje.from_user.id),
            parse_mode=ParseMode.HTML,
        )
        return

    # Enlaces que llegan desde la app: /start trial | buy | my
    if argumento == "trial":
        await accion_prueba(bot, mensaje.from_user.id)
    elif argumento == "buy":
        await accion_comprar(bot, mensaje.from_user.id)
    elif argumento == "my":
        await accion_mi_vpn(bot, mensaje.from_user.id)


@router.message(Command("menu"))
async def comando_menu(mensaje: Message, bot: Bot):
    idi = idioma(mensaje.from_user.id)
    await mensaje.answer(
        t(idi, "bienvenida", marca=config.MARCA, dias=config.DIAS_PRUEBA),
        reply_markup=teclado_fijo(mensaje.from_user.id),
        parse_mode=ParseMode.HTML,
    )


# --------------------------------------------------------------------------- #
# Teclado fijo (texto)
# --------------------------------------------------------------------------- #
@router.message(F.reply_to_message, F.from_user.id == ADMIN)
async def responder_soporte(mensaje: Message, bot: Bot):
    """El dueno responde a un ticket y el mensaje llega al cliente."""
    if ADMIN and mensaje.from_user.id != ADMIN:
        return

    original = mensaje.reply_to_message
    if original is None or not original.text:
        return
    if "Ticket de soporte" not in original.text and "Support ticket" not in original.text \
            and "Сообщение в поддержку" not in original.text:
        return

    import re as _re
    encontrado = _re.search(r"ID (\d+)", original.text)
    if not encontrado:
        return

    tg_id = int(encontrado.group(1))
    try:
        await bot.send_message(
            tg_id,
            t(idioma(tg_id), "soporte_respuesta", mensaje=mensaje.text or ""),
            reply_markup=teclado_fijo(tg_id),
        )
        await mensaje.reply(t(idioma(mensaje.from_user.id), "soporte_enviado"))
    except Exception:  # noqa: BLE001
        log.warning("no se pudo responder al cliente %s", tg_id)
        await mensaje.reply("No se pudo enviar: el cliente bloqueó el bot.")


@router.message(F.text, ~F.text.startswith("/"))
async def texto_libre(mensaje: Message, bot: Bot):
    tg_id = mensaje.from_user.id
    idi = idioma(tg_id)
    texto = (mensaje.text or "").strip()

    # 1) Botones del menu (tambien para el administrador)
    accion = ACCIONES.get(texto)
    if accion:
        try:
            await REPARTIDOR[accion](bot, tg_id)
        except Exception:  # noqa: BLE001
            log.exception("fallo en la accion %s", accion)
            await mensaje.answer(t(idi, "error_generico"))
        return

    # 2) Si acaba de pulsar "Canjear codigo", esto es el codigo
    cuando = ESPERANDO_PROMO.get(tg_id)
    if cuando and time.time() - cuando < MINUTOS_PROMO * 60:
        ESPERANDO_PROMO.pop(tg_id, None)
        dias = db.usar_promo(texto, tg_id)
        if dias is None:
            await mensaje.answer(
                t(idi, "promo_mal"), reply_markup=teclado_fijo(tg_id)
            )
            return
        try:
            actualizado = activar(tg_id, dias)
        except Exception:  # noqa: BLE001
            log.exception("fallo canjeando promo")
            await mensaje.answer(t(idi, "error_generico"))
            return
        await mensaje.answer(t(idi, "promo_ok", dias=dias), parse_mode=ParseMode.HTML)
        await enviar_conf(bot, tg_id, actualizado, t(idi, "pais"))
        return

    # 3) Cualquier otro texto es un mensaje para soporte.
    #    El administrador no genera tickets con sus propios mensajes.
    if ADMIN and tg_id == ADMIN:
        return

    await mensaje.answer(
        t(idi, "soporte_recibido"), reply_markup=teclado_fijo(tg_id)
    )

    destino = int(config.AVISOS_ID) if config.AVISOS_ID else ADMIN
    if not destino:
        return

    usuario = db.obtener(tg_id) or {}
    try:
        await bot.send_message(
            destino,
            t("es", "soporte_ticket",
              usuario=("@" + usuario["usuario"]) if usuario.get("usuario") else "—",
              id=tg_id,
              mensaje=texto),
            parse_mode=None,
        )
    except Exception:  # noqa: BLE001
        log.warning("no se pudo enviar el ticket de %s", tg_id)


# --------------------------------------------------------------------------- #
# Botones internos (submenús)
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == "menu")
async def volver_menu(llamada: CallbackQuery, bot: Bot):
    idi = idioma(llamada.from_user.id)
    await llamada.message.edit_text(
        t(idi, "bienvenida", marca=config.MARCA, dias=config.DIAS_PRUEBA),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=t(idi, "menu_comprar"), callback_data="comprar"),
            InlineKeyboardButton(text=t(idi, "menu_mi_vpn"), callback_data="mi_vpn"),
        ]]),
    )
    await llamada.answer()


@router.callback_query(F.data == "comprar")
async def cb_comprar(llamada: CallbackQuery, bot: Bot):
    idi = idioma(llamada.from_user.id)
    await llamada.answer()
    await llamada.message.edit_text(
        t(idi, "comprar_titulo"),
        reply_markup=teclado_planes(llamada.from_user.id),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("pc:"))
async def cb_pais_compra(llamada: CallbackQuery, bot: Bot):
    """Guarda el pais elegido y muestra los planes."""
    await llamada.answer()

    _, nodo_id = llamada.data.split(":")
    tg_id = llamada.from_user.id
    idi = idioma(tg_id)

    if nodos.existe(nodo_id):
        db.guardar(tg_id, pais_compra=nodo_id)

    nodo = nodos.por_id(nodo_id)
    await llamada.message.edit_text(
        t(idi, "comprar_titulo") + f"\n\n🌍 {nodo['bandera']} <b>{nodo['nombre']}</b>",
        reply_markup=teclado_planes(tg_id),
        parse_mode=ParseMode.HTML,
    )


async def _menu_metodos(llamada: CallbackQuery, meses: int) -> None:
    """Pantalla con las formas de pago del plan elegido."""
    tg_id = llamada.from_user.id
    idi = idioma(tg_id)

    filas = [
        [InlineKeyboardButton(
            text=t(idi, "metodo_stars_corto"),
            callback_data=f"metodo:stars:{meses}")],
    ]

    enlace = ""
    base = _web_pagos().rstrip("/")
    if base.startswith("https://") or base.startswith("http://"):
        enlace = f"{base}/?p={meses}&u={tg_id}"
        filas.append([InlineKeyboardButton(text=t(idi, "metodo_web"), url=enlace)])

    filas.append([InlineKeyboardButton(text="◀️", callback_data="comprar")])

    texto = (
        t(idi, "plan_linea", duracion=_duracion(meses, idi))
        + "\n"
        + t(
            idi, "plan_precios",
            estrellas=config.PRECIOS.get(meses, 0),
            rub=config.PRECIOS_RUB.get(meses, 0),
        )
        + "\n\n"
        + t(idi, "metodo_titulo")
    )
    teclado = InlineKeyboardMarkup(inline_keyboard=filas)
    try:
        await llamada.message.edit_text(texto, reply_markup=teclado, parse_mode=ParseMode.HTML)
    except Exception:  # noqa: BLE001
        log.exception("no se pudo editar el mensaje del plan %s", meses)
        await llamada.bot.send_message(tg_id, texto, reply_markup=teclado, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("plan:"))
async def cb_plan(llamada: CallbackQuery, bot: Bot):
    """Plan elegido: formas de pago."""
    await llamada.answer()
    meses = int(llamada.data.split(":")[1])
    await _menu_metodos(llamada, meses)


@router.callback_query(F.data.startswith("pais:"))
async def cb_pais(llamada: CallbackQuery, bot: Bot):
    """Guarda el pais elegido y sigue con las formas de pago."""
    await llamada.answer()

    _, nodo_id, meses_texto = llamada.data.split(":")
    meses = int(meses_texto)
    tg_id = llamada.from_user.id

    if nodos.existe(nodo_id):
        db.guardar(tg_id, servidor=nodo_id)

    await _menu_metodos(llamada, meses)


@router.callback_query(F.data.startswith("metodo:stars:"))
async def cb_estrellas(llamada: CallbackQuery, bot: Bot):
    """Estrellas: pagar con las que tiene o comprar si no tiene."""
    await llamada.answer()

    meses = int(llamada.data.split(":")[2])
    tg_id = llamada.from_user.id
    idi = idioma(tg_id)
    cantidad = config.PRECIOS[meses]

    teclado = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t(idi, "estrellas_pagar"),
            callback_data=f"estrellas:pagar:{meses}")],
        [InlineKeyboardButton(
            text=t(idi, "estrellas_comprar"),
            callback_data=f"estrellas:comprar:{meses}")],
        [InlineKeyboardButton(text="◀️", callback_data=f"plan:{meses}")],
    ])

    try:
        await bot.send_message(
            tg_id,
            t(idi, "estrellas_titulo", cantidad=cantidad),
            reply_markup=teclado,
            parse_mode=ParseMode.HTML,
        )
    except Exception:  # noqa: BLE001
        log.exception("no se pudo mostrar la pantalla de estrellas")


@router.callback_query(F.data.startswith("estrellas:comprar:"))
async def cb_estrellas_comprar(llamada: CallbackQuery, bot: Bot):
    """Explica cómo comprar estrellas con SBP y vuelve a la factura."""
    await llamada.answer()

    meses = int(llamada.data.split(":")[2])
    tg_id = llamada.from_user.id
    idi = idioma(tg_id)
    cantidad = config.PRECIOS[meses]
    usuario = db.obtener(tg_id) or {}
    nombre = usuario.get("usuario")
    quien = ("@" + nombre) if nombre else "—"

    teclado = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t(idi, "estrellas_ir", cantidad=cantidad),
            url=getattr(config, "ESTRELLAS_URL", ""))],
        [InlineKeyboardButton(
            text=t(idi, "estrellas_volver"),
            callback_data=f"metodo:stars:{meses}")],
        [InlineKeyboardButton(text="◀️", callback_data=f"plan:{meses}")],
    ])

    await bot.send_message(
        tg_id,
        t(idi, "estrellas_instrucciones",
          servicio=getattr(config, "ESTRELLAS_SERVICIO", "krab.gg bot"),
          cantidad=cantidad,
          usuario=quien),
        reply_markup=teclado,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


@router.callback_query(F.data.startswith("estrellas:pagar:"))
async def cb_estrellas_pagar(llamada: CallbackQuery, bot: Bot):
    await llamada.answer()

    meses = int(llamada.data.split(":")[2])
    estrellas = config.PRECIOS[meses]
    idi = idioma(llamada.from_user.id)

    await bot.send_invoice(
        chat_id=llamada.from_user.id,
        title=f"{config.MARCA} · {_duracion(meses, idi)}",
        description=t(
            idi, "factura_desc",
            marca=config.MARCA,
            duracion=_duracion(meses, idi),
            fecha=fecha(int(time.time()) + (30 * meses + _regalo_dias(meses)) * DIA),
        ),
        payload=f"plan:{meses}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=f"{meses} m", amount=estrellas)],
    )


@router.callback_query(F.data.startswith("metodo:crypto:"))
async def cb_cripto(llamada: CallbackQuery):
    meses = int(llamada.data.split(":")[2])
    idi = idioma(llamada.from_user.id)

    factura = await pagos.crear_factura(meses, llamada.from_user.id)
    if not factura or not factura.get("url"):
        await llamada.answer(t(idi, "cripto_no"), show_alert=True)
        return

    teclado = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🪙 {factura['monto']} USDT", url=factura["url"])],
        [InlineKeyboardButton(text="◀️", callback_data="comprar")],
    ])
    await llamada.message.edit_text(
        t(idi, "cripto_texto", monto=factura["monto"], url=factura["url"]),
        reply_markup=teclado,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    await llamada.answer()


@router.callback_query(F.data.startswith("metodo:manual:"))
async def cb_manual(llamada: CallbackQuery, bot: Bot):
    """SBP / tarjeta rusa: importe, telefono (y QR si esta configurado)."""
    meses = int(llamada.data.split(":")[2])
    tg_id = llamada.from_user.id
    idi = idioma(tg_id)
    importe = config.PRECIOS_RUB.get(meses, 0)

    # Se responde al toque de inmediato: el boton nunca se queda girando.
    await llamada.answer()

    texto = t(idi, "manual_texto",
              importe=importe,
              id=tg_id,
              duracion=_duracion(meses, idi))

    teclado = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t(idi, "manual_boton"), callback_data=f"paguei:{meses}")],
        [InlineKeyboardButton(text="◀️", callback_data="comprar")],
    ])

    qr = db.leer_ajuste("qr_sbp") or config.SBP_QR_URL
    if not qr:
        await bot.send_message(
            tg_id,
            "El pago por QR no está disponible ahora mismo.",
        )
        return
    enviado = False
    if qr:
        try:
            await bot.send_photo(
                chat_id=tg_id,
                photo=qr,
                caption=texto,
                parse_mode=ParseMode.HTML,
                reply_markup=teclado,
            )
            enviado = True
        except Exception:  # noqa: BLE001
            log.exception("no se pudo enviar el QR; se manda solo el texto")
    if enviado:
        try:
            await llamada.message.delete()
        except Exception:  # noqa: BLE001
            pass
    else:
        await llamada.message.edit_text(
            texto,
            reply_markup=teclado,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )


async def avisar_pago(bot: Bot, tg_id: int, meses: int) -> None:
    """Avisa al dueño de un pago pendiente (botón para activar)."""
    usuario = db.obtener(tg_id) or {}
    destino = int(config.AVISOS_ID) if config.AVISOS_ID else ADMIN
    if destino:
        try:
            await bot.send_message(
                destino,
                t("es", "manual_admin",
                  usuario=usuario.get("usuario") or "—",
                  id=tg_id, meses=meses,
                  importe=config.PRECIOS_RUB.get(meses, 0)),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=f"✅ Activar {meses} mes(es)",
                        callback_data=f"act:{tg_id}:{meses}",
                    )
                ]]),
            )
        except Exception:  # noqa: BLE001
            log.warning("no se pudo avisar al administrador")

    if avisos is not None:
        await avisos.avisar(
            f"PAGO {config.PRECIOS_RUB.get(meses, 0)} RUB - "
            f"{usuario.get('usuario') or tg_id}",
            "Pago avisado desde la web de pago.\n\n"
            f"Usuario: {usuario.get('usuario') or '—'} (ID {tg_id})\n"
            f"Plan: {meses} mes(es)\n"
            f"Importe: {config.PRECIOS_RUB.get(meses, 0)} RUB\n\n"
            f"Comprueba tu banco y activa con /activar {tg_id} {meses}",
        )


@router.callback_query(F.data.startswith("paguei:"))
async def cb_paguei(llamada: CallbackQuery, bot: Bot):
    meses = int(llamada.data.split(":")[1])
    tg_id = llamada.from_user.id
    idi = idioma(tg_id)

    await avisar_pago(bot, tg_id, meses)

    await llamada.message.edit_text(
        t(idi, "manual_aviso"), reply_markup=teclado_volver(tg_id)
    )
    await llamada.answer()



@router.callback_query(F.data.startswith("act:"))
async def admin_activar(llamada: CallbackQuery, bot: Bot):
    """El administrador activa con un solo toque desde el aviso de pago."""
    if llamada.from_user.id != ADMIN:
        await llamada.answer("Solo para el administrador", show_alert=True)
        return

    _, sid, smeses = llamada.data.split(":")
    tg_id, meses = int(sid), int(smeses)
    db.crear_si_falta(tg_id, None)
    usuario = activar_plan(tg_id, meses)
    db.registrar_pago(
        tg_id, meses, config.PRECIOS_RUB.get(meses, 0),
        f"sbp:{int(time.time())}",
    )

    await llamada.message.edit_text(
        f"✅ Activado <code>{tg_id}</code> hasta {fecha(usuario['expira'])}",
        parse_mode=ParseMode.HTML,
    )
    try:
        await bot.send_message(
            tg_id,
            t(idioma(tg_id), "pago_ok", fecha=fecha(usuario["expira"])),
            parse_mode=ParseMode.HTML,
            reply_markup=teclado_fijo(tg_id),
        )
        await enviar_conf(bot, tg_id, usuario, "GeoiD · SBP")
    except Exception:  # noqa: BLE001
        log.warning("no se pudo avisar al cliente %s", tg_id)
    await recompensar_padrino(bot, tg_id)
    await entregar_proxy(bot, tg_id, meses)
    await llamada.answer("Activado")
@router.callback_query(F.data == "proxy")
async def cb_proxy(llamada: CallbackQuery, bot: Bot):
    tg_id = llamada.from_user.id
    usuario = db.obtener(tg_id) or {}
    if not usuario.get("proxy") or not usuario.get("proxy_secreto"):
        await llamada.answer(t(idioma(tg_id), "proxy_sin"), show_alert=True)
        return

    if not proxies_ok():
        await llamada.answer("El proxy no está disponible ahora mismo.", show_alert=True)
        return

    puerto = usuario["proxy_puerto"]
    secreto = usuario["proxy_secreto"]
    if not proxy_personal.activo(tg_id):
        datos = proxy_personal.crear(tg_id, secreto)
        puerto = datos["puerto"]
        db.guardar(tg_id, proxy_puerto=puerto)

    ips = proxy_personal.ips_conectadas(tg_id)
    enlace = (
        f"tg://proxy?server={config.PROXY_SERVIDOR}"
        f"&port={puerto}&secret={secreto}"
    )
    await bot.send_message(
        tg_id,
        t(idioma(tg_id), "proxy_regalo",
          enlace=enlace,
          servidor=config.PROXY_SERVIDOR,
          puerto=puerto,
          secreto=secreto)
        + f"\n\n⚙️ Dispositivos conectados ahora: {len(ips)}/"
        f"{config.PROXY_DISPOSITIVOS}",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    await llamada.answer()


@router.callback_query(F.data == "mi_vpn")
async def cb_mi_vpn(llamada: CallbackQuery, bot: Bot):
    await llamada.answer()
    await accion_mi_vpn(bot, llamada.from_user.id)


@router.callback_query(F.data == "reenviar")
async def cb_reenviar(llamada: CallbackQuery, bot: Bot):
    tg_id = llamada.from_user.id
    usuario = db.obtener(tg_id) or {}
    idi = usuario.get("idioma") or "es"
    if not usuario.get("ip"):
        await llamada.answer(t(idi, "mi_vpn_sin"), show_alert=True)
        return
    await enviar_conf(bot, tg_id, usuario, t(idi, "reenvio"))
    await bot.send_message(
        tg_id,
        t(idi, "instalar_conf"),
        parse_mode=ParseMode.HTML,
        reply_markup=teclado_fijo(tg_id),
    )
    await llamada.answer()


@router.callback_query(F.data.startswith("idi:"))
async def elegir_idioma(llamada: CallbackQuery, bot: Bot):
    idi = llamada.data.split(":")[1]
    tg_id = llamada.from_user.id
    db.guardar(tg_id, idioma=idi)
    await llamada.message.edit_text(t(idi, "idioma_ok"))
    # Se reenvía el menú fijo ya traducido.
    await bot.send_message(
        tg_id,
        t(idi, "bienvenida", marca=config.MARCA, dias=config.DIAS_PRUEBA),
        reply_markup=teclado_fijo(tg_id),
        parse_mode=ParseMode.HTML,
    )
    await llamada.answer()


# --------------------------------------------------------------------------- #
# Pagos con estrellas
# --------------------------------------------------------------------------- #
@router.pre_checkout_query()
async def preparar_pago(consulta: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(consulta.id, ok=True)


@router.callback_query(F.data == "dispositivo")
async def cb_dispositivo(llamada: CallbackQuery, bot: Bot):
    """Factura de un dispositivo adicional."""
    await llamada.answer()

    tg_id = llamada.from_user.id
    idi = idioma(tg_id)
    usuario = db.obtener(tg_id) or {}

    if not usuario.get("ip") or usuario.get("expira", 0) <= int(time.time()):
        await bot.send_message(tg_id, t(idi, "mi_vpn_sin"), reply_markup=teclado_fijo(tg_id))
        return

    await bot.send_invoice(
        chat_id=tg_id,
        title=t(idi, "extra_titulo", marca=config.MARCA),
        description=t(idi, "extra_desc", dias=config.DIAS_DISPOSITIVO),
        payload="extra:1",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="+1", amount=config.PRECIO_DISPOSITIVO_ESTRELLAS)],
    )


@router.message(F.successful_payment)
async def pago_recibido(mensaje: Message, bot: Bot):
    pago = mensaje.successful_payment
    if not pago:
        return

    if pago.invoice_payload.startswith("extra:"):
        tg_id = mensaje.from_user.id
        idi = idioma(tg_id)
        usuario = db.obtener(tg_id) or {}
        actuales = int(usuario.get("dispositivos") or 1)

        if actuales >= config.MAX_DISPOSITIVOS:
            await mensaje.answer(t(idi, "extra_max", maximo=config.MAX_DISPOSITIVOS))
            return

        nuevo = actuales + 1
        db.guardar(tg_id, dispositivos=nuevo)
        creados = crear_perfiles_faltantes(tg_id, dispositivo=nuevo)

        if avisos is not None:
            await avisos.avisar(
                f"DISPOSITIVO EXTRA - {tg_id}",
                f"El cliente {tg_id} compro un dispositivo adicional "
                f"({nuevo} en total). Estrellas: {pago.total_amount}",
            )

        await mensaje.answer(
            t(idi, "extra_ok", numero=nuevo, cuantos=max(1, creados)),
            parse_mode=ParseMode.HTML,
        )
        await enviar_conf(bot, tg_id, db.obtener(tg_id) or usuario,
                          t(idi, "reenvio_texto"), dispositivo=nuevo)
        return

    if not pago.invoice_payload.startswith("plan:"):
        return

    meses = int(pago.invoice_payload.split(":")[1])
    tg_id = mensaje.from_user.id
    idi = idioma(tg_id)

    try:
        actualizado = activar_plan(tg_id, meses)
    except Exception:  # noqa: BLE001
        log.exception("fallo activando tras el pago")
        await mensaje.answer(t(idi, "error_generico"))
        return

    db.registrar_pago(tg_id, meses, pago.total_amount,
                      pago.telegram_payment_charge_id or "")

    await recompensar_padrino(bot, tg_id)

    if avisos is not None:
        await avisos.avisar(
        f"VENTA {meses} mes(es) por estrellas - {tg_id}",
        f"Pago con estrellas de {tg_id}.\n"
        f"Plan: {meses} mes(es)\n"
        f"Estrellas: {pago.total_amount}\n"
        f"Activo hasta: {fecha(actualizado['expira'])}",
    )

    await mensaje.answer(
        t(idi, "pago_ok", fecha=fecha(actualizado["expira"])),
        parse_mode=ParseMode.HTML,
    )
    await enviar_conf(bot, tg_id, actualizado, f"{config.MARCA} · {meses} m")
    await entregar_proxy(bot, tg_id, meses)


# --------------------------------------------------------------------------- #
# Administración
# --------------------------------------------------------------------------- #
@router.message(Command("promo"))
async def comando_promo(mensaje: Message, command: CommandObject):
    """Administrador: crea o borra códigos promocionales.

    /promo CODIGO DIAS USOS [dd.mm.aaaa]
    /promo borrar CODIGO
    """
    if mensaje.from_user.id != ADMIN:
        return

    partes = (command.args or "").split()

    if len(partes) == 2 and partes[0].lower() == "borrar":
        codigo = partes[1].upper()
        if db.borrar_promo(codigo):
            await mensaje.answer(f"🗑 Código {codigo} eliminado.")
        else:
            await mensaje.answer(f"El código {codigo} no existe.")
        return

    if len(partes) < 3:
        await mensaje.answer(
            "Uso:\n"
            "/promo CODIGO DIAS USOS [dd.mm.aaaa]\n"
            "/promo borrar CODIGO\n\n"
            "Ejemplo: /promo VERANO 7 20 31.12.2026\n"
            "  → código VERANO, 7 días, 20 usos, caduca el 31.12.2026\n\n"
            "Ver todos: /promos"
        )
        return

    codigo = partes[0].upper()
    try:
        dias = int(partes[1])
        usos = int(partes[2])
    except ValueError:
        await mensaje.answer("Los días y los usos tienen que ser números.")
        return

    caduca = None
    if len(partes) >= 4:
        try:
            dia, mes, anio = partes[3].split(".")
            from datetime import datetime as _dt
            caduca = int(
                _dt(int(anio), int(mes), int(dia), 23, 59).timestamp()
            )
        except Exception:  # noqa: BLE001
            await mensaje.answer(
                "La fecha debe ser dd.mm.aaaa (por ejemplo 31.12.2026)."
            )
            return

    db.crear_promo(codigo, dias, usos, caduca)
    extra = f", caduca el {partes[3]}" if caduca else ""
    await mensaje.answer(
        f"✅ Código {codigo}: {dias} días, {usos} usos{extra}.\n"
        "Cada persona puede usarlo una sola vez."
    )



@router.message(Command("enlaces"))
async def comando_enlaces(mensaje: Message, bot: Bot):
    """Administrador: ver y refrescar los enlaces de descarga."""
    if mensaje.from_user.id != ADMIN:
        return

    if descargas is None:
        await mensaje.answer("El actualizador de enlaces no está instalado.")
        return

    datos = await descargas.actualizar()
    android, windows = descargas.enlaces(config.URL_ANDROID, config.URL_WINDOWS)

    texto = [
        "🔗 <b>Enlaces de descarga</b>\n",
        f"Versión publicada: <b>v{descargas.version_actual() or '?'}</b>",
        f"Última revisión: {descargas.ultima_revision()}",
        "",
        f"Android:\n<code>{android}</code>",
        "",
        f"Windows:\n<code>{windows}</code>",
    ]
    if not datos:
        texto.append("\n⚠️ No se pudo consultar GitHub ahora mismo.")

    await mensaje.answer(
        "\n".join(texto),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


@router.message(Command("promos"))
async def comando_promos(mensaje: Message):
    if mensaje.from_user.id != ADMIN:
        return

    promos = db.listar_promos()
    if not promos:
        await mensaje.answer("No hay códigos creados. Usa /promo CODIGO DIAS USOS")
        return

    from datetime import datetime as _dt

    lineas = ["🎟 <b>Códigos promocionales</b>\n"]
    for p in promos:
        restantes = p["usos"] - p["usados"]
        caduca = p.get("caduca")
        vence = ""
        if caduca:
            vence = " · caduca " + _dt.fromtimestamp(caduca).strftime("%d.%m.%Y")
        estado = "✅" if restantes > 0 else "⛔"
        lineas.append(
            f"{estado} <code>{p['codigo']}</code> · {p['dias']} días · "
            f"{restantes}/{p['usos']} usos{vence}"
        )

    await mensaje.answer("\n".join(lineas), parse_mode=ParseMode.HTML)


@router.message(Command("regalar"))
async def comando_regalar(mensaje: Message, command: CommandObject):
    if mensaje.from_user.id != ADMIN:
        return
    partes = (command.args or "").split()
    if len(partes) != 2:
        await mensaje.answer("Uso: /regalar ID DÍAS")
        return
    tg_id, dias = int(partes[0]), int(partes[1])
    db.crear_si_falta(tg_id, None)
    usuario = activar(tg_id, dias)
    await mensaje.answer(f"Activado para {tg_id} hasta {fecha(usuario['expira'])}.")


@router.message(Command("activar"))
async def comando_activar(mensaje: Message, command: CommandObject, bot: Bot):
    """Administrador: activa a mano un pago por transferencia."""
    if mensaje.from_user.id != ADMIN:
        return
    partes = (command.args or "").split()
    if len(partes) != 2:
        await mensaje.answer("Uso: /activar ID MESES")
        return
    tg_id, meses = int(partes[0]), int(partes[1])
    db.crear_si_falta(tg_id, None)
    usuario = activar_plan(tg_id, meses)
    db.registrar_pago(tg_id, meses, 0, f"manual:{int(time.time())}")
    await mensaje.answer(
        t(idioma(mensaje.from_user.id), "activar_ok",
          id=tg_id, fecha=fecha(usuario["expira"])),
        parse_mode=ParseMode.HTML,
    )
    try:
        await bot.send_message(
            tg_id,
            t(idioma(tg_id), "pago_ok", fecha=fecha(usuario["expira"])),
            parse_mode=ParseMode.HTML,
        )
        await enviar_conf(bot, tg_id, usuario, "GeoiD · transferencia")
        await recompensar_padrino(bot, tg_id)
        await entregar_proxy(bot, tg_id, meses)
    except Exception:  # noqa: BLE001
        log.warning("no se pudo avisar al cliente %s", tg_id)


@router.message(Command("diag"))
async def comando_diag(mensaje: Message, bot: Bot):
    """Diagnóstico para el dueño: qué versión hay y cómo está configurado."""
    if ADMIN and mensaje.from_user.id != ADMIN:
        return

    claves = [
        "metodo_web", "metodo_estrellas_comprar", "metodo_stars_corto",
        "estrellas_titulo", "estrellas_instrucciones", "estrellas_ir",
        "estrellas_volver", "manual_aviso",
    ]
    faltan = [c for c in claves if c not in textos.TEXTOS.get("ru", {})]

    lineas = [
        "<b>Diagnóstico</b>",
        f"bot.py: {'con avisar_pago' if 'avisar_pago' in globals() else 'VIEJO'}",
        f"pagado_: {'sí' if 'pagado_' in open(__file__, encoding='utf-8').read() else 'NO'}",
        f"WEB_PAGOS: <code>{_web_pagos() or '(vacío)'}</code>",
        f"precios ₽: {config.PRECIOS_RUB}",
        f"precios ⭐: {config.PRECIOS}",
        f"idioma por defecto: {config.IDIOMA_DEFECTO}",
        f"claves de texto que faltan: {faltan or 'ninguna'}",
        f"QR en el bot: {'sí' if hay_qr() else 'no'}",
        f"proxy propio: {'listo' if proxies_ok() else 'no disponible'}",
    ]
    await mensaje.answer("\n".join(lineas), parse_mode=ParseMode.HTML)


@router.message(Command("estrellas"))
async def comando_estrellas(mensaje: Message, bot: Bot, command: CommandObject):
    """Manda la factura de estrellas del plan indicado (por defecto 1 mes)."""
    argumento = (command.args or "").strip()
    meses = int(argumento) if argumento.isdigit() else 1
    if meses not in config.PRECIOS:
        meses = 1

    idi = idioma(mensaje.from_user.id)
    await bot.send_invoice(
        chat_id=mensaje.from_user.id,
        title=f"{config.MARCA} · {_duracion(meses, idi)}",
        description=t(
            idi, "factura_desc",
            marca=config.MARCA,
            duracion=_duracion(meses, idi),
            fecha=fecha(int(time.time()) + (30 * meses + _regalo_dias(meses)) * DIA),
        ),
        payload=f"plan:{meses}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=f"{meses} m", amount=config.PRECIOS[meses])],
    )


@router.message(Command("ticket"))
async def comando_ticket(mensaje: Message, bot: Bot):
    """Administrador: genera un ticket de prueba para comprobar el soporte."""
    if mensaje.from_user.id != ADMIN:
        return

    destino = int(config.AVISOS_ID) if config.AVISOS_ID else ADMIN
    if not destino:
        await mensaje.answer(
            "Falta GEOID_AVISOS_ID (o eres el único administrador)."
        )
        return

    usuario = db.obtener(ADMIN) or {}
    await bot.send_message(
        destino,
        t("es", "soporte_ticket",
          usuario=("@" + usuario["usuario"]) if usuario.get("usuario") else "prueba",
          id=ADMIN,
          mensaje="Ticket de prueba: responde a este mensaje y te llegará la respuesta al privado."),
    )
    await mensaje.answer("✅ Ticket de prueba enviado. Responde a ese mensaje para probar la respuesta.")


@router.message(Command("chatid"))
async def comando_chatid(mensaje: Message):
    """Dice el ID del chat actual. Sirve para configurar el grupo de avisos."""
    if ADMIN and mensaje.from_user.id != ADMIN:
        return
    await mensaje.answer(
        f"ID de este chat: <code>{mensaje.chat.id}</code>\n\n"
        "Para usarlo como destino de avisos, en el servidor:\n"
        f"<code>echo 'GEOID_AVISOS_ID={mensaje.chat.id}' >> /etc/geoid-bot.env "
        "&& systemctl restart geoid-bot</code>",
        parse_mode=ParseMode.HTML,
    )

@router.message(Command("qr"))
async def comando_qr(mensaje: Message):
    """Administrador: envia una foto con /qr para usarla como QR de pago."""
    if mensaje.from_user.id != ADMIN:
        await mensaje.answer(
            "Este comando es solo para el administrador.\n\n"
            f"Tu ID es {mensaje.from_user.id}. Para activarlo, en el servidor:\n"
            f"sed -i 's|^GEOID_ADMIN=.*|GEOID_ADMIN={mensaje.from_user.id}|' "
            "/etc/geoid-bot.env && systemctl restart geoid-bot"
        )
        return

    foto = None
    if mensaje.reply_to_message and mensaje.reply_to_message.photo:
        foto = mensaje.reply_to_message.photo[-1].file_id
    elif mensaje.photo:
        foto = mensaje.photo[-1].file_id

    if foto:
        db.guardar_ajuste("qr_sbp", foto)
        await mensaje.answer(
            "✅ QR guardado. Se enviará como imagen en los pagos por SBP.\n\n"
            "Para quitarlo: /qr borrar"
        )
        return

    if (mensaje.text or "").endswith("borrar"):
        db.guardar_ajuste("qr_sbp", None)
        await mensaje.answer("🗑 QR eliminado.")
        return

    await mensaje.answer(
        "Envíame una foto del QR de tu banco (СБП) y respóndele con /qr.\n\n"
        "También sirve: enviar la foto y luego escribir /qr."
    )

@router.message(Command("estado"))
async def comando_estado(mensaje: Message):
    if mensaje.from_user.id != ADMIN:
        return
    ahora = int(time.time())
    activos = db.activos_hasta(ahora)
    avisos = provision.revisar_servidor()
    texto = [
        f"Activos: {len(activos)}",
        f"Servidor: {config.ENDPOINT}",
        f"Interfaz: {config.AWG_INTERFAZ}",
        f"Estrellas: {config.PRECIOS}",
        f"Dólares: {config.PRECIOS_USD}",
        f"Cripto: {'activado' if pagos.disponible() else 'sin token'}",
        f"Avisos: {', '.join(avisos) if avisos else 'ninguno'}",
    ]
    await mensaje.answer("\n".join(texto))



@router.my_chat_member()
async def al_entrar_en_grupo(evento: ChatMemberUpdated, bot: Bot):
    """Al añadir el bot a un grupo, se le dice al administrador el id del chat."""
    if ADMIN == 0:
        return
    estado = evento.new_chat_member.status
    if estado not in ("member", "administrator"):
        return
    titulo = getattr(evento.chat, "title", None) or str(evento.chat.id)
    await bot.send_message(
        ADMIN,
        "✅ Me han añadido al chat <b>{}</b>.\n\n"
        "Si quieres que los avisos de pago lleguen aquí, en el servidor:\n"
        "<code>echo 'GEOID_AVISOS_ID={}' >> /etc/geoid-bot.env "
        "&& systemctl restart geoid-bot</code>".format(titulo, evento.chat.id),
        parse_mode=ParseMode.HTML,
    )

# --------------------------------------------------------------------------- #
# Tareas de fondo
# --------------------------------------------------------------------------- #
async def vigilar_caducidades(bot: Bot):
    """Cada 10 minutos quita del servidor a quien haya caducado."""
    while True:
        await asyncio.sleep(600)
        ahora = int(time.time())
        try:
            for usuario in db.caducados(ahora):
                for fila in db.perfiles(usuario["tg_id"]):
                    try:
                        nodos.borrar(nodos.por_id(fila["nodo"]), fila["ip"])
                    except Exception:  # noqa: BLE001
                        log.warning("no se pudo borrar el perfil %s de %s",
                                    fila["ip"], usuario["tg_id"])
                db.borrar_perfiles(usuario["tg_id"])
                db.guardar(
                    usuario["tg_id"],
                    ip=None, privada=None, publica=None, preshared=None,
                )
                if usuario.get("proxy") and proxy_personal is not None:
                    try:
                        proxy_personal.eliminar(usuario["tg_id"])
                    except Exception:  # noqa: BLE001
                        log.warning("no se pudo cerrar el proxy de %s", usuario["tg_id"])
                    db.guardar(usuario["tg_id"], proxy=0, proxy_puerto=None,
                               proxy_secreto=None)
                try:
                    await bot.send_message(
                        usuario["tg_id"],
                        t(usuario.get("idioma") or "es", "caducado"),
                    )
                except Exception:  # noqa: BLE001
                    pass
                log.info("caducado %s (%s)", usuario["tg_id"], usuario.get("ip"))
        except Exception:  # noqa: BLE001
            log.exception("error revisando caducidades")


async def vigilar_cripto(bot: Bot):
    """Cada 45 segundos mira si alguien pagó con cripto y lo activa."""
    if not pagos.disponible():
        log.info("cripto desactivado (falta GEOID_CRYPTO_TOKEN)")
        return

    while True:
        await asyncio.sleep(45)
        try:
            for factura in await pagos.facturas_pagadas():
                datos = pagos.leer_payload(factura.get("payload") or "")
                if not datos:
                    continue
                tg_id, meses = datos
                cargo = f"crypto:{factura.get('invoice_id')}"
                if db.pago_existe(cargo):
                    continue

                db.crear_si_falta(tg_id, None)
                usuario = activar_plan(tg_id, meses)
                db.registrar_pago(
                    tg_id, meses,
                    int(float(factura.get("amount") or 0)), cargo,
                )
                try:
                    await bot.send_message(
                        tg_id,
                        t(idioma(tg_id), "pago_ok", fecha=fecha(usuario["expira"])),
                        parse_mode=ParseMode.HTML,
                    )
                    await enviar_conf(bot, tg_id, usuario, "GeoiD · cripto")
                except Exception:  # noqa: BLE001
                    log.warning("no se pudo avisar a %s", tg_id)
                if avisos is not None:
                    await avisos.avisar(
                    f"VENTA {meses} mes(es) con cripto - {tg_id}",
                    f"Pago en cripto de {tg_id}.\n"
                    f"Plan: {meses} mes(es)\n"
                    f"Importe: {factura.get('amount')} {factura.get('asset')}\n"
                    f"Activo hasta: {fecha(usuario['expira'])}",
                )
                await recompensar_padrino(bot, tg_id)
                await entregar_proxy(bot, tg_id, meses)
                log.info("cripto pagado: %s -> %s meses", tg_id, meses)
        except Exception:  # noqa: BLE001
            log.exception("error revisando pagos con cripto")



async def configurar_comandos(bot: Bot):
    """Menú ☰ de Telegram: así el usuario siempre puede volver al menú."""
    publicos = [
        BotCommand(command="start", description="Menú principal"),
        BotCommand(command="menu", description="Mostrar el menú"),
    ]
    try:
        await bot.set_my_commands(publicos)
    except Exception:  # noqa: BLE001
        log.warning("no se pudieron fijar los comandos")

    if ADMIN:
        try:
            await bot.set_my_commands(
                publicos + [
                    BotCommand(command="chatid", description="ID de este chat"),
                    BotCommand(command="qr", description="Guardar el QR de pago"),
                    BotCommand(command="estado", description="Estado del bot"),
                    BotCommand(command="activar", description="Activar ID MESES"),
                    BotCommand(command="regalar", description="Regalar ID DÍAS"),
                    BotCommand(command="promo", description="Crear o borrar código"),
                    BotCommand(command="promos", description="Ver códigos"),
                    BotCommand(command="enlaces", description="Enlaces de descarga"),
                    BotCommand(command="ticket", description="Probar el soporte"),
                ],
                scope=BotCommandScopeChat(chat_id=ADMIN),
            )
        except Exception:  # noqa: BLE001
            log.warning("no se pudieron fijar los comandos de administrador")

async def vigilar_duplicados(bot: Bot):
    """Avisa si varias cuentas de prueba salen por la misma IP publica."""
    destino = int(config.AVISOS_ID) if config.AVISOS_ID else ADMIN
    if not destino:
        return

    while True:
        await asyncio.sleep(900)
        try:
            ips = provision.endpoints()
            if not ips:
                continue

            usuarios = db.con_peer()
            por_ip: dict[str, list] = {}
            for usuario in usuarios:
                ip = ips.get(usuario["publica"] or "")
                if not ip:
                    continue
                if not usuario["prueba_usada"] or db.ha_pagado(usuario["tg_id"]):
                    continue  # clientes que pagan no cuentan
                por_ip.setdefault(ip, []).append(usuario)

            for ip, cuentas in por_ip.items():
                if len(cuentas) < 2:
                    continue
                clave = ip + ":" + ",".join(str(c["tg_id"]) for c in cuentas)
                if db.aviso_visto(clave):
                    continue
                db.marcar_aviso(clave)

                detalle = "\n".join(
                    f"· {c['usuario'] or '—'} (ID <code>{c['tg_id']}</code>)"
                    for c in cuentas
                )
                await bot.send_message(
                    destino,
                    "🕵️ <b>Posible granja de pruebas</b>\n\n"
                    f"IP pública: <code>{ip}</code>\n"
                    f"Cuentas de prueba conectadas a la vez: {len(cuentas)}\n\n"
                    f"{detalle}\n\n"
                    "Si quieres cortarles el acceso:\n"
                    + "\n".join(
                        f"<code>awg set awg0 peer {c['publica']} remove</code>"
                        for c in cuentas
                    ),
                    parse_mode=ParseMode.HTML,
                )
                log.info("duplicado detectado en %s (%s cuentas)", ip, len(cuentas))
        except Exception:  # noqa: BLE001
            log.exception("error revisando duplicados")

async def vigilar_proxies(bot: Bot):
    """Si un proxy personal supera los dispositivos permitidos, avisa y corta."""
    destino = int(config.AVISOS_ID) if config.AVISOS_ID else ADMIN
    while True:
        await asyncio.sleep(300)
        if not proxies_ok():
            continue
        try:
            with db.conectar() as con:
                usuarios = con.execute(
                    "SELECT tg_id, usuario, proxy_puerto FROM usuarios "
                    "WHERE proxy = 1 AND proxy_puerto IS NOT NULL"
                ).fetchall()

            for usuario in usuarios:
                tg_id = usuario["tg_id"]
                ips = proxy_personal.ips_conectadas(tg_id)
                if len(ips) <= config.PROXY_DISPOSITIVOS:
                    continue

                sobra = ips[config.PROXY_DISPOSITIVOS:]
                if destino:
                    await bot.send_message(
                        destino,
                        "⚠️ <b>Proxy con demasiados dispositivos</b>\n\n"
                        f"Cliente: {usuario['usuario'] or '—'} "
                        f"(ID <code>{tg_id}</code>)\n"
                        f"Conectados: {len(ips)} de {config.PROXY_DISPOSITIVOS}\n"
                        f"IPs: <code>{', '.join(ips)}</code>\n\n"
                        "Para cortar el sobrante:\n"
                        + "\n".join(
                            f"<code>iptables -I INPUT -p tcp --dport "
                            f"{usuario['proxy_puerto']} -s {ip} -j DROP</code>"
                            for ip in sobra
                        ),
                        parse_mode=ParseMode.HTML,
                    )
                log.info("proxy %s con %s dispositivos", tg_id, len(ips))
        except Exception:  # noqa: BLE001
            log.exception("error revisando los proxies personales")



async def vigilar_descargas(bot: Bot):
    """Cada 6 horas mira si hay versión nueva y actualiza los enlaces."""
    if descargas is None:
        return

    destino = int(config.AVISOS_ID) if config.AVISOS_ID else ADMIN

    async def avisar(version: str) -> None:
        if not destino:
            return
        android, windows = descargas.enlaces(config.URL_ANDROID, config.URL_WINDOWS)
        try:
            await bot.send_message(
                destino,
                "🆕 <b>Nueva versión publicada: v" + version + "</b>\n\n"
                "Los enlaces del bot ya están actualizados:\n"
                f"Android: {android}\n"
                f"Windows: {windows}",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except Exception:  # noqa: BLE001
            log.warning("no se pudo avisar de la versión nueva")

    while True:
        try:
            await descargas.actualizar(avisar)
        except Exception:  # noqa: BLE001
            log.exception("error actualizando los enlaces de descarga")
        await asyncio.sleep(6 * 3600)


async def main():
    if not config.TOKEN:
        raise SystemExit("Falta GEOID_TOKEN (token del bot de BotFather)")

    bot = Bot(
        config.TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    await configurar_comandos(bot)
    asyncio.create_task(vigilar_caducidades(bot))
    asyncio.create_task(vigilar_cripto(bot))
    asyncio.create_task(vigilar_duplicados(bot))
    asyncio.create_task(vigilar_proxies(bot))
    asyncio.create_task(vigilar_descargas(bot))
    log.info("bot en marcha · servidor %s", config.ENDPOINT)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
