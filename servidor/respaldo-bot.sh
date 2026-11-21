#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  Copia de seguridad del bot (base de datos + configuracion) y envio a Suecia
#
#  Se ejecuta solo, cada dia. Hace:
#    1. copia consistente de bot.sqlite (aunque el bot este funcionando)
#    2. copia del env con los secretos
#    3. envio por SSH al otro servidor
#    4. limpieza de copias de mas de 7 dias
# ---------------------------------------------------------------------------
set -eu

DESTINO="/root/respaldos"
NODO_REMOTO="${GEOID_RESPALDO_REMOTO:-root@194.76.136.210}"
CARPETA_REMOTA="${GEOID_RESPALDO_CARPETA:-/root/respaldos-finlandia}"
BASE="${GEOID_DB:-/var/lib/geoid-bot/bot.sqlite}"
ENTORNO="${GEOID_ENV:-/etc/geoid-bot.env}"
LLAVE="/root/.ssh/id_ed25519"
FECHA="$(date +%F_%H%M)"
DIAS="${GEOID_RESPALDO_DIAS:-7}"

azul()  { printf '\033[1;36m%s\033[0m\n' "$*"; }
verde() { printf '\033[1;32m%s\033[0m\n' "$*"; }
rojo()  { printf '\033[1;31m%s\033[0m\n' "$*"; }

if [ "$(id -u)" -ne 0 ]; then rojo "Ejecutalo como root."; exit 1; fi
if [ ! -f "$BASE" ]; then rojo "No existe la base de datos: $BASE"; exit 1; fi

mkdir -p "$DESTINO"
chmod 700 "$DESTINO"

azul "1/4 - Copiando la base de datos"
python3 - "$BASE" "$DESTINO/bot-$FECHA.sqlite" <<'PY'
import sqlite3, sys
origen = sqlite3.connect(sys.argv[1])
destino = sqlite3.connect(sys.argv[2])
with destino:
    origen.backup(destino)
destino.close()
origen.close()
print("   copia consistente hecha")
PY
gzip -f "$DESTINO/bot-$FECHA.sqlite"
verde "   $(du -h "$DESTINO/bot-$FECHA.sqlite.gz" | cut -f1) comprimido"

azul "2/4 - Copiando la configuracion"
if [ -f "$ENTORNO" ]; then
  cp "$ENTORNO" "$DESTINO/geoid-bot-$FECHA.env"
  verde "   configuracion guardada (contiene secretos: permisos 600)"
fi
chmod 600 "$DESTINO"/* 2>/dev/null || true

azul "3/4 - Enviando al servidor de respaldo"
if [ ! -f "$LLAVE" ]; then
  rojo "   falta la llave SSH ($LLAVE). Ejecuta antes instalar-respaldo.sh"
  exit 1
fi

if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 -i "$LLAVE" "$NODO_REMOTO" \
     "mkdir -p '$CARPETA_REMOTA' && chmod 700 '$CARPETA_REMOTA'"; then
  if rsync -az -e "ssh -o StrictHostKeyChecking=no -i $LLAVE" \
       "$DESTINO/" "$NODO_REMOTO:$CARPETA_REMOTA/"; then
    verde "   enviado a $NODO_REMOTO:$CARPETA_REMOTA"
  else
    rojo "   rsync fallo (la copia local se conserva)"
    exit 1
  fi
else
  rojo "   no se pudo conectar con $NODO_REMOTO (la copia local se conserva)"
  exit 1
fi

azul "4/4 - Limpiando copias antiguas"
find "$DESTINO" -type f -mtime "+$DIAS" -delete
ssh -o StrictHostKeyChecking=no -i "$LLAVE" "$NODO_REMOTO" \
  "find '$CARPETA_REMOTA' -type f -mtime +$DIAS -delete" 2>/dev/null || true
verde "   copias de mas de $DIAS dias eliminadas"

echo ""
verde "RESPALDO COMPLETO: $(date '+%d.%m.%Y %H:%M')"
echo "  local : $DESTINO"
echo "  remoto: $NODO_REMOTO:$CARPETA_REMOTA"
