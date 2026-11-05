# Perfil editorial v1

`profile.json` es una configuración local, no una memoria de secretos. Las claves canónicas están definidas por el validador del kit. Este ejemplo es ficticio; sustituirlo a partir de la conversación y evidencia, no copiarlo como perfil real.

```json
{
  "schema_version": 1,
  "newsroom": "Diario Ejemplo",
  "newsroom_url": "https://example.org",
  "journalist": {
    "name": "Andrea Ejemplo",
    "signature": "Andrea Ejemplo",
    "role": "Periodista",
    "section": "Ciudad",
    "formats": ["noticia", "explicador"]
  },
  "country": "AR",
  "language": "es",
  "timezone": "America/Argentina/Buenos_Aires",
  "privacy": {"allow_cloud_processing": false, "allow_public_archiving": false},
  "publication": {"human_approval_required": true},
  "style": {"tone": "Claro, sobrio, sin adjetivación innecesaria"},
  "topics": ["transporte"],
  "bylines": [],
  "rules": [
    {
      "rule": "Prefiere explicar los tecnicismos en su primera aparición",
      "type": "preference",
      "source_urls": [],
      "consulted_at": "2026-11-01",
      "approval": "pending",
      "evidence_limit": "Preferencia declarada durante el onboarding; pendiente de confirmar la síntesis"
    }
  ]
}
```

## Registro de evidencia

- **Identidad:** `journalist.name`, `signature`, `role`, `section`, `formats`; `author_url` sólo si está verificada. `country` es la jurisdicción de trabajo elegida, no una nacionalidad inferida. La zona horaria debe confirmarse si hay ambigüedad relevante.
- **Medio:** nombre y URL oficial. Conservar alias o aclaraciones en notas editoriales, no inventar claves que el schema no admite.
- **Firmas:** cada elemento de `bylines` lleva `title`, `url`, `consulted_at`, `authorship_confirmed` y `confidence` (`high`, `medium`, `low`); opcionales `published_at` y `notes`. Explicar cómo se descartó un homónimo. Sólo las confirmadas sustentan voz personal; las dudosas quedan fuera de la muestra.
- **Reglas:** `rule`, `type`, `source_urls`, `consulted_at`, `approval` (`pending`, `approved`, `rejected`) y, cuando haga falta, `evidence_limit`. En `explicit`, enlazar política institucional y fragmento/epígrafe identificable; en `inferred`, enlazar las piezas de la muestra y describir alcance, género y excepciones. En `preference`, puede no existir URL: dejar array vacío y atribuir la elección a la conversación, sin inventar una fuente.
- **Fechas:** ISO `AAAA-MM-DD` o fecha-hora UTC. Diferenciar fecha de publicación, actualización y consulta. No atribuir una versión actual a una pieza histórica.
- **Privacidad:** los valores de privacidad empiezan en `false`. Un valor `true` no es permiso universal para cualquier destino o material: confirmar el alcance de cada egress sensible. Aprobaciones de publicación siempre humanas.

## Nota complementaria opcional

En `perfil-editorial.md` del espacio de trabajo registrar el alcance de la búsqueda, listado completo de muestra, reglas no encontradas, ambigüedades y preguntas pendientes. Mantenerlo sin datos sensibles. La fecha de revisión no debe actualizarse si no se volvió a revisar la evidencia.

## Pregunta de confirmación recomendada

«Encontré estas pautas públicas; observé estos patrones en estas notas; y anoté estas preferencias tuyas. ¿Te representa? No encontré/confirmé tus firmas todavía, así que no estoy atribuyéndote una voz propia». Guardar como aprobado sólo lo aceptado, no todo el perfil por el silencio del usuario.
