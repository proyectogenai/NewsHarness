# Informe de verificación

## Encabezado

Título; fecha del texto y del chequeo; responsable; versión/archivo revisado; alcance (completo/parcial); material faltante; confidencialidad y restricciones. En un ejercicio cerrado escribir «Cotejo contra expediente ficticio, no verificación del mundo real».

## Resumen

Total de afirmaciones inventariadas, cuántas se investigaron y distribución de estados. Separar «no investigadas» del resto de no resueltas. No inventar un porcentaje de confianza ni un sello de veracidad para toda la nota.

## Una ficha por ID

- **Cita literal / ubicación:** ancla recuperable en el original.
- **Qué se evalúa:** si la cita contiene más de una afirmación, indicar cuál.
- **Estado / subtipo:** vocabulario de la skill.
- **Hallazgo:** explicación corta, sin acusar por ausencia de resultados.
- **Evidencia:** documento, URL o archivo local, página/celda/timestamp, productor, fecha de publicación/actualización y consulta; fragmento pertinente y límite de acceso.
- **Independencia:** origen primario compartido, agencia, comunicado o reporte propio.
- **Cálculo:** entradas, fórmula, unidades y redondeo cuando corresponda.
- **Acción editorial:** corrección propuesta o documento/pregunta concreta que resolvería el pendiente. No sustituir evidencia por «consultar una fuente» genérico.

## Registro de acceso

Por cada acceso fallido: fuente, error observado, alternativa intentada, qué afirmaciones afecta y qué permitiría continuar. No registrar contraseñas, cookies ni URLs con tokens. Si una fuente se resolvió por otra evidencia, aclararlo; no mantener un bloqueo falso.

## Conciliación final

Todos los IDs están representados exactamente una vez como unidad de verificación; pueden compartir evidencia, no fusionarse para esconder pendientes. Las cifras del resumen suman. Los enlaces se abren o quedan marcados inaccesibles. Las correcciones conservan incertidumbre y no atribuyen al reportero verificaciones que hizo el agente.

Cerrar con: «Revisión asistida; la decisión editorial requiere evaluar la evidencia y resolver los pendientes. Método adaptado a partir de Big If True, de Verso». No presentar el kit como producto oficial ni avalado por Verso.

## Validación estructural opcional del kit

El agente puede guardar un JSON con `extracted_claim_ids` y una entrada por ID en `claims`. Ejemplo de una **sola afirmación de demostración**, no un informe completo de la nota del taller:

```json
{
  "extracted_claim_ids": ["c1"],
  "claims": [
    {
      "id": "c1",
      "quote": "Los viajes del sistema Faro crecieron un 50% en un año",
      "status": "needs_review",
      "rationale": "En el expediente ficticio, Norte y Sur pasan de 1.500 a 1.800 viajes: el aumento es 20%, no 50%. No hay cobertura completa para todo el sistema.",
      "sources": [
        {
          "file": "examples/demo-publica/datos.csv",
          "locator": "r001, r002, r003 y r004; deduplicación según diccionario-datos.md",
          "evidence": "(1.800 - 1.500) / 1.500 * 100 = 20%; Oeste tiene datos faltantes."
        }
      ]
    }
  ]
}
```

Los tres `status` son `supported`, `needs_review`, `could_not_verify`. Para el último agregar `unresolved_reason`: `not_researched`, `reporter_material`, `inaccessible` o `inconclusive`. En cada fuente usar **o** `url` HTTP(S) sin secretos **o** `file` relativo dentro del proyecto con `locator`; siempre incluir `evidence` concreta. No fabricar enlaces para un expediente local.

Desde el kit fuente:

```bash
python3 scripts/validate_report.py --source ORIGINAL --report INFORME_JSON
```

Desde un proyecto instalado, usar `python3 .newsharness-kit/scripts/validate_report.py` con los mismos argumentos. La comprobación valida estructura, coincidencia literal y conciliación de IDs; **no demuestra verdad, independencia, existencia/acceso de la fuente ni que el extractor encontró todas las afirmaciones**. El inventario sigue requiriendo revisión editorial contra el original. No interpretar `ok: true` como «nota lista para publicar».
