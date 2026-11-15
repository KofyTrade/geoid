# Geoid

Cliente VPN para Android con **AmneziaWG** (WireGuard ofuscado), pensado para redes
con inspección profunda de paquetes. Interfaz oscura, perfiles múltiples, selección
de aplicaciones y bloqueo de publicidad por DNS.

> **Versión 2.x: Flutter.** La app actual está en `flutter_app/` (un solo código
> para Android y, más adelante, escritorio). La versión 1.x en Kotlin sigue en
> `app/` como referencia y legado.

<p align="center">
  <em>Un poliedro que gira como un planeta cuando el túnel está activo.</em>
</p>

## Descargar

APK firmado, desde Releases:

<https://github.com/KofyTrade/geoid/releases/latest>

La app comprueba las versiones nuevas al abrirse y al conectar, y ofrece
descargarlas.

Para escritorio hay un paquete de Windows en el mismo release: ver
[la guía de Windows](docs/GUIA-05-windows.md).

## Qué hace

- **Túnel real** con AmneziaWG 3.1 sobre `VpnService`: TCP y UDP, sin proxies.
- **Camuflaje** con los parámetros `Jc/Jmin/Jmax`, `S1–S4`, `H1–H4`, `I1` y
  `HeaderProtectionKey`, que rompen la firma de WireGuard ante el DPI.
- **Perfiles**: varios servidores, con renombrar, editar y borrar.
- **Importación** de `.conf` desde archivo o compartiendo desde otra app.
- **Selección de aplicaciones** con lista blanca opcional.
- **Panel en vivo**: velocidad, latencia y país del servidor.
- **Bloqueo de anuncios** por DNS (lista de ~500.000 dominios en el servidor).
- **8 idiomas**: inglés, español, francés, alemán, italiano, ruso, japonés y coreano.

## Estructura

```
flutter_app/                  app 2.x en Flutter (la que se publica)
  lib/                        interfaz, perfiles, actualizador e idiomas
  android/                    tunel VpnService + motor AmneziaWG (awg.aar)
app/
  android/                    plantillas de codigo + script de instalacion (1.x)
    instalar-codigo.ps1       copia las plantillas al proyecto de Android Studio
    strings/                  traducciones (values, -es, -fr, -de, -it, -ru, -ja, -ko)
  android-proyecto/           proyecto de Android Studio (Kotlin)
  icono/generar.py            genera el icono (Python + Pillow)
docs/                         guias, diseno y especificaciones
servidor/                     scripts de instalacion del servidor
```

## Compilar la app

Requisitos: Android Studio (JDK 17), Android SDK 37, NDK r28c, Go 1.25+ y
`gomobile` (fork de SagerNet).

1. Compilar el motor (una vez), en el repositorio de `amneziawg-go`:

   ```bash
   gomobile bind -target android -androidapi 24 -javapkg com.geoid \
       -o awg.aar ./mobile/awg
   ```

   Copiar `awg.aar` a `app/android/`.

2. Instalar las plantillas y compilar:

   ```powershell
   powershell -ExecutionPolicy Bypass -File app\android\instalar-codigo.ps1 `
              -Proyecto app\android-proyecto
   cd app\android-proyecto
   .\gradlew.bat assembleDebug
   ```

El APK queda en `app/android-proyecto/app/build/outputs/apk/debug/app-debug.apk`.

## Servidor

El servidor usa Xray (REALITY) y AmneziaWG con dnsmasq como resolutor con filtro
de publicidad. Las instrucciones están en [`docs/`](docs/):

- [`docs/GUIA-01-servidor.md`](docs/GUIA-01-servidor.md) — preparar el VPS
- [`docs/especificacion.md`](docs/especificacion.md) — decisiones tecnicas y fallos resueltos


## Actualizaciones

Las versiones se publican en [Releases](https://github.com/KofyTrade/geoid/releases).
Al empujar una etiqueta `vX.Y` GitHub Actions compila el APK firmado y lo publica:

```bash
git tag v1.4 && git push origin v1.4
```

La app consulta la ultima release al abrirse y al conectar, y muestra un aviso
para descargar la version nueva. **Importante**: el APK debe estar firmado
siempre con la misma clave (`geoid-release.jks`), o Android rechazara la
actualizacion por diferencia de firma.
## Notas

- El proyecto **no incluye** claves, perfiles ni configuración de servidor:
  esos archivos están en `.gitignore` a propósito.
- El binario `awg.aar` tampoco se versiona; se compila con el paso 1.

## English summary

Geoid is an Android VPN client built on **AmneziaWG** (obfuscated WireGuard) for
censored networks. It runs a real `VpnService` tunnel with TCP and UDP, supports
multiple profiles, per-app routing, a live speed/latency panel, DNS-based ad
blocking and eight languages. Build instructions are above; no keys or server
configuration are included in this repository.
