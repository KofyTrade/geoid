"""
Genera el icono .ico de Windows a partir del mismo dibujo que el del movil.

Los tamanos pequenos (16-32 px) se dibujan simplificados: lineas mas gruesas,
sin nodos intermedios y sin halo, para que se lean en la barra de tareas.
Los grandes (48-256 px) llevan el dibujo completo con halo.

Uso:
    python generar_ico.py

Escribe:
    flutter_app/windows/runner/resources/app_icon.ico
"""

import io
import math
import os
import struct
import sys

from PIL import Image, ImageDraw, ImageFilter

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from generar import (  # noqa: E402  (mismo dibujo que el movil)
    TURQUESA,
    aristas,
    dibujar_poliedro,
    fondo_gradiente,
    mascara_cuadrada_redondeada,
    proyectar,
    rotar,
    vertices_icosaedro,
)

RAIZ = os.path.dirname(os.path.dirname(AQUI))  # E:\PC\vpn
DESTINO = os.path.join(
    RAIZ, "flutter_app", "windows", "runner", "resources", "app_icon.ico"
)

TAMANOS = [16, 24, 32, 48, 64, 128, 256]
PEQUENOS = {16, 24, 32, 48, 64}


def _fondo(lado):
    return fondo_gradiente(lado).convert("RGBA")


def icono_simple(lado):
    """Version para tamanos pequenos: polihedro con trazo grueso y sin nodos."""
    ss = 8
    L = lado * ss

    capa = Image.new("RGBA", (L, L), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)

    verts = vertices_icosaedro()
    rotados = [rotar(v, math.radians(28), math.radians(20)) for v in verts]
    pts = [proyectar(v, L * 0.205, L / 2.0, L / 2.0) for v in rotados]

    grosor = max(1, int(L * 0.055))
    for i, j in aristas(verts):
        p, q = pts[i], pts[j]
        prof = (p[2] + q[2]) / 2.0
        cerca = max(0.0, min(1.0, (1.7 - prof) / 3.4))
        alfa = int(150 + 105 * cerca)
        d.line([(p[0], p[1]), (q[0], q[1])], fill=TURQUESA + (alfa,), width=grosor)

    # Vertices como puntos solidos, para que el contorno se lea.
    r = L * 0.028
    for x, y, _ in pts:
        d.ellipse([x - r, y - r, x + r, y + r], fill=(190, 255, 246, 255))

    lienzo = Image.alpha_composite(_fondo(L), capa)
    lienzo = lienzo.resize((lado, lado), Image.LANCZOS)
    lienzo.putalpha(mascara_cuadrada_redondeada(lado, int(lado * 0.22)))
    return lienzo


def icono_detallado(lado):
    """Version grande: la misma que el icono del movil, con el trazo algo mas grueso."""
    ss = 2
    L = lado * ss

    capa = Image.new("RGBA", (L, L), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    dibujar_poliedro(
        d,
        L * 0.170,
        L / 2.0,
        L / 2.0,
        ry=math.radians(28),
        rx=math.radians(20),
        grosor=max(3, int(L * 0.012)),
        escala_nodos=1.45,
    )

    lienzo = _fondo(L)
    lienzo = Image.alpha_composite(lienzo, capa.filter(ImageFilter.GaussianBlur(L * 0.016)))
    lienzo = Image.alpha_composite(lienzo, capa.filter(ImageFilter.GaussianBlur(L * 0.005)))
    lienzo = Image.alpha_composite(lienzo, capa)

    lienzo = lienzo.resize((lado, lado), Image.LANCZOS)
    lienzo.putalpha(mascara_cuadrada_redondeada(lado, int(lado * 0.22)))
    return lienzo


def escribir_ico(ruta, imagenes):
    """Escribe un .ico con una imagen PNG distinta para cada tamano."""
    entradas = sorted(imagenes.items())
    cabecera = struct.pack("<HHH", 0, 1, len(entradas))
    directorio = b""
    datos = b""
    desplazamiento = 6 + 16 * len(entradas)

    for lado, imagen in entradas:
        buffer = io.BytesIO()
        imagen.save(buffer, "PNG")
        png = buffer.getvalue()
        ancho = 0 if lado >= 256 else lado
        alto = 0 if lado >= 256 else lado
        directorio += struct.pack(
            "<BBBBHHII", ancho, alto, 0, 0, 1, 32, len(png), desplazamiento
        )
        desplazamiento += len(png)
        datos += png

    with open(ruta, "wb") as f:
        f.write(cabecera + directorio + datos)


def main():
    imagenes = {}
    for lado in TAMANOS:
        imagenes[lado] = icono_simple(lado) if lado in PEQUENOS else icono_detallado(lado)

    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    escribir_ico(DESTINO, imagenes)

    # Previas para revisarlas
    imagenes[256].save(os.path.join(AQUI, "windows-256.png"), "PNG")
    hoja = Image.new("RGB", (128 * 3 + 40, 150), (5, 22, 26))
    x = 10
    for lado in (16, 32, 48):
        mini = imagenes[lado].resize((128, 128), Image.NEAREST)
        hoja.paste(mini, (x, 10), mini)
        x += 138
    hoja.save(os.path.join(AQUI, "windows-tamanos.png"), "PNG")

    print("ico: " + DESTINO)
    print("   " + str(os.path.getsize(DESTINO)) + " bytes")
    print("previas: windows-256.png, windows-tamanos.png")


if __name__ == "__main__":
    main()
