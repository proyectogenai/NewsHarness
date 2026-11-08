#!/usr/bin/env python3
"""NewsHarness Kit 0.1: local, dependency-light journalism helpers (Python >=3.10).

This program never calls a language-model API or publishes material. Only the
explicit `fetch --approve-download` command can contact the network. Agent/model
privacy is a separate decision: using a cloud agent can disclose file contents.
"""
from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import hashlib
import importlib.util
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import signal
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import wave
import warnings

VERSION = "0.1.0"
ROOT = Path(__file__).resolve().parent.parent
GIB = 1024 ** 3
MODELS = {
    "tiny": {"filename": "ggml-tiny-q5_1.bin", "approx_download_mb": 32.2,
             "state": 384, "layers": 4, "heads": 6, "planning_ram_bytes": GIB // 2},
    "base": {"filename": "ggml-base-q5_1.bin", "approx_download_mb": 59.7,
             "state": 512, "layers": 6, "heads": 8, "planning_ram_bytes": GIB},
    "small": {"filename": "ggml-small-q5_1.bin", "approx_download_mb": 190,
              "state": 768, "layers": 12, "heads": 12, "planning_ram_bytes": 2 * GIB},
}


class NewsHarnessError(Exception):
    """An actionable, user-facing error, not a Python traceback."""


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def confined_path(root, relative):
    """Reject traversal, absolute paths and symlinks escaping the output root."""
    root = Path(root).resolve()
    relative = Path(relative)
    # as_posix(): on Windows "\" is a separator; on POSIX a literal "\" stays and is rejected.
    # drive/root also rejects drive-relative names such as "C:x" on Windows.
    if relative.is_absolute() or relative.drive or relative.root or ".." in relative.parts or "\\" in relative.as_posix():
        raise NewsHarnessError("Ruta no permitida: use un nombre relativo dentro del espacio de trabajo.")
    result = (root / relative).resolve()
    try:
        result.relative_to(root)
    except ValueError:
        raise NewsHarnessError("Ruta no permitida: un enlace sale del espacio de trabajo.") from None
    return result


def write_new(path, content):
    """Create, or accept identical bytes. Never silently replace an existing file."""
    path = Path(path)
    data = content.encode("utf-8") if isinstance(content, str) else content
    if path.exists():
        if path.is_file() and path.read_bytes() == data:
            return False
        raise NewsHarnessError(f"Ya existe un archivo diferente: {path}. No se sobrescribió.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as f:
        f.write(data)
    return True


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise NewsHarnessError(f"No se pudo leer JSON {path}: {exc}") from None


def run(args, *, timeout=30, check=True, cwd=None):
    """Only an argument list, no shell; bounded lifetime and local subprocesses."""
    if not isinstance(args, (list, tuple)) or not args or not all(isinstance(x, str) for x in args):
        raise NewsHarnessError("Se requiere una lista de argumentos; no se aceptan comandos shell.")
    if not 0 < timeout <= 86400:
        raise NewsHarnessError("El límite de ejecución debe ser entre 1 y 86400 segundos.")
    env = {k: v for k, v in os.environ.items() if not k.startswith("WHISPER_")}
    # Nested kit workers inherit the outer owned group; otherwise their decoders
    # would survive an outer timeout in a new session. This marker is internal.
    own_group = os.name != "nt" and env.get("_NEWSHARNESS_OWNED_PROCESS_GROUP") != "1"
    if os.name != "nt":
        env["_NEWSHARNESS_OWNED_PROCESS_GROUP"] = "1"
    try:
        process = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, errors="replace", shell=False,
                                   start_new_session=own_group, cwd=cwd, env=env)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            if own_group:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            elif os.name == "nt":
                # The OCR worker may own a decoder. Terminate that tree too.
                taskkill = str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "taskkill.exe")
                try:
                    subprocess.run([taskkill, "/PID", str(process.pid), "/T", "/F"],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, timeout=10, shell=False)
                except (OSError, subprocess.TimeoutExpired):
                    process.kill()
            else:
                process.kill()
            process.communicate()
            raise
        p = subprocess.CompletedProcess(args, process.returncode, stdout, stderr)
    except FileNotFoundError:
        raise NewsHarnessError(f"No está instalado {args[0]}. Ejecute doctor y revise el plan.") from None
    except subprocess.TimeoutExpired:
        raise NewsHarnessError(f"{Path(args[0]).name} excedió {timeout}s; el original está intacto. Use una muestra menor.") from None
    if check and p.returncode:
        detail = (p.stderr or p.stdout)[-2000:].strip()
        raise NewsHarnessError(f"{Path(args[0]).name} terminó con código {p.returncode}: {detail}")
    return p


def parse_meminfo(text):
    values = {}
    for line in text.splitlines():
        match = re.match(r"^(\w+):\s+(\d+)\s+kB\s*$", line)
        if match:
            values[match[1]] = int(match[2]) * 1024
    return {"total_bytes": values.get("MemTotal"),
            "available_bytes": values.get("MemAvailable"),
            "method": "linux_memavailable" if "MemAvailable" in values else "unknown_available"}


def parse_vm_stat(text):
    page = re.search(r"page size of (\d+) bytes", text)
    if not page:
        return None
    counts = {}
    for label in ("Pages free", "Pages inactive", "Pages speculative"):
        match = re.search(re.escape(label) + r":\s*(\d+)\.", text)
        if not match:
            return None
        counts[label] = int(match[1])
    return sum(counts.values()) * int(page[1])


def constrain_memory(memory, limit, used):
    """Container limits matter more than host memory. Unknown stays unknown."""
    result = dict(memory)
    if isinstance(limit, int) and 0 < limit < 2 ** 60:
        total = result.get("total_bytes")
        if total is None or limit < total:
            result["total_bytes"] = limit
            available = max(0, limit - used) if isinstance(used, int) else None
            previous = result.get("available_bytes")
            result["available_bytes"] = min(previous, available) if previous is not None and available is not None else available
            result["method"] += "+cgroup"
    return result


def memory_info():
    unknown = {"total_bytes": None, "available_bytes": None, "method": "unknown"}
    try:
        if sys.platform.startswith("linux"):
            result = parse_meminfo(Path("/proc/meminfo").read_text(encoding="utf-8", errors="replace"))
            for cap, current in (("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory.current"),
                                 ("/sys/fs/cgroup/memory/memory.limit_in_bytes", "/sys/fs/cgroup/memory/memory.usage_in_bytes")):
                try:
                    limit = Path(cap).read_text(encoding="utf-8").strip()
                    if limit.isdigit():
                        result = constrain_memory(result, int(limit), int(Path(current).read_text(encoding="utf-8").strip()))
                        break
                except (OSError, ValueError):
                    pass
            return result
        if sys.platform == "darwin":
            total = int(run(["sysctl", "-n", "hw.memsize"], timeout=10).stdout.strip())
            available = parse_vm_stat(run(["vm_stat"], timeout=10).stdout)
            return {"total_bytes": total, "available_bytes": available,
                    "method": "macos_free_inactive_speculative_estimate"}
        if sys.platform == "win32":
            class MemoryStatus(ctypes.Structure):
                _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                    (n, ctypes.c_ulonglong) for n in ("totalPhys", "availPhys", "totalPage", "availPage", "totalVirtual", "availVirtual", "availExtended")]
            status = MemoryStatus()
            status.length = ctypes.sizeof(status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return {"total_bytes": status.totalPhys, "available_bytes": status.availPhys,
                        "method": "windows_globalmemorystatusex"}
    except (OSError, ValueError, NewsHarnessError, AttributeError):
        pass
    return unknown


def cpu_info():
    name, flags = platform.processor() or "unknown", []
    if sys.platform.startswith("linux"):
        try:
            text = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace")
            match = re.search(r"^(?:model name|Hardware)\s*:\s*(.+)$", text, re.M)
            if match:
                name = match[1]
            match = re.search(r"^(?:flags|Features)\s*:\s*(.+)$", text, re.M)
            if match:
                flags = match[1].split()
        except OSError:
            pass
    elif sys.platform == "darwin":
        try:
            name = run(["sysctl", "-n", "machdep.cpu.brand_string"], timeout=10).stdout.strip() or name
        except NewsHarnessError:
            pass
    cores = os.cpu_count()
    try:
        usable = len(os.sched_getaffinity(0))
    except AttributeError:
        usable = cores
    return {"name": name, "logical_cores": cores, "usable_logical_cores": usable, "flags": flags}


def tool_info(name, args):
    path = shutil.which(name)
    if not path:
        return {"found": False, "path": None, "version": None}
    try:
        p = run([path] + args, timeout=10, check=False)
        lines = (p.stdout + "\n" + p.stderr).strip().splitlines()
        return {"found": True, "path": path, "version": lines[0][:300] if lines else "unknown",
                "probe_exit_code": p.returncode}
    except NewsHarnessError as exc:
        return {"found": True, "path": path, "version": "unknown", "probe_error": str(exc)}


def available_languages(tesseract, tessdata=None):
    args = [tesseract, "--list-langs"]
    if tessdata:
        args += ["--tessdata-dir", str(tessdata)]
    output = run(args, timeout=15).stdout
    return [line.strip() for line in output.splitlines() if re.fullmatch(r"[a-zA-Z0-9_+-]+", line.strip())]


def doctor(workspace=None):
    disk_path = Path(workspace or Path.cwd()).expanduser().resolve()
    while not disk_path.exists():
        disk_path = disk_path.parent
    tools = {name: tool_info(name, [flag]) for name, flag in (
        ("tesseract", "--version"), ("ffmpeg", "-version"), ("whisper-cli", "--version"))}
    if tools["tesseract"]["found"]:
        try:
            tools["tesseract"]["languages"] = available_languages(tools["tesseract"]["path"])
        except NewsHarnessError as exc:
            tools["tesseract"]["language_probe_error"] = str(exc)
    optional = {}
    for import_name, package in (("pypdfium2", "pypdfium2"), ("PIL", "Pillow")):
        found = importlib.util.find_spec(import_name) is not None
        try:
            version = importlib.metadata.version(package) if found else None
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"
        optional[import_name] = {"found": found, "version": version}
    return {"kit_version": VERSION, "checked_at": utc_now(),
            "os": {"system": platform.system(), "version": platform.version(), "release": platform.release(),
                   "architecture": platform.machine(), "python": platform.python_version()},
            "cpu": cpu_info(), "memory": memory_info(),
            "disk": {"checked_path": str(disk_path), "free_bytes": shutil.disk_usage(disk_path).free},
            "tools": tools, "optional_python": optional, "network_used": False}


def setup_plan(report, quality="base", allow_restricted_tiny=False):
    if quality not in MODELS:
        raise NewsHarnessError("Modelo no admitido: elija base, small o tiny multilingüe Q5_1.")
    if quality == "tiny" and not allow_restricted_tiny:
        raise NewsHarnessError("tiny es un borrador restringido. Requiere --allow-restricted-tiny; no se elige automáticamente.")
    available = report["memory"]["available_bytes"]
    floor = MODELS[quality]["planning_ram_bytes"]
    memory_status = "unknown" if available is None else ("provisional_ok" if available >= floor else "insufficient_planning_headroom")
    disk_floor = int(MODELS[quality]["approx_download_mb"] * 1_000_000) + 256 * 1024 ** 2
    disk_status = "provisional_ok" if report["disk"]["free_bytes"] >= disk_floor else "insufficient_planning_headroom"
    missing = [name for name, value in report["tools"].items() if not value["found"]]
    if "spa" not in report["tools"].get("tesseract", {}).get("languages", []):
        missing.append("spa.traineddata (tessdata_fast)")
    if not report["optional_python"]["pypdfium2"]["found"]:
        missing.append("pypdfium2 (solo PDF)")
    if not report["optional_python"]["PIL"]["found"]:
        missing.append("Pillow (validación de imágenes y PDF escaneado)")
    cores = report["cpu"].get("usable_logical_cores") or report["cpu"].get("logical_cores") or 1
    return {"selected_model": MODELS[quality]["filename"], "quality": quality,
            "approx_model_download_mb": MODELS[quality]["approx_download_mb"],
            "device": "cpu", "threads": max(1, min(4, cores - 1)),
            "memory_status": memory_status, "planning_available_ram_floor_bytes": floor,
            "disk_status": disk_status, "planning_free_disk_floor_bytes": disk_floor,
            "memory_rule_is_measured_requirement": False, "missing": missing,
            "ocr_model_policy": "Preferir spa.traineddata fijado en workspace/tessdata; un idioma del sistema no demuestra que sea tessdata_fast.",
            "needs_local_calibration": True, "silent_downgrade": False,
            "notes": ["Los MB del modelo no son RAM ni tamaño total de instalación.",
                      "Los márgenes de RAM son reglas conservadoras del kit, no requisitos medidos del proveedor.",
                      "Calibre con 60–120 segundos representativos; no hay garantía de velocidad o precisión.",
                      "El margen de disco no incluye todo audio futuro: WAV mono 16 kHz/16 bit ocupa unos 115 MB por hora, además del original.",
                      "No se instala software ni se descarga nada con plan. La instalación nativa requiere revisión por plataforma.",
                      "OCR y audio son locales; el agente anfitrión puede usar un modelo en la nube."]}


def expect_object(value, allowed, required, label):
    if not isinstance(value, dict):
        raise NewsHarnessError(f"{label} debe ser un objeto JSON.")
    extra, missing = set(value) - set(allowed), set(required) - set(value)
    if extra or missing:
        raise NewsHarnessError(f"Campos inválidos en {label}: desconocidos={sorted(extra)}, faltantes={sorted(missing)}. No incluya claves o contraseñas.")


def text_value(value, label, max_length=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > max_length or "\x00" in value:
        raise NewsHarnessError(f"{label} debe ser texto no vacío (máximo {max_length} caracteres).")


def strings(value, label):
    if not isinstance(value, list) or len(value) > 200:
        raise NewsHarnessError(f"{label} debe ser una lista de hasta 200 textos.")
    for item in value:
        text_value(item, label)


def url_value(value, label):
    text_value(value, label)
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username or parsed.password:
        raise NewsHarnessError(f"{label} debe ser una URL pública http(s), sin credenciales.")
    if any(re.search(r"token|secret|password|api.?key|signature", key, re.I) for key, _ in urllib.parse.parse_qsl(parsed.query)):
        raise NewsHarnessError(f"{label} parece contener una credencial; quite los parámetros secretos.")


def date_value(value, label):
    text_value(value, label, 40)
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise NewsHarnessError(f"{label} requiere fecha ISO (AAAA-MM-DD o fecha y hora ISO).") from None


def validate_profile(profile):
    required = {"schema_version", "newsroom", "journalist", "country", "language", "timezone", "privacy", "publication"}
    allowed = required | {"newsroom_url", "style", "topics", "source_policy", "bylines", "rules"}
    expect_object(profile, allowed, required, "perfil")
    if type(profile["schema_version"]) is not int or profile["schema_version"] != 1:
        raise NewsHarnessError("schema_version debe ser 1.")
    text_value(profile["newsroom"], "newsroom", 200)
    if not isinstance(profile["country"], str) or not re.fullmatch(r"[A-Z]{2}", profile["country"]):
        raise NewsHarnessError("country debe ser un código ISO de dos letras mayúsculas, por ejemplo AR o MX.")
    if profile["language"] not in ("es", "pt", "en"):
        raise NewsHarnessError("language debe ser es, pt o en en esta versión.")
    text_value(profile["timezone"], "timezone", 100)
    if not re.fullmatch(r"(?:[A-Za-z_+-]+/)+[A-Za-z_+-]+|UTC", profile["timezone"]) or ".." in profile["timezone"]:
        raise NewsHarnessError("timezone debe ser un nombre IANA, por ejemplo America/Mexico_City.")
    # The system timezone database is absent on some supported Windows hosts.
    try:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        ZoneInfo(profile["timezone"])
    except ZoneInfoNotFoundError:
        try:
            ZoneInfo("UTC")
        except ZoneInfoNotFoundError:
            pass  # structural validation only; never download tzdata here
        else:
            raise NewsHarnessError("timezone no se reconoce en la base IANA del sistema.") from None
    journalist = profile["journalist"]
    keys = {"name", "signature", "role", "section", "formats"}
    expect_object(journalist, keys | {"author_url"}, keys, "journalist")
    for key in keys - {"formats"}:
        text_value(journalist[key], f"journalist.{key}", 300)
    strings(journalist["formats"], "journalist.formats")
    if "author_url" in journalist:
        url_value(journalist["author_url"], "journalist.author_url")
    if "newsroom_url" in profile:
        url_value(profile["newsroom_url"], "newsroom_url")
    expect_object(profile["privacy"], {"allow_cloud_processing", "allow_public_archiving"}, {"allow_cloud_processing", "allow_public_archiving"}, "privacy")
    if any(type(value) is not bool for value in profile["privacy"].values()):
        raise NewsHarnessError("Las opciones de privacy deben ser booleanos; nunca autorizan publicación por sí mismas.")
    expect_object(profile["publication"], {"human_approval_required"}, {"human_approval_required"}, "publication")
    if profile["publication"]["human_approval_required"] is not True:
        raise NewsHarnessError("La revisión humana antes de publicar es obligatoria: human_approval_required=true.")
    if "style" in profile:
        expect_object(profile["style"], {"tone", "number_style", "date_style"}, set(), "style")
        for key, value in profile["style"].items():
            text_value(value, f"style.{key}")
    if "topics" in profile:
        strings(profile["topics"], "topics")
    if "source_policy" in profile:
        policy = profile["source_policy"]
        expect_object(policy, {"preferred_domains", "require_primary_source"}, {"preferred_domains", "require_primary_source"}, "source_policy")
        strings(policy["preferred_domains"], "source_policy.preferred_domains")
        if any(not re.fullmatch(r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}", domain) for domain in policy["preferred_domains"]):
            raise NewsHarnessError("preferred_domains contiene un dominio inválido (sin URL ni ruta).")
        if type(policy["require_primary_source"]) is not bool:
            raise NewsHarnessError("require_primary_source debe ser booleano.")
    for kind in ("bylines", "rules"):
        entries = profile.get(kind, [])
        if not isinstance(entries, list) or len(entries) > 200:
            raise NewsHarnessError(f"{kind} debe ser una lista de hasta 200 elementos.")
        for entry in entries:
            if kind == "bylines":
                req = {"title", "url", "consulted_at", "authorship_confirmed", "confidence"}
                expect_object(entry, req | {"published_at", "notes"}, req, "bylines[]")
                text_value(entry["title"], "bylines.title")
                url_value(entry["url"], "bylines.url")
                if type(entry["authorship_confirmed"]) is not bool or entry["confidence"] not in ("high", "medium", "low"):
                    raise NewsHarnessError("bylines requiere authorship_confirmed booleano y confidence high/medium/low.")
                if "published_at" in entry:
                    date_value(entry["published_at"], "bylines.published_at")
                if "notes" in entry:
                    text_value(entry["notes"], "bylines.notes")
            else:
                req = {"rule", "type", "source_urls", "consulted_at", "approval"}
                expect_object(entry, req | {"evidence_limit"}, req, "rules[]")
                text_value(entry["rule"], "rules.rule")
                if entry["type"] not in ("explicit", "inferred", "preference") or entry["approval"] not in ("pending", "approved", "rejected"):
                    raise NewsHarnessError("rules requiere type explicit/inferred/preference y approval pending/approved/rejected.")
                strings(entry["source_urls"], "rules.source_urls")
                for url in entry["source_urls"]:
                    url_value(url, "rules.source_urls")
                if entry["type"] in ("explicit", "inferred") and not entry["source_urls"]:
                    raise NewsHarnessError("Una regla oficial o inferida requiere fuentes; no invente evidencia.")
                if "evidence_limit" in entry:
                    text_value(entry["evidence_limit"], "rules.evidence_limit")
            date_value(entry["consulted_at"], f"{kind}.consulted_at")
    return profile


def initialize(workspace, profile_path):
    profile = validate_profile(read_json(profile_path))
    root = Path(workspace).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    changed = write_new(confined_path(root, "profile.json"), json_text(profile))
    for name in ("originals", "output", "models", "tessdata"):
        confined_path(root, name).mkdir(exist_ok=True)
    write_new(confined_path(root, ".newsharness-workspace.json"), json_text({"schema_version": 1, "kit_version": VERSION}))
    return {"workspace": str(root), "profile": "profile.json", "created": changed,
            "network_used": False, "message": "Perfil validado. Los originales se conservan y nada se publica."}


def workspace_root(workspace):
    root = Path(workspace).expanduser().resolve()
    marker = confined_path(root, ".newsharness-workspace.json")
    if not marker.is_file():
        raise NewsHarnessError("Espacio no inicializado. Ejecute init --workspace DIR --profile FILE primero.")
    validate_profile(read_json(confined_path(root, "profile.json")))
    return root


def local_input(path, suffixes=None):
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise NewsHarnessError(f"No existe el archivo local: {path}")
    if suffixes and path.suffix.lower() not in suffixes:
        raise NewsHarnessError(f"Formato no admitido: {path.suffix}. Admitidos: {', '.join(sorted(suffixes))}.")
    return path


def preserve_original(root, source):
    digest = sha256(source)
    target = confined_path(root, Path("originals") / (digest + source.suffix.lower()))
    target.parent.mkdir(exist_ok=True)
    if target.exists():
        if sha256(target) != digest:
            raise NewsHarnessError("La copia de un original cambió. Revise originals antes de continuar.")
    else:
        with source.open("rb") as src, target.open("xb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
        if sha256(target) != digest:
            target.unlink()
            raise NewsHarnessError("El original cambió mientras se copiaba. Vuelva a intentarlo cuando esté estable.")
    return target, digest


def new_job(root, kind):
    parent = confined_path(root, "output")
    parent.mkdir(exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f"{kind}-", dir=parent))


def tool_required(name):
    path = shutil.which(name)
    if not path:
        raise NewsHarnessError(f"Falta {name}. Ejecute doctor y revise docs/instalacion.md; el kit no instala binarios no verificados.")
    return path


def tessdata_path(root, requested):
    if requested:
        candidate = Path(requested).expanduser().resolve()
        try:
            relative = candidate.relative_to(root)
        except ValueError:
            raise NewsHarnessError("--tessdata-dir debe estar dentro del workspace para no modificar ni usar rutas globales por accidente.") from None
        candidate = confined_path(root, relative)
        if not candidate.is_dir():
            raise NewsHarnessError("--tessdata-dir no existe.")
        return candidate
    automatic = confined_path(root, "tessdata")
    return automatic if (automatic / "spa.traineddata").is_file() else None


def ocr_image(image, base, language, tessdata, timeout, frame_index=0):
    executable = tool_required("tesseract")
    if not re.fullmatch(r"[a-z]{3}(?:\+[a-z]{3})*", language):
        raise NewsHarnessError("Idioma OCR inválido: use spa, eng o spa+eng, no opciones de comando.")
    missing = set(language.split("+")) - set(available_languages(executable, tessdata))
    if missing:
        raise NewsHarnessError(f"Falta el idioma Tesseract {', '.join(sorted(missing))}. Coloque el modelo verificado en workspace/tessdata; no se sustituirá por inglés.")
    # Tesseract accepts file-list input: never give it original untrusted bytes.
    # Fully decode a bounded raster and re-encode pixels into a fresh local PNG.
    try:
        from PIL import Image
    except ImportError:
        raise NewsHarnessError("OCR de imágenes requiere Pillow para validar y normalizar archivos; no se enviarán bytes sin validar a Tesseract.") from None
    normalized_path = Path(str(base) + ".input.png")
    if normalized_path.exists():
        raise NewsHarnessError("La imagen normalizada ya existe; use una carpeta de trabajo nueva.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(image) as raster:
                if raster.format not in ("PNG", "JPEG", "TIFF", "BMP", "WEBP", "PPM"):
                    raise NewsHarnessError("Formato raster no admitido por la normalización segura.")
                raster.seek(frame_index)
                if raster.width <= 0 or raster.height <= 0 or raster.width * raster.height > 50_000_000:
                    raise NewsHarnessError("La imagen supera el límite de 50 millones de píxeles; prepare una copia reducida.")
                raster.load()
                normalized = raster.convert("RGB")
                try:
                    normalized.info.clear()
                    with normalized_path.open("xb") as target:
                        normalized.save(target, format="PNG")
                finally:
                    normalized.close()
    except NewsHarnessError:
        raise
    except Exception as exc:
        raise NewsHarnessError(f"Imagen inválida o no admitida: {exc}. No se aceptan listas de archivos disfrazadas de imagen.") from None
    command = [executable, str(normalized_path), str(base), "-l", language, "--oem", "1"]
    if tessdata:
        command += ["--tessdata-dir", str(tessdata)]
    command += ["txt", "tsv"]
    run(command, timeout=timeout)
    return Path(str(base) + ".txt").read_text(encoding="utf-8")


def ocr_document(source, job, language, tessdata, max_pages, page_timeout):
    if not job.is_dir() or any(job.iterdir()):
        raise NewsHarnessError("El trabajo OCR debe usar una carpeta vacía nueva; no se seguirán archivos ni enlaces preexistentes.")
    pages = []
    if source.suffix.lower() != ".pdf":
        try:
            from PIL import Image
            with Image.open(source) as raster:
                frame_count = getattr(raster, "n_frames", 1)
        except Exception as exc:
            raise NewsHarnessError(f"Imagen inválida o falta Pillow: {exc}. Solo se procesan imágenes decodificables.") from None
        if frame_count > max_pages:
            raise NewsHarnessError(f"La imagen contiene {frame_count} páginas; excede --max-pages {max_pages}.")
        for index in range(frame_count):
            stem = f"page-{index + 1:04d}"
            text = ocr_image(source, job / stem, language, tessdata, page_timeout, index)
            pages.append({"page": index + 1, "method": "tesseract", "text": text,
                          "coordinates_confidence": stem + ".tsv", "normalized_page": stem + ".input.png"})
    else:
        try:
            import pypdfium2 as pdfium
        except ImportError:
            raise NewsHarnessError("PDF requiere pypdfium2 en un entorno local revisado. Tesseract no puede leer PDF directamente.") from None
        try:
            with pdfium.PdfDocument(str(source)) as pdf:
                if len(pdf) > max_pages:
                    raise NewsHarnessError(f"El PDF tiene {len(pdf)} páginas; límite {max_pages}. Divídalo o aumente --max-pages explícitamente (máximo 2000).")
                for index in range(len(pdf)):
                    page = pdf[index]
                    try:
                        textpage = page.get_textpage()
                        try:
                            text = textpage.get_text_range()
                        finally:
                            textpage.close()
                        if text.strip():
                            pages.append({"page": index + 1, "method": "existing_text", "text": text,
                                          "warning": "Capa de texto existente: no garantiza cobertura de imágenes ni fidelidad al original visual."})
                            continue
                        if importlib.util.find_spec("PIL") is None:
                            raise NewsHarnessError("Una página escaneada requiere Pillow además de pypdfium2 para la imagen local.")
                        width, height = page.get_size()
                        if width * height * (300 / 72) ** 2 > 50_000_000:
                            raise NewsHarnessError("Página demasiado grande para renderizar a 300 dpi con seguridad. Prepare una copia reducida, sin borrar el original.")
                        stem = f"page-{index + 1:04d}"
                        image_path = job / (stem + ".png")
                        bitmap = page.render(scale=300 / 72)
                        try:
                            image = bitmap.to_pil()
                            image.save(image_path)
                            image.close()
                        finally:
                            bitmap.close()
                        text = ocr_image(image_path, job / stem, language, tessdata, page_timeout)
                        pages.append({"page": index + 1, "method": "tesseract", "text": text,
                                      "coordinates_confidence": stem + ".tsv", "rendered_page": stem + ".png"})
                    finally:
                        page.close()
        except NewsHarnessError:
            raise
        except Exception as exc:
            raise NewsHarnessError(f"No se pudo procesar el PDF: {exc}. Revise si está dañado o cifrado.") from None
    write_new(job / "pages.json", json_text(pages))
    write_new(job / "text.txt", "\n\n".join(f"--- Página {p['page']} ({p['method']}) ---\n{p['text']}" for p in pages))
    return pages


def ocr(args):
    root = workspace_root(args.workspace)
    source = local_input(args.input, {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp", ".pnm", ".ppm", ".pgm"})
    tessdata = tessdata_path(root, args.tessdata_dir)
    if tessdata and "spa" in args.lang.split("+"):
        verify_local_artifact(tessdata / "spa.traineddata")
    snapshot, digest = preserve_original(root, source)
    job = new_job(root, "ocr")
    start = time.monotonic()
    command = [sys.executable, str(Path(__file__).resolve()), "_ocr-worker", "--workspace", str(root),
               "--input", str(snapshot), "--job", job.name, "--lang", args.lang,
               "--max-pages", str(args.max_pages), "--page-timeout", str(args.page_timeout)]
    if tessdata:
        command += ["--tessdata-dir", str(tessdata)]
    try:
        run(command, timeout=args.timeout)
    except NewsHarnessError as exc:
        write_new(job / "failure.json", json_text({"status": "incomplete", "error": str(exc), "source_sha256": digest}))
        raise
    pages = read_json(job / "pages.json")
    provenance = {"kit_version": VERSION, "operation": "ocr", "status": "draft_needs_human_review",
                  "source_filename": source.name, "source_sha256": digest,
                  "original_copy": str(snapshot.relative_to(root)), "created_at": utc_now(),
                  "elapsed_seconds": round(time.monotonic() - start, 3), "language": args.lang,
                  "page_count": len(pages), "network_used": False,
                  "tesseract": tool_info("tesseract", ["--version"]),
                  "tessdata": {"source": "workspace" if tessdata else "system_unpinned",
                               "spa_sha256": sha256(tessdata / "spa.traineddata") if tessdata and (tessdata / "spa.traineddata").is_file() else None},
                  "review": "Coteje nombres, cifras y citas con el original. El TSV conserva coordenadas y confianza técnica, no certeza factual."}
    write_new(job / "provenance.json", json_text(provenance))
    return {"output": str(job), **provenance}


def validate_model(path, quality):
    if quality not in MODELS:
        raise NewsHarnessError("Calidad desconocida: elija tiny, base o small.")
    path = local_input(path, {".bin"})
    spec = MODELS[quality]
    if path.name != spec["filename"]:
        raise NewsHarnessError(f"El modelo no coincide con --quality {quality}. Se requiere {spec['filename']} multilingüe; no se aceptan .en ni una calidad distinta.")
    with path.open("rb") as f:
        header = f.read(48)
    if len(header) != 48:
        raise NewsHarnessError("Modelo incompleto: cabecera GGML ausente.")
    fields = struct.unpack("<12i", header)
    magic, vocab, audio_ctx, audio_state, audio_head, audio_layer, text_ctx, text_state, text_head, text_layer, mels, ftype = fields
    if magic != 0x67676D6C or vocab != 51865 or mels != 80 or ftype % 1000 != 9:
        raise NewsHarnessError("El archivo no es el modelo Whisper GGML multilingüe Q5_1 esperado. No basta con renombrarlo.")
    if (audio_state, text_state, audio_layer, text_layer, audio_head, text_head) != (
            spec["state"], spec["state"], spec["layers"], spec["layers"], spec["heads"], spec["heads"]):
        raise NewsHarnessError("La arquitectura del modelo no coincide con la calidad seleccionada.")
    if audio_ctx != 1500 or text_ctx != 448 or path.stat().st_size < 1_000_000:
        raise NewsHarnessError("Modelo incompleto o contexto incompatible; obtenga el artefacto verificado.")
    verify_local_artifact(path)
    return path


def verify_local_artifact(path):
    manifest = read_json(ROOT / "config" / "toolchain.lock.json")
    artifacts = [a for a in manifest.get("artifacts", []) if a.get("filename") == path.name]
    if len(artifacts) != 1:
        raise NewsHarnessError("No hay identidad verificada única para este modelo en el manifiesto.")
    artifact = validate_artifact(artifacts[0])
    if sha256(path) != artifact["sha256"]:
        raise NewsHarnessError("El SHA256 del modelo no coincide con el artefacto oficial fijado. No se ejecutará.")
    return artifact


def wav_is_digital_silence(path):
    with wave.open(str(path), "rb") as wav:
        if wav.getsampwidth() != 2 or wav.getnchannels() != 1:
            raise NewsHarnessError("La conversión no produjo PCM mono de 16 bits.")
        while True:
            chunk = wav.readframes(65536)
            if not chunk:
                return True
            if chunk.strip(b"\x00"):
                return False


def whisper_command(binary, model, audio, output_base, language, threads, vad_model=None, word_json=False):
    if not re.fullmatch(r"[a-z]{2,3}", language):
        raise NewsHarnessError("Idioma de audio inválido: use es, pt o un código admitido por Whisper.")
    if type(threads) is not int or not 1 <= threads <= 64:
        raise NewsHarnessError("threads debe estar entre 1 y 64.")
    command = [str(binary), "--model", str(model), "--file", str(audio), "--language", language,
               "--threads", str(threads), "--no-gpu", "--output-txt", "--output-srt", "--output-json",
               "--output-file", str(output_base)]
    if word_json:
        # JSON completo: segmentos con tokens y sus offsets, para subtítulos por palabra.
        command.append("--output-json-full")
    if vad_model:
        command += ["--vad", "--vad-model", str(vad_model)]
    return command


def transcribe(args):
    root = workspace_root(args.workspace)
    if args.quality == "tiny" and not args.allow_restricted_tiny:
        raise NewsHarnessError("tiny solo genera un borrador restringido; requiere --allow-restricted-tiny.")
    source = local_input(args.input, {".wav", ".mp3", ".m4a", ".mp4", ".aac", ".flac", ".ogg", ".opus", ".webm", ".mov", ".mkv"})
    model = validate_model(args.model, args.quality)
    ffmpeg, whisper = tool_required("ffmpeg"), tool_required("whisper-cli")
    help_output = run([whisper, "--help"], timeout=15, check=False)
    help_text = help_output.stdout + help_output.stderr
    word_json = bool(getattr(args, "word_timestamps", False))
    for required in ("--no-gpu", "--output-srt", "--output-json") + (("--output-json-full",) if word_json else ()):
        if required not in help_text:
            raise NewsHarnessError(f"whisper-cli no documenta {required}. Use una versión revisada compatible; no se ejecutará con opciones supuestas.")
    vad = None
    auto_vad = confined_path(root, "models/ggml-silero-v6.2.0.bin")
    chosen_vad = args.vad_model or (str(auto_vad) if auto_vad.is_file() else None)
    if chosen_vad:
        if "--vad-model" not in help_text or "--vad" not in help_text:
            raise NewsHarnessError("Este whisper-cli no admite VAD. Actualice con un binario revisado o quite --vad-model explícitamente.")
        vad = local_input(chosen_vad, {".bin"})
        if vad.name != "ggml-silero-v6.2.0.bin":
            raise NewsHarnessError("VAD requiere ggml-silero-v6.2.0.bin verificado en esta versión.")
        verify_local_artifact(vad)
    elif not args.allow_no_vad:
        raise NewsHarnessError("Falta VAD local. Use fetch --artifact whisper-vad-silero-v6.2.0 --approve-download, o acepte explícitamente mayor riesgo con --allow-no-vad. No se descargó nada.")
    threads = args.threads or max(1, min(4, (os.cpu_count() or 1) - 1))
    # Validate language/threads before creating a job or invoking a decoder.
    whisper_command(whisper, model, source, root, args.language, threads, vad, word_json)
    snapshot, digest = preserve_original(root, source)
    job = new_job(root, "calibration" if args.command == "calibrate" else "transcription")
    audio = job / "audio-16k-mono.wav"
    start = time.monotonic()
    demuxers = {".wav": "wav", ".mp3": "mp3", ".m4a": "mov", ".mp4": "mov", ".mov": "mov", ".aac": "aac",
                ".flac": "flac", ".ogg": "ogg", ".opus": "ogg", ".webm": "matroska", ".mkv": "matroska"}
    # Force the expected demuxer: a disguised concat/playlist must not read other
    # local files. Also disable external references in QuickTime containers.
    demuxer = demuxers[source.suffix.lower()]
    command = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-protocol_whitelist", "file,pipe", "-f", demuxer]
    if demuxer == "mov":
        command += ["-enable_drefs", "0", "-use_absolute_path", "0"]
    command += ["-i", str(snapshot), "-map", "0:a:0", "-vn"]
    if args.sample_seconds:
        command += ["-t", str(args.sample_seconds)]
    command += ["-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", "-f", "wav", "-n", str(audio)]
    try:
        run(command, timeout=min(args.timeout, 1800))
        with wave.open(str(audio), "rb") as wav:
            duration = wav.getnframes() / wav.getframerate()
        if duration <= 0:
            raise NewsHarnessError("El archivo no contiene audio utilizable.")
        if args.command == "calibrate" and duration < 60:
            raise NewsHarnessError("La muestra disponible dura menos de 60 segundos; elija 60–120 segundos representativos para calibrar.")
        digital_silence = wav_is_digital_silence(audio)
        inference_start = time.monotonic()
        remaining = max(1, args.timeout - int(inference_start - start))
        if digital_silence:
            write_new(job / "transcript.txt", "")
            write_new(job / "transcript.srt", "")
            write_new(job / "transcript.json", json_text({"transcription": [], "status": "digital_silence_no_inference"}))
        else:
            run(whisper_command(whisper, model, audio, job / "transcript", args.language, threads, vad, word_json), timeout=remaining)
        for suffix in (".txt", ".srt", ".json"):
            if not (job / ("transcript" + suffix)).is_file():
                raise NewsHarnessError(f"whisper-cli no generó transcript{suffix}; revise la versión. No hay entrega completa.")
        inference_elapsed = time.monotonic() - inference_start
        transcript_json = read_json(job / "transcript.json")
        if not isinstance(transcript_json, dict) or not isinstance(transcript_json.get("transcription"), list):
            raise NewsHarnessError("La salida JSON de whisper-cli no tiene el esquema esperado; no se marcará como completa.")
    except NewsHarnessError as exc:
        write_new(job / "failure.json", json_text({"status": "incomplete", "error": str(exc), "source_sha256": digest}))
        raise
    elapsed = time.monotonic() - start
    report = {"kit_version": VERSION, "status": "draft_needs_human_review", "created_at": utc_now(),
              "source_filename": source.name, "source_sha256": digest, "original_copy": str(snapshot.relative_to(root)),
              "model_filename": model.name, "model_sha256": sha256(model),
              "model_authenticity": "header_and_sha256_verified_against_pinned_manifest",
              "quality": args.quality, "device": "cpu", "threads": threads, "language": args.language,
              "vad_enabled": bool(vad), "vad_model_sha256": sha256(vad) if vad else None,
              "digital_silence": digital_silence, "asr_inference_run": not digital_silence,
              "no_speech_detected": not bool(transcript_json["transcription"]),
              "audio_seconds": round(duration, 3), "elapsed_seconds": round(elapsed, 3),
              "inference_seconds": round(inference_elapsed, 3), "real_time_factor_total": round(elapsed / duration, 4),
              "peak_memory_bytes": None, "memory_measurement_note": "No se midió el pico de memoria; no extrapolar RAM del tamaño del modelo.",
              "is_calibration_sample": bool(args.sample_seconds), "network_used": False,
              "calibration_usable": bool(args.sample_seconds) and duration >= 60 and bool(transcript_json["transcription"]),
              "tools": {"ffmpeg": tool_info("ffmpeg", ["-version"]), "whisper-cli": tool_info("whisper-cli", ["--version"])},
              "warnings": ["Borrador: escuche y compruebe citas, nombres y números. Whisper puede inventar texto, especialmente en silencio.",
                           "Los tiempos no identifican hablantes; no hay diarización garantizada.",
                           "VAD activo no elimina todas las alucinaciones." if vad else "VAD no activado: proporcione un modelo VAD local compatible para reducir silencios."]}
    write_new(job / "provenance.json", json_text(report))
    return {"output": str(job), **report}


def validate_artifact(artifact):
    required = {"id", "url", "sha256", "revision", "filename", "destination", "max_bytes", "license", "source"}
    expect_object(artifact, required | {"size_bytes", "verified_at"}, required, "artifact")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,100}", artifact["id"]):
        raise NewsHarnessError("ID de artefacto inválido.")
    if not re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"] or ""):
        raise NewsHarnessError("Falta SHA256 verificado; no se descargará.")
    if not re.fullmatch(r"[0-9a-f]{40,64}", artifact["revision"] or ""):
        raise NewsHarnessError("Falta revisión inmutable verificada; no se descargará.")
    url = urllib.parse.urlsplit(artifact["url"])
    if url.scheme != "https" or url.hostname not in ("huggingface.co", "raw.githubusercontent.com") or url.username or url.password or url.query or url.fragment:
        raise NewsHarnessError("Solo se admiten URLs HTTPS oficiales fijadas, sin credenciales ni parámetros.")
    if artifact["revision"] not in url.path.split("/"):
        raise NewsHarnessError("La URL no fija la revisión declarada.")
    official = (url.hostname == "huggingface.co" and url.path.startswith(("/ggerganov/whisper.cpp/resolve/", "/ggml-org/whisper-vad/resolve/"))) or (
        url.hostname == "raw.githubusercontent.com" and url.path.startswith("/tesseract-ocr/tessdata_fast/"))
    if not official:
        raise NewsHarnessError("El repositorio no pertenece a las fuentes oficiales revisadas de este manifiesto.")
    if Path(artifact["filename"]).name != artifact["filename"] or not re.fullmatch(r"[A-Za-z0-9._-]+", artifact["filename"]):
        raise NewsHarnessError("Nombre de archivo inseguro.")
    if artifact["destination"] not in ("models", "tessdata") or not artifact["filename"].endswith((".bin", ".traineddata")):
        raise NewsHarnessError("El descargador solo acepta datos de modelos, nunca ejecutables o instaladores.")
    if type(artifact["max_bytes"]) is not int or not 1 <= artifact["max_bytes"] <= 2 * GIB:
        raise NewsHarnessError("max_bytes debe acotar el tamaño de la descarga.")
    return artifact


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        url = urllib.parse.urlsplit(newurl)
        host = url.hostname or ""
        allowed = host in ("huggingface.co", "raw.githubusercontent.com", "cdn-lfs.huggingface.co", "cdn-lfs-us-1.huggingface.co") or host.endswith(".hf.co")
        if url.scheme != "https" or not allowed or url.username or url.password:
            raise NewsHarnessError("Redirección de descarga no admitida; no se contactó el destino.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_artifact(workspace, artifact_id, approve=False):
    if not approve:
        raise NewsHarnessError("Descargar requiere autorización explícita: --approve-download. Solo baja el modelo fijado; nunca envía documentos.")
    root = workspace_root(workspace)
    manifest = read_json(ROOT / "config" / "toolchain.lock.json")
    candidates = [a for a in manifest.get("artifacts", []) if a.get("id") == artifact_id]
    if len(candidates) != 1:
        raise NewsHarnessError("Artefacto ausente o ambiguo en el manifiesto verificado. No se usará una URL o hash supuesto.")
    artifact = validate_artifact(candidates[0])
    target = confined_path(root, Path(artifact["destination"]) / artifact["filename"])
    target.parent.mkdir(exist_ok=True)
    if target.exists():
        if sha256(target) != artifact["sha256"]:
            raise NewsHarnessError("Ya existe un modelo con otro SHA256; no se sobrescribió.")
        return {"artifact": artifact_id, "path": str(target), "downloaded": False, "sha256_verified": True}
    if shutil.disk_usage(root).free < artifact["max_bytes"] + 50 * 1024 ** 2:
        raise NewsHarnessError("Espacio libre insuficiente para descargar y verificar el modelo.")
    fd, temp_name = tempfile.mkstemp(prefix=".download-", dir=target.parent)
    temp = Path(temp_name)
    start = time.monotonic()
    try:
        opener = urllib.request.build_opener(SafeRedirect)
        req = urllib.request.Request(artifact["url"], headers={"User-Agent": f"newsharness-kit/{VERSION}"})
        digest, count = hashlib.sha256(), 0
        with os.fdopen(fd, "wb") as dest, opener.open(req, timeout=30) as response:
            while True:
                if time.monotonic() - start > 600:
                    raise NewsHarnessError("La descarga excedió 10 minutos; se eliminó el archivo parcial.")
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                count += len(chunk)
                if count > artifact["max_bytes"]:
                    raise NewsHarnessError("El artefacto supera el tamaño permitido; descarga cancelada.")
                digest.update(chunk)
                dest.write(chunk)
        if digest.hexdigest() != artifact["sha256"]:
            raise NewsHarnessError("SHA256 distinto del manifiesto: archivo rechazado y eliminado.")
        if "size_bytes" in artifact and count != artifact["size_bytes"]:
            raise NewsHarnessError("El tamaño no coincide con el artefacto fijado.")
        # Atomic no-clobber publication on the same filesystem; no second full
        # copy and no partial final name on disk-full or cancellation. Unsupported
        # filesystems fail safely instead of falling back to an unsafe overwrite.
        os.link(temp, target)
        return {"artifact": artifact_id, "path": str(target), "downloaded": True,
                "bytes": count, "sha256_verified": True, "revision": artifact["revision"]}
    except (OSError, ValueError) as exc:
        raise NewsHarnessError(f"No se pudo descargar el modelo: {exc}. El original no se modificó.") from None
    finally:
        temp.unlink(missing_ok=True)


def install_skills(project, agent):
    destinations = {"codex": (".agents/skills", "AGENTS.md"), "claude": (".claude/skills", "CLAUDE.md"),
                    "opencode": (".opencode/skills", "AGENTS.md")}
    if agent not in destinations:
        raise NewsHarnessError("Agente no admitido.")
    root = Path(project).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    skill_dir, bridge_name = destinations[agent]
    names, skills, kit = kit_sources()
    copies = [(src, confined_path(root, Path(skill_dir) / rel)) for rel, src in skills.items()]
    copies += [(src, confined_path(root, Path(".newsharness-kit") / rel)) for rel, src in kit.items()]
    bridge = ROOT / "adapters" / agent / bridge_name
    manual_merge = False
    if bridge.is_file():
        dest = confined_path(root, bridge_name)
        if dest.exists() and dest.read_bytes() != bridge.read_bytes():
            dest = confined_path(root, f"NEWSHARNESS-{agent.upper()}.md")
            manual_merge = True
        copies.append((bridge, dest))
    # Preflight all conflicts before writing any file.
    for src, dest in copies:
        if dest.exists() and (not dest.is_file() or dest.read_bytes() != src.read_bytes()):
            raise NewsHarnessError(f"Instalación detenida: {dest} ya existe y es diferente. No se sobrescribió configuración.")
    created = sum(write_new(dest, src.read_bytes()) for src, dest in copies)
    return {"project": str(root), "agent": agent, "skills": names,
            "created_files": created, "manual_bridge_merge_required": manual_merge,
            "runtime": ".newsharness-kit/scripts/newsharness.py", "network_used": False,
            "warning": "La copia no demuestra compatibilidad end-to-end con una versión concreta del agente. Reinicie o recargue y compruebe descubrimiento."}


KIT_FILES = ("AGENTS.md", "README.md", "INSTALAR.md", "LICENSE", "THIRD_PARTY_NOTICES.md")
KIT_DIRS = ("scripts", "config", "docs", "examples", "skills", "adapters", "tests")
GLOBAL_KIT = ".newsharness-kit"
GLOBAL_MANIFEST = ".newsharness-install.json"


def global_skill_root(agent, home):
    """User-level discovery folder of each agent. Never the agent's global instructions file."""
    env = os.environ
    if agent == "claude":
        return home / ".claude" / "skills"
    if agent == "codex":
        return (Path(env["CODEX_HOME"]).expanduser() if env.get("CODEX_HOME") else home / ".codex") / "skills"
    if agent == "opencode":
        base = Path(env["XDG_CONFIG_HOME"]).expanduser() if env.get("XDG_CONFIG_HOME") else home / ".config"
        return base / "opencode" / "skills"
    raise NewsHarnessError("Agente no admitido.")


def kit_sources():
    sources = sorted((ROOT / "skills").glob("newsharness-*/SKILL.md"))
    if not sources:
        raise NewsHarnessError("No se encontraron los skills canónicos. Ejecute el instalador desde la carpeta original del kit.")
    skills, kit = {}, {}
    for skill in sources:
        for path in sorted(skill.parent.rglob("*")):
            if path.is_symlink():
                raise NewsHarnessError("El paquete contiene un enlace; revíselo antes de instalar.")
            if path.is_file() and "__pycache__" not in path.parts:
                skills[path.relative_to(ROOT / "skills").as_posix()] = path
    for directory in KIT_DIRS:
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and not path.is_symlink():
                kit[path.relative_to(ROOT).as_posix()] = path
    for filename in KIT_FILES:
        path = ROOT / filename
        if path.is_file() and not path.is_symlink():
            kit[filename] = path
    return [p.parent.name for p in sources], skills, kit


def replace_file(path, data):
    """Write through a temporary sibling and an atomic rename; used only for files the manifest proves unmodified."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.newsharness-tmp")
    temp.unlink(missing_ok=True)
    with temp.open("xb") as f:
        f.write(data)
    os.replace(temp, path)


def install_global(agent, update=False, uninstall=False, home=None):
    """Install the kit once in ~/.newsharness-kit and the skills in the agent's user-level folder.

    A manifest with the SHA256 of every installed file lets --update replace and
    --uninstall remove only what the kit wrote and the user did not modify."""
    home = Path(home).expanduser().resolve() if home else Path.home().resolve()
    kit_root = home / GLOBAL_KIT
    skill_root = global_skill_root(agent, home).resolve()
    manifest_path = kit_root / GLOBAL_MANIFEST
    manifest = read_json(manifest_path) if manifest_path.is_file() else {"schema_version": 1, "kit_files": {}, "agents": {}}
    if uninstall:
        return uninstall_global(agent, manifest, manifest_path, kit_root, skill_root)
    names, skills, kit = kit_sources()
    if kit_root.resolve() == ROOT.resolve():
        raise NewsHarnessError("Ejecute el instalador desde la carpeta descomprimida, no desde la copia global.")
    previous_agent = manifest["agents"].get(agent, {}).get("files", {})
    plan = [(kit_root, rel, src, manifest["kit_files"].get(rel)) for rel, src in kit.items()]
    plan += [(skill_root, rel, src, previous_agent.get(rel)) for rel, src in skills.items()]
    writes, conflicts = [], []
    for root, rel, src, recorded in plan:
        dest = confined_path(root, rel)
        data = src.read_bytes()
        if not dest.exists():
            writes.append((dest, data, False))
        elif not dest.is_file():
            conflicts.append(str(dest))
        elif dest.read_bytes() == data:
            continue
        elif update and recorded and sha256(dest) == recorded:
            writes.append((dest, data, True))
        else:
            conflicts.append(str(dest))
    # Files of the previous version that disappeared from the new one: removable only if unmodified.
    stale = []
    if update:
        for root, old, new in ((kit_root, manifest["kit_files"], kit), (skill_root, previous_agent, skills)):
            for rel, digest in old.items():
                dest = confined_path(root, rel)
                if rel not in new and dest.is_file() and sha256(dest) == digest:
                    stale.append(dest)
    if conflicts:
        hint = "" if update else " Si es una versión anterior de NewsHarness, use --update."
        raise NewsHarnessError("Instalación detenida: estos archivos existen y son diferentes; no se modificó nada: "
                          + ", ".join(conflicts[:5]) + (" …" if len(conflicts) > 5 else "") + "." + hint)
    created = replaced = 0
    for dest, data, existing in writes:
        if existing:
            replace_file(dest, data); replaced += 1
        else:
            write_new(dest, data); created += 1
    for dest in stale:
        dest.unlink()
    manifest["kit_version"] = VERSION
    manifest["kit_files"] = {rel: hashlib.sha256(src.read_bytes()).hexdigest() for rel, src in kit.items()}
    manifest["agents"][agent] = {"skills_root": str(skill_root), "skills": names,
                                 "files": {rel: hashlib.sha256(src.read_bytes()).hexdigest() for rel, src in skills.items()}}
    replace_file(manifest_path, json_text(manifest).encode("utf-8"))
    return {"mode": "global", "agent": agent, "kit": str(kit_root), "skills_root": str(skill_root), "skills": names,
            "created_files": created, "replaced_files": replaced, "removed_stale_files": len(stale),
            "runtime": str(kit_root / "scripts" / "newsharness.py"), "global_instructions_modified": False, "network_used": False,
            "warning": "Reinicie el agente para que descubra las skills. La copia no demuestra compatibilidad end-to-end con su versión."}


def uninstall_global(agent, manifest, manifest_path, kit_root, skill_root):
    entry = manifest["agents"].pop(agent, None)
    if entry is None:
        raise NewsHarnessError(f"No hay una instalación global de NewsHarness registrada para {agent}. No se eliminó nada.")
    removed, kept = 0, []
    targets = [(skill_root, entry["files"])]
    if not manifest["agents"]:
        targets.append((kit_root, manifest["kit_files"]))
    for root, files in targets:
        for rel, digest in files.items():
            dest = confined_path(root, rel)
            if not dest.is_file():
                continue
            if sha256(dest) == digest:
                dest.unlink(); removed += 1
            else:
                kept.append(str(dest))
    for root, files in targets:
        # Remove only folders left empty by this uninstall, deepest first.
        for folder in sorted({confined_path(root, rel).parent for rel in files}, key=lambda p: len(p.parts), reverse=True):
            while folder != root and folder.is_dir() and not any(folder.iterdir()):
                folder.rmdir(); folder = folder.parent
    if manifest["agents"]:
        replace_file(manifest_path, json_text(manifest).encode("utf-8"))
    else:
        manifest_path.unlink(missing_ok=True)
        if kit_root.is_dir() and not any(kit_root.iterdir()):
            kit_root.rmdir()
    return {"mode": "global", "agent": agent, "uninstalled": True, "removed_files": removed,
            "kept_modified_files": kept, "kit_removed": not manifest["agents"] and not kit_root.exists(),
            "note": "Perfiles, espacios de trabajo y modelos descargados no forman parte de la instalación y no se tocaron."}


def positive_int(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Se requiere un número entero.") from None
    if not 1 <= number <= 86400:
        raise argparse.ArgumentTypeError("Debe estar entre 1 y 86400.")
    return number


def parser():
    p = argparse.ArgumentParser(description="NewsHarness Kit: preparación editorial, OCR y audio locales. No publica ni envía documentos.")
    p.add_argument("--version", action="version", version=VERSION)
    commands = p.add_subparsers(dest="command", required=True)
    for name in ("doctor", "plan"):
        command = commands.add_parser(name, help="Diagnóstico local sin cambios" if name == "doctor" else "Plan de preparación; no instala")
        command.add_argument("--workspace")
        command.add_argument("--json", action="store_true")
        if name == "plan":
            command.add_argument("--quality", choices=MODELS, default="base")
            command.add_argument("--allow-restricted-tiny", action="store_true")
    command = commands.add_parser("init", help="Validar perfil y crear espacio de trabajo")
    command.add_argument("--workspace", required=True)
    command.add_argument("--profile", required=True)
    for name in ("ocr", "_ocr-worker"):
        command = commands.add_parser(name, help="OCR local / texto existente primero" if name == "ocr" else argparse.SUPPRESS)
        command.add_argument("--workspace", required=True)
        command.add_argument("--input", required=True)
        command.add_argument("--lang", default="spa")
        command.add_argument("--tessdata-dir")
        command.add_argument("--max-pages", type=positive_int, default=250)
        command.add_argument("--page-timeout", type=positive_int, default=300)
        if name == "ocr":
            command.add_argument("--timeout", type=positive_int, default=1800)
        else:
            command.add_argument("--job", required=True)
    for name in ("transcribe", "calibrate"):
        command = commands.add_parser(name, help="Transcribir audio local con tiempos" if name == "transcribe" else "Medir una muestra local; no garantiza calidad")
        command.add_argument("--workspace", required=True)
        command.add_argument("--input", required=True)
        command.add_argument("--model", required=True)
        command.add_argument("--quality", choices=MODELS, default="base")
        command.add_argument("--allow-restricted-tiny", action="store_true")
        command.add_argument("--language", default="es")
        command.add_argument("--threads", type=positive_int)
        command.add_argument("--vad-model")
        command.add_argument("--allow-no-vad", action="store_true", help="Aceptación explícita del mayor riesgo sin VAD")
        command.add_argument("--timeout", type=positive_int, default=7200)
        command.add_argument("--sample-seconds", type=positive_int, default=90 if name == "calibrate" else None)
        command.add_argument("--palabras", dest="word_timestamps", action="store_true",
                             help="JSON completo con tiempos por palabra (para subtítulos de video)")
    command = commands.add_parser("fetch", help="Descargar un modelo fijado con SHA256 y autorización explícita")
    command.add_argument("--workspace", required=True)
    command.add_argument("--artifact", required=True)
    command.add_argument("--approve-download", action="store_true")
    command = commands.add_parser("install-skills", help="Copiar skills a un proyecto o al usuario sin sobrescribir configuración")
    target = command.add_mutually_exclusive_group(required=True)
    target.add_argument("--project")
    target.add_argument("--global", dest="global_install", action="store_true",
                        help="Kit en ~/.newsharness-kit y skills en la carpeta de usuario del agente; no modifica instrucciones globales")
    command.add_argument("--agent", choices=("codex", "claude", "opencode"), required=True)
    action = command.add_mutually_exclusive_group()
    action.add_argument("--update", action="store_true", help="Sólo con --global: reemplazar archivos de NewsHarness no modificados")
    action.add_argument("--uninstall", action="store_true", help="Sólo con --global: quitar archivos de NewsHarness no modificados")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if getattr(args, "max_pages", 1) > 2000:
            raise NewsHarnessError("--max-pages admite como máximo 2000; divida documentos mayores.")
        if args.command == "calibrate" and not 60 <= args.sample_seconds <= 120:
            raise NewsHarnessError("Calibre una muestra de 60–120 segundos con --sample-seconds.")
        if args.command == "doctor":
            result = doctor(args.workspace)
        elif args.command == "plan":
            result = setup_plan(doctor(args.workspace), args.quality, args.allow_restricted_tiny)
        elif args.command == "init":
            result = initialize(args.workspace, args.profile)
        elif args.command == "ocr":
            result = ocr(args)
        elif args.command == "_ocr-worker":
            root = workspace_root(args.workspace)
            if not re.fullmatch(r"ocr-[a-zA-Z0-9_-]+", args.job):
                raise NewsHarnessError("Identificador de trabajo no válido.")
            job = confined_path(root, Path("output") / args.job)
            source = local_input(args.input)
            source.relative_to(confined_path(root, "originals"))
            result = {"pages": len(ocr_document(source, job, args.lang, tessdata_path(root, args.tessdata_dir), args.max_pages, args.page_timeout))}
        elif args.command in ("transcribe", "calibrate"):
            result = transcribe(args)
        elif args.command == "fetch":
            result = fetch_artifact(args.workspace, args.artifact, args.approve_download)
        elif args.global_install:
            result = install_global(args.agent, update=args.update, uninstall=args.uninstall)
        elif args.update or args.uninstall:
            raise NewsHarnessError("--update y --uninstall sólo se admiten con --global.")
        else:
            result = install_skills(args.project, args.agent)
        if args.command == "doctor" and not args.json:
            print(f"NewsHarness Kit {VERSION} · {result['os']['system']} {result['os']['release']} · {result['os']['architecture']}")
            print(f"CPU: {result['cpu']['name']} · núcleos lógicos: {result['cpu']['logical_cores']}")
            available = result['memory']['available_bytes']
            print("RAM disponible: " + (f"{available / GIB:.2f} GiB" if available is not None else "desconocida; no se adivina"))
            print(f"Disco libre: {result['disk']['free_bytes'] / GIB:.2f} GiB")
            for name, value in result["tools"].items():
                print(f"{name}: {value['version'] if value['found'] else 'NO instalado'}")
                if "languages" in value:
                    print("  Idiomas: " + ", ".join(value["languages"]))
            for name, value in result["optional_python"].items():
                print(f"{name}: {value['version'] if value['found'] else 'NO instalado (opcional para PDF)'}")
            print("Sin red, instalación ni cambios. Ejecute plan para próximos pasos.")
        elif args.command == "plan" and not args.json:
            print(f"Modelo propuesto: {result['selected_model']} · CPU · {result['threads']} hilos")
            print(f"RAM: {result['memory_status']} · descarga del modelo ≈ {result['approx_model_download_mb']} MB (no RAM)")
            print("Falta: " + (", ".join(result["missing"]) or "ninguna herramienta detectada; el modelo debe comprobarse aparte"))
            for note in result["notes"]:
                print("- " + note)
        else:
            print(json_text(result), end="")
        return 0
    except (NewsHarnessError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Interrumpido. Los originales permanecen intactos; no use resultados parciales sin revisar.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
