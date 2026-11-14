# Guía 03 — Reparar el servidor (y seguir con el handshake)

## Qué pasó

A las 04:20 reiniciaste Xray en el servidor con `systemctl restart xray`. Desde entonces:

| Prueba | Antes del reinicio | Ahora |
|---|---|---|
| Puerto 443 abierto | ✅ | ✅ |
| Handshake TLS (REALITY) | ✅ respondía como Microsoft | ❌ se cuelga a los 12 s |

**Tu VPN del móvil tampoco estará funcionando ahora mismo.** Es lo primero que hay que
arreglar: sin servidor sano no se puede probar nada más.

Síntoma típico de **proceso colgado o duplicado**: el sistema acepta la conexión TCP (el
puerto está abierto) pero nadie contesta al saludo TLS.

---

## Arreglo: pega este bloque completo

```bash
echo "=== 1. Estado del servicio ==="
systemctl status xray --no-pager | head -12

echo
echo "=== 2. Procesos xray ==="
ps aux | grep -v grep | grep xray

echo
echo "=== 3. Validando configuracion ==="
/usr/local/bin/xray -test -config /usr/local/etc/xray/config.json && echo "CONFIG OK" || echo "CONFIG CON ERRORES"

echo
echo "=== 4. Quien escucha en el 443 ==="
ss -lntp | grep ':443'

echo
echo "=== 5. Reinicio limpio ==="
systemctl stop xray
pkill -9 -f '/usr/local/bin/xray'
sleep 1
systemctl start xray
sleep 3
systemctl is-active xray

echo
echo "=== 6. Comprobacion final ==="
ss -lntp | grep ':443'
```

### Qué esperar

- Paso 3: `CONFIG OK` → la configuración está bien, el problema era el proceso.
  Si sale `CONFIG CON ERRORES`, mándame ese texto y reconstruimos la configuración.
- Paso 5: `active` → el servicio está vivo.
- Paso 6: debe aparecer una línea con `:443` y un proceso `xray`.

Pégame el bloque entero. Con eso sé exactamente qué hacer.

---

## Después de repararlo: la prueba pendiente

Antes del reinicio teníamos una contradicción que hay que resolver:

- **v2rayNG (Xray) en tu móvil**: conectaba bien.
- **sing-box** (nuestra app y la CLI en tu PC): `reality verification failed`.
- **Xray CLI en tu PC**: no llegó a probarse, el servidor ya estaba roto.

Mañana, con el servidor sano, hay que repetir esta prueba desde el PC:

```
E:\PC\vpn\tools\xray-cli.exe run -c E:\PC\vpn\tools\xray-test.json
```

y en otra ventana:

```
curl --socks5-hostname 127.0.0.1:1086 https://ipinfo.io/json
```

- Si **Xray conecta y sing-box no** → es una incompatibilidad entre motores. Solución:
  usar el motor de Xray en la app (libXray) o cambiar el servidor a sing-box.
- Si **ninguno conecta** → el problema está en los datos del enlace y lo buscamos ahí.

---

## Herramientas que quedan listas en `E:\PC\vpn\tools`

| Fichero | Qué es |
|---|---|
| `sing-box-cli.exe` | cliente sing-box compilado (con `with_utls`) |
| `xray-cli.exe` | cliente Xray compilado |
| `cli-test.json` | config de sing-box con tu enlace |
| `xray-test.json` | config de Xray con tu enlace |
| `sing-box\` | código fuente de sing-box v1.14.4 |
| `android-ndk-r28c\` | NDK con el que se compiló `libbox.aar` |

Con esto, cualquier prueba del túnel se hace **sin tocar Android**: se lanza el cliente en
el PC y se mira si conecta. Mucho más rápido para depurar.
