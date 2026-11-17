#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  Instala la página de pagos de GeoiD fuera de Telegram.
#
#  - Copia pagos_web.py a /opt/geoid-pagos
#  - La arranca como servicio en 127.0.0.1:8099
#  - Instala Caddy y le pone HTTPS para el dominio indicado
#
#  Uso:
#     bash instalar-pagina-pagos.sh geoidvpn.duckdns.org
#
#  El dominio debe existir y apuntar a este servidor (DuckDNS gratis).
#  El QR se sube después a /opt/geoid-pagos/qr.png
# ---------------------------------------------------------------------------
set -euo pipefail

DOMINIO="${1:-}"
DESTINO="/opt/geoid-pagos"
PUERTO="8099"
SERVICIO="/etc/systemd/system/geoid-pagos.service"

azul()  { printf '\033[1;36m%s\033[0m\n' "$*"; }
verde() { printf '\033[1;32m%s\033[0m\n' "$*"; }
rojo()  { printf '\033[1;31m%s\033[0m\n' "$*"; }

if [ "$(id -u)" -ne 0 ]; then
  rojo "Ejecútalo como root."
  exit 1
fi

if [ -z "$DOMINIO" ]; then
  rojo "Falta el dominio. Uso: bash $0 geoidvpn.duckdns.org"
  exit 1
fi

if ! getent hosts "$DOMINIO" >/dev/null 2>&1; then
  rojo "El dominio $DOMINIO todavía no resuelve."
  echo "  Créalo en duckdns.org apuntando a la IP de este servidor y espera 1 minuto."
  exit 1
fi

azul "1/5 · Copiando la página"
mkdir -p "$DESTINO"
if [ ! -f "$DESTINO/pagos_web.py" ]; then
  if [ -f "/root/pagos_web.py" ]; then
    cp /root/pagos_web.py "$DESTINO/pagos_web.py"
  else
    rojo "No encuentro pagos_web.py. Súbelo a /root/ con scp y repite."
    exit 1
  fi
fi
chmod 700 "$DESTINO"

azul "2/5 · Probando la página en local"
cd "$DESTINO"
set -a
# shellcheck disable=SC1091
. /etc/geoid-bot.env
set +a
timeout 4 python3 pagos_web.py >/tmp/pagos_prueba.log 2>&1 || true
if grep -q "escuchando" /tmp/pagos_prueba.log; then
  verde "   responde correctamente"
else
  rojo "   no arrancó:"; cat /tmp/pagos_prueba.log; exit 1
fi

azul "3/5 · Creando el servicio"
cat > "$SERVICIO" <<EOF
[Unit]
Description=Pagina de pagos de GeoiD
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$DESTINO
EnvironmentFile=/etc/geoid-bot.env
Environment=GEOID_WEB_PUERTO=$PUERTO
ExecStart=/usr/bin/python3 $DESTINO/pagos_web.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable geoid-pagos >/dev/null 2>&1 || true
systemctl restart geoid-pagos
sleep 2
systemctl is-active --quiet geoid-pagos || { rojo "El servicio no arrancó:"; journalctl -u geoid-pagos -n 15 --no-pager; exit 1; }
verde "   servicio activo en 127.0.0.1:$PUERTO"

azul "4/5 · Instalando Caddy (HTTPS automático)"
if ! command -v caddy >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https curl gnupg >/dev/null
  curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
    | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
    > /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -qq
  apt-get install -y -qq caddy >/dev/null
fi
verde "   $(caddy version 2>/dev/null | head -1)"

azul "5/5 · Configurando el dominio"
cat > /etc/caddy/Caddyfile <<EOF
# Página de pagos de GeoiD
$DOMINIO {
    encode gzip
    reverse_proxy 127.0.0.1:$PUERTO
    header {
        Strict-Transport-Security "max-age=31536000"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "no-referrer"
    }
}
EOF
systemctl enable caddy >/dev/null 2>&1 || true
systemctl restart caddy
sleep 3

IP=$(curl -fsSL https://api.ipify.org || echo "?")
ENLACE="https://$DOMINIO/?p=1&u=123456789"
CODIGO=$(curl -s -o /dev/null -w "%{http_code}" --max-time 12 "$ENLACE" || echo "000")

verde ""
verde "================================================================"
verde " PÁGINA DE PAGOS LISTA"
verde "================================================================"
echo ""
echo "  Dirección:  https://$DOMINIO/?p=<meses>&u=<id_de_telegram>"
echo "  Prueba:     $ENLACE"
echo "  Respuesta:  HTTP $CODIGO   (200 = funciona)"
echo ""
echo "  Servicios:  systemctl status geoid-pagos   ·   systemctl status caddy"
echo "  Registro:   journalctl -u geoid-pagos -f"
echo ""
echo "  Falta subir el QR de tu banco a:  $DESTINO/qr.png"
echo "     scp TU-QR.png root@$IP:$DESTINO/qr.png"
echo ""
if [ "$CODIGO" != "200" ]; then
  rojo "  OJO: la página aún no responde 200. Suele ser el DNS o el certificado."
  echo "  Espera 2 minutos y vuelve a probar el enlace. Registro: journalctl -u caddy -n 20"
fi
verde "================================================================"
