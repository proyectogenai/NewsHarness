# Subtítulos para video periodístico

## Qué texto va

- El subtítulo **reproduce lo dicho**. Sale del transcript revisado contra el audio, con las mismas palabras.
- Se puede dividir en bloques y líneas, pero no reescribir. Si hace falta acortar por espacio, usar una edición rotulada y avisar al periodista; nunca cambiar una cifra, una negación o un nombre.
- Muletillas: sacarlas sólo si el medio lo admite y no cambian el tono ni el sentido («eh… no sé» no es lo mismo que «no sé»).
- Lo inaudible queda marcado `[inaudible]`, no se completa.
- Una voz en otro idioma se subtitula con una **traducción** rotulada; no se presenta como transcripción literal.

## Lectura

| Regla | Valor de partida |
|---|---|
| Caracteres por línea | 9:16: ~22 · 1:1: ~28 · 16:9: ~38 |
| Líneas por bloque | 2 como máximo |
| Tiempo en pantalla | entre 1 y 3,5 segundos por bloque |
| Corte de bloque | fin de oración, pausa mayor a 0,6 s, o límite de caracteres |
| Velocidad | no más de ~17 caracteres por segundo; si el habla es más rápida, bloques más cortos |

`video.py subtitulos` aplica estos cortes. Revisar que ningún bloque separe un artículo de su sustantivo o una negación de su verbo.

## Estilos de `video.py`

| Estilo | Qué hace | Cuándo |
|---|---|---|
| `resaltado` (por defecto) | Muestra el bloque y colorea la palabra que se está diciendo | Reels y videos verticales |
| `karaoke` | El color avanza palabra por palabra | Testimonios, ritmo más lento |
| `frase` | El bloque entero, sin animación | Horizontal, entrevistas largas, tono sobrio |

Los dos primeros necesitan **tiempos por palabra**: transcribir con `--palabras`. Con un SRT o un JSON por frases, `--estimar-palabras` reparte el tiempo según el largo de cada palabra: sirve como efecto visual, **no** como minuto de una cita.

Opciones: `--formato`, `--fuente`, `--color`, `--color-resaltado` (#RRGGBB) y `--max-caracteres`. La fuente tiene que estar instalada en el equipo; si no, FFmpeg usa otra parecida.

## Ubicación y legibilidad

- **Zona segura:** en 9:16 la interfaz de las redes tapa la franja inferior y el costado derecho. `video.py` deja el subtítulo a unos 620 px del borde inferior en 1080×1920. Los márgenes por formato están en [formatos.md](formatos.md).
- No tapar la cara de quien habla, ni un zócalo, ni un dato en pantalla. Si el material ya trae texto quemado, revisarlo con la hoja de contactos de [ffmpeg.md](ffmpeg.md#placas-y-miniaturas).
- Contraste: letra clara con borde oscuro. Sobre fondos claros, subir el borde o sumar una franja semitransparente detrás del texto.

## Accesibilidad

Para personas sordas o con hipoacusia también cuentan los sonidos relevantes (`[aplausos]`, `[silbidos]`). Se agregan a mano, rotulados entre corchetes, y nunca se inventan. Cuando la plataforma lo permite, dejar además una pista de subtítulos aparte (SRT) con el mismo texto.

## Control antes de entregar

1. Sincronía al principio, en el medio y al final del clip.
2. Texto literal contra el audio en todas las cifras, nombres y negaciones.
3. Ningún bloque fuera de la zona segura ni cortado por el borde.
4. Si el transcript tenía tiempos estimados, decirlo en la entrega.
