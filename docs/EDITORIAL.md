# Guía editorial · v1

## Para qué sirve

Un mismo asistente puede aprender cómo trabaja un periodista, ordenar sus fuentes, revisar una nota, explorar una tabla y preparar texto de documentos o grabaciones. El kit no reemplaza criterio, reportería ni edición. Está pensado para que la persona pida tareas, no programe comandos.

## Seis pedidos para empezar

1. **«Prepará mi perfil. Firmo…, trabajo en…, cubro… y suelo producir…»** El agente busca pautas oficiales y notas de sección, busca y desambigua firmas propias, propone un perfil y pide confirmación. Si no hay firma o manual público, avanza sin inventarlos.
2. **«Revisá esta nota antes de publicarla. Este material es público/confidencial».** Se entrega un inventario completo y un reporte con respaldos, problemas y pendientes. No se promete un chequeo completo con un extracto.
3. **«Con estos materiales, prepará un explicador para…».** Produce un borrador con fuentes y huecos separados. No completa una declaración faltante.
4. **«¿Qué muestra esta tabla y qué no podemos afirmar?».** Recalcula, identifica nulos/duplicados y evita confundir porcentajes, puntos porcentuales, personas y registros.
5. **«Pasá este escaneo a texto y marcá lo dudoso».** El OCR local conserva originales y requiere cotejo visual para lo que se publicará.
6. **«Transcribí esta entrevista sin subir el audio».** Resuelve el motor local, conserva marcas de tiempo y señala dudas. Las marcas no identifican hablantes; las citas se escuchan antes de usarse.

## El perfil no es un simulador de personalidad

Se distinguen **reglas públicas**, **patrones observados** y **preferencias declaradas**. Cada inferencia tiene muestra y límites. La voz no manda sobre los hechos, las citas o una salvedad. Una nota de agencia o una columna no representa por sí sola el estilo de toda una redacción. No se atribuye a alguien el trabajo de un homónimo.

## La revisión dice qué se sabe

«Respaldada» describe evidencia suficiente para una afirmación concreta. «Requiere revisión» necesita respaldo del problema; «no resuelta» no acusa de falsedad. Esta última puede corresponder a reportería propia, acceso imposible, búsqueda inconclusa o algo todavía no investigado. Los estados y sus cantidades deben cubrir todo el inventario.

La verificación toma la fecha de publicación como referencia, reconoce revisiones posteriores y hace de nuevo las cuentas. Una fuente oficial puede equivocarse; múltiples sitios con el mismo cable no son fuentes independientes. Para probar una ausencia hace falta un corpus completo y pertinente, no sólo una búsqueda vacía.

## Privacidad práctica

Consultar la web revela la consulta. Subir un documento revela el documento. Procesar audio localmente evita enviarlo a un motor externo, pero el agente remoto puede recibir su transcripción si se le muestra. Por eso el medio debe aprobar el flujo para material reservado. Ningún prompt convierte al proveedor del agente en un entorno sin salida de datos.

El agente pregunta antes de instalar, descargar modelos, enviar contenido o archivar en público; nunca pide contraseñas en el perfil. Publicar en un CMS, mandar un correo o contactar a una fuente no está incluido en una revisión de texto.

## Demostración sin riesgo

Usar `examples/demo-publica/`: todo el expediente es ficticio, con errores sembrados. No contiene declaraciones reales de ningún medio real ni de una autoridad pública. Primero ejecutar el ejercicio sin abrir su clave; después comparar con `revision-esperada.md`. La transcripción textual no prueba reconocimiento de audio: una prueba del motor requiere un archivo de audio real autorizado y escuchar el resultado.

## Criterio de aceptación editorial

- El periodista reconoce su perfil y sabe qué es una inferencia.
- Cada cambio sustantivo vuelve a una fuente y una ubicación.
- Los originales están intactos y se distinguen salida cruda y revisada.
- Los pendientes no desaparecen del resumen.
- No hubo publicaciones, archivos públicos ni egress no autorizado.
- Una persona puede decidir qué corregir y qué preguntar sin leer código.
