# Costa Rica · rutas documentales

Consulta: **2026-11-01**. Paquete de fuentes para afirmaciones sobre Costa Rica, independientemente del país del medio. La Nación de Costa Rica usa `nacion.com`; no confundirla con LA NACION de Argentina. Estas rutas no constituyen conectores API ni una prueba de acceso a todos los documentos.

| Necesidad | Fuente oficial | Acceso y límite comprobado |
|---|---|---|
| Población, precios, pobreza y empleo | [INEC](https://inec.cr/) y [catálogo de metadatos](https://sistemas.inec.cr/nada5.4/index.php/catalog/central) | Resultados y metodologías publicados. La portada devolvió 403 al acceso automatizado; no deducir paywall. Microdatos tienen condiciones distintas: algunos requieren registro; otros solicitud y aprobación. No crear cuentas automáticamente. |
| Moneda, tasas, cuentas nacionales y series | [BCCR: indicadores / SDDE](https://sdd.bccr.fi.cr/es/IndicadoresEconomicos/Inicio/) | Distinguir consulta pública de API. El [estándar oficial SDDE](https://gee.bccr.fi.cr/indicadoreseconomicos/Documentos/DocumentosMetodologiasNotasTecnicas/Estandar_API_SDDE.pdf) documenta registro y token Bearer. API no ejecutada; no generar ni guardar credenciales como parte rutinaria del perfil. |
| Resultados, padrón agregado y participación electoral | [TSE: estadísticas](https://www.tse.go.cr/estadisticas.html) | Índice público; algunos productos son interactivos. Conservar elección, ronda, fecha y territorio. No confundir transmisión provisional con cómputo/declaratoria. |
| Legislación y dictámenes de la Procuraduría | [SINALEVI](https://sinalevi.go.cr/) | Portal público actual; la antigua ruta pgrweb.go.cr/scij/main.aspx redirige aquí. [Alcance del sistema](https://sinalevi.go.cr/Escritorio/SCIJ). Un dictamen PGR no es una sentencia. Identificar tipo, número, versión y artículos. |
| Publicación oficial de normas y avisos | [La Gaceta / Imprenta Nacional](https://www.imprentanacional.go.cr/diarios_oficiales/index.aspx) | La [FAQ oficial](https://www.imprentanacional.go.cr/contactenos/preguntas_frecuentes.aspx) distingue lectura/descarga gratuita sin registro de trámites de publicación. Conservar edición, fecha, Alcance, página y PDF. Archivo antiguo en [Museo de Gacetas](https://museodegacetas.imprentanacional.go.cr/). |
| Jurisprudencia y boletines judiciales | [Nexus.PJ](https://nexuspj.poder-judicial.go.cr/) | Servicio de consulta de documentos publicados; portada dinámica. La [FAQ](https://nexuspj.poder-judicial.go.cr/PreguntasFrecuentes/PreguntasFrecuentesNexus.html) fue accesible. No equivale a acceso irrestricto a todos los expedientes; respetar anonimización y restricciones. |
| Contratación pública | [SICOP](https://www.sicop.go.cr/index.jsp) | Ruta confirmada por [COMEX y sus guías ciudadanas](https://www.comex.go.cr/transparencia/contrataci%C3%B3n-p%C3%BAblica/). El portal falló en el acceso de investigación; no se verificaron búsqueda, exportación ni barreras de sesión de punta a punta. Buscar el expediente autorizado, no inventar resultados. |
| Personas jurídicas y certificaciones | [Registro Nacional / RNP Digital](https://www.rnpdigital.com/shopping/login.jspx) | Existen registro y servicios de certificación pagados; no tratar todo el registro como abierto. [FAQ oficial](https://www.rnpdigital.com/tramites_servicios/Preguntas%20Frecuentes.htm). No crear cuenta, comprar ni descargar datos personales por defecto. |

## Criterios de interpretación

- Conservar la unidad: colones/CRC, dólares, porcentajes o millones. En cambio, indicar compra o venta y fecha; no usar una cotización indistinta.
- La ECE puede informar trimestres móviles: conservar los tres meses y el período comparable, además de incertidumbre estadística. Ver [ejemplo metodológico de INEC](https://admin.inec.cr/noticias/principales-indicadores-del-mercado-laboral-se-mantienen-sin-cambios-significativos).
- Identificar si se usa la [Estimación de Población y Vivienda 2022](https://admin.inec.cr/estimaciones-poblacion-vivienda-2022), una proyección u otra operación. No renombrar su naturaleza ni mezclar sus universos.
- Provincias, cantones, distritos, regiones de planificación y divisiones electorales no son equivalentes.
- En contratos, separar monto estimado, adjudicación, contrato, modificaciones y pago. En registros societarios, una representación legal no prueba por sí sola propiedad final.
- Para normas, revisar texto, modificaciones, fecha de efecto y jurisdicción. Una búsqueda sin nombres no prueba inexistencia de un proceso: puede haber anonimización o cobertura limitada.

## Si falla el acceso

Registrar el límite, probar publicaciones públicas o navegador autorizado, o solicitar el documento pertinente. No automatizar CAPTCHA, alta de cuentas, adquisición de certificados ni acceso reservado sin la autorización correspondiente. Cada hallazgo debe citar el registro específico, no sólo esta portada.
