"""
Genera el icono de VlessGen: poliedro facetado sobre fondo verde azulado,
igual que la pantalla principal.

Salidas:
  - mipmap-*/ic_launcher.png         (icono clasico, API < 26)
  - mipmap-*/ic_launcher_round.png   (version redonda)
  - mipmap-*/ic_launcher_foreground.png  (capa del icono adaptativo, API 26+)
"""

import math
import os
from PIL import Image, ImageDraw, ImageFilter

RAIZ = r"E:\PC\vpn\app\android-proyecto\app\src\main\res"

FONDO_CENTRO = (12, 52, 58)
FONDO_BORDE = (5, 22, 26)
TURQUESA = (46, 230, 197)
NODO = (190, 255, 246)

DENSIDADES = {
    "mdpi": 48,
    "hdpi": 72,
    "xhdpi": 96,
    "xxhdpi": 144,
    "xxxhdpi": 192,
}

ESCALA_FOREGROUND = {
    "mdpi": 108,
    "hdpi": 162,
    "xhdpi": 216,
    "xxhdpi": 324,
    "xxxhdpi": 432,
}


def vertices_icosaedro():
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    v = [
        (-1, phi, 0), (1, phi, 0), (-1, -phi, 0), (1, -phi, 0),
        (0, -1, phi), (0, 1, phi), (0, -1, -phi), (0, 1, -phi),
        (phi, 0, -1), (phi, 0, 1), (-phi, 0, -1), (-phi, 0, 1),
    ]
    return [(float(a), float(b), float(c)) for a, b, c in v]


def aristas(verts):
    salida = []
    for i in range(len(verts)):
        for j in range(i + 1, len(verts)):
            a, b = verts[i], verts[j]
            d = math.dist(a, b)
            if abs(d - 2.0) < 0.01:
                salida.append((i, j))
    return salida


def rotar(p, ry, rx):
    x, y, z = p
    cosy, siny = math.cos(ry), math.sin(ry)
    x, z = x * cosy + z * siny, -x * siny + z * cosy
    cosx, sinx = math.cos(rx), math.sin(rx)
    y, z = y * cosx - z * sinx, y * sinx + z * cosx
    return (x, y, z)


def proyectar(p, escala, cx, cy):
    x, y, z = p
    factor = 5.0 / (5.0 + z)
    return cx + x * escala * factor, cy + y * escala * factor, z


def dibujar_poliedro(dibujo, escala, cx, cy, ry, rx, grosor, escala_nodos=1.0):
    verts = vertices_icosaedro()
    aristas_idx = aristas(verts)

    rotados = [rotar(v, ry, rx) for v in verts]
    pts = [proyectar(v, escala, cx, cy) for v in rotados]

    # Aristas: tres pasadas para simular el brillo (halo exterior tenue).
    for ancho, alfa in ((grosor * 3.2, 26), (grosor * 1.9, 64), (grosor, 235)):
        for i, j in aristas_idx:
            p, q = pts[i], pts[j]
            prof = (p[2] + q[2]) / 2.0
            cerca = max(0.0, min(1.0, (1.7 - prof) / 3.4))
            a = int(alfa * (0.45 + 0.55 * cerca))
            color = TURQUESA + (a,)
            dibujo.line([(p[0], p[1]), (q[0], q[1])], fill=color, width=max(1, int(ancho)))

    # Nodos intermedios sobre las aristas.
    for i, j in aristas_idx:
        for f in (0.3, 0.5, 0.7):
            p, q = rotados[i], rotados[j]
            m = (p[0] + (q[0] - p[0]) * f,
                 p[1] + (q[1] - p[1]) * f,
                 p[2] + (q[2] - p[2]) * f)
            x, y, z = proyectar(m, escala, cx, cy)
            cerca = max(0.0, min(1.0, (1.7 - z) / 3.4))
            r = (1.4 + 1.8 * cerca) * escala_nodos
            a = int(120 + 110 * cerca)
            dibujo.ellipse([x - r, y - r, x + r, y + r], fill=NODO + (a,))

    # Vertices.
    for x, y, z in pts:
        cerca = max(0.0, min(1.0, (1.7 - z) / 3.4))
        r = (2.2 + 3.0 * cerca) * escala_nodos
        dibujo.ellipse([x - r, y - r, x + r, y + r], fill=NODO + (int(150 + 105 * cerca),))


def fondo_gradiente(lado):
    """Degradado radial: turquesa muy oscuro en el centro, casi negro fuera."""
    img = Image.new("RGB", (lado, lado), FONDO_BORDE)
    px = img.load()
    cx = cy = lado / 2.0
    max_d = math.hypot(cx, cy)
    for y in range(lado):
        for x in range(lado):
            d = math.hypot(x - cx, y - cy) / max_d
            t = min(1.0, d ** 1.25)
            px[x, y] = (
                int(FONDO_CENTRO[0] + (FONDO_BORDE[0] - FONDO_CENTRO[0]) * t),
                int(FONDO_CENTRO[1] + (FONDO_BORDE[1] - FONDO_CENTRO[1]) * t),
                int(FONDO_CENTRO[2] + (FONDO_BORDE[2] - FONDO_CENTRO[2]) * t),
            )
    return img


def mascara_redonda(lado, margen=0):
    m = Image.new("L", (lado, lado), 0)
    d = ImageDraw.Draw(m)
    d.ellipse([margen, margen, lado - 1 - margen, lado - 1 - margen], fill=255)
    return m


def mascara_cuadrada_redondeada(lado, radio):
    m = Image.new("L", (lado, lado), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, lado - 1, lado - 1], radius=radio, fill=255)
    return m


def crear_icono(lado=1024, redondo=False, solo_poliedro=False):
    """Devuelve un RGBA del icono terminado."""
    ss = 2  # supersampling para bordes suaves
    L = lado * ss

    if solo_poliedro:
        lienzo = Image.new("RGBA", (L, L), (0, 0, 0, 0))
    else:
        base = fondo_gradiente(L).convert("RGBA")
        lienzo = base

    capa = Image.new("RGBA", (L, L), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    escala = L * (0.175 if solo_poliedro else 0.150)
    dibujar_poliedro(
        d, escala, L / 2.0, L / 2.0,
        ry=math.radians(28), rx=math.radians(20),
        grosor=max(2, int(L * 0.007)),
        escala_nodos=1.0 if solo_poliedro else 1.15,
    )

    # Halo suave del poliedro (doble pasada: brillo de neon)
    halo = capa.filter(ImageFilter.GaussianBlur(L * 0.018))
    lienzo = Image.alpha_composite(lienzo, halo)
    halo2 = capa.filter(ImageFilter.GaussianBlur(L * 0.006))
    lienzo = Image.alpha_composite(lienzo, halo2)
    lienzo = Image.alpha_composite(lienzo, capa)

    lienzo = lienzo.resize((lado, lado), Image.LANCZOS)

    if solo_poliedro:
        return lienzo

    if redondo:
        lienzo.putalpha(mascara_redonda(lado))
    else:
        lienzo.putalpha(mascara_cuadrada_redondeada(lado, int(lado * 0.22)))
    return lienzo


def guardar(img, ruta):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    img.save(ruta, "PNG", optimize=True)
    print("  " + ruta)


def main():
    print("Generando iconos de VlessGen...")

    maestro = crear_icono(1024, redondo=False)
    maestro_redondo = crear_icono(1024, redondo=True)
    primer_plano = crear_icono(1024, solo_poliedro=True)

    for densidad, tam in DENSIDADES.items():
        carpeta = os.path.join(RAIZ, "mipmap-" + densidad)
        guardar(maestro.resize((tam, tam), Image.LANCZOS),
                os.path.join(carpeta, "ic_launcher.png"))
        guardar(maestro_redondo.resize((tam, tam), Image.LANCZOS),
                os.path.join(carpeta, "ic_launcher_round.png"))

    for densidad, tam in ESCALA_FOREGROUND.items():
        carpeta = os.path.join(RAIZ, "mipmap-" + densidad)
        # El contenido del icono adaptativo debe caber en el 66% central.
        lienzo = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
        interior = int(tam * 0.86)
        reducido = primer_plano.resize((interior, interior), Image.LANCZOS)
        lienzo.paste(reducido, ((tam - interior) // 2, (tam - interior) // 2), reducido)
        guardar(lienzo, os.path.join(carpeta, "ic_launcher_foreground.png"))

    # Vista previa grande para revisarlo
    previa = crear_icono(512, redondo=False)
    previa.save(r"E:\PC\vpn\app\icono\vista-previa.png", "PNG")

    # Hoja de contactos: como se ve en el lanzador, a tamanos reales
    tam_hdpi = 72
    hoja = Image.new("RGB", (tam_hdpi * 5 + 60, tam_hdpi + 40), (10, 10, 12))
    x = 10
    for tam in (48, 72, 96, 144):
        mini = maestro.resize((tam, tam), Image.LANCZOS)
        hoja.paste(mini, (x, (hoja.height - tam) // 2), mini)
        x += tam + 10
    # version redonda
    mini = maestro_redondo.resize((tam_hdpi, tam_hdpi), Image.LANCZOS)
    hoja.paste(mini, (x, (hoja.height - tam_hdpi) // 2), mini)
    hoja = hoja.resize((hoja.width * 2, hoja.height * 2), Image.LANCZOS)
    hoja.save(r"E:\PC\vpn\app\icono\tamanos-reales.png", "PNG")

    print("  vista previa: E:\\PC\\vpn\\app\\icono\\vista-previa.png")
    print("  tamanos reales: E:\\PC\\vpn\\app\\icono\\tamanos-reales.png")
    print("Listo.")


if __name__ == "__main__":
    main()
