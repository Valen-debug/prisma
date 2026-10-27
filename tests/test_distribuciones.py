"""Reglas de conteo y reserva de temas de los gráficos operativos."""
import analisis


def test_reportes_descartados_solo_en_estado_y_temas_reservados():
    filas = [
        {'estado': 'Validada', 'variable': 'Seguridad', 'municipio': 'Cali', 'sensible': True},
        {'estado': 'Por validar', 'variable': 'Nuevo tema', 'municipio': 'Cali', 'sensible': False},
        {'estado': 'Descartada', 'variable': 'Otro tema', 'municipio': 'Bogotá', 'sensible': False},
    ]
    r = analisis.graficos_senales(filas)
    assert sum(x['cantidad'] for x in r['estados']) == 3
    assert sum(x['cantidad'] for x in r['temas']) == 2
    assert r['lugares'] == [{'etiqueta': 'Cali', 'cantidad': 2}]
    assert 'Seguridad' not in [x['etiqueta'] for x in r['temas']]
    assert 'Tema reservado' in [x['etiqueta'] for x in r['temas']]
    autorizados = analisis.graficos_senales(filas, ver_sensible=True)
    assert 'Seguridad' in [x['etiqueta'] for x in autorizados['temas']]


def test_categorias_agrupadas_conservan_total():
    filas = analisis.distribucion_grafico({str(i): i for i in range(1, 9)}, limite=6, resto='Resto')
    assert len(filas) == 6
    assert sum(x['cantidad'] for x in filas) == 36
    assert filas[-1] == {'etiqueta': 'Resto', 'cantidad': 6}


def test_responsables_compartidos_sin_repetir_y_sin_asignar():
    estados = {
        'A': {'avance': 'En curso', 'actores': 'Dirección, Operaciones, Dirección'},
        'B': {'avance': None, 'actores': ''},
    }
    r = analisis.graficos_compromisos([{'id': 'A'}, {'id': 'B'}], estados)
    assert sum(x['cantidad'] for x in r['avances']) == 2
    assert {x['etiqueta']: x['cantidad'] for x in r['responsables']} == {
        'Dirección': 1, 'Operaciones': 1, 'Sin asignar': 1,
    }
    vacio = analisis.graficos_compromisos([], {})
    assert not vacio['responsables']
    assert sum(x['cantidad'] for x in vacio['avances']) == 0
