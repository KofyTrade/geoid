#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  Instala el AGENTE del nodo de GeoiD
#
#  Uso:
#     bash instalar-agente.sh Suecia 10.9.10
#     bash instalar-agente.sh Finlandia 10.9.9 awg0 21766
#
#  Parametros:
#     1) nombre del nodo      (obligatorio)
#     2) prefijo de subred    (obligatorio, por ejemplo 10.9.10)
#     3) interfaz             (por defecto awg0)
#     4) puerto del VPN       (por defecto 21766)
#
#  Genera un token, abre el puerto del agente, permite solo la IP del bot
#  si se indica, y deja el servicio arrancando con el sistema.
# ---------------------------------------------------------------------------
set -eu

NOMBRE="${1:-}"
PREFIJO="${2:-}"
INTERFAZ="${3:-awg0}"
PUERTO_VPN="${4:-21766}"

DESTINO="/opt/geoid-agente"
SERVICIO="/etc/systemd/system/geoid-agente.service"
ENTORNO="/etc/geoid-agente.env"
PUERTO_WEB="8443"

azul()  { printf '\033[1;36m%s\033[0m\n' "$*"; }
verde() { printf '\033[1;32m%s\033[0m\n' "$*"; }
rojo()  { printf '\033[1;31m%s\033[0m\n' "$*"; }

if [ "$(id -u)" -ne 0 ]; then rojo "Ejecutalo como root."; exit 1; fi
if [ -z "$NOMBRE" ] || [ -z "$PREFIJO" ]; then
  rojo "Uso: bash $0 <NombreDelNodo> <prefijo de subred>"
  exit 1
fi

CONF_SERVIDOR="/etc/amnezia/amneziawg/${INTERFAZ}.conf"
if [ ! -f "$CONF_SERVIDOR" ]; then
  rojo "No existe $CONF_SERVIDOR (monta antes el nodo)."
  exit 1
fi

azul "1/5 - Copiando el agente"
mkdir -p "$DESTINO"
if [ -f "/root/agente-nodo.py" ]; then
  cp /root/agente-nodo.py "$DESTINO/agente-nodo.py"
else
  rojo "Falta /root/agente-nodo.py (subelo con curl o scp)."
  exit 1
fi
chmod 700 "$DESTINO"

azul "2/5 - Preparando la configuracion"
if [ -f "$ENTORNO" ] && grep -q "GEOID_NODO_TOKEN=." "$ENTORNO"; then
  verde "   ya existia un token, se conserva"
else
  TOKEN=$(head -c 48 /dev/urandom | base64 | tr -d '/+=' | head -c 48)
  IP_BOT_GUARDADA="${IP_BOT:-}"
  cat > "$ENTORNO" <<EOF
GEOID_NODO_NOMBRE=${NOMBRE}
GEOID_NODO_INTERFAZ=${INTERFAZ}
GEOID_NODO_CONF=${CONF_SERVIDOR}
GEOID_NODO_PUERTO=${PUERTO_VPN}
GEOID_NODO_PREFIJO=${PREFIJO}
GEOID_NODO_DNS=${PREFIJO}.1
GEOID_NODO_MTU=1280
GEOID_NODO_WEB_PUERTO=${PUERTO_WEB}
GEOID_NODO_TOKEN=${TOKEN}
${IP_BOT_GUARDADA:+GEOID_NODO_PERMITIDOS=${IP_BOT_GUARDADA}}
EOF
  chmod 600 "$ENTORNO"
  verde "   token nuevo generado"
fi

azul "3/5 - Creando el servicio"
cat > "$SERVICIO" <<EOF
[Unit]
Description=Agente del nodo GeoiD (${NOMBRE})
After=network-online.target awg-quick@${INTERFAZ}.service
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=${ENTORNO}
ExecStart=/usr/bin/python3 ${DESTINO}/agente-nodo.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable geoid-agente >/dev/null 2>&1 || true
systemctl restart geoid-agente
sleep 2
if ! systemctl is-active --quiet geoid-agente; then
  rojo "El agente no arranco:"
  journalctl -u geoid-agente -n 15 --no-pager
  exit 1
fi
verde "   servicio activo"

azul "4/5 - Abriendo el puerto ${PUERTO_WEB}"
if command -v ufw >/dev/null 2>&1; then
  ufw allow "${PUERTO_WEB}"/tcp >/dev/null 2>&1 || true
fi
iptables -I INPUT -p tcp --dport "$PUERTO_WEB" -j ACCEPT 2>/dev/null || true
verde "   puerto abierto (protegelo con el token y, si puedes, con IP)"

azul "5/5 - Comprobando"
TOKEN_ACTUAL=$(grep '^GEOID_NODO_TOKEN=' "$ENTORNO" | cut -d= -f2-)
RESPUESTA=$(python3 - "$TOKEN_ACTUAL" "$PUERTO_WEB" <<'PY'
import json, sys, urllib.request
token, puerto = sys.argv[1], sys.argv[2]
peticion = urllib.request.Request(
    f"http://127.0.0.1:{puerto}/salud",
    headers={"Authorization": f"Bearer {token}"},
)
try:
    print(urllib.request.urlopen(peticion, timeout=8).read().decode())
except Exception as error:
    print(json.dumps({"error": str(error)}))
PY
)
echo "   respuesta: $RESPUESTA"

if printf '%s' "$RESPUESTA" | grep -q '"nodo"'; then
  verde ""
  verde "================================================================"
  verde " AGENTE DEL NODO ${NOMBRE} LISTO"
  verde "================================================================"
  echo ""
  echo "  Token (guardalo en el bot):"
  echo ""
  echo "  ${TOKEN_ACTUAL}"
  echo ""
  echo "  Servicio : systemctl status geoid-agente"
  echo "  Registro : journalctl -u geoid-agente -n 20 --no-pager"
  verde "================================================================"
else
  rojo "El agente no respondio correctamente. Revisa el registro."
  exit 1
fi
