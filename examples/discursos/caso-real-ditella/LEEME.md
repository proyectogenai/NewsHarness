# Caso real aportado · Milei en la Universidad Torcuato Di Tella

**Demostración parcial y pendiente de selección editorial; no es un chequeo terminado.** El usuario aportó [este video](https://www.youtube.com/watch?v=6KxqkedLOO4). No es la entrevista Majul/Milei mencionada como caso propuesto en el documento de prompts.

## Qué se comprobó y qué no

- La [página oficial de Casa Rosada](https://www.casarosada.gob.ar/slider-principal/51415-discurso-del-presidente-javier-milei-en-la-universidad-torcuato-di-tella) fecha el discurso el **30 de octubre de 2026** e incorpora el mismo video.
- La interfaz de YouTube mostró publicación **31 de octubre de 2026**, canal **Oficina del Presidente (@OPRArg)** y duración **2:07:37**. Publicación no equivale a fecha del acto.
- El extracto literal breve cotejado en la transcripción oficial es: «casi cuatro puntos del PBI bajamos de impuestos».
- El panel de transcripción de YouTube sitúa el inicio de un segmento relevante en [43:36](https://www.youtube.com/watch?v=6KxqkedLOO4&t=2616s). **No se escuchó el audio ni se verificó un tiempo exacto de palabra.** Por eso el JSON conserva tiempos `null` y registra el enlace al segmento por separado.

Consulta de estas fuentes: 1 de noviembre de 2026. Ambas pertenecen al mismo emisor institucional: no representan dos corroboraciones independientes.

## Qué demuestra el módulo

`extracto-oficial.txt` conserva sólo esa cita, no el discurso completo. `inventario-fragmento.json` ancla los caracteres exactos, registra fuentes y propone dos hipótesis neutrales: base comparativa y unidad/denominador. La cobertura está marcada como **parcial**.

El próximo paso es que una persona elija si investigar la afirmación y confirme alcance y período. Después corresponde localizar la metodología, identificar medidas efectivas frente a estimaciones, verificar la unidad «puntos del PBI», contrastar datos pertinentes a la fecha del discurso y separar revisiones posteriores. No hay cifras de contraste precargadas ni un veredicto supuesto.

Desde la raíz del kit:

```sh
python3 scripts/validate_discourse.py --source examples/discursos/caso-real-ditella/extracto-oficial.txt --report examples/discursos/caso-real-ditella/inventario-fragmento.json --stage inventory
```

Un resultado estructural satisfactorio **no confirma la cifra**, ni prueba que la cita capture todo el contexto, ni autentica una aprobación humana. No exporta ni publica. La investigación completa y la escucha del pasaje original siguen pendientes.
