"""
Genera el icono .ico de Windows a partir del mismo dibujo que el del movil.

Uso:
    python generar_ico.py

Escribe:
    flutter_app/windows/runner/resources/app_icon.ico
"""

import os
import sys

from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from generar import crear_icono  # noqa: E402  (mismo dibujo que el movil)

RAIZ = os.path.dirname(os.path.dirname(AQUI))  # E:\PC\vpn
DESTINO = os.path.join(
    RAIZ, "flutter_app", "windows", "runner", "resources", "app_icon.ico"
)

# Tamanos que pide Windows: barra de tareas, escritorio, explorador y vista grande.
TAMANOS = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def main():
    maestro = crear_icono(1024, redondo=False)
    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    maestro.save(DESTINO, format="ICO", sizes=TAMANOS)

    # Vista previa para revisarlo
    previa = os.path.join(AQUI, "windows-256.png")
    maestro.resize((256, 256), Image.LANCZOS).save(previa, "PNG")

    print("ico: " + DESTINO)
    print("   " + str(os.path.getsize(DESTINO)) + " bytes")
    print("previa: " + previa)


if __name__ == "__main__":
    main()
