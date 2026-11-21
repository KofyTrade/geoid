#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  Nodo de SUECIA para GeoiD VPN
#
#  Instala AmneziaWG, crea la interfaz awg0 en 10.9.10.0/24 (misma ofuscacion
#  que Finlandia), activa NAT + BBR y genera el primer .conf de cliente.
#
#  Uso:
#     bash instalar-nodo-suecia.sh                     (nodo + 1 cliente)
#     bash instalar-nodo-suecia.sh --solo-interfaz     (sin cliente)
#
#  Al final deja el .conf en /root/geoid-suecia.conf
# ---------------------------------------------------------------------------
set -eu

# --- parametros del nodo (iguales que Finlandia salvo la subred) ------------
INTERFAZ="awg0"
PUERTO="21766"
RED="10.9.10.1/24"
PREFIJO="10.9.10"
MTU="1280"
DNS_CLIENTE="1.1.1.1, 9.9.9.9"
CONF="/etc/amnezia/amneziawg/${INTERFAZ}.conf"
CLIENTE="/root/geoid-suecia.conf"
SALIDA_CLIENTE="1"

if [ "${1:-}" = "--solo-interfaz" ]; then SALIDA_CLIENTE="0"; fi

azul()  { printf '\033[1;36m%s\033[0m\n' "$*"; }
verde() { printf '\033[1;32m%s\033[0m\n' "$*"; }
rojo()  { printf '\033[1;31m%s\033[0m\n' "$*"; }

if [ "$(id -u)" -ne 0 ]; then rojo "Ejecutalo como root."; exit 1; fi

# --------------------------------------------------------------- 1. sistema
azul "1/7 - Preparando el sistema"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq curl ca-certificates gnupg lsb-release \
  software-properties-common python3-launchpadlib iptables >/dev/null 2>&1 || true
verde "   paquetes base listos"

# --------------------------------------------------------------- 2. amneziawg
azul "2/7 - Instalando AmneziaWG"
MODO=""

# a) repositorio oficial (modulo del kernel + herramientas)
if add-apt-repository -y ppa:amnezia/ppa >/dev/null 2>&1; then
  apt-get update -qq >/dev/null 2>&1 || true
  if apt-get install -y -qq amneziawg-dkms amneziawg-tools \
       "linux-headers-$(uname -r)" >/dev/null 2>&1; then
    if modprobe amneziawg 2>/dev/null; then
      MODO="kernel"
      verde "   modulo del kernel + herramientas instalados"
    fi
  fi
fi

# b) sin modulo: herramientas desde el codigo y datos en espacio de usuario
if [ -z "$MODO" ]; then
  rojo "   el PPA no sirvio para este kernel; paso al modo usuarios"
  apt-get install -y -qq git build-essential >/dev/null 2>&1
  rm -rf /tmp/awg-tools
  git clone --depth 1 https://github.com/amnezia-vpn/amneziawg-tools /tmp/awg-tools >/dev/null 2>&1
  make -C /tmp/awg-tools/src >/dev/null 2>&1
  make -C /tmp/awg-tools/src install >/dev/null 2>&1
  ARQ=$(uname -m)
  case "$ARQ" in
    x86_64) SUFIJO="amd64" ;;
    aarch64) SUFIJO="arm64" ;;
    *) rojo "   arquitectura no soportada: $ARQ"; exit 1 ;;
  esac
  URL="https://github.com/amnezia-vpn/amneziawg-go/releases/latest/download/amneziawg-go-linux-${SUFIJO}"
  curl -fsSL "$URL" -o /usr/bin/amneziawg-go
  chmod +x /usr/bin/amneziawg-go
  MODO="usuarios"
  verde "   modo usuarios preparado (amneziawg-go)"
fi

if ! command -v awg >/dev/null 2>&1 || ! command -v awg-quick >/dev/null 2>&1; then
  rojo "   no se pudieron instalar las herramientas awg. Abortando."
  exit 1
fi

# --------------------------------------------------------------- 3. red base
azul "3/7 - Activando reenvio de paquetes y BBR"
mkdir -p /etc/sysctl.d
cat > /etc/sysctl.d/99-geoid-vpn.conf <<'EOF'
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
EOF
sysctl --system >/dev/null 2>&1 || true
verde "   IP forwarding: $(sysctl -n net.ipv4.ip_forward) · congestion: $(sysctl -n net.ipv4.tcp_congestion_control)"

# --------------------------------------------------------------- 4. interfaz
azul "4/7 - Creando la interfaz ${INTERFAZ}"
mkdir -p /etc/amnezia/amneziawg
chmod 700 /etc/amnezia/amneziawg

if [ ! -f "$CONF" ]; then
  PRIVADA=$(awg genkey)
  umask 077
  cat > "$CONF" <<EOF
[Interface]
PrivateKey = ${PRIVADA}
Address = ${RED}
ListenPort = ${PUERTO}
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
PostUp = iptables -I FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o $(ip route show default | awk '{print $5; exit}') -j MASQUERADE; iptables -t mangle -A FORWARD -o %i -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1240; iptables -t mangle -A FORWARD -i %i -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1240; while iptables -D FORWARD -i %i -o %i -j DROP 2>/dev/null; do :; done; iptables -I FORWARD -i %i -o %i -j DROP
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o $(ip route show default | awk '{print $5; exit}') -j MASQUERADE; while iptables -D FORWARD -i %i -o %i -j DROP 2>/dev/null; do :; done
EOF
  chmod 600 "$CONF"
  verde "   configuracion del servidor creada"
else
  verde "   ya existia la configuracion del servidor"
fi

# servicio: en modo usuarios hay que decirle a awg-quick que use amneziawg-go
if [ "$MODO" = "usuarios" ]; then
  mkdir -p "/etc/systemd/system/awg-quick@${INTERFAZ}.service.d"
  cat > "/etc/systemd/system/awg-quick@${INTERFAZ}.service.d/usuarios.conf" <<'EOF'
[Service]
Environment=WG_QUICK_USERSPACE_IMPLEMENTATION=/usr/bin/amneziawg-go
Environment=WG_SUDO=1
EOF
  systemctl daemon-reload
fi

systemctl enable "awg-quick@${INTERFAZ}" >/dev/null 2>&1 || true
systemctl restart "awg-quick@${INTERFAZ}" || true
sleep 2
if awg show "$INTERFAZ" >/dev/null 2>&1; then
  verde "   interfaz ${INTERFAZ} levantada (modo: ${MODO})"
else
  rojo "   la interfaz no arranco. Revisa: journalctl -u awg-quick@${INTERFAZ} -n 20"
  exit 1
fi

# --------------------------------------------------------------- 5. cortafuegos
azul "5/7 - Abriendo el puerto UDP ${PUERTO}"
if command -v ufw >/dev/null 2>&1; then
  ufw allow "${PUERTO}"/udp >/dev/null 2>&1 || true
fi
iptables -I INPUT -p udp --dport "$PUERTO" -j ACCEPT 2>/dev/null || true
verde "   puerto ${PUERTO}/udp habilitado"

# --------------------------------------------------------------- 6. cliente
if [ "$SALIDA_CLIENTE" = "1" ]; then
  azul "6/7 - Creando el primer perfil de cliente"
  IP_CLIENTE="${PREFIJO}.2"

  PRIV_CLI=$(awg genkey)
  PUB_CLI=$(printf '%s\n' "$PRIV_CLI" | awg pubkey)
  PSK=$(awg genpsk)
  PUB_SRV=$(awg show "$INTERFAZ" public-key)

  # el peer se anade en caliente y al fichero (sobrevive a reinicios)
  printf '%s' "$PSK" > /tmp/psk.$$
  chmod 600 /tmp/psk.$$
  awg set "$INTERFAZ" peer "$PUB_CLI" preshared-key /tmp/psk.$$ allowed-ips "${IP_CLIENTE}/32"
  rm -f /tmp/psk.$$

  cat >> "$CONF" <<EOF

[Peer]
# Cliente Suecia 1
PublicKey = ${PUB_CLI}
PresharedKey = ${PSK}
AllowedIPs = ${IP_CLIENTE}/32
EOF

  umask 077
  cat > "$CLIENTE" <<EOF
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
Endpoint = $(curl -fsSL https://api.ipify.org 2>/dev/null || echo "IP_DEL_SERVIDOR"):${PUERTO}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOF
  chmod 600 "$CLIENTE"
  verde "   perfil listo: ${CLIENTE}"
else
  azul "6/7 - Sin cliente (modo --solo-interfaz)"
fi

# --------------------------------------------------------------- 7. resumen
IP_PUBLICA=$(curl -fsSL https://api.ipify.org 2>/dev/null || echo "?")
azul "7/7 - Comprobaciones"
echo "   interfaz : $(awg show "$INTERFAZ" | head -1)"
echo "   escucha  : $(ss -lunp 2>/dev/null | grep -c ":$PUERTO" || echo 0) socket(s) en udp/$PUERTO"
echo "   forward  : $(sysctl -n net.ipv4.ip_forward)"

verde ""
verde "================================================================"
verde " NODO DE SUECIA LISTO"
verde "================================================================"
echo ""
echo "  IP publica : ${IP_PUBLICA}"
echo "  Subred     : ${PREFIJO}.0/24"
echo "  Puerto     : ${PUERTO}/udp"
echo "  Modo       : ${MODO}"
echo ""
if [ "$SALIDA_CLIENTE" = "1" ]; then
  echo "  Perfil de cliente: ${CLIENTE}"
  echo "  Bajalo al PC con:"
  echo "     scp root@${IP_PUBLICA}:${CLIENTE} E:\\PC\\vpn\\awg\\suecia.conf"
fi
echo ""
echo "  Servicio: systemctl status awg-quick@${INTERFAZ}"
echo "  Registro: journalctl -u awg-quick@${INTERFAZ} -n 20 --no-pager"
verde "================================================================"
