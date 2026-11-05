# NewsHarness · kit periodístico para agentes · v0.1 de evaluación

Un entorno de trabajo open source para periodistas que no programan, preparado para adaptar a **Codex, Claude Code y OpenCode**.

Proyecto de código abierto para compartir entre redacciones. No pertenece a ningún medio ni está certificado: es un prototipo en evaluación.

## Qué resuelve

- **Onboarding editorial:** identifica medio, sección, firma, formatos y preferencias. El agente investiga políticas públicas y notas del medio; busca notas del autor y continúa si no encuentra. Separa reglas publicadas, patrones inferidos y preferencias antes de pedir aprobación.
- **Preparación técnica:** diagnostica el equipo, comprueba herramientas y prepara una selección de modelos locales. Las instalaciones y descargas requieren autorización; el agente realiza los pasos técnicos.
- **Discursos y entrevistas (ejemplo central):** inventario con citas literales, tiempos conocidos o anclas de párrafo, selección humana, hipótesis neutrales y evidencia fechada/versionada. El caso real aportado es [Milei en la Universidad Torcuato Di Tella](examples/discursos/caso-real-ditella/LEEME.md); hay un fragmento documentado, no un chequeo completo.
- **Chequeo:** afirmaciones concretas, fuentes abiertas y evidencia verificable; distingue errores, respaldo limitado y asuntos no resueltos.
- **Edición:** aplica el perfil sin cambiar silenciosamente cifras, citas, hechos ni grados de certeza.
- **Datos, OCR y desgrabación:** procedimientos revisables, originales preservados y herramientas locales. Las rutas de fuentes iniciales cubren Argentina, México, Perú, Colombia y Costa Rica. El onboarding acepta cualquier medio; los otros países aún no tienen rutas curadas.

- **Análisis con Python sin programar:** el agente escribe y ejecuta scripts reproducibles (variaciones, inflación acumulada, deflactar, cruces, gráficos) y entrega la respuesta en lenguaje de nota.
- **Versiones con git sin jerga:** «guardá esta versión», «¿qué cambié desde ayer?», «volvé a la de las 10», sin riesgo de perder trabajo ni subir nada sin permiso.
- **Fuentes de Argentina:** INDEC, BCRA (API v4.0), Series de Tiempo de datos.gob.ar, Boletín Oficial y normativa, verificadas el 3/11/2026.
- **INDEC por API:** la skill `newsharness-indec` consulta las 19 tablas oficiales del Catálogo API-INDEC (inflación, canastas, pobreza, empleo, actividad, comercio exterior, población) con procedencia, signos convencionales y cita lista. Requiere un token personal del INDEC que el periodista guarda fuera del chat. Adaptada de [indec-api-skill](https://github.com/jonymusky/indec-api-skill) de Jony Musky (MIT).

Splash, video y publicación automática quedan fuera de esta versión.

## Para empezar, sin configurar a mano

**Instalación recomendada para periodistas:** seguí [INSTALAR.md](INSTALAR.md). Con un ZIP y un texto para pegar, tu agente instala NewsHarness de forma global y queda disponible en cualquier consulta, sin tocar tus instrucciones propias.

Para probar el kit dentro de su propia carpeta, sin instalarlo:

1. Descargá el kit: en GitHub, botón **Code → Download ZIP** (y descomprimilo), o `git clone` si usás git. Abrí la carpeta en el agente que ya usás.
2. Pedile lo siguiente:

> Leé AGENTS.md y la skill de onboarding de este kit. Revisá las instrucciones de tu adaptador, diagnosticá mi equipo y explicame qué herramientas y descargas faltan. No instales ni transmitas material privado sin mi autorización. Después guiame para configurar mi perfil editorial, investigando el medio y mis notas publicadas. Conservá mis originales y terminá con una prueba de ejemplo.

El agente debe leer `adapters/` y usar los comandos reales de `python3 scripts/newsharness.py --help`. No debe inventar opciones ni declarar preparada una función cuyo motor falta. En Windows puede corresponder `py -3` en lugar de `python3`.

**Requisito de arranque:** contar con uno de los agentes y una sesión autorizada. Si falta Python u otra herramienta, el agente debe explicar el plan de instalación apropiado al sistema. En equipos administrados por el diario puede ser necesaria intervención de Sistemas; el kit no elude restricciones.

## Qué contiene la carpeta

- `AGENTS.md`: reglas compartidas del proyecto.
- `skills/`: procedimientos reutilizables con instrucciones y referencias.
- `adapters/`: instrucciones particulares de cada agente.
- `scripts/`: diagnóstico, perfil y ejecutores locales.
- `config/`: catálogo acotado de herramientas y artefactos.
- `examples/discursos/`: caso central real documentado parcialmente y ejercicio sintético separado. `demo-publica/` conserva la prueba ficticia anterior como regresión; `pruebas-tecnicas/` contiene fixtures de OCR y silencio.
- `tests/`: pruebas automatizadas.
- `docs/`: criterios editoriales, seguridad, alcance y verificación.

## Ejemplo central: discurso → inventario → selección → evidencia

El [módulo de discursos](docs/DISCURSOS.md) adapta el documento metodológico aportado por el usuario sin ejecutar su pedido interno de construir una app. La demostración usa el [video elegido](https://www.youtube.com/watch?v=6KxqkedLOO4), no traslada las frases de la entrevista distinta mencionada en aquel documento.

> Usá newsharness-discursos con este material. Conservá el original, separá hechos, proyecciones, promesas y opiniones, y armá un inventario con citas exactas. No inventes minutos. Mostrame qué se pudo comprobar y qué falta; esperá mi selección antes de investigar. El informe debe distinguir datos disponibles al hablar de revisiones posteriores y quedar pendiente de revisión humana, sin publicación automática.

El validador adicional `scripts/validate_discourse.py` comprueba anclajes y consistencia del expediente; no verifica la verdad ni autentica quién aprobó. La ficha real conserva tiempos exactos `null`: el enlace 43:36 señala un segmento de subtítulos, no precisión de palabra. El [ejercicio sintético](examples/discursos/ejercicio-sintetico/transcripcion.txt) prueba estructura y salvaguardas sin atribuir frases inventadas a una persona real.

## Qué significa «local»

El OCR y el reconocimiento de audio pueden ejecutarse en el equipo después de instalar los motores y descargar sus modelos. Eso **no convierte al agente completo en un modelo local**. El proveedor de Codex, Claude Code u OpenCode puede recibir mensajes, archivos o salidas de herramientas según su configuración.

Si el material es confidencial, no debe abrirse en un agente remoto hasta revisar el flujo de datos. Los permisos reales deben configurarse por herramienta; un archivo de instrucciones o un entorno virtual de Python no equivale a un sandbox.

## Estado y comprobaciones

Consultar `docs/VERIFICACION.md` para ver exactamente qué se ejecutó, qué pasó y qué requiere pruebas en equipos reales. El soporte documental de tres agentes no equivale a haber validado los tres entornos de ejecución.

Las decisiones automáticas de modelo son propuestas iniciales, no garantías de velocidad o calidad. Las entrevistas, citas, nombres y cifras siempre requieren revisión contra la fuente original.

## Licencia y contribuciones

Código, skills y documentación se publican bajo [licencia MIT](LICENSE): se pueden usar, adaptar y redistribuir en cualquier redacción conservando el aviso de copyright. Para aportar, ver [CONTRIBUTING.md](CONTRIBUTING.md); para reportar un problema de seguridad, [SECURITY.md](SECURITY.md).

Los motores y modelos externos (Tesseract, whisper.cpp, FFmpeg, PDFium) tienen sus propias licencias y no se incluyen en el repositorio: ver `docs/TERCEROS.md`. Tampoco se incluyen cuentas, claves, datos reales de periodistas, modelos de audio ni software instalado del sistema.
