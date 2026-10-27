"""
Base de datos de Prisma (SQLite).

Crea las tablas y carga los datos de demostración la primera vez que se ejecuta.
Las calificaciones técnicas y las señales comunitarias son datos de DEMOSTRACIÓN
construidos por el equipo a partir de información pública; no son mediciones oficiales.
"""
import json
import os
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from werkzeug.security import generate_password_hash

import plantillas

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "prisma_territorial.db")

FACTORES = [
    ("P", "Político"),
    ("E", "Económico"),
    ("S", "Social"),
    ("T", "Tecnológico"),
    ("A", "Ecológico"),
    ("L", "Legal"),
]



SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE NOT NULL,
    clave_hash TEXT NOT NULL,
    nombre TEXT NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('directivo', 'analista', 'ti'))
);

CREATE TABLE IF NOT EXISTS municipios (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    departamento TEXT NOT NULL,
    cultivo TEXT NOT NULL,
    pdet INTEGER NOT NULL DEFAULT 0,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    nota TEXT
);

CREATE TABLE IF NOT EXISTS variables (
    id TEXT PRIMARY KEY,
    factor TEXT NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    tipo TEXT NOT NULL CHECK (tipo IN ('R', 'O')),
    probabilidad INTEGER NOT NULL CHECK (probabilidad BETWEEN 1 AND 5),
    impacto INTEGER NOT NULL CHECK (impacto BETWEEN 1 AND 5),
    tendencia TEXT NOT NULL,
    horizonte TEXT NOT NULL,
    cultivo TEXT NOT NULL DEFAULT 'Ambos',
    ods TEXT,                -- reservado (ODS); no se muestra en esta versión
    fuente TEXT,
    confiabilidad TEXT NOT NULL,
    frecuencia TEXT NOT NULL,
    decision TEXT,
    responsable TEXT,
    senal TEXT,
    icono TEXT,
    sensible INTEGER NOT NULL DEFAULT 0,
    actualizado TEXT
);

CREATE TABLE IF NOT EXISTS escenarios (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    origen TEXT NOT NULL DEFAULT 'base',   -- base | ia | reglas
    pregunta TEXT,                         -- la pregunta «¿Y si…?» que lo originó
    creado_por TEXT,
    cadena TEXT                            -- JSON: cadena de consecuencias por factor (rueda de futuros)
);

CREATE TABLE IF NOT EXISTS escenario_efectos (
    escenario_id TEXT NOT NULL REFERENCES escenarios(id),
    variable_id TEXT NOT NULL REFERENCES variables(id) ON DELETE CASCADE,
    probabilidad INTEGER NOT NULL,
    impacto INTEGER NOT NULL,
    PRIMARY KEY (escenario_id, variable_id)
);

CREATE TABLE IF NOT EXISTS senales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    municipio_id TEXT NOT NULL REFERENCES municipios(id),
    variable_id TEXT REFERENCES variables(id) ON DELETE SET NULL,
    gravedad INTEGER NOT NULL CHECK (gravedad BETWEEN 1 AND 5),
    descripcion TEXT,
    quien TEXT,
    estado TEXT NOT NULL DEFAULT 'Por validar',
    validado_por TEXT,
    origen TEXT,
    emergente TEXT,          -- tema nuevo que la IA detectó y aún no es variable
    foto TEXT,               -- archivo en la carpeta fotos/ (sin metadatos de ubicación)
    ia TEXT                  -- JSON con lo que sugirió la IA (tema, confianza, datos protegidos, motor)
);

CREATE TABLE IF NOT EXISTS ia_cache (
    clave TEXT PRIMARY KEY,
    contenido TEXT NOT NULL,
    motor TEXT,
    fecha TEXT
);

CREATE TABLE IF NOT EXISTS ajustes (
    clave TEXT PRIMARY KEY,
    valor TEXT
);

CREATE TABLE IF NOT EXISTS decisiones (
    variable_id TEXT PRIMARY KEY REFERENCES variables(id) ON DELETE CASCADE,
    estado TEXT NOT NULL DEFAULT 'Pendiente',
    comentario TEXT,
    actores TEXT,
    fecha_limite TEXT,
    avance TEXT DEFAULT 'Sin iniciar',
    actualizado_por TEXT,
    fecha TEXT
);

CREATE TABLE IF NOT EXISTS bitacora (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    usuario TEXT NOT NULL,
    accion TEXT NOT NULL,
    detalle TEXT
);
"""







# Las tres cuentas de demostración; el nombre visible lo pone la plantilla
USUARIOS = [("coordinacion", "coordinacion123", "directivo"), ("tecnico", "tecnico123", "analista"), ("ti", "ti123", "ti")]

# Metadatos de IA para que la demostración muestre cómo se ve una señal procesada
IA_DEMO = {"motor": "ia", "confianza": "alta", "datos_protegidos": [], "explicacion": "Clasificada por la IA y confirmada por la persona."}


ZONA = ZoneInfo(os.environ.get("PRISMA_ZONA", "America/Bogota"))


def hora_local():
    """Hora de Colombia, aunque el servidor esté en otro país (PythonAnywhere usa UTC)."""
    return datetime.now(ZONA).replace(tzinfo=None)


def ahora():
    return hora_local().strftime("%Y-%m-%d %H:%M")


def conectar():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con




def leer_ajuste(con, clave, defecto=None):
    try:
        fila = con.execute("SELECT valor FROM ajustes WHERE clave = ?", (clave,)).fetchone()
    except sqlite3.OperationalError:
        return defecto
    return fila["valor"] if fila and fila["valor"] is not None else defecto


def migrar(con):
    """Agrega las columnas nuevas a una base creada con una versión anterior (sin perder datos)."""
    columnas = {r["name"] for r in con.execute("PRAGMA table_info(escenarios)")}
    if "cadena" not in columnas:
        con.execute("ALTER TABLE escenarios ADD COLUMN cadena TEXT")


def plantilla_activa(con=None):
    """La plantilla de organización que está cargada en la base de datos."""
    propia = con is None
    con = con or conectar()
    pid = leer_ajuste(con, "plantilla", plantillas.POR_DEFECTO)
    if propia:
        con.close()
    return plantillas.obtener(pid)


def inicializar(forzar=False, plantilla=None):
    """Crea la base de datos y carga los datos de demostración de la plantilla elegida.
    Al cambiar de plantilla se conserva la clave de IA."""
    clave_ia = None
    if os.path.exists(DB_PATH):
        con = conectar()
        clave_ia = leer_ajuste(con, "clave_ia")
        plantilla = plantilla or leer_ajuste(con, "plantilla")
        con.close()
    plantilla = plantillas.obtener(plantilla)
    if forzar and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    nueva = not os.path.exists(DB_PATH)
    con = conectar()
    con.executescript(SCHEMA)
    migrar(con)
    if nueva:
        d, T = plantilla["datos"], plantilla["T"]
        con.execute("INSERT INTO ajustes (clave, valor) VALUES ('plantilla', ?)", (plantilla["id"],))
        if clave_ia:
            con.execute("INSERT INTO ajustes (clave, valor) VALUES ('clave_ia', ?)", (clave_ia,))
        for usuario, clave, rol in USUARIOS:
            con.execute("INSERT INTO usuarios (usuario, clave_hash, nombre, rol) VALUES (?, ?, ?, ?)",
                        (usuario, generate_password_hash(clave), T["roles"][rol], rol))
        con.executemany("INSERT INTO municipios VALUES (?, ?, ?, ?, ?, ?, ?, ?)", d.MUNICIPIOS)
        for v in d.VARIABLES:
            con.execute(
                """INSERT INTO variables (id, factor, nombre, descripcion, tipo, probabilidad, impacto, tendencia,
                   horizonte, cultivo, ods, fuente, confiabilidad, frecuencia, decision, responsable, senal, icono,
                   sensible, actualizado) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (*v, ahora()))
        for eid, nombre, desc, efectos in d.ESCENARIOS:
            con.execute("INSERT INTO escenarios (id, nombre, descripcion) VALUES (?, ?, ?)", (eid, nombre, desc))
            for vid, (p, i) in efectos.items():
                con.execute("INSERT INTO escenario_efectos VALUES (?, ?, ?, ?)", (eid, vid, p, i))
        hoy = hora_local()
        validador = T["roles"]["analista"]
        for dias, mun, var, grav, desc, quien, estado in d.SENALES:
            con.execute(
                """INSERT INTO senales (fecha, municipio_id, variable_id, gravedad, descripcion, quien, estado,
                   validado_por, origen) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ((hoy - timedelta(days=dias)).strftime("%Y-%m-%d %H:%M"), mun, var, grav, desc, quien, estado,
                 validador if estado != "Por validar" else None, "Formulario"))
        for dias, mun, grav, desc, quien, estado, tema in d.EMERGENTES:
            con.execute(
                """INSERT INTO senales (fecha, municipio_id, variable_id, gravedad, descripcion, quien, estado,
                   validado_por, origen, emergente, ia) VALUES (?, ?, NULL, ?, ?, ?, ?, ?, 'Formulario', ?, ?)""",
                ((hoy - timedelta(days=dias)).strftime("%Y-%m-%d %H:%M"), mun, grav, desc, quien, estado,
                 validador if estado != "Por validar" else None, tema,
                 json.dumps({**IA_DEMO, "confianza": "media", "tema_nuevo": tema}, ensure_ascii=False)))
        # Una señal de seguridad con datos ya protegidos, para mostrar el anonimato
        mun, var, grav, texto, protegidos = d.SENAL_PROTEGIDA
        con.execute(
            """INSERT INTO senales (fecha, municipio_id, variable_id, gravedad, descripcion, quien, estado, origen, ia)
               VALUES (?, ?, ?, ?, ?, 'Prefiero no decir', 'Por validar', 'Formulario', ?)""",
            ((hoy - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"), mun, var, grav, texto,
             json.dumps({**IA_DEMO, "datos_protegidos": protegidos}, ensure_ascii=False)))
        for vid, estado, coment, actores, dias_limite, avance in d.COMPROMISOS:
            con.execute("""INSERT INTO decisiones (variable_id, estado, comentario, actores, fecha_limite, avance,
                           actualizado_por, fecha) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (vid, estado, coment, actores, (hoy + timedelta(days=dias_limite)).strftime("%Y-%m-%d"), avance,
                         T["roles"]["directivo"], (hoy - timedelta(days=6)).strftime("%Y-%m-%d %H:%M")))
        con.execute("INSERT INTO bitacora (fecha, usuario, accion, detalle) VALUES (?, ?, ?, ?)",
                    (ahora(), "sistema", "Inicialización", f"Datos de demostración: {plantilla['nombre']}"))
        con.commit()
    con.close()


if __name__ == "__main__":
    inicializar(forzar=True)
    print("Base de datos reiniciada:", DB_PATH)
