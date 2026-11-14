# ---------------------------------------------------------------------------
#  instalar-codigo.ps1
#
#  Copia las plantillas de esta carpeta (app\android) al proyecto de Android
#  Studio y deja Gradle y el manifiesto listos.
#
#  Uso:
#     powershell -ExecutionPolicy Bypass -File instalar-codigo.ps1 `
#                -Proyecto "E:\PC\vpn\app\android-proyecto"
#
#  Es idempotente: se puede ejecutar tantas veces como haga falta.
# ---------------------------------------------------------------------------
param(
    [Parameter(Mandatory = $true)]
    [string]$Proyecto
)

$ErrorActionPreference = 'Stop'

function Fallar([string]$mensaje) {
    Write-Host ""
    Write-Host "  [ERROR] $mensaje" -ForegroundColor Red
    Write-Host ""
    exit 1
}

function Ok([string]$mensaje) {
    Write-Host "  [OK] $mensaje" -ForegroundColor Green
}

function Nota([string]$mensaje) {
    Write-Host "  $mensaje" -ForegroundColor DarkGray
}

$utf8SinBom = New-Object System.Text.UTF8Encoding($false)

# --------------------------------------------------------------- comprobacion
$raiz = Join-Path $Proyecto 'app'
if (-not (Test-Path -LiteralPath (Join-Path $Proyecto 'settings.gradle.kts'))) {
    Fallar "No parece un proyecto Android Studio: $Proyecto"
}

$java = Join-Path (Join-Path (Join-Path $raiz 'src\main') 'java') 'com\geoid\vpn'
$res = Join-Path (Join-Path $raiz 'src\main') 'res'
$manifiesto = Join-Path (Join-Path $raiz 'src\main') 'AndroidManifest.xml'

Write-Host ""
Write-Host "  Instalando codigo en: $Proyecto" -ForegroundColor Cyan
Write-Host ""

New-Item -ItemType Directory -Force -Path $java | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $res 'layout') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $res 'drawable') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $res 'color') | Out-Null

# ------------------------------------------------------------------ Kotlin
foreach ($kt in Get-ChildItem -Path $PSScriptRoot -Filter *.kt) {
    Copy-Item -LiteralPath $kt.FullName -Destination (Join-Path $java $kt.Name) -Force
    Ok $kt.Name
}

# --------------------------------------------------------------------- XML
$layouts = @('activity_main.xml', 'activity_apps.xml', 'item_app.xml', 'activity_perfiles.xml', 'item_perfil.xml', 'activity_importar.xml')
foreach ($x in $layouts) {
    $origen = Join-Path $PSScriptRoot $x
    if (Test-Path -LiteralPath $origen) {
        Copy-Item -LiteralPath $origen -Destination (Join-Path (Join-Path $res 'layout') $x) -Force
        Ok "layout/$x"
    }
}

$drawables = @('bg_busqueda.xml', 'fondo_etiqueta.xml')
foreach ($x in $drawables) {
    $origen = Join-Path $PSScriptRoot $x
    if (Test-Path -LiteralPath $origen) {
        Copy-Item -LiteralPath $origen -Destination (Join-Path (Join-Path $res 'drawable') $x) -Force
        Ok "drawable/$x"
    }
}

$colores = @('switch_thumb.xml', 'switch_track.xml')
foreach ($x in $colores) {
    $origen = Join-Path $PSScriptRoot $x
    if (Test-Path -LiteralPath $origen) {
        Copy-Item -LiteralPath $origen -Destination (Join-Path (Join-Path $res 'color') $x) -Force
        Ok "color/$x"
    }
}

# ---------------------------------------------------------------- temas
New-Item -ItemType Directory -Force -Path (Join-Path $res 'values') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $res 'values-night') | Out-Null

$temaClaro = Join-Path $PSScriptRoot 'themes.xml'
if (Test-Path -LiteralPath $temaClaro) {
    Copy-Item -LiteralPath $temaClaro -Destination (Join-Path (Join-Path $res 'values') 'themes.xml') -Force
    Ok 'values/themes.xml'
}

$temaOscuro = Join-Path $PSScriptRoot 'themes-night.xml'
if (Test-Path -LiteralPath $temaOscuro) {
    Copy-Item -LiteralPath $temaOscuro -Destination (Join-Path (Join-Path $res 'values-night') 'themes.xml') -Force
    Ok 'values-night/themes.xml'
}

# ---------------------------------------------------------------- idiomas
$carpetaIdiomas = Join-Path $PSScriptRoot 'strings'
if (Test-Path -LiteralPath $carpetaIdiomas) {
    foreach ($idioma in Get-ChildItem -LiteralPath $carpetaIdiomas -Directory) {
        $destinoIdioma = Join-Path $res $idioma.Name
        New-Item -ItemType Directory -Force -Path $destinoIdioma | Out-Null
        $archivoIdioma = Join-Path $idioma.FullName 'strings.xml'
        if (Test-Path -LiteralPath $archivoIdioma) {
            Copy-Item -LiteralPath $archivoIdioma -Destination (Join-Path $destinoIdioma 'strings.xml') -Force
            Ok ("idioma: " + $idioma.Name)
        }
    }
}

# ------------------------------------------------------- icono adaptativo
$fondoIcono = Join-Path $PSScriptRoot 'ic_launcher_fondo.xml'
if (Test-Path -LiteralPath $fondoIcono) {
    Copy-Item -LiteralPath $fondoIcono -Destination (Join-Path (Join-Path $res 'drawable') 'ic_launcher_fondo.xml') -Force
    Ok 'drawable/ic_launcher_fondo.xml'
}

$iconoAdaptativo = Join-Path $PSScriptRoot 'ic_launcher.xml'
if (Test-Path -LiteralPath $iconoAdaptativo) {
    $anydpi = Join-Path $res 'mipmap-anydpi-v26'
    New-Item -ItemType Directory -Force -Path $anydpi | Out-Null
    Copy-Item -LiteralPath $iconoAdaptativo -Destination (Join-Path $anydpi 'ic_launcher.xml') -Force
    Copy-Item -LiteralPath $iconoAdaptativo -Destination (Join-Path $anydpi 'ic_launcher_round.xml') -Force
    Ok 'mipmap-anydpi-v26/ic_launcher.xml (+ round)'
}

if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'generar.py')) {
    Nota 'los PNG del icono se generan con:  python app\icono\generar.py'
}

# --------------------------------------------------------------------- AAR
$aar = Join-Path $PSScriptRoot 'awg.aar'
if (Test-Path -LiteralPath $aar) {
    $libs = Join-Path $raiz 'libs'
    New-Item -ItemType Directory -Force -Path $libs | Out-Null
    $destinoAar = Join-Path $libs 'awg.aar'
    Copy-Item -LiteralPath $aar -Destination $destinoAar -Force
    Ok ("libs/awg.aar (" + [math]::Round((Get-Item -LiteralPath $destinoAar).Length / 1MB, 1) + " MB)")
}

# ------------------------------------------------------------------ Gradle
$gradle = Get-ChildItem -Path $raiz -Filter 'build.gradle.kts' -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($gradle) {
    $g = [System.IO.File]::ReadAllText($gradle.FullName, [System.Text.Encoding]::UTF8)

    if ($g -notmatch 'libs/awg\.aar') {
        $pos = $g.IndexOf('dependencies {')
        if ($pos -ge 0) {
            $g = $g.Insert($pos + 'dependencies {'.Length,
                "`n    implementation(files(`"libs/awg.aar`"))")
            [System.IO.File]::WriteAllText($gradle.FullName, $g, $utf8SinBom)
            Ok 'build.gradle.kts: + awg.aar'
        }
    } else {
        Nota 'Gradle ya enlaza awg.aar'
    }

    # libbox (sing-box) queda aparcado: si sigue enlazado, se quita.
    $g2 = [System.IO.File]::ReadAllText($gradle.FullName, [System.Text.Encoding]::UTF8)
    if ($g2 -match 'libs/libbox\.aar') {
        $g2 = $g2 -replace '(?m)^\s*implementation\(files\("libs/libbox\.aar"\)\)\s*$', ''
        [System.IO.File]::WriteAllText($gradle.FullName, $g2, $utf8SinBom)
        Ok 'build.gradle.kts: - libbox.aar (aparcado)'
    }
}

# --------------------------------------------------------------- manifiesto
$xmlMan = [System.IO.File]::ReadAllText($manifiesto, [System.Text.Encoding]::UTF8)
$cambiado = $false

$permisos = @(
    'android.permission.INTERNET',
    'android.permission.ACCESS_NETWORK_STATE',
    'android.permission.FOREGROUND_SERVICE',
    'android.permission.FOREGROUND_SERVICE_SPECIAL_USE',
    'android.permission.POST_NOTIFICATIONS'
)
foreach ($p in $permisos) {
    if ($xmlMan -notmatch [regex]::Escape($p)) {
        $xmlMan = $xmlMan.Replace(
            '<application',
            ('    <uses-permission android:name="' + $p + '" />' + "`n`n    <application")
        )
        $cambiado = $true
        Ok "permiso: $p"
    }
}

if ($xmlMan -notmatch 'WRITE_EXTERNAL_STORAGE') {
    $xmlMan = $xmlMan.Replace(
        '<application',
        ('    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"' +
         ' android:maxSdkVersion="28" />' + "`n`n    <application")
    )
    $cambiado = $true
    Ok 'permiso: WRITE_EXTERNAL_STORAGE (solo hasta Android 9)'
}

if ($xmlMan -notmatch 'AppsActivity') {
    $actividad = @"
        <activity
            android:name=".AppsActivity"
            android:exported="false" />

"@
    $idx = $xmlMan.IndexOf('</application>')
    if ($idx -lt 0) { Fallar 'No encuentro </application> en el manifiesto.' }
    $xmlMan = $xmlMan.Insert($idx, $actividad)
    $cambiado = $true
    Ok 'manifiesto: + AppsActivity'
}

if ($xmlMan -notmatch 'PerfilesActivity') {
    $actividadPerfiles = @"
        <activity
            android:name=".PerfilesActivity"
            android:exported="false" />

"@
    $idx = $xmlMan.IndexOf('</application>')
    if ($idx -lt 0) { Fallar 'No encuentro </application> en el manifiesto.' }
    $xmlMan = $xmlMan.Insert($idx, $actividadPerfiles)
    $cambiado = $true
    Ok 'manifiesto: + PerfilesActivity'
}

if ($xmlMan -notmatch 'ImportarActivity') {
    $importar = @"
        <activity
            android:name=".ImportarActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.SEND" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:mimeType="text/plain" />
                <data android:mimeType="application/octet-stream" />
                <data android:mimeType="application/x-wireguard-conf" />
                <data android:mimeType="text/x-conf" />
                <data android:mimeType="application/x-conf" />
                <data android:mimeType="application/conf" />
                <data android:mimeType="text/*" />
            </intent-filter>
            <intent-filter>
                <action android:name="android.intent.action.VIEW" />
                <category android:name="android.intent.category.DEFAULT" />
                <category android:name="android.intent.category.BROWSABLE" />
                <data android:scheme="content" android:mimeType="text/plain" />
                <data android:scheme="content" android:mimeType="application/octet-stream" />
                <data android:scheme="content" android:mimeType="text/x-conf" />
                <data android:scheme="content" android:mimeType="application/x-conf" />
                <data android:scheme="content" android:mimeType="application/conf" />
                <data android:scheme="file" android:mimeType="text/plain" />
                <data android:scheme="file" android:mimeType="application/octet-stream" />
                <data android:scheme="file" android:mimeType="text/x-conf" />
                <data android:scheme="file" android:mimeType="application/x-conf" />
            </intent-filter>
            <intent-filter>
                <action android:name="android.intent.action.VIEW" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:scheme="content" android:mimeType="*/*" android:pathPattern=".*\\.conf" />
                <data android:scheme="file" android:mimeType="*/*" android:pathPattern=".*\\.conf" />
            </intent-filter>
        </activity>

"@
    $idx = $xmlMan.IndexOf('</application>')
    if ($idx -lt 0) { Fallar 'No encuentro </application> en el manifiesto.' }
    $xmlMan = $xmlMan.Insert($idx, $importar)
    $cambiado = $true
    Ok 'manifiesto: + ImportarActivity (abrir/compartir .conf)'
}

if ($xmlMan -notmatch 'AwgTunnelService') {
    $servicio = @"
        <service
            android:name=".AwgTunnelService"
            android:exported="false"
            android:permission="android.permission.BIND_VPN_SERVICE"
            android:foregroundServiceType="specialUse">
            <intent-filter>
                <action android:name="android.net.VpnService" />
            </intent-filter>
            <property
                android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE"
                android:value="vpn" />
        </service>

"@
    $idx = $xmlMan.IndexOf('</application>')
    if ($idx -lt 0) { Fallar 'No encuentro </application> en el manifiesto.' }
    $xmlMan = $xmlMan.Insert($idx, $servicio)
    $cambiado = $true
    Ok 'manifiesto: + AwgTunnelService'
}

# El servicio de sing-box, fuera.
if ($xmlMan -match 'android:name="\.VpnTunnelService"') {
    $idx = $xmlMan.IndexOf('android:name=".VpnTunnelService"')
    $ini = $xmlMan.LastIndexOf('<service', $idx)
    $fin = $xmlMan.IndexOf('</service>', $idx) + '</service>'.Length
    $xmlMan = $xmlMan.Remove($ini, $fin - $ini)
    $cambiado = $true
    Ok 'manifiesto: - VpnTunnelService (aparcado)'
}

if ($cambiado) {
    [System.IO.File]::WriteAllText($manifiesto, $xmlMan, $utf8SinBom)
}

Write-Host ""
Write-Host "  Listo. Ahora:" -ForegroundColor Cyan
Write-Host "    cd `"$Proyecto`""
Write-Host "    .\gradlew.bat assembleDebug"
Write-Host ""
Write-Host "  APK: app\build\outputs\apk\debug\app-debug.apk"
Write-Host ""
