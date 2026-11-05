# Contrato del expediente local · esquema 1

El agente prepara el JSON para la persona; no se exige programar ni completar manualmente estos campos. La plantilla `../templates/expediente-vacio.json` tiene marcadores que deben reemplazarse y **no es un expediente válido listo para uso**. Los ejemplos completos viven en `examples/discursos/` del kit.

## CLI y límites

```sh
python3 scripts/validate_discourse.py --source original.txt --report expediente.json --stage inventory
python3 scripts/validate_discourse.py --source original.txt --report expediente.json --stage research --print-review-hash
python3 scripts/validate_discourse.py --source original.txt --report expediente.json --stage reviewed
```

En un proyecto instalado el ejecutable está en `.newsharness-kit/scripts/validate_discourse.py`. `--stage` vale `inventory` por defecto. Código de salida: 0 estructura coherente; 1 hallazgos de validación; 2 entrada ilegible o JSON inválido. No se abren enlaces ni referencias locales, no se ejecutan cálculos y no se escribe nada. Máximo por archivo: 5 MB. Se rechazan claves JSON duplicadas.

La salida dice siempre `human_review_authenticated: false` y `publication_authorized: false`. El validador **no puede saber quién tomó una decisión**, si la evidencia prueba el hecho ni si se extrajeron todas las afirmaciones. Tener un registro humano consistente no equivale a autenticarlo. Comprobar su procedencia en la conversación o registro autorizado antes de usarlo.

## Campos raíz

| Campo | Contenido |
|---|---|
| `schema_version` | `1` |
| `source_sha256` | SHA256 de los bytes UTF-8 exactos del original; no normalizar saltos ni reescribirlo |
| `metadata` | `title`; `speaker`, `medium`, `program`, `interviewer` (texto o `null`); `emitted_at` (ISO o `null`); `source_url` (URL pública o `null`); `duration_seconds` (número o `null`); `provenance`: `user_supplied`, `primary_source_verified` o `synthetic_fixture` |
| `analysis_as_of` | Fecha ISO de corte del análisis; no confundir con emisión, publicación o período de datos |
| `coverage` | `scope`: `full_source` o `partial`; `limitations`: lista de límites. Una cobertura parcial debe decir qué falta |
| `claims`, `sources`, `human_decisions` | Listas; identificadores únicos dentro de cada una |
| `selection_decision_id`, `review_decision_id` | ID de la decisión aplicable o `null` |

`full_source` describe el alcance declarado, no una garantía de exhaustividad. Preservar las afirmaciones no elegidas en el inventario, con `assessment: null`.

## Afirmación

Campos obligatorios: `id`, `kind` (`fact`, `projection`, `promise`, `opinion`), `quote_original`, `anchor`, `display_quote`, `display_spans`, `display_edit_note`, `numeric`, `causal_claim`, `reference_period`, `due_at`, `patterns`, `assessment`.

- `anchor.start` inclusivo y `anchor.end` exclusivo cuentan **caracteres Unicode**, no bytes. La porción debe coincidir exactamente con `quote_original`. `paragraph` empieza en 1; separan párrafos las líneas vacías. Una cita no concatena párrafos distintos.
- `time_start_seconds`, `time_end_seconds`, `time_source`: todos `null` si no se dispone de marcas verificables. Un tiempo numérico exige una marca literal original `[mm:ss]` o `[hh:mm:ss]`, concordante, en `time_source.start_cue` / `end_cue`. El final puede quedar `null`. No convertir un inicio de segmento en precisión por palabra. Si el tiempo se cotejó sólo en un reproductor, registrarlo en la fuente y mantener estos campos `null` hasta tener una transcripción temporizada auténtica.
- Edición: `display_quote: null`, `display_spans: []`, `display_edit_note: null` si no se edita. Si se recorta, los spans `{start,end}` son offsets dentro de `quote_original`, ordenados, no solapados. El texto mostrado debe ser la unión literal de esos fragmentos con ` (…) `; documentar motivo. No reemplazar palabras dentro de la cita original ni llamar literal a una paráfrasis.
- `numeric` y `causal_claim`: booleanos. `reference_period`: período o `null`. `due_at`: fecha de promesa o `null`; no usarlo para fingir certeza sobre una proyección.

## Patrones: hipótesis, nunca etiquetas de culpabilidad

Cada objeto contiene `id`, `hypothesis`, `test`, `alternative`, `status`, `source_ids`.

IDs: `comparative_base`, `series_and_vintage`, `denominator_and_units`, `coverage`, `causal_attribution`, `stocks_flows_overlap`, `forecast_vs_observed`, `definition`, `international_comparability`.

Estados: `untested`, `supported`, `not_supported`, `inconclusive`. Para probar o descartar se exige evidencia y selección humana previa. Una hipótesis puede no aplicar; `patterns: []` es válido. Ni el nombre del hablante ni reconocer una frase prueba el patrón.

## Fuente y revisión de datos

Cada fuente: `id`, `publisher`, `title`, `location`, `published_at`, `consulted_at`, `reference_period`, `version`, `valid_as_of`, `supersedes`, `limitations`, `independence_group`, `role`, `excerpt`, `observations`.

- `location` contiene exactamente `url` o `file`, más `locator`. Las rutas son relativas al expediente, sin `..`; URLs http(s), sin credenciales. El validador **no comprueba la existencia ni abre el contenido**.
- `published_at` puede ser `null` si se desconoce; no sirve para una conclusión histórica decisiva sin aclaración. `consulted_at` y `valid_as_of` son fechas de consulta y vigencia comprobada, no promesas de actualización futura. `version` identifica la publicación/vintage concreto; `supersedes` referencia otra fuente del expediente o `null`. No borrar la versión anterior ni crear ciclos.
- `reference_period` puede ser `null` cuando no hay período estadístico. `role`: `primary` o `secondary`. `limitations` debe indicar límites conocidos; una fuente oficial puede ser parte interesada. `independence_group` permite advertir que dos sitios reproducen el mismo emisor; no es una evaluación automática de independencia.
- `excerpt`: evidencia o descripción localizable. Para cifras, `observations` contiene objetos con **textos** `value`, `unit`, `period`, `locator`. Esto conserva formatos y unidades sin convertirlos de forma implícita.

## Evaluación de una afirmación seleccionada

`assessment` permanece `null` antes de la selección. Después contiene `status`, `rationale`, `evidence`, `unresolved_reason`, `temporal_basis`, `revision_note`, `causal_support`, `causal_limitations`, `calculations`.

| Tipo | Estados admitidos |
|---|---|
| Hecho | `supported`, `contradicted`, `needs_context`, `unresolved` |
| Proyección | `methods_assessed`, `awaiting_outcome`, `unresolved` |
| Promesa | `tracking`, `fulfilled`, `partly_fulfilled`, `not_fulfilled`, `unresolved` |
| Opinión | `not_fact_checked` |

`evidence` contiene `{source_id, relation, reason}`; relaciones: `supports`, `contradicts`, `context`, `methodology`. Un hecho contradicho requiere evidencia contradictoria: la búsqueda infructuosa no basta. Una opinión que encierra un dato comprobable debe descomponerse: valoración y hecho reciben fichas distintas.

`temporal_basis`: `contemporaneous`, `later_revision`, `mixed`, `not_applicable`. No presentar una publicación posterior como dato conocido al hablar. Cuando se usa revisión posterior, `revision_note` explica la diferencia. La revisión de metodología de una proyección no prueba el resultado futuro. Incumplimiento final o cumplimiento parcial de promesas requieren plazo vencido; si falta, seguir en `tracking`/`unresolved`.

`causal_support`: `not_causal`, `correlation_only`, `causal_evidence`, `not_established`. Fechas con hora deben incluir zona horaria; el validador compara instantes, no trunca las horas. Si emisión y publicación tienen sólo la misma fecha, no asegura orden intradía: obtener la precisión necesaria o explicar un criterio mixto/revisión. Una promesa fechada sólo por día no se declara vencida dentro de ese mismo día.

Una conclusión causal de confirmación/refutación exige evidencia causal declarada y `causal_limitations`. El validador no juzga si el diseño realmente identifica causalidad.

Cada cálculo contiene `expression`, `inputs`, `result`, `unit`, `note`; los insumos son `{source_id, observation_index}` con índice desde 0. La expresión es **texto, no código ejecutable**. Comprobar las cuentas por separado con un procedimiento revisado.

## Decisiones humanas y versión revisada

Cada registro: `id`, `kind` (`selection` o `review`), `actor`, `decided_at`, `record_ref`, `recorded_from`, `claim_ids`, `outcome`, `snapshot_sha256`.

- `record_ref` usa `{url|file,locator}` y apunta a una instrucción real de la persona; no es una marca que el agente se concede. `recorded_from: human_instruction` para trabajo real. Sólo ejercicios sintéticos usan `synthetic_fixture`, nunca aprobación real.
- Selección: `outcome: selected`, `snapshot_sha256: null`. El agente puede proponer prioridades, pero no registrar una selección como decisión humana inexistente.
- Revisión: `outcome: approved` o `changes_requested`. `snapshot_sha256` fija la versión del contenido y de la selección revisados. `--print-review-hash` ayuda a identificarla; **calcular el hash no significa aprobar**. Registrar aprobación sólo tras una decisión real sobre esa versión.
- Si cambia contenido, evidencia o selección, el hash deja de coincidir y la etapa `reviewed` exige nueva revisión. No reutilizar una aprobación anterior si el registro incluye una revisión posterior. La revisión debe cubrir exactamente la selección; mantener pendientes, opiniones y proyecciones explícitas es compatible con aprobar la calidad de un informe, no convierte esos asuntos en hechos verdaderos.

No hay comando de publicación/exportación en este módulo. Los borradores locales pueden entregarse claramente rotulados; ninguna validación autoriza difusión externa por sí misma.
