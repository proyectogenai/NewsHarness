# Catálogo de hipótesis de contraste

Estas preguntas organizan la investigación. **No son veredictos, señales de culpabilidad ni un detector de engaño.** Una afirmación puede no corresponder a ningún patrón; no forzar etiquetas. Para cada hipótesis elegida, documentar evidencia favorable, evidencia contraria, explicación alternativa y resultado pendiente o resuelto.

| ID | Hipótesis neutral | Qué comparar | Qué puede descartarla o limitarla |
|---|---|---|---|
| H01 | Base de comparación distinta | Fecha inicial, cobertura, fuente y criterio de elección | La base está declarada, es pertinente y produce una comparación válida; mostrar sensibilidad a otras bases sin llamar «inflada» a una por anticipado. |
| H02 | Series con ajustes diferentes | Original, desestacionalizada, tendencia-ciclo y sus notas metodológicas | Las series contestan preguntas distintas; usar una puede ser adecuado. No declarar que una «mide mal» sin examinar método, revisiones y propósito. |
| H03 | Total y denominador no equivalentes | Total, por habitante, por hogar, población de referencia, período | El emisor especificó correctamente el indicador o las diferencias no alteran la afirmación concreta. No sustituir total por per cápita sin explicarlo. |
| H04 | Períodos o estacionalidad no comparables | Mes, trimestre, año, promedio histórico y fecha de corte | Los períodos son equivalentes o se aplicó un ajuste pertinente y documentado. Informar por qué se eligió la ventana, sin presumir selección maliciosa. |
| H05 | Categorías, cobertura o definiciones distintas | Personas/puestos; empleo formal/informal; stock/flujo; bruto/neto; concepto legal/estadístico | Las definiciones coinciden o la declaración acota expresamente su alcance. Desagregar sin sumar categorías solapadas. |
| H06 | Cambio de composición o de canal | Partes, total, pesos, cobertura territorial y canales medidos | El cambio de composición puede explicar el total; comprobar magnitud y cobertura antes de aceptar o rechazar esa explicación. |
| H07 | Solapamiento o doble conteo | Componentes, pasivos, disponibilidad, moneda, unidad y fecha | Las partidas son independientes y el agregado responde a la definición declarada. Un monto nominal no demuestra disponibilidad inmediata. |
| H08 | Versión o disponibilidad temporal diferente | Fecha de emisión, publicación del dato, revisión y calendario | El dato más nuevo aún no existía o no era pertinente al período. Separar evaluación histórica de una actualización presente. |
| H09 | Ajuste construido por el emisor | Fórmula, insumos, supuestos, indicador sin ajustar y análisis de sensibilidad | El ajuste es reproducible, pertinente y transparente; no rechazarlo sólo por no ser oficial ni aceptarlo por venir de una autoridad. |
| H10 | Proyección expresada con certeza excesiva | Horizonte, escenario, supuestos, rango y metodología | El carácter condicional se conserva en el contexto. Analizar plausibilidad e incertidumbre; no declarar incumplido un resultado futuro. |
| H11 | Comparación internacional heterogénea | Métrica, precios, moneda, poder adquisitivo, población, período y revisión | Los datos son comparables o los ajustes están justificados. El puesto en un ranking depende del universo y de su fecha. |
| H12 | Atribución causal por evaluar | Mecanismo, secuencia temporal, factores alternativos y estrategia de identificación | Hay evidencia causal pertinente o sólo asociación. Resultados sectoriales diferentes pueden coexistir con múltiples causas; no usar una correlación aislada para resolver el mecanismo. |
| H13 | Afirmación sobre eventos o acusaciones | Qué evento concreto se afirma, definición, documentos, proceso y respuesta pertinente | Un registro puede ser incompleto o no cubrir el universo. Distinguir declaración, denuncia, investigación y hecho establecido; proteger personas y evitar repetir acusaciones innecesariamente. |

## Correspondencia con el JSON

H01–H13 son etiquetas de lectura de esta tabla, **no IDs admitidos en `patterns[].id`**. El validador usa familias estables:

| Tabla editorial | ID del esquema |
|---|---|
| H01, H04 | `comparative_base` |
| H02, H08 | `series_and_vintage` |
| H03, H09 | `denominator_and_units` |
| H05 (universo), H06 | `coverage` |
| H05 (definición), H13 | `definition` |
| H07 | `stocks_flows_overlap` |
| H10 | `forecast_vs_observed` |
| H11 | `international_comparability` |
| H12 | `causal_attribution` |

Explicar la hipótesis concreta en `hypothesis`, el contraste en `test` y una explicación alternativa en `alternative`. Las familias no establecen culpabilidad y una etiqueta editorial no obliga a marcar un patrón. Ver el [contrato del esquema](esquema.md).

## Añadir una hipótesis

Proponer un nombre descriptivo (no inventar un ID técnico no admitido), definición, condiciones de uso, qué evidencia la refutaría, fuentes y límites. Señalar si nació de una sola pieza. Solicitar revisión editorial antes de incorporarla como regla estable; no crear un perfil de intenciones o un catálogo de «excusas» de una persona.
