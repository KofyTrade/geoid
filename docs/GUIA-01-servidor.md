# Guía 01 — Montar el servidor (VLESS + REALITY)

**Estado: ✅ completada** (noviembre 2026). Al final tendrás internet sin bloqueos en tu
móvil, y una base sólida sobre la que construir la app.

```
[ v2rayNG en tu Android ]  ──HTTPS falso hacia microsoft.com──►  [ Tu VPS ]
```

---

## Paso 1 — Contratar el VPS

> ⚠️ **Hetzner no sirve para esto.** Desde 2024 no acepta clientes de Rusia y su web ni
> siquiera carga desde allí. Lo comprobamos en la práctica: no pierdas el tiempo.

**Proveedor elegido: Aeza** — <https://aeza.net>
Panel en inglés o ruso, acepta tarjetas rusas, СБП y cripto, y tiene sede en **Helsinki**.
Tu latencia medida: **17 ms**.

1. Crea la cuenta con un correo secundario y una contraseña única.
2. **Finance → Top up**: recarga ~8 € (unos 700 ₽). Se paga por adelantado.
3. **Add service → virtual server**.
4. Configuración:

   | Campo | Valor |
   |---|---|
   | **Location** | `Helsinki` (17 ms) |
   | **Tariff** | `HELs-1` — 1 core, 2 GB, 30 GB, tráfico ilimitado, ~5,93 €/mes |
   | **Billing period** | `1 month` · **Auto renewal**: apagado |
   | **System** | `Ubuntu 24.04` o `26.04` (sirve cualquiera) |
   | **Backups** | apagado |

5. Pulsa **Pay**. En 1–3 minutos el estado pasa de `activation` a `active`.

> **Nunca elijas Moscú ni San Petersburgo**, aunque tengan el mismo ping: un servidor
> *dentro* de Rusia no evade los bloqueos rusos, porque el tráfico no sale del país.

### Credenciales de acceso

Aeza no pide clave SSH al crear el servidor: te da **usuario `root`** y **contraseña** en
la ficha del servidor (pestaña **Information**, icono de copiar). Con eso entras por SSH.

> **Alternativas:** Fornex (Países Bajos/Alemania, desde ~551 ₽), VDSina, AdminVPS.
> Vultr y DigitalOcean funcionan, pero sus contratos permiten cerrar la cuenta a clientes
> de Rusia sin previo aviso.

---

## Paso 2 — Conectar por SSH

En **PowerShell** de tu PC:

```powershell
ssh root@TU_IP
```

- La primera vez pregunta por la huella → escribe `yes` + Enter.
- Luego pide la contraseña → pégala con clic derecho y Enter.
  **No verás nada mientras escribes**: es normal en Linux.
- Sabrás que estás dentro cuando el prompt sea `root@<hostname>:~#`.

---

## Paso 3 — Subir y ejecutar el instalador

El script está en `E:\PC\vpn\servidor\`. **Desde una segunda ventana de PowerShell**
(no desde dentro del SSH):

```powershell
scp "E:\PC\vpn\servidor\instalar-xray-reality.sh" root@TU_IP:/root/
```

Comprueba en el SSH que llegó (debe pesar ~6,4 KB):

```bash
ls -l /root/instalar-xray-reality.sh
```

Y ejecútalo (ya eres root):

```bash
bash /root/instalar-xray-reality.sh
```

Tarda 1–2 minutos. Al final dibuja un **QR** y guarda el enlace en
`/root/vpn-enlace.txt`.

---

## Paso 4 — Conectar desde Android

1. Instala **v2rayNG** desde GitHub (en Rusia la Play Store no lo ofrece):
   <https://github.com/2dust/v2rayNG/releases> → **Assets** → `..._universal.apk`.
   - Android pedirá permitir instalación desde esa fuente. Play Protect avisará: es
     normal en apps que no están en la tienda.
2. Abre v2rayNG → **`+`** → **Scan QR code** → apunta al QR de la terminal.
3. Toca la entrada para seleccionarla y pulsa el **botón redondo** de abajo.
4. Acepta el permiso de VPN de Android.

**Comprobación:** abre <https://ipinfo.io/json>. Debe mostrar la IP del servidor,
`"country": "FI"` y `"org": "... AEZA GROUP ..."`.

> Si el QR ya no está en pantalla, vuelve a dibujarlo:
> ```bash
> qrencode -t ANSIUTF8 "$(cat /root/vpn-enlace.txt)"
> ```
> Plan B sin QR: `cat /root/vpn-enlace.txt`, copia la línea y usa
> **Import config from clipboard**.

---

## Paso 5 — Comprobaciones en el servidor

```bash
systemctl status xray --no-pager     # active (running)
ss -lntp | grep 443                  # xray escuchando en :443
journalctl -u xray -n 20 --no-pager  # errores, si los hay
```

---

## Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| La web del proveedor no carga desde Rusia | El proveedor no atiende a Rusia | Cambia de proveedor (nos pasó con Hetzner) |
| `ssh: connect ... timed out` | Servidor aún arrancando | Espera 1 min y reintenta |
| `Permission denied` | Contraseña copiada incompleta | Vuelve a copiarla del panel |
| **`invalid "password"` en el móvil** | La clave pública del enlace está mal formada | Ver *Claves de Xray 25+* abajo |
| **`empty "password"` en el móvil** | La clave pública quedó vacía | Igual: regenera el enlace y comprueba 43 caracteres |
| El script falla al instalar Xray | Sin salida a internet | `curl -I https://github.com` debe responder 200 |
| `xray no arranco` | Puerto 443 ocupado | Edita `PUERTO=8443` y vuelve a ejecutar |
| Conecta pero no navega | DNS o reloj desajustado | `timedatectl`; en v2rayNG usa DNS remoto |
| Funciona en Wi-Fi, **no en datos móviles** | El DPI móvil es más agresivo | Cambia `PUERTO` a `8443` o `2053` |
| Funciona 1–2 días y muere | La IP fue detectada | Nuevo servidor o cambia `DESTINO`/`SNI` |

### Claves de Xray 25+ (el fallo que nos costó una hora)

Xray 26 imprime las claves así:

```
PrivateKey: <43 caracteres>
Password:   <43 caracteres>   <- esta es la clave PUBLICA que va en el enlace
Hash32:     <43 caracteres>
```

En versiones antiguas era `Public key:`. Un script que busque "public" no la encuentra y
puede acabar **pegando dos líneas juntas** (86 caracteres) o dejándola vacía. El enlace
solo es válido si el parámetro `pbk` mide **exactamente 43 caracteres**.

Para reconstruir el enlace desde cero, con comprobación:

```bash
CONF=/usr/local/etc/xray/config.json
UUID=$(grep -o '"id": *"[^"]*"' $CONF | head -1 | cut -d'"' -f4)
SID=$(grep -o '"shortIds": *\[ *"[^"]*"' $CONF | cut -d'"' -f4)
PRIV=$(grep -o '"privateKey": *"[^"]*"' $CONF | cut -d'"' -f4)
PBK=$(xray x25519 -i "$PRIV" | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g' | grep -i password | grep -oE '[A-Za-z0-9_-]{43}' | head -1)
echo "UUID=${#UUID} SID=${#SID} PBK=${#PBK}"   # esperado: 36 16 43
```

**Truco útil:** cambia `DESTINO` y `SNI` por otro sitio grande, estable, con TLS 1.3 y
HTTP/2 y que **no** esté bloqueado en Rusia. Ejemplos: `www.microsoft.com`,
`www.samsung.com`, `dl.google.com`, `www.icloud.com`. Ambos valores deben coincidir.

---

## Seguridad y mantenimiento

- **No compartas el enlace.** Es la credencial: quien lo tenga usa tu servidor.
- Apunta en un lugar seguro: IP, UUID, clave pública y shortId (o guarda una copia de
  `/root/vpn-enlace.txt`).
- Actualiza de vez en cuando:
  ```bash
  apt update && apt upgrade -y
  bash -c "$(curl -fsSL https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
  ```
- Para un segundo dispositivo, añade otro UUID al bloque `clients` del JSON y genera su
  propio enlace; no compartas el primero.

---

## Siguiente paso

**Fase 2** — la app Android en Kotlin: genera y gestiona tus enlaces `vless://`
(y más adelante crea el túnel ella misma).
