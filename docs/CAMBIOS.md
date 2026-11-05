# Cambios de la v0.1

## Versión neutral para compartir · 4 de noviembre de 2026

- Se publica como proyecto abierto independiente de cualquier medio. El catálogo `config/medios.json` se distribuye vacío y se retiran las herramientas y referencias propias de un medio. Las rutas de fuentes por país (AR, MX, PE, CO, CR) y la skill del INDEC no cambian.

## INDEC por API · 3 de noviembre de 2026

- Nueva skill `newsharness-indec` y `scripts/indec_api.py`, adaptados de [indec-api-skill](https://github.com/jonymusky/indec-api-skill) de Jony Musky (MIT, ver [TERCEROS.md](TERCEROS.md)): 19 tablas oficiales del Catálogo API-INDEC (IPC, canastas, pobreza y mercado de trabajo de la EPH, EMAE, IPI, salarios, construcción, mayoristas, población, comercio exterior).
- Cambios respecto del original: comandos en español (`tablas`, `columnas`, `consultar`, `valores`, `ultimos`, `contar`) con alias en inglés; URL base fija y redirecciones rechazadas para que el token no viaje a otro host; token sólo desde `INDEC_TOKEN`, nunca impreso ni guardado; límite de 200.000 filas; `--salida` que no sobrescribe y agrega `.procedencia.json`; conteo de signos convencionales (`s`, `*`, `e`…) y cita sugerida; spec incluida en `config/indec/openapi.json` para validar sin red; `comparar-spec` para detectar cambios publicados; catálogo de tablas generado por la propia herramienta.
- La skill indica al periodista cómo registrarse y guardar el token fuera del chat; el agente no crea cuentas ni pide el token. Las skills de datos, Python, chequeo y onboarding derivan a `newsharness-indec`.
- 13 pruebas nuevas sin red, incluida una que valida contra la spec cada tabla y columna citada en las recetas.

## Skills ampliadas, Python, git y fuentes de Argentina · 3 de noviembre de 2026

- Dos skills nuevas: `newsharness-python` (análisis reproducible ejecutado por el agente, con recetas para variaciones, inflación acumulada, deflactar, cruces sin pérdida silenciosa, APIs del BCRA y datos.gob.ar, gráficos y exportación segura a Excel) y `newsharness-git` (versiones de borradores en lenguaje de redacción; prohíbe operaciones destructivas y cualquier subida sin autorización explícita).
- Las siete skills existentes suman descripción con frases de activación, «cuándo usarla» y derivaciones, flujo rápido, plantilla de entrega y errores frecuentes. `newsharness-redaccion` agrega [formatos.md](../skills/newsharness-redaccion/references/formatos.md); `newsharness-onboarding`, una recorrida de capacidades.
- Nueva referencia [fuentes-ar.md](../skills/newsharness-factcheck/references/fuentes-ar.md): INDEC y su calendario, Series de Tiempo de datos.gob.ar, BCRA API v4.0 (v3.0 dada de baja), cotizaciones, Boletín Oficial con URL estable de avisos, normativa, presupuesto, CNV, justicia y elecciones, y errores frecuentes en notas argentinas.
- `config/countries/ar.json` apunta a la nueva referencia.
- 133 pruebas aprobadas en Windows 11 (2 omitidas por plataforma).

## Instalación global · 2 de noviembre de 2026

- Nuevo `install-skills --global --agent claude|codex|opencode`: el kit queda en `~/.newsharness-kit/` y las skills en la carpeta de usuario del agente (`~/.claude/skills/`, `~/.codex/skills/` o `$CODEX_HOME/skills/`, `~/.config/opencode/skills/`). NewsHarness queda disponible en cualquier consulta.
- No modifica `CLAUDE.md`, `AGENTS.md` ni otras instrucciones globales: cada skill indica dónde leer las reglas comunes del kit.
- Manifiesto con SHA256 por archivo: `--update` reemplaza sólo archivos no modificados y retira los que la versión nueva ya no trae; `--uninstall` quita sólo lo que instaló NewsHarness y conserva lo editado. Perfiles, espacios de trabajo y modelos quedan fuera.
- `AGENTS.md` admite esta instalación global como única excepción, con pedido o confirmación del usuario.
- Nuevo [INSTALAR.md](../INSTALAR.md) con el texto para que el periodista se lo pegue a su agente.
- 125 pruebas aprobadas en Windows 11 (2 omitidas por plataforma); 6 nuevas para la instalación global.

## Preparación para repositorio · 1 de noviembre de 2026

- Corregido: en Windows, el runtime rechazaba rutas con subcarpetas (instalación de skills, descargas, copia de originales). La validación ahora usa `as_posix()` y rechaza también rutas relativas a unidad.
- Corregido: lecturas de texto con codificación explícita UTF-8 en runtime y pruebas.
- Nuevos: `.gitattributes` (LF obligatorio para anclajes y checksums), `LICENSE` MIT, `CONTRIBUTING.md`, `SECURITY.md`, plantillas de issues e integración continua en Linux/Windows/macOS.
- 119 pruebas aprobadas en Windows 11 (2 omitidas por plataforma). Checksums regenerados.

## Ampliación regional · 1 de noviembre de 2026

- Rutas documentales añadidas: Perú, Colombia y Costa Rica. Cobertura inicial: AR, MX, PE, CO y CR.
- Catálogo de medios para desambiguar nombre/país/dominio en el onboarding.
- Onboarding consulta el catálogo para desambiguar nombre/país/dominio, sin convertir la membresía en reglas editoriales.
- Medios de otro idioma se señalan como tales; el catálogo no promete OCR ni evaluación de audio en otros idiomas.
- Accesos restringidos, tokens, CAPTCHA, portales dinámicos y consultas no probadas quedan señalados en cada ruta.
- 82 pruebas automatizadas aprobadas; no cambian los límites de verificación de motores de la entrega inicial.
- Sin Splash, sin publicación externa y sin nuevas instalaciones en el equipo del usuario.

Esta revisión actualiza el mismo paquete; no requiere configurar perfiles de periodistas desde cero. El instalador no sobrescribe archivos diferentes: para una instalación previa, comparar y aplicar cambios revisados con autorización, conservando los perfiles.

## Analista de discursos y entrevistas · nueva revisión de v0.1

- Nueva séptima skill `newsharness-discursos`, plantillas de ingreso/inventario/evidencia/informe/revisión y esquema JSON.
- Ejemplo central: video de Milei en Universidad Torcuato Di Tella aportado por el usuario. Ficha real parcial documentada, sin trasplantar las frases de otro caso incluido en el prompt metodológico. Ejercicio sintético separado para pruebas.
- Inventario literal → selección humana → evidencia fechada/versionada → informe → revisión de versión concreta. Opiniones, proyecciones y promesas separadas del chequeo factual.
- Catálogo neutral de hipótesis contrastables, no etiquetas de engaño ni causalidades preestablecidas. Dato pertinente a la fecha, con revisiones posteriores explícitas.
- Validador offline `scripts/validate_discourse.py`: anclas, cortes, precisión temporal, consistencia de estados y hash de revisión. No comprueba la verdad, la exhaustividad ni la identidad humana, ni autoriza publicar.
- 118 pruebas aprobadas. Instalador existente incluye módulo y archivos de apoyo para los tres adaptadores; no sobrescribe instalaciones distintas.
- Sin app, video, conectores nuevos, instalaciones adicionales ni publicación externa. Continúa la versión v0.1 de evaluación, con nueva revisión del mismo paquete.
