#!/usr/bin/env bash
# Instala el bot en el VPS. Se ejecuta desde la carpeta bot/ como root.
#
#   bash instalar.sh
#
set -euo pipefail

AQUI="$(cd "$(dirname "$0")" && pwd)"
DESTINO="/opt/geoid-bot"
DATOS="/var/lib/geoid-bot"
ENTORNO="/etc/geoid-bot.env"
SERVICIO="/etc/systemd/system/geoid-bot.service"

echo "== paquetes =="
apt-get update -y
apt-get install -y python3 python3-venv python3-pip

echo "== copiando =="
mkdir -p "$DESTINO" "$DATOS"
cp "$AQUI"/*.py "$AQUI/requirements.txt" "$DESTINO/"

echo "== entorno python =="
cd "$DESTINO"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

echo "== configuracion =="
if [ ! -f "$ENTORNO" ]; then
  cat > "$ENTORNO" <<'EOF'
# Token de BotFather
GEOID_TOKEN=
# Tu id de Telegram (para /estado, /promo y /regalar). Lo da @userinfobot
GEOID_ADMIN=0

# Servidor
GEOID_AWG_IF=awg0
GEOID_ENDPOINT=193.29.224.164:21766
GEOID_DNS=10.9.9.1
GEOID_MTU=1280
GEOID_RED=10.9.9.
GEOID_IP_MIN=10
GEOID_IP_MAX=250

# Producto
GEOID_DIAS_PRUEBA=3
GEOID_DIAS_INVITADO=7
GEOID_PRECIO_1M=150
GEOID_PRECIO_3M=400
GEOID_PRECIO_12M=1200
EOF
  chmod 600 "$ENTORNO"
  echo "  creado $ENTORNO -> rellena GEOID_TOKEN y GEOID_ADMIN"
fi

echo "== servicio =="
cat > "$SERVICIO" <<EOF
[Unit]
Description=GeoiD VPN Telegram bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$DESTINO
EnvironmentFile=$ENTORNO
Environment=GEOID_DATOS=$DATOS
ExecStart=$DESTINO/.venv/bin/python bot.py
Restart=always
RestartSec=5
NoNewPrivileges=no
ProtectSystem=full
ReadWritePaths=$DATOS /etc/amnezia/amneziawg

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable geoid-bot >/dev/null
echo
echo "Listo."
echo "1) edita $ENTORNO  (token y tu id)"
echo "2) systemctl restart geoid-bot"
echo "3) journalctl -u geoid-bot -f    (para ver que arranca bien)"
