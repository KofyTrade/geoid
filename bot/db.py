"""Base de datos SQLite: usuarios, suscripciones y códigos promocionales."""

import os
import sqlite3
import time

import config

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    tg_id       INTEGER PRIMARY KEY,
    usuario     TEXT,
    idioma      TEXT DEFAULT 'es',
    creado      INTEGER NOT NULL,
    prueba_usada INTEGER DEFAULT 0,
    expira      INTEGER DEFAULT 0,
    ip          TEXT,
    privada     TEXT,
    publica     TEXT,
    preshared   TEXT,
    referido    INTEGER,
    codigo_ref  TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS promos (
    codigo      TEXT PRIMARY KEY,
    dias        INTEGER NOT NULL,
    usos        INTEGER NOT NULL,
    usados      INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pagos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id       INTEGER NOT NULL,
    meses       INTEGER NOT NULL,
    estrellas   INTEGER NOT NULL,
    cuando      INTEGER NOT NULL,
    cargo       TEXT
);
"""


def conectar() -> sqlite3.Connection:
    os.makedirs(config.DIR_DATOS, exist_ok=True)
    con = sqlite3.connect(config.DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.executescript(ESQUEMA)
    return con


def obtener(tg_id: int):
    with conectar() as con:
        fila = con.execute(
            "SELECT * FROM usuarios WHERE tg_id = ?", (tg_id,)
        ).fetchone()
        return dict(fila) if fila else None


def crear_si_falta(tg_id: int, usuario: str | None, referido: int | None = None) -> dict:
    actual = obtener(tg_id)
    if actual:
        return actual
    with conectar() as con:
        codigo = f"r{tg_id:x}"
        con.execute(
            "INSERT INTO usuarios (tg_id, usuario, creado, referido, codigo_ref) "
            "VALUES (?, ?, ?, ?, ?)",
            (tg_id, usuario, int(time.time()), referido, codigo),
        )
    return obtener(tg_id)


def guardar(tg_id: int, **campos):
    if not campos:
        return
    claves = ", ".join(f"{k} = ?" for k in campos)
    valores = list(campos.values()) + [tg_id]
    with conectar() as con:
        con.execute(f"UPDATE usuarios SET {claves} WHERE tg_id = ?", valores)


def activos_hasta(instante: int):
    with conectar() as con:
        return [
            dict(f)
            for f in con.execute(
                "SELECT * FROM usuarios WHERE expira > ? AND ip IS NOT NULL",
                (instante,),
            )
        ]


def caducados(instante: int):
    with conectar() as con:
        return [
            dict(f)
            for f in con.execute(
                "SELECT * FROM usuarios WHERE expira <= ? AND ip IS NOT NULL",
                (instante,),
            )
        ]


def ips_en_uso() -> set[str]:
    with conectar() as con:
        return {
            fila["ip"]
            for fila in con.execute(
                "SELECT ip FROM usuarios WHERE ip IS NOT NULL AND expira > 0"
            )
        }


def registrar_pago(tg_id: int, meses: int, estrellas: int, cargo: str):
    with conectar() as con:
        con.execute(
            "INSERT INTO pagos (tg_id, meses, estrellas, cuando, cargo) "
            "VALUES (?, ?, ?, ?, ?)",
            (tg_id, meses, estrellas, int(time.time()), cargo),
        )


def por_codigo(codigo: str):
    with conectar() as con:
        fila = con.execute(
            "SELECT * FROM usuarios WHERE codigo_ref = ?", (codigo,)
        ).fetchone()
        return dict(fila) if fila else None


def usar_promo(codigo: str) -> int | None:
    """Devuelve los días del código si se pudo usar, o None."""
    codigo = codigo.strip().upper()
    with conectar() as con:
        fila = con.execute(
            "SELECT * FROM promos WHERE codigo = ?", (codigo,)
        ).fetchone()
        if not fila or fila["usados"] >= fila["usos"]:
            return None
        con.execute(
            "UPDATE promos SET usados = usados + 1 WHERE codigo = ?", (codigo,)
        )
        return int(fila["dias"])


def crear_promo(codigo: str, dias: int, usos: int):
    with conectar() as con:
        con.execute(
            "INSERT OR REPLACE INTO promos (codigo, dias, usos, usados) "
            "VALUES (?, ?, ?, 0)",
            (codigo.strip().upper(), dias, usos),
        )

def pago_existe(cargo: str) -> bool:
    with conectar() as con:
        fila = con.execute(
            "SELECT 1 FROM pagos WHERE cargo = ? LIMIT 1", (cargo,)
        ).fetchone()
        return fila is not None


def pago_mas_reciente(tg_id: int) -> dict | None:
    with conectar() as con:
        fila = con.execute(
            "SELECT * FROM pagos WHERE tg_id = ? ORDER BY cuando DESC LIMIT 1",
            (tg_id,),
        ).fetchone()
        return dict(fila) if fila else None