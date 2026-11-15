# GeoiD-vpn para Windows

## Instalar

1. Descarga `GeoiD-vpn-windows.zip` desde
   <https://github.com/KofyTrade/geoid/releases/latest>
2. Descomprímelo donde quieras (por ejemplo `C:\GeoiD-vpn`). No hay instalador:
   no toca el registro ni deja servicios.
3. Ejecuta **GeoiD-vpn.exe**.
4. Windows pedirá **permisos de administrador**: acéptalos. Son necesarios para
   crear el adaptador de red virtual (controlador Wintun) y configurar las rutas.

## Usar

1. **Perfiles** → **+** → pega el contenido del `.conf` → **Guardar**
2. **Conectar**

El estado cambia a **CONECTADO** y el polihedro empieza a girar. Verás la
velocidad y la latencia en la esquina superior derecha.

Para desconectar, pulsa **Desconectar** (o cierra la app: el túnel se cierra solo).

## Qué contiene el paquete

| Fichero | Para qué |
|---|---|
| `GeoiD-vpn.exe` | La aplicación (interfaz Flutter) |
| `geoid-tun.exe` | El motor: AmneziaWG + adaptador Wintun |
| `wintun.dll` | Controlador oficial de WireGuard (firmado por WireGuard LLC) |
| `flutter_windows.dll`, `data\` | Motor de Flutter y recursos |

## Si algo falla

El motor escribe un registro en **`geoid-tun.log`**, en la misma carpeta que el
ejecutable. Las líneas más habituales:

- `hacen falta permisos de administrador` → abre la app con *Ejecutar como
  administrador*.
- `configuracion incompleta` → el `.conf` no tiene `[Interface]`/`[Peer]` o le
  falta la clave.
- `wintun.dll` no encontrado → el zip no se descomprimió entero; vuelve a
  descomprimirlo en una carpeta propia.

## Aviso

La app no se ha firmado con un certificado de pago, así que SmartScreen puede
avisar la primera vez: *Más información* → *Ejecutar de todas formas*.

## Cómo se construye

Cada cambio en `flutter_app/` lanza GitHub Actions:

1. clona `amnezia-vpn/amneziawg-go` y compila `geoid-tun.exe` para Windows
2. descarga `wintun.dll` de wintun.net
3. compila la app con Flutter
4. empaqueta todo en `GeoiD-vpn-windows.zip`

El proceso está en `.github/workflows/flutter-windows.yml`.
