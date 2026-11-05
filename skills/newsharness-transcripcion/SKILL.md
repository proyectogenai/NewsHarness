---
name: newsharness-transcripcion
description: Transcribir entrevistas, conferencias y audios periodísticos con procesamiento local, marcas de tiempo y revisión de citas, sin inventar palabras ni hablantes; usar cuando pidan "desgrabá esta entrevista", "transcribí el audio", "buscá en qué minuto dijo…" o "sacame las citas".
---
# Transcripción local, no reconstrucción de lo dicho

> **Reglas comunes y ubicación del kit.** Antes de actuar, leer `AGENTS.md` del kit: en el kit fuente está en la raíz; instalado en un proyecto, en `.newsharness-kit/AGENTS.md`; instalado de forma global, en `~/.newsharness-kit/AGENTS.md` (Windows: `%USERPROFILE%\.newsharness-kit\AGENTS.md`). Los comandos `python3 scripts/newsharness.py` de esta skill se ejecutan desde esa misma ubicación del kit.

## Cuándo usarla

- **Sí:** entrevistas propias, conferencias, audios autorizados, videos con audio descargado legítimamente.
- **Derivar:** analizar lo que dijo una persona y contrastarlo → `newsharness-discursos`; usar las citas en una nota → `newsharness-redaccion`.
- **Audio largo:** calibrar primero con 60–120 segundos (`calibrate`) para estimar tiempo y elegir modelo; avisar al periodista cuánto va a tardar antes de lanzar una corrida de horas.

## Flujo rápido

1. Confirmar autorización y sensibilidad; todo local.
2. Diagnóstico y modelo (`base` por defecto; `small` si el equipo lo permite).
3. Corrida nueva con VAD; revisar duración procesada y huecos.
4. Escuchar cada tramo citable con unos segundos de contexto.
5. Entregar cruda + revisada + tabla de citas con minuto y estado.

## Proteger y preparar

Confirmar que el usuario tiene autorización editorial para trabajar con la grabación y clasificar su sensibilidad. No subir audio a servicios externos ni mostrar texto reservado a un modelo remoto sin aprobación del flujo por el medio. No confundir disponer del archivo con permiso para difundirlo.

El agente identifica formato, duración y canales mediante herramientas disponibles; no pide flags al periodista. Usar `newsharness-onboarding` para el diagnóstico y modelos. Comprobar el ejecutable local y su ayuda antes de usar opciones; resolver dependencias con aprobación, no con instaladores silenciosos.

## Ejecutar

Desde la raíz del kit:

```bash
python3 scripts/newsharness.py transcribe --workspace ESPACIO --input AUDIO --model MODELO_LOCAL --quality base --language es
```

`--model` es un archivo verificado, no un nombre para que el motor descargue automáticamente. `base` no garantiza precisión suficiente; revisar muestra y material publicable. Si el equipo permite `small`, el agente puede proponerlo. `tiny` requiere aceptación explícita de un modo restringido y `--allow-restricted-tiny`; no elegirlo en secreto por velocidad. El runtime busca por defecto el VAD local aprobado `models/ggml-silero-v6.2.0.bin` dentro del espacio y verifica su hash. Si falta, se detiene sin descargar: el agente prepara la descarga autorizada desde el lock. `--vad-model` permite una ruta local compatible y verificada; no se le pide al periodista que la elija. VAD reduce el riesgo de texto alucinado durante silencios, pero no lo elimina ni identifica personas. `--allow-no-vad` sólo se usa con aceptación explícita del mayor riesgo y revisión reforzada, nunca como atajo silencioso ante un bloqueo.

El runtime produce una corrida nueva, conserva original y procedencia y no publica. Verificar duración procesada, archivos de salida y segmentos omitidos. La ausencia de palabras en un silencio o ruido no demuestra ausencia de una declaración.

## Fidelidad y límites

- Conservar una salida cruda separada de la versión revisada. No sustituir negaciones, nombres, cifras ni tecnicismos por lo que «tendría sentido».
- Marcar `[inaudible HH:MM:SS]`, `[palabra dudosa: …]` o solapamientos. No rellenar huecos por contexto.
- Las marcas de tiempo ubican segmentos; **no son diarización**. No inventar hablantes. Usar `Voz 1`/`Voz 2` sólo tras diferenciarlos de manera fiable; identidad real sólo con evidencia o confirmación del usuario.
- No eliminar muletillas o corregir gramática dentro de una cita como si fuera literal. Si se pide lectura limpia, separarla y rotularla como edición no literal; mantener negaciones, reservas y sentido. Omitir con puntos suspensivos sólo cuando no se altera contexto y la norma editorial lo admite.
- Revisar en el audio todos los tramos citables y sus segundos previos/posteriores, además de nombres, cifras y afirmaciones centrales. Una confianza del motor no reemplaza escuchar.
- Detectar falsos textos repetidos en silencio, música o ruido. No convertir una hipótesis acústica en una declaración atribuida.

## Entrega

Transcripción cruda, versión revisada si se pidió, timestamps, segmentos dudosos y límite de identificación de voces. Indicar qué se escuchó efectivamente y qué sigue pendiente. Para usar una frase en una nota, entregar también el timestamp y estado de revisión de la cita. Si no hay audio accesible, trabajar con el texto como **transcripción aportada no cotejada**, nunca afirmar que se escuchó.

## Plantilla de citas para la nota

```
| Minuto | Cita (literal)                             | Escuchada | Nota                                  |
|--------|--------------------------------------------|-----------|---------------------------------------|
| 12:41  | «No vamos a subir las tarifas este año»    | sí        | Voz 1 = entrevistado (conf. usuario)  |
| 27:05  | «[palabra dudosa: cuatrocientos] millones» | no        | Ruido; escuchar antes de usar         |
```

## Errores frecuentes

- Cifras y negaciones mal reconocidas (un «no» que desaparece, «catorce» por «cuarenta»).
- Nombres propios «corregidos» al más parecido conocido.
- Texto inventado durante silencios o música (por eso VAD y revisión).
- Atribuir una frase a una persona sin haber separado las voces.

## Cuando el kit se instaló dentro de otro proyecto

Los comandos anteriores parten de la raíz del checkout del kit. En un proyecto instalado, el runtime está en `.newsharness-kit/`; en una instalación global, en `~/.newsharness-kit/` (Windows: `%USERPROFILE%\.newsharness-kit`). Reemplazar el prefijo `python3 scripts/newsharness.py` por la ruta que corresponda, por ejemplo `python3 ~/.newsharness-kit/scripts/newsharness.py`. Resolver la ruta del perfil, espacio de trabajo y modelos desde el contexto real; no crear copias redundantes para hacer funcionar un ejemplo.
