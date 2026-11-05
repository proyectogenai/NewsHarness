---
name: newsharness-ocr
description: Pasar a texto escaneos, fotos de documentos y PDFs con OCR local, revisando visualmente nombres, cifras, tablas y citas; usar cuando pidan "sacá el texto de este PDF", "leé este escaneo", "pasá esta foto a texto" o "extraé la tabla del documento".
---
# OCR local con control editorial

> **Reglas comunes y ubicación del kit.** Antes de actuar, leer `AGENTS.md` del kit: en el kit fuente está en la raíz; instalado en un proyecto, en `.newsharness-kit/AGENTS.md`; instalado de forma global, en `~/.newsharness-kit/AGENTS.md` (Windows: `%USERPROFILE%\.newsharness-kit\AGENTS.md`). Los comandos `python3 scripts/newsharness.py` de esta skill se ejecutan desde esa misma ubicación del kit.

## Cuándo usarla

- **Sí:** PDF escaneado, foto de un documento, capturas, expedientes, boletines en imagen.
- **Antes de OCR:** si el PDF tiene texto seleccionable, extraerlo directamente (es más fiel). El runtime ya lo hace en PDFs mixtos.
- **Después:** para comprobar lo que dice el documento → `newsharness-factcheck`; para trabajar una tabla extraída → `newsharness-datos`.

## Flujo rápido

1. Clasificar sensibilidad y confirmar que se puede procesar localmente.
2. Comprobar motor y datos de idioma (`doctor`); pedir aprobación para lo que falte.
3. Ejecutar en una corrida nueva, sin tocar el original.
4. Revisión visual de citas, nombres, fechas y cifras contra la página.
5. Entregar texto crudo, copia revisada y lista de dudas con página.

El reconocimiento óptico produce un borrador de lectura. El original visual sigue siendo la evidencia.

## Antes de ejecutar

Determinar si el archivo tiene texto nativo útil; extraerlo sin OCR si conserva orden y contenido. En PDFs mixtos, distinguir páginas digitales y escaneadas. Clasificar confidencialidad: no subir ni mostrar páginas reservadas al modelo si el entorno no está autorizado.

Usar `newsharness-onboarding` para comprobar herramientas; el agente resuelve rutas e idioma. El wrapper sólo ejecuta CLIs locales verificadas. No inventar una opción por recordar otra versión. Comprobar ayuda/runtime y lenguajes disponibles; pedir aprobación antes de instalar motores o descargar datos de idioma.

## Ejecutar sin sobrescribir

Desde la raíz del kit, con rutas resueltas por el agente:

```bash
python3 scripts/newsharness.py ocr --workspace ESPACIO --input ARCHIVO --lang spa
```

Si los datos de idioma están en una ubicación propia, usar `--tessdata-dir RUTA` sólo tras verificarla. El runtime genera un resultado por corrida y conserva copia/procedencia. Un fallo no autoriza reemplazar el original o enviar a un OCR web. No afirmar éxito sólo por código de salida: revisar archivos, páginas y texto.

## Control visual obligatorio

Comparar la salida con páginas representativas de cada tipo de diseño y **todas** las porciones que se usarán como citas, nombres, fechas, cantidades o afirmaciones centrales. Revisar columnas, notas al pie, sellos, manuscritos y orden de lectura. En tablas, comprobar alineación celda por celda donde fundamente el hallazgo; no reconstruir columnas por plausibilidad.

Errores frecuentes que cambian la noticia: 0/O, 1/l/I, signos negativos, separadores decimales, miles, porcentajes, tildes en nombres, fechas y encabezados que pasan a ser datos. Marcar ilegible o dudoso y conservar la forma reconocida en la salida cruda; toda corrección va en una copia y registro aparte.

## Entregar

Texto crudo, copia revisada si corresponde, referencia de página y registro de dudas/correcciones; si una página falló, indicar cuál. No llamar «transcripción fiel» a una salida sin revisión. Una cita de un escaneo debe poder volver a su página y región visual. Para verificar su contenido, pasar a `newsharness-factcheck`: reconocer caracteres no demuestra autenticidad del documento.

## Plantilla de entrega

```
Documento: <nombre> · <N> páginas (<n> con texto digital, <n> escaneadas)
Salida cruda: <ruta>       Copia revisada: <ruta o "no se pidió">
Revisado contra la imagen: <páginas/regiones>
Dudas: p. 3 «1O.000» ¿10.000? · p. 7 sello ilegible · p. 9 tabla con columnas corridas
Fallos: <páginas que no se procesaron y por qué>
```

## Consejos para tablas

- Pedir la tabla página por página y reconstruirla en CSV sólo con celdas confirmadas visualmente.
- Comparar totales de fila/columna con los impresos: si no cierran, hay un error de reconocimiento o de lectura.
- Marcar celdas dudosas en una columna aparte; no completarlas por interpolación.

## Cuando el kit se instaló dentro de otro proyecto

Los comandos anteriores parten de la raíz del checkout del kit. En un proyecto instalado, el runtime está en `.newsharness-kit/`; en una instalación global, en `~/.newsharness-kit/` (Windows: `%USERPROFILE%\.newsharness-kit`). Reemplazar el prefijo `python3 scripts/newsharness.py` por la ruta que corresponda, por ejemplo `python3 ~/.newsharness-kit/scripts/newsharness.py`. Resolver la ruta del perfil, espacio de trabajo y modelos desde el contexto real; no crear copias redundantes para hacer funcionar un ejemplo.
