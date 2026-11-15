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
