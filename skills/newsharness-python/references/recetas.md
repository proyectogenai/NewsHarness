# Recetas de Python para análisis periodístico

Fragmentos para el agente. Adaptarlos al archivo real; no copiarlos sin revisar columnas, unidades y formato. Requieren `pandas` salvo donde se indica «estándar».

## Plantilla

```python
"""
Pregunta: ¿Cuánto subió la canasta básica total en el último año?
Fuente: INDEC, Valorización mensual de la CBA y CBT, descargado 2026-11-03
Entradas: datos/originales/cbt.csv
Salidas:  salidas/cbt-interanual.csv
"""
from pathlib import Path
import pandas as pd

ORIGEN = Path("datos/originales/cbt.csv")
SALIDA = Path("salidas/cbt-interanual.csv")
assert not SALIDA.exists(), f"{SALIDA} ya existe: elegir otro nombre"

df = pd.read_csv(ORIGEN, parse_dates=["fecha"])

# Controles: frenar si algo no es lo esperado
assert df["fecha"].is_unique, "fechas duplicadas"
assert df["valor"].notna().all(), "hay valores faltantes"
print("filas:", len(df), "desde", df["fecha"].min().date(), "hasta", df["fecha"].max().date())

df = df.sort_values("fecha").set_index("fecha")
df["var_interanual_%"] = df["valor"].pct_change(12) * 100   # mensual: 12 períodos

SALIDA.parent.mkdir(parents=True, exist_ok=True)
df.tail(13).to_csv(SALIDA)
print(df.tail(3).round(1))
```

## Leer archivos con formato argentino

```python
# CSV con ; y coma decimal (muchos portales oficiales)
df = pd.read_csv(ruta, sep=";", decimal=",", thousands=".", encoding="utf-8")
# Si da error de codificación, probar encoding="latin-1" y verificar tildes en una fila conocida.

# Excel: indicar hoja y filas de encabezado; revisar notas al pie al final
df = pd.read_excel(ruta, sheet_name="Cuadro 1", skiprows=3, nrows=40)
```

## Variaciones (estándar o pandas)

```python
variacion_pct = (nuevo - anterior) / anterior * 100     # anterior != 0
diferencia_pp = tasa_nueva - tasa_anterior              # puntos porcentuales, no %
df["var_mensual_%"]    = df["valor"].pct_change(1) * 100
df["var_interanual_%"] = df["valor"].pct_change(12) * 100   # serie mensual
```

## Inflación acumulada e interanual desde tasas mensuales

```python
m = ipc.set_index("fecha")["valor"] / 100                      # 1,9 % -> 0.019
acum_2026 = ((1 + m["2026"]).prod() - 1) * 100                 # acumulada en el año
interanual = ((1 + m).rolling(12).apply(lambda x: x.prod()) - 1) * 100
```

Comprobar contra el informe del INDEC: el redondeo de las tasas mensuales puede dar una décima de diferencia. Si difiere, citar la cifra publicada por el INDEC y explicar.

## Deflactar (pesos de distintos meses a pesos de un mes base)

```python
# nivel = índice de precios (no la variación). Base: último mes disponible
nivel = (1 + m).cumprod()
factor = nivel.iloc[-1] / nivel
df["valor_real"] = df["valor_nominal"] * factor.reindex(df.index)
```

Decir siempre «a precios de <mes año>» y qué índice se usó.

## Tasas agregadas sin promediar porcentajes

```python
g = df.groupby("provincia")[["desocupados", "activos"]].sum()
g["tasa_%"] = g["desocupados"] / g["activos"] * 100           # correcto
# df.groupby("provincia")["tasa"].mean()  -> incorrecto si los grupos tienen distinto tamaño
```

## Cruzar tablas sin perder filas en silencio

```python
cruce = a.merge(b, on="cuit", how="left", validate="many_to_one", indicator=True)
print(cruce["_merge"].value_counts())    # cuántas no encontraron pareja
sin_pareja = cruce[cruce["_merge"] == "left_only"]
```

Normalizar claves antes (espacios, mayúsculas, guiones del CUIT, tildes) y contar cuántas cambió esa normalización.

## Rankings

```python
top = df.sort_values("monto", ascending=False).head(10)
top["puesto"] = top["monto"].rank(method="min", ascending=False).astype(int)  # empates comparten puesto
```

## APIs oficiales argentinas (sin token)

```python
import json, urllib.request
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "NewsHarness-Kit"}), timeout=30) as r:
        return json.load(r)

# BCRA v4.0: reservas internacionales (id 1). Listado de ids: .../estadisticas/v4.0/monetarias
res = get("https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/1?desde=2026-01-01&hasta=2026-10-31")
reservas = pd.DataFrame(res["results"][0]["detalle"])

# Series de Tiempo (datos.gob.ar): buscar el id y después pedir la serie
busq = get("https://apis.datos.gob.ar/series/api/search/?q=ipc%20nivel%20general&limit=5")
serie = get("https://apis.datos.gob.ar/series/api/series/?ids=148.3_INIVELNAL_DICI_M_26&format=json&limit=5000")
```

Guardar la respuesta cruda en `datos/originales/` con fecha de descarga antes de procesarla.

## Gráfico con fuente

```python
import matplotlib
matplotlib.use("Agg")                     # sin ventana: sólo archivo
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(serie.index, serie.values)
ax.set_title("Inflación mensual, enero 2025 – septiembre 2026")
ax.set_ylabel("Variación mensual (%)")
fig.text(0.01, 0.01, "Fuente: INDEC. Elaboración propia.", fontsize=8)
fig.tight_layout(); fig.savefig("salidas/ipc-mensual.png", dpi=150)
```

## Exportar a Excel sin fórmulas inyectadas

```python
def seguro(v):
    return "'" + v if isinstance(v, str) and v[:1] in ("=", "+", "-", "@") else v
df.map(seguro).to_excel("salidas/tabla.xlsx", index=False)    # pandas >= 2.1; antes: applymap
```
