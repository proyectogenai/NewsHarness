# Referencias y componentes externos

Este prototipo no implica patrocinio, afiliación ni validación de los proyectos citados.

## Referencias metodológicas

- **Big If True, Verso Lab:** https://github.com/Verso-Lab/big-if-true-plugin . Revisión de la versión 0.7.1, commit `1ece4ebcc646b39d8c56ad9624a03260fe47b367`. El proyecto publica licencia MIT. Los procedimientos de este kit son una adaptación editorial propia; no se redistribuye el plugin original. Si se incorporan archivos o porciones sustanciales del original en una versión posterior, deben conservarse sus avisos y licencia.
- **indec-api-skill, Jony Musky:** https://github.com/jonymusky/indec-api-skill . Revisión del commit `0a95cccee05ca5c902035c83728882a0eec0cab3` (2 de noviembre de 2026). Licencia MIT. `scripts/indec_api.py`, `skills/newsharness-indec/` y sus referencias adaptan su cliente, sus trampas documentadas y sus recetas: comandos en español, URL base fija, sin redirecciones, token nunca impreso, límite de filas, salida sin sobrescribir con procedencia, conteo de signos convencionales y spec incluida en `config/indec/openapi.json` (spec pública del INDEC, consultada el 3 de noviembre de 2026). Se conserva su aviso:

  ```
  MIT License

  Copyright (c) 2026 Jony Musky

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.
  ```
- La publicación de URLs en Wayback Machine no se incorpora como acción automática. Un archivo público puede revelar material o una investigación.

## Motores y modelos candidatos

- **Tesseract:** https://github.com/tesseract-ocr/tesseract ; **tessdata_fast:** https://github.com/tesseract-ocr/tessdata_fast . Licencias Apache-2.0 del proyecto y modelos. Conservar los avisos correspondientes si se redistribuyen.
- **whisper.cpp:** https://github.com/ggml-org/whisper.cpp ; modelos convertidos por su autor: https://huggingface.co/ggerganov/whisper.cpp . Licencia MIT publicada por los proyectos. Descargar sólo los artefactos identificados en el catálogo y verificar sus huellas.
- **pypdfium2/PDFium:** https://github.com/pypdfium2-team/pypdfium2 . El wrapper y los binarios incluyen licencias distintas y avisos de terceros. Revisar los archivos de licencia de la distribución elegida antes de redistribuirla.
- **FFmpeg:** https://ffmpeg.org/legal.html . La licencia y los componentes dependen de cómo se compiló el ejecutable. No se incluye un binario de FFmpeg en esta entrega.

El tamaño de un archivo de modelo no indica el tamaño total de la instalación ni su memoria máxima. No se considera una herramienta «segura» únicamente por tener licencia abierta.

## Video (skill newsharness-video)

Revisados el 2026-11-08. Ninguno se incluye en el repositorio: se instalan, si hacen falta, con autorización del usuario.

- **HyperFrames (HeyGen):** https://github.com/heygen-com/hyperframes . Apache-2.0, versión `v0.9.22`. Requiere Node.js 22+ y FFmpeg; envía telemetría de uso salvo que se desactive (`hyperframes telemetry disable` o `HYPERFRAMES_NO_TELEMETRY=1`). Sus funciones Pro y de nube usan servicios de HeyGen y quedan fuera del uso recomendado.
- **Auto-Editor:** https://github.com/WyattBlue/auto-editor . Unlicense. Opcional.
- **PySceneDetect:** https://github.com/Breakthrough/PySceneDetect . BSD-3-Clause. Opcional.

## Fuera de alcance

- **Remotion** (https://github.com/remotion-dev/remotion) se evaluó y se descartó para esta versión por su licencia: es gratuito para personas, equipos de hasta 3 personas y organizaciones sin fines de lucro, pero exige una licencia paga a empresas con fines de lucro de 4 o más personas, que incluye a la mayoría de las redacciones. Que este kit sea open source no cambia la obligación de quien lo usa.
- Splash queda para una posible segunda etapa.
