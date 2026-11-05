# Instalar NewsHarness en tu agente

Para periodistas: no hace falta saber programar ni usar la terminal. Tu agente (Claude Code, Codex u OpenCode) hace la parte técnica y te pide permiso antes de cada paso importante.

## Antes de empezar

- Tener instalado uno de los agentes y una sesión iniciada.
- Tener el archivo `newsharness-kit-v0.1.0.zip`. Recibilo por un canal de confianza (en mano, pendrive o el Drive del equipo), no de un enlace desconocido.
- En una computadora del diario, Sistemas puede tener bloqueada la instalación de programas. Si el agente lo detecta, te va a avisar; no intenta saltear esos controles.

## Pasos

1. Creá una carpeta vacía, por ejemplo `Documentos\NewsHarness-instalador`.
2. Poné el ZIP adentro, **sin descomprimir**.
3. Abrí esa carpeta en tu agente.
4. Copiá y pegá este texto:

```text
Quiero instalar NewsHarness, un kit para periodistas, para usarlo en todas mis consultas. En esta carpeta hay un ZIP con el kit.
1. Descomprimí ese ZIP acá mismo, sin borrarlo ni modificarlo. No bajes el kit de Internet ni de ninguna otra fuente.
2. Comprobá los archivos con CHECKSUMS.sha256. Si alguno no coincide, frená y avisame.
3. Leé README.md, AGENTS.md y el adaptador de tu agente en adapters/. Instalá NewsHarness de forma global con el instalador del kit (install-skills --global, con el agente que sos).
4. No modifiques mis instrucciones globales existentes (CLAUDE.md, AGENTS.md) ni otros archivos míos.
5. Antes de instalar o descargar cualquier otra cosa (Python, motores, modelos), explicame qué es, de dónde viene y cuánto pesa, y esperá mi OK.
6. Al terminar, decime en lenguaje simple qué quedó instalado, cómo se desinstala y cómo empiezo el onboarding.
```

5. Cuando termine, **cerrá y volvé a abrir el agente** para que encuentre las skills.
6. Desde cualquier carpeta, pedile: «Configurá mi perfil de NewsHarness».

## Qué queda instalado

- El kit, en una carpeta oculta de tu usuario: `.newsharness-kit`.
- Las skills, en la carpeta de skills de tu agente.
- Nada más: tus instrucciones globales, documentos y configuración no se tocan.

Tus notas, audios y perfil van en una carpeta aparte que te propone el agente durante el onboarding, nunca dentro de `.newsharness-kit`.

## Actualizar o desinstalar

Pedíselo a tu agente con estas palabras:

- **Actualizar** (con el ZIP nuevo en una carpeta vacía): «Actualizá NewsHarness con este ZIP usando install-skills --global --update».
- **Desinstalar:** «Desinstalá NewsHarness con install-skills --global --uninstall».

Si modificaste algún archivo del kit, el instalador no lo pisa ni lo borra: te avisa y lo deja como está.

## Si algo falla

Anotá qué pediste, qué respondió el agente y en qué sistema estás. Reportalo en la pestaña *Issues* del repositorio, sin pegar material periodístico reservado ni datos de fuentes.
