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
    BufferedInputFile,
    CallbackQuery,
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
import pagos
import provision
from textos import IDIOMAS, t

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
log = logging.getLogger("geoid")

router = Router()
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
def idioma(tg_id: int) -> str:
    usuario = db.obtener(tg_id)
    return (usuario or {}).get("idioma") or "es"


def fecha(instante: int) -> str:
    return datetime.fromtimestamp(instante, tz=timezone.utc).strftime("%d.%m.%Y %H:%M UTC")


def dias_restantes(instante: int) -> int:
    return max(0, (instante - int(time.time()) + DIA - 1) // DIA)


def teclado_fijo(tg_id: int) -> ReplyKeyboardMarkup:
    """Menú de abajo: se queda siempre visible."""
    idi = idioma(tg_id)
    filas = [
        [t(idi, "menu_prueba"), t(idi, "menu_comprar")],
        [t(idi, "menu_mi_vpn"), t(idi, "menu_pais")],
        [t(idi, "menu_invitar"), t(idi, "menu_promo")],
        [t(idi, "menu_ayuda"), t(idi, "menu_idioma")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=x) for x in fila] for fila in filas],
        resize_keyboard=True,
        is_persistent=True,
    )


def teclado_planes(tg_id: int) -> InlineKeyboardMarkup:
    idi = idioma(tg_id)
    filas = [
        [InlineKeyboardButton(
            text=t(idi, "plan_boton", meses=meses, estrellas=estrellas),
            callback_data=f"plan:{meses}",
        )]
        for meses, estrellas in config.PRECIOS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=filas)


def teclado_volver(tg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="◀️", callback_data="menu")
    ]])


def hay_qr() -> bool:
    """El pago por QR solo existe si hay un QR guardado."""
    return bool(db.leer_ajuste("qr_sbp") or config.SBP_QR_URL)


def _destino(evento: Message | CallbackQuery) -> int:
    return evento.message.chat.id if isinstance(evento, CallbackQuery) else evento.chat.id


# --------------------------------------------------------------------------- #
# Accesos
# --------------------------------------------------------------------------- #
def activar(tg_id: int, dias: int) -> dict:
    """Crea el peer si hace falta y extiende la caducidad."""
    usuario = db.obtener(tg_id) or {}
    ahora = int(time.time())

    if usuario.get("ip"):
        base = max(ahora, int(usuario.get("expira") or 0))
        db.guardar(tg_id, expira=base + dias * DIA)
        return db.obtener(tg_id)

    cliente = provision.crear_cliente()
    db.guardar(
        tg_id,
        ip=cliente["ip"],
        privada=cliente["privada"],
        publica=cliente["publica"],
        preshared=cliente["preshared"],
        expira=ahora + dias * DIA,
    )
    return db.obtener(tg_id)


async def enviar_conf(bot: Bot, tg_id: int, usuario: dict, texto: str):
    contenido = provision.generar_conf(
        usuario["privada"], usuario["preshared"], usuario["ip"]
    )
    archivo = BufferedInputFile(
        contenido.encode("utf-8"),
        filename=f"geoid-{usuario['ip'].replace('.', '-')}.conf",
    )
    await bot.send_document(
        chat_id=tg_id,
        document=archivo,
        caption=texto,
        parse_mode=ParseMode.HTML,
    )


# --------------------------------------------------------------------------- #
# Acciones (las usan tanto el teclado fijo como los botones internos)
# --------------------------------------------------------------------------- #
async def accion_prueba(bot: Bot, tg_id: int) -> None:
    usuario = db.obtener(tg_id) or {}
    idi = usuario.get("idioma") or "es"
    ahora = int(time.time())

    if usuario.get("expira", 0) > ahora:
        await bot.send_message(
            tg_id, t(idi, "prueba_cabecera", fecha=fecha(usuario["expira"]))
        )
        return

    if usuario.get("prueba_usada"):
        await bot.send_message(tg_id, t(idi, "prueba_ya_usada"))
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
    )
    await enviar_conf(bot, tg_id, actualizado, t(idi, "pais"))


async def accion_comprar(bot: Bot, tg_id: int) -> None:
    idi = idioma(tg_id)
    await bot.send_message(
        tg_id, t(idi, "comprar_titulo"),
        reply_markup=teclado_planes(tg_id),
        parse_mode=ParseMode.HTML,
    )


async def accion_mi_vpn(bot: Bot, tg_id: int) -> None:
    usuario = db.obtener(tg_id) or {}
    idi = usuario.get("idioma") or "es"
    ahora = int(time.time())

    if not usuario.get("ip") or usuario.get("expira", 0) <= ahora:
        texto = t(idi, "mi_vpn_sin") if not usuario.get("ip") else t(idi, "caducado")
        await bot.send_message(tg_id, texto)
        return

    teclado = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t(idi, "boton_reenviar"), callback_data="reenviar")
    ]])
    await bot.send_message(
        tg_id,
        t(idi, "mi_vpn_activo",
          pais=t(idi, "pais"),
          ip=usuario["ip"],
          fecha=fecha(usuario["expira"]),
          dias=dias_restantes(usuario["expira"]),
          enlace=""),
        reply_markup=teclado,
        parse_mode=ParseMode.HTML,
    )


async def accion_pais(bot: Bot, tg_id: int) -> None:
    await bot.send_message(tg_id, t(idioma(tg_id), "pais_unico"))


async def accion_invitar(bot: Bot, tg_id: int) -> None:
    usuario = db.obtener(tg_id) or {}
    idi = usuario.get("idioma") or "es"
    me = await bot.get_me()
    enlace = f"https://t.me/{me.username}?start={usuario.get('codigo_ref') or 'r'}"
    with db.conectar() as con:
        cuantos = con.execute(
            "SELECT COUNT(*) c FROM usuarios WHERE referido = ?", (tg_id,)
        ).fetchone()["c"]
    await bot.send_message(
        tg_id,
        t(idi, "invitar_texto", dias=config.DIAS_INVITADO, enlace=enlace, cuantos=cuantos),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


async def accion_promo(bot: Bot, tg_id: int) -> None:
    await bot.send_message(tg_id, t(idioma(tg_id), "promo_pedir"))


async def accion_ayuda(bot: Bot, tg_id: int) -> None:
    idi = idioma(tg_id)
    await bot.send_message(
        tg_id,
        t(idi, "ayuda", android=config.URL_ANDROID, windows=config.URL_WINDOWS),
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
@router.message(CommandStart())
async def start(mensaje: Message, bot: Bot, command: CommandObject):
    referido = None
    if command.args and command.args.startswith("r"):
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
@router.message(F.text, ~F.text.startswith("/"))
async def texto_libre(mensaje: Message, bot: Bot):
    tg_id = mensaje.from_user.id
    idi = idioma(tg_id)
    texto = (mensaje.text or "").strip()

    accion = ACCIONES.get(texto)
    if accion:
        try:
            await REPARTIDOR[accion](bot, tg_id)
        except Exception:  # noqa: BLE001
            log.exception("fallo en la accion %s", accion)
            await mensaje.answer(t(idi, "error_generico"))
        return

    # Un texto suelto puede ser un código promocional.
    dias = db.usar_promo(texto)
    if dias is None:
        await mensaje.answer(t(idi, "promo_mal"))
        return

    try:
        actualizado = activar(tg_id, dias)
    except Exception:  # noqa: BLE001
        log.exception("fallo canjeando promo")
        await mensaje.answer(t(idi, "error_generico"))
        return

    await mensaje.answer(t(idi, "promo_ok", dias=dias), parse_mode=ParseMode.HTML)
    await enviar_conf(bot, tg_id, actualizado, t(idi, "pais"))


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
    await llamada.message.edit_text(
        t(idi, "comprar_titulo"),
        reply_markup=teclado_planes(llamada.from_user.id),
        parse_mode=ParseMode.HTML,
    )
    await llamada.answer()


@router.callback_query(F.data.startswith("plan:"))
async def cb_plan(llamada: CallbackQuery):
    meses = int(llamada.data.split(":")[1])
    idi = idioma(llamada.from_user.id)

    filas = [
        [InlineKeyboardButton(
            text=t(idi, "metodo_stars"), callback_data=f"metodo:stars:{meses}")],
        [InlineKeyboardButton(
            text=t(idi, "metodo_crypto"), callback_data=f"metodo:crypto:{meses}")],
    ]
    # El pago por QR solo aparece si hay un QR guardado.
    if hay_qr():
        filas.append([InlineKeyboardButton(
            text=t(idi, "metodo_manual"), callback_data=f"metodo:manual:{meses}")])
    filas.append([InlineKeyboardButton(text="◀️", callback_data="comprar")])
    await llamada.message.edit_text(
        t(idi, "metodo_titulo"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=filas),
    )
    await llamada.answer()


@router.callback_query(F.data.startswith("metodo:stars:"))
async def cb_estrellas(llamada: CallbackQuery, bot: Bot):
    meses = int(llamada.data.split(":")[2])
    estrellas = config.PRECIOS[meses]
    idi = idioma(llamada.from_user.id)

    await bot.send_invoice(
        chat_id=llamada.from_user.id,
        title=f"{config.MARCA} · {meses} {'mes' if meses == 1 else 'meses'}",
        description=t(idi, f"plan_{'mes' if meses == 1 else ('3meses' if meses == 3 else 'anio')}"),
        payload=f"plan:{meses}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=f"{meses} m", amount=estrellas)],
    )
    await llamada.answer()


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

    texto = t(idi, "manual_texto", importe=importe, id=tg_id)

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


@router.callback_query(F.data.startswith("paguei:"))
async def cb_paguei(llamada: CallbackQuery, bot: Bot):
    meses = int(llamada.data.split(":")[1])
    tg_id = llamada.from_user.id
    idi = idioma(tg_id)
    usuario = db.obtener(tg_id) or {}

    if ADMIN:
        try:
            await bot.send_message(
                ADMIN,
                t(idioma(ADMIN), "manual_admin",
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
    usuario = activar(tg_id, 30 * meses)
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
    await llamada.answer("Activado")
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


@router.message(F.successful_payment)
async def pago_recibido(mensaje: Message, bot: Bot):
    pago = mensaje.successful_payment
    if not pago or not pago.invoice_payload.startswith("plan:"):
        return

    meses = int(pago.invoice_payload.split(":")[1])
    tg_id = mensaje.from_user.id
    idi = idioma(tg_id)

    try:
        actualizado = activar(tg_id, 30 * meses)
    except Exception:  # noqa: BLE001
        log.exception("fallo activando tras el pago")
        await mensaje.answer(t(idi, "error_generico"))
        return

    db.registrar_pago(tg_id, meses, pago.total_amount,
                      pago.telegram_payment_charge_id or "")

    usuario = db.obtener(tg_id) or {}
    padrino = usuario.get("referido")
    if padrino:
        try:
            activar(padrino, config.DIAS_INVITADO)
            await bot.send_message(padrino, t(idioma(padrino), "invitar_bienvenida"))
        except Exception:  # noqa: BLE001
            log.warning("no se pudo premiar al padrino %s", padrino)

    await mensaje.answer(
        t(idi, "pago_ok", fecha=fecha(actualizado["expira"])),
        parse_mode=ParseMode.HTML,
    )
    await enviar_conf(bot, tg_id, actualizado, f"{config.MARCA} · {meses} m")


# --------------------------------------------------------------------------- #
# Administración
# --------------------------------------------------------------------------- #
@router.message(Command("promo"))
async def comando_promo(mensaje: Message, command: CommandObject):
    if mensaje.from_user.id != ADMIN:
        return
    partes = (command.args or "").split()
    if len(partes) != 3:
        await mensaje.answer("Uso: /promo CODIGO DIAS USOS")
        return
    codigo, dias, usos = partes[0], int(partes[1]), int(partes[2])
    db.crear_promo(codigo, dias, usos)
    await mensaje.answer(f"Código {codigo.upper()}: {dias} días, {usos} usos.")


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
    usuario = activar(tg_id, 30 * meses)
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
    except Exception:  # noqa: BLE001
        log.warning("no se pudo avisar al cliente %s", tg_id)


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
                if usuario.get("publica"):
                    provision.eliminar_cliente(usuario["publica"])
                db.guardar(
                    usuario["tg_id"],
                    ip=None, privada=None, publica=None, preshared=None,
                )
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
                usuario = activar(tg_id, 30 * meses)
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
                log.info("cripto pagado: %s -> %s meses", tg_id, meses)
        except Exception:  # noqa: BLE001
            log.exception("error revisando pagos con cripto")


async def main():
    if not config.TOKEN:
        raise SystemExit("Falta GEOID_TOKEN (token del bot de BotFather)")

    bot = Bot(
        config.TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    asyncio.create_task(vigilar_caducidades(bot))
    asyncio.create_task(vigilar_cripto(bot))
    log.info("bot en marcha · servidor %s", config.ENDPOINT)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
