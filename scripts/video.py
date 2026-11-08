#!/usr/bin/env python3
"""Herramientas de video para NewsHarness (Python estándar, >=3.10).

Tres trabajos chicos y revisables, pensados para que un agente los ejecute por
cuenta del periodista:

- ``subtitulos``: del transcript (whisper.cpp JSON, JSON completo con tokens,
  SRT o lista de palabras) a un archivo .ass con estilo de redes, que FFmpeg
  quema sin otras dependencias.
- ``palabras``: el mismo transcript como lista normalizada de palabras
  ``[{"text", "start", "end"}]``, la entrada de subtítulos de HyperFrames.
- ``cortes``: de una lista de cortes con su cita a comandos de FFmpeg, con el
  texto que queda antes y después de cada corte para revisar el contexto.
  Sin ``--ejecutar`` sólo muestra el plan.
- ``quemar``: pega un .ass sobre un video.

No sobrescribe archivos, no usa la red y nunca toca el original: todo sale en
archivos nuevos con su procedencia (SHA256 del original y comandos usados).
"""
import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

FORMATOS = {
    # ancho, alto, tamaño de letra, margen inferior, caracteres por línea
    "9:16": (1080, 1920, 84, 620, 22),
    "16:9": (1920, 1080, 64, 80, 38),
    "1:1": (1080, 1080, 64, 110, 28),
    "4:5": (1080, 1350, 70, 220, 26),
}
ESTILOS = ("frase", "karaoke", "resaltado")
MAX_BLOQUE = 3.5        # segundos máximos en pantalla por bloque
PAUSA_CORTE = 0.6       # una pausa más larga empieza un bloque nuevo
CONTEXTO = 12.0         # segundos de texto que se muestran antes y después de un corte
FIN_FRASE = re.compile(r"[.!?…]$")
NOMBRE_SIMPLE = re.compile(r"^[A-Za-z0-9._-]+$")


class VideoError(Exception):
    pass


# ---------------------------------------------------------------- tiempos

def parse_time(value):
    """Acepta segundos (12.5), MM:SS(.mmm) o HH:MM:SS(,mmm|.mmm)."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        seconds = float(value)
    else:
        text = str(value).strip().replace(",", ".")
        parts = text.split(":")
        if not 1 <= len(parts) <= 3 or not all(re.fullmatch(r"\d+(\.\d+)?", p) for p in parts):
            raise VideoError(f"Tiempo inválido: {value!r}. Use segundos, MM:SS o HH:MM:SS.mmm.")
        seconds = 0.0
        for part in parts:
            seconds = seconds * 60 + float(part)
    if not math.isfinite(seconds) or seconds < 0:
        raise VideoError(f"Tiempo inválido: {value!r}.")
    return round(seconds, 3)


def fmt_clock(seconds):
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def fmt_ass_time(seconds):
    cs = int(round(max(0.0, seconds) * 100))
    h, cs = divmod(cs, 360_000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


# ---------------------------------------------------------------- transcript

def _offsets(item):
    off = item.get("offsets")
    if isinstance(off, dict) and "from" in off and "to" in off:
        return off["from"] / 1000, off["to"] / 1000
    ts = item.get("timestamps")
    if isinstance(ts, dict) and "from" in ts and "to" in ts:
        return parse_time(ts["from"]), parse_time(ts["to"])
    raise VideoError("Segmento sin tiempos reconocibles en el transcript.")


def _words_from_tokens(tokens):
    """Une los tokens de whisper.cpp en palabras: un token con espacio inicial abre una palabra."""
    words = []
    for tok in tokens:
        text = tok.get("text", "")
        if not text or text.startswith("[_") or re.fullmatch(r"\[.*\]", text.strip()):
            continue  # tokens especiales ([_BEG_], [_TT_..]) y marcas como [Música]
        start, end = _offsets(tok)
        if text.startswith(" ") or not words:
            if text.strip():
                words.append({"text": text.strip(), "start": start, "end": end})
        else:
            words[-1]["text"] += text
            words[-1]["end"] = end
    return [w for w in words if w["text"]]


def _segments_from_srt(text):
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip())
    segs = []
    for block in blocks:
        lines = [l for l in block.split("\n") if l.strip()]
        idx = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if idx is None:
            continue
        a, b = (p.strip().split(" ")[0] for p in lines[idx].split("-->"))
        body = " ".join(lines[idx + 1:]).strip()
        if body:
            segs.append({"text": body, "start": parse_time(a), "end": parse_time(b)})
    return segs


def load_transcript(path):
    """Devuelve (segmentos, palabras|None, formato). Las palabras sólo existen si el original las trae."""
    path = Path(path)
    if not path.is_file():
        raise VideoError(f"No existe el transcript: {path}")
    raw = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() in (".srt", ".vtt"):
        segs = _segments_from_srt(re.sub(r"^WEBVTT.*?\n", "", raw, flags=re.S) if path.suffix.lower() == ".vtt" else raw)
        return segs, None, path.suffix.lower()[1:]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise VideoError(f"El transcript no es JSON válido: {exc}") from None
    if isinstance(data, list):  # lista normalizada de palabras
        words = []
        for w in data:
            if not isinstance(w, dict) or not {"text", "start", "end"} <= w.keys():
                raise VideoError("La lista de palabras debe tener text, start y end en cada elemento.")
            words.append({"text": str(w["text"]).strip(), "start": float(w["start"]), "end": float(w["end"])})
        words = [w for w in words if w["text"]]
        return [{"text": " ".join(w["text"] for w in words), "start": words[0]["start"], "end": words[-1]["end"]}] if words else [], words, "palabras"
    if not isinstance(data, dict) or not isinstance(data.get("transcription"), list):
        raise VideoError("Formato de transcript no reconocido: se espera JSON de whisper.cpp, SRT, VTT o lista de palabras.")
    segs, words, has_tokens = [], [], False
    for item in data["transcription"]:
        start, end = _offsets(item)
        text = item.get("text", "").strip()
        if text:
            segs.append({"text": text, "start": start, "end": end})
        if item.get("tokens"):
            has_tokens = True
            words += _words_from_tokens(item["tokens"])
    return segs, (words if has_tokens else None), ("whisper-json-full" if has_tokens else "whisper-json")


def estimate_words(segments):
    """Reparte cada segmento en palabras según su largo. Sólo sirve como efecto visual."""
    words = []
    for seg in segments:
        tokens = seg["text"].split()
        total = sum(len(t) for t in tokens) or 1
        t = seg["start"]
        span = max(0.0, seg["end"] - seg["start"])
        for tok in tokens:
            d = span * len(tok) / total
            words.append({"text": tok, "start": round(t, 3), "end": round(t + d, 3)})
            t += d
    return words


def clip_items(items, desde, hasta):
    """Recorta a [desde, hasta] y corre los tiempos para que el clip empiece en 0."""
    out = []
    for it in items:
        if it["end"] <= desde or (hasta is not None and it["start"] >= hasta):
            continue
        start = max(it["start"], desde) - desde
        end = (min(it["end"], hasta) if hasta is not None else it["end"]) - desde
        out.append({**it, "start": round(start, 3), "end": round(max(end, start), 3)})
    return out


# ---------------------------------------------------------------- bloques y ASS

def group_blocks(words, max_chars, max_lines=2):
    """Agrupa palabras en bloques de hasta max_lines líneas; corta en pausas, fin de frase o duración."""
    limit = max_chars * max_lines
    blocks, cur = [], []
    for w in words:
        if cur:
            length = len(" ".join(x["text"] for x in cur + [w]))
            pause = w["start"] - cur[-1]["end"]
            if (length > limit or pause > PAUSA_CORTE or w["end"] - cur[0]["start"] > MAX_BLOQUE
                    or FIN_FRASE.search(cur[-1]["text"])):
                blocks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        blocks.append(cur)
    return blocks


def split_lines(words, max_chars):
    """Índices donde empieza cada línea; equilibra dos líneas si el bloque no entra en una."""
    text = " ".join(w["text"] for w in words)
    if len(text) <= max_chars or len(words) < 2:
        return [0]
    best, best_diff = 1, None
    for i in range(1, len(words)):
        a = len(" ".join(w["text"] for w in words[:i]))
        b = len(" ".join(w["text"] for w in words[i:]))
        diff = abs(a - b) + (1000 if max(a, b) > max_chars else 0)
        if best_diff is None or diff < best_diff:
            best, best_diff = i, diff
    return [0, best]


def ass_color(hex_color, alpha=0):
    m = re.fullmatch(r"#?([0-9A-Fa-f]{6})", hex_color or "")
    if not m:
        raise VideoError(f"Color inválido: {hex_color!r}. Use #RRGGBB.")
    rr, gg, bb = m.group(1)[0:2], m.group(1)[2:4], m.group(1)[4:6]
    return f"&H{alpha:02X}{bb}{gg}{rr}".upper()


def check_text(text):
    if re.search(r"[{}\\]", text):
        raise VideoError("El transcript tiene llaves o barras invertidas, que el formato .ass interpreta como "
                         f"comandos: «{text[:60]}». Revisar el texto antes de generar subtítulos.")
    return text


def _render_block(words, max_chars, estilo, active=None, highlight=None):
    starts = split_lines(words, max_chars)
    parts = []
    for i, w in enumerate(words):
        sep = "" if i == 0 else ("\\N" if i in starts else " ")
        token = check_text(w["text"])
        if estilo == "karaoke":
            dur = max(1, int(round((w["end"] - w["start"]) * 100)))
            gap = int(round((w["start"] - words[i - 1]["end"]) * 100)) if i else 0
            pre = f"{{\\k{gap}}}" if gap > 0 else ""
            parts.append(f"{sep}{pre}{{\\kf{dur}}}{token}")
        elif estilo == "resaltado" and i == active:
            parts.append(f"{sep}{{\\c{highlight}\\fscx108\\fscy108}}{token}{{\\r}}")
        else:
            parts.append(f"{sep}{token}")
    return "".join(parts)


def build_ass(words, formato="9:16", estilo="resaltado", fuente="Arial", color="#FFFFFF",
              resaltado="#FF6B35", max_chars=None, titulo="NewsHarness"):
    if formato not in FORMATOS:
        raise VideoError(f"Formato desconocido: {formato}. Opciones: {', '.join(FORMATOS)}.")
    if estilo not in ESTILOS:
        raise VideoError(f"Estilo desconocido: {estilo}. Opciones: {', '.join(ESTILOS)}.")
    if not re.fullmatch(r"[\w .-]{1,40}", fuente):
        raise VideoError("Nombre de fuente inválido.")
    width, height, size, margin, chars = FORMATOS[formato]
    max_chars = max_chars or chars
    base, high = ass_color(color), ass_color(resaltado)
    # En karaoke, \kf pinta de SecondaryColour a PrimaryColour: primario = resaltado.
    primary, secondary = (high, base) if estilo == "karaoke" else (base, high)
    header = [
        "[Script Info]", f"Title: {titulo}", "ScriptType: v4.00+", f"PlayResX: {width}", f"PlayResY: {height}",
        "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{fuente},{size},{primary},{secondary},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,"
        f"{max(3, size // 18)},1,2,60,60,{margin},1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    events = []
    for block in group_blocks(words, max_chars):
        if estilo == "resaltado":
            for i, w in enumerate(block):
                end = block[i + 1]["start"] if i + 1 < len(block) else w["end"]
                events.append((w["start"], max(end, w["start"] + 0.05),
                               _render_block(block, max_chars, estilo, i, high)))
        else:
            events.append((block[0]["start"], block[-1]["end"], _render_block(block, max_chars, estilo)))
    lines = header + [f"Dialogue: 0,{fmt_ass_time(a)},{fmt_ass_time(b)},Default,,0,0,0,,{t}" for a, b, t in events]
    return "\n".join(lines) + "\n", len(events)


# ---------------------------------------------------------------- archivos

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_new(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    except FileExistsError:
        raise VideoError(f"{path} ya existe: elija otro nombre. NewsHarness no sobrescribe archivos.") from None


def ffmpeg_bin():
    found = shutil.which("ffmpeg")
    if not found:
        raise VideoError("No se encontró FFmpeg. El agente debe explicar cómo instalarlo y esperar autorización.")
    return found


def ffprobe_duration(video):
    probe = shutil.which("ffprobe")
    if not probe:
        return None
    out = subprocess.run([probe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                         capture_output=True, text=True, timeout=60)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return None


# ---------------------------------------------------------------- comandos

def words_for(args, notes):
    segs, words, fmt = load_transcript(args.transcripcion)
    if words is None:
        if args.estilo != "frase" and not args.estimar_palabras:
            raise VideoError(f"El transcript ({fmt}) no trae tiempos por palabra. Opciones: transcribir con "
                             "`transcribe --palabras`, usar --estilo frase, o --estimar-palabras (efecto visual aproximado).")
        if args.estilo == "frase":
            words = estimate_words(segs)
            notes.append("El transcript no trae tiempos por palabra: si una frase larga se parte en dos "
                         "subtítulos, el punto de corte es aproximado.")
        else:
            words = estimate_words(segs)
            notes.append("Tiempos por palabra ESTIMADOS a partir de frases: sirven como efecto visual, "
                         "no como minuto exacto de una cita.")
    desde = parse_time(args.desde) if args.desde is not None else 0.0
    hasta = parse_time(args.hasta) if args.hasta is not None else None
    if hasta is not None and hasta <= desde:
        raise VideoError("--hasta debe ser mayor que --desde.")
    words = clip_items(words, desde, hasta)
    if not words:
        raise VideoError("No hay palabras en el tramo pedido.")
    return words, fmt, desde, hasta


def cmd_subtitulos(args):
    notes = []
    words, fmt, desde, hasta = words_for(args, notes)
    text, n = build_ass(words, args.formato, args.estilo, args.fuente, args.color, args.color_resaltado, args.max_caracteres)
    write_new(args.salida, text)
    if desde or hasta is not None:
        notes.append(f"Tiempos corridos al tramo {fmt_clock(desde)}–{fmt_clock(hasta) if hasta is not None else 'fin'}: "
                     "usar con el clip recortado en ese mismo tramo.")
    notes.append("Revisar cada subtítulo contra el audio: el texto es una cita y debe ser literal.")
    return {"salida": str(args.salida), "formato": args.formato, "estilo": args.estilo, "eventos": n,
            "palabras": len(words), "transcript": {"archivo": str(args.transcripcion), "tipo": fmt,
                                                    "sha256": sha256(args.transcripcion)}, "avisos": notes}


def cmd_palabras(args):
    notes = []
    args.estilo = "karaoke"
    words, fmt, desde, hasta = words_for(args, notes)
    for w in words:
        check_text(w["text"])
    words = [{"id": f"w{i}", **w} for i, w in enumerate(words)]
    write_new(args.salida, json.dumps(words, ensure_ascii=False, indent=1) + "\n")
    return {"salida": str(args.salida), "palabras": len(words), "tipo": fmt, "avisos": notes}


def load_cuts(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VideoError(f"No se pudo leer la lista de cortes: {exc}") from None
    cuts = data.get("cortes") if isinstance(data, dict) else None
    if not isinstance(cuts, list) or not cuts:
        raise VideoError('La lista de cortes debe ser {"cortes": [{"id", "desde", "hasta", "cita"}, ...]}.')
    seen, out = set(), []
    for i, c in enumerate(cuts, 1):
        cid = str(c.get("id") or f"corte-{i:02d}")
        if not NOMBRE_SIMPLE.fullmatch(cid) or cid in seen:
            raise VideoError(f"id de corte inválido o repetido: {cid!r} (letras, números, punto, guion).")
        seen.add(cid)
        a, b = parse_time(c.get("desde")), parse_time(c.get("hasta"))
        if b <= a:
            raise VideoError(f"{cid}: 'hasta' debe ser mayor que 'desde'.")
        out.append({"id": cid, "desde": a, "hasta": b, "cita": str(c.get("cita", "")).strip(),
                    "nota": str(c.get("nota", "")).strip()})
    return out


def text_between(segments, a, b):
    return " ".join(s["text"] for s in segments if s["end"] > a and s["start"] < b).strip()


def video_filter(formato):
    if formato is None:
        return None
    width, height = FORMATOS[formato][:2]
    # Llena el cuadro y recorta al centro: revisar que no quede afuera lo importante.
    return f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1"


def cut_command(ffmpeg, source, cut, out, formato):
    cmd = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
           "-ss", f"{cut['desde']:.3f}", "-i", str(source), "-t", f"{cut['hasta'] - cut['desde']:.3f}"]
    vf = video_filter(formato)
    if vf:
        cmd += ["-vf", vf]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]
    return cmd


def cmd_cortes(args):
    source = Path(args.fuente)
    if not source.is_file():
        raise VideoError(f"No existe el video o audio: {source}")
    cuts = load_cuts(args.lista)
    out_dir = Path(args.salida_dir)
    segments = load_transcript(args.transcripcion)[0] if args.transcripcion else None
    duration = ffprobe_duration(source)
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    notes, plan = [], []
    if segments is None:
        notes.append("Sin --transcripcion no se puede mostrar qué queda afuera de cada corte: revisarlo escuchando.")
    for c in cuts:
        if duration is not None and c["hasta"] > duration + 0.05:
            raise VideoError(f"{c['id']}: termina en {fmt_clock(c['hasta'])}, después del final del archivo ({fmt_clock(duration)}).")
        out = out_dir / f"{c['id']}.mp4"
        item = {"id": c["id"], "desde": fmt_clock(c["desde"]), "hasta": fmt_clock(c["hasta"]),
                "duracion_s": round(c["hasta"] - c["desde"], 3), "cita": c["cita"], "nota": c["nota"],
                "salida": str(out), "comando": cut_command(ffmpeg, source, c, out, args.formato)}
        if segments is not None:
            item["contexto"] = {
                "antes": text_between(segments, max(0.0, c["desde"] - CONTEXTO), c["desde"]),
                "dentro": text_between(segments, c["desde"], c["hasta"]),
                "despues": text_between(segments, c["hasta"], c["hasta"] + CONTEXTO),
            }
        plan.append(item)
    record = {"herramienta": "scripts/video.py cortes", "original": {"archivo": str(source), "sha256": sha256(source),
              "duracion_s": duration}, "formato": args.formato, "cortes": plan,
              "advertencia": "Cada corte debe conservar el sentido de lo dicho. Revisar el contexto antes de publicar."}
    if not args.ejecutar:
        notes.append("Plan sin ejecutar: revisar citas y contexto con el periodista y repetir con --ejecutar.")
        return {**record, "ejecutado": False, "avisos": notes}
    ffmpeg = ffmpeg_bin()
    for item in plan:
        if Path(item["salida"]).exists():
            raise VideoError(f"{item['salida']} ya existe: elija otra carpeta. NewsHarness no sobrescribe archivos.")
    out_dir.mkdir(parents=True, exist_ok=True)
    registro = out_dir / "registro-cortes.json"
    if registro.exists():
        raise VideoError(f"{registro} ya existe: elija otra carpeta.")
    for item in plan:
        item["comando"][0] = ffmpeg
        res = subprocess.run(item["comando"], capture_output=True, text=True, timeout=3600)
        if res.returncode != 0:
            raise VideoError(f"FFmpeg falló en {item['id']}: {res.stderr.strip()[-400:]}")
        item["sha256_salida"] = sha256(item["salida"])
    write_new(registro, json.dumps({**record, "ejecutado": True}, ensure_ascii=False, indent=1) + "\n")
    return {**record, "ejecutado": True, "registro": str(registro), "avisos": notes}


def cmd_quemar(args):
    video, subs, out = Path(args.video), Path(args.subtitulos), Path(args.salida)
    for p in (video, subs):
        if not p.is_file():
            raise VideoError(f"No existe: {p}")
    if subs.suffix.lower() != ".ass" or not NOMBRE_SIMPLE.fullmatch(subs.name):
        raise VideoError("Los subtítulos deben ser un .ass con nombre simple (letras, números, punto, guion).")
    if out.exists():
        raise VideoError(f"{out} ya existe: elija otro nombre.")
    # FFmpeg corre en la carpeta del .ass para no escapar rutas de Windows dentro del filtro.
    cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-n", "-i", str(video.resolve()),
           "-vf", f"ass={subs.name}", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "copy", "-movflags", "+faststart", str(out.resolve())]
    result = {"video": str(video), "subtitulos": str(subs), "salida": str(out), "comando": cmd, "ejecutado": False}
    if not args.ejecutar:
        return {**result, "avisos": ["Plan sin ejecutar: repetir con --ejecutar."]}
    cmd[0] = ffmpeg_bin()
    out.parent.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, cwd=str(subs.resolve().parent))
    if res.returncode != 0:
        raise VideoError(f"FFmpeg falló: {res.stderr.strip()[-400:]}")
    return {**result, "ejecutado": True, "sha256_salida": sha256(out),
            "avisos": ["Mirar el video completo: subtítulos legibles, dentro de la zona segura y sincronizados."]}


def build_parser():
    p = argparse.ArgumentParser(prog="video.py", description="Video para NewsHarness: subtítulos, cortes y quemado, sin sobrescribir.")
    sub = p.add_subparsers(dest="cmd", required=True)

    def transcript_args(sp):
        sp.add_argument("--transcripcion", required=True, help="JSON de whisper.cpp, SRT, VTT o lista de palabras")
        sp.add_argument("--desde", help="Inicio del tramo (corre los tiempos a 0)")
        sp.add_argument("--hasta", help="Fin del tramo")
        sp.add_argument("--estimar-palabras", action="store_true", help="Repartir frases en palabras (sólo efecto visual)")
        sp.add_argument("--salida", required=True)

    s = sub.add_parser("subtitulos", help="Transcript → .ass con estilo de redes")
    transcript_args(s)
    s.add_argument("--formato", choices=FORMATOS, default="9:16")
    s.add_argument("--estilo", choices=ESTILOS, default="resaltado")
    s.add_argument("--fuente", default="Arial")
    s.add_argument("--color", default="#FFFFFF")
    s.add_argument("--color-resaltado", default="#FF6B35")
    s.add_argument("--max-caracteres", type=int)
    s.set_defaults(func=cmd_subtitulos)

    s = sub.add_parser("palabras", help="Transcript → lista de palabras para HyperFrames")
    transcript_args(s)
    s.set_defaults(func=cmd_palabras)

    s = sub.add_parser("cortes", help="Lista de cortes → plan y comandos de FFmpeg")
    s.add_argument("--fuente", required=True, help="Video o audio original (no se modifica)")
    s.add_argument("--lista", required=True, help='JSON {"cortes": [{"id", "desde", "hasta", "cita"}]}')
    s.add_argument("--salida-dir", required=True)
    s.add_argument("--transcripcion", help="Para mostrar el texto antes, dentro y después de cada corte")
    s.add_argument("--formato", choices=FORMATOS, help="Reencuadrar (recorta al centro)")
    s.add_argument("--ejecutar", action="store_true")
    s.set_defaults(func=cmd_cortes)

    s = sub.add_parser("quemar", help="Pegar un .ass sobre un video")
    s.add_argument("--video", required=True)
    s.add_argument("--subtitulos", required=True)
    s.add_argument("--salida", required=True)
    s.add_argument("--ejecutar", action="store_true")
    s.set_defaults(func=cmd_quemar)
    return p


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    try:
        result = args.func(args)
    except VideoError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
