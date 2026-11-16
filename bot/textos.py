"""Textos del bot en español, ruso e inglés."""

TEXTOS = {
    "es": {
        "soporte_invita": "Si necesitas ayuda, escribe tu mensaje aquí abajo y te responderemos en este mismo chat.",
        "soporte_recibido": "Mensaje recibido. Te contestamos aquí en cuanto podamos.",
        "soporte_ticket": "\U0001F3AB Ticket de soporte\n\nDe: {usuario} (ID {id})\n\n{mensaje}\n\nResponde a este mensaje para contestarle.",
        "soporte_respuesta": "Respuesta del equipo:\n\n{mensaje}",
        "soporte_enviado": "Enviado al cliente.",
        "instalar_conf": "\U0001F4F2 Toca el archivo de arriba y elige \u00abAbrir con GeoiD-vpn\u00bb. La app a\u00f1ade el perfil y lo activa sola; despu\u00e9s solo pulsa Conectar.\n\nSi no aparece la app: guarda el archivo (Descargar), abre Descargas y \u00e1brelo desde ah\u00ed.",
        "factura_desc": (
            "Acceso completo a {marca} durante {duracion}.\n"
            "Se activa al instante y caduca el {fecha}."
        ),
        "plan_linea": "💳 Plan: <b>{duracion}</b>",
        "manual_plan": "Plan: <b>{duracion}</b>",
        "plan_6meses": "Acceso 6 meses + proxy de Telegram de regalo",
        "proxy_boton": "🎁 Mi proxy de Telegram",
        "proxy_sin": "El proxy de regalo es para planes de 6 meses o más.",
                "proxy_regalo": (
            "🎁 <b>Tu regalo: proxy de Telegram</b>\n\n"
            "Con tu plan de 6 meses o más te llevas un proxy de Telegram "
            "<b>gratis y exclusivo para ti</b>. Sirve para usar Telegram en "
            "Rusia <b>sin VPN encendida</b>.\n\n"
            "Toca este enlace desde el móvil y Telegram se configura solo:\n"
            "<code>{enlace}</code>\n\n"
            "O a mano, en Telegram → Ajustes → Datos y almacenamiento → Proxy:\n"
            "Servidor: <code>{servidor}</code>\n"
            "Puerto: <code>{puerto}</code>\n"
            "Clave: <code>{secreto}</code>\n\n"
            "⚠️ <b>Este enlace es personal.</b> Puedes compartirlo si quieres, "
            "pero si lo usa mucha gente irá más lento e incluso podría dejar de "
            "funcionar bien: en ese caso <b>no nos hacemos responsables</b> del "
            "rendimiento del proxy. La conexión VPN sí mantiene su garantía."
        ),
                "bienvenida": (
            "¡Hola! Esto es <b>{marca}</b>, una VPN con <b>WireGuard ofuscado</b>: "
            "no se puede bloquear por firma de tráfico.\n\n"
            "🎁 Tienes <b>{dias} días gratis</b> para probarla, sin tarjeta.\n\n"
            "📱 Además: con la compra de <b>6 meses o más</b> te llevas <b>gratis</b> "
            "el proxy de Telegram, para usarlo en Rusia sin VPN.\n\n"
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
        "boton_reenviar": "📄 Mi configuración (.conf)",
        "reenvio": "Aquí tienes tu configuración de nuevo.",
        "comprar_titulo": "💎 <b>Elige el plan</b>\n\nSe paga por QR ruso, cripto o estrellas.",
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
            "Solo cuentan los amigos que <b>compren</b> (la prueba gratis de 3 "
            "días no cuenta):\n\n"
            "· 3 amigos → <b>7 días</b> gratis\n"
            "· 10 amigos → <b>15 días</b> gratis\n"
            "· 20 amigos → <b>1 mes</b> gratis\n\n"
            "Los días se suman a los que ya tengas.\n\n"
            "Tu enlace:\n{enlace}\n\n"
            "Amigos que ya han comprado: <b>{cuantos}</b>"
        ),
        "invitar_siguiente": "Te faltan <b>{faltan}</b> para el siguiente premio ({premio}).",
        "invitar_maximo": "¡Ya tienes el premio máximo! 🎉",
        "premio_invitacion": (
            "🎉 <b>¡Premio por invitar!</b>\n\n"
            "Amigos que han comprado: <b>{cuantos}</b>\n"
            "Has ganado: <b>{dias} días</b>\n\n"
            "Tu acceso ahora vence el {fecha}."
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
            "Plan: <b>{duracion}</b>\n\n"
            "1. Abre la app de tu banco y elige <b>«Escanear QR»</b>.\n"
            "2. Escanea el código y confirma <b>{importe} ₽</b>.\n"
            "3. Vuelve aquí y pulsa <b>«Ya he pagado»</b>.\n\n"
            "Tu acceso se activa en minutos.\n\n"
            "Tu ID de Telegram: <code>{id}</code>"
        ),
        "manual_boton": "✅ Ya he pagado",
        "manual_aviso": "✅ Aviso enviado. En cuanto confirmemos el pago recibirás tu configuración aquí mismo.",
        "manual_admin": (
            "💰 <b>PAGO {importe} ₽ · {meses} mes(es)</b>\n\n"
            "Usuario: {usuario} (ID <code>{id}</code>)\n\n"
            "Pulsa el botón cuando veas el ingreso en el banco:"
        ),
        "activar_ok": "Activado {id} hasta {fecha}.",        "pais": "Finlandia",
    },
    "ru": {
        "soporte_invita": "Если нужна помощь, напишите сообщение здесь — ответим в этом же чате.",
        "soporte_recibido": "Сообщение получено. Ответим здесь, как только сможем.",
        "soporte_ticket": "\U0001F3AB Сообщение в поддержку\n\nОт: {usuario} (ID {id})\n\n{mensaje}\n\nОтветьте на это сообщение, чтобы написать клиенту.",
        "soporte_respuesta": "Ответ поддержки:\n\n{mensaje}",
        "soporte_enviado": "Отправлено клиенту.",
        "instalar_conf": "\U0001F4F2 \u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u043d\u0430 \u0444\u0430\u0439\u043b \u0432\u044b\u0448\u0435 \u0438 \u0432\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u00ab\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u0432 GeoiD-vpn\u00bb. \u041f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0435 \u0434\u043e\u0431\u0430\u0432\u0438\u0442 \u043f\u0440\u043e\u0444\u0438\u043b\u044c \u0441\u0430\u043c\u043e.\n\n\u0415\u0441\u043b\u0438 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f \u043d\u0435\u0442 \u0432 \u0441\u043f\u0438\u0441\u043a\u0435: \u0441\u043a\u0430\u0447\u0430\u0439\u0442\u0435 \u0444\u0430\u0439\u043b \u0438 \u043e\u0442\u043a\u0440\u043e\u0439\u0442\u0435 \u0435\u0433\u043e \u0438\u0437 \u043f\u0430\u043f\u043a\u0438 \u00ab\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0438\u00bb.",
        "factura_desc": (
            "Полный доступ к {marca} на {duracion}.\n"
            "Активируется сразу, действует до {fecha}."
        ),
        "plan_linea": "💳 Тариф: <b>{duracion}</b>",
        "manual_plan": "Тариф: <b>{duracion}</b>",
        "plan_6meses": "Доступ на 6 месяцев + прокси Telegram в подарок",
        "proxy_boton": "🎁 Мой прокси Telegram",
        "proxy_sin": "Прокси в подарок — для тарифов от 6 месяцев.",
                "proxy_regalo": (
            "🎁 <b>Ваш подарок: прокси Telegram</b>\n\n"
            "С тарифом от 6 месяцев вы получаете прокси Telegram "
            "<b>бесплатно и только для вас</b>. Он нужен, чтобы пользоваться "
            "Telegram в России <b>без VPN</b>.\n\n"
            "Нажмите ссылку на телефоне — Telegram настроится сам:\n"
            "<code>{enlace}</code>\n\n"
            "Или вручную: Telegram → Настройки → Данные и память → Прокси:\n"
            "Сервер: <code>{servidor}</code>\n"
            "Порт: <code>{puerto}</code>\n"
            "Секрет: <code>{secreto}</code>\n\n"
            "⚠️ <b>Эта ссылка персональная.</b> Вы можете ею делиться, но если "
            "ею будет пользоваться много людей, она станет медленнее и может "
            "работать хуже: в этом случае <b>мы не отвечаем</b> за скорость "
            "прокси. На VPN это не влияет — его гарантия сохраняется."
        ),
                "bienvenida": (
            "Привет! Это <b>{marca}</b>, VPN на <b>WireGuard с обфускацией</b>: "
            "его нельзя заблокировать по сигнатуре трафика.\n\n"
            "🎁 У вас <b>{dias} дней бесплатно</b>, без карты.\n\n"
            "📱 При покупке на <b>6 месяцев или больше</b> — прокси Telegram "
            "<b>в подарок</b>, чтобы пользоваться Telegram в РФ без VPN.\n\n"
            "Конфигурация придёт сюда же. Для подключения нужно приложение "
            "<b>GeoiD-vpn</b>; ссылки в разделе ❓ Помощь.\n\n"
            "Выберите вариант 👇"
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
        "boton_reenviar": "📄 Моя конфигурация (.conf)",
        "reenvio": "Вот ваша конфигурация.",
        "comprar_titulo": "💎 <b>Выберите тариф</b>\n\nОплата по QR, криптой или звёздами.",
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
            "Считаются только друзья, которые <b>купили</b> (бесплатные 3 дня "
            "не считаются):\n\n"
            "· 3 друга → <b>7 дней</b> бесплатно\n"
            "· 10 друзей → <b>15 дней</b> бесплатно\n"
            "· 20 друзей → <b>1 месяц</b> бесплатно\n\n"
            "Дни прибавляются к вашим текущим.\n\n"
            "Ваша ссылка:\n{enlace}\n\n"
            "Друзей уже купили: <b>{cuantos}</b>"
        ),
        "invitar_siguiente": "Осталось <b>{faltan}</b> до следующей награды ({premio}).",
        "invitar_maximo": "Максимальная награда уже ваша! 🎉",
        "premio_invitacion": (
            "🎉 <b>Награда за приглашения!</b>\n\n"
            "Купивших друзей: <b>{cuantos}</b>\n"
            "Вы получили: <b>{dias} дней</b>\n\n"
            "Доступ теперь действует до {fecha}."
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
            "Тариф: <b>{duracion}</b>\n\n"
            "1. Откройте приложение банка и выберите <b>«Сканировать QR»</b>.\n"
            "2. Отсканируйте код и подтвердите <b>{importe} ₽</b>.\n"
            "3. Вернитесь сюда и нажмите <b>«Я оплатил»</b>.\n\n"
            "Доступ включим в течение нескольких минут.\n\n"
            "Ваш ID в Telegram: <code>{id}</code>"
        ),
        "manual_boton": "✅ Я оплатил",
        "manual_aviso": "✅ Заявка отправлена. Как только подтвердим оплату, конфигурация придёт сюда.",
        "manual_admin": (
            "💰 <b>ОПЛАТА {importe} ₽ · {meses} мес.</b>\n\n"
            "Пользователь: {usuario} (ID <code>{id}</code>)\n\n"
            "Нажмите кнопку, когда увидите поступление:"
        ),
        "activar_ok": "Активирован {id} до {fecha}.",        "pais": "Финляндия",
    },
    "en": {
        "soporte_invita": "If you need help, write your message below and we will reply in this same chat.",
        "soporte_recibido": "Message received. We will answer here as soon as we can.",
        "soporte_ticket": "\U0001F3AB Support ticket\n\nFrom: {usuario} (ID {id})\n\n{mensaje}\n\nReply to this message to answer.",
        "soporte_respuesta": "Reply from the team:\n\n{mensaje}",
        "soporte_enviado": "Sent to the customer.",
        "instalar_conf": "\U0001F4F2 Tap the file above and choose \u00abOpen with GeoiD-vpn\u00bb. The app adds the profile and activates it by itself.\n\nIf the app is not listed: download the file, open Downloads and open it from there.",
        "factura_desc": (
            "Full access to {marca} for {duracion}.\n"
            "Activates instantly and expires on {fecha}."
        ),
        "plan_linea": "💳 Plan: <b>{duracion}</b>",
        "manual_plan": "Plan: <b>{duracion}</b>",
        "plan_6meses": "6 months + free Telegram proxy",
        "proxy_boton": "🎁 My Telegram proxy",
        "proxy_sin": "The free proxy is for plans of 6 months or more.",
                "proxy_regalo": (
            "🎁 <b>Your gift: Telegram proxy</b>\n\n"
            "With a 6-month plan or longer you get a Telegram proxy "
            "<b>free and exclusive to you</b>. It lets you use Telegram in "
            "Russia <b>without a VPN</b>.\n\n"
            "Tap this link on your phone and Telegram sets it up:\n"
            "<code>{enlace}</code>\n\n"
            "Or manually: Telegram → Settings → Data and storage → Proxy:\n"
            "Server: <code>{servidor}</code>\n"
            "Port: <code>{puerto}</code>\n"
            "Secret: <code>{secreto}</code>\n\n"
            "⚠️ <b>This link is personal.</b> You may share it, but if many "
            "people use it, it will get slower and may stop working well: in "
            "that case <b>we are not responsible</b> for the proxy performance. "
            "The VPN connection keeps its guarantee."
        ),
                "bienvenida": (
            "Hi! This is <b>{marca}</b>, a VPN with <b>obfuscated WireGuard</b>: "
            "it cannot be blocked by traffic signature.\n\n"
            "🎁 You get <b>{dias} days free</b>, no card needed.\n\n"
            "📱 Plus: buy <b>6 months or more</b> and get the <b>Telegram proxy</b> "
            "free, to use Telegram in Russia without a VPN.\n\n"
            "Your configuration arrives right here. You need the "
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
        "boton_reenviar": "📄 My configuration (.conf)",
        "reenvio": "Here is your configuration again.",
        "comprar_titulo": "💎 <b>Choose a plan</b>\n\nPay by QR, crypto or stars.",
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
            "Only friends who <b>buy</b> count (the 3-day free trial does "
            "not):\n\n"
            "· 3 friends → <b>7 days</b> free\n"
            "· 10 friends → <b>15 days</b> free\n"
            "· 20 friends → <b>1 month</b> free\n\n"
            "Days are added to the ones you already have.\n\n"
            "Your link:\n{enlace}\n\n"
            "Friends who already bought: <b>{cuantos}</b>"
        ),
        "invitar_siguiente": "You need <b>{faltan}</b> more for the next reward ({premio}).",
        "invitar_maximo": "You already have the top reward! 🎉",
        "premio_invitacion": (
            "🎉 <b>Referral reward!</b>\n\n"
            "Friends who bought: <b>{cuantos}</b>\n"
            "You earned: <b>{dias} days</b>\n\n"
            "Your access now expires on {fecha}."
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
            "Plan: <b>{duracion}</b>\n\n"
            "1. Open your bank app and choose <b>Scan QR</b>.\n"
            "2. Scan the code and confirm <b>{importe} ₽</b>.\n"
            "3. Come back and press <b>\"I have paid\"</b>.\n\n"
            "Your access activates within minutes.\n\n"
            "Your Telegram ID: <code>{id}</code>"
        ),
        "manual_boton": "✅ I have paid",
        "manual_aviso": "✅ Sent. As soon as we confirm the payment your configuration arrives here.",
        "manual_admin": (
            "💰 <b>PAYMENT {importe} ₽ · {meses} month(s)</b>\n\n"
            "User: {usuario} (ID <code>{id}</code>)\n\n"
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
