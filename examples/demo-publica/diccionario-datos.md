# Diccionario ficticio · boletín del 5 de octubre de 2026

Este documento y los números del CSV son inventados para el taller.

- `registro_id`: clave única de un registro; la repetición idéntica de `r003` es un error de exportación confirmado en este diccionario. Conservar una sola copia en el conjunto limpio, dejar registro del descarte y mantener intacto el CSV original.
- `linea`: línea del sistema. Sólo Norte y Sur tienen cobertura comparable entre los dos períodos mostrados.
- `periodo`: mes de prestación del servicio, no fecha de carga.
- `viajes`: validaciones de viaje. Una misma persona puede generar varias; no se relevan personas distintas.
- `servicios_programados`: servicios incluidos en el indicador mensual de puntualidad.
- `servicios_puntuales`: de esos servicios, los que llegaron dentro del umbral definido por el boletín ficticio.
- Celda vacía: dato faltante, **no cero**. Oeste no informó datos del mes; tampoco tiene línea de base en 2025 en este expediente.
- Puntualidad agregada: suma de servicios puntuales dividida por suma de servicios programados; ambos períodos cubren Norte y Sur con el mismo criterio.

El archivo contiene sólo dos meses: no permite sostener un récord histórico, una tendencia continua ni el motivo causal de un cambio. No hay distribución de pasajeros únicos ni datos de adopción de la aplicación.
