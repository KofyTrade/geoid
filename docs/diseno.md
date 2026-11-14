# Diseño de la aplicación — dirección visual

Referencia aportada: fondo verde-petróleo con degradado, **poliedro negro facetado** en el
centro, **esfera de nodos y líneas** finas alrededor, círculo de apoyo y pequeñas fórmulas
(`v = 4/3 πr³`, `i = p/4πr²`, `r`) en los márgenes.

## Paleta (medida sobre la referencia)

| Uso | Hex | Notas |
|---|---|---|
| Fondo profundo | `#06171B` | esquinas |
| Fondo medio | `#0B2429` | centro del degradado |
| Halo superior | `#12414A` | luz que entra desde arriba |
| Poliedro — cara iluminada | `#1B262B` | |
| Poliedro — cara en sombra | `#070A0C` | casi negro |
| Líneas y nodos | `#E8F4F5` | blanco roto, nunca blanco puro |
| Acento (estado activo) | `#22D3EE` | el turquesa que ya usa la app |

Sin texto decorativo: la pantalla se queda solo con el poliedro, la esfera y el botón.

Tipografía de las fórmulas: serif itálica muy fina, tamaño pequeño, opacidad ~35 %.

## Composición

```
┌─────────────────────────────┐
│  ·  ·   ·    ·   ·   ·      │  ← campo de estrellas tenue
│        ╭───────╮            │
│             ◈◈◈             │  ← poliedro + esfera de nodos
│        ╰───────╯            │
│                             │
│      [ Conectar ]           │  ← único control visible
│      Desconectado           │
└─────────────────────────────┘
```

- El poliedro ocupa el **45–55 %** del ancho.
- La esfera de nodos lo rodea a ~1,25× su radio, con 30–40 nodos y líneas solo entre
  vecinos cercanos (no todos contra todos).
- Un círculo fino, casi invisible, cierra la esfera.

## Estados y animación

| Estado | Poliedro | Esfera | Texto |
|---|---|---|---|
| **Desconectado** | giro lento (30 s/vuelta), opacidad 100 % | estática | "Desconectado", gris |
| **Conectando** | pulso de escala 1.00 → 1.03 | nodos parpadean en secuencia | "Conectando…" |
| **Conectado** | **giro continuo 6–8 s/vuelta** + inclinación 15° | nodos con leve deriva | "Conectado", `#22D3EE` |
| **Error** | se detiene y se inclina 3° | se apaga | "Sin conexión" |

- La transición de velocidad usa *easing* de 600 ms: no arranca de golpe.
- Rotación siempre sobre el eje Y, con inclinación fija de ~15° en X (como la Tierra).
- Sin sombras difusas ni desenfoques: el estilo es geométrico y nítido.

## Cómo se implementa en Android

1. **Vista propia** (`View` + `onDraw`) o `Canvas` de Compose. Nada de imágenes estáticas:
   el poliedro se calcula por vértices y se proyecta en 2D.
2. Modelo: **icosaedro** (12 vértices, 20 caras). Las caras se ordenan por profundidad
   y se rellenan de atrás hacia delante; el sombreado sale del producto escalar de la
   normal con una luz fija arriba-izquierda.
3. Animación: `ValueAnimator` con `infinite` sobre el ángulo; la velocidad es una variable
   que se interpola al cambiar de estado. **No** usar `Animation` de vistas: aquí
   redibujamos cada frame.
4. Esfera de nodos: puntos por espiral de Fibonacci, unidos a sus 2–3 vecinos más cercanos.
   Se calcula una vez y solo se rota con el poliedro.
5. Rendimiento: 60 fps con ~20 caras y ~40 nodos es trivial. Evitar `Paint` nuevos dentro
   de `onDraw`; reutilizarlos.
6. Accesibilidad: respetar `Settings.Global.ANIMATOR_DURATION_SCALE == 0` → mostrar el
   poliedro quieto.

## Prototipo

[`diseno/prototipo.html`](diseno/prototipo.html) — ábrelo en el navegador y pulsa el botón
para ver el cambio de estado y la rotación.
