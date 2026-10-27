# Prisma · Lectura de entorno

Plataforma genérica para que cualquier organización lea su entorno con el método PESTEL, uniendo dos miradas: los datos técnicos y lo que reportan desde el campo quienes viven la operación o el territorio.

## Enfoques: una instalación por cliente

El código es el mismo para todas; cada plantilla (`plantillas.py` y `plantilla_*.py`) define las palabras, los actores, los lugares, las variables y los datos de ejemplo:

| Versión (enfoque) | Para quién | Quién reporta |
|---|---|---|
| **General** (por defecto) | Cualquier organización: empresas, entidades públicas, organizaciones sociales | Comunidad, colaboradores, proveedores, aliados, clientes |
| Territorio cafetero y cacaotero | Desarrollo rural, gobiernos locales | Productores, líderes, asociaciones |
| Empresa compradora de cacao y café | Exportadoras, chocolateras, tostadoras | Productores proveedores, técnicos de compras, centros de acopio |
| Empresa industrial · planta de empaques | Empresas con plantas y operación logística | Colaboradores, transportadores, proveedores, vecinos |

Cada cliente recibe su propia instalación con un solo enfoque; dentro de la aplicación no se cambia. El enfoque se elige al instalar en `config.py` (o con la variable de entorno `PRISMA_ENFOQUE`): `general` (por defecto), `territorio`, `cadena` o `industrial`. Para un cliente nuevo se agrega un archivo de plantilla; no se tocan las pantallas.

Todos los datos son de demostración: los lugares son ejemplos y las señales de campo no son reportes reales.

## Qué hace

- **Lectura PESTEL técnica**: cada variable tiene probabilidad × impacto (1 a 25), fuente, confiabilidad y área.
- **Voz del territorio**: un formulario público para el celular (`/reportar`), sin cuenta y en menos de un minuto. Si no hay señal, el reporte se guarda en el celular y se envía solo cuando vuelve la conexión.
- **Validación**: la técnica de campo valida o descarta cada señal antes de que cuente.
- **Dos lecturas y brechas**: la lectura de la comunidad es la gravedad promedio de las señales validadas de los últimos 60 días × qué tanto se repiten. Cuando técnica y comunidad se separan 6 puntos o más, aparece una brecha. El nivel final usa la más alta de las dos.
- **Territorio**: mapa de municipios, ficha por municipio y ficha imprimible para asamblea con código QR.
- **Escenarios**: lluvias, El Niño, precio del cacao, precio del café, exigencias europeas (EUDR), orden público y cambios de programas.
- **Compromisos**: las decisiones aprobadas llevan actores, fecha límite y avance.
- **Inteligencia artificial (Claude, de Anthropic)**: la comunidad cuenta lo que pasa con sus palabras, por voz o con una foto; la IA sugiere el tema y la gravedad, quita nombres, teléfonos y lugares exactos antes de guardar, describe la foto y detecta temas nuevos que todavía no son variables. Para el equipo redacta boletines por lugar. La IA sugiere; una persona valida. Sin clave o sin internet, todo funciona con reglas simples.
- **Escenarios «¿Y si…?» y alerta temprana**: la IA propone un escenario a partir de una pregunta y la persona ajusta los valores antes de guardarlo. Cada escenario avisa cuando empieza a pasar: 3 o más señales validadas en 14 días sobre sus variables en un mismo lugar.
- **Tres métodos de prospectiva con IA** (siempre decide una persona):
  - **Panel de expertos** (método Delphi), al registrar o editar una variable: seis expertos, uno por cada factor PESTEL, califican probabilidad e impacto por separado. Prisma muestra el consenso y cuánto discrepan; si no se ponen de acuerdo, hay alta incertidumbre.
  - **Efecto dominó** (rueda de futuros), en «¿Y si…?»: además de las variables que cambian, la IA muestra la cadena de consecuencias directas e indirectas entre factores.
  - **«¿Dónde podemos estar equivocados?»**, desde el tablero: la IA hace de abogado del diablo y señala puntos ciegos, calificaciones dudosas y supuestos. Sin IA hace una revisión básica por reglas.
- **Seguimiento público** (`/seguimiento`): la comunidad ve qué compromisos salieron de sus reportes.
- **Informe**: PDF imprimible, Excel y CSV. Los reportes de seguridad son anónimos y su texto no sale en el Excel ni lo ve el rol de TI.

## Cuentas de demostración

| Usuario | Contraseña | Rol |
|---|---|---|
| coordinacion | coordinacion123 | Dirección (coordinación o gerencia): decide y fija compromisos |
| tecnico | tecnico123 | Análisis (técnica de campo o analista): califica variables y valida señales |
| ti | ti123 | Administración TI: fuentes, accesos y datos de ejemplo |

## Cómo correrlo en el computador

```
pip install -r requirements.txt
python app.py
```

Abra http://127.0.0.1:5000. La base de datos `prisma_territorial.db` se crea sola la primera vez. Para volver a los datos de ejemplo: `python database.py`, o el botón «Restablecer» con la cuenta de TI.

## Publicarlo en PythonAnywhere

1. Suba `prisma.zip` en la pestaña Files y en una consola Bash ejecute `unzip -o prisma.zip`.
2. `pip install --user -r prisma/requirements.txt`
3. En la pestaña Web, el archivo WSGI debe apuntar a la carpeta `prisma` e importar `from app import app as application`.
4. Pulse Reload.

El formulario sin conexión necesita https (PythonAnywhere ya lo trae). El mapa carga las calles de OpenStreetMap, así que necesita internet en el navegador.

## Activar la IA

1. Cree una cuenta en console.anthropic.com, cargue crédito (Billing) y genere una clave (API keys).
2. Entre a Prisma con la cuenta `ti`, abra el menú del usuario → «Inteligencia artificial», pegue la clave y pulse «Guardar y probar».
   También se puede definir como variable de entorno `ANTHROPIC_API_KEY` en el archivo WSGI.

Para controlar el gasto hay un tope de consultas diarias (por defecto 150; se cambia con `PRISMA_IA_TOPE_DIA`). El uso del día se ve en esa misma pantalla. El panel de expertos usa 6 consultas cada vez.

## Seguridad

- Contraseñas cifradas (scrypt), permisos por rol en el servidor y bitácora de cada cambio.
- Protección CSRF en todos los formularios y cookies de sesión `HttpOnly` y `SameSite`.
- La clave de las sesiones se genera al azar la primera vez (o se define con `PRISMA_SECRET`).
- La hora es la de Colombia aunque el servidor esté en otro país (`PRISMA_ZONA`).
- Sin modo de depuración en producción (solo con `PRISMA_DEBUG=1`).

## Pruebas

```
pip install pytest
python -m pytest -q
```

El modelo se cambia con la variable `PRISMA_MODELO` (por defecto `claude-haiku-4-5-20251001`, rápido y económico).

## Tecnología

Python 3 · Flask · SQLite · Anthropic (Claude) · Bootstrap 5 · Chart.js · Leaflet · qrcode-generator · openpyxl. Todas las librerías del navegador vienen incluidas en `static/vendor`.

## Fuentes del contexto

Valora Analitik (producción de café 2026), La República (cacao), Mongabay (reglamento EUDR), El Cronista (extorsión a caficultores en el Huila), Vanguardia (posesión presidencial 2026) y Naciones Unidas (ODS).
