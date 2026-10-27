# Prisma · Lectura de entorno

Aplicación web para que cualquier organización lea su entorno con el método **PESTEL** (Político, Económico, Social, Tecnológico, Ecológico y Legal) y decida a tiempo. Sirve igual para una planta industrial, una multinacional de café, una entidad pública o una organización social.

Prisma une dos lecturas del entorno:

- **Lectura técnica**: variables PESTEL calificadas por el analista con datos de fuentes oficiales, gremios y prensa.
- **Lectura de grupos de interés**: lo que reportan comunidades, colaboradores, proveedores, aliados y clientes desde el celular.

Cuando las dos no coinciden aparece una **brecha**: una alerta temprana o una señal de que hace falta informar mejor. La inteligencia artificial apoya cada paso, pero siempre decide una persona.

> Prototipo académico de Arquitectura Empresarial. Todos los datos son de demostración.

## El flujo

| Paso | Quién | Dónde |
|---|---|---|
| 1. Registrar | Analista | Variables PESTEL, Agente vigía |
| 2. Escuchar | Grupos de interés y analista | Formulario para reportar, Grupos de interés |
| 3. Leer | Dirección y analista | Inicio, Tablero, Mapa |
| 4. Anticipar | Dirección y analista | Escenarios |
| 5. Decidir | Dirección | Compromisos, Informe |

## Qué hace

- **Variables PESTEL**: cada variable tiene probabilidad × impacto (1 a 25), tendencia, plazo, fuente y confiabilidad. Niveles: Bajo 1–4, Medio 5–9, Alto 10–16, Crítico 20–25.
- **Grupos de interés**: un formulario público para el celular (`/reportar`), sin cuenta y en menos de un minuto, por texto, voz o foto. Funciona sin señal: el reporte se envía cuando vuelve la conexión. El analista valida cada señal antes de que cuente.
- **Dos lecturas y brechas**: la lectura de grupos de interés es la gravedad promedio de las señales validadas de los últimos 60 días × qué tanto se repiten. Con 6 puntos o más de diferencia aparece una brecha. El nivel final usa la más alta de las dos.
- **Tablero y mapa**: indicadores, radar con las dos lecturas, alertas, brechas y oportunidades; mapa de los lugares de la organización con su ficha.
- **Escenarios**: paro nacional, temporada de lluvias, El Niño, alza del dólar, cambio de prioridades del gobierno, ciberataque y deterioro del orden público, combinables. Cada escenario avisa cuando empieza a pasar (3 o más señales validadas en 14 días en un mismo lugar).
- **Compromisos**: las decisiones sugeridas (riesgos de 10 o más, oportunidades de 12 o más) se aprueban con responsables, fecha límite y avance. Lo aprobado se publica en `/seguimiento`.
- **Informe**: imprimible en PDF, en Excel y en CSV, con resumen ejecutivo redactado por la IA.

## Inteligencia artificial

Prisma usa Claude (Anthropic). La IA sugiere y una persona revisa; sin clave o sin internet, la app funciona igual con reglas simples.

**Tres métodos de prospectiva:**

- **Panel de expertos** (método Delphi), al registrar o editar una variable: seis expertos, uno por cada factor PESTEL, califican probabilidad e impacto por separado. Prisma muestra el consenso y cuánto discrepan; si no se ponen de acuerdo, hay alta incertidumbre.
- **Efecto dominó** (rueda de futuros), en «¿Y si…?»: a partir de una pregunta, la IA propone qué variables cambian y la cadena de consecuencias directas e indirectas entre factores.
- **«¿Dónde podemos estar equivocados?»**, desde el tablero: la IA hace de abogado del diablo y señala puntos ciegos, calificaciones dudosas y supuestos.

**Además:**

- **Agente vigía**: busca noticias recientes en internet y propone señales con fuente y calificación de impacto, novedad y credibilidad.
- **Lectura de reportes**: sugiere el tema y la gravedad, quita nombres, teléfonos y lugares exactos, describe fotos y detecta temas nuevos.
- **Boletines** por lugar y para el informe.

## Cuentas de demostración

| Usuario | Contraseña | Rol |
|---|---|---|
| coordinacion | coordinacion123 | Dirección: decide y fija compromisos |
| tecnico | tecnico123 | Analista de entorno: califica variables y valida señales |
| ti | ti123 | Administración TI: fuentes, accesos, IA y datos de ejemplo |

## Cómo correrlo en el computador

Necesita Python 3.10 o más nuevo (en Windows, marque «Add Python to PATH» al instalarlo).

```
pip install -r requirements.txt
python app.py
```

Abra http://127.0.0.1:5000. La base de datos se crea sola la primera vez con los datos de ejemplo. Para volver a ellos: `python database.py`, o el botón «Restablecer» con la cuenta de TI.

En Windows, si `pip` o `python` no se reconocen, use `py -m pip install -r requirements.txt` y `py app.py`. En Mac, `pip3` y `python3`.

## Publicarlo en PythonAnywhere

1. Suba `prisma.zip` en la pestaña Files y en una consola Bash ejecute `unzip -o prisma.zip`.
2. Si viene de una versión anterior, borre `prisma/prisma_territorial.db`.
3. `pip install --user -r prisma/requirements.txt`
4. En la pestaña Web, el archivo WSGI debe apuntar a la carpeta `prisma` e importar `from app import app as application`.
5. Pulse Reload.

## Activar la IA

1. Cree una cuenta en console.anthropic.com (es distinta del plan Pro de Claude), cargue crédito en Billing y cree una clave en API keys.
2. Entre a Prisma con la cuenta `ti`, abra el menú del usuario → «Inteligencia artificial», pegue la clave y pulse «Guardar y probar».

La clave se guarda en la base de datos del servidor y nunca se sube a GitHub. Hay un tope de 150 consultas a la IA por día para controlar el gasto; el panel de expertos usa 6 por consulta y el agente vigía usa además la búsqueda web, que tiene un costo adicional.

## Seguridad

- Contraseñas cifradas (scrypt), permisos por rol en el servidor y bitácora de cada cambio.
- Protección CSRF en todos los formularios y cookies de sesión `HttpOnly` y `SameSite`.
- Consultas a la base de datos con parámetros (sin inyección de SQL).
- Datos personales protegidos antes de guardar; los reportes de seguridad son siempre anónimos.
- La hora es la de Colombia aunque el servidor esté en otro país. Sin modo de depuración en producción.

## Código

Arquitectura por capas sencilla; el código está en español.

| Archivo | Qué hace |
|---|---|
| `app.py` | Rutas, permisos, CSRF y exportaciones |
| `analisis.py` | Motor PESTEL: niveles, lecturas, brechas, escenarios y consenso del panel |
| `ia.py` | Funciones de IA, con su respaldo sin IA y el tope diario |
| `database.py` | Base de datos y datos de ejemplo |
| `plantillas.py`, `plantilla_*.py` | Textos y datos de ejemplo de cada enfoque |
| `templates/`, `static/` | Pantallas, estilos y librerías (todo local) |
| `tests/` | Pruebas del motor: `pip install pytest` y `python -m pytest -q` |

**Un solo código para cualquier organización.** Cada instalación usa un enfoque, que se elige en `config.py` o con la variable `PRISMA_ENFOQUE`: `general` (por defecto), `territorio`, `cadena` (comprador de cacao y café) o `industrial`. Para una organización nueva se agrega un archivo de plantilla, sin tocar las pantallas.

**Variables opcionales:** `ANTHROPIC_API_KEY` (clave de la IA), `PRISMA_MODELO` (por defecto `claude-haiku-4-5-20251001`), `PRISMA_IA_TOPE_DIA` (por defecto 150), `PRISMA_SECRET`, `PRISMA_ZONA` y `PRISMA_DEBUG`.

## Tecnología

Python 3 · Flask · SQLite · Claude (Anthropic) · Bootstrap 5 · Chart.js · Leaflet · openpyxl.

## Fuentes del contexto

Valora Analitik (clima y producción 2026), Vanguardia (posesión presidencial 2026), El Cronista (extorsión en las regiones) y Mongabay (reglamento europeo EUDR).
