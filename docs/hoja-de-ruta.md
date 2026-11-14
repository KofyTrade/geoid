# Proyecto VPN personal — acceso libre desde Rusia

Objetivo: tener internet sin bloqueos desde Rusia, con **servidor propio** y, al final,
una **app Android propia** que sea un cliente VPN real.

---

## Decisiones tomadas

| Tema | Decisión | Por qué |
|---|---|---|
| Plataforma | Android primero | Es donde más duele el bloqueo y donde antes vas a usarlo |
| Protocolo | **VLESS + XTLS-Vision + REALITY** (Xray-core) | Es el que mejor aguanta el DPI ruso: se hace pasar por TLS legítimo |
| Núcleo | Xray-core / sing-box (open source) | No escribimos criptografía ni protocolos propios; eso es mala ingeniería |
| Servidor | VPS Ubuntu 24.04 fuera de Rusia | Finlandia/Alemania: latencia baja y sin censura |
| Alcance | Uso **personal** | Publicitar/popularizar VPN en Rusia conlleva multas |

---

## Hoja de ruta

- [x] **Fase 1 — Servidor funcionando** ✅ (14 nov 2026)
  VPS Aeza en Helsinki + Xray + REALITY. Validado con `v2rayNG`: el móvil sale por
  Finlandia. → Ver [`GUIA-01-servidor.md`](GUIA-01-servidor.md)

- [x] **Fase 2 — App Android (v0.1 y v0.2)** ✅
  - **v0.1**: generador HTML → [`app/v0.1-generador.html`](app/v0.1-generador.html)
  - **v0.2**: app nativa Kotlin, compila y corre en emulador → [`app/android-proyecto`](app/android-proyecto)
  - Requisitos y plan de la v1.0 → [`app/ESPECIFICACION.md`](app/ESPECIFICACION.md)

- [x] **Fase 3 — App Android v1.0: cliente VPN real** ✅ (14 nov)
  `sing-box` (`libbox`) como motor, compilado desde la rama `testing`.
  Verificado en emulador: sale por Helsinki con el bloqueador de anuncios activo.
  Detalles y trampas en [`app/ESPECIFICACION.md`](app/ESPECIFICACION.md).

- [ ] **Fase 4 — Robustez**
  Varios servidores, perfil de reserva, reconexión automática, split tunneling.

---

## Estructura

```
vpn/
├── README.md                        <- este archivo
├── GUIA-01-servidor.md              <- paso a paso del servidor
└── servidor/
    └── instalar-xray-reality.sh     <- instalador automático
```

---

## Por qué no una VPN "normal"

En Rusia el problema no es cifrar, es **no parecer una VPN**. El DPI (TSPU) reconoce:

- **WireGuard** → por el patrón fijo de su *handshake*. Bloqueado, sobre todo en móvil.
- **OpenVPN** → por la firma del handshake TLS.
- **Shadowsocks clásico** → por análisis de entropía y sondeo activo.

**VLESS + REALITY** no cifra "a lo VPN" visible: durante el saludo TLS el servidor se
comporta como un sitio real (`www.microsoft.com`), y solo un cliente que conoce la clave
puede usarlo como túnel. Para un observador, es tráfico HTTPS normal hacia Microsoft.

---

## Reglas del proyecto

1. **No compartas el enlace `vless://`** ni el `id` (UUID). Es tu credencial.
2. **No escribas criptografía propia.** Usa Xray/sing-box y construye la capa de app.
3. **Una cosa por fase.** Primero que funcione, luego que sea bonito.
