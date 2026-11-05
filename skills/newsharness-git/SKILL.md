---
name: newsharness-git
description: Guardar versiones de borradores, ver qué cambió entre versiones, recuperar una versión anterior y compartir con edición usando git por cuenta del periodista, sin jerga ni riesgo de perder trabajo; usar cuando pidan "guardá esta versión", "qué cambié", "volvé a la versión de ayer" o "pasale esto al editor".
---
# Versiones de tus textos, sin aprender git

> **Reglas comunes y ubicación del kit.** Antes de actuar, leer `AGENTS.md` del kit: en el kit fuente está en la raíz; instalado en un proyecto, en `.newsharness-kit/AGENTS.md`; instalado de forma global, en `~/.newsharness-kit/AGENTS.md` (Windows: `%USERPROFILE%\.newsharness-kit\AGENTS.md`). Los comandos `python3 scripts/newsharness.py` de esta skill se ejecutan desde esa misma ubicación del kit.

Git es un historial de versiones: cada «versión guardada» es una foto de la carpeta que se puede comparar o recuperar. El agente ejecuta los comandos; al periodista se le habla de versiones, cambios y copias, nunca de commits, HEAD o ramas, salvo que pregunte.

## Vocabulario para hablar con el periodista

| El periodista dice | Lo que hace el agente | Cómo se lo cuenta |
|---|---|---|
| «Guardá esta versión» | `git add` de los archivos de trabajo + `git commit -m "<qué cambió>"` | «Guardé la versión "Segunda vuelta con datos del INDEC", 3 archivos.» |
| «¿Qué cambié desde ayer?» | `git diff --word-diff` contra la versión elegida | Lista de párrafos cambiados, con lo agregado y lo quitado. |
| «Mostrame las versiones» | `git log --date=format:'%d/%m %H:%M' --pretty='%ad · %s'` | Lista con fecha y descripción, la más nueva arriba. |
| «Volvé a la versión de las 10» | Recuperar en una **copia nueva**: `git show <versión>:nota.md > nota-version-10hs.md` | «Te dejé la versión de las 10 como nota-version-10hs.md; la actual sigue intacta.» |
| «Deshacé lo último que guardé» | `git revert --no-edit <versión>` (agrega una versión que deshace) | «Deshice esa versión; el historial conserva las dos por si querés volver.» |
| «Marcá la que mandé a edición» | `git tag -a enviado-edicion-AAAAMMDD -m "..."` | «Quedó marcada como la versión enviada a edición.» |
| «Probemos otro enfoque sin perder este» | `git switch -c enfoque-alternativo` | «Abrí un borrador alternativo; el original queda guardado.» |

## Primer uso en una carpeta

1. Comprobar que git existe (`git --version`). Si falta, explicar la instalación oficial (git-scm.com) y esperar autorización.
2. Inicializar **sólo la carpeta de trabajo del periodista** (`git init`), nunca su carpeta de usuario, Documentos completo ni una carpeta de sistema. Si ya es un repositorio, usarlo tal como está.
3. Identidad: si `git config user.name` está vacío, preguntar cómo quiere firmar las versiones y guardarlo **sólo en ese repositorio** (`git config user.name`, sin `--global`). No inventar un email: pedirlo o usar uno local explícito como `periodista@localhost`, avisando.
4. Crear `.gitignore` antes de la primera versión, mostrando qué se excluye:

```
# Pesados o sensibles: no van al historial
*.wav
*.mp3
*.m4a
*.mp4
*.mov
models/
tessdata/
.venv/
*.bin
```

5. Preguntar si los **originales** (documentos de fuentes, grabaciones) deben entrar al historial. Por defecto, no: el historial se copia entero si alguna vez se comparte. El kit ya preserva los originales por su cuenta.

## Buenas prácticas que aplica el agente

- Proponer guardar una versión en momentos naturales: antes de una reescritura grande, al terminar de chequear, antes de enviar a edición. No llenar el historial de versiones sin sentido.
- Mensajes de versión en castellano y descriptivos: «Agrega datos de pobreza del segundo semestre», no «cambios».
- Mostrar qué archivos entran antes de guardar (`git status`). Nunca `git add` de archivos con contraseñas, tokens, `.env` ni perfiles con datos sensibles.
- Para comparar prosa, usar `--word-diff`: el diff por línea es ilegible en párrafos largos.
- Los `.docx` no se comparan bien en git. Si el periodista trabaja en Word, ofrecer mantener una copia en `.md` o `.txt` para el historial, o comparar con la herramienta de Word.

## Lo que el agente nunca hace sin una confirmación explícita y específica

- **Nada que borre trabajo:** `git reset --hard`, `git checkout -- .`, `git restore` sobre cambios sin guardar, `git clean`, borrar ramas o etiquetas. Si hay cambios sin guardar y hay que moverse de versión, primero guardarlos o hacer `git stash` y avisar.
- **Nada que reescriba la historia:** `rebase`, `commit --amend` sobre versiones ya compartidas, `push --force`.
- **Nada que salga de la computadora:** `git push`, crear repositorios en GitHub/GitLab, agregar remotos o compartir enlaces. Compartir requiere saber **qué** se sube (todo el historial, no sólo la última versión), **a dónde** y **quién** lo va a ver.
- Nunca pegar tokens ni contraseñas en la conversación ni en la configuración. Si hace falta autenticarse en GitHub, el periodista lo hace con `gh auth login` o desde el navegador, por su cuenta.

## Compartir con edición (cuando lo autoriza)

1. Confirmar destino (repositorio privado del equipo, cuenta y visibilidad) y revisar con `git log --stat` que el historial no tenga material que no debe salir.
2. Si apareció algo sensible en una versión vieja, **frenar**: borrar el archivo hoy no lo saca del historial. Explicarlo y proponer compartir una copia limpia en un repositorio nuevo.
3. Subir y devolver el enlace. No dar permisos a terceros ni hacer público un repositorio.

## Entrega típica

```
Guardé la versión "Chequeo terminado: 14 afirmaciones, 2 a corregir".
Cambios desde la versión anterior: 3 párrafos (bajada, párrafo 4, cierre).
Versiones de hoy: 10:12 Primer borrador · 12:40 Con datos INDEC · 15:05 Chequeo terminado.
Nada se subió a Internet.
```
