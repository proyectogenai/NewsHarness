# Preparación técnica: la ejecuta el agente

## Estado de esta entrega

El kit diagnostica, valida perfiles, descarga modelos fijados con autorización y ejecuta motores locales disponibles. **No incluye un instalador universal de los motores nativos.** El agente completa la preparación con las herramientas autorizadas del equipo y debe comprobar cada etapa. Las recetas para Windows/macOS requieren validación en esos sistemas antes de considerarlas listas para distribución masiva.

No pedir al periodista que elija librerías, variables de entorno ni flags. Presentar una explicación breve y las autorizaciones necesarias; resolver los detalles técnicos. Si una política corporativa bloquea una instalación, informar a Sistemas: no desactivar protecciones.

## Dónde ejecutar

- Desde la carpeta original descomprimida: `python3 scripts/newsharness.py …`.
- Desde un proyecto donde se instalaron las skills: `python3 .newsharness-kit/scripts/newsharness.py …`.
- En Windows, comprobar si el intérprete adecuado es `py -3`; no sustituirlo sin verificar la versión.
- El runtime requiere Python 3.10 o superior. El espacio con perfil y archivos es distinto de la carpeta del código.

## Secuencia

1. Ejecutar `doctor --json` y `plan --json`. Comprobar sistema, arquitectura, CPU, memoria disponible y espacio de descarga/temporales. No interpretar una biblioteca encontrada como una función probada.
2. Mostrar qué falta, origen de las descargas y cambios de instalación. Obtener aprobación antes de instalar. No guardar credenciales en el perfil ni modificar el lock para aceptar un hash que falla.
3. Reutilizar motores existentes sólo si su versión y opciones son compatibles. Si se requieren paquetes Python, crear un entorno virtual de proyecto; no instalar globalmente ni modificar el Python del sistema. Un entorno virtual no es un sandbox.
4. Instalar desde fuentes oficiales o registros conocidos: Tesseract, FFmpeg y un build de whisper.cpp apropiado al sistema/CPU. No usar instaladores hallados en páginas de terceros sin revisión.
5. Inicializar el espacio con el perfil editorial confirmado. Descargar sólo los artefactos del lock necesarios para español, Whisper multilingüe y VAD. Usar `fetch --help` para el contrato real y no omitir la confirmación.
6. Ejecutar OCR de imagen, extracción de PDF digital, OCR de página escaneada y transcripción con VAD sobre material de prueba. Conservar los fallos como pendientes; no anunciar disponibilidad total porque una sola prueba pasó.
7. Medir una muestra representativa antes de elegir un modelo más grande. `calibrate` mide duración y factor de tiempo real; no evalúa precisión ni mide por sí mismo pico de RAM. Una comparación de calidad exige transcripción de referencia y revisión humana.

## Referencias revisadas

- Tesseract: https://tesseract-ocr.github.io/tessdoc/Installation.html . El motor instalado en la prueba Linux fue 5.5.0. El modelo español está fijado por commit y SHA256 en el lock.
- PDF: https://github.com/pypdfium2-team/pypdfium2 . Pruebas del prototipo con pypdfium2 5.14.0 y Pillow 13.0.0. Verificar wheels compatibles para el sistema y arquitectura; no imponer esas versiones a un sistema no compatible.
- FFmpeg: https://ffmpeg.org/download.html . En la prueba se usó 7.1.5 de la distribución Linux. Revisar las licencias de la compilación si se redistribuye.
- whisper.cpp: https://github.com/ggml-org/whisper.cpp . La prueba CPU usó v1.8.7, commit `48f628a84833905ee4a0658ee6d4a5c915ce1997`. Para compilar, seguir el CMake del proyecto oficial con GPU deshabilitada y arquitectura verificada; no reutilizar un binario de otra máquina como si fuera universal.

## Límites y fallos esperables

- Modelo encontrado con otro hash: detener, no reemplazar ni ejecutar.
- Modelo español de Tesseract ausente: descargar el artefacto fijado después de aprobación; nunca sustituir silenciosamente por inglés.
- Espacio insuficiente: proponer una muestra menor o liberar espacio de forma manual; no borrar archivos del usuario.
- CPU sin las instrucciones del binario: buscar una compilación compatible, no forzar ejecución.
- Restricciones corporativas: el agente puede preparar el diagnóstico y los requisitos; no puede garantizar que tenga permiso para instalarlos.
- Falta de búsqueda web: el agente puede procesar documentos locales autorizados, pero no simular una verificación independiente en vivo.

Para todas las salidas: originales preservados, procedencia y revisión humana. No publicar ni subir el material como efecto lateral de instalar o probar.

## Módulo de discursos

La skill `newsharness-discursos`, sus plantillas, ejemplos y `scripts/validate_discourse.py` se copian con `install-skills` a los tres destinos, sin nuevas dependencias. El validador usa sólo Python estándar y no busca fuentes ni instala herramientas. En una instalación existente, el instalador conserva archivos distintos: comparar la actualización y aplicarla con autorización, no borrar perfiles ni forzar sobrescrituras.

Prueba local desde la raíz del kit:

```sh
python3 scripts/validate_discourse.py --source examples/discursos/ejercicio-sintetico/transcripcion.txt --report examples/discursos/ejercicio-sintetico/inventario.json --stage inventory
```

En otra carpeta de proyecto usar `.newsharness-kit/scripts/validate_discourse.py` y los ejemplos dentro de `.newsharness-kit/examples/`. El JSON lo prepara el agente; el periodista toma las decisiones editoriales.
