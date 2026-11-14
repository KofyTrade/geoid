# Especificación — App VPN (hacia v3.0)

> **v3.0 COMPLETADA** (14 nov, 13:11). Motor nuevo: **AmneziaWG** (WireGuard ofuscado).
> Verificado: `{"ip":"<IP_DEL_VPS>","country":"FI"}` y YouTube cargando con imágenes.
>
> ## Cómo se montó
>
> 1. **Servidor:** `amneziawg-installer` (bivlked) → AmneziaWG 3.1, puerto **21766/UDP**,
>    perfiles en `/root/awg/*.conf` con `Jc=4 Jmin=77 Jmax=170 S1=20 S2=93 S3=33 S4=27
>    H1..H4=1..4 I1=... HeaderProtectionKey=... ContentPaddingAddition=32-128`.
> 2. **Librería Android:** `amneziawg-go` (módulo `/v3`) envuelto en `mobile/awg/awg.go`
>    y compilado con `gomobile bind` → `awg.aar` (11,2 MB, 4 ABIs).
> 3. **Cliente:** `AwgTunnelService` crea el TUN con `VpnService` y llama
>    `Awg.start(fd, mtu, uapi)`. El `.conf` se traduce a UAPI en `AwgConfig.kt`
>    (base64 → hex para las claves).
>
> ## Los tres fallos que costaron horas
>
> | Síntoma | Causa | Solución |
> |---|---|---|
> | `permission denied` al arrancar | `CreateTUNFromFile` intenta cambiar el MTU; Android lo prohíbe | `CreateUnmonitoredTUNFromFD` |
> | Túnel arriba, RX=0, sin handshake | El socket UDP del handshake entra en el túnel (bucle) | `Builder.excludeRoute(IP_servidor/32)` |
> | Handshake enviado pero rechazado | Faltaban los parámetros **AmneziaWG 3.1** (I1, HeaderProtectionKey, ContentPaddingAddition) | Enviarlos en la UAPI |
>
> ## Ventaja sobre el motor anterior
>
> WireGuard transporta **TCP y UDP** por igual: no hay problema de QUIC, ni de DNS
> envenenado (el DNS viaja dentro del túnel). Eso elimina los tres infiernos de la v1.2.
>
> ## Pendiente
>
> - Bloqueador de anuncios: ahora debe ir en el DNS del servidor (dnsmasq + lista).
> - Motor VLESS aparcado en `app/singbox-parked/` (dos runtimes de Go no caben en un APK).

# Especificación histórica — v1.x (sing-box)

# Especificación — App VPN (hacia v1.0)

> **v1.1 COMPLETADA** (14 nov, 10:47). El túnel funciona y **el DNS también**: Instagram
> carga a través de Helsinki. Resuelto el envenenamiento de DNS del DPI ruso.

> **v1.2 COMPLETADA** (14 nov, 11:10). El túnel funciona y **las apps cargan de verdad**:
> YouTube e Instagram abren con vídeo e imágenes.
>
> **El último fallo era QUIC.** Las apps usan UDP/443 (QUIC) para vídeo e imágenes, y el
> UDP no vuelve por el túnel (XTLS-Vision no lo transporta bien). Resultado: la API
> (TCP) cargaba y los medios no. Solución en la app:
>
> ```json
> { "network": "udp", "port": 443, "action": "reject" }
> ```
>
> Al rechazar QUIC, las apps caen a TCP y todo carga.

## La solución del DNS (el bloqueo anterior)

El DPI ruso devuelve `NXDOMAIN` para los dominios bloqueados cuando el DNS sale directo.
Y el DNS por el túnel fallaba: UDP no vuelve, y DoT/DoH a resolutores públicos daban
timeout de 5 s desde el servidor.

**Solución:** resolver en el propio VPS y consultarlo por TCP dentro del túnel.

En el servidor (`dnsmasq` en el puerto 5353):

```
port=5353
no-resolv
no-hosts
server=1.1.1.1
server=8.8.8.8
cache-size=1000
```

En la app (config de sing-box):

```json
"dns": {
  "servers": [{ "type": "tcp", "tag": "remote",
                "server": "<IP_DEL_VPS>", "server_port": 5353,
                "detour": "proxy" }],
  "final": "remote"
}
```

Resultado: `i.instagram.com → 157.240.205.63` resuelto por nuestro servidor, e Instagram
carga. Sin depender de resolutores externos, que el host bloquea.

## Las dos causas del último fallo (y su solución)

**1. Versión del motor incompatible.**
`libbox` 1.14.4 (octubre) no entiende a Xray 26.11.9 (noviembre): `reality verification failed`.
Comprobado comparando clientes con el MISMO enlace: Xray conectaba, sing-box no.
→ Solución: compilar `libbox.aar` desde la rama **`testing`** de sing-box.

**2. MTU 9000 rompía TCP.**
Con MTU 9000 pasaban DNS y UDP (por eso parecía "casi funciona") pero **ninguna conexión
TCP**, y sin error en el log: los paquetes entraban al túnel y se perdían.
→ Solución: `"mtu": 1400`. Ahora TCP y UDP funcionan.

**3. La API de `PlatformInterface` creció** en la rama nueva (`usePlatformAutoRedirect`,
`createAutoRedirect`). Implementados como no soportados.

**Nota:** el tráfico del usuario `shell` (por ejemplo `adb shell nc`) NO pasa por la VPN por
diseño de Android. Para probar hay que usar una app (Chrome) o `adb shell run-as`.

## Visión

Cliente VPN propio para Android: **rápido, simple y con control por aplicación**.
Nada de menús profundos ni animaciones que estorben.

---

## Requisitos de producto

| # | Requisito | Prioridad |
|---|---|---|
| R1 | Interfaz moderna y simple: un botón grande de conectar, estado claro | Alta |
| R2 | **Selección por app**: marcar qué apps usan la VPN y cuáles no | Alta |
| R3 | Las apps marcadas usan la VPN **sin tener que abrir la app cada vez** | Alta |
| R4 | Rapidez: abrir y conectar en menos de 2 segundos, sin pantallas intermedias | Alta |
| R5 | Varios servidores / perfiles, con el más rápido por defecto | Media |
| R6 | Reconexión automática si se cae el túnel | Media |

---

## Decisiones técnicas

### Per-app routing: es nativo, no hay que hackear nada

`VpnService.Builder` tiene dos métodos que hacen exactamente esto:

```kotlin
builder.addAllowedApplication("com.instagram.android")     // lista blanca
builder.addDisallowedApplication("com.whatsapp")           // lista negra
```

- Si **no** llamas a ninguno, **todas** las apps pasan por el túnel (comportamiento actual de v2rayNG).
- Si usas `addAllowedApplication`, **solo esas** pasan por la VPN y el resto navega directo.
- La app de VPN queda excluida automáticamente (no hay bucles).

**Implicación importante:** el filtrado ocurre en el `VpnService`, **no** en el motor del túnel.
Así que esta función es independiente de que usemos sing-box, Xray o lo que sea. Se puede
construir y probar mucho antes de tener el túnel real.

### "Sin tener que activar la app cada vez"

Son dos cosas distintas y conviene no confundirlas:

1. **Elegir apps** (R2) → lo anterior, `addAllowedApplication`.
2. **Conectar sola** (R3) → aquí entran:
   - **Always-on VPN** del sistema: Ajustes → Red → VPN → engranaje → *Always-on VPN*.
     Android reconecta al arrancar y tras caídas. Es lo más fiable y no gasta batería
     con trucos.
   - Alternativa casera: `BOOT_COMPLETED` + servicio en primer plano. Más frágil.

**Recomendación:** usar el Always-on VPN del sistema y que nuestra app solo tenga que
funcionar bien al reconectar.

> ⚠️ **Cuidado con "Block connections without VPN":** si se activa y nuestra app falla al
> arrancar, el móvil se queda **sin internet**. Probarlo siempre con esa opción desactivada.

### Motor del túnel

**sing-box** (`libbox.aar`): soporta VLESS + REALITY, es el mismo motor que usa mucha
gente en Rusia y ya está probado contra el DPI. Integración por JNI + servicio.

### Interfaz

- **Jetpack Compose + Material 3** para lo visual.
- Pantalla principal: estado grande (Conectado / Desconectado), botón redondo, servidor
  actual, y un acceso directo a *Aplicaciones*.
- Pantalla *Aplicaciones*: lista con icono, nombre y casilla. Buscador arriba.
- Sin animaciones largas ni pantallas de carga.

### Lo que NO hace más rápido a la VPN

La interfaz no influye en la velocidad. Lo que manda es:
1. La distancia al servidor (Helsinki: **17 ms** desde tu conexión).
2. El protocolo (REALITY añade muy poco).
3. No tunelizar tráfico que no lo necesita — y aquí el per-app **ayuda**: menos apps
   pasando por el túnel = menos batería y menos latencia percibida.

---

## Fachada de versiones

| Versión | Qué añade | Estado |
|---|---|---|
| v0.1 | Generador/validador HTML | ✅ hecho |
| v0.2 | App Android que gestiona y valida enlaces | ✅ hecho (formulario) |
| **v0.3** | `VpnService` + botón conectar/desconectar + notificación. **Sin túnel real todavía**: se crea la interfaz TUN y se comprueba el ciclo de vida | ✅ hecho (14 nov) |
| **v0.4** | Lista de apps instaladas + `addAllowedApplication` (lista blanca) | ✅ hecho (14 nov) |
| **v1.0** | sing-box como motor real: el tráfico sale cifrado por Helsinki | ✅ hecho (14 nov, 08:37) |

La razón del orden: cada capa se puede probar sola. Si metemos el túnel y el per-app a la
vez y algo falla, no sabremos cuál de los dos es.

---

## v1.0 — Hallazgos sobre sing-box (libbox)

Comprobado el 14 nov contra la release oficial **v1.14.4** (API de GitHub):

- **`libbox.aar` NO se publica.** Los assets son APKs de SFA, paquetes de iOS y binarios
  de CLI. No hay ningún `.aar` en la release.
- **Tampoco está en Maven Central.** El proyecto Android oficial lo enlaza como archivo
  local: `implementation(files("libs/libbox.aar"))`.
- Por tanto el AAR **hay que compilarlo** desde el código Go:
  ```
  go run ./cmd/internal/build_libbox -target android
  ```
  Requiere **Go** y el **Android NDK**. Resultado: ~110 MB, 4 ABIs.
  En esta máquina no hay ninguno de los dos instalado (comprobado).

### Qué implica integrarlo

1. Implementar `PlatformInterface` (≈20 métodos: `OpenTun`, `FindConnectionOwner`,
   `StartDefaultInterfaceMonitor`, `ReadWIFIState`, `SystemCertificates`…).
2. Construir el JSON de sing-box a partir de los datos del formulario (VLESS + REALITY).
3. Sustituir el `Builder` actual de `VpnTunnelService` por el arranque de `BoxService`.

Es un proyecto de **1–3 horas** con riesgo real de desajustes de API entre versiones.

### Alternativa honesta

La app oficial **SFA** (`SFA-1.14.4-*.apk` de esa misma release) ya es un cliente completo:
VLESS+REALITY, selección por app y always-on. Para el uso diario no hace falta nuestra v1.0;
la nuestra es un proyecto de aprendizaje.

---

## Estado de la compilación de libbox (14 nov, 03:10)

**Herramientas instaladas y funcionando:**

| Pieza | Versión / ruta |
|---|---|
| Go | 1.27.4 (`C:\Program Files\Go`) |
| JDK 17 (Temurin) | `C:\Program Files\Eclipse Adoptium\jdk-17*` |
| JDK 25 (Android Studio) | solo para Gradle, no vale para libbox |
| Android SDK | `C:\Users\KOFY\AppData\Local\Android\Sdk` |
| Android NDK | **r27c** en `E:\PC\vpn\tools\android-ndk-r27c` |
| gomobile (fork SagerNet) | v0.1.12 en `%USERPROFILE%\go\bin` |
| sing-box | v1.14.4 clonado en `E:\PC\vpn\tools\sing-box` |

**Variables de entorno necesarias para compilar:**

```powershell
$env:TMP = $env:TEMP = $env:GOTMPDIR = "E:\PC\vpn\tools\tmp"
$env:CGO_LDFLAGS_ALLOW = ".*"
$env:JAVA_HOME = "<ruta jdk-17>"
$env:ANDROID_HOME = $env:ANDROID_SDK_ROOT = "$env:LOCALAPPDATA\Android\Sdk"
$env:ANDROID_NDK_HOME = $env:ANDROID_NDK_ROOT = "E:\PC\vpn\tools\android-ndk-r27c"
```

**RESUELTO — el AAR ya está compilado** ✅ (14 nov, 03:05)

```
libbox.aar          113.9 MB   4 ABIs
libbox-legacy.aar    94.8 MB
```

Copiado a `app/android-proyecto/app/libs/libbox.aar` y a `app/android/libbox.aar`.

**La receta que funciona** (intentos 1–8 quedan documentados arriba como fallos):

| Pieza | Valor correcto |
|---|---|
| NDK | **r28c** (con r27c el linker rechaza `libcronet.a`) |
| JDK | **17** (Temurin; el 25 de Android Studio no vale) |
| gomobile | fork **SagerNet** v0.1.12 |
| `CGO_LDFLAGS_ALLOW` | `.*` (si no, rechaza `-l:libcronet.a`) |
| `TMP`/`TEMP`/`GOTMPDIR` | dentro del espacio de trabajo (si no, clang no puede escribir) |
| SDK platform | **android-24** instalado (`platform-24_r02.zip` → renombrar `android-7.0` a `android-24`) |

---

## API real de libbox 1.14.4 (extraída del AAR)

**No existe `BoxService`.** El modelo es:

```kotlin
Libbox.setup(SetupOptions().apply {
    basePath = filesDir.absolutePath
    workingPath = ...
    tempPath = cacheDir.absolutePath
    fixAndroidStack = true
})

val server = Libbox.newCommandServer(handler, platformInterface)  // CommandServer
server.start()
server.startOrReloadService(jsonConfig, null)   // aquí arranca sing-box
```

**`PlatformInterface.openTun(TunOptions): Int`** — invertido respecto a lo que esperaba:
**sing-box nos pide el TUN**, y nosotros lo creamos con `VpnService.Builder` y devolvemos
el descriptor (`fd`).

Y el detalle que vale oro: **`TunOptions` trae `getIncludePackage()` / `getExcludePackage()`**.
Es decir, la lista blanca de apps **viaja dentro del JSON de sing-box**
(`"inbound": { "type": "tun", "include_package": [...] }`), no en nuestro código Kotlin.
Nuestra pantalla de apps solo tiene que escribir esos nombres en el JSON.

**Métodos de `PlatformInterface` (26).** Los que importan de verdad:

| Método | Qué hay que hacer |
|---|---|
| `openTun(TunOptions)` | crear el TUN y devolver el fd — **el crítico** |
| `startDefaultInterfaceMonitor` / `closeDefaultInterfaceMonitor` | registrar/liberar el listener |
| `getInterfaces()` | listar interfaces de red |
| `findConnectionOwner(...)` | resolver UID/proceso de una conexión |
| `readWIFIState()` | estado Wi-Fi (puede devolver `null`) |
| `localDNSTransport()` | puede devolver `null` |
| `registerMyInterface(nombre)` | guardar el nombre |
| el resto | `false` / `null` / no-op |

**`CommandServerHandler` (7 métodos).** Casi todos no-op para nuestro caso:
`serviceStop()`, `serviceReload()`, `getSystemProxyStatus()`, `setSystemProxyEnabled()`,
`writeDebugMessage()`, `connectSSHAgent()`, `triggerNativeCrash()`.

---

## Plan de integración (próxima sesión)

1. `app/build.gradle.kts`: `implementation(files("libs/libbox.aar"))`.
2. `PlatformInterfaceImpl`: los 8 métodos de arriba; el resto no-op.
3. `CommandServerHandlerImpl`: no-op salvo `writeDebugMessage` → Logcat.
4. Generar el JSON de sing-box desde el formulario (VLESS+REALITY + `include_package`).
5. `VpnTunnelService`: sustituir el `Builder` propio por `openTun` + `CommandServer`.
6. Compilar, instalar y probar contra Helsinki con `adb`.

---

## Estado de la v1.0 (14 nov, 03:35)

### Lo que YA funciona ✅

| Pieza | Evidencia |
|---|---|
| `libbox.aar` compilado | 113,9 MB, 4 ABIs |
| Enlazado en Gradle | `implementation(files("libs/libbox.aar"))` |
| `Libbox.setup()` + `CommandServer` | `sing-box started (0.22s)` |
| `PlatformInterface.openTun()` | `tun0` con `172.19.0.1/30`, MTU 9000, ruta `0.0.0.0/0` |
| Enumeración de interfaces | `updated available networks: dummy0, eth0, wlan0 (wifi), lo` |
| Monitor de interfaz por defecto | `updated default interface wlan0, index 16` |
| Regla `hijack-dns` | `pre-match[0] port=53 => hijack-dns` |
| **Resolución DNS por el túnel** | `dns: exchanged ipinfo.io NOERROR 249` |

### Lo que FALTA ❌

```
outbound/vless[proxy]: outbound packet connection to ...:443
ERROR connection: ... reality verification failed
```

El handshake REALITY falla. El `pbk` y el `sid` de `vpn-enlace.txt` coinciden con los
que usa la app (comprobado), y el reloj del emulador está correcto (00:33 GMT = 03:33 MSK).

**Siguientes pasos, en orden:**

1. Re-derivar la clave pública en el servidor y compararla carácter a carácter (la
   salida de consola confunde `l/I` y `0/O`):
   ```bash
   PRIV=$(grep -o '"privateKey": *"[^"]*"' /usr/local/etc/xray/config.json | cut -d'"' -f4)
   xray x25519 -i "$PRIV"
   ```
2. Probar el mismo enlace en la app oficial SFA (mismo `libbox`): si SFA tampoco conecta,
   el problema está en los datos; si SFA conecta, está en nuestra configuración.
3. Revisar que el servidor y `vpn-enlace.txt` sigan sincronizados.

### Errores ya resueltos (para no repetirlos)

| Síntoma | Causa | Solución |
|---|---|---|
| `panic` en `StartOrReloadService` | `OverrideOptions` null | pasar `OverrideOptions()` |
| `legacy inbound fields` | `"sniff"` en el inbound | eliminado (es acción de ruta desde 1.11) |
| `panic` en `FindConnectionOwner` | devolvíamos `null` | devolver objeto con `setAndroidPackageNames` |
| `operation not permitted` | falta `INTERNET` en el manifest | añadido |
| `no such network interface` | `getInterfaces()` vacía | enumerar desde Java |
| `panic: ParsePrefix ... no '/'` | direcciones sin CIDR | usar `InterfaceAddress.networkPrefixLength` |
| `missing default interface` | se reportaba `tun0` en vez de `wlan0` | saltar la red VPN y usar la subyacente |
| Sin red por defecto | falta `setUnderlyingNetworks` | llamarlo al reportar la interfaz |

---

## Bloqueador de anuncios (v1.1) — ✅ implementado (14 nov, 04:50)

**Estado:** integrado y verificado hasta donde se puede sin servidor:

- [x] Lista de 95 dominios en `app/android/ads.json` (formato *source*, versión 3)
- [x] Se copia a `assets/` y de ahí a `filesDir/ads.json` al conectar
- [x] Regla `rule_set` + `action: reject` generada en el JSON de sing-box
- [x] Interruptor **"Bloquear anuncios"** en la pantalla principal (por defecto activo)
- [x] `sing-box check` con la regla → **exit 0**
- [x] En el emulador: `files/ads.json` (2.782 B) copiado y el config activo contiene
      `"rule_set":[{"type":"local","tag":"ads",...,"path":".../files/ads.json"}]`

Pendiente de probar contra un servidor sano: que el bloqueo efectivamente corte los
anuncios.

### Qué se puede bloquear y qué no

| Tipo | ¿Bloqueable por DNS? | Por qué |
|---|---|---|
| Banners y pop-ups en webs | **Sí** | vienen de dominios de anuncios propios |
| Anuncios intersticiales de apps | **Sí, en su mayoría** | usan SDKs con dominios conocidos |
| Rastreadores y telemetría | **Sí** | dominio dedicado |
| Anuncios de Google/AdMob | **Sí** (rompe algún servicio de Google) | `googleads.g.doubleclick.net`, etc. |
| **Anuncios dentro de YouTube** | **NO** | el vídeo y el anuncio salen del **mismo** dominio (`googlevideo.com`); el DNS no puede distinguirlos |
| Vídeo pre-roll en webs | **No en general** | mismo CDN que el contenido |

Es el mismo límite que tienen AdGuard, Blokada o Pi-hole. Para quitar los anuncios de
dentro de YouTube hace falta un **cliente modificado** (tipo ReVanced) o la versión web con
un bloqueador de contenido: eso ya no es DNS, es filtrar dentro de la app.

### Implementación (sing-box 1.14)

Nuestra app ya intercepta el DNS, así que el bloqueo es una regla más. Esquema verificado
en `option/rule_set.go`:

```json
{
  "route": {
    "rule_set": [
      {
        "type": "local",
        "tag": "ads",
        "format": "source",
        "path": "<filesDir>/ads.json"
      }
    ],
    "rules": [
      { "port": 53, "action": "hijack-dns" },
      { "rule_set": "ads", "action": "reject" }
    ],
    "final": "proxy",
    "auto_detect_interface": true
  }
}
```

Y el fichero `ads.json` en formato *source*:

```json
{
  "version": 3,
  "rules": [
    { "domain_suffix": ["doubleclick.net", "googlesyndication.com", "adservice.google.com"] }
  ]
}
```

`action: "reject"` corta la conexión sin salir a internet: es más rápido y más limpio que
devolver una IP falsa.

### Origen de la lista

- **Incluida en la app** (offline, ~3.000–5.000 dominios, ~150 KB). Se genera desde
  listas públicas tipo StevenBlack/hosts y se guarda en `assets/ads.json`.
- **Actualizable** (opcional): `"type": "remote"` con `"url"` a una lista `.srs`, y
  `"update_interval"`. Requiere que el usuario acepte descargarla.

### Interfaz

- Interruptor **"Bloquear anuncios"** en Ajustes, activado por defecto.
- Contador de bloqueos sería deseable, pero exige leer los logs de sing-box: fase 2.

### Riesgos

- Bloquear de más rompe apps (pagos, inicios de sesión con Google). Por eso la lista debe
  ser conservadora y el interruptor debe poder apagarse al instante.
- Con `action: reject` el fallo es silencioso: la app afectada se queda esperando. Es el
  comportamiento normal de estos bloqueadores.

---

## Riesgos conocidos
| Riesgo | Detalle | Mitigación |
|---|---|---|
| `QUERY_ALL_PACKAGES` | Android 11+ exige este permiso (o `<queries>`) para listar apps instaladas | Declararlo; solo afecta a publicar en Play Store, no a instalar por APK |
| Always-on + bloqueo | Puede dejar el móvil sin red si la app falla | Probar sin "Block connections without VPN" |
| `libbox` | AAR con JNI, documentación escasa, versiones que rompen | Fijar una versión concreta y no actualizar a ciegas |
| Batería | Servicio en primer plano mal gestionado | Notificación persistente y sin wake-locks innecesarios |
