"""Pruebas del motor PESTEL. Ejecutar desde la carpeta del proyecto: python -m pytest -q"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import analisis  # noqa: E402


def test_niveles_de_riesgo():
    assert analisis.nivel(4) == "Bajo"
    assert analisis.nivel(5) == "Medio"
    assert analisis.nivel(10) == "Alto"
    assert analisis.nivel(16) == "Alto"
    assert analisis.nivel(20) == "Crítico"


def test_consenso_con_acuerdo():
    panel = [{"probabilidad": 4, "impacto": 4}, {"probabilidad": 4, "impacto": 5}, {"probabilidad": 3, "impacto": 4}]
    c = analisis.consenso(panel)
    assert (c["probabilidad"], c["impacto"], c["puntaje"]) == (4, 4, 16)
    assert c["acuerdo"] == "Alto"


def test_consenso_con_desacuerdo_es_incertidumbre():
    panel = [{"probabilidad": 1, "impacto": 3}, {"probabilidad": 5, "impacto": 3}]
    c = analisis.consenso(panel)
    assert c["probabilidad"] == 3  # 3,0
    assert c["acuerdo"] == "Bajo"


def test_redondeo_hacia_arriba():
    assert analisis.redondear(2.5) == 3
    assert analisis.redondear(2.4) == 2


def test_consenso_vacio():
    assert analisis.consenso([]) is None


def variable(vid, factor, p, i, **extra):
    return {"id": vid, "factor": factor, "nombre": vid, "tipo": "R", "probabilidad": p, "impacto": i,
            "confiabilidad": "Alta", "tendencia": "Estable", **extra}


def test_revision_detecta_factor_sin_cobertura_y_fuente_debil():
    vs = [variable("E1", "E", 4, 4, confiabilidad="Baja"), variable("E2", "E", 2, 3, tendencia="Sube")]
    r = analisis.revision_reglas(vs)
    assert any("político" in p["tema"] for p in r["puntos_ciegos"])
    assert [d["variable_id"] for d in r["dudosas"]] == ["E1", "E2"]
