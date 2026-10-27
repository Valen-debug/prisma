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
from datetime import datetime, timedelta

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


def distribucion_grafico(conteos, limite=None, resto="Otros"):
    """Agrupa categorías conservando el total, incluso al limitar las barras."""
    filas = [{"etiqueta": k, "cantidad": v} for k, v in conteos.items()]
    filas.sort(key=lambda x: (-x["cantidad"], x["etiqueta"]))
    if limite and len(filas) > limite:
        filas = filas[:limite - 1] + [{"etiqueta": resto, "cantidad": sum(f["cantidad"] for f in filas[limite - 1:])}]
    return filas


def graficos_senales(filas, ver_sensible=False):
    estados = {"Validada": 0, "Por validar": 0, "Descartada": 0}
    temas, lugares = {}, {}
    for s in filas:
        estado = s["estado"]
        estados[estado] = estados.get(estado, 0) + 1
        if estado == "Descartada":
            continue
        tema = "Tema reservado" if s.get("sensible") and not ver_sensible else (s.get("variable") or "Sin tema asignado")
        lugar = s.get("municipio") or "Sin ubicación"
        temas[tema] = temas.get(tema, 0) + 1
        lugares[lugar] = lugares.get(lugar, 0) + 1
    return {"estados": [{"etiqueta": k, "cantidad": v} for k, v in estados.items()],
            "temas": distribucion_grafico(temas, 6, "Resto de temas"),
            "lugares": distribucion_grafico(lugares, 6, "Resto de ubicaciones")}


def graficos_compromisos(compromisos, estados):
    avances = {"Sin iniciar": 0, "En curso": 0, "Cumplido": 0, "Atrasado": 0}
    responsables = {}
    for v in compromisos:
        e = estados[v["id"]]
        avance = e.get("avance") or "Sin iniciar"
        avances[avance] = avances.get(avance, 0) + 1
        actores = set(a.strip() for a in (e.get("actores") or "").split(",") if a.strip()) or {"Sin asignar"}
        for actor in actores:
            responsables[actor] = responsables.get(actor, 0) + 1
    return {"avances": [{"etiqueta": k, "cantidad": v} for k, v in avances.items()],
            "responsables": distribucion_grafico(responsables, 6, "Resto de responsables")}


def actividad_tablero(con, fecha=None):
    """Conteos de recepción, no historia de riesgo ni de fechas de validación."""
    fecha = (fecha or hora_local()).replace(second=0, microsecond=0)
    desde = fecha - timedelta(days=VENTANA_DIAS)
    lunes = fecha.replace(hour=0, minute=0) - timedelta(days=fecha.weekday(), weeks=7)
    semanas = []
    for i in range(8):
        inicio = lunes + timedelta(weeks=i)
        fin = min((inicio + timedelta(days=6)).date(), fecha.date())
        semanas.append({"inicio": inicio.strftime("%Y-%m-%d"),
                        "etiqueta": f"{inicio:%d/%m}–{fin:%d/%m}",
                        "validadas": 0, "pendientes": 0, "descartadas": 0, "otros": 0})
    validadas = vinculadas = 0
    por_lugar = {}
    filas = con.execute("SELECT fecha, estado, variable_id, municipio_id FROM senales WHERE fecha >= ? AND fecha <= ?",
                        (min(desde, lunes).strftime("%Y-%m-%d %H:%M"), fecha.strftime("%Y-%m-%d %H:%M")))
    claves = {"Validada": "validadas", "Por validar": "pendientes", "Descartada": "descartadas"}
    for fila in filas:
        try:
            recibida = datetime.strptime(fila["fecha"][:16], "%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            continue
        if recibida >= desde and fila["estado"] == "Validada":
            validadas += 1
            vinculadas += int(fila["variable_id"] is not None)
            mid = fila["municipio_id"]
            por_lugar[mid] = por_lugar.get(mid, 0) + 1
        if recibida >= lunes:
            indice = (recibida.date() - lunes.date()).days // 7
            semanas[indice][claves.get(fila["estado"], "otros")] += 1
    avances = {"Sin iniciar": 0, "En curso": 0, "Cumplido": 0, "Atrasado": 0}
    for fila in con.execute("SELECT avance, COUNT(*) AS n FROM decisiones WHERE estado = 'Aprobada' GROUP BY avance"):
        estado = fila["avance"] or "Sin iniciar"
        avances[estado] = avances.get(estado, 0) + fila["n"]
    pendientes = con.execute("SELECT COUNT(*) FROM senales WHERE estado = 'Por validar'").fetchone()[0]
    return {"validadas": validadas, "vinculadas": vinculadas, "sin_variable": validadas - vinculadas,
            "pendientes": pendientes, "por_lugar": por_lugar, "semanas": semanas,
            "recibidas": sum(sum(s[k] for k in ("validadas", "pendientes", "descartadas", "otros")) for s in semanas),
            "compromisos": [{"estado": k, "cantidad": v} for k, v in avances.items()],
            "total_compromisos": sum(avances.values()), "desde": desde.strftime("%d/%m/%Y"),
            "hasta": fecha.strftime("%d/%m/%Y"), "actualizado": fecha.strftime("%d/%m/%Y · %H:%M")}


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
