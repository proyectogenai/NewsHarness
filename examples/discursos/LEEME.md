# Ejemplo central: analizar discursos y entrevistas

La **fuente central real elegida por el usuario** es este video: [https://youtu.be/6KxqkedLOO4](https://youtu.be/6KxqkedLOO4). El documento aportado `prompt-chequeador-discursos-milei.md` sirve como referencia metodológica, pero el caso mencionado dentro de ese documento es distinto de la fuente elegida después.

El expediente debe registrar qué se pudo abrir y verificar de ese video. **No transferirle frases, números o minutos del prompt.** El enlace por sí solo no habilita un inventario literal: para extraer citas hace falta acceso al contenido o una transcripción autorizada. Cualquier acceso faltante se declara, sin reconstruir palabras desde títulos, resúmenes o memoria. Para verificar afirmaciones también hace falta la selección de la persona responsable.

## Ficha real disponible

Ver [caso-real-ditella/LEEME.md](caso-real-ditella/LEEME.md): metadatos contrastados, extracto oficial breve y enlace al segmento 43:36 del panel de transcripción. El audio no fue escuchado, no hay inventario completo ni veredicto. La fecha del discurso (30/10/2026) se distingue de la publicación del video (31/10/2026). Los tiempos exactos de la cita permanecen `null`.

## Prueba técnica separada

El ejercicio de transcripción e inventario incluido para probar el módulo está rotulado **SINTÉTICO**. Los emisores, declaraciones y datos de ese ejercicio no describen a personas o instituciones reales. No usarlo como evidencia periodística ni como resultado del caso aportado.

La prueba permite comprobar que se conservan citas literales, que las anclas corresponden al texto, que un tiempo desconocido permanece `null`, que se separan tipos de afirmación y que una aprobación humana no se presume. Los resultados de esas comprobaciones no demuestran exhaustividad ni verdad factual.

## Cómo pedirlo al agente

> Usá la skill newsharness-discursos. Primero indicá qué material recibiste, preservá el original y armá un inventario con citas exactas y ubicaciones. No inventes tiempos si sólo hay texto. Separá hechos, proyecciones, promesas y opiniones, y esperá mi selección antes de contrastar. Después mostrame la evidencia con fechas y versiones, los límites y el registro de revisión pendiente. No publiques ni exportes a servicios externos.

El agente usa el validador estructural del kit según la etapa y explica los errores sin pedir al periodista que programe. El flujo editorial completo está en `skills/newsharness-discursos/SKILL.md` y `docs/DISCURSOS.md`, desde la raíz del kit.
