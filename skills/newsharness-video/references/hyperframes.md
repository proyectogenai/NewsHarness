# HyperFrames: títulos, zócalos y subtítulos con efectos

[HyperFrames](https://github.com/heygen-com/hyperframes) es un framework open source (Apache-2.0) de HeyGen que convierte HTML, CSS y animaciones en MP4. Trae skills propias para agentes y unos 450 bloques listos (títulos, zócalos, subtítulos animados, gráficos, mapas). Revisado el 2026-11-08, versión `v0.9.22`.

Se usa cuando el pedido supera lo que da un `.ass` con FFmpeg: títulos animados, zócalos, placas, gráficos o subtítulos con un estilo particular.

## Antes de instalar

- **Requisitos:** Node.js 22 o superior y FFmpeg. Usa un navegador sin interfaz para renderizar.
- **Pedir autorización** explicando qué se instala: el paquete `hyperframes` de npm, sus skills (`npx hyperframes skills update`, con las 4 del conjunto básico) y el navegador que descarga para renderizar. Dar el tamaño que informe la instalación. No instalar en forma global sin pedido explícito.
- **Telemetría:** el CLI envía estadísticas de uso. Desactivarla antes del primer uso con `npx hyperframes telemetry disable` o la variable `HYPERFRAMES_NO_TELEMETRY=1`, y comprobar con `npx hyperframes telemetry status`.
- **Sólo local.** HyperFrames ofrece render en la nube, publicación y un plan Pro con modelos de HeyGen (avatares, voces, video, música e imágenes generados). Para material periodístico se usa **sólo el render local**. No conectar una cuenta de HeyGen, no usar avatares ni voces generadas y no subir material a sus servicios sin la autorización del medio.

## Uso básico

```bash
npx hyperframes init clip-01
cd clip-01
npx hyperframes preview      # vista previa en el navegador
npx hyperframes render       # MP4 local
```

Con sus skills instaladas, el agente sigue `/hyperframes` (contrato de render y flujo de trabajo) y `/hyperframes-registry` (bloques listos). Usar los bloques del catálogo antes de dibujar algo desde cero: `npx hyperframes catalog --tag caption-style --json` lista los estilos de subtítulos.

## Transcript: usar el del kit

HyperFrames tiene su propio comando `transcribe`, pero **por defecto usa el modelo `small.en`, que traduce al inglés** sin avisar. Además, sobrescribe `assets/transcript.json` en cada corrida.

Por eso se prefiere el transcript **ya revisado** de `newsharness-transcripcion`, convertido a la lista de palabras que espera HyperFrames:

```bash
python3 scripts/video.py palabras --transcripcion transcript.json --desde 00:03:12.4 --hasta 00:03:41.0 --salida clip-01/assets/palabras-clip-01.json
```

El resultado es `[{"id": "w0", "text": "No", "start": 0.0, "end": 0.3}, …]`, con los tiempos corridos al clip. Si igual se usa su `transcribe`, indicar siempre `--model small --language es`.

## Criterios que se mantienen

- Los subtítulos siguen siendo citas literales ([subtitulos.md](subtitulos.md)).
- Zócalos con nombre y cargo confirmados.
- Gráficos con fuente y fecha visibles, igual que en la nota.
- Un fondo o elemento generado, si se usa, se rotula y no simula registro.
- `remove-background` (recortar a la persona del fondo) descarga un modelo de unos 168 MB y altera la imagen: sólo con pedido explícito y nunca para cambiar el lugar donde ocurrió algo.
