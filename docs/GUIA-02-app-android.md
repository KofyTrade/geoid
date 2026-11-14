# Guía 02 — La app Android (v0.2)

**Objetivo:** app nativa en Kotlin que valida y genera enlaces `vless://`.
**Tiempo:** 30–45 min (la mayor parte son descargas).
**Requisitos:** Windows 10/11, ~4 GB libres, conexión estable.

> Esta guía la puedes seguir otro día con calma. El código ya está escrito:
> [`MainActivity.kt`](android/MainActivity.kt) y [`activity_main.xml`](android/activity_main.xml).

---

## Paso 1 — Instalar Android Studio

Abre **PowerShell** y ejecuta:

```powershell
winget install -e --id Google.AndroidStudio
```

- Son ~1,2 GB. Windows pedirá permiso (UAC) → **Sí**.
- Si `winget` falla, descárgalo a mano: <https://developer.android.com/studio>

---

## Paso 2 — Primer arranque

1. Si pregunta por importar ajustes → **Do not import settings**.
2. **Setup Wizard** → elige **Standard** → Next.
3. Acepta las licencias → Finish. Descargará el SDK (~1–2 GB).
4. Espera a que termine sin cerrar la ventana.

---

## Paso 3 — Crear el proyecto

**New Project** → elige **Empty Views Activity**.

> ⚠️ Importante: **Views**, no "Empty Activity" (esa es Compose y no nos sirve).

| Campo | Valor |
|---|---|
| **Name** | `VlessGen` |
| **Package name** | `com.kofy.vlessgen` |
| **Save location** | `E:\PC\vpn\app\android-proyecto` |
| **Language** | `Kotlin` |
| **Minimum SDK** | `API 24` |
| **Build configuration language** | `Kotlin DSL` |

Pulsa **Finish** y espera a que la barra de abajo diga **Gradle sync finished**.

---

## Paso 4 — Inyectar el código (lo hace un script)

En **PowerShell** (sustituye la ruta si elegiste otra):

```powershell
powershell -ExecutionPolicy Bypass -File "E:\PC\vpn\app\android\instalar-codigo.ps1" -Proyecto "E:\PC\vpn\app\android-proyecto"
```

**Qué deberías ver:**

```
Proyecto : E:\PC\vpn\app\android-proyecto
Paquete  : com.kofy.vlessgen
  [OK] MainActivity.kt
  [OK] activity_main.xml
Listo. Vuelve a Android Studio y pulsa Run (triangulo verde).
```

El script detecta el nombre del paquete, escribe el código con el `package` correcto y
guarda copias `.bak` de lo que reemplaza.

---

## Paso 5 — Ejecutar

**Opción A — emulador** (más simple, pero descarga ~1,5 GB más):
arriba, en el desplegable de dispositivos → **Device Manager** → **Create device** →
Pixel 7 → API 34 → Finish. Luego pulsa **▶ Run**.

**Opción B — tu móvil por USB** (más rápido y prueba en hardware real):
1. En el móvil: Ajustes → Información del teléfono → pulsa 7 veces en *Número de compilación*.
2. Ajustes → Opciones de desarrollador → activa **Depuración USB**.
3. Conecta el cable y acepta el aviso en el móvil.
4. El teléfono aparecerá en el desplegable de Android Studio → **▶ Run**.

---

## Paso 6 — Probar

Abre tu `vpn-enlace.txt`, copia los datos a la app y comprueba:

- Con los datos correctos → **"Datos correctos"** en verde y el enlace abajo.
- Si borras un carácter de la clave pública → **"debe tener 43 caracteres"** en rojo.
- Botón **Copiar enlace** → pega en v2rayNG con *Import from clipboard*.

---

## Problemas típicos

| Síntoma | Causa | Solución |
|---|---|---|
| `Unresolved reference: AppCompatActivity` | El proyecto es Compose | Crea otro con **Empty Views Activity** |
| `Gradle sync failed` por red | Descargas bloqueadas o lentas | Reintenta; o cambia el DNS del PC a `1.1.1.1` |
| El emulador va a 2 fps | Virtualización desactivada | Usa el móvil por USB, es mejor prueba |
| `Execution policy` al lanzar el script | Política de PowerShell | Usa el comando tal cual, con `-ExecutionPolicy Bypass` |
| La app compila pero sale en blanco | Layout no copiado | Vuelve a ejecutar el script del Paso 4 |

---

## Qué falta para la v1.0 (cliente VPN real)

La v0.2 solo **gestiona** enlaces; no crea el túnel. Para eso hará falta:

1. `VpnService` + permiso `BIND_VPN_SERVICE` en el manifiesto.
2. Servicio en primer plano con notificación persistente.
3. Integrar **sing-box** (`libbox.aar`) como motor del túnel.
4. Leer la configuración de sing-box en JSON a partir de los datos del formulario.

Eso es un proyecto aparte, con iteración real y pruebas en el teléfono.
