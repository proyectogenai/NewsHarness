# Formatos de video para redes

Valores de partida, revisados el 2026-11-08. Las plataformas cambian sus límites seguido: confirmar en la ayuda oficial de cada una antes de un trabajo grande.

| Formato | Resolución | Uso | Zona segura del texto |
|---|---|---|---|
| 9:16 vertical | 1080×1920 | Reels, Shorts, TikTok, historias | Dejar libres ~250 px arriba, ~620 px abajo y ~140 px a la derecha |
| 4:5 | 1080×1350 | Publicación en el feed | Margen inferior de ~220 px |
| 1:1 | 1080×1080 | Feed, X, LinkedIn | Margen inferior de ~110 px |
| 16:9 horizontal | 1920×1080 | YouTube, web, X, televisión | Dentro del 90 % central; subtítulos a ~80 px del borde inferior |

## Duración

- **Reel o Short informativo:** entre 15 y 60 segundos. Una idea por clip, con la cita en los primeros 3 segundos.
- **Clip de declaración:** la frase completa con su contexto mínimo. Si no entra, va un clip más largo, no un corte más agresivo.
- **Horizontal para web:** lo que pida la nota; con subtítulos, porque una gran parte se mira sin sonido.

## Exportación

- Video H.264 (`libx264`), `yuv420p`, `-crf 18` y 25 o 30 cuadros por segundo, iguales a los del original.
- Audio AAC de 192 kbps, normalizado a −14 LUFS para redes.
- `-movflags +faststart`, para que empiece a reproducirse antes de bajar todo el archivo.

## Elementos de cierre

Placa final con el nombre del medio, la fuente del material y la fecha de grabación, si no es del día. Si el video mezcla material de archivo con material nuevo, rotular el de archivo con su fecha.
