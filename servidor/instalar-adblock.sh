#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  DNS con bloqueo de anuncios para un nodo de GeoiD
#
#  Instala dnsmasq escuchando SOLO en la interfaz del VPN (awg0) y descarga
#  una lista de anuncios y rastreadores. Los clientes que tengan marcado
#  "bloquear anuncios" en la app usan esta IP como DNS.
#
#  Uso:
#     bash instalar-adblock.sh                    (awg0 / 10.9.10.1)
#     bash instalar-adblock.sh awg0 10.9.9.1      (otra interfaz e IP)
# ---------------------------------------------------------------------------
set -eu

INTERFAZ="${1:-awg0}"
IP_DNS="${2:-10.9.10.1}"

LISTA="/etc/dnsmasq.d/geoid-adblock.conf"
CONF="/etc/dnsmasq.d/geoid.conf"
ACTUALIZA="/usr/local/bin/geoid-adblock-actualizar"

azul()  { printf '\033[1;36m%s\033[0m\n' "$*"; }
verde() { printf '\033[1;32m%s\033[0m\n' "$*"; }
rojo()  { printf '\033[1;31m%s\033[0m\n' "$*"; }

if [ "$(id -u)" -ne 0 ]; then rojo "Ejecutalo como root."; exit 1; fi

if ! ip link show "$INTERFAZ" >/dev/null 2>&1; then
  rojo "La interfaz $INTERFAZ no existe. Monta antes el nodo del VPN."
  exit 1
fi

# --------------------------------------------------------------- 1. paquetes
azul "1/5 - Instalando dnsmasq"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq dnsmasq dnsutils curl >/dev/null 2>&1
verde "   instalado"

# --------------------------------------------------------------- 2. script de lista
azul "2/5 - Preparando la lista de bloqueo"
cat > "$ACTUALIZA" <<'EOF'
#!/usr/bin/env bash
# Descarga la lista de anuncios y reinicia dnsmasq si ha cambiado.
set -eu
DESTINO="/etc/dnsmasq.d/geoid-adblock.conf"
TEMPORAL="$(mktemp)"
FUENTES=(
  "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
  "https://adaway.org/hosts.txt"
  "https://raw.githubusercontent.com/AdguardTeam/cname-trackers/master/data/combined_disguised_trackers_justdomains.txt"
)
: > "$TEMPORAL"
for url in "${FUENTES[@]}"; do
  datos=$(curl -fsSL --max-time 40 "$url" 2>/dev/null || true)
  printf '%s\n' "$datos" | awk '
    /^0\.0\.0\.0[ \t]+[a-zA-Z0-9]/ { print "address=/"$2"/0.0.0.0" }
    /^127\.0\.0\.1[ \t]+[a-zA-Z0-9]/ { print "address=/"$2"/0.0.0.0" }
    /^[a-zA-Z0-9.*-]+\.[a-zA-Z]{2,}$/ { print "address=/"$1"/0.0.0.0" }
  ' >> "$TEMPORAL" || true
done
sort -u "$TEMPORAL" -o "$TEMPORAL"
if [ "$(wc -l < "$TEMPORAL")" -lt 100 ]; then
  rm -f "$TEMPORAL"
  echo "lista vacia: no se toca nada"
  exit 0
fi
if cmp -s "$TEMPORAL" "$DESTINO" 2>/dev/null; then
  rm -f "$TEMPORAL"
  echo "sin cambios"
  exit 0
fi
mv "$TEMPORAL" "$DESTINO"
systemctl restart dnsmasq
echo "lista actualizada: $(wc -l < "$DESTINO") dominios"
EOF
chmod +x "$ACTUALIZA"
verde "   script de actualizacion en $ACTUALIZA"

# --------------------------------------------------------------- 3. configuracion
azul "3/5 - Configurando dnsmasq en ${INTERFAZ} (${IP_DNS})"
cat > "$CONF" <<EOF
# GeoiD: DNS del nodo, solo para clientes del VPN
interface=${INTERFAZ}
bind-dynamic
no-hosts
no-resolv
cache-size=2000
domain-needed
bogus-priv
server=1.1.1.1
server=9.9.9.9
server=77.88.8.8
log-queries=no
EOF

# que no interfiera con el resolutor del sistema
if [ -f /etc/systemd/resolved.conf ]; then
  systemctl stop systemd-resolved >/dev/null 2>&1 || true
  systemctl disable systemd-resolved >/dev/null 2>&1 || true
  if [ -L /etc/resolv.conf ]; then
    rm -f /etc/resolv.conf
    printf 'nameserver 1.1.1.1\nnameserver 9.9.9.9\n' > /etc/resolv.conf
  fi
fi

# primera descarga de la lista
"$ACTUALIZA" || true
verde "   lista: $(wc -l < "$LISTA" 2>/dev/null || echo 0) dominios"

systemctl enable dnsmasq >/dev/null 2>&1 || true
systemctl restart dnsmasq
sleep 2

# --------------------------------------------------------------- 4. comprobacion
azul "4/5 - Comprobando"
OK=1
if ! ss -lunp 2>/dev/null | grep -q "${IP_DNS}:53"; then
  rojo "   dnsmasq no escucha en ${IP_DNS}:53"
  OK=0
fi
PRUEBA_BLOQUEO=$(dig +short +time=3 +tries=1 @"$IP_DNS" doubleclick.net 2>/dev/null | head -1 || true)
PRUEBA_NORMAL=$(dig +short +time=3 +tries=1 @"$IP_DNS" ya.ru 2>/dev/null | head -1 || true)
echo "   doubleclick.net -> ${PRUEBA_BLOQUEO:-sin respuesta}   (esperado 0.0.0.0)"
echo "   ya.ru           -> ${PRUEBA_NORMAL:-sin respuesta}   (esperado una IP real)"
if [ "$PRUEBA_BLOQUEO" != "0.0.0.0" ]; then
  rojo "   el bloqueo no responde; revisa: journalctl -u dnsmasq -n 20"
  OK=0
fi

# --------------------------------------------------------------- 5. actualizacion diaria
azul "5/5 - Actualizacion automatica de la lista"
cat > /etc/systemd/system/geoid-adblock.service <<EOF
[Unit]
Description=Actualizar la lista de anuncios de GeoiD

[Service]
Type=oneshot
ExecStart=${ACTUALIZA}
EOF
cat > /etc/systemd/system/geoid-adblock.timer <<'EOF'
[Unit]
Description=Actualiza la lista de anuncios cada dia

[Timer]
OnCalendar=*-*-* 04:30:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload
systemctl enable --now geoid-adblock.timer >/dev/null 2>&1 || true

verde ""
verde "================================================================"
verde " DNS CON BLOQUEO LISTO"
verde "================================================================"
echo ""
echo "  Interfaz : ${INTERFAZ}"
echo "  DNS      : ${IP_DNS}"
echo "  Dominios : $(wc -l < "$LISTA" 2>/dev/null || echo 0) bloqueados"
echo "  Estado   : $(systemctl is-active dnsmasq)"
echo ""
echo "  Servicio : systemctl status dnsmasq"
echo "  Registro : journalctl -u dnsmasq -n 20 --no-pager"
echo "  Probar   : dig @${IP_DNS} doubleclick.net  (debe dar 0.0.0.0)"
if [ "$OK" = "0" ]; then
  rojo "  ATENCION: alguna comprobacion fallo (mira arriba)."
fi
verde "================================================================"
