#!/usr/bin/env bash
# =============================================================================
#  Instalador: Xray-core + VLESS + XTLS-Vision + REALITY
#  Probado en Ubuntu 22.04 / 24.04 (x86_64 y arm64)
#
#  Uso:   sudo bash instalar-xray-reality.sh
#
#  Al terminar imprime un enlace "vless://..." que es TU credencial.
#  Guardalo. Tambien queda copiado en /root/vpn-enlace.txt
# =============================================================================

set -euo pipefail

# ------------------------- Ajustes editables --------------------------------
PUERTO=443
DESTINO="www.microsoft.com:443"   # sitio real que imitamos (necesita TLS 1.3 + H2)
SNI="www.microsoft.com"
ETIQUETA="mi-vps"                 # nombre visible en el cliente
# ----------------------------------------------------------------------------

ROJO=$'\e[31m'; VERDE=$'\e[32m'; AMARILLO=$'\e[33m'; AZUL=$'\e[34m'; FIN=$'\e[0m'
info()  { echo "${AZUL}==>${FIN} $*"; }
ok()    { echo "${VERDE}[OK]${FIN} $*"; }
aviso() { echo "${AMARILLO}[AVISO]${FIN} $*"; }
error() { echo "${ROJO}[ERROR]${FIN} $*" >&2; }

if [[ $EUID -ne 0 ]]; then
  error "Ejecuta con sudo:  sudo bash $0"
  exit 1
fi

# --- 1. Dependencias --------------------------------------------------------
info "1/6 Instalando dependencias..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y >/dev/null 2>&1 || apt-get update -y || aviso "apt update fallo; continuo igualmente"
apt-get install -y curl openssl ca-certificates >/dev/null 2>&1 \
  || apt-get install -y curl openssl ca-certificates
if ! apt-get install -y qrencode >/dev/null 2>&1; then
  aviso "qrencode no disponible: no habra QR, pero el enlace de texto si."
fi
ok "Dependencias listas"

# --- 2. Xray-core -----------------------------------------------------------
info "2/6 Instalando Xray-core..."
if command -v xray >/dev/null 2>&1; then
  ok "Xray ya estaba instalado: $(xray version | head -n1)"
else
  bash -c "$(curl -fsSL https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
  ok "Xray instalado: $(xray version | head -n1)"
fi

# --- 3. Credenciales --------------------------------------------------------
info "3/6 Generando UUID, claves x25519 y shortId..."
UUID="$(xray uuid)"
# Quitamos posibles codigos de color ANSI antes de parsear la salida.
KEYS="$(xray x25519 | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g')"
# La salida de 'xray x25519' cambia de formato entre versiones:
#   "Private key: xxx / Public key: xxx"      (Xray antiguo)
#   "PrivateKey: xxx / Password: xxx / Hash32: xxx"  (Xray 25+/26+)
PRIV_KEY="$(printf '%s\n' "$KEYS" | awk 'tolower($1) ~ /private/ {print $NF; exit}' | tr -d '[:space:]')"
# Tomamos SOLO la primera linea que coincida, para no encadenar dos claves.
PUB_KEY="$(printf '%s\n' "$KEYS" | awk 'tolower($1) ~ /(public|password)/ {print $NF; exit}' | tr -d '[:space:]')"
if [[ -n "${PRIV_KEY}" && -z "${PUB_KEY}" ]]; then
  PUB_KEY="$(xray x25519 -i "${PRIV_KEY}" | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g' \
    | awk 'tolower($1) ~ /(public|password)/ {print $NF; exit}' | tr -d '[:space:]')"
fi
SHORT_ID="$(openssl rand -hex 8)"

# Una clave x25519 valida siempre mide 43 caracteres. Si no, algo fallo.
if [[ ${#PRIV_KEY} -ne 43 || ${#PUB_KEY} -ne 43 ]]; then
  error "Formato de claves inesperado (priv=${#PRIV_KEY}, pub=${#PUB_KEY} caracteres; se esperaban 43 y 43)."
  error "Salida de 'xray x25519':"
  printf '%s\n' "$KEYS"
  exit 1
fi
ok "Credenciales generadas"

IP_PUBLICA="$(curl -fsS4 --max-time 10 https://api.ipify.org \
              || curl -fsS4 --max-time 10 https://ifconfig.me \
              || hostname -I | awk '{print $1}')"
ok "IP publica detectada: ${IP_PUBLICA}"

# --- 4. Configuracion -------------------------------------------------------
info "4/6 Escribiendo /usr/local/etc/xray/config.json ..."
mkdir -p /usr/local/etc/xray
cat > /usr/local/etc/xray/config.json <<EOF
{
  "log": { "loglevel": "warning" },
  "inbounds": [
    {
      "listen": "0.0.0.0",
      "port": ${PUERTO},
      "protocol": "vless",
      "settings": {
        "clients": [
          { "id": "${UUID}", "flow": "xtls-rprx-vision" }
        ],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "show": false,
          "dest": "${DESTINO}",
          "xver": 0,
          "serverNames": [ "${SNI}" ],
          "privateKey": "${PRIV_KEY}",
          "shortIds": [ "${SHORT_ID}" ]
        }
      },
      "sniffing": {
        "enabled": true,
        "destOverride": [ "http", "tls", "quic" ],
        "routeOnly": true
      }
    }
  ],
  "outbounds": [
    { "protocol": "freedom", "tag": "direct" },
    { "protocol": "blackhole", "tag": "block" }
  ],
  "routing": {
    "rules": [
      { "type": "field", "ip": [ "geoip:private" ], "outboundTag": "block" }
    ]
  }
}
EOF
ok "Configuracion escrita"

# --- 5. Servicio ------------------------------------------------------------
info "5/6 Arrancando el servicio xray..."
systemctl enable xray >/dev/null 2>&1 || true
systemctl restart xray
sleep 2

if ! systemctl is-active --quiet xray; then
  error "xray no arranco. Ultimas lineas del log:"
  journalctl -u xray -n 40 --no-pager || true
  exit 1
fi
ok "Servicio activo"

if command -v ss >/dev/null 2>&1 && ss -lntH "sport = :${PUERTO}" 2>/dev/null | grep -q .; then
  ok "Escuchando en el puerto ${PUERTO}"
else
  aviso "No pude confirmar que escuche en el puerto ${PUERTO}. Revisa: ss -lntp | grep ${PUERTO}"
fi

# --- 6. Enlace de conexion --------------------------------------------------
info "6/6 Generando enlace de conexion..."

ENLACE="vless://${UUID}@${IP_PUBLICA}:${PUERTO}?encryption=none&flow=xtls-rprx-vision&security=reality&sni=${SNI}&fp=chrome&pbk=${PUB_KEY}&sid=${SHORT_ID}&type=tcp&headerType=none#${ETIQUETA}"

printf '%s\n' "$ENLACE" > /root/vpn-enlace.txt
chmod 600 /root/vpn-enlace.txt

echo
echo "============================================================"
echo "  LISTO. Este es tu enlace de conexion:"
echo "============================================================"
echo
printf '%s\n' "$ENLACE"
echo
if command -v qrencode >/dev/null 2>&1; then
  echo "------------------------------------------------------------"
  echo "  QR (escanéalo con v2rayNG):"
  echo "------------------------------------------------------------"
  qrencode -t ANSIUTF8 "$ENLACE" 2>/dev/null || true
  echo
fi
echo "------------------------------------------------------------"
printf '  Guardado tambien en: /root/vpn-enlace.txt\n'
printf '  UUID:        %s\n' "$UUID"
printf '  Clave pub.:  %s\n' "$PUB_KEY"
printf '  ShortId:     %s\n' "$SHORT_ID"
echo "------------------------------------------------------------"
echo "  NO compartas este enlace: es tu credencial de acceso."
echo "============================================================"
