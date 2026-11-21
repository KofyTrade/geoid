#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  Deja el bot INSTALADO Y PARADO en el servidor de respaldo (Suecia)
#
#  Se ejecuta en FINLANDIA. Copia el codigo, crea el entorno de Python y
#  deja el servicio creado pero desactivado, listo para arrancar en un
#  momento si Finlandia falla.
#
#  Uso:  bash instalar-espera.sh
# ---------------------------------------------------------------------------
set -eu

DESTINO="${GEOID_RESPALDO_REMOTO:-root@194.76.136.210}"
LLAVE="/root/.ssh/id_ed25519"
ORIGEN="/opt/geoid-bot"

azul()  { printf '\033[1;36m%s\033[0m\n' "$*"; }
verde() { printf '\033[1;32m%s\033[0m\n' "$*"; }
rojo()  { printf '\033[1;31m%s\033[0m\n' "$*"; }

if [ "$(id -u)" -ne 0 ]; then rojo "Ejecutalo como root."; exit 1; fi
if [ ! -f "$LLAVE" ]; then rojo "Falta la llave SSH de respaldo."; exit 1; fi
if [ ! -d "$ORIGEN" ]; then rojo "No existe $ORIGEN."; exit 1; fi

SSH="ssh -o StrictHostKeyChecking=no -i $LLAVE $DESTINO"
RSYNC="rsync -az -e \"ssh -o StrictHostKeyChecking=no -i $LLAVE\""

azul "1/5 - Comprobando la conexion"
if ! $SSH true 2>/dev/null; then
  rojo "No se puede conectar con $DESTINO"
  exit 1
fi
verde "   conexion correcta"

azul "2/5 - Copiando el codigo del bot"
$SSH "mkdir -p /opt/geoid-bot"
eval "$RSYNC $ORIGEN/'*.py' $DESTINO:/opt/geoid-bot/"
if [ -f "$ORIGEN/requirements.txt" ]; then
  eval "$RSYNC $ORIGEN/requirements.txt $DESTINO:/opt/geoid-bot/"
fi
$SSH "ls /opt/geoid-bot/*.py | wc -l"
verde "   codigo copiado"

azul "3/5 - Preparando Python en el servidor de respaldo"
$SSH 'export DEBIAN_FRONTEND=noninteractive
      apt-get update -qq
      apt-get install -y -qq python3-venv python3-pip rsync >/dev/null 2>&1
      cd /opt/geoid-bot
      if [ ! -d .venv ]; then python3 -m venv .venv; fi
      ./.venv/bin/pip install --quiet --upgrade pip >/dev/null 2>&1
      ./.venv/bin/pip install --quiet aiogram "cryptography>=42" aiohttp >/dev/null 2>&1
      ./.venv/bin/python -c "import aiogram; print(\"aiogram\", aiogram.__version__)"'
verde "   entorno listo"

azul "4/5 - Creando el servicio (desactivado)"
$SSH 'cat > /etc/systemd/system/geoid-bot.service <<"EOF"
[Unit]
Description=GeoiD VPN Telegram bot (espera)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/geoid-bot
EnvironmentFile=/etc/geoid-bot.env
ExecStart=/opt/geoid-bot/.venv/bin/python /opt/geoid-bot/bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl disable geoid-bot >/dev/null 2>&1 || true
systemctl stop geoid-bot >/dev/null 2>&1 || true
echo "estado: $(systemctl is-enabled geoid-bot 2>&1) / $(systemctl is-active geoid-bot 2>&1)"'
verde "   servicio creado y parado"

azul "5/5 - Comprobando que el codigo arrancaria bien"
$SSH 'cd /opt/geoid-bot
set -a; . /etc/geoid-bot.env 2>/dev/null || true; set +a
./.venv/bin/python -c "
import ast, pathlib
for f in pathlib.Path(\".\").glob(\"*.py\"):
    ast.parse(f.read_text(encoding=\"utf-8\"))
print(\"sintaxis correcta en\", len(list(pathlib.Path(\".\").glob(\"*.py\"))), \"archivos\")
"' || rojo "   revisa el resultado de arriba"

verde ""
verde "==============================================================================="
verde " BOT EN ESPERA PREPARADO EN $(echo "$DESTINO" | cut -d@ -f2)"
verde "==============================================================================="
echo ""
echo "  Ahora mismo NO esta corriendo (correcto: dos bots a la vez se pelean)."
echo ""
echo "  DIA DEL RESCATE (si Finlandia cae), en el servidor de respaldo:"
echo ""
echo "     gunzip -c \$(ls -t /root/respaldos-finlandia/bot-*.sqlite.gz | head -1) \\"
echo "       > /var/lib/geoid-bot/bot.sqlite"
echo "     cp \$(ls -t /root/respaldos-finlandia/geoid-bot-*.env | head -1) /etc/geoid-bot.env"
echo "     systemctl enable --now geoid-bot"
echo ""
echo "  Y si Finlandia revive: en Suecia  ->  systemctl disable --now geoid-bot"
echo ""
verde "==============================================================================="
