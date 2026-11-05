# Consultas a la API INDEC · sintaxis y recetas

`I` = `python3 scripts/indec_api.py`, ejecutado desde la ubicación del kit. Los valores entre `<…>` salen del paso `valores`: **no completarlos de memoria**, porque `eq.` compara el texto literal. Adaptado de las recetas de [indec-api-skill](https://github.com/jonymusky/indec-api-skill) (MIT).

## Filtros (sintaxis PostgREST)

Cada filtro es `columna=operador.valor`. Varios filtros sobre columnas distintas se combinan con Y.

| Operador | Significado | Ejemplo |
|---|---|---|
| `eq` / `neq` | igual / distinto | `region=eq.<region>` |
| `gt` `gte` `lt` `lte` | comparaciones | `periodo=gte.202401` |
| `like` / `ilike` | patrón (con / sin distinguir mayúsculas); comodín `*` | `descripcion=ilike.*alimentos*` |
| `in` | en una lista; comillas dobles si el valor tiene comas o espacios | `pais_cod=in.(200,203)` |
| `is` | nulo, verdadero o falso | `valor=is.null` |
| `not.` | niega cualquier operador | `region=not.eq.<region>` |
| `or` / `and` | combinación explícita | `and=(periodo.gte.202401,periodo.lte.202412)` |

Opciones: `--select a,b` (columnas; alias `p:periodo`), `--order periodo.desc` (varias separadas por coma), `--limit`, `--offset`, `--todo` (pagina sola), `--salida archivo.csv|.json`.

## Errores frecuentes de la API

| Código | Causa |
|---|---|
| 400 `PGRST100` | filtro sin operador (`periodo=202401`) |
| 400 `42703` | columna inexistente, casi siempre por mayúsculas (la herramienta lo detecta antes) |
| 401 `42501` / `PGRST301` | sin token, token vencido o reemplazado por uno nuevo |
| 404 `PGRST205` | tabla inexistente (`canasta_crianza` → `canasta-crianza`) |
| 206 | no es un error: respuesta parcial con total en `Content-Range` |

## Inflación mensual

```bash
I consultar ipc_nacional --select periodo --order periodo.desc --limit 1          # último período
I valores ipc_nacional region,clasificador,nivel periodo=eq.<ultimo_periodo>
I valores ipc_nacional tipo_de_indicador,tipo_de_indicador_descripcion periodo=eq.<ultimo_periodo>
I consultar ipc_nacional region=eq.<region> nivel=eq.<nivel_general> tipo_de_indicador=eq.<variacion_mensual> \
  periodo=gte.202401 --select periodo,descripcion,valor,observaciones --order periodo --todo \
  --salida ESPACIO/datos/originales/ipc-mensual.csv
```

Por región o división: mismos pasos, cambiando `region` o filtrando `descripcion` con el texto listado.

## Inflación acumulada

Usar el `tipo_de_indicador` de variación acumulada o interanual si la tabla lo trae. Si hay que calcularla, encadenar las mensuales: `(1 + v1/100) × (1 + v2/100) × … − 1`. **Nunca sumar porcentajes.** El cálculo va en un script de `newsharness-python` y se compara con el informe técnico.

## Ajustar un monto por inflación

1. Traer el **índice** (no la variación) del IPC nivel general para el período de origen y el de destino.
2. `monto_ajustado = monto × índice_destino / índice_origen`.
3. Si el período destino no está publicado, decirlo; no extrapolar sin avisar.

## Canasta básica (líneas de pobreza e indigencia)

```bash
I valores valorizacion_canastas_cba_cbt descripcion,tipo_de_indicador,unidad_de_medida,region
I ultimos valorizacion_canastas_cba_cbt --periodos 2
```

Mirar `unidad_de_medida`: por adulto equivalente o por hogar tipo. Para un hogar concreto se multiplica el valor por adulto equivalente por la suma de unidades de sus integrantes (tabla de equivalencias de la metodología del INDEC).

## Pobreza e indigencia (semestral, tabla ancha)

```bash
I valores pobreza_eph area_geografica_nom
I ultimos pobreza_eph --periodos 4
I consultar pobreza_eph --select periodo,area_geografica_nom,tasa_pobreza_personas,tasa_indigencia_personas,observaciones \
  --order periodo.desc --limit 8
```

Es sobre los aglomerados urbanos de la EPH, no sobre todo el país: decirlo en la nota.

## Mercado de trabajo (trimestral, tabla ancha)

```bash
I ultimos mercado_trabajo_eph --periodos 4 \
  --select periodo,area_geografica_nom,tasa_de_actividad,tasa_de_empleo,tasa_de_desocupacion,tasa_de_empleo_informal
```

## Actividad económica (EMAE)

```bash
I valores estimador-mensual-de-actividad-economica-nivel-general tipo_de_indicador,tipo_de_indicador_descripcion
I consultar estimador-mensual-de-actividad-economica-nivel-general tipo_de_indicador_descripcion=eq.<serie_desestacionalizada> \
  --order periodo.desc --limit 24
I valores estimador-mensual-de-actividad-economica-sectores codigo,descripcion
```

Comparar meses consecutivos con la serie desestacionalizada; contra el mismo mes del año anterior, con la original.

## Exportaciones o importaciones por país

```bash
I valores comercio_exterior_nomenclaturas nombre_columna
I consultar comercio_exterior_nomenclaturas nombre_columna=eq.pais_cod codigo_descripcion=ilike.*brasil*
I consultar comercio_exterior_exportacion_bienes Anio=eq.2025 pais_cod=eq.<codigo> --todo --etiquetas \
  --salida ESPACIO/datos/originales/expo-<pais>-2025.csv
```

`valor_FOB` en dólares, `Peso_Neto` en kilos. Muchas celdas por país y subrubro vienen nulas con `s`: el total que se suma es un **piso** y hay que decirlo. Si la investigación es sensible, bajar el año completo sin filtrar el país y filtrar en el equipo.

## Población

```bash
I consultar proyecciones_poblacion_nacional_2022_2040 fecha=eq.2026 --select edad,sexo_nom,poblacion --todo
I valores proyecciones_poblacion_jurisdiccion_2022_2040 jurisdiccion_cod,jurisdiccion_nom
I consultar estimaciones_poblacion_departamento_2022_2035 jurisdiccion_cod=eq.<codigo> fecha=eq.2025 --todo
```

Son proyecciones y estimaciones, no conteos censales: decirlo cuando se usan como denominador.

## Tabla entera a disco

```bash
I contar ipc_nacional
I consultar ipc_nacional periodo=gte.202001 --todo --salida ESPACIO/datos/originales/ipc-2020-en-adelante.csv
```

Cada página son 1000 filas y una consulta. Con más de 200.000 filas la herramienta se detiene: filtrar por período o región.
