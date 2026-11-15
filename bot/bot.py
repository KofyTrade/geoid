"""Bot de Telegram de GeoiD VPN.

Vende y aprovisiona accesos AmneziaWG: genera el peer en el servidor y entrega
al cliente su fichero .conf.

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
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

import config
import db
import provision
from textos import IDIOMAS, t

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
log = logging.getLogger("geoid")

router = Router()
ADMIN = int(os.environ.get("GEOID_ADMIN", "0") or 0)
DIA = 86400


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


def menu_principal(tg_id: int) -> InlineKeyboardMarkup:
    idi = idioma(tg_id)
    filas = [
        [
            InlineKeyboardButton(text=t(idi, "menu_prueba"), callback_data="prueba"),
            InlineKeyboardButton(text=t(idi, "menu_comprar"), callback_data="comprar"),
        ],
        [
            InlineKeyboardButton(text=t(idi, "menu_mi_vpn"), callback_data="mi_vpn"),
            InlineKeyboardButton(text=t(idi, "menu_pais"), callback_data="pais"),
        ],
        [
            InlineKeyboardButton(text=t(idi, "menu_invitar"), callback_data="invitar"),
            InlineKeyboardButton(text=t(idi, "menu_promo"), callback_data="promo"),
        ],
        [
            InlineKeyboardButton(text=t(idi, "menu_ayuda"), callback_data="ayuda"),
            InlineKeyboardButton(text=t(idi, "menu_idioma"), callback_data="idioma"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=filas)


def teclado_planes(tg_id: int) -> InlineKeyboardMarkup:
    idi = idioma(tg_id)
    filas = []
    for meses, estrellas in config.PRECIOS.items():
        filas.append([
            InlineKeyboardButton(
                text=t(idi, "plan_boton", meses=meses, estrellas=estrellas),
                callback_data=f"plan:{meses}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=filas)


def teclado_volver(tg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="◀️", callback_data="menu")
    ]])


# --------------------------------------------------------------------------- #
# Alta de accesos
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
# Comandos
# --------------------------------------------------------------------------- #
@router.message(CommandStart())
async def start(mensaje: Message, comando: CommandObject):
    referido = None
    if comando.args and comando.args.startswith("r"):
        padrino = db.por_codigo(comando.args)
        if padrino and padrino["tg_id"] != mensaje.from_user.id:
            referido = padrino["tg_id"]

    usuario = db.crear_si_falta(mensaje.from_user.id, mensaje.from_user.username, referido)
    idi = usuario["idioma"] or "es"

    await mensaje.answer(
        t(idi, "bienvenida", marca=config.MARCA, dias=config.DIAS_PRUEBA),
        reply_markup=menu_principal(mensaje.from_user.id),
        parse_mode=ParseMode.HTML,
    )

    if referido:
        await mensaje.answer(t(idi, "invitar_bienvenida"))


@router.message(Command("menu"))
async def comando_menu(mensaje: Message):
    idi = idioma(mensaje.from_user.id)
    await mensaje.answer(
        t(idi, "bienvenida", marca=config.MARCA, dias=config.DIAS_PRUEBA),
        reply_markup=menu_principal(mensaje.from_user.id),
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("promo"))
async def comando_promo(mensaje: Message, comando: CommandObject):
    """Solo administrador: /promo CODIGO DIAS USOS"""
    if mensaje.from_user.id != ADMIN:
        return
    partes = (comando.args or "").split()
    if len(partes) != 3:
        await mensaje.answer("Uso: /promo CODIGO DIAS USOS")
        return
    codigo, dias, usos = partes[0], int(partes[1]), int(partes[2])
    db.crear_promo(codigo, dias, usos)
    await mensaje.answer(f"Código {codigo.upper()}: {dias} días, {usos} usos.")


@router.message(Command("regalar"))
async def comando_regalar(mensaje: Message, comando: CommandObject):
    if mensaje.from_user.id != ADMIN:
        return
    partes = (comando.args or "").split()
    if len(partes) != 2:
        await mensaje.answer("Uso: /regalar ID DÍAS")
        return
    tg_id, dias = int(partes[0]), int(partes[1])
    db.crear_si_falta(tg_id, None)
    usuario = activar(tg_id, dias)
    await mensaje.answer(f"Activado para {tg_id} hasta {fecha(usuario['expira'])}.")


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
        f"Precios: {config.PRECIOS}",
        f"Avisos: {', '.join(avisos) if avisos else 'ninguno'}",
    ]
    await mensaje.answer("\n".join(texto))


# --------------------------------------------------------------------------- #
# Botones
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == "menu")
async def volver_menu(llamada: CallbackQuery):
    idi = idioma(llamada.from_user.id)
    await llamada.message.edit_text(
        t(idi, "bienvenida", marca=config.MARCA, dias=config.DIAS_PRUEBA),
        reply_markup=menu_principal(llamada.from_user.id),
        parse_mode=ParseMode.HTML,
    )
    await llamada.answer()


@router.callback_query(F.data == "prueba")
async def boton_prueba(llamada: CallbackQuery, bot: Bot):
    tg_id = llamada.from_user.id
    usuario = db.obtener(tg_id) or {}
    idi = usuario.get("idioma") or "es"
    ahora = int(time.time())

    if usuario.get("expira", 0) > ahora:
        await llamada.message.edit_text(
            t(idi, "prueba_cabecera", fecha=fecha(usuario["expira"])),
            reply_markup=teclado_volver(tg_id),
        )
        await llamada.answer()
        return

    if usuario.get("prueba_usada"):
        await llamada.message.edit_text(
            t(idi, "prueba_ya_usada"),
            reply_markup=teclado_volver(tg_id),
        )
        await llamada.answer()
        return

    try:
        actualizado = activar(tg_id, config.DIAS_PRUEBA)
        db.guardar(tg_id, prueba_usada=1)
    except Exception as e:  # noqa: BLE001
        log.exception("fallo creando la prueba")
        await llamada.answer(t(idi, "error_generico"), show_alert=True)
        return

    texto = t(
        idi, "prueba_lista",
        dias=config.DIAS_PRUEBA,
        pais=t(idi, "pais"),
        ip=actualizado["ip"],
        fecha=fecha(actualizado["expira"]),
    )
    await llamada.message.edit_text(texto, reply_markup=teclado_volver(tg_id),
                                    parse_mode=ParseMode.HTML)
    await enviar_conf(bot, tg_id, actualizado, t(idi, "pais"))
    await llamada.answer()


@router.callback_query(F.data == "comprar")
async def boton_comprar(llamada: CallbackQuery):
    idi = idioma(llamada.from_user.id)
    await llamada.message.edit_text(
        t(idi, "comprar_titulo"),
        reply_markup=teclado_planes(llamada.from_user.id),
        parse_mode=ParseMode.HTML,
    )
    await llamada.answer()


@router.callback_query(F.data.startswith("plan:"))
async def boton_plan(llamada: CallbackQuery, bot: Bot):
    meses = int(llamada.data.split(":")[1])
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

    db.registrar_pago(
        tg_id, meses, pago.total_amount, pago.telegram_payment_charge_id or ""
    )

    # Bonus por invitar: el padrino gana días.
    usuario = db.obtener(tg_id) or {}
    padrino = usuario.get("referido")
    if padrino:
        try:
            activar(padrino, config.DIAS_INVITADO)
            await bot.send_message(
                padrino,
                t(idioma(padrino), "invitar_bienvenida"),
            )
        except Exception:  # noqa: BLE001
            log.warning("no se pudo premiar al padrino %s", padrino)

    await mensaje.answer(
        t(idi, "pago_ok", fecha=fecha(actualizado["expira"])),
        parse_mode=ParseMode.HTML,
    )
    await enviar_conf(bot, tg_id, actualizado, f"{config.MARCA} · {meses} m")


@router.callback_query(F.data == "mi_vpn")
async def boton_mi_vpn(llamada: CallbackQuery):
    tg_id = llamada.from_user.id
    usuario = db.obtener(tg_id) or {}
    idi = usuario.get("idioma") or "es"
    ahora = int(time.time())

    if not usuario.get("ip") or usuario.get("expira", 0) <= ahora:
        texto = t(idi, "mi_vpn_sin") if not usuario.get("ip") else t(idi, "caducado")
        await llamada.message.edit_text(texto, reply_markup=teclado_volver(tg_id))
        await llamada.answer()
        return

    texto = t(
        idi, "mi_vpn_activo",
        pais=t(idi, "pais"),
        ip=usuario["ip"],
        fecha=fecha(usuario["expira"]),
        dias=dias_restantes(usuario["expira"]),
        enlace="",
    )
    teclado = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(idi, "boton_reenviar"), callback_data="reenviar")],
        [InlineKeyboardButton(text="◀️", callback_data="menu")],
    ])
    await llamada.message.edit_text(texto, reply_markup=teclado,
                                    parse_mode=ParseMode.HTML)
    await llamada.answer()


@router.callback_query(F.data == "reenviar")
async def boton_reenviar(llamada: CallbackQuery, bot: Bot):
    tg_id = llamada.from_user.id
    usuario = db.obtener(tg_id) or {}
    idi = usuario.get("idioma") or "es"
    if not usuario.get("ip"):
        await llamada.answer(t(idi, "mi_vpn_sin"), show_alert=True)
        return
    await enviar_conf(bot, tg_id, usuario, t(idi, "reenvio"))
    await llamada.answer()


@router.callback_query(F.data == "pais")
async def boton_pais(llamada: CallbackQuery):
    idi = idioma(llamada.from_user.id)
    await llamada.message.edit_text(
        t(idi, "pais_unico"), reply_markup=teclado_volver(llamada.from_user.id)
    )
    await llamada.answer()


@router.callback_query(F.data == "invitar")
async def boton_invitar(llamada: CallbackQuery, bot: Bot):
    tg_id = llamada.from_user.id
    usuario = db.obtener(tg_id) or {}
    idi = usuario.get("idioma") or "es"
    me = await bot.get_me()
    enlace = f"https://t.me/{me.username}?start={usuario.get('codigo_ref') or 'r'}"
    with db.conectar() as con:
        cuantos = con.execute(
            "SELECT COUNT(*) c FROM usuarios WHERE referido = ?", (tg_id,)
        ).fetchone()["c"]
    await llamada.message.edit_text(
        t(idi, "invitar_texto", dias=config.DIAS_INVITADO, enlace=enlace, cuantos=cuantos),
        reply_markup=teclado_volver(tg_id),
        parse_mode=ParseMode.HTML,
    )
    await llamada.answer()


@router.callback_query(F.data == "promo")
async def boton_promo(llamada: CallbackQuery):
    idi = idioma(llamada.from_user.id)
    await llamada.message.edit_text(
        t(idi, "promo_pedir"), reply_markup=teclado_volver(llamada.from_user.id)
    )
    await llamada.answer()


@router.callback_query(F.data == "ayuda")
async def boton_ayuda(llamada: CallbackQuery):
    idi = idioma(llamada.from_user.id)
    await llamada.message.edit_text(
        t(idi, "ayuda", android=config.URL_ANDROID, windows=config.URL_WINDOWS),
        reply_markup=teclado_volver(llamada.from_user.id),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    await llamada.answer()


@router.callback_query(F.data == "idioma")
async def boton_idioma(llamada: CallbackQuery):
    filas = [
        [InlineKeyboardButton(text=n, callback_data=f"idi:{c}")]
        for c, n in IDIOMAS.items()
    ]
    filas.append([InlineKeyboardButton(text="◀️", callback_data="menu")])
    await llamada.message.edit_text(
        t(idioma(llamada.from_user.id), "idioma_pedir"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=filas),
    )
    await llamada.answer()


@router.callback_query(F.data.startswith("idi:"))
async def elegir_idioma(llamada: CallbackQuery):
    idi = llamada.data.split(":")[1]
    db.guardar(llamada.from_user.id, idioma=idi)
    await llamada.message.edit_text(
        t(idi, "idioma_ok"), reply_markup=teclado_volver(llamada.from_user.id)
    )
    await llamada.answer()


@router.message(F.text)
async def texto_libre(mensaje: Message, bot: Bot):
    """Un texto suelto puede ser un código promocional."""
    tg_id = mensaje.from_user.id
    idi = idioma(tg_id)
    dias = db.usar_promo(mensaje.text or "")
    if dias is None:
        await mensaje.answer(t(idi, "promo_mal"))
        return
    try:
        actualizado = activar(tg_id, dias)
    except Exception:  # noqa: BLE001
        log.exception("fallo canjeando promo")
        await mensaje.answer(t(idi, "error_generico"))
        return
    await mensaje.answer(
        t(idi, "promo_ok", dias=dias), parse_mode=ParseMode.HTML
    )
    await enviar_conf(bot, tg_id, actualizado, t(idi, "pais"))


# --------------------------------------------------------------------------- #
# Caducidad
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
    log.info("bot en marcha · servidor %s", config.ENDPOINT)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
