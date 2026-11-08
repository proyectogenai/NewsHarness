# Recetas de FFmpeg para video periodístico

Recetas para que el agente las adapte al archivo real. Todas escriben un archivo **nuevo**: usar `-n` (no sobrescribir) y nunca la misma ruta de entrada y salida. Antes de cortar, mirar el archivo con `ffprobe`.

```bash
ffprobe -v error -show_entries format=duration:stream=codec_type,codec_name,width,height,r_frame_rate -of json ORIGINAL
```

## Cortar un tramo

Preciso al cuadro (reencoda). `-ss` antes de `-i` es rápido y, al reencodar, exacto:

```bash
ffmpeg -n -ss 00:03:12.4 -i ORIGINAL -t 28.6 -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart clip.mp4
```

Sin reencodar (instantáneo, pero corta en el keyframe más cercano y puede arrancar unos segundos antes): `-c copy`. Sirve para una vista previa, no para el corte final de una cita.

Para varios cortes con su cita y el contexto, usar `scripts/video.py cortes`, que arma estos comandos y deja registro.

## Reencuadrar

| Formato | Filtro |
|---|---|
| 9:16 (1080×1920), recorte al centro | `-vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1"` |
| 9:16 con el plano completo y fondo desenfocado | `-filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1"` |
| 1:1 (1080×1080) | `-vf "scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,setsar=1"` |
| Recorte desplazado (persona a la izquierda) | `crop=1080:1920:X:0` con X entre 0 y el ancho escalado menos 1080 |

El recorte al centro puede dejar afuera a quien habla: mirar un cuadro (`-frames:v 1 cuadro.png`) antes de exportar. Con dos personas en plano abierto, preferir el fondo desenfocado.

## Audio

Normalizar volumen para redes (−14 LUFS integrado, picos a −1 dB):

```bash
ffmpeg -n -i clip.mp4 -c:v copy -af loudnorm=I=-14:TP=-1:LRA=11 -c:a aac -b:a 192k clip-norm.mp4
```

- Extraer audio: `ffmpeg -n -i ORIGINAL -vn -c:a aac -b:a 192k audio.m4a`.
- Clip de audio con imagen fija, para redes: `ffmpeg -n -loop 1 -i placa.png -i audio.m4a -c:v libx264 -tune stillimage -pix_fmt yuv420p -c:a aac -shortest audio-video.mp4`.
- Fundidos de 0,3 s al principio y al final: `-af "afade=t=in:d=0.3,afade=t=out:st=DURACION_MENOS_0.3:d=0.3"`.

## Unir clips

Con el mismo códec y resolución (salidas de `video.py cortes` en un mismo formato), crear `lista.txt` con `file 'clip-01.mp4'` por línea y ejecutar:

```bash
ffmpeg -n -f concat -safe 0 -i lista.txt -c copy unido.mp4
```

Un corte entre dos fragmentos de una misma declaración se tiene que notar (un fundido corto o una placa). No unir dos frases como si fueran una sola respuesta.

## Subtítulos

- Quemarlos en la imagen: `scripts/video.py quemar` (usa `ass=archivo.ass`).
- Dejarlos como pista aparte, para que la plataforma los muestre o los oculte: `ffmpeg -n -i clip.mp4 -i clip.srt -c copy -c:s mov_text clip-con-pista.mp4`.

## Placas y miniaturas

- Cuadro para miniatura: `ffmpeg -n -ss 00:00:05 -i clip.mp4 -frames:v 1 miniatura.png`.
- Hoja de contactos, un cuadro por segundo, para revisar encuadre o subtítulos ya quemados: `ffmpeg -n -i clip.mp4 -vf "fps=1,scale=320:-1,tile=6x5" contactos.png`.

## Extras opcionales

Se instalan sólo si el pedido los justifica, explicando origen y tamaño y con autorización:

- **Auto-Editor** (Unlicense, [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor)): quita silencios largos. En una entrevista, un silencio puede ser parte de la respuesta: proponer el corte y revisarlo, no aplicarlo a ciegas sobre una declaración.
- **PySceneDetect** (BSD-3, [Breakthrough/PySceneDetect](https://github.com/Breakthrough/PySceneDetect)): detecta cambios de plano para ubicar momentos en un material largo.

Estabilizar, escalar con IA, separar voces o cambiar el fondo existe, pero altera la imagen o el sonido registrados: no forma parte de esta skill.
