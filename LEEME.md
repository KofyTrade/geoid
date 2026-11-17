# GeoiD-vpn — estado del proyecto

Documento de referencia para retomar el trabajo en el futuro sin tener que
reconstruir el contexto.

**Última versión publicada: 3.0.3**

- Descargas: <https://github.com/KofyTrade/geoid/releases/latest>
  - Android: `GeoiD-vpn-Android-3.0.x-<arquitectura>.apk` (arm64-v8a, armeabi-v7a, x86_64)
  - Windows: `GeoiD-vpn-Windows.zip`
- Repositorio: <https://github.com/KofyTrade/geoid> (privado)
- Cuenta: `KofyTrade`

## Qué hay en esta carpeta

```
flutter_app/      LA APP (Flutter). Aquí está todo el código que importa.
  lib/            interfaz, perfiles, actualizador, idiomas
  android/        túnel VpnService + motor AmneziaWG (awg.aar)
  windows/        runner de Windows
  windows_tun/    main.go: motor del túnel para Windows (Wintun + AmneziaWG)
app/              versión 1.x en Kotlin, solo como referencia histórica
bot/              bot de Telegram que vende y aprovisiona accesos (ver bot/LEEME.md)
docs/             guías: servidor, app, diseño, rendimiento
servidor/         script de instalación de Xray en el VPS
.github/          flujos de compilación y publicación automática
awg/              perfiles .conf (móvil y portátil)  ← NO se sube a git
firma-geoid.txt   contraseña de la clave de firma   ← NO se sube a git
vpn-enlace.txt    datos del servidor (UUID, clave)  ← NO se sube a git
GeoiD-vpn-windows.zip   copia local del paquete de Windows
```

## Lo que NO está aquí (y se puede volver a descargar)

Se borró para dejar la carpeta ligera (ocupaba ~15 GB):

| Qué | Para qué servía | Cómo recuperarlo |
|---|---|---|
| `flutter_app/flutter-sdk` | compilar Flutter en local | <https://docs.flutter.dev/get-started/install/windows> |
| `tools/` | NDK, caché de Go, Gradle, `wintun.dll`, APK de prueba | se descarga solo al compilar |

**No hace falta nada de eso para continuar**: las compilaciones y publicaciones
las hace GitHub Actions.

## Cómo se publica una versión nueva

1. Cambiar la versión en `flutter_app/pubspec.yaml` (`version: 3.0.4+37`)
2. Hacer commit y subir
3. Etiquetar con la **misma** versión y subir la etiqueta:

```powershell
cd E:\PC\vpn
git add -A
git commit -m "Version 3.0.4"
git push
git tag v3.0.4
git push origin v3.0.4
```

GitHub Actions compila el APK por arquitectura y el ZIP de Windows, los firma
con la clave del repositorio y los adjunta al release. Avisa en unos 6 minutos.

> Si la etiqueta no coincide con `pubspec.yaml`, el flujo **falla a propósito**
> (para que no vuelva a publicarse un binario con la versión equivocada).

## Claves que no se pueden perder

- `firma-geoid.txt` — contraseña de la clave de firma.
- `app/android-proyecto/geoid-release.jks` — la clave en sí.

Sin ambas, Android rechazará las actualizaciones sobre la app instalada. En
GitHub están como secretos (`KEYSTORE_BASE64`, `KEYSTORE_PASSWORD`, `KEY_ALIAS`,
`KEY_PASSWORD`), pero conviene guardar copia fuera del ordenador.

## Estado del servidor

VPS Aeza en Helsinki, `193.29.224.164`.

| Pieza | Estado |
|---|---|
| AmneziaWG (UDP 21766) | funcionando, MTU 1280 |
| dnsmasq (10.9.9.1) | funcionando, con lista de anuncios (~500.000 dominios) |
| BBR + fq | **activado** (`/etc/sysctl.d/99-geoid.conf`) |
| Xray REALITY | aparcado (cliente en pausa) |

Optimización pendiente si algún día va lento: revisar `journalctl -u dnsmasq` y
la caché de DNS (se intentó y el servicio falló al reiniciar; se dejó como estaba).

## Qué se ha hecho ya (resumen)

- App Android con túnel real AmneziaWG, perfiles múltiples, selección de
  aplicaciones, bloqueo de anuncios por DNS, 8 idiomas y actualizador propio.
- App de Windows con el mismo diseño, túnel propio (Wintun + AmneziaWG),
  pide administrador y se minimiza a la bandeja del sistema.
- Publicación automática de ambas en GitHub Releases, firmadas.
- Rendimiento del cliente: polihedro sin reconstruir el árbol de widgets,
  socket de latencia reutilizado, listado de apps en segundo plano.

## Ideas para la siguiente sesión

- Instalador para Windows (evitar descomprimir a mano).
- Mostrar progreso de descarga de la actualización dentro de la app.
- Selección por aplicación en Windows (requiere un controlador WFP firmado).
- Prueba de velocidad integrada para comparar antes/después de BBR.

---

## Estado al 16/11/2026 (cierre de sesión)

**App**: 3.0.3 en Android y Windows, con actualización automática desde Releases.

**Bot @geoidvpn_bot** (en el VPS, servicio `geoid-bot`):
- Menú fijo abajo + menú ☰ con `/start` y `/menu`
- Prueba de 3 días
- Cobro con ⭐ Estrellas (automático), 🪙 Cripto Crypto Pay (automático) y
  📱 Pago por QR / SBP (el bot avisa y se activa con un toque)
- Avisos de pago en un grupo privado aparte (`GEOID_AVISOS_ID`)
- Comandos de administrador: `/estado`, `/qr`, `/chatid`, `/activar`,
  `/regalar`, `/promo`
- Precios: 150 / 399 / 699 ₽ · 115 / 300 / 520 ⭐ · 1.9 / 4.8 / 8 USDT

**Servidor**: AmneziaWG (UDP 21766, MTU 1280), dnsmasq con bloqueo de anuncios,
BBR activo.

### Pendiente para la próxima sesión

1. Sacarte el **самозанятый** → integrar Freekassa/Lava y automatizar el SBP.
2. Comando `/ventas` con resumen de ingresos y clientes activos.
3. Añadir más países (otro VPS por país + columna `pais`).
4. Copia de seguridad de `bot.sqlite` y del keystore fuera del servidor/PC.

---

## Versión 4.0 (17 de noviembre de 2026)

Primera versión "redonda": todo el ciclo de venta funciona sin intervención
manual salvo confirmar el pago por QR.

### Aplicación (Android 4.0.0 · Windows 4.0.0)

- **Abrir `.conf` con la app**: aparece directamente en «Abrir con» (también
  desde Telegram) y al abrirlo **crea y activa el perfil solo**.
- **Botón de estado**: muestra *VPN activa*, *Periodo de prueba* o *Activar VPN*
  leyendo el plan que el bot escribe dentro del `.conf`.
- **Pantalla Activar VPN**: prueba de 3 días, compra y Mi VPN, con enlace al bot.
- **Ajustes**: idioma (9), tema claro/oscuro, bloqueo de anuncios, Acerca de.
- **Aplicaciones sin VPN**: lista negra. Dos casillas para separar
  *instaladas* y *del sistema*; solo se marca lo del grupo visible.
- Textos de «Acerca de»: WireGuard ofuscado (sin tecnicismos).

### Bot (@geoidvpn_bot)

- Menú fijo con 7 botones (sin «Cambiar país» mientras haya un solo servidor).
- **3 planes**: 1, 3 y 6 meses (máximo 6), con precio en rublos y 🎁 en los largos.
- **Pagos**: ⭐ estrellas, 🪙 cripto (Crypto Pay) y 📱 QR/SBP con activación en un
  toque desde el grupo de pagos.
- **Proxy de Telegram de regalo** desde 6 meses: proxy **personal** por cliente,
  puerto propio, límite de 2 dispositivos y aviso si lo divulga.
- **Soporte privado**: el cliente escribe y llega un ticket al grupo; respondiendo
  al ticket le llega en privado. Comando `/ticket` para probarlo.
- **Invitaciones por niveles**: 3 amigos = 7 días, 10 = 15 días, 20 = 1 mes;
  solo cuentan los que compran.
- **Códigos promocionales**: un uso por persona, caducidad opcional, `/promos`
  y `/promo borrar`.
- **Enlaces de descarga automáticos**: cada 6 h consulta GitHub y actualiza los
  enlaces; `/enlaces` para forzar la revisión.
- **Anti-abuso**: aviso si varias cuentas de prueba comparten IP pública.

### Servidor

- AmneziaWG (UDP 21766, MTU 1280), BBR, dnsmasq con bloqueo de anuncios.
- Proxy MTProto propio en el puerto 443 (`mtg`) para tu Telegram.
- Plantilla `mtg-user@.service` para los proxies personales de clientes.

### Pendiente para la próxima sesión

1. **самозанятый** → integrar Freekassa/Lava y automatizar el SBP.
2. Comando `/ventas` con ingresos por método y clientes activos.
3. Segundo país (Países Bajos o Alemania) cuando haya demanda.
4. Copias de seguridad de `bot.sqlite` y del keystore fuera del servidor.
5. Crear el dominio `geoidvpn.duckdns.org` (quita el aviso del proxy).
6. Avisos por correo: falta poner las claves SMTP en `/etc/geoid-bot.env`.

