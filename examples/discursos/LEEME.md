# Ejemplo: analizar discursos y entrevistas

## Ejercicio sintético

La carpeta [ejercicio-sintetico/](ejercicio-sintetico/) contiene una transcripción, un inventario, un registro de evidencia y un informe **inventados** para probar el módulo. Los emisores, declaraciones y datos no describen a personas o instituciones reales. No usarlo como evidencia periodística.

La prueba permite comprobar que se conservan citas literales, que las anclas corresponden al texto, que un tiempo desconocido permanece `null`, que se separan tipos de afirmación y que una aprobación humana no se presume. Los resultados de esas comprobaciones no demuestran exhaustividad ni verdad factual.

## Con un discurso real

Para extraer citas hace falta acceso al contenido: el audio, el video o una transcripción autorizada. Un enlace por sí solo no alcanza. Cualquier acceso faltante se declara, sin reconstruir palabras desde títulos, resúmenes o memoria. Para verificar afirmaciones también hace falta la selección de la persona responsable.

## Cómo pedirlo al agente

> Usá la skill newsharness-discursos. Primero indicá qué material recibiste, preservá el original y armá un inventario con citas exactas y ubicaciones. No inventes tiempos si sólo hay texto. Separá hechos, proyecciones, promesas y opiniones, y esperá mi selección antes de contrastar. Después mostrame la evidencia con fechas y versiones, los límites y el registro de revisión pendiente. No publiques ni exportes a servicios externos.

El agente usa el validador estructural del kit según la etapa y explica los errores sin pedir al periodista que programe. El flujo editorial completo está en `skills/newsharness-discursos/SKILL.md` y `docs/DISCURSOS.md`, desde la raíz del kit.
