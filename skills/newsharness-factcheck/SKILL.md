---
name: newsharness-factcheck
description: Verificar afirmaciones de una nota, borrador, discurso o publicación con inventario completo, evidencia actual y un informe trazable por afirmación; usar para chequeo previo a publicar, "¿esto es cierto?", "chequeá las cifras" o "revisá esta nota antes de que salga".
---
# Chequeo editorial, afirmación por afirmación

> **Reglas comunes y ubicación del kit.** Antes de actuar, leer `AGENTS.md` del kit: en el kit fuente está en la raíz; instalado en un proyecto, en `.newsharness-kit/AGENTS.md`; instalado de forma global, en `~/.newsharness-kit/AGENTS.md` (Windows: `%USERPROFILE%\.newsharness-kit\AGENTS.md`). Los comandos `python3 scripts/newsharness.py` de esta skill se ejecutan desde esa misma ubicación del kit.

## Cuándo usarla y en qué modo

- **Completo (por defecto):** pieza entera, tres pasadas, informe con todas las afirmaciones.
- **Urgente:** si el periodista lo pide explícitamente por tiempo, chequear primero título, bajada, cifras y atribuciones centrales, y declarar en el informe que el resto quedó `not_researched`. Nunca presentar un chequeo urgente como completo.
- **Derivar:** declaraciones de una persona con inventario y selección humana → `newsharness-discursos`; cálculos sobre tablas → `newsharness-datos` + `newsharness-python`; cifra oficial del INDEC → `newsharness-indec`.
- **Argentina:** usar [fuentes-ar.md](references/fuentes-ar.md): rutas oficiales verificadas. Una compilación de un medio o consultora sirve para orientarse, pero es fuente secundaria: verificar y citar el organismo de origen.

Adaptación propia inspirada en el método [Big If True de Verso](https://github.com/Verso-Lab/big-if-true-plugin), revisado el 1 de noviembre de 2026. No incorpora sus scripts ni ejecuta su plugin. Ver [metodo-y-alcance.md](references/metodo-y-alcance.md).

## Antes de buscar

Preservar una copia exacta del texto con título, bajada, cuerpo, epígrafes propios y fecha de publicación o fecha prevista. Excluir publicidad, navegación y otras notas. Declarar qué se recibió realmente: texto completo, fragmento, resumen, OCR o acceso parcial. **Un resumen no permite afirmar que se revisó la pieza completa.** Si falta contenido, pedirlo o entregar una revisión parcial explícita; no inventar el corpus.

Clasificar confidencialidad antes de enviar consultas. No pegar un borrador inédito, una cita exclusiva identificante ni datos de una fuente protegida en un buscador. Usar consultas generales o pedir permiso con destino y datos concretos. No archivar públicamente páginas ni enviar URLs a Wayback sin autorización explícita.

Sin acceso a búsqueda fresca, hacer sólo inventario y controles internos; marcar las afirmaciones externas como no resueltas/no investigadas. No emitir veredictos externos desde memoria ni llamar «verificado» a un cotejo interno.

## Tres pasadas separadas

### 1. Inventario literal y atómico

Leer [extraccion.md](references/extraccion.md). Extraer cada hecho comprobable con ID, ubicación y un tramo **literal** del original, conservando matices. Separar cantidad, fecha, comparación, atribución y causalidad cuando admitan respuestas distintas. No resumir una oración compuesta como una sola afirmación cómoda.

Si existe delegación segura, pedir a un extractor sólo el inventario, sin mostrar resultados de verificación. Si no, hacer una pasada independiente antes de buscar. Reconciliar títulos, bajada, cuerpo, tablas y epígrafes; no usar una densidad fija como prueba de exhaustividad. Indicar número de afirmaciones y alcance.

### 2. Verificación con evidencia actual de la consulta

Empezar por la fuente nombrada, acceder al documento completo y registrar URL/ubicación y fechas. Si falla una descarga, probar un acceso autorizado disponible —navegador, publicación oficial equivalente o archivo aportado—, sin saltar paywalls ni controles. Una página que no se pudo leer no es evidencia.

Preferir registros primarios pertinentes y fuentes independientes. Un emisor interesado puede acreditar sus palabras, pero no probar por sí solo sus acusaciones ni causalidades. No tratar a una fuente oficial como infalible. Cinco republicaciones de la misma agencia cuentan como **un origen**, no cinco confirmaciones.

Recalcular totales, porcentajes, diferencias, tasas y récords; revisar unidades, base, denominador, cobertura, moneda, precios corrientes/constantes, redondeos y revisiones. Usar la fecha de publicación como corte: separar lo conocido entonces de lo publicado después. Para rutas regionales leer [fuentes-latam.md](references/fuentes-latam.md) y la configuración del país; no inventar una API para completar el flujo.

### 3. Informe y cierre de cobertura

Usar [informe.md](references/informe.md). Cada ID debe tener estado, motivo y evidencia o faltante. Presentar primero problemas, luego pendientes, luego respaldos. Reconciliar total de inventario = respaldadas + requieren revisión + no resueltas. Si quedó trabajo sin investigar, declararlo; un límite de tiempo no lo transforma en resultado.

## Estados

- **Respaldada / `supported`:** evidencia suficiente sostiene todas las partes relevantes. Usar dos fuentes verdaderamente independientes, o un registro primario decisivo **para esa afirmación concreta**. No confundir esto con certeza universal.
- **Requiere revisión / `needs_review`:** evidencia muestra un error material, contradicción o encuadre engañoso. Explicar qué cambia y con qué respaldo. Una búsqueda sin resultados no alcanza para acusar al texto.
- **No resuelta / `could_not_verify`:** evidencia insuficiente o incompatible. Subtipo obligatorio: `not_researched` (no investigada), `reporter_material` (requiere material del reportero), `inaccessible` (fuente inaccesible) o `inconclusive` (investigada pero no concluyente). No equivale a falsa.

Sólo usar una ausencia como evidencia negativa si el corpus es completo para esa afirmación, el registro debería contenerla y se revisó íntegramente. Documentar por qué: una transcripción parcial o un buscador vacío no cumplen ese criterio.

## Entrega y límites

No reescribir el original en secreto. Entregar cambios sugeridos vinculados a IDs y dudas precisas para el editor o reportero. Indicar restricciones de acceso y comprobaciones pendientes. El informe no certifica publicabilidad legal ni autoriza publicación, contacto con fuentes o comentarios en un CMS.

## Resumen para el periodista (además del informe)

```
Revisé <N> afirmaciones de <título> (<texto completo / fragmento>).
⚠ Requieren corrección: <n> — <ID: qué cambiar, con qué fuente>
? Sin resolver: <n> — <ID: qué falta y quién puede aportarlo>
✓ Respaldadas: <n>
No se consultó: <fuentes inaccesibles o fuera de alcance>
Nada se publicó ni se envió a terceros.
```

## Errores frecuentes al chequear

- Dar por verificada una cifra porque aparece en otros medios (probablemente copian la misma fuente).
- Comparar con el dato de hoy una declaración de hace meses, o ignorar una revisión posterior.
- Confundir «no encontré» con «es falso».
- Verificar el número pero no la comparación («el más alto desde…» exige revisar toda la serie).
- Aceptar el comunicado oficial como prueba del hecho que el propio emisor afirma.
