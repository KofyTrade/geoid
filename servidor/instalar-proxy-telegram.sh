#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  Proxy MTProto para Telegram en el propio servidor.
#
#  Para que Telegram funcione en Rusia sin tener la VPN encendida 24 horas.
#  Solo se enruta Telegram: el resto del móvil va directo y no gasta batería.
#
#  Uso:   bash instalar-proxy-telegram.sh [PUERTO]
#         (por defecto 8443; si lo bloquean, prueba 443 o 2053)
# ---------------------------------------------------------------------------
set -euo pipefail

PUERTO="${1:-8443}"
BIN="/usr/local/bin/mtg"
SERVICIO="/etc/systemd/system/mtg.service"
SECRETO="/etc/mtg.secret"

azul()  { printf '\033[1;36m%s\033[0m\n' "$*"; }
verde() { printf '\033[1;32m%s\033[0m\n' "$*"; }
rojo()  { printf '\033[1;31m%s\033[0m\n' "$*"; }

if [ "$(id -u)" -ne 0 ]; then
  rojo "Ejecútalo como root (estás en el servidor, ¿verdad?)"
  exit 1
fi

azul "1/5 · Instalando lo necesario"
apt-get update -qq
apt-get install -y -qq curl tar ca-certificates >/dev/null

azul "2/5 · Descargando mtg (proxy MTProto)"
if [ ! -x "$BIN" ]; then
  URL=$(curl -fsSL https://api.github.com/repos/9seconds/mtg/releases/latest \
        | grep -oE 'https://[^"]+linux-amd64\.tar\.gz' | head -1)
  if [ -z "$URL" ]; then
    rojo "No se encontró el archivo de mtg. Revisa la conexión del servidor."
    exit 1
  fi
  echo "   $URL"
  TMP=$(mktemp -d)
  curl -fsSL "$URL" -o "$TMP/mtg.tar.gz"
  tar -xzf "$TMP/mtg.tar.gz" -C "$TMP"
  ENCONTRADO=$(find "$TMP" -type f -name mtg | head -1)
  install -m 755 "$ENCONTRADO" "$BIN"
  rm -rf "$TMP"
fi
"$BIN" --version || true

azul "3/5 · Generando la clave del proxy"
if [ -f "$SECRETO" ]; then
  SECRET=$(cat "$SECRETO")
  echo "   (usando la clave existente)"
else
  SECRET=$("$BIN" generate-secret --hex tls)
  echo "$SECRET" > "$SECRETO"
  chmod 600 "$SECRETO"
  echo "   clave generada"
fi

azul "4/5 · Arrancando el servicio (puerto $PUERTO)"
cat > "$SERVICIO" <<EOF
[Unit]
Description=Proxy MTProto para Telegram (GeoiD)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$BIN run -b 0.0.0.0:$PUERTO $SECRET
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable mtg >/dev/null 2>&1 || true
systemctl restart mtg
sleep 2
systemctl is-active --quiet mtg || { rojo "El servicio no arrancó:"; journalctl -u mtg -n 15 --no-pager; exit 1; }

IP=$(curl -fsSL https://api.ipify.org || echo "193.29.224.164")

verde ""
verde "=================================================================="
verde " PROXY LISTO"
verde "=================================================================="
echo ""
echo "  Enlace (tócalo en el móvil con Telegram instalado):"
echo ""
echo "    tg://proxy?server=${IP}&port=${PUERTO}&secret=${SECRET}"
echo ""
echo "  Si prefieres pegarlo a mano:"
echo "    Servidor: ${IP}"
echo "    Puerto:   ${PUERTO}"
echo "    Clave:    ${SECRET}"
echo ""
echo "  En Telegram: Ajustes → Datos y almacenamiento → Proxy"
echo "               → Usar proxy → Añadir proxy → MTPROTO"
echo ""
verde "  Comprobar estado:   systemctl status mtg"
verde "  Ver el registro:    journalctl -u mtg -f"
verde "  Cambiar de puerto:  bash $0 443"
verde "=================================================================="
echo ""
echo "  No hace falta abrir el puerto en el firewall si usas ufw:"
echo "    ufw allow ${PUERTO}/tcp"
