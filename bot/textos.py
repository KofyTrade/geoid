"""Textos del bot en español, ruso e inglés."""

TEXTOS = {
    "es": {
        "bienvenida": (
            "¡Hola! Esto es <b>{marca}</b>, una VPN con protocolo "
            "<b>AmneziaWG v3</b> (WireGuard ofuscado, no se puede bloquear "
            "por firma de tráfico).\n\n"
            "🎁 Tienes <b>{dias} días gratis</b> para probarla, sin tarjeta.\n\n"
            "Aquí mismo recibirás tu configuración. Para usarla necesitas la "
            "aplicación <b>GeoiD-vpn</b>; los enlaces están en ❓ Ayuda.\n\n"
            "Elige una opción 👇"
        ),
        "menu_prueba": "🎁 Prueba gratis",
        "menu_comprar": "💎 Comprar VPN",
        "menu_mi_vpn": "📱 Mi VPN",
        "menu_pais": "🌍 Cambiar país",
        "menu_invitar": "👥 Invitar amigo",
        "menu_promo": "🎟 Canjear código",
        "menu_ayuda": "❓ Ayuda",
        "menu_idioma": "🌐 Idioma",
        "prueba_ya_usada": (
            "Ya has usado tu prueba gratuita.\n\n"
            "Puedes comprar acceso con 💎 Comprar VPN."
        ),
        "prueba_lista": (
            "✅ <b>Tu prueba de {dias} días está lista</b>\n\n"
            "Servidor: <b>{pais}</b>\n"
            "Dirección: <code>{ip}</code>\n"
            "Caduca: <b>{fecha}</b>\n\n"
            "Te adjunto la configuración. Ábrela con la app y pulsa Conectar."
        ),
        "prueba_cabecera": "⚠️ Ya tienes un acceso activo hasta {fecha}.",
        "mi_vpn_sin": (
            "No tienes ningún acceso activo.\n\n"
            "Puedes empezar con 🎁 Prueba gratis."
        ),
        "mi_vpn_activo": (
            "📱 <b>Tu acceso</b>\n\n"
            "Servidor: <b>{pais}</b>\n"
            "Dirección: <code>{ip}</code>\n"
            "Estado: <b>activo</b>\n"
            "Caduca: <b>{fecha}</b> ({dias} días)\n\n"
            "{enlace}\n\n"
            "Si quieres, te reenvío el fichero de configuración."
        ),
        "boton_reenviar": "📄 Reenviar configuración",
        "reenvio": "Aquí tienes tu configuración de nuevo.",
        "comprar_titulo": "💎 <b>Elige el plan</b>\n\nEl pago se hace con estrellas de Telegram.",
        "plan_mes": "1 mes",
        "plan_3meses": "3 meses",
        "plan_anio": "1 año",
        "plan_boton": "{meses} · {estrellas} ⭐",
        "pago_ok": (
            "✅ <b>¡Pago recibido!</b>\n\n"
            "Tu acceso está activo hasta <b>{fecha}</b>.\n"
            "Te adjunto la configuración actualizada."
        ),
        "pais_unico": (
            "Ahora mismo solo hay un servidor disponible: <b>Finlandia</b> "
            "(Helsinki).\n\n"
            "Es la ruta más rápida hacia Rusia. Cuando añadamos más países "
            "aparecerán aquí."
        ),
        "invitar_texto": (
            "👥 <b>Invita y gana días</b>\n\n"
            "Por cada amigo que compre, te regalamos <b>{dias} días</b>.\n\n"
            "Tu enlace:\n<code>{enlace}</code>\n\n"
            "Invitados hasta ahora: <b>{cuantos}</b>"
        ),
        "invitar_bienvenida": "🎉 Has llegado con una invitación. ¡Disfruta!",
        "promo_pedir": "Escribe el código promocional:",
        "promo_ok": "✅ Código canjeado: <b>{dias} días</b> añadidos.",
        "promo_mal": "❌ Ese código no es válido o ya no tiene usos.",
        "ayuda": (
            "❓ <b>Cómo usarla</b>\n\n"
            "1. Instala la app:\n"
            "• Android: {android}\n"
            "• Windows: {windows}\n\n"
            "2. Descarga tu configuración desde 📱 Mi VPN.\n"
            "3. En la app: <b>Perfiles → + → Importar .conf</b>.\n"
            "4. Pulsa <b>Conectar</b> y listo.\n\n"
            "Si algo no funciona, escríbenos aquí mismo."
        ),
        "idioma_pedir": "Elige tu idioma:",
        "idioma_ok": "Idioma cambiado.",
        "caducado": (
            "⏳ Tu acceso ha caducado.\n\n"
            "Renueva con 💎 Comprar VPN y seguirás con la misma configuración."
        ),
        "error_generico": "Ha habido un problema. Inténtalo de nuevo en un minuto.",
        "sin_pagos": (
            "Los pagos con estrellas aún no están activados en este bot.\n"
            "Pide acceso manual al administrador."
        ),
        "metodo_titulo": "¿Cómo quieres pagar?",
        "metodo_stars": "⭐ Estrellas de Telegram",
        "metodo_crypto": "🪙 Cripto (USDT / TON)",
        "metodo_manual": "📱 Pago por QR",
        "cripto_texto": (
            "🪙 <b>Factura creada</b>\n\n"
            "Importe: <b>{monto} USDT</b>\n"
            "Paga aquí: {url}\n\n"
            "Se activa sola en cuanto se confirme el pago (1-2 minutos)."
        ),
        "cripto_no": "El pago con cripto no está disponible ahora mismo. Usa estrellas o transferencia.",
        "manual_texto": (
            "📱 <b>Pago por QR</b>\n\n"
            "Importe: <b>{importe} ₽</b>\n"
            "Teléfono: <code>{telefono}</code>{titular}\n\n"
            "1. Abre tu banco y elige transferir por <b>SBP</b>.\n"
            "2. Envía <b>{importe} ₽</b> al número de arriba.\n"
            "3. Vuelve aquí y pulsa <b>«Ya he pagado»</b>.\n\n"
            "Tu acceso se activa en minutos (lo revisamos a mano).\n\n"
            "Tu ID de Telegram: <code>{id}</code>"
        ),
        "manual_boton": "✅ Ya he pagado",
        "manual_aviso": "✅ Aviso enviado. En cuanto confirmemos el pago recibirás tu configuración aquí mismo.",
        "manual_admin": (
            "💳 <b>Pago pendiente</b>\n\n"
            "Usuario: {usuario} (ID <code>{id}</code>)\n"
            "Plan: <b>{meses} mes(es)</b> · {importe} ₽\n\n"
            "Pulsa el botón cuando veas el ingreso:"
        ),
        "activar_ok": "Activado {id} hasta {fecha}.",        "pais": "Finlandia",
    },
    "ru": {
        "bienvenida": (
            "Привет! Это <b>{marca}</b> — VPN на протоколе <b>AmneziaWG v3</b> "
            "(обфусцированный WireGuard, его не блокируют по отпечатку "
            "трафика).\n\n"
            "🎁 Доступно <b>{dias} дня бесплатно</b>, без карты.\n\n"
            "Конфигурация придёт сюда же. Для подключения нужно приложение "
            "<b>GeoiD-vpn</b>, ссылки в ❓ Помощь.\n\n"
            "Выберите действие 👇"
        ),
        "menu_prueba": "🎁 Бесплатный доступ",
        "menu_comprar": "💎 Купить VPN",
        "menu_mi_vpn": "📱 Мой VPN",
        "menu_pais": "🌍 Сменить страну",
        "menu_invitar": "👥 Пригласить друга",
        "menu_promo": "🎟 Промокод",
        "menu_ayuda": "❓ Помощь",
        "menu_idioma": "🌐 Язык",
        "prueba_ya_usada": (
            "Вы уже использовали бесплатный доступ.\n\n"
            "Можно купить: 💎 Купить VPN."
        ),
        "prueba_lista": (
            "✅ <b>Пробный доступ на {dias} дня готов</b>\n\n"
            "Сервер: <b>{pais}</b>\n"
            "Адрес: <code>{ip}</code>\n"
            "Действует до: <b>{fecha}</b>\n\n"
            "Конфигурация во вложении. Откройте её в приложении и нажмите "
            "«Подключить»."
        ),
        "prueba_cabecera": "⚠️ У вас уже есть доступ до {fecha}.",
        "mi_vpn_sin": "Активного доступа нет.\n\nНачните с 🎁 Бесплатный доступ.",
        "mi_vpn_activo": (
            "📱 <b>Ваш доступ</b>\n\n"
            "Сервер: <b>{pais}</b>\n"
            "Адрес: <code>{ip}</code>\n"
            "Статус: <b>активен</b>\n"
            "Действует до: <b>{fecha}</b> ({dias} дн.)\n\n"
            "{enlace}\n\n"
            "Могу отправить файл конфигурации заново."
        ),
        "boton_reenviar": "📄 Отправить конфигурацию",
        "reenvio": "Вот ваша конфигурация.",
        "comprar_titulo": "💎 <b>Выберите тариф</b>\n\nОплата звёздами Telegram.",
        "plan_mes": "1 месяц",
        "plan_3meses": "3 месяца",
        "plan_anio": "1 год",
        "plan_boton": "{meses} · {estrellas} ⭐",
        "pago_ok": (
            "✅ <b>Оплата получена!</b>\n\n"
            "Доступ активен до <b>{fecha}</b>.\n"
            "Конфигурация во вложении."
        ),
        "pais_unico": (
            "Пока доступен один сервер: <b>Финляндия</b> (Хельсинки).\n\n"
            "Это самый быстрый маршрут в Россию. Другие страны появятся "
            "здесь же."
        ),
        "invitar_texto": (
            "👥 <b>Приглашайте и получайте дни</b>\n\n"
            "За каждого друга, который купит, дарим <b>{dias} дней</b>.\n\n"
            "Ваша ссылка:\n<code>{enlace}</code>\n\n"
            "Приглашено: <b>{cuantos}</b>"
        ),
        "invitar_bienvenida": "🎉 Вы пришли по приглашению. Пользуйтесь!",
        "promo_pedir": "Введите промокод:",
        "promo_ok": "✅ Промокод принят: добавлено <b>{dias} дней</b>.",
        "promo_mal": "❌ Код недействителен или уже использован.",
        "ayuda": (
            "❓ <b>Как подключиться</b>\n\n"
            "1. Установите приложение:\n"
            "• Android: {android}\n"
            "• Windows: {windows}\n\n"
            "2. Скачайте конфигурацию в 📱 Мой VPN.\n"
            "3. В приложении: <b>Профили → + → импорт .conf</b>.\n"
            "4. Нажмите <b>Подключить</b>.\n\n"
            "Если что-то не работает — напишите здесь."
        ),
        "idioma_pedir": "Выберите язык:",
        "idioma_ok": "Язык изменён.",
        "caducado": (
            "⏳ Доступ истёк.\n\n"
            "Продлите через 💎 Купить VPN — конфигурация останется той же."
        ),
        "error_generico": "Что-то пошло не так. Повторите через минуту.",
        "sin_pagos": (
            "Оплата звёздами ещё не включена в этом боте.\n"
            "Напишите администратору."
        ),
        "metodo_titulo": "Как оплатить?",
        "metodo_stars": "⭐ Звёзды Telegram",
        "metodo_crypto": "🪙 Криптовалюта (USDT / TON)",
        "metodo_manual": "📱 Оплата по QR",
        "cripto_texto": (
            "🪙 <b>Счёт создан</b>\n\n"
            "Сумма: <b>{monto} USDT</b>\n"
            "Оплатить: {url}\n\n"
            "Доступ включится автоматически после подтверждения (1-2 минуты)."
        ),
        "cripto_no": "Оплата криптой сейчас недоступна. Используйте звёзды или перевод.",
        "manual_texto": (
            "📱 <b>Оплата по QR</b>\n\n"
            "Сумма: <b>{importe} ₽</b>\n"
            "Телефон: <code>{telefono}</code>{titular}\n\n"
            "1. Откройте банк и выберите перевод по <b>СБП</b>.\n"
            "2. Отправьте <b>{importe} ₽</b> на номер выше.\n"
            "3. Вернитесь сюда и нажмите <b>«Я оплатил»</b>.\n\n"
            "Доступ включим в течение нескольких минут.\n\n"
            "Ваш ID в Telegram: <code>{id}</code>"
        ),
        "manual_boton": "✅ Я оплатил",
        "manual_aviso": "✅ Заявка отправлена. Как только подтвердим оплату, конфигурация придёт сюда.",
        "manual_admin": (
            "💳 <b>Ожидает оплаты</b>\n\n"
            "Пользователь: {usuario} (ID <code>{id}</code>)\n"
            "Тариф: <b>{meses} мес.</b> · {importe} ₽\n\n"
            "Нажмите кнопку, когда увидите поступление:"
        ),
        "activar_ok": "Активирован {id} до {fecha}.",        "pais": "Финляндия",
    },
    "en": {
        "bienvenida": (
            "Hi! This is <b>{marca}</b>, a VPN running <b>AmneziaWG v3</b> "
            "(obfuscated WireGuard, it can't be blocked by traffic "
            "fingerprinting).\n\n"
            "🎁 Try it <b>free for {dias} days</b>, no card needed.\n\n"
            "Your configuration is delivered right here. You need the "
            "<b>GeoiD-vpn</b> app; links are under ❓ Help.\n\n"
            "Pick an option 👇"
        ),
        "menu_prueba": "🎁 Free trial",
        "menu_comprar": "💎 Buy VPN",
        "menu_mi_vpn": "📱 My VPN",
        "menu_pais": "🌍 Change country",
        "menu_invitar": "👥 Invite a friend",
        "menu_promo": "🎟 Redeem promo code",
        "menu_ayuda": "❓ Help",
        "menu_idioma": "🌐 Language",
        "prueba_ya_usada": "You already used your free trial.\n\nBuy access: 💎 Buy VPN.",
        "prueba_lista": (
            "✅ <b>Your {dias}-day trial is ready</b>\n\n"
            "Server: <b>{pais}</b>\n"
            "Address: <code>{ip}</code>\n"
            "Expires: <b>{fecha}</b>\n\n"
            "The configuration is attached. Open it in the app and tap Connect."
        ),
        "prueba_cabecera": "⚠️ You already have access until {fecha}.",
        "mi_vpn_sin": "No active access.\n\nStart with 🎁 Free trial.",
        "mi_vpn_activo": (
            "📱 <b>Your access</b>\n\n"
            "Server: <b>{pais}</b>\n"
            "Address: <code>{ip}</code>\n"
            "Status: <b>active</b>\n"
            "Expires: <b>{fecha}</b> ({dias} days)\n\n"
            "{enlace}\n\n"
            "I can send the configuration file again."
        ),
        "boton_reenviar": "📄 Resend configuration",
        "reenvio": "Here is your configuration again.",
        "comprar_titulo": "💎 <b>Choose a plan</b>\n\nPayment in Telegram stars.",
        "plan_mes": "1 month",
        "plan_3meses": "3 months",
        "plan_anio": "1 year",
        "plan_boton": "{meses} · {estrellas} ⭐",
        "pago_ok": (
            "✅ <b>Payment received!</b>\n\n"
            "Access is active until <b>{fecha}</b>.\n"
            "Configuration attached."
        ),
        "pais_unico": (
            "Only one server for now: <b>Finland</b> (Helsinki).\n\n"
            "It's the fastest route to Russia. More countries will appear here."
        ),
        "invitar_texto": (
            "👥 <b>Invite and earn days</b>\n\n"
            "For every friend who buys, you get <b>{dias} days</b>.\n\n"
            "Your link:\n<code>{enlace}</code>\n\nInvited so far: <b>{cuantos}</b>"
        ),
        "invitar_bienvenida": "🎉 You arrived through an invitation. Enjoy!",
        "promo_pedir": "Type the promo code:",
        "promo_ok": "✅ Code redeemed: <b>{dias} days</b> added.",
        "promo_mal": "❌ That code is invalid or used up.",
        "ayuda": (
            "❓ <b>How to connect</b>\n\n"
            "1. Install the app:\n"
            "• Android: {android}\n"
            "• Windows: {windows}\n\n"
            "2. Download your configuration in 📱 My VPN.\n"
            "3. In the app: <b>Profiles → + → import .conf</b>.\n"
            "4. Tap <b>Connect</b>.\n\n"
            "If something fails, write to us here."
        ),
        "idioma_pedir": "Choose your language:",
        "idioma_ok": "Language changed.",
        "caducado": (
            "⏳ Your access expired.\n\n"
            "Renew with 💎 Buy VPN and keep the same configuration."
        ),
        "error_generico": "Something went wrong. Try again in a minute.",
        "sin_pagos": "Star payments are not enabled in this bot yet.",
        "metodo_titulo": "How do you want to pay?",
        "metodo_stars": "⭐ Telegram stars",
        "metodo_crypto": "🪙 Crypto (USDT / TON)",
        "metodo_manual": "📱 Pay by QR",
        "cripto_texto": (
            "🪙 <b>Invoice created</b>\n\n"
            "Amount: <b>{monto} USDT</b>\n"
            "Pay here: {url}\n\n"
            "It activates by itself once the payment confirms (1-2 minutes)."
        ),
        "cripto_no": "Crypto payment is unavailable right now. Use stars or a transfer.",
        "manual_texto": (
            "📱 <b>Pay by QR</b>\n\n"
            "Amount: <b>{importe} ₽</b>\n"
            "Phone: <code>{telefono}</code>{titular}\n\n"
            "1. Open your bank and choose an <b>SBP</b> transfer.\n"
            "2. Send <b>{importe} ₽</b> to the number above.\n"
            "3. Come back and press <b>\"I have paid\"</b>.\n\n"
            "Your access activates within minutes (checked by hand).\n\n"
            "Your Telegram ID: <code>{id}</code>"
        ),
        "manual_boton": "✅ I have paid",
        "manual_aviso": "✅ Sent. As soon as we confirm the payment your configuration arrives here.",
        "manual_admin": (
            "💳 <b>Payment pending</b>\n\n"
            "User: {usuario} (ID <code>{id}</code>)\n"
            "Plan: <b>{meses} month(s)</b> · {importe} ₽\n\n"
            "Press the button once you see the transfer:"
        ),
        "activar_ok": "Activated {id} until {fecha}.",        "pais": "Finland",
    },
}

IDIOMAS = {"es": "🇪🇸 Español", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}


def t(idioma: str, clave: str, **datos) -> str:
    tabla = TEXTOS.get(idioma) or TEXTOS["es"]
    texto = tabla.get(clave) or TEXTOS["es"].get(clave) or clave
    try:
        return texto.format(**datos)
    except (KeyError, IndexError):
        return texto
