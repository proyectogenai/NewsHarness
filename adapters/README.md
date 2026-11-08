# Adaptadores finos, un solo núcleo

`skills/` es la fuente canónica. El instalador copia los once packs completos, con referencias, a la ruta de descubrimiento del agente elegido. No se mantienen tres versiones distintas del método.

| Agente | Descubrimiento en el proyecto | Instalación global (`--global`) | Puente de instrucciones (sólo proyecto) |
|---|---|---|---|
| Codex | `.agents/skills/newsharness-*/SKILL.md` | `~/.codex/skills/` o `$CODEX_HOME/skills/` (experimental según versión) | `AGENTS.md` |
| Claude Code | `.claude/skills/newsharness-*/SKILL.md` | `~/.claude/skills/` | `CLAUDE.md` |
| OpenCode | `.opencode/skills/newsharness-*/SKILL.md` | `~/.config/opencode/skills/` | `AGENTS.md` |

En la instalación global el kit vive en `~/.newsharness-kit/` y **no se escribe ningún puente** en las instrucciones globales del usuario: cada skill indica dónde leer las reglas comunes.

Estos son adaptadores de instrucciones, no plugins ejecutables, barreras de seguridad ni garantía de las mismas herramientas. Verificar la versión instalada y sus permisos efectivos. En todos los casos el usuario puede pedir en lenguaje natural «prepará mi perfil», «revisá esta nota» o «transcribí este audio» o «analizá este discurso». El módulo `newsharness-discursos` usa el mismo esquema y validador local en los tres adaptadores.

Los archivos de este directorio son puentes breves para integrar al proyecto. No reemplazar un `AGENTS.md` o `CLAUDE.md` existente: añadir un bloque identificado sólo con permiso y después de revisar conflictos. Si no hay descubrimiento automático, cargar explícitamente el `SKILL.md` y sus referencias desde el núcleo; no concluir que toda la capacidad está averiada.
