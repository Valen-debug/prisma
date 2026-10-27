"""
Motor de análisis de Prisma Territorial.

Lectura técnica de una variable = probabilidad x impacto (1 a 25).
  Bajo 1-4 | Medio 5-9 | Alto 10-16 | Crítico 20-25
Lectura comunitaria de una variable = gravedad promedio que reporta la gente (1-5)
  x presión de la señal según cuántas veces se repite (1 señal = 2, 2 = 3, 3 = 4, 4 o más = 5).
  Solo cuentan las señales validadas de los últimos 60 días.
Brecha = lectura comunitaria - lectura técnica.
  +6 o más: la comunidad ve más riesgo del que muestran los datos (alerta temprana).
  -6 o menos: la comunidad lo percibe menos (necesita información o pedagogía).
Nivel efectivo = el mayor entre la lectura técnica y la comunitaria; es el que activa alertas y decisiones.
"""
from datetime import timedelta

from database import FACTORES, hora_local

NOMBRE_FACTOR = dict(FACTORES)
VENTANA_DIAS = 60
UMBRAL_BRECHA = 6


def nivel(puntaje):
    if puntaje is None:
        return "Sin datos"
    if puntaje >= 20:
        return "Crítico"
    if puntaje >= 10:
        return "Alto"
    if puntaje >= 5:
        return "Medio"
    return "Bajo"


CLASE_NIVEL = {"Crítico": "critico", "Alto": "alto", "Medio": "medio", "Bajo": "bajo", "Sin datos": "nd"}


def presion(n):
    return 0 if n == 0 else min(5, n + 1)


def efectos_activos(con, escenarios_activos):
    efectos = {}
    if not escenarios_activos:
        return efectos
    marcas = ",".join("?" * len(escenarios_activos))
    for f in con.execute(f"SELECT variable_id, probabilidad, impacto FROM escenario_efectos WHERE escenario_id IN ({marcas})",
                         list(escenarios_activos)).fetchall():
        p, i = efectos.get(f["variable_id"], (0, 0))
        efectos[f["variable_id"]] = (max(p, f["probabilidad"]), max(i, f["impacto"]))
    return efectos


def senales_validas(con, municipio=None):
    desde = (hora_local() - timedelta(days=VENTANA_DIAS)).strftime("%Y-%m-%d %H:%M")
    sql = "SELECT * FROM senales WHERE estado = 'Validada' AND fecha >= ?"
    args = [desde]
    if municipio:
        sql += " AND municipio_id = ?"
        args.append(municipio)
    return con.execute(sql, args).fetchall()


def lectura_comunitaria(senales):
    """{variable_id: {"n", "gravedad", "puntaje"}} a partir de una lista de señales."""
    grupos = {}
    for s in senales:
        grupos.setdefault(s["variable_id"], []).append(s["gravedad"])
    salida = {}
    for vid, gs in grupos.items():
        prom = sum(gs) / len(gs)
        salida[vid] = {"n": len(gs), "gravedad": round(prom, 1), "puntaje": round(prom * presion(len(gs)))}
    return salida


def evaluar(con, escenarios_activos=(), municipio=None):
    """Variables con lectura técnica (con escenarios), lectura comunitaria, brecha y nivel efectivo."""
    efectos = efectos_activos(con, escenarios_activos)
    comunidad = lectura_comunitaria(senales_validas(con, municipio))
    resultado = []
    for v in con.execute("SELECT * FROM variables ORDER BY factor, id").fetchall():
        d = dict(v)
        d["factor_nombre"] = NOMBRE_FACTOR.get(d["factor"], d["factor"])
        d["puntaje_base"] = d["probabilidad"] * d["impacto"]
        p, i = d["probabilidad"], d["impacto"]
        if d["id"] in efectos:
            ep, ei = efectos[d["id"]]
            p, i = max(p, ep), max(i, ei)
        d["prob_ef"], d["imp_ef"] = p, i
        d["puntaje"] = p * i                      # lectura técnica
        d["modificada"] = d["puntaje"] != d["puntaje_base"]
        c = comunidad.get(d["id"])
        d["com_n"] = c["n"] if c else 0
        d["com_gravedad"] = c["gravedad"] if c else None
        d["com_puntaje"] = c["puntaje"] if c else None
        d["brecha"] = (d["com_puntaje"] - d["puntaje"]) if c else None
        d["efectivo"] = max(d["puntaje"], d["com_puntaje"] or 0)
        d["origen"] = "Comunidad" if c and d["com_puntaje"] > d["puntaje"] else "Técnica"
        d["nivel"] = nivel(d["efectivo"])
        d["nivel_tecnico"] = nivel(d["puntaje"])
        d["nivel_comunidad"] = nivel(d["com_puntaje"])
        d["clase"] = "oportunidad" if d["tipo"] == "O" else CLASE_NIVEL[d["nivel"]]
        d["clase_tecnica"] = "oportunidad" if d["tipo"] == "O" else CLASE_NIVEL[d["nivel_tecnico"]]
        d["clase_comunidad"] = "oportunidad" if d["tipo"] == "O" and c else CLASE_NIVEL[d["nivel_comunidad"]]
        resultado.append(d)
    return resultado


def indices_factores(variables, campo="efectivo"):
    """Índice por factor: promedio de los riesgos. campo = 'efectivo', 'puntaje' (técnico), 'puntaje_base' o 'com_puntaje'."""
    salida = []
    for k, nombre in FACTORES:
        riesgos = [v[campo] for v in variables if v["factor"] == k and v["tipo"] == "R" and v[campo] is not None]
        indice = round(sum(riesgos) / len(riesgos), 1) if riesgos else None
        niv = nivel(indice)
        salida.append({
            "clave": k, "letra": "E" if k == "A" else k, "nombre": nombre,
            "indice": indice, "nivel": niv, "clase": CLASE_NIVEL[niv],
            "oportunidades": len([v for v in variables if v["factor"] == k and v["tipo"] == "O"]),
            "variables": len([v for v in variables if v["factor"] == k]),
            "senales": sum(v["com_n"] for v in variables if v["factor"] == k),
        })
    return salida


def brechas(variables):
    """Variables con brecha significativa entre la lectura comunitaria y la técnica."""
    riesgos = [v for v in variables if v["tipo"] == "R" and v["brecha"] is not None]
    mas = [v for v in riesgos if v["brecha"] >= UMBRAL_BRECHA]
    menos = [v for v in riesgos if v["brecha"] <= -UMBRAL_BRECHA]
    return (sorted(mas, key=lambda v: -v["brecha"]), sorted(menos, key=lambda v: v["brecha"]))


def decisiones_sugeridas(variables):
    """Riesgos con nivel efectivo alto/crítico y oportunidades con puntaje >= 12."""
    items = [v for v in variables
             if (v["tipo"] == "R" and v["efectivo"] >= 10) or (v["tipo"] == "O" and v["efectivo"] >= 12)]
    return sorted(items, key=lambda v: v["efectivo"], reverse=True)


# ---------------------------------------------------------------- señales de entrada de los escenarios
ENTRADA_DIAS = 14
ENTRADA_MINIMO = 3


def escenarios_en_entrada(con):
    """Escenarios que empiezan a pasar: en algún lugar hay ENTRADA_MINIMO o más señales validadas,
    en los últimos ENTRADA_DIAS días, sobre las variables que ese escenario mueve."""
    desde = (hora_local() - timedelta(days=ENTRADA_DIAS)).strftime("%Y-%m-%d %H:%M")
    salida = []
    for e in con.execute("SELECT * FROM escenarios").fetchall():
        vids = [r[0] for r in con.execute("SELECT variable_id FROM escenario_efectos WHERE escenario_id = ?", (e["id"],))]
        if not vids:
            continue
        filas = con.execute(
            f"""SELECT m.id, m.nombre, COUNT(*) AS n FROM senales s JOIN municipios m ON m.id = s.municipio_id
                WHERE s.estado = 'Validada' AND s.fecha >= ? AND s.variable_id IN ({','.join('?' * len(vids))})
                GROUP BY m.id HAVING n >= ? ORDER BY n DESC""", (desde, *vids, ENTRADA_MINIMO)).fetchall()
        if filas:
            salida.append({"id": e["id"], "nombre": e["nombre"], "lugares": [dict(f) for f in filas],
                           "total": sum(f["n"] for f in filas)})
    return sorted(salida, key=lambda x: -x["total"])


# ---------------------------------------------------------------- panel de expertos (método Delphi)
def redondear(x):
    return int(x + 0.5)  # 2,5 → 3 (round() de Python daría 2)


def consenso(opiniones):
    """Resume un panel: el promedio es la calificación sugerida y la dispersión mide la incertidumbre.
    Rango (máximo - mínimo) de 0-1 = acuerdo alto, 2 = medio, 3 o más = desacuerdo."""
    if not opiniones:
        return None
    ps = [o["probabilidad"] for o in opiniones]
    is_ = [o["impacto"] for o in opiniones]
    p, i = redondear(sum(ps) / len(ps)), redondear(sum(is_) / len(is_))
    rango = max(max(ps) - min(ps), max(is_) - min(is_))
    acuerdo = "Alto" if rango <= 1 else "Medio" if rango == 2 else "Bajo"
    return {"probabilidad": p, "impacto": i, "puntaje": p * i, "nivel": nivel(p * i), "clase": CLASE_NIVEL[nivel(p * i)],
            "rango_p": f"{min(ps)} a {max(ps)}", "rango_i": f"{min(is_)} a {max(is_)}", "rango": rango, "acuerdo": acuerdo,
            "expertos": len(opiniones)}


# ---------------------------------------------------------------- revisión crítica sin IA
def revision_reglas(variables):
    """Versión básica de «¿Dónde podemos estar equivocados?» cuando no hay IA: revisa cobertura y coherencia."""
    puntos, dudosas = [], []
    for k, nombre in FACTORES:
        n = len([v for v in variables if v["factor"] == k])
        if n < 2:
            puntos.append({"factor_nombre": nombre, "tema": f"Solo {n} variable{'s' if n != 1 else ''} en {nombre.lower()}",
                           "por_que": "Con tan poca cobertura el índice de este factor puede no representar el entorno real."})
    for v in variables:
        if v["tipo"] == "R" and v["confiabilidad"] == "Baja" and v["probabilidad"] * v["impacto"] >= 10:
            dudosas.append({"variable_id": v["id"], "nombre": v["nombre"], "antes": f"P{v['probabilidad']}×I{v['impacto']}",
                            "propuesta": "Verificar la fuente",
                            "observacion": "Nivel alto apoyado en una fuente de confiabilidad baja."})
        elif v["tendencia"] == "Sube" and v["probabilidad"] <= 2:
            dudosas.append({"variable_id": v["id"], "nombre": v["nombre"], "antes": f"P{v['probabilidad']}×I{v['impacto']}",
                            "propuesta": f"P{v['probabilidad'] + 1}×I{v['impacto']}",
                            "observacion": "La tendencia sube, pero la probabilidad está calificada como baja."})
    return {"puntos_ciegos": puntos[:3], "dudosas": dudosas[:3],
            "supuestos": ["Que las calificaciones de probabilidad e impacto siguen vigentes desde su última actualización."]}
