# Preparación técnica a cargo del agente

Estos comandos los ejecuta el agente, no se convierten en deberes para el periodista. Ejecutarlos desde la raíz del kit; resolver las rutas y versiones antes de correrlos.

## Diagnóstico de lectura

```bash
python3 scripts/newsharness.py doctor --json
python3 scripts/newsharness.py plan --quality base --json
```

`doctor`/`plan` no conceden permisos ni instalan dependencias. Si Python no existe, identificar el sistema por herramientas disponibles y proponer al usuario una instalación oficial, con su alcance. No inventar que se completó un diagnóstico.

Comprobar sistema/arquitectura, memoria y espacio disponibles, herramientas locales, versión y capacidades reales. No ejecutar scripts desconocidos por aparecer en un resultado de búsqueda. Revisar `config/toolchain.lock.json` y la ayuda de la versión instalada; un nombre de comando no prueba compatibilidad.

## Elección de calidad y aprobación

Preferir el modo de calidad que el plan considere viable para el equipo. No bajar silenciosamente a `tiny`: es un modo restringido, requiere explicar la pérdida de precisión, aceptación explícita y revisión de citas/nombres/números. El flag `--allow-restricted-tiny` expresa una decisión ya aprobada, no reemplaza la aprobación. No pedir al periodista tamaño de RAM o rutas técnicas; medir y resolverlos.

Separar estas autorizaciones:
1. descargar un artefacto (origen, destino y tamaño);
2. instalar o ejecutar software (qué cambia y permisos);
3. enviar contenido a un servicio externo (qué información, a quién y para qué).

La descarga de un modelo no implica enviar el audio. El procesamiento local no evita que el agente remoto reciba los fragmentos de texto que se le muestren. Para un archivo confidencial, usar únicamente el flujo aprobado por el medio o detener su lectura.

El subcomando `fetch`, si se usa, sólo acepta un ID del lock con URL inmutable y hash SHA-256. No editar el lock para eludir una comprobación fallida ni autorizar un hash observado después como si hubiera sido confiable antes. Verificar la documentación y la ayuda local para su sintaxis vigente.

## Crear el espacio de trabajo

Preparar el JSON con el esquema de [perfil-editorial.md](perfil-editorial.md); validarlo mediante el runtime:

```bash
python3 scripts/newsharness.py init --workspace RUTA_NUEVA --profile PERFIL_JSON
```

Usar una carpeta nueva y sin secretos, distinta de los originales. No sobrescribir un perfil o un proyecto existente. Si hay una instalación previa, comparar y actualizar con una copia de seguridad y el alcance autorizado.

## Instalar las skills en el proyecto elegido

```bash
python3 scripts/newsharness.py install-skills --project PROYECTO --agent codex
```

Sustituir `codex` por `claude` u `opencode` según el agente elegido. No instalar los tres porque existan. El núcleo se copia a su ruta de descubrimiento; conservar instrucciones existentes del proyecto y revisar cualquier colisión antes de continuar. Los adaptadores no convierten las políticas del modelo en un sandbox ni garantizan paridad de herramientas.

## Instalación global: NewsHarness disponible en cualquier consulta

Sólo si el usuario la pidió o la confirma explícitamente. Desde la carpeta descomprimida del kit:

```bash
python3 scripts/newsharness.py install-skills --global --agent claude
```

Sustituir `claude` por `codex` u `opencode` según el agente en uso. El kit queda en `~/.newsharness-kit/` y las skills en la carpeta de usuario del agente: `~/.claude/skills/`, `~/.codex/skills/` (o `$CODEX_HOME/skills/`) o `~/.config/opencode/skills/`. **No se modifican** `CLAUDE.md`, `AGENTS.md` ni otras instrucciones globales del usuario: las reglas comunes viajan dentro de cada skill. Un manifiesto (`~/.newsharness-kit/.newsharness-install.json`) registra la huella de cada archivo instalado.

- **Actualizar** desde una versión nueva descomprimida: agregar `--update`. Sólo reemplaza archivos de NewsHarness que el usuario no modificó; si encuentra uno editado, se detiene sin cambiar nada.
- **Desinstalar:** `python3 ~/.newsharness-kit/scripts/newsharness.py install-skills --global --agent claude --uninstall`. Quita sólo los archivos de NewsHarness sin modificar; conserva los editados y avisa cuáles quedaron. El kit compartido se retira cuando no queda ningún agente registrado.
- Perfiles, espacios de trabajo y modelos descargados no son parte de la instalación: ni se crean ni se borran con estos comandos.

Para el espacio de trabajo global proponer una carpeta visible del usuario, por ejemplo `~/Documentos/NewsHarness` (o la equivalente del sistema), distinta de `~/.newsharness-kit/`: el código y los originales periodísticos no se mezclan. Después de instalar, pedir que reinicie el agente y comprobar que descubre las skills; Codex trata las skills de usuario como experimentales según la versión.

## Prueba mínima

Usar los archivos ficticios de `examples/demo-publica/`, nunca material reservado como prueba de conectividad. Para transcripción, incluir el modelo VAD aprobado que el runtime descubre localmente; si falta, resolver su descarga con autorización. Comprobar que existe salida legible, procedencia y original preservado. No presentar una prueba de OCR como prueba de transcripción ni un stub de test como ejecución real del motor. Informar estado por capacidad: probado, disponible sin prueba, bloqueado o no configurado.

## Cuando el kit se instaló dentro de otro proyecto

Los comandos anteriores parten de la raíz del checkout del kit. En un proyecto instalado, el runtime está en `.newsharness-kit/`; en una instalación global, en `~/.newsharness-kit/` (Windows: `%USERPROFILE%\.newsharness-kit`). Reemplazar el prefijo `python3 scripts/newsharness.py` por la ruta que corresponda, por ejemplo `python3 ~/.newsharness-kit/scripts/newsharness.py`. Resolver la ruta del perfil, espacio de trabajo y modelos desde el contexto real; no crear copias redundantes para hacer funcionar un ejemplo.
