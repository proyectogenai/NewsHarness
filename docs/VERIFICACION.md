# Verificación de v0.1 · 1 de noviembre de 2026

## Alcance real

Prototipo ejecutado en Linux x86-64, Python 3.12.14. Esta revisión no certifica la seguridad de los motores ni la fiabilidad editorial del agente. Las pruebas automatizadas comprueban comportamientos concretos; no prueban que una conclusión periodística sea verdadera.

## Pruebas automatizadas

Comando desde la raíz del kit:

```bash
python3 -m unittest discover -s tests -v
```

**118 pruebas aprobadas**: 60 de runtime, 14 del validador general de informes, 36 del módulo de discursos, 4 del contenido/paquete y 4 del catálogo regional. Incluyen detección de memoria desconocida, márgenes provisionales, perfiles sin secretos estructurados, archivos originales, rutas de salida, descargas con consentimiento y SHA256, repetición de instalación, preservación de instrucciones existentes, formatos admitidos, detención de procesos, modelos multilingües y estados de evidencia.

No equivale a probar todas las entradas maliciosas posibles ni el comportamiento completo del sistema operativo. Los scripts y tests se entregan para revisión.

## Pruebas reales de motores

### OCR en español

- Tesseract 5.5.0 con `tessdata_fast/spa.traineddata` fijado por commit y SHA256.
- Imagen sintética: conservó las palabras esperadas, «María Pérez», las tildes, la fecha y las cifras.
- PDF mixto: primera página extraída de su capa digital; segunda página escaneada procesada con OCR. Se comprobó preservación del original por hash.
- pypdfium2 5.14.0 y Pillow 13.0.0. Se corrigió durante la prueba el uso incompatible del administrador de contexto de páginas PDF; el caso completo volvió a ejecutarse correctamente.
- Las imágenes se decodifican y normalizan antes de enviarlas al motor; no se usa el nombre de extensión como única validación.

### Audio CPU

- whisper.cpp v1.8.7, commit `48f628a84833905ee4a0658ee6d4a5c915ce1997`.
- Modelo multilingüe `base-q5_1` y VAD Silero v6.2.0, ambos con SHA256 verificado.
- Muestra pública JFK de 11 segundos, incluida en el repositorio oficial: reconocimiento **en inglés**, salida TXT/SRT/JSON y marcas de tiempo. Pasó tanto la prueba directa del motor como la del ejecutor del kit, en CPU.
- Prueba negativa: sin VAD, 10 segundos de silencio digital con idioma `es` produjeron `[Música]`. Con VAD la salida fue vacía. El kit final también detecta silencio digital completo antes del reconocimiento y produce salida vacía sin ejecutar ASR.
- Este resultado no elimina el riesgo de alucinaciones con ruido, música o voz real. No valida español hablado ni identificación de hablantes.
- El tiempo del fragmento corto en un servidor de prueba no se extrapola al portátil del periodista. El comando de calibración no mide pico de memoria ni exactitud de transcripción.

## Descargas

Descarga real y verificación SHA256 del modelo español por el ejecutor del kit; una segunda ejecución reutilizó el archivo sin sobrescribirlo. Descarga real del VAD por ese mismo ejecutor. Los modelos Whisper y VAD usados en la prueba se cotejaron con artefactos oficiales fijados. No se incluyen motores ni modelos en el repositorio.

## Agentes

Se entregan diez skills con frontmatter validado, referencias y adaptadores de descubrimiento para Codex, Claude Code y OpenCode. El instalador conserva configuración existente y copia una versión de soporte del kit al proyecto.

**No se ha realizado una sesión end-to-end en los tres agentes comerciales.** Copiar los archivos o pasar un test de instalación no prueba invocación automática, permisos, búsquedas web ni compatibilidad de todas sus versiones.

## Pendientes antes de una distribución a redacciones

1. Validar instalación y ejecución en Windows y macOS, incluyendo equipos corporativos sin permisos de administrador y CPUs con otras instrucciones.
2. Evaluar entrevistas españolas con transcripción de referencia, acentos, ruido, nombres propios, cifras, negaciones y varios hablantes. Medir errores y memoria en equipos representativos.
3. Ejecutar el onboarding de punta a punta y revisar perfiles inferidos con periodistas de distintos medios; cubrir autores sin notas y homónimos.
4. Calibrar el chequeo con notas reales autorizadas de Argentina, México, Perú, Colombia y Costa Rica y casos preparados con evidencia conocida. El validador sólo comprueba estructura y anclajes, no verdad, independencia ni exhaustividad.
5. Validar comportamiento de cada agente, sus controles reales y los flujos de salida de información.
6. Completar y probar la instalación nativa por plataforma; esta entrega usa diagnóstico, descargas controladas y recetas para el agente, no un instalador universal terminado.
7. Acordar licencia y revisar avisos de dependencias antes de distribuir institucionalmente.

Las muestras técnicas incluidas son ficticias. Los datos y borradores periodísticos privados no se utilizaron en estas pruebas.

## Ampliación regional de esta revisión

Se incorporaron rutas documentales de Perú, Colombia y Costa Rica a las ya existentes de Argentina y México. Se añadió un catálogo de medios con fecha de consulta (se distribuye vacío). Las cuatro pruebas nuevas revisan unicidad, cobertura declarada, desambiguación de cabeceras y existencia de archivos de referencia. No prueban APIs, precisión del fact-checking ni acceso integral a registros públicos.

## INDEC por API · 3 de noviembre de 2026

Se revisó el código de indec-api-skill (commit `0a95ccc`) antes de adaptarlo; no se ejecutó el original. La spec pública `https://api.indec.gob.ar/api/openapi?v=2` respondió sin token y se incluyó en el kit; tiene las mismas 19 tablas y columnas que el snapshot del repositorio original. Sin token, `/v1/ipc_nacional` respondió 401, como documenta el INDEC. Se ejecutaron en vivo `tablas`, `columnas`, la sugerencia de nombres (`canasta_crianza`, `Periodo`), el aviso de token faltante y `comparar-spec` (sin cambios estructurales).

**No se hizo ninguna consulta de datos con token**: no hubo cuenta del INDEC en esta prueba. La paginación, los reintentos, las etiquetas de comercio exterior, el rechazo de redirecciones y el resguardo del token se probaron con un servidor simulado (13 pruebas). Validar con un token real antes de distribuir: una consulta mensual (`ipc_nacional`), una semestral (`pobreza_eph`) y una de comercio exterior con `--etiquetas`.

## Fuentes de Argentina · 3 de noviembre de 2026

Se comprobó el acceso, sin cuentas ni tokens, a INDEC (sitio y calendario), Series de Tiempo de datos.gob.ar (serie y búsqueda), BCRA API v4.0 (listado y serie de reservas) y cotizaciones v1.0, Boletín Oficial (primera sección con URLs de avisos), Normativa, InfoLEG, Presupuesto Abierto, CNV, Cámara Nacional Electoral y estadísticas de CABA y Provincia de Buenos Aires. La API del BCRA v3.0 respondió 410. economia.gob.ar presentó un certificado HTTPS vencido: no se forzó la conexión. La búsqueda avanzada del Boletín Oficial redirigió a una página de error en la prueba automática.

**No se verificó** el comportamiento de las skills nuevas en sesiones reales de los tres agentes.

## Instalación global · 2 de noviembre de 2026

Seis pruebas con una carpeta de usuario temporal: instalación idempotente que no toca un `CLAUDE.md` global existente; rutas de Claude Code, OpenCode y Codex (incluido `CODEX_HOME`); exigencia de `--update` ante una versión nueva; actualización que respeta archivos editados por el usuario; retiro de archivos obsoletos; desinstalación por agente que conserva el kit mientras otro agente lo use, y archivos ajenos o editados. Se comprobó además un ciclo completo instalar → repetir → desinstalar sobre el kit real en Windows 11.

**No se comprobó que cada agente descubra las skills desde su carpeta de usuario.** Las rutas surgen de la documentación: la de OpenCode es oficial; la de Codex proviene de documentación del repositorio que la marca como experimental. Validar en cada agente antes de una distribución amplia.

## Portabilidad Windows · 1 de noviembre de 2026

Suite ejecutada en Windows 11 Pro con Python 3.12.10: inicialmente 15 de 118 pruebas fallaban. Causas: (1) `confined_path` rechazaba toda ruta con subcarpetas porque Windows representa `Path` con `\`; (2) lecturas de texto sin `encoding="utf-8"` usaban cp1252. Tras la corrección: **119 pruebas aprobadas, 2 omitidas** por diseño en Windows (symlinks y grupos de procesos POSIX), incluida una prueba de regresión nueva para rutas anidadas y rutas relativas a unidad (`C:x`). No se probaron motores (Tesseract, whisper.cpp) en Windows ni macOS; la integración continua (`.github/workflows/tests.yml`) corre la suite en Linux, Windows y macOS.

## Ampliación de discursos e entrevistas · 1 de noviembre de 2026

Se leyó completo el documento metodológico aportado y se adaptó como skill portable, sin ejecutar su pedido interno de una app. El caso central real pasa al discurso en Universidad Torcuato Di Tella elegido posteriormente por el usuario. La ficha real registra emisión 30/10/2026, publicación del video 31/10, canal, duración, un extracto literal breve cotejado en Casa Rosada y enlace a un segmento de subtítulos 43:36. **No se escuchó el audio ni se verificó la afirmación fiscal.** El JSON queda parcial, sin selección, evaluación ni revisión humana; sus tiempos exactos son null.

Las 36 pruebas nuevas cubren anclas, hash del original, recortes literales, tiempos desconocidos y cue más próximo, selección humana previa, decisiones simuladas separadas de reales, versión revisada fijada por hash, rechazo de aprobaciones superadas, opiniones/proyecciones/promesas, causalidad, ausencia de evidencia, unidades/períodos, versiones de fuentes, orden temporal intradía, rutas/credenciales y JSON malformado. La muestra sintética no evalúa a una persona real. Se comprobaron el inventario real en etapa inventory y el fixture en inventory/research/reviewed.

No hay nuevos motores, dependencias, conectores, app, biblioteca gestionada, exportación ni publicación. Un estado reviewed estructural no autentica a la persona ni demuestra verdad. La compatibilidad real de los tres agentes y la evaluación editorial completa siguen pendientes.
