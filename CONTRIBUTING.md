# Cómo contribuir

Este kit lo usan periodistas que no programan. Toda contribución debe respetar las reglas de [AGENTS.md](AGENTS.md): originales preservados, revisión humana y nada de publicación automática.

## Formas de aportar

- **Reportar un fallo en tu equipo:** abrí un issue con sistema operativo, agente (Codex, Claude Code u OpenCode), versión de Python y el mensaje de error. No pegues material periodístico reservado, perfiles reales, tokens ni rutas que revelen datos personales.
- **Proponer rutas de fuentes de un país:** seguí el formato de `skills/newsharness-factcheck/references/fuentes-*.md` y `config/countries/`. Indicá fecha de consulta y límites de acceso (registro, token, CAPTCHA). Una ruta no revisada se marca como tal.
- **Mejorar una skill:** explicá el problema editorial que resuelve. Un cambio de método debe venir con un caso de prueba ficticio o público, nunca con material de una fuente protegida.

## Antes de abrir un pull request

1. Correr las pruebas desde la raíz del kit:

   ```sh
   python3 -m unittest discover -s tests -v
   ```

   En Windows puede corresponder `py -3`. Las pruebas corren en Linux, Windows y macOS en la integración continua.
2. Si cambiaste archivos del paquete, regenerar `CHECKSUMS.sha256` (ver más abajo).
3. Registrar el cambio en [docs/CAMBIOS.md](docs/CAMBIOS.md) y, si cambia lo comprobado, en [docs/VERIFICACION.md](docs/VERIFICACION.md).
4. Mantener LF como fin de línea (lo fuerza `.gitattributes`): los anclajes de citas dependen de bytes exactos.

## Regenerar checksums

```sh
git ls-files | grep -vx CHECKSUMS.sha256 | LC_ALL=C sort | xargs sha256sum > CHECKSUMS.sha256
```

## Qué no se acepta

- Modelos, binarios de motores o instaladores dentro del repositorio.
- Credenciales, cuentas o datos reales de periodistas o fuentes.
- Funciones que publiquen, envíen o archiven públicamente sin autorización humana explícita.
- Casos que atribuyan frases inventadas a personas reales.
