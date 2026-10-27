"""Verifica periodos, cobertura y estados usados por los gráficos del tablero."""
import sqlite3
from datetime import datetime

import analisis


def conexion():
    con = sqlite3.connect(':memory:')
    con.row_factory = sqlite3.Row
    con.executescript('''
        CREATE TABLE senales (fecha TEXT, estado TEXT, variable_id TEXT, municipio_id TEXT);
        CREATE TABLE decisiones (estado TEXT, avance TEXT);
    ''')
    return con


def test_periodos_recepcion_y_senales_sin_variable():
    con = conexion()
    con.executemany('INSERT INTO senales VALUES (?, ?, ?, ?)', [
        ('2026-01-05 08:00', 'Validada', 'A1', 'cal'),
        ('2026-01-04 08:00', 'Validada', None, 'cal'),
        ('2025-11-07 12:00', 'Validada', 'P1', 'bog'),  # límite incluido de 60 días
        ('2025-11-07 11:59', 'Validada', 'P1', 'bog'),  # fuera de la ventana
        ('2026-01-06 12:01', 'Validada', 'P1', 'bog'),  # no contar datos futuros
        ('2026-01-06 10:00', 'Por validar', 'A1', 'cal'),
        ('2026-01-01 10:00', 'Descartada', 'A1', 'cal'),
    ])
    r = analisis.actividad_tablero(con, datetime(2026, 1, 6, 12))
    assert (r['validadas'], r['vinculadas'], r['sin_variable']) == (3, 2, 1)
    assert r['por_lugar'] == {'cal': 2, 'bog': 1}
    assert r['recibidas'] == 4  # ventana semanal distinta de la ventana de riesgo
    assert r['semanas'][0]['inicio'] == '2025-11-17'
    assert r['semanas'][-1]['inicio'] == '2026-01-05'
    assert r['semanas'][-1]['validadas'] == 1
    assert r['semanas'][-2]['validadas'] == 1
    assert r['semanas'][-2]['descartadas'] == 1
    assert r['semanas'][-1]['pendientes'] == 1
    assert r['pendientes'] == 1
    con.close()


def test_compromisos_solo_aprobados_y_estados_sin_perdida():
    con = conexion()
    con.executemany('INSERT INTO decisiones VALUES (?, ?)', [
        ('Aprobada', 'En curso'), ('Aprobada', None),
        ('Aprobada', 'En pausa'), ('Descartada', 'Cumplido'),
        ('En análisis', 'Sin iniciar'),
    ])
    r = analisis.actividad_tablero(con, datetime(2026, 1, 6, 12))
    counts = {x['estado']: x['cantidad'] for x in r['compromisos']}
    assert r['total_compromisos'] == 3
    assert counts['En curso'] == counts['Sin iniciar'] == counts['En pausa'] == 1
    assert counts['Cumplido'] == 0
    assert r['validadas'] == r['recibidas'] == 0
    assert len(r['semanas']) == 8
    assert all(s['validadas'] == s['pendientes'] == s['descartadas'] == 0 for s in r['semanas'])
    con.close()
