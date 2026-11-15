# Rendimiento del túnel

## Lo que ya está medido

Desde el móvil, con el túnel activo:

| Medida | Valor |
|---|---|
| Latencia media (DNS real al servidor) | **21–23 ms** |
| Pérdida de paquetes | **0 %** |
| MTU efectivo | 1280 |

Con esos números, el túnel en sí **no es el problema**: 0 % de pérdida y 21 ms
son valores buenos. Cuando una web "va lenta", lo que falla está más arriba.

## Por qué el MTU es 1280 y no se puede subir

El perfil lleva `ContentPaddingAddition = 32-128`: AmneziaWG añade entre 32 y
128 bytes de relleno a cada paquete. El cálculo con un enlace de 1500:

```
MTU + relleno_max + cabeceras = 1280 + 128 + 60 = 1468  ✅ cabe
MTU + relleno_max + cabeceras = 1400 + 128 + 60 = 1588  ❌ no cabe
```

Con 1400 los paquetes grandes se pierden y el túnel se atasca a ratos
(eso ya pasó y se corrigió). **1280 es el valor correcto** con este relleno.
Si se quiere subir el MTU habría que bajar el relleno en el servidor
(`ContentPaddingAddition`), lo que reduce el camuflaje.

## Lo que hay que optimizar: el servidor

### 1. Diagnóstico (solo lectura)

Pegar en la sesión SSH del VPS:

```bash
echo "== nucleo =="; uname -r
sysctl net.ipv4.tcp_congestion_control net.core.default_qdisc 2>/dev/null

echo "== carga y memoria =="; uptime; free -m | head -2

echo "== procesos =="; ps aux --sort=-%cpu | head -6

echo "== tunel =="; awg show 2>/dev/null | head -20

echo "== perdida hacia internet =="; ping -c 20 -q 1.1.1.1 | tail -2

echo "== dns =="; grep -hE 'cache-size|server=|dns-forward-max' \
  /etc/dnsmasq.conf /etc/dnsmasq.d/*.conf 2>/dev/null | head -10
```

### 2. Optimización (BBR y memorias)

El cambio con más impacto. BBR gestiona mucho mejor los enlaces con algo de
pérdida y latencia alta, que es justo el caso de Rusia → Helsinki.

```bash
cat > /etc/sysctl.d/99-geoid.conf <<'EOF'
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.ipv4.tcp_rmem=4096 87380 16777216
net.ipv4.tcp_wmem=4096 65536 16777216
net.ipv4.tcp_mtu_probing=1
net.ipv4.tcp_fastopen=3
net.ipv4.tcp_slow_start_after_idle=0
net.core.netdev_max_backlog=5000
EOF
sysctl --system
echo "control: $(sysctl -n net.ipv4.tcp_congestion_control)"
```

Debe imprimir `control: bbr`. No corta el túnel ni hace falta reiniciar nada.

### 3. Caché de DNS

Con la lista de anuncios (unas 500.000 entradas), dnsmasq resuelve bien, pero
conviene darle caché amplia para que YouTube e Instagram no repitan consultas:

```bash
printf 'cache-size=20000\nmin-cache-ttl=300\ndns-forward-max=1000\n' \
  > /etc/dnsmasq.d/99-cache.conf
systemctl restart dnsmasq
systemctl is-active dnsmasq
```

## Si aun así va lento

Señales y qué significan:

| Síntoma | Causa probable |
|---|---|
| Todo carga pero con 1-2 s de espera inicial | DNS: el servidor tarda en responder |
| Las imágenes cargan y los vídeos se cortan | Ancho de banda del VPS o peering |
| Unas webs sí y otras no | Relleno/MTU: baja el MTU a 1240 y prueba |
| Lento solo en el móvil, bien en el PC | CPU del teléfono (el motor va en espacio de usuario) |

## Lo que ya se ha optimizado en la app (versión 2.2.1)

- El polihedro ya no reconstruye la pantalla 60 veces por segundo: se repinta
  solo el lienzo, y a 30 fps cuando está quieto.
- Un único socket para medir la latencia (antes se abría uno cada 2 segundos).
- La latencia se mide cada 6 segundos en vez de cada 2.
- Se respeta el MTU del perfil (con límites de 1280 a 1400) en vez de forzar uno.
- Las medidas no se solapan si una tarda más de lo normal.
