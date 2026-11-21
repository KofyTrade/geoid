#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  Instala el respaldo automatico del bot y lo envia al servidor de respaldo
#
#  Uso (en el servidor de Finlandia):
#     bash instalar-respaldo.sh                          -> respaldo a Suecia
#     bash instalar-respaldo.sh root@OTRA_IP /otra/ruta   -> otro destino
#
#  Antes de nada crea una llave SSH y te dice que pegar en el otro servidor.
# ---------------------------------------------------------------------------
set -eu

REMOTO="${1:-root@194.76.136.210}"
CARPETA="${2:-/root/respaldos-finlandia}"
LLAVE="/root/.ssh/id_ed25519"
SCRIPT="/usr/local/bin/geoid-respaldo.sh"
SERVICIO="/etc/systemd/system/geoid-respaldo.service"
TEMPORIZADOR="/etc/systemd/system/geoid-respaldo.timer"

azul()  { printf '\033[1;36m%s\033[0m\n' "$*"; }
verde() { printf '\033[1;32m%s\033[0m\n' "$*"; }
rojo()  { printf '\033[1;31m%s\033[0m\n' "$*"; }

if [ "$(id -u)" -ne 0 ]; then rojo "Ejecutalo como root."; exit 1; fi

azul "1/5 - Preparando la llave SSH"
mkdir -p /root/.ssh && chmod 700 /root/.ssh
if [ ! -f "$LLAVE" ]; then
  ssh-keygen -t ed25519 -N "" -f "$LLAVE" -C "geoid-respaldo" >/dev/null
  verde "   llave creada"
else
  verde "   la llave ya existia"
fi

if ! ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -i "$LLAVE" "$REMOTO" true 2>/dev/null; then
  rojo ""
  rojo "==============================================================================="
  rojo " FALTA AUTORIZAR ESTA LLAVE EN EL OTRO SERVIDOR"
  rojo "==============================================================================="
  echo ""
  echo " 1) Copia esta linea entera:"
  echo ""
  cat "${LLAVE}.pub"
  echo ""
  echo " 2) Pegala en el servidor de respaldo ($REMOTO) con este comando:"
  echo ""
  echo "    mkdir -p /root/.ssh && chmod 700 /root/.ssh"
  echo "    echo 'AQUI_LA_LLAVE' >> /root/.ssh/authorized_keys"
  echo "    chmod 600 /root/.ssh/authorized_keys"
  echo ""
  echo " 3) Vuelve aqui y ejecuta otra vez:  bash $0 $REMOTO $CARPETA"
  echo ""
  rojo "==============================================================================="
  exit 1
fi
verde "   conexion con $REMOTO correcta"

azul "2/5 - Copiando el script de respaldo"
if [ -f /root/respaldo-bot.sh ]; then
  cp /root/respaldo-bot.sh "$SCRIPT"
else
  rojo "   falta /root/respaldo-bot.sh (subelo con curl o scp)"
  exit 1
fi
chmod 700 "$SCRIPT"
verde "   instalado en $SCRIPT"

azul "3/5 - Creando el servicio y el temporizador"
cat > "$SERVICIO" <<EOF
[Unit]
Description=Respaldo del bot de GeoiD

[Service]
Type=oneshot
Environment=GEOID_RESPALDO_REMOTO=${REMOTO}
Environment=GEOID_RESPALDO_CARPETA=${CARPETA}
ExecStart=${SCRIPT}
EOF

cat > "$TEMPORIZADOR" <<'EOF'
[Unit]
Description=Respaldo diario del bot de GeoiD

[Timer]
OnCalendar=*-*-* 03:30:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now geoid-respaldo.timer >/dev/null 2>&1 || true
verde "   respaldo diario a las 03:30"

azul "4/5 - Primer respaldo (prueba real)"
if "$SCRIPT"; then
  verde "   el primer respaldo funciono"
else
  rojo "   el respaldo fallo; revisa los mensajes de arriba"
  exit 1
fi

azul "5/5 - Resumen"
verde ""
verde "==============================================================================="
verde " RESPALDO AUTOMATICO CONFIGURADO"
verde "==============================================================================="
echo ""
echo "  Origen  : $(hostname) ($(curl -fsSL https://api.ipify.org 2>/dev/null || echo '?'))"
echo "  Destino : ${REMOTO}:${CARPETA}"
echo "  Horario : todos los dias a las 03:30"
echo "  Copias  : 7 dias (local y remoto)"
echo ""
echo "  Ver estado : systemctl list-timers geoid-respaldo"
echo "  Ejecutar   : systemctl start geoid-respaldo"
echo "  Registro   : journalctl -u geoid-respaldo -n 30"
echo ""
verde "==============================================================================="
