# Perú · rutas documentales

Consulta: **2026-11-01**. El paquete se selecciona por jurisdicción del hecho, no sólo por país del periodista. Se revisaron páginas y documentación; **no se ejecutaron APIs, consultas autenticadas, compras ni exportaciones masivas**.

| Necesidad | Fuente oficial | Acceso y límites |
|---|---|---|
| Población, economía, precios y encuestas | [INEI: índices de precios](https://www.inei.gob.pe/estadisticas/indice-tematico/price-indexes/) y [Microdatos](https://proyectos.inei.gob.pe/microdatos/) | Directorios públicos legibles. [Guía oficial de bases](https://www.gob.pe/institucion/inei/pages/14307-consultar-bases-de-datos-del-inei) describe descargas y documentación; descargas no completadas en esta revisión. Comprobar condiciones de cada conjunto. |
| Moneda, tipos de cambio y series económicas | [BCRPData](https://estadisticas.bcrp.gob.pe/estadisticas/series/index) y [documentación API](https://estadisticas.bcrp.gob.pe/estadisticas/series/documentos/bcrpdataapi.pdf) | Existe documentación oficial de consultas por URL. El acceso directo mostró un control automatizado; no hay conector probado. Registrar código de serie, unidad, frecuencia y fecha; no inventar una ruta ante el bloqueo. |
| Resultados y decisiones electorales | [Resultados ONPE](https://resultadoelectoral.onpe.gob.pe/) y [Plataforma Electoral JNE](https://plataformaelectoral.jne.gob.pe/) | Rutas públicas institucionales, pero ONPE devolvió 403 y JNE una aplicación dinámica al lector. Verificar acta, elección, territorio, estado y fecha. Diferenciar cómputo ONPE de proclamaciones y decisiones JNE. |
| Publicación de normas y actos | [El Peruano: buscador oficial](https://busquedas.elperuano.pe/) | Buscador y ediciones consultables sin sesión en esta revisión; PDF individual no probado. Conservar fecha, edición, identificador y texto íntegro. Publicación, entrada en vigor y versión consolidada son cosas distintas. |
| Jurisprudencia publicada | [Poder Judicial: jurisprudencia sistematizada](https://jurisprudencia.pj.gob.pe/jurisprudenciaweb/faces/page/inicio.xhtml) y [guía oficial](https://www.gob.pe/13973-consultar-jurisprudencia-nacional-sistematizada) | La guía describe búsqueda y descarga de resoluciones; servicio directo devolvió 403. No confundir jurisprudencia publicada con acceso general a expedientes. |
| Contrataciones | [OECE: directorio de buscadores públicos SEACE](https://www.gob.pe/institucion/oece/pages/7505-consultar-los-buscadores-publicos-del-sistema-electronico-de-contrataciones-del-estado-seace) | La guía señala que los buscadores públicos no necesitan certificado SEACE/usuario/contraseña. Búsquedas y exportaciones no probadas; parte del acceso automatizado falló. Usar identificador de proceso/contrato y RUC, no sólo nombre. |
| Personas jurídicas | [SUNARP: directorio](https://www.sunarp.gob.pe/dn-personas-juridicas.asp), [alcance oficial](https://www.gob.pe/26674-conocer-el-directorio-nacional-de-personas-juridicas) y [Conoce Aquí](https://conoce-aqui.sunarp.gob.pe/) | El directorio se describe gratuito, referencial y actualizado mensualmente. Conoce Aquí tiene sesión y condiciones propias; no implica certificación registral. No crear cuentas ni adquirir publicidad registral por defecto. |

## Criterios locales y restricciones

- El IPC **nacional** y el de **Lima Metropolitana** son series distintas. Separar variación mensual, acumulada y anual; no empalmar bases sin serie enlazada oficial. Identificar soles/PEN frente a dólares y la cotización usada.
- Provincia, departamento/región, distrito y circunscripción electoral no son equivalentes. Confirmar el nivel territorial.
- En contratos, distinguir convocatoria, adjudicación, contrato firmado y pago. La presencia de un proveedor en un proceso no prueba adjudicación ni incumplimiento.
- El [CEJ](https://cej.pj.gob.pe/cej/forms/busquedaform.html) informa restricciones de acceso a partes, pide nombre exacto y CAPTCHA y excluye búsquedas penales en ese servicio. **No presentarlo como búsqueda abierta irrestricta de expedientes ni intentar eludir su control.** Usar resoluciones publicadas o material autorizado.
- La disponibilidad técnica de una página puede cambiar. Guardar el límite observado; una respuesta 403/418 del lector no prueba caída pública ni ausencia de un registro.

Cada informe debe enlazar la tabla, acta o resolución específica y sus límites. Una portada de organismo por sí sola no respalda una afirmación.
