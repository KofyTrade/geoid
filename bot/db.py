"""Base de datos SQLite: usuarios, suscripciones y códigos promocionales."""

import os
import sqlite3
import time

import config

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    tg_id       INTEGER PRIMARY KEY,
    usuario     TEXT,
    idioma      TEXT DEFAULT 'ru',
    creado      INTEGER NOT NULL,
    prueba_usada INTEGER DEFAULT 0,
    expira      INTEGER DEFAULT 0,
    ip          TEXT,
    privada     TEXT,
    publica     TEXT,
    preshared   TEXT,
    referido    INTEGER,
    codigo_ref  TEXT UNIQUE,
    proxy       INTEGER DEFAULT 0,
    nivel_ref   INTEGER DEFAULT 0,
    proxy_puerto INTEGER,
    proxy_secreto TEXT,
    proxy2_puerto INTEGER,
    proxy2_secreto TEXT
);

CREATE TABLE IF NOT EXISTS promos (
    codigo      TEXT PRIMARY KEY,
    dias        INTEGER NOT NULL,
    usos        INTEGER NOT NULL,
    usados      INTEGER DEFAULT 0,
    caduca      INTEGER
);

CREATE TABLE IF NOT EXISTS promos_usos (
    codigo      TEXT NOT NULL,
    tg_id       INTEGER NOT NULL,
    cuando      INTEGER NOT NULL,
    PRIMARY KEY (codigo, tg_id)
);

CREATE TABLE IF NOT EXISTS avisos (
    clave       TEXT PRIMARY KEY,
    cuando      INTEGER
);

CREATE TABLE IF NOT EXISTS ajustes (
    clave       TEXT PRIMARY KEY,
    valor       TEXT
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
            "INSERT INTO usuarios "
            "(tg_id, usuario, creado, referido, codigo_ref, idioma) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (tg_id, usuario, int(time.time()), referido, codigo, config.IDIOMA_DEFECTO),
        )
    return obtener(tg_id)


def _migrar(con) -> None:
    columnas = {f[1] for f in con.execute("PRAGMA table_info(usuarios)")}
    if "proxy" not in columnas:
        con.execute("ALTER TABLE usuarios ADD COLUMN proxy INTEGER DEFAULT 0")
    if "nivel_ref" not in columnas:
        con.execute("ALTER TABLE usuarios ADD COLUMN nivel_ref INTEGER DEFAULT 0")
    if "proxy_puerto" not in columnas:
        con.execute("ALTER TABLE usuarios ADD COLUMN proxy_puerto INTEGER")
    if "proxy_secreto" not in columnas:
        con.execute("ALTER TABLE usuarios ADD COLUMN proxy_secreto TEXT")
    if "proxy2_puerto" not in columnas:
        con.execute("ALTER TABLE usuarios ADD COLUMN proxy2_puerto INTEGER")
    if "proxy2_secreto" not in columnas:
        con.execute("ALTER TABLE usuarios ADD COLUMN proxy2_secreto TEXT")


def guardar(tg_id: int, **campos):
    if not campos:
        return
    claves = ", ".join(f"{k} = ?" for k in campos)
    valores = list(campos.values()) + [tg_id]
    with conectar() as con:
        _migrar(con)
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


def _migrar_promos(con) -> None:
    columnas = {f[1] for f in con.execute("PRAGMA table_info(promos)")}
    if "caduca" not in columnas:
        con.execute("ALTER TABLE promos ADD COLUMN caduca INTEGER")


def usar_promo(codigo: str, tg_id: int = 0) -> int | None:
    """Devuelve los dias del codigo si se pudo usar, o None."""
    codigo = codigo.strip().upper()
    ahora = int(time.time())
    with conectar() as con:
        _migrar_promos(con)
        fila = con.execute(
            "SELECT * FROM promos WHERE codigo = ?", (codigo,)
        ).fetchone()
        if not fila:
            return None
        if fila["usados"] >= fila["usos"]:
            return None
        if fila["caduca"] and ahora > int(fila["caduca"]):
            return None

        # un uso por persona
        if tg_id:
            ya = con.execute(
                "SELECT 1 FROM promos_usos WHERE codigo = ? AND tg_id = ?",
                (codigo, tg_id),
            ).fetchone()
            if ya:
                return None
            con.execute(
                "INSERT INTO promos_usos (codigo, tg_id, cuando) VALUES (?, ?, ?)",
                (codigo, tg_id, ahora),
            )

        con.execute(
            "UPDATE promos SET usados = usados + 1 WHERE codigo = ?", (codigo,)
        )
        return int(fila["dias"])


def crear_promo(codigo: str, dias: int, usos: int, caduca: int | None = None):
    with conectar() as con:
        _migrar_promos(con)
        con.execute(
            "INSERT OR REPLACE INTO promos (codigo, dias, usos, usados, caduca) "
            "VALUES (?, ?, ?, 0, ?)",
            (codigo.strip().upper(), dias, usos, caduca),
        )
        con.execute(
            "DELETE FROM promos_usos WHERE codigo = ?", (codigo.strip().upper(),)
        )


def listar_promos():
    with conectar() as con:
        _migrar_promos(con)
        return [
            dict(f)
            for f in con.execute(
                "SELECT * FROM promos ORDER BY codigo"
            ).fetchall()
        ]


def borrar_promo(codigo: str) -> bool:
    codigo = codigo.strip().upper()
    with conectar() as con:
        fila = con.execute(
            "SELECT 1 FROM promos WHERE codigo = ?", (codigo,)
        ).fetchone()
        if not fila:
            return False
        con.execute("DELETE FROM promos WHERE codigo = ?", (codigo,))
        con.execute("DELETE FROM promos_usos WHERE codigo = ?", (codigo,))
        return True


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

def con_peer():
    """Usuarios que tienen peer creado."""
    with conectar() as con:
        return con.execute(
            "SELECT tg_id, usuario, publica, prueba_usada, expira "
            "FROM usuarios WHERE publica IS NOT NULL"
        ).fetchall()


def referidos_pagados(tg_id: int) -> int:
    """Amigos invitados que han COMPRADO (no cuentan las pruebas)."""
    with conectar() as con:
        fila = con.execute(
            "SELECT COUNT(DISTINCT u.tg_id) c FROM usuarios u "
            "JOIN pagos p ON p.tg_id = u.tg_id "
            "WHERE u.referido = ?",
            (tg_id,),
        ).fetchone()
        return fila["c"] if fila else 0


def ha_pagado(tg_id: int) -> bool:
    with conectar() as con:
        fila = con.execute(
            "SELECT COUNT(*) c FROM pagos WHERE tg_id = ?", (tg_id,)
        ).fetchone()
        return fila["c"] > 0


def aviso_visto(clave: str) -> bool:
    with conectar() as con:
        fila = con.execute(
            "SELECT 1 FROM avisos WHERE clave = ?", (clave,)
        ).fetchone()
        return fila is not None


def marcar_aviso(clave: str) -> None:
    with conectar() as con:
        con.execute(
            "INSERT OR IGNORE INTO avisos (clave, cuando) VALUES (?, ?)",
            (clave, int(time.time())),
        )


def leer_ajuste(clave: str) -> str | None:
    with conectar() as con:
        fila = con.execute(
            "SELECT valor FROM ajustes WHERE clave = ?", (clave,)
        ).fetchone()
        return fila["valor"] if fila else None


def guardar_ajuste(clave: str, valor: str | None) -> None:
    with conectar() as con:
        if valor is None:
            con.execute("DELETE FROM ajustes WHERE clave = ?", (clave,))
        else:
            con.execute(
                "INSERT INTO ajustes (clave, valor) VALUES (?, ?) "
                "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor",
                (clave, valor),
            )