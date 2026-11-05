# Fuentes de Argentina

Consulta y pruebas de acceso: **2026-11-03**. Rutas comprobadas desde un equipo en Argentina, sin cuentas ni tokens. Son puntos de partida para abrir el documento o la serie concreta: ninguna ruta reemplaza leer la metodología, la fecha y la cobertura de lo que se cita. Si una ruta deja de responder, registrarlo y usar la alternativa; no eludir certificados vencidos, CAPTCHA ni muros de pago.

## Orden de preferencia para un dato

1. **Organismo productor del dato** (INDEC, BCRA, ministerio, Boletín Oficial): es lo que se cita.
2. **API o serie oficial que redistribuye ese dato** (BCRA API, Series de Tiempo de datos.gob.ar): sirve para bajar la serie completa; comprobar que coincide con la publicación vigente.
3. **Compilaciones de medios, consultoras o agregadores**: útiles para orientarse; son **fuente secundaria** y no se citan como origen de una cifra oficial.

## Estadística oficial

| Necesidad | Ruta | Cómo usarla |
|---|---|---|
| Precios, actividad, empleo, pobreza, comercio, cuentas nacionales | [INDEC](https://www.indec.gob.ar/) | Informe técnico del período + cuadros descargables. Citar el informe, no la portada. Revisar base, cobertura regional y revisiones. |
| Fechas de publicación | [Calendario INDEC](https://www.indec.gob.ar/indec/web/Calendario-Fecha-0) | Saber si ya salió el dato; el corte temporal del chequeo es la fecha de la declaración. |
| Series de tiempo oficiales por API | [Series de Tiempo · datos.gob.ar](https://apis.datos.gob.ar/series/api/series/?ids=148.3_INIVELNAL_DICI_M_26&last=3&format=json) | API pública sin token. Buscar IDs con `https://apis.datos.gob.ar/series/api/search/?q=desocupacion`. Puede **ir atrasada** respecto del INDEC (al 03/11 el IPC nivel llegaba a agosto y el INDEC ya había publicado septiembre): comparar con el informe vigente. |
| Catálogo INDEC por API | [API-INDEC](https://api.indec.gob.ar/) | 19 tablas oficiales (IPC, canastas, EPH, EMAE, IPI, salarios, comercio exterior, población). Requiere **token personal** que gestiona el periodista. Usar la skill `newsharness-indec` y `scripts/indec_api.py`, que valida columnas, pagina, cuenta signos convencionales (`s` = secreto estadístico) y guarda procedencia. Marcado beta. |
| CABA | [Estadística Ciudad](https://www.estadisticaciudad.gob.ar/) | IPC CABA y datos porteños; no mezclar con el IPC nacional. |
| Provincia de Buenos Aires | [Dirección Provincial de Estadística](https://www.estadistica.ec.gba.gov.ar/) | Datos provinciales con su propia metodología. |

## Banco Central (BCRA)

- Catálogo: [APIs del Banco Central](https://www.bcra.gob.ar/apis-banco-central/).
- **Variables monetarias, API v4.0:** `https://api.bcra.gob.ar/estadisticas/v4.0/monetarias` lista las variables (id, descripción, unidad, periodicidad, último valor). Serie: `…/monetarias/{id}?desde=AAAA-MM-DD&hasta=AAAA-MM-DD` (o `?limit=N`). Ejemplo comprobado: id 1 = reservas internacionales en millones de USD. **La v3.0 respondió 410 (dada de baja)**: no usar ejemplos viejos.
- **Cotizaciones de monedas:** `https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones` (día) y `…/Cotizaciones/USD?fechadesde=…&fechahasta=…`.
- Distinguir dólar mayorista (Comunicación A 3500), minorista promedio, MEP, CCL y blue. «El dólar» sin tipo ni fecha no es un dato.
- La Central de Deudores contiene datos de personas: **no consultarla** salvo encargo autorizado y con cuidado de datos personales.

## Normas y actos de gobierno

| Necesidad | Ruta | Cómo usarla |
|---|---|---|
| Normas publicadas hoy o en una fecha | [Boletín Oficial](https://www.boletinoficial.gob.ar/) · [Primera sección](https://www.boletinoficial.gob.ar/seccion/primera) | Primera sección: leyes, decretos, DNU, resoluciones. Segunda: sociedades. Tercera: contrataciones. Cada aviso tiene URL estable `/detalleAviso/primera/{id}/{AAAAMMDD}`; citar esa URL y la fecha de edición. La búsqueda avanzada redirigió a error en la prueba automática: buscar desde el navegador. |
| Texto actualizado y normas relacionadas | [Normativa · argentina.gob.ar](https://www.argentina.gob.ar/normativa) · [InfoLEG](https://servicios.infoleg.gob.ar/infolegInternet/) | Texto consolidado, modificatorias y derogaciones. Publicación no equivale a vigencia: leer artículos de entrada en vigor. |
| Presupuesto y ejecución | [Presupuesto Abierto](https://www.presupuestoabierto.gob.ar/sici/) | Crédito vigente vs devengado vs pagado: no son lo mismo. |
| Ministerio de Economía | economia.gob.ar | **Al 03/11/2026 su certificado HTTPS estaba vencido.** No forzar la conexión; buscar el documento en argentina.gob.ar o en el Boletín Oficial. |
| Mercado de capitales | [CNV](https://www.cnv.gov.ar/) | Hechos relevantes y sanciones de emisoras. |

## Justicia y elecciones

- [Cámara Nacional Electoral](https://www.electoral.gob.ar/nuevo/): resultados definitivos, padrones agregados y fallos electorales. Escrutinio provisorio ≠ definitivo.
- [Centro de Información Judicial](https://www.cij.gov.ar/): fallos de la Corte Suprema y del Poder Judicial. Leer el fallo, no la gacetilla.

## Errores frecuentes en notas argentinas

- **Inflación:** mensual, interanual y acumulada en el año son tres cifras distintas. Núcleo ≠ general. Mayorista ≠ minorista. Diferencia entre dos tasas = puntos porcentuales.
- **Comparaciones en pesos:** con inflación alta, una variación nominal no dice nada. Deflactar con IPC del mismo período y explicar la base.
- **Pobreza e indigencia:** semestrales, sobre personas u hogares, 31 aglomerados urbanos. No proyectarlas al país rural ni a un mes.
- **Canastas:** las comparaciones suelen usar el «Hogar 2» (tipo); hay otros hogares de referencia. Decir cuál.
- **Actividad:** EMAE y PBI se publican en serie original, desestacionalizada y tendencia-ciclo; la comparación mensual corresponde a la desestacionalizada.
- **Fiscal:** primario ≠ financiero (este incluye intereses). Base caja.
- **Riesgo país:** puntos básicos (100 pb = 1 punto porcentual de sobretasa).
- **Fechas:** una declaración de hoy se contrasta con el dato disponible hoy; si después hubo revisión, separarla (ver `newsharness-discursos`).
