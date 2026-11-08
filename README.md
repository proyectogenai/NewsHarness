# NewsHarness

**Un kit open source que le enseña a tu agente de IA a trabajar con método periodístico.**

Funciona con **Claude Code, Codex y OpenCode**. Está pensado para periodistas que no programan: vos pedís en lenguaje de redacción («chequeá las cifras de esta nota», «desgrabá la entrevista», «¿cuánto subió la canasta básica en un año?») y el agente hace la parte técnica.

> Desarrollado desde una redacción para agilizar el trabajo periodístico diario. Es un proyecto en desarrollo (versión 0.1): [qué se probó y qué falta](docs/VERIFICACION.md).

## El problema que resuelve

Un agente de IA general escribe rápido, pero no trae las reglas básicas del oficio. Si le falta un dato, puede completarlo con algo que «suena bien». También puede emprolijar una cita hasta cambiarle el sentido. Un comunicado oficial puede terminar tratado como prueba del hecho, y lo que dice un PDF puede tomarse como una orden.

NewsHarness le da al agente **procedimientos y límites**:

- **No inventa.** Las citas se copian literales y las cifras llevan fuente, fecha y unidad. Si algo no se pudo comprobar, queda como «no resuelto», no como verdadero ni como falso.
- **Conserva los originales.** Nunca sobrescribe un audio, un PDF o una planilla. Cada cálculo deja un script que se puede revisar.
- **La persona decide.** El agente propone, pero vos elegís qué chequear y aprobás lo que se publica. **Nunca publica ni envía nada solo.**
- **Cuida el material sensible.** Antes de buscar en Internet una frase o un nombre, evalúa si eso revela información no publicada o una fuente. Tampoco sube archivos a servicios externos sin permiso.
- **Pide permiso antes de instalar.** Si necesita Python, un motor de OCR o un modelo de audio, te explica qué es, de dónde viene y cuánto pesa, y espera tu OK.

## Instalalo con tu agente

No hace falta usar la terminal. Abrí tu agente (Claude Code, Codex u OpenCode) en una **carpeta vacía**, copiá este texto y pegáselo:

```text
Quiero instalar NewsHarness, un kit open source para periodistas, para usarlo en todas mis consultas.
El repositorio oficial es https://github.com/proyectogenai/NewsHarness

1. Descargá el kit SÓLO de ese repositorio, en esta carpeta: con "git clone" si tengo git, o si no
   bajando https://github.com/proyectogenai/NewsHarness/archive/refs/heads/main.zip y descomprimiéndolo.
   No uses otra fuente ni otra copia.
2. Comprobá los archivos con CHECKSUMS.sha256. Si alguno no coincide, frená y avisame.
3. Leé README.md, AGENTS.md y el adaptador de tu agente en adapters/.
4. Instalalo de forma global con el instalador del kit:
   python3 scripts/newsharness.py install-skills --global --agent <claude | codex | opencode, según el agente que sos>
   (en Windows puede ser "py -3" en lugar de "python3").
5. No modifiques mis instrucciones globales (CLAUDE.md, AGENTS.md) ni otros archivos míos.
6. Si falta Python u otra herramienta, explicame qué es, de dónde viene y cuánto pesa, y esperá mi OK antes de instalarla.
7. Al terminar, decime en lenguaje simple qué quedó instalado, cómo se actualiza, cómo se desinstala
   y cómo empiezo la configuración de mi perfil.
```

Cuando termine:

1. **Cerrá y volvé a abrir el agente** para que encuentre las skills nuevas.
2. Desde cualquier carpeta, pedile: **«Configurá mi perfil de NewsHarness»**. El agente te pregunta tu medio, tu sección y tus formatos, investiga las pautas públicas de tu medio y tus notas firmadas, y te muestra el perfil para que lo apruebes.

**Qué queda instalado:** el kit en una carpeta oculta de tu usuario (`~/.newsharness-kit`) y las skills en la carpeta de skills de tu agente. Tus notas, audios y perfil van en una carpeta de trabajo aparte. Para actualizar o desinstalar, pedíselo al agente: «Actualizá NewsHarness con la última versión del repositorio» o «Desinstalá NewsHarness». Si modificaste un archivo del kit, el instalador no lo pisa.

Cada agente tiene su propia instalación: si usás dos, hay que instalarlo en los dos. ¿No podés descargar desde GitHub, o el kit te llegó en un ZIP? Seguí [INSTALAR.md](INSTALAR.md).

## Qué le podés pedir

| Tarea | Ejemplo de pedido | Qué hace el agente |
|---|---|---|
| **Chequear una nota** | «Chequeá las cifras de este borrador antes de que salga» | Inventaría cada afirmación, busca la fuente original y entrega un informe por afirmación con evidencia fechada. |
| **Analizar un discurso o entrevista** | «Armá el inventario de lo que dijo en esta entrevista» | Separa hechos, proyecciones, promesas y opiniones con citas literales ancladas. Espera tu selección antes de investigar. |
| **Desgrabar** | «Desgrabá esta entrevista y sacame las citas» | Transcribe en tu computadora, con marcas de tiempo, y te marca qué citas revisar contra el audio. |
| **Pasar a texto un documento** | «Sacá el texto de este PDF escaneado» | Hace OCR local y señala nombres, cifras y tablas para revisar a ojo. |
| **Trabajar con datos** | «¿Cuánto subió la canasta básica en un año?» | Baja la serie oficial, calcula con un script reproducible y te responde en lenguaje de nota, con la fuente para citar. |
| **Consultar el INDEC** | «Traé la última pobreza por región» | Consulta la API oficial del INDEC con procedencia y signos convencionales (requiere registrarse en el INDEC para obtener un token personal). |
| **Redactar y editar** | «Pasalo a newsletter» · «Dame cinco títulos» | Aplica tu perfil sin cambiar hechos, citas ni grados de certeza. Los cambios quedan a la vista. |
| **Hacer un video** | «Armá un reel con esta frase de la entrevista» · «Ponele subtítulos» | Corta sin sacar la frase de contexto, reencuadra a vertical y pone subtítulos literales con estilo de redes. Te entrega el archivo para que lo revises. |
| **Guardar versiones** | «Guardá esta versión» · «¿Qué cambié desde ayer?» | Usa git por vos, sin jerga y sin subir nada sin permiso. |

## Las skills

Una *skill* es un procedimiento que el agente carga cuando reconoce la tarea. No hace falta nombrarlas, pero podés hacerlo («usá newsharness-factcheck»).

| Skill | Para qué |
|---|---|
| `newsharness-onboarding` | Configurar tu perfil editorial y preparar la computadora. |
| `newsharness-factcheck` | Verificar afirmaciones con inventario completo y evidencia trazable. |
| `newsharness-discursos` | Inventariar y contrastar discursos y entrevistas. |
| `newsharness-transcripcion` | Transcribir audio en forma local, con revisión de citas. |
| `newsharness-ocr` | Pasar a texto escaneos, fotos y PDFs. |
| `newsharness-datos` | Pensar una tabla: unidades, denominadores, comparabilidad. |
| `newsharness-python` | Calcular, cruzar y graficar con scripts reproducibles. |
| `newsharness-indec` | Datos oficiales del INDEC (Argentina) por API. |
| `newsharness-redaccion` | Redactar, editar, acortar y adaptar formatos. |
| `newsharness-video` | Recortar, armar reels, subtítulos y títulos con material propio. |
| `newsharness-git` | Versiones de borradores sin perder trabajo. |

**Fuentes incluidas:** rutas documentales verificadas para **Argentina, México, Perú, Colombia y Costa Rica**, elegidas según el país del hecho y no el del medio. Para Argentina incluye INDEC, BCRA (API v4.0), Series de Tiempo de datos.gob.ar, Boletín Oficial y normativa. Otros países funcionan con el mismo método, sin rutas curadas todavía.

## Antes de usarlo con material reservado

- **«Local» no significa «privado».** El OCR y la transcripción corren en tu computadora, pero el agente (Claude Code, Codex u OpenCode) es un servicio remoto: su proveedor puede recibir lo que escribís en el chat y lo que las herramientas le devuelven. Si el material es confidencial, revisá primero el entorno que aprobó tu medio.
- **Un archivo de instrucciones no es un candado.** Las reglas del kit guían al agente, pero los permisos reales (archivos, red, ejecución) se configuran en cada herramienta.
- **El resultado es un borrador.** Las entrevistas, citas, nombres y cifras siempre requieren revisión contra la fuente original. La responsabilidad editorial es de las personas.

## Probarlo sin instalar

Descargá el repositorio (botón **Code → Download ZIP**), abrí la carpeta en tu agente y pedile:

> Leé AGENTS.md y la skill de onboarding de este kit. Diagnosticá mi equipo y explicame qué herramientas faltan, sin instalar nada sin mi autorización. Después mostrame qué puede hacer con el ejercicio de ejemplo de `examples/discursos/`.

Los ejemplos de `examples/` son **ficticios**: sirven para probar el método sin atribuir frases a personas reales.

## Qué hay en el repositorio

- `AGENTS.md`: reglas editoriales comunes a todas las skills.
- `skills/`: los procedimientos, con sus referencias.
- `adapters/`: instrucciones particulares de Codex, Claude Code y OpenCode.
- `scripts/`: instalador, diagnóstico, OCR, audio, video, validadores e INDEC.
- `config/`: países, catálogo de medios (vacío: cada redacción agrega el suyo) y artefactos fijados por SHA256.
- `examples/`: ejercicios ficticios.
- `tests/`: pruebas automatizadas (`python3 -m unittest discover -s tests`).
- `docs/`: criterios editoriales, seguridad, instalación de motores y [verificación](docs/VERIFICACION.md).

## Licencia y contribuciones

Código, skills y documentación se publican bajo [licencia MIT](LICENSE): se pueden usar, adaptar y redistribuir en cualquier redacción conservando el aviso de copyright. Para aportar, ver [CONTRIBUTING.md](CONTRIBUTING.md); para reportar un problema de seguridad, [SECURITY.md](SECURITY.md).

Los motores y modelos externos (Tesseract, whisper.cpp, FFmpeg, PDFium, HyperFrames) tienen sus propias licencias y no se incluyen en el repositorio: ver [docs/TERCEROS.md](docs/TERCEROS.md). La skill del INDEC es una adaptación de [indec-api-skill](https://github.com/jonymusky/indec-api-skill) de Jony Musky (MIT).
