#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  Crea (o borra) clientes en el nodo de SUECIA
#
#  Uso:
#     bash nuevo-cliente-suecia.sh                    -> cliente nuevo
#     bash nuevo-cliente-suecia.sh ana                -> cliente "ana"
#     bash nuevo-cliente-suecia.sh --listar           -> ver clientes
#     bash nuevo-cliente-suecia.sh --borrar 10.9.10.5 -> borrar un cliente
#
#  Deja los .conf en /root/clientes-suecia/
# ---------------------------------------------------------------------------
set -eu

INTERFAZ="awg0"
CONF="/etc/amnezia/amneziawg/${INTERFAZ}.conf"
PUERTO="21766"
PREFIJO="10.9.10"
MTU="1280"
DNS_CLIENTE="1.1.1.1, 9.9.9.9"
CARPETA="/root/clientes-suecia"

azul()  { printf '\033[1;36m%s\033[0m\n' "$*"; }
verde() { printf '\033[1;32m%s\033[0m\n' "$*"; }
rojo()  { printf '\033[1;31m%s\033[0m\n' "$*"; }

if [ "$(id -u)" -ne 0 ]; then rojo "Ejecutalo como root."; exit 1; fi
if [ ! -f "$CONF" ]; then rojo "No existe $CONF (monta antes el nodo)."; exit 1; fi

mkdir -p "$CARPETA"
chmod 700 "$CARPETA"

# ---------------------------------------------------------------- listar
if [ "${1:-}" = "--listar" ]; then
  azul "Clientes del nodo de Suecia"
  printf '%-14s %-18s %s\n' "IP" "HANDSHAKE" "ESTADO"
  awg show "$INTERFAZ" dump | tail -n +2 | while read -r pub psk endpoint ips hs rx tx keep; do
    estado="desconectado"
    if [ "${hs:-0}" -gt 0 ] 2>/dev/null; then estado="conectado"; fi
    printf '%-14s %-18s %s\n' "${ips%%,*}" "$hs" "$estado"
  done
  exit 0
fi

# ---------------------------------------------------------------- borrar
if [ "${1:-}" = "--borrar" ]; then
  IP="${2:-}"
  if [ -z "$IP" ]; then rojo "Falta la IP: --borrar 10.9.10.5"; exit 1; fi

  PUB=$(awg show "$INTERFAZ" dump | awk -v ip="${IP}/32" '$4 == ip {print $1}')
  if [ -z "$PUB" ]; then rojo "No hay ningun cliente con esa IP."; exit 1; fi

  awg set "$INTERFAZ" peer "$PUB" remove
  # quitar del fichero el bloque del peer
  python3 - "$CONF" "$PUB" <<'PY'
import sys, re
ruta, pub = sys.argv[1], sys.argv[2]
texto = open(ruta, encoding="utf-8").read()
bloques = texto.split("[Peer]")
cabecera, resto = bloques[0], bloques[1:]
quedan = [b for b in resto if pub not in b]
nuevo = cabecera + "".join("[Peer]" + b for b in quedan)
open(ruta, "w", encoding="utf-8").write(nuevo)
print("configuracion actualizada")
PY
  verde "Cliente ${IP} borrado."
  exit 0
fi

# ---------------------------------------------------------------- crear
NOMBRE="${1:-cliente}"
SAFE=$(printf '%s' "$NOMBRE" | tr -c 'A-Za-z0-9_.-' '_')

# IP libre
USADAS=$(awg show "$INTERFAZ" allowed-ips 2>/dev/null | awk '{print $2}' | sed 's#/32##')
IP_CLIENTE=""
for n in $(seq 2 250); do
  cand="${PREFIJO}.${n}"
  if ! printf '%s\n' "$USADAS" | grep -qx "$cand"; then IP_CLIENTE="$cand"; break; fi
done
if [ -z "$IP_CLIENTE" ]; then rojo "No quedan IPs libres."; exit 1; fi

PRIV_CLI=$(awg genkey)
PUB_CLI=$(printf '%s\n' "$PRIV_CLI" | awg pubkey)
PSK=$(awg genpsk)
PUB_SRV=$(awg show "$INTERFAZ" public-key)
IP_PUBLICA=$(curl -fsSL https://api.ipify.org 2>/dev/null || echo "IP_DEL_SERVIDOR")

# peer en caliente
umask 077
printf '%s' "$PSK" > "/tmp/psk.$$"
awg set "$INTERFAZ" peer "$PUB_CLI" preshared-key "/tmp/psk.$$" allowed-ips "${IP_CLIENTE}/32"
rm -f "/tmp/psk.$$"

# al fichero, para que sobreviva a reinicios
cat >> "$CONF" <<EOF

[Peer]
# ${NOMBRE}
PublicKey = ${PUB_CLI}
PresharedKey = ${PSK}
AllowedIPs = ${IP_CLIENTE}/32
EOF

# el .conf del cliente
DESTINO="${CARPETA}/${SAFE}.conf"
cat > "$DESTINO" <<EOF
# GeoiD-vpn
# plan=pago
# servidor=Suecia
[Interface]
PrivateKey = ${PRIV_CLI}
Address = ${IP_CLIENTE}/32
DNS = ${DNS_CLIENTE}
MTU = ${MTU}
Jc = 4
Jmin = 77
Jmax = 170
S1 = 20
S2 = 93
S3 = 33
S4 = 27
H1 = 1
H2 = 2
H3 = 3
H4 = 4

[Peer]
PublicKey = ${PUB_SRV}
PresharedKey = ${PSK}
Endpoint = ${IP_PUBLICA}:${PUERTO}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOF
chmod 600 "$DESTINO"

verde ""
verde "================================================================"
verde " CLIENTE CREADO EN SUECIA"
verde "================================================================"
echo ""
echo "  Nombre : ${NOMBRE}"
echo "  IP     : ${IP_CLIENTE}"
echo "  Perfil : ${DESTINO}"
echo ""
echo "  Bajalo al PC con:"
echo "     scp root@${IP_PUBLICA}:${DESTINO} E:\\PC\\vpn\\awg\\suecia-${SAFE}.conf"
echo ""
verde "================================================================"
