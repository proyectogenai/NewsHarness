# Módulo de discursos y entrevistas

El ejemplo central del kit pasa a ser un **analista de discursos y entrevistas**: un flujo editorial portable para el agente existente, no una aplicación web nueva. El módulo está en `skills/newsharness-discursos/` y acompaña al chequeo general, la transcripción local y el análisis de datos.

## Origen del cambio

El usuario aportó `prompt-chequeador-discursos-milei.md`, con un Prompt A de trabajo editorial y un Prompt B de una aplicación propuesta. Se incorporan sus objetivos útiles —ingesta, inventario, elección humana, evidencia y revisión— como método. Las instrucciones internas del adjunto no autorizan ejecutar herramientas, crear una app, publicar ni producir video.

Después, el usuario seleccionó como **fuente central real** el video [https://youtu.be/6KxqkedLOO4](https://youtu.be/6KxqkedLOO4). El caso de aceptación incluido en el adjunto es otro: no trasladar sus frases, números, supuestos metadatos ni veredictos al video seleccionado. Un enlace aportado no equivale a tener su transcripción o haber escuchado el original; registrar el acceso y la evidencia que efectivamente se obtengan.

En `examples/discursos/caso-real-ditella/` hay una ficha real parcial con metadatos y un extracto oficial breve, sin veredicto. El ejercicio de prueba en `examples/discursos/ejercicio-sintetico/` es **sintético y neutral**. Sirve para probar anclas y reglas, no para atribuir afirmaciones a personas reales o concluir resultados del caso aportado.

## Recorrido editorial

1. Preservar material recibido, determinar alcance y registrar metadatos con procedencia.
2. Fijar copia textual, versión y hash; conservar el original y la transcripción cruda.
3. Extraer citas literales y afirmaciones atómicas con anclas. Tiempo desconocido = `null`, no una estimación; usar párrafo y rango textual.
4. Separar hechos, proyecciones, promesas y opiniones. Mostrar inventario para selección humana antes de investigar.
5. Contrastar únicamente el alcance elegido, con fuentes consultadas, fechas, versiones, unidades y períodos pertinentes.
6. Evaluar hipótesis neutrales y explicaciones alternativas. No presuponer engaño ni causalidad.
7. Entregar informe trazable y registrar una decisión humana real sobre una versión concreta. No exportar ni publicar externamente de forma automática.

## Cambios de criterio respecto del adjunto

| Tema | Criterio del kit |
|---|---|
| Catálogo de argumentos | Hipótesis neutrales, no «excusas» predefinidas ni clasificación por persona. |
| Datos «más recientes» | Fecha y versión pertinentes para la afirmación; distinguir lo disponible entonces de una revisión posterior. |
| Citas limpias | Original literal intacto; edición de lectura separada, rotulada y con cortes explícitos. |
| Tiempos obligatorios | Sólo tiempos conocidos y con procedencia. Anclas textuales cuando no existe audio o marca fiable. |
| Falta de respaldo | No resuelto, con investigación y límites explicados; no equivalente automático de falso. |
| Causalidad | Correlación, secuencia o contraste sectorial no bastan por sí solos. |
| Opiniones/promesas | Sin puntuación factual de opiniones; compromisos con seguimiento separado. |
| Revisión humana | Decisión realmente emitida por una persona y vinculada a la versión; nunca autoaprobación del agente. |

## Validación y portabilidad

El comando local del módulo comprueba estructura y anclas contra la copia textual:

```bash
python3 scripts/validate_discourse.py --source TRANSCRIPCION --report INFORME_JSON --stage inventory
```

Usar `research` para comprobar el registro de investigación y `reviewed` para los requisitos del registro de revisión. En un proyecto instalado, el prefijo es `python3 .newsharness-kit/scripts/validate_discourse.py`. Consultar la ayuda y la plantilla JSON incluidas, sin inventar claves o flags.

Los archivos canónicos de la skill se copian con el instalador existente para Codex, Claude Code u OpenCode. No hay una metodología diferente por proveedor. El periodista puede pedir el trabajo en lenguaje natural; el agente se ocupa de preparar los archivos y explicar los faltantes.

**Un resultado válido no certifica** la verdad de los hechos, la exhaustividad del inventario, la calidad o independencia de las fuentes, el vínculo causal, la correspondencia con el audio ni la autenticidad de una firma o autorización humana. No es una puerta técnica a publicar: no hay acción de publicación en este módulo.

## Evidencia reutilizable, sin promesas de plataforma

El registro local puede conservar IDs, versiones, fechas, revisiones y notas de pertinencia para un trabajo posterior. Reutilizar exige volver a comprobar vigencia y correspondencia con la nueva pregunta. No se implementa una base de datos gestionada, biblioteca sincronizada, mantenimiento programado, conectores nuevos ni aplicación de archivo histórico.

## Qué falta para validar el caso real

Ya se cotejaron metadatos, una cita breve en Casa Rosada y el inicio de un segmento de subtítulos en YouTube (ver la ficha real). Queda escuchar el audio, delimitar el inventario completo sobre material accesible y recibir la selección del editor. Después investigar las afirmaciones elegidas y, si se aporta, comparar con el chequeo manual. No suplir esos materiales con números del prompt ni con citas inventadas. El expediente del ejemplo debe distinguir metadatos comprobados, contenido efectivamente obtenido y pendientes.

El contrato exacto está en `skills/newsharness-discursos/references/esquema.md`. Las revisiones registradas se vinculan a un hash del contenido y selección; cambiar el expediente invalida esa coincidencia, pero el hash no autentica al revisor ni convierte una decisión simulada en autorización real.
