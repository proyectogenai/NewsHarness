---
name: newsharness-redaccion
description: Redactar, editar, acortar o adaptar piezas periodísticas (nota, explicador, entrevista, newsletter, títulos, redes) con el perfil confirmado y material trazable, sin inventar hechos ni citas; usar cuando pidan "escribí la nota", "editá esto", "dame títulos", "pasalo a newsletter" o "acortalo a 3.000 caracteres".
---
# Redacción con evidencia y voz propia

> **Reglas comunes y ubicación del kit.** Antes de actuar, leer `AGENTS.md` del kit: en el kit fuente está en la raíz; instalado en un proyecto, en `.newsharness-kit/AGENTS.md`; instalado de forma global, en `~/.newsharness-kit/AGENTS.md` (Windows: `%USERPROFILE%\.newsharness-kit\AGENTS.md`). Los comandos `python3 scripts/newsharness.py` de esta skill se ejecutan desde esa misma ubicación del kit.

## Cuándo usarla

- **Sí:** primer borrador con material reunido, edición o corrección, cambio de formato, títulos y bajadas, versiones para redes o newsletter.
- **Derivar:** cifras o afirmaciones dudosas → `newsharness-factcheck`; tablas → `newsharness-datos`; declaraciones de una persona → `newsharness-discursos`; audio → `newsharness-transcripcion`.
- **Formatos y checklists:** [formatos.md](references/formatos.md).

## Flujo rápido

1. Confirmar formato, extensión, audiencia y ángulo (sólo lo que falta).
2. Inventario de hechos, citas y huecos con su fuente.
3. Borrador que respeta el perfil, separado de las notas al editor.
4. Pasada de coherencia (título ↔ cuerpo, cifras, nombres, citas, fechas).
5. Entrega con pendientes visibles y lista de cambios si fue edición.

## Preparar el encargo

Confirmar sólo lo que falta: audiencia, formato, extensión aproximada, ángulo y entrega. Cargar perfil aprobado; distinguir regla oficial, patrón inferido y preferencia. Sin perfil, usar español claro y un formato explícito, no imitar de memoria a un medio.

Leer el material efectivamente disponible. Hacer un inventario breve de hechos, citas y huecos relevantes, con fuente o ubicación. Si falta una pieza indispensable para sostener el ángulo, pedirla o proponer un ángulo respaldado. No convertir un comunicado en una investigación propia ni atribuir al periodista entrevistas que no realizó.

## Escribir

- Priorizar qué pasó, a quién afecta y qué está probado. Diferenciar hechos, contexto, interpretación, atribuciones y escenarios.
- Respetar denominaciones, fechas, cifras y unidades. Mantener «según», condicionales y límites cuando son parte de la evidencia.
- Las citas directas proceden de un texto o audio identificable; si no está comprobada la literalidad, usar paráfrasis atribuida o marcar pendiente. No «mejorar» una cita para que el entrevistado parezca más elocuente ni unir tramos como una frase continua.
- Aplicar estilo después de fijar los hechos. Una muestra de notas propias puede orientar estructura y ritmo, no justificar plagio, invención ni simplificación engañosa.
- Titulares, bajadas, redes y SEO no pueden prometer más de lo que sostiene el cuerpo. Evitar cifras sin denominador, superlativos sin universo y causalidades no demostradas.
- Si se solicita otro formato, conservar el mismo grado de certeza y atribución. La brevedad no autoriza quitar una salvedad esencial.

## Revisar y entregar

Hacer una pasada de coherencia entre título/cuerpo, nombres, cifras, citas y cronología. Cuando el encargo requiere verificación, usar `newsharness-factcheck`; una corrección gramatical no es un fact-check.

Entregar el borrador separado de notas al editor: fuentes usadas, decisiones relevantes y pendientes concretos. No dejar marcadores ambiguos que puedan publicarse por accidente; los pendientes deben estar visiblemente fuera del texto final o señalados como «NO PUBLICAR SIN RESOLVER».

Para edición, preservar una versión de origen y mostrar cambios sustantivos o una lista de qué se modificó. Si el usuario sólo pidió corrección, no cambiar enfoque, conclusiones ni estilo sin necesidad. No publicar, enviar al CMS ni escribir en documentos ajenos sin autorización específica.

## Plantilla de entrega

```
## Borrador
<texto listo para revisión, sin marcas ocultas>

## Notas al editor (no publicar)
- Fuentes usadas: <documento/entrevista, con ubicación>
- Decisiones: <ángulo elegido y por qué>
- Pendientes: <dato o cita sin confirmar> — NO PUBLICAR SIN RESOLVER
- Cambios respecto del original (si fue edición): <lista breve>
```

## Errores que delatan un texto armado por máquina

- Frases de relleno («en un contexto de…», «cabe destacar», «en este sentido») y cierres con moraleja.
- Adjetivos que juzgan sin respaldo («polémico», «histórico», «drástico»).
- Atribuciones vagas («según expertos», «fuentes indicaron») cuando el material tiene nombres o documentos.
- Cifras redondeadas que cambian el sentido («casi la mitad» por 41 %), o sin período ni unidad.
- Citas pulidas: una cita literal no se corrige; si hace falta, se parafrasea con atribución.
- Títulos que afirman lo que el cuerpo sólo sugiere.
