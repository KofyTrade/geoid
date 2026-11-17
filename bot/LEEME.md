# Bot de venta — GeoiD VPN

Bot de Telegram que **vende y aprovisiona accesos** AmneziaWG: crea el peer en
el servidor, entrega el `.conf` al cliente y lo retira al caducar.

Copia el menú de DiveVPN: prueba gratis, comprar, mi VPN, cambiar país,
invitar, código promocional, ayuda e idioma.

## Cómo funciona

```
Cliente ──/start──▶ Bot ──awg set──▶ Servidor AmneziaWG
                     │                    │
                     └─ .conf por chat ◀──┘
```

El bot corre **en el propio VPS** (como servicio), así que habla con `awg`
directamente y lee los parámetros de ofuscación del `.conf` del servidor.

## 1. Crear el bot en Telegram

1. Abre **@BotFather** y envía `/newbot`
2. Nombre visible: `GeoiD VPN`
3. Usuario: algo terminado en `bot`, por ejemplo `geoidvpn_bot`
4. Copia el **token** (`123456:ABC-DEF...`)

Opcional pero recomendado, con `/setdescription`, `/setuserpic` y `/setcommands`:

```
start - Menú principal
menu - Volver al menú
```

## 2. Cobrar con estrellas de Telegram

No hace falta pasarela ni cuenta de empresa:

- El bot emite la factura con `currency: "XTR"` (ya está en el código)
- El cliente paga con **estrellas** que compra en Telegram
- Tú las retiras desde **@BotFather → /mybots → tu bot → Monetization**

Referencia: **1 estrella ≈ 0,013 $**. Los precios por defecto son
150 / 400 / 1200 estrellas ≈ 2 $ / 5,20 $ / 15,60 $ al mes, trimestre y año.

Si prefieres cripto (USDT/TON), se añade después con **@CryptoBot**; el código
está preparado para añadir esa pasarela sin tocar la lógica de accesos.

## 3. Instalarlo en el VPS

Sube la carpeta `bot/` al servidor. Desde tu PC:

```powershell
scp -r E:\PC\vpn\bot root@193.29.224.164:/root/bot
```

Y en la sesión SSH:

```bash
cd /root/bot
bash instalar.sh
```

Luego rellena el token y tu id:

```bash
nano /etc/geoid-bot.env
```

- `GEOID_TOKEN=` → el token de BotFather
- `GEOID_ADMIN=` → tu id de Telegram (te lo dice **@userinfobot**)

Y arranca:

```bash
systemctl restart geoid-bot
journalctl -u geoid-bot -f
```

Debe aparecer `bot en marcha · servidor 193.29.224.164:21766`.

## 4. Comprobar la ruta del servidor

El bot necesita saber cómo se llama la interfaz y dónde está su `.conf`:

```bash
awg show interfaces
ls -l /etc/amnezia/amneziawg/
```

Si el resultado no es `awg0` y `/etc/amnezia/amneziawg/awg0.conf`, ajústalo en
`/etc/geoid-bot.env` (`GEOID_AWG_IF` y `GEOID_AWG_CONF`).

## 5. Probar

1. Escríbete al bot: `/start`
2. **🎁 Prueba gratis** → debe llegarte un `.conf`
3. En la app: **Perfiles → + → Importar .conf** → **Conectar**
4. Comprueba que el peer aparece en el servidor:

```bash
awg show awg0
```

## Comandos de administrador

| Comando | Para qué |
|---|---|
| `/estado` | activos, avisos del servidor y precios |
| `/promo CODIGO DIAS USOS` | crea un código promocional |
| `/regalar ID DIAS` | activa acceso a mano a alguien |

## Cómo se guarda todo

| Qué | Dónde |
|---|---|
| Usuarios, accesos, pagos | `/var/lib/geoid-bot/bot.sqlite` |
| Configuración | `/etc/geoid-bot.env` |
| Peers | `/etc/amnezia/amneziawg/awg0.conf` (el bot los añade y los quita) |

Haz copia de la base de datos de vez en cuando:

```bash
cp /var/lib/geoid-bot/bot.sqlite /root/bot-$(date +%F).sqlite
```

## Limitaciones actuales (y siguiente paso)

- **Un solo país** (Helsinki). El botón *Cambiar país* lo explica. Para añadir
  países: un servidor por país, una columna `pais` en la base de datos y elegir
  interfaz al crear el peer.
- **Pagos solo con estrellas.** Falta cripto y tarjeta.
- **Sin panel web**: todo se gestiona con comandos.

## Aviso importante

Al empezar a vender:

- Ten claro **qué pasa si el servicio cae** (devolución, días extra).
- Guarda los datos de pago: son la única prueba de quién pagó.
- No prometas "imposible de bloquear": AmneziaWG ofusca, pero ningún protocolo
  es inmune para siempre.
- Revisa las condiciones de Telegram para bots de pago en tu país.

## Pagos: tres métodos

Al elegir un plan, el bot pregunta cómo pagar:

| Método | Cómo funciona | Qué necesitas |
|---|---|---|
| ⭐ **Estrellas** | Telegram cobra al instante | nada (ya funciona) |
| 🪙 **Cripto** | Factura de Crypto Pay; el bot la vigila y activa solo | token de @CryptoBot → Crypto Pay → Create App |
| 💳 **Transferencia / tarjeta rusa** | El cliente paga y tú activas con `/activar ID MESES` | tus datos de cobro |

### Activar cripto

1. Abre **@CryptoBot** → **Crypto Pay** → **Create App**
2. Copia el token y pégalo en `/etc/geoid-bot.env`:

```bash
cat >> /etc/geoid-bot.env <<'EOF'
GEOID_CRYPTO_TOKEN=PEGA_EL_TOKEN
GEOID_CRYPTO_MONEDA=USDT
GEOID_USD_1M=3.5
GEOID_USD_3M=9
GEOID_USD_12M=30
EOF
systemctl restart geoid-bot
```

El bot consulta las facturas pagadas cada 45 segundos y activa el acceso sin
intervención. Acepta USDT, TON, BTC, TRX… según lo que configures.

### Activar pago por transferencia

Pon tus datos reales (tarjeta o SBP). Puedes cambiarlos cuando quieras:

```bash
sed -i "s|^GEOID_PAGO_MANUAL=.*|GEOID_PAGO_MANUAL=Tarjeta 2200 0000 0000 0000 (Ivan I.) o SBP al +7 900 000 00 00. Comentario: tu ID de Telegram.|" /etc/geoid-bot.env
systemctl restart geoid-bot
```

Cuando alguien pulse **“Ya he pagado”**, te llegará un aviso con su ID. Lo
activas con:

```
/activar 123456789 1
```

Y el cliente recibe su `.conf` al instante.

### Tarjeta internacional

Ya está cubierta: las **estrellas** se compran con tarjeta internacional desde
cualquier Telegram. No hace falta pasarela propia.

### Si algún día quieres cobro automático con tarjeta rusa

Eso exige cuenta de autónomo/IP, contrato de adquirencia con un banco
(YooKassa, CloudPayments, Tinkoff) y, normalmente, cheques fiscales. Es un paso
administrativo, no técnico.

## SBP / tarjeta rusa (la vía fácil para clientes rusos)

Sin самозанятый no hay cobro automático, pero sí un flujo de **dos toques**:

1. El cliente elige **💳 СБП / Tarjeta rusa** y ve: importe en ₽, tu teléfono
   (y tu QR si lo configuras), y su ID de Telegram.
2. Paga desde su banco y pulsa **«Ya he pagado»**.
3. A ti te llega el aviso con **un botón «✅ Activar 1 mes»**.
4. Un toque: se activa, se registra el pago y el cliente recibe su `.conf`.

### Configurarlo

```bash
cat >> /etc/geoid-bot.env <<'EOF'
GEOID_SBP_TELEFONO=+79001234567
GEOID_SBP_TITULAR=Ivan Ivanov
GEOID_RUB_1M=199
GEOID_RUB_3M=539
GEOID_RUB_12M=1690
EOF
systemctl restart geoid-bot
```

**QR (recomendado, sin enlaces)**: en la app de tu banco busca «Мой QR» /
«QR для переводов» y guarda la imagen. Luego, en Telegram:

1. Envíale esa foto **a tu propio bot** (como si fuera un mensaje)
2. Responde a la foto escribiendo `/qr`

El bot la guarda y la enviará en cada pago por SBP. Para quitarla: `/qr borrar`.

### Por qué así y no automático

Cobrar con tarjeta o SBP de forma automática exige **самозанятый o ИП** y un
agregador (Freekassa, Lava…). El flujo de arriba funciona **hoy**, sin papeleo,
y añade solo unos minutos de espera. Cuando el volumen lo justifique, se integra
el agregador y el paso 3 desaparece.

## Ajuste: solo QR (sin teléfono ni nombre)

El pago por QR muestra únicamente el importe, el QR y los pasos. El nombre y el
teléfono ya no aparecen en el mensaje.

El botón **📱 Pago por QR** solo se enseña cuando hay un QR guardado:

1. En la app del banco: «Мой QR» / «QR для переводов» → guarda la imagen
2. Envíale esa foto al bot
3. Responde a la foto con `/qr`

Para ocultar el método (por ejemplo, mientras lo preparas): `/qr borrar`.

## Avisos de pago en un grupo aparte

Para que no se mezclen con los clientes y suenen con un tono propio:

1. Crea un **grupo privado** en Telegram (solo tú dentro)
2. Añade el bot **@geoidvpn_bot** como miembro
3. El bot te escribirá en privado con el **ID del grupo**
4. Copia ese comando (te lo da el propio bot) o hazlo a mano:

```bash
echo 'GEOID_AVISOS_ID=-1001234567890' >> /etc/geoid-bot.env
systemctl restart geoid-bot
```

Desde ese momento los avisos de pago (con su botón **✅ Activar**) llegan al
grupo, y en ese chat puedes poner un sonido distinto y fijarlo.

Si quieres volver al privado: borra la línea con
`sed -i "/^GEOID_AVISOS_ID=/d" /etc/geoid-bot.env` y reinicia.

## Anti-abuso de la prueba gratis

La prueba está atada a la **cuenta de Telegram** en la base de datos del servidor:
desinstalar la app, borrar sus datos o cambiar de móvil **no** da otra prueba.
El único hueco es crear otra cuenta de Telegram.

Para detectarlo, el bot revisa cada 15 minutos qué cuentas de prueba están
conectadas y desde qué IP pública:

- Si **dos o más cuentas de prueba sin ningún pago** salen por la misma IP, avisa
  al grupo de pagos con los usuarios y el comando exacto para cortarles el peer.
- Cada aviso se manda una sola vez (tabla `avisos`), no spam.
- **No bloquea nada solo**: en redes móviles rusas mucha gente comparte IP
  (CGNAT), así que el aviso es para que decidas tú.

Para verlo funcionando sin esperar:

```bash
journalctl -u geoid-bot -f | grep -i duplicado
```

## Avisos por correo (independiente de Telegram)

Si Telegram está bloqueado o el proxy falla, los avisos llegan igual al móvil
como notificación del correo.

```bash
cat >> /etc/geoid-bot.env <<'EOF'
GEOID_SMTP_HOST=smtp.yandex.ru
GEOID_SMTP_PORT=465
GEOID_SMTP_USER=tu@yandex.ru
GEOID_SMTP_PASS=CONTRASEÑA_DE_APLICACION
GEOID_CORREO_DESTINO=tu@yandex.ru
EOF
systemctl restart geoid-bot
```

- **Yandex**: `smtp.yandex.ru`, puerto `465`, y hay que crear una
  *contraseña de aplicación* en la configuración de la cuenta.
- **Gmail**: `smtp.gmail.com`, puerto `465`, también con contraseña de aplicación.
- **Mail.ru**: `smtp.mail.ru`, puerto `465`.

Se envía un correo en tres momentos: cuando alguien pulsa «Ya he pagado»,
en cada pago con estrellas y en cada pago con cripto.

## Plan de 6 meses con proxy de Telegram de regalo

Quien compra **6 meses (o 12)** recibe automáticamente el proxy de Telegram: la
mensajería funciona en Rusia sin VPN encendida.

- Se entrega solo, al confirmarse el pago (estrellas, cripto o activación manual).
- Vuelve a pedirlo con **Mi VPN → 🎁 Mi proxy de Telegram**.
- El mínimo de meses se cambia con `GEOID_PROXY_MESES` (por defecto 6).

| Plan | Precio | Proxy |
|---|---|---|
| 1 mes | 150 ₽ · 115 ⭐ · 1,9 USDT | — |
| 3 meses | 399 ₽ · 300 ⭐ · 4,8 USDT | ✅ 1 proxy |
| **6 meses** | **699 ₽ · 520 ⭐ · 8 USDT** | ✅ 2 proxies + 20 días |


Datos del proxy en `/etc/geoid-bot.env`:

```bash
GEOID_PROXY_SERVIDOR=193.29.224.164
GEOID_PROXY_PUERTO=443
GEOID_PROXY_SECRETO=ee2aafaaad9922e542f900a1fb25c68cfc67656f696476706e2e6475636b646e732e6f7267
GEOID_PROXY_MESES=6
```

## Proxy personal (uno por cliente, máximo 2 dispositivos)

Cada cliente con plan de 6 meses o más recibe **su propio proxy**: puerto y
clave únicos. Así se puede limitar y revocar.

### Preparar el servidor (una sola vez)

```bash
scp E:\PC\vpn\servidor\proxy-multiusuario.sh root@193.29.224.164:/root/
bash /root/proxy-multiusuario.sh
```

Crea la plantilla `mtg-user@.service` y la carpeta `/etc/mtg/users`, y abre los
puertos 20000–40000.

### Cómo funciona

| Pieza | Detalle |
|---|---|
| Puerto del cliente | `20000 + (ID de Telegram % 20000)` |
| Clave | Única, generada al comprar |
| Servicio | `systemctl status mtg-user@<ID>` |
| Límite | `GEOID_PROXY_DISPOSITIVOS` (2 por defecto) |
| Control | Cada 5 min el bot cuenta las IPs conectadas |
| Aviso | Si hay más de 2, avisa al grupo con los comandos `iptables` |
| Caducidad | Al vencer el plan, el proxy se **borra** solo |
| Recuperar enlace | **Mi VPN → 🎁 Mi proxy de Telegram** (muestra dispositivos activos) |

Configuración nueva en `/etc/geoid-bot.env`:

```bash
GEOID_PROXY_DOMINIO=geoidvpn.duckdns.org
GEOID_PROXY_DISPOSITIVOS=2
```

> El límite se mide por **IP pública**: dos móviles con datos distintos cuentan
> como dos; un móvil y un portátil en la misma wifi cuentan como uno. Es una
> aproximación razonable: en el peor caso es más permisivo, nunca corta a un
> cliente legítimo por error.

### Separación importante

- **Tu proxy personal** (para tu Telegram): puerto **443**, servicio `mtg`,
  configuración `/etc/mtg.toml`. No se comparte con nadie.
- **Proxy de los clientes**: puertos **20000–40000**, servicios
  `mtg-user@<ID>`, uno por cliente.

El bot **nunca** entrega a un cliente el proxy del puerto 443. Si falta el
sistema multiusuario, simplemente no entrega nada y avisa en el registro.

## Códigos promocionales

### Crear

```bash
/promo VERANO 7 20            # 7 días, 20 usos en total
/promo LANZAMIENTO 3 100 31.12.2026   # además caduca ese día
```

- **Un uso por persona**: el mismo cliente no puede repetir el código
- Si un código se recrea con el mismo nombre, los usos por persona se reinician
- Los días **se suman** a lo que le quedara al cliente

### Gestionar

| Comando | Para qué |
|---|---|
| `/promos` | Lista con usos restantes y fecha de caducidad |
| `/promo borrar VERANO` | Elimina el código |

### Cómo lo usa el cliente

Menú **🎟 Canjear código** → escribe el código (vale en minúsculas) → recibe
los días y su `.conf` al instante.

## Enlaces de descarga automáticos

El bot **no lleva los enlaces escritos a mano**: cada 6 horas pregunta a GitHub
por la última versión publicada y guarda los archivos reales en la base de datos.

| Situación | Qué hace el bot |
|---|---|
| Se publica una versión nueva | Actualiza los enlaces y avisa al grupo de pagos |
| Cambia el nombre de un archivo | Detecta el archivo correcto por sí solo |
| GitHub no responde | Mantiene los enlaces anteriores y reintenta |
| Se borra una versión antigua | No afecta: usa `releases/latest` |

Comando de administrador:

```
/enlaces
```

Muestra la versión detectada, la última revisión y los enlaces guardados, y
fuerza una comprobación inmediata.

> Los enlaces que reparte el bot son del tipo
> `releases/latest/download/GeoiD-vpn-Android-arm64-v8a.apk`: como el nombre es
> fijo y `latest` siempre apunta a la última, no caducan nunca.

## Soporte privado (tickets)

El botón **❓ Ayuda** sigue mostrando los enlaces de descarga y, además, invita
al cliente a escribir. A partir de ahí:

1. **El cliente escribe** lo que necesite en el chat del bot.
2. **Al grupo de pagos** llega un ticket:

```
🎫 Ticket de soporte

De: @usuario (ID 123456789)

No me conecta con el perfil nuevo

Responde a este mensaje para contestarle.
```

3. **Tú respondes al ticket** (mantener pulsado → Responder → escribir).
4. El bot entrega la respuesta **en privado** a ese cliente y te confirma
   con "✅ Enviado al cliente".

Cada conversación es privada: el cliente solo ve sus mensajes y tu respuesta.

### Detalles

| Situación | Cómo se comporta |
|---|---|
| El cliente pulsa **🎟 Canjear código** y escribe | Se trata como código (10 minutos de margen) |
| Cualquier otro texto | Se convierte en ticket de soporte |
| Tú escribes en el grupo | No genera ticket (se ignora) |
| El cliente bloqueó el bot | El bot te avisa de que no se pudo entregar |
| Sin grupo configurado | Los tickets llegan a tu privado |

> Para que el bot vea tus respuestas en el grupo, la **privacidad de grupos**
> debe estar desactivada: @BotFather → /mybots → geoidvpn_bot →
> Bot Settings → Group Privacy → Turn off.

---

## Resumen de la versión 4.0 del bot

| Función | Estado |
|---|---|
| Menú fijo (7 botones) | ✅ |
| Prueba de 3 días | ✅ |
| 3 planes con precio en ₽ (máx. 6 meses) | ✅ |
| Estrellas / Cripto / QR | ✅ |
| Proxy personal desde 6 meses | ✅ (máx. 2 dispositivos) |
| Soporte con tickets privados | ✅ |
| Invitaciones por niveles | ✅ |
| Promos (1 uso por persona, caducidad) | ✅ |
| Enlaces de descarga automáticos | ✅ |
| Anti-abuso por IP | ✅ |

Archivos del bot: `bot.py`, `config.py`, `db.py`, `textos.py`, `provision.py`,
`pagos.py`, `proxy.py`, `avisos.py`, `descargas.py`.

Comprobar antes de reiniciar:

```bash
cd /opt/geoid-bot && for f in *.py; do python3 -m py_compile $f || echo "FALLA $f"; done && echo "TODO OK"
```

## Pago con estrellas: solo si el cliente ya las tiene

Las estrellas se quedan como opción, pero **sin servicio externo**. Motivo: para
un cliente ruso comprar estrellas en un tercero son 4–5 pasos, dar su @usuario y
un recargo del 10–40 %; en la práctica muchos abandonan.

El orden de pago que se muestra ahora:

1. **📱 Pago por QR · rublos (lo más rápido)** — su banco, 2 toques, 0 % comisión
2. **🪙 Cripto (USDT / TON)** — para quien ya tiene cripto
3. **⭐ Estrellas (si ya tiene)** — factura directa de Telegram

El código del servicio externo queda aparcado (`GEOID_ESTRELLAS_URL` en
`config.py`) por si algún día se quiere recuperar, pero no aparece en el menú.
