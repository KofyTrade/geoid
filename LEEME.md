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
