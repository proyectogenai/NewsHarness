---
name: newsharness-indec
description: Consultar datos oficiales del INDEC por su API (api.indec.gob.ar) con procedencia y cita lista, para inflación/IPC, canasta básica (CBA/CBT), canasta de crianza, pobreza e indigencia, desocupación e informalidad (EPH), EMAE, IPI manufacturero y minero, salarios, construcción, precios mayoristas, población y exportaciones o importaciones por país; usar cuando pidan "bajá el dato del INDEC", "¿cuánto dio la pobreza?", "exportaciones a Brasil", "último IPC por región" o "canasta de crianza".
license: MIT (adaptación de indec-api-skill de Jony Musky; ver docs/TERCEROS.md)
---
# INDEC por API

> **Reglas comunes y ubicación del kit.** Antes de actuar, leer `AGENTS.md` del kit: en el kit fuente está en la raíz; instalado en un proyecto, en `.newsharness-kit/AGENTS.md`; instalado de forma global, en `~/.newsharness-kit/AGENTS.md` (Windows: `%USERPROFILE%\.newsharness-kit\AGENTS.md`). Los comandos `python3 scripts/indec_api.py` de esta skill se ejecutan desde esa misma ubicación del kit.

El Catálogo API-INDEC sirve los cuadros oficiales como tablas consultables. El agente arma y ejecuta las consultas; el periodista recibe el dato, el período, si es provisorio y la cita. Basada en [indec-api-skill](https://github.com/jonymusky/indec-api-skill) de Jony Musky (MIT), con controles de token, procedencia y salida propios de NewsHarness.

## Cuándo usarla y cuándo no

- **Sí:** traer una serie o un valor oficial del INDEC de las 19 tablas del [catálogo](references/tablas.md), con su período y signos convencionales.
- **Sin token:** usar [Series de Tiempo de datos.gob.ar](../newsharness-factcheck/references/fuentes-ar.md) (no pide registro, puede ir atrasada) o el informe técnico del INDEC.
- **Después:** cálculos y gráficos → `newsharness-python`; qué comparar y cómo decirlo → `newsharness-datos`; chequear una afirmación → `newsharness-factcheck`.
- **No:** el dato que no está en estas tablas (cuentas nacionales, balanza de pagos, censos completos): ir al cuadro o informe del INDEC.

## 0. Token: lo gestiona la persona, nunca el chat

La API exige un token personal. **El agente no crea la cuenta, no acepta términos por la persona y no pide el token en la conversación**: lo escrito en el chat llega al proveedor del agente.

Indicar a la persona, en este orden:

1. Registrarse en https://api.indec.gob.ar (correo → código → perfil → «generar token»). El token se muestra **una sola vez**; generar otro anula el anterior.
2. Guardarlo como variable de entorno `INDEC_TOKEN`, fuera del agente:
   - **Windows:** menú Inicio → «Editar las variables de entorno de esta cuenta» → Nueva → nombre `INDEC_TOKEN`, valor: pegar el token → Aceptar. No requiere administrador.
   - **macOS:** en la app Terminal (no en el chat del agente): `touch ~/.zshrc && open -e ~/.zshrc`, agregar la línea `export INDEC_TOKEN="pegar-aquí"` y guardar.
   - **Linux:** lo mismo en `~/.profile`.
3. Cerrar y volver a abrir el agente para que tome la variable.

Para comprobar, ejecutar `python3 scripts/indec_api.py contar pobreza_eph`: devuelve un número o explica qué falta. **Nunca** `echo $INDEC_TOKEN`, `env`, `printenv`, `set` ni `Get-ChildItem env:`. No guardar el token en `profile.json`, en un `.env` del proyecto, en scripts, informes ni commits. Si la persona lo pega en el chat, avisarle que ya salió del equipo y sugerir generar uno nuevo (anula el anterior).

**Reserva:** el INDEC registra qué consulta cada usuario. Para una investigación sensible (un país, un producto, un departamento puntual), bajar una tabla más amplia y filtrar en el equipo.

## 1. Elegir la tabla

| Pregunta | Tabla |
|---|---|
| Inflación, IPC por región o división | `ipc_nacional` |
| Línea de pobreza e indigencia (CBA, CBT) | `valorizacion_canastas_cba_cbt` |
| % de pobreza e indigencia (semestral) | `pobreza_eph` |
| Desocupación, actividad, informalidad (trimestral) | `mercado_trabajo_eph` |
| Actividad económica mensual | `estimador-mensual-de-actividad-economica-nivel-general`, `estimador-mensual-de-actividad-economica-sectores` |
| Industria y minería | `ipi_manufacturero`, `ipi_minero` |
| Salarios | `indice_salarios` |
| Construcción, mayoristas, obra pública | `icc_precios_construccion`, `sipm_precios_mayoristas`, `redeterminacion_precios_contratos_obras_publicas` |
| Costo de criar a un chico | `canasta-crianza` |
| Población | `proyecciones_poblacion_nacional_2022_2040`, `proyecciones_poblacion_jurisdiccion_2022_2040`, `estimaciones_poblacion_departamento_2022_2035` |
| Comercio exterior por país | `comercio_exterior_exportacion_bienes`, `comercio_exterior_importacion_bienes` + `comercio_exterior_nomenclaturas` |

`python3 scripts/indec_api.py tablas` y `columnas <tabla>` funcionan sin token, contra la spec incluida en el kit.

## 2. Descubrir los textos exactos antes de filtrar

Las tablas de índices son **largas**: una fila por región × clasificador × nivel × descripción × tipo de indicador × período, con un único `valor`. Cómo se escribe «Nacional» o «variación mensual» **no figura en la spec**. Nunca adivinarlo:

```bash
python3 scripts/indec_api.py valores ipc_nacional region,clasificador,nivel periodo=eq.<ultimo_periodo>
python3 scripts/indec_api.py valores ipc_nacional tipo_de_indicador,tipo_de_indicador_descripcion,unidad_de_medida periodo=eq.<ultimo_periodo>
```

`valores` recorre la tabla: acotarlo con un filtro de período. El último período sale de `consultar <tabla> --select periodo --order periodo.desc --limit 1`.

## 3. Consultar y guardar

```bash
python3 scripts/indec_api.py consultar <tabla> col=op.valor … --select a,b --order periodo.desc --limit 12
python3 scripts/indec_api.py ultimos <tabla> [filtros] --periodos 3
python3 scripts/indec_api.py consultar <tabla> [filtros] --todo --salida ESPACIO/datos/originales/<nombre>.csv
python3 scripts/indec_api.py contar <tabla> [filtros]
```

- La pantalla muestra una muestra corta; **la tabla completa va a `--salida`**, junto con `<nombre>.procedencia.json` (URL, SHA256 de las respuestas, fecha de consulta, filtros). Nunca sobrescribe.
- Comercio exterior: `--etiquetas` agrega el nombre de país, rubro o uso económico a cada código.
- El resultado trae `ultimo_periodo`, `observaciones` (signos convencionales contados) y `cita_sugerida`.
- Sintaxis de filtros y recetas por tema: [consultas.md](references/consultas.md).

## 4. Revisar antes de informar

- **Signos convencionales:** `valor` nulo con `s` es secreto estadístico, no cero; `*` provisorio, `**` preliminar, `e`/`i` estimado, `-` cero absoluto, `...` no disponible, `///` no corresponde. Una suma con celdas `s` es un **piso**.
- **Cifra de título:** cotejarla con el informe técnico del período en indec.gob.ar. Si difiere, manda el informe y se explica.
- **Variaciones publicadas:** si la tabla trae `tipo_de_indicador` de variación, usar la publicada; no recalcular dividiendo índices (el redondeo puede dar otra décima).
- **Período:** decir el último disponible y la fecha de consulta. Si el dato pedido todavía no salió, decirlo; no extrapolar.

## 5. Entregar

```
**Dato:** <cifra con unidad y período, en lenguaje de nota>
**Estado:** definitivo | provisorio | preliminar | estimado (según observaciones)
**Tabla:** <5–10 filas, si sirve>
**Cómo se obtuvo:** tabla <tabla>, filtros <…>; <cálculo, si lo hubo>
**Límites:** cobertura (región, aglomerados), revisiones, celdas en secreto estadístico
**Archivos:** ESPACIO/datos/originales/<nombre>.csv + .procedencia.json
**Cita:** INDEC, <nombre del cuadro o informe>, <período>.
```

## Trampas de la API

1. **Mayúsculas en columnas**: `Anio`, `Mes`, `Periodo` en comercio exterior; en `canasta-crianza`, `anio` pero `Mes` y `Periodo`; `valor_FOB`/`Peso_Neto` (exportaciones) frente a `valor_CIF`/`peso_neto` (importaciones); `codigo_CLaNAE_2004` (IPI manufacturero) frente a `codigo_ClaNAE_2010` (IPI minero). La herramienta avisa y sugiere el nombre correcto.
2. **Guiones o guiones bajos en el nombre**: `estimador-mensual-…` y `canasta-crianza` llevan guiones; el resto, guiones bajos.
3. **Tope de 1000 filas** por respuesta: `--todo` pagina por la clave primaria completa y avisa si faltan filas. Hay un límite de 200.000 filas por consulta (`--max-filas`): acotar antes de subirlo.
4. **Formato del período**: `AAAAMM` en mensuales. En `pobreza_eph` (semestre) y `mercado_trabajo_eph` (trimestre) mirar un valor real con `ultimos` antes de filtrar por rango, o filtrar por `anio` y `semestre`/`trimestre`. En población, `fecha` es el año.
5. **`valor` es texto en `indice_salarios`**: convertir antes de operar.
6. **Tablas anchas y largas**: EPH y `canasta-crianza` tienen una columna por tasa o tramo; las de índices, `valor` + dimensiones.
7. **Comercio exterior usa códigos**: traducirlos con `--etiquetas` o con `comercio_exterior_nomenclaturas`.
8. **Los ejemplos de uso de la spec oficial son autogenerados** (`anio=gt.100`): no copiarlos como consultas reales.
9. **La spec del kit tiene fecha** (`config/indec/openapi.json`). Si una tabla o columna nueva no valida, `comparar-spec` muestra los cambios publicados; `--sin-validar` sólo con ese motivo.

## Errores que el agente no debe cometer

- Pedir el token en el chat, mostrarlo o guardarlo en un archivo del proyecto.
- Inventar el texto de una región o un indicador en lugar de listarlo con `valores`.
- Sumar porcentajes para una inflación acumulada: se encadenan, ver [consultas.md](references/consultas.md#inflación-acumulada).
- Tratar una celda `s` como cero o como dato faltante sin avisar.
- Citar «la API» o «el script» como fuente: se cita el INDEC y el cuadro o informe.
