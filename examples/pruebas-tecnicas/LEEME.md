# Muestras técnicas sintéticas

Todos los nombres, cifras y documentos de esta carpeta son ficticios y fueron creados para probar el kit. No son noticias ni documentos de ningún medio real. Son independientes de la historia de `demo-publica/`.

- `ocr-es.png`: imagen generada con texto español. La salida esperada está en `ocr-es-esperado.txt`; ignorar únicamente diferencias de espacio al comparar. Revisar tildes, nombre, fecha y cifras.
- `mixto-es.pdf`: página 1 con texto digital y página 2 escaneada. Esperar extracción directa en la primera y OCR en la segunda; verificar que conserva todas las páginas y el original.
- `silencio-10s.wav`: 10 segundos de silencio digital. La salida correcta contiene cero palabras. Una salida vacía en este caso no demuestra calidad de reconocimiento de voz. El runtime evita enviar silencio digital completo al modelo; VAD protege además otros tramos sin voz, sin garantía absoluta.

El agente ejecuta los comandos `ocr` y `transcribe` siguiendo su ayuda real y con un espacio inicializado. No se incluyen los modelos ni motores, que se comprueban y descargan por separado con autorización. Esta carpeta no contiene una entrevista española grabada: esa evaluación continúa pendiente.
