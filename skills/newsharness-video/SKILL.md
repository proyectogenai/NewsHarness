---
name: newsharness-video
description: Hacer videos periodísticos con material propio, como recortar un video o un audio, armar un reel vertical, poner subtítulos con estilo de redes a partir del transcript o sumar títulos y zócalos, sin cambiar el sentido de lo dicho; usar cuando pidan "armá un reel con esta entrevista", "recortá del minuto 3 al 4", "ponele subtítulos", "sacá un clip de esta frase" o "hacé un video para redes".
---
# Video con material propio, sin cambiar lo que se dijo

> **Reglas comunes y ubicación del kit.** Antes de actuar, leer `AGENTS.md` del kit: en el kit fuente está en la raíz; instalado en un proyecto, en `.newsharness-kit/AGENTS.md`; instalado de forma global, en `~/.newsharness-kit/AGENTS.md` (Windows: `%USERPROFILE%\.newsharness-kit\AGENTS.md`). Los comandos `python3 scripts/video.py` de esta skill se ejecutan desde esa misma ubicación del kit.

## Cuándo usarla

- **Sí:** recortar un video o audio propio o autorizado, sacar un clip de una frase, armar un reel 9:16, poner subtítulos, sumar título, zócalo o placa final, y adaptar un mismo clip a varios formatos.
- **Derivar:** desgrabar y revisar el audio → `newsharness-transcripcion` (primero, siempre que haya subtítulos o cortes por frase); chequear lo que se dice en el clip → `newsharness-discursos` o `newsharness-factcheck`; textos del posteo → `newsharness-redaccion`.
- **Fuera de alcance:** generar personas, voces o escenas con IA, clonar una voz, cambiar lo que alguien dijo y publicar en redes. Se entrega un archivo para revisión, no se publica.

## Reglas propias del video

1. **Un corte no puede cambiar el sentido.** Antes de cortar, mostrar qué se dijo **antes y después** del tramo elegido (`cortes --transcripcion`). Si el contexto cambia, matiza o niega la frase, advertirlo y no avanzar sin decisión del periodista. Una pregunta que la frase responde también es contexto.
2. **El subtítulo es una cita.** Sale del transcript **revisado contra el audio**, literal: sin corregir gramática ni sacar muletillas que cambien el tono, y sin «mejorar» cifras o nombres. Si se acorta para pantalla, se rotula como edición y se avisa.
3. **El original no se toca.** Se trabaja sobre copias; `video.py` nunca sobrescribe y registra el SHA256 del original y cada comando.
4. **Nada sintético presentado como real.** No hay caras, voces ni escenas generadas que parezcan registro. Un gráfico, ilustración o fondo generado se rotula como tal. No usar las funciones de avatar, voz o video generado de servicios externos.
5. **Derechos y personas.** Preguntar de quién es el material y si se puede usar en redes. Prestar atención a menores, víctimas y fuentes que pidieron reserva: pueden aparecer en el cuadro o en el audio.
6. **Material sensible, sólo local.** No subir audio ni video a servicios en la nube (transcripción, render, «mejoras» de audio) sin la autorización que exija el medio.
7. **Entrega para revisión.** El periodista mira el video completo antes de usarlo; el agente no puede ver el resultado, sólo comprobarlo técnicamente.

## Herramientas

| Necesidad | Herramienta | Requisito |
|---|---|---|
| Cortar, unir, reencuadrar, volumen, exportar | **FFmpeg** ([recetas](references/ffmpeg.md)) | FFmpeg, que ya usa la transcripción |
| Clips desde una lista de cortes con su cita, con contexto | `scripts/video.py cortes` | FFmpeg |
| Subtítulos con estilo de redes (resaltado, karaoke, frase) | `scripts/video.py subtitulos` + `quemar` ([criterios](references/subtitulos.md)) | FFmpeg; sin Node |
| Títulos animados, zócalos, subtítulos con efectos más elaborados | **HyperFrames** ([guía](references/hyperframes.md)) | Node 22+ y FFmpeg; instalación con permiso |
| Quitar silencios largos, detectar planos | Auto-Editor, PySceneDetect ([extras](references/ffmpeg.md#extras-opcionales)) | Instalación con permiso |

Empezar por lo más simple que resuelva el pedido: un clip con subtítulos sale con FFmpeg y `video.py`. HyperFrames se propone cuando se piden títulos animados, zócalos o un estilo que el `.ass` no da. Medidas y duraciones por red: [formatos.md](references/formatos.md).

## Flujo rápido

1. **Ingreso.** Qué material hay, de quién es y para qué red y formato (9:16, 16:9, 1:1, 4:5). Duración buscada. Preservar el original y trabajar en un espacio aparte.
2. **Transcript.** Con `newsharness-transcripcion`, en el idioma real del audio y **con `--palabras`** si va a haber subtítulos animados:
   ```bash
   python3 scripts/newsharness.py transcribe --workspace ESPACIO --input VIDEO --model MODELO --quality base --language es --palabras
   ```
   Revisar contra el audio los tramos que se van a usar.
3. **Selección.** El periodista elige los fragmentos por su cita. Armar `cortes.json`:
   ```json
   {"cortes": [{"id": "clip-01", "desde": "00:03:12.4", "hasta": "00:03:41.0",
                "cita": "No vamos a subir las tarifas este año", "nota": "responde a la pregunta por el FMI"}]}
   ```
4. **Plan y contexto, sin ejecutar.** Mostrar al periodista, por cada corte, la cita y el texto de antes y después:
   ```bash
   python3 scripts/video.py cortes --fuente VIDEO --lista cortes.json --salida-dir ESPACIO/video/clips --transcripcion transcript.json --formato 9:16
   ```
   Con su OK, repetir con `--ejecutar`. Queda `registro-cortes.json` con hashes y comandos.
5. **Subtítulos.** Del mismo transcript, corrido al tramo del clip:
   ```bash
   python3 scripts/video.py subtitulos --transcripcion transcript.json --desde 00:03:12.4 --hasta 00:03:41.0 --formato 9:16 --estilo resaltado --salida ESPACIO/video/clips/clip-01.ass
   python3 scripts/video.py quemar --video ESPACIO/video/clips/clip-01.mp4 --subtitulos ESPACIO/video/clips/clip-01.ass --salida ESPACIO/video/clip-01-subtitulado.mp4 --ejecutar
   ```
   Para HyperFrames, `video.py palabras` entrega la lista de palabras que usa su skill de subtítulos.
6. **Control técnico.** Duración y resolución con `ffprobe`, audio presente, subtítulos sincronizados en el inicio, el medio y el final, y que el reencuadre al centro no dejó afuera a quien habla.
7. **Entrega.** Archivo final, ficha y pendientes. El periodista lo mira completo.

## Plantilla de entrega

```
**Video:** <archivo> · <formato> · <duración> · <resolución>
**Original:** <archivo> (SHA256 <primeros 12>) · derechos: <de quién / autorización>
**Cortes:** <id> <desde>–<hasta> «<cita>» · contexto revisado: sí/no
**Subtítulos:** literales del transcript revisado / con edición rotulada · estilo <…>
**Elementos agregados:** <títulos, zócalos, música, gráficos; cuáles son generados>
**Revisado por el agente:** duración, sincronía en 3 puntos, audio, encuadre
**Pendiente para el periodista:** mirar el video completo · confirmar nombres y cargos del zócalo
```

## Errores frecuentes

- Cortar la respuesta y dejar afuera la pregunta, o el «pero» que viene después.
- Transcribir en español con un modelo `.en`: lo traduce al inglés sin avisar (pasa en HyperFrames si no se indica el modelo).
- Subtítulos con tiempos del video completo pegados sobre un clip: siempre usar `--desde`/`--hasta` del mismo corte.
- Reencuadrar a 9:16 un plano abierto y dejar a la persona fuera del cuadro.
- Zócalo con nombre o cargo sin confirmar. Es un dato más de la nota.
- Música de una librería «gratuita» sin revisar su licencia de uso en redes.

## Cuando el kit se instaló dentro de otro proyecto

Los comandos parten de la raíz del kit. En un proyecto instalado, los scripts están en `.newsharness-kit/scripts/`; en una instalación global, en `~/.newsharness-kit/scripts/` (Windows: `%USERPROFILE%\.newsharness-kit\scripts`). Reemplazar el prefijo `python3 scripts/` por la ruta que corresponda.
