#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  Prepara el servidor para proxies MTProto PERSONALES (uno por cliente).
#
#  Crea:
#    /etc/mtg/users/                 configuración de cada cliente
#    mtg-user@.service               plantilla systemd (un servicio por cliente)
#
#  Después, el bot crea el proxy de cada cliente que compra 6 meses o más,
#  con su propio puerto y su propia clave.
#
#  Uso:   bash proxy-multiusuario.sh
# ---------------------------------------------------------------------------
set -euo pipefail

BIN="/usr/local/bin/mtg"
CARPETA="/etc/mtg/users"
PLANTILLA="/etc/systemd/system/mtg-user@.service"

azul()  { printf '\033[1;36m%s\033[0m\n' "$*"; }
verde() { printf '\033[1;32m%s\033[0m\n' "$*"; }
rojo()  { printf '\033[1;31m%s\033[0m\n' "$*"; }

if [ "$(id -u)" -ne 0 ]; then
  rojo "Ejecútalo como root."
  exit 1
fi

if [ ! -x "$BIN" ]; then
  rojo "Falta $BIN. Ejecuta antes: bash instalar-proxy-telegram.sh"
  exit 1
fi

azul "1/3 · Creando la carpeta de clientes"
mkdir -p "$CARPETA"
chmod 700 "$CARPETA"
echo "   $CARPETA"

azul "2/3 · Instalando la plantilla de servicio"
cat > "$PLANTILLA" <<'EOF'
[Unit]
Description=Proxy MTProto personal de GeoiD (%i)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/mtg run /etc/mtg/users/%i.toml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
echo "   $PLANTILLA"

azul "3/3 · Abriendo los puertos de los clientes (20000-40000)"
if command -v ufw >/dev/null 2>&1; then
  ufw allow 20000:40000/tcp >/dev/null 2>&1 || true
  echo "   ufw: rango permitido"
else
  echo "   sin ufw: no hay que abrir nada"
fi

verde ""
verde "===================== LISTO ====================="
echo ""
echo "  El bot ya puede crear proxies personales."
echo "  Cada cliente tendrá:"
echo "    · su propio puerto (20000-40000)"
echo "    · su propia clave"
echo "    · máximo 2 dispositivos conectados a la vez"
echo ""
echo "  Comprobar un cliente concreto:"
echo "    systemctl status mtg-user@<ID>"
echo "    ss -tn | grep ':2<xxxx>'"
echo ""
verde "================================================"
