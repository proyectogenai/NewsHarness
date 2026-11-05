#!/usr/bin/env python3
"""Cliente del Catálogo API-INDEC para NewsHarness (Python estándar, >=3.10).

Adaptación de indec-api-skill de Jony Musky (MIT, commit 0a95ccc):
https://github.com/jonymusky/indec-api-skill . Ver docs/TERCEROS.md.

Sólo consulta https://api.indec.gob.ar por GET. El token personal se lee de la
variable de entorno INDEC_TOKEN, nunca se imprime ni se guarda, y no viaja a
otro host: no se siguen redirecciones ni se admite otra URL base. Las columnas
se validan contra la spec incluida en config/indec/openapi.json. No escribe
salvo en un archivo nuevo pedido con --salida, acompañado de su procedencia.
"""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = "api.indec.gob.ar"
BASE = f"https://{HOST}/v1/"
SPEC_URL = f"https://{HOST}/api/openapi?v=2"
SPEC_FILE = ROOT / "config" / "indec" / "openapi.json"
PORTAL = f"https://{HOST}/"
PAGE = 1000  # tope duro del servidor por respuesta
MAX_BYTES = 20 * 1024 * 1024
MAX_ROWS = 200_000
SHOW = 50
UA = "NewsHarness-Kit/0.1 (+indec_api)"
LOGICAL = {"or", "and", "not.or", "not.and"}
PERIOD_COLS = ("periodo", "Periodo", "fecha")
TABLE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
SLEEP = time.sleep


class IndecError(Exception):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect could carry the Authorization header to another host: refuse it."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise IndecError(f"La API respondió con una redirección ({code}); no se siguió para proteger el token.")


_OPENER = urllib.request.build_opener(_NoRedirect)


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


# ---------------------------------------------------------------- spec

def load_spec(path=None):
    data = json.loads(Path(path or SPEC_FILE).read_text(encoding="utf-8"))
    spec = data.get("spec", data)
    spec.setdefault("_newsharness", {"retrieved_at": data.get("retrieved_at"), "source": data.get("source")})
    return spec


def _res(spec, node):
    while isinstance(node, dict) and "$ref" in node:
        cur = spec
        for part in node["$ref"].lstrip("#/").split("/"):
            cur = cur[part]
        node = cur
    return node


def table_meta(spec, table):
    if not TABLE_NAME.match(table or ""):
        raise IndecError(f"Nombre de tabla no válido: {table!r}.")
    op = spec["paths"].get("/" + table, {}).get("get")
    if not op:
        lower = {p.strip("/").lower().replace("-", "_"): p.strip("/") for p in spec["paths"]}
        hint = lower.get(table.lower().replace("-", "_"))
        names = ", ".join(p.strip("/") for p in spec["paths"])
        raise IndecError(f"Tabla desconocida: {table!r}." + (f" ¿Quiso decir {hint!r}?" if hint else "") + f" Disponibles: {names}")
    desc = op.get("description", "")
    m = re.search(r"### Clave primaria.*?:\s*(.+)", desc, re.S)
    pk = re.findall(r"`([^`]+)`", m.group(1).splitlines()[0]) if m else []
    schema = _res(spec, op["responses"]["200"]["content"]["application/json"]["schema"])
    if schema.get("type") == "array":
        schema = _res(spec, schema["items"])
    cols = {}
    for name, cs in schema.get("properties", {}).items():
        cs = _res(spec, cs)
        types = [s.get("type") for s in cs.get("anyOf", [cs])]
        cols[name] = {"type": "/".join(t for t in types if t != "null") or "null", "nullable": "null" in types,
                      "description": re.sub(r"\s+", " ", cs.get("description") or "").strip()}
    return {"summary": op.get("summary", ""), "description": desc.split("###")[0].strip(), "pk": pk, "columns": cols}


def check_columns(meta, table, names):
    cols = meta["columns"]
    lower = {c.lower(): c for c in cols}
    bad = []
    for n in names:
        if n in cols or n in LOGICAL:
            continue
        hint = lower.get(n.lower())
        bad.append(f"{n!r}" + (f" (¿quiso decir {hint!r}? Las columnas distinguen mayúsculas)" if hint else ""))
    if bad:
        raise IndecError(f"Columnas inexistentes en {table}: {', '.join(bad)}. Válidas: {', '.join(cols)}")


def parse_filters(items):
    out = []
    for it in items or []:
        if "=" not in it:
            raise IndecError(f"Filtro inválido {it!r}: use columna=operador.valor (ej. periodo=gte.202401).")
        k, v = it.split("=", 1)
        if k in ("select", "order", "limit", "offset"):
            raise IndecError(f"Use la opción --{k}, no un filtro {k}=.")
        out.append((k, v))
    return out


def validate(spec, table, filters, select=None, order=None, check=True):
    meta = table_meta(spec, table)  # la tabla se valida siempre: no se arman rutas arbitrarias
    if not check:
        return meta
    names = [k for k, _ in filters]
    for part in (select or "").split(","):
        part = part.strip()
        if part and part != "*":
            names.append(part.split("::")[0].split(":")[-1])  # alias:col y col::cast
    for part in (order or "").split(","):
        if part.strip():
            names.append(part.strip().split(".")[0])
    check_columns(meta, table, names)
    return meta


# ---------------------------------------------------------------- HTTP

def token_from_env():
    token = os.environ.get("INDEC_TOKEN", "").strip()
    if not token:
        raise IndecError("Falta INDEC_TOKEN. La persona debe registrarse en " + PORTAL + ", generar el token en su perfil "
                         "y guardarlo como variable de entorno INDEC_TOKEN fuera del chat (ver skills/newsharness-indec/SKILL.md). "
                         "Sin token, usar Series de Tiempo de datos.gob.ar o el informe del INDEC.")
    if token.count(".") != 2 or any(ch.isspace() for ch in token):
        raise IndecError("INDEC_TOKEN no tiene forma de JWT (tres partes separadas por puntos). Revisar que se copió completo.")
    return token


class Session:
    """Keeps the token out of every message and hashes the exact bytes received."""

    def __init__(self, opener=None, token=None):
        self.open = opener or _OPENER.open
        self._token = token
        self.digest = hashlib.sha256()
        self.requests = 0
        self.first_url = None

    def _clean(self, text):
        return text.replace(self._token, "<token>") if self._token else text

    def get(self, table, params, count=False):
        if self._token is None:
            self._token = token_from_env()
        url = BASE + table
        if params:
            # safe= deja legibles los operadores PostgREST ( . , ( ) * ) sin romper la URL
            url += "?" + urllib.parse.urlencode(params, safe=".,()*:")
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname != HOST or not parsed.path.startswith("/v1/"):
            raise IndecError("URL no permitida: sólo se consulta api.indec.gob.ar/v1.")
        headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/json", "User-Agent": UA}
        if count:
            headers["Prefer"] = "count=exact"
        request = urllib.request.Request(url, headers=headers)
        for attempt in range(4):
            try:
                with self.open(request, timeout=120) as r:  # 200 y 206 son éxito
                    data = r.read(MAX_BYTES + 1)
                    content_range = r.headers.get("Content-Range") if hasattr(r, "headers") else None
                break
            except urllib.error.HTTPError as e:
                body = self._clean(e.read(4000).decode("utf-8", "replace"))
                if e.code in (429, 502, 503, 504) and attempt < 3:
                    SLEEP(2 ** attempt); continue
                hint = {401: " El token falta, venció o fue reemplazado por otro: generar uno nuevo en el perfil del portal.",
                        404: " La tabla no existe en la API; revisar guiones y guiones bajos."}.get(e.code, "")
                raise IndecError(f"HTTP {e.code} en {url}.{hint}\n{body}") from None
            except urllib.error.URLError as e:
                if attempt < 3:
                    SLEEP(2 ** attempt); continue
                raise IndecError(f"Error de red en {url}: {self._clean(str(e.reason))}") from None
        if len(data) > MAX_BYTES:
            raise IndecError("Respuesta mayor que 20 MB; acotar la consulta con filtros.")
        try:
            rows = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise IndecError(f"{url} no devolvió JSON válido.") from None
        if not isinstance(rows, list):
            raise IndecError(f"{url} no devolvió una lista de filas.")
        self.digest.update(data)
        self.requests += 1
        self.first_url = self.first_url or url
        return rows, content_range


def total_from(content_range):
    if content_range and "/" in content_range:
        tail = content_range.rsplit("/", 1)[1]
        return int(tail) if tail.isdigit() else None
    return None


def fetch_all(session, table, filters, select=None, order=None, max_rows=MAX_ROWS, notes=None):
    # La primera página pide Prefer: count=exact: el total sale del Content-Range (0-999/103545).
    rows, offset, total = [], 0, None
    while True:
        params = list(filters) + [("order", order), ("limit", PAGE), ("offset", offset)]
        if select:
            params.append(("select", select))
        page, cr = session.get(table, params, count=offset == 0)
        if offset == 0:
            total = total_from(cr)
            if total is not None and total > max_rows:
                raise IndecError(f"La consulta trae {total} filas (límite {max_rows}). Acotar con filtros de período o región, "
                                 "o subir --max-filas con criterio.")
        rows.extend(page)
        if total is not None and total > PAGE:
            print(f"# página {offset // PAGE + 1}/{-(-total // PAGE)} ({len(rows)}/{total} filas)", file=sys.stderr)
        offset += PAGE
        if len(page) < PAGE or (total is not None and offset >= total) or len(rows) >= max_rows:
            break
    if total is not None and len(rows) != total and notes is not None:
        notes.append(f"Se esperaban {total} filas y llegaron {len(rows)}: la tabla pudo cambiar durante la descarga "
                     "o el orden no incluye la clave primaria completa.")
    return rows, total


def period_col(meta):
    for c in PERIOD_COLS:
        if c in meta["columns"]:
            return c
    raise IndecError("La tabla no tiene columna de período (periodo/Periodo/fecha).")


def add_labels(session, rows, table, notes):
    if not table.startswith("comercio_exterior_"):
        notes.append("--etiquetas sólo aplica a tablas comercio_exterior_*; se ignoró.")
        return rows
    code_cols = {k for r in rows[:1] for k in r if k.lower().endswith("_cod")}
    if not code_cols:
        return rows
    dic, _ = fetch_all(session, "comercio_exterior_nomenclaturas", [], "nombre_columna,codigo,codigo_descripcion",
                       "nombre_columna,codigo")
    lookup = {}
    for d in dic:
        lookup.setdefault(str(d["nombre_columna"]).lower(), {})[str(d["codigo"])] = d["codigo_descripcion"]
    missing = sorted(c for c in code_cols if c.lower() not in lookup)
    if missing:
        notes.append(f"Sin nomenclatura para {missing}.")
    out = []
    for r in rows:
        r = dict(r)
        for c in sorted(code_cols):
            m = lookup.get(c.lower())
            if m is not None:
                r[c[:-4] + "_desc"] = m.get(str(r.get(c)))
        out.append(r)
    return out


# ---------------------------------------------------------------- resultado

SIGNS = {"*": "provisorio", "**": "preliminar", "e": "estimado", "i": "estimado", "-": "cero absoluto",
         "...": "no disponible", "///": "no corresponde", "s": "secreto estadístico"}


def observations(rows):
    """Count conventional signs: a null value with 's' is statistical secrecy, not a zero."""
    counts = {}
    nulls = 0
    for r in rows:
        key = next((k for k in r if k.lower() == "observaciones"), None)
        mark = str(r.get(key) or "").strip() if key else ""
        if mark:
            counts[mark] = counts.get(mark, 0) + 1
        if "valor" in r and r["valor"] is None:
            nulls += 1
    return {"signos": {k: {"filas": v, "significado": SIGNS.get(k, "ver metodología")} for k, v in sorted(counts.items())},
            "valores_nulos": nulls}


def result(session, spec, table, meta, filters, rows, total=None, notes=None):
    info = spec.get("_newsharness", {})
    last = None
    try:
        pc = period_col(meta)
        values = [r.get(pc) for r in rows if r.get(pc) is not None]
        last = max(values, key=str) if values else None
    except IndecError:
        pass
    return {
        "fuente": "INDEC, Catálogo API-INDEC",
        "tabla": table, "titulo": meta["summary"], "filtros": [f"{k}={v}" for k, v in filters],
        "filas": len(rows), "total_declarado": total, "ultimo_periodo": last,
        "observaciones": observations(rows),
        "procedencia": {"url_primera_consulta": session.first_url, "consultas": session.requests,
                        "sha256_respuestas": session.digest.hexdigest() if session.requests else None,
                        "retrieved_at": now(), "spec_incluida": info.get("retrieved_at")},
        "cita_sugerida": f"INDEC, Catálogo API-INDEC, tabla {table}" + (f", período {last}" if last else "")
                         + f", consultado el {dt.date.today().isoformat()}.",
        "avisos": notes or [],
        "datos": rows,
    }


def write_output(path, res):
    path = Path(path)
    if path.exists():
        raise IndecError(f"{path} ya existe; no se sobrescribió. Elija otro nombre.")
    suffix = path.suffix.lower()
    if suffix not in (".csv", ".json"):
        raise IndecError("--salida debe terminar en .csv o .json.")
    path.parent.mkdir(parents=True, exist_ok=True)
    if suffix == ".json":
        with path.open("x", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        return
    meta = path.with_suffix(".procedencia.json")
    if meta.exists():
        raise IndecError(f"{meta} ya existe; no se sobrescribió.")
    fields = []
    for r in res["datos"]:
        fields += [k for k in r if k not in fields]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(res["datos"])
    with path.open("x", encoding="utf-8", newline="") as f:
        f.write(buffer.getvalue())
    with meta.open("x", encoding="utf-8") as f:
        json.dump({k: v for k, v in res.items() if k != "datos"}, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------- comandos

def list_tables(spec):
    out = []
    for path in spec["paths"]:
        m = table_meta(spec, path.strip("/"))
        out.append({"tabla": path.strip("/"), "titulo": m["summary"], "clave_primaria": m["pk"]})
    return {"spec_incluida": spec.get("_newsharness", {}).get("retrieved_at"), "tablas": out}


def describe_table(spec, table):
    m = table_meta(spec, table)
    return {"tabla": table, "titulo": m["summary"], "descripcion": m["description"], "clave_primaria": m["pk"],
            "columnas": [{"columna": k, **v} for k, v in m["columns"].items()]}


def query(spec, table, filters=(), select=None, order=None, limit=None, offset=None, everything=False, labels=False,
          check=True, max_rows=MAX_ROWS, session=None):
    filters = parse_filters(filters)
    meta = validate(spec, table, filters, select, order, check)
    session = session or Session()
    notes, total = [], None
    if everything:
        rows, total = fetch_all(session, table, filters, select, order or ",".join(meta["pk"]), max_rows, notes)
    else:
        params = list(filters)
        for k, v in (("select", select), ("order", order), ("limit", limit), ("offset", offset)):
            if v is not None:
                params.append((k, v))
        rows, _ = session.get(table, params)
        if len(rows) == PAGE and (limit is None or limit > PAGE):
            notes.append(f"Llegaron {PAGE} filas, el tope del servidor: puede haber más. Usar --todo o paginar con --offset.")
    if labels:
        rows = add_labels(session, rows, table, notes)
    return result(session, spec, table, meta, filters, rows, total, notes)


def count(spec, table, filters=(), check=True, session=None):
    filters = parse_filters(filters)
    validate(spec, table, filters, check=check)
    session = session or Session()
    _, cr = session.get(table, filters + [("limit", 1)], count=True)
    return {"tabla": table, "filtros": [f"{k}={v}" for k, v in filters], "total": total_from(cr)}


def distinct(spec, table, columns, filters=(), check=True, max_rows=MAX_ROWS, session=None):
    meta = table_meta(spec, table)
    cols = [c.strip() for c in columns.split(",") if c.strip()]
    filters = parse_filters(filters)
    if check:
        check_columns(meta, table, cols + [k for k, _ in filters])
    session = session or Session()
    notes = []
    # PostgREST no tiene DISTINCT: se traen esas columnas ordenando por la clave primaria completa y se deduplica.
    rows, total = fetch_all(session, table, filters, ",".join(cols), ",".join(meta["pk"]), max_rows, notes)
    seen, out = set(), []
    for r in rows:
        key = tuple(r.get(c) for c in cols)
        if key not in seen:
            seen.add(key)
            out.append(r)
    out.sort(key=lambda r: tuple("" if r.get(c) is None else str(r.get(c)) for c in cols))
    res = result(session, spec, table, meta, filters, out, total, notes)
    res["filas_recorridas"] = len(rows)
    return res


def latest(spec, table, filters=(), periods=1, select=None, labels=False, check=True, max_rows=MAX_ROWS, session=None):
    filters = parse_filters(filters)
    meta = validate(spec, table, filters, select, check=check)
    pc = period_col(meta)
    rest = [c for c in meta["pk"] if c != pc]
    session = session or Session()
    found, offset = [], 0
    while len(found) < periods:
        params = filters + [("select", pc), ("order", ",".join([pc + ".desc"] + rest)), ("limit", PAGE), ("offset", offset)]
        page, _ = session.get(table, params)
        for r in page:
            if r[pc] not in found:
                found.append(r[pc])
                if len(found) == periods:
                    break
        if len(page) < PAGE:
            break
        offset += PAGE
    notes = []
    if not found:
        return result(session, spec, table, meta, filters, [], 0, ["No hay filas para esos filtros."])
    in_list = "in.(" + ",".join(f'"{p}"' if isinstance(p, str) else str(p) for p in found) + ")"
    rows, total = fetch_all(session, table, filters + [(pc, in_list)], select, ",".join(meta["pk"]), max_rows, notes)
    if labels:
        rows = add_labels(session, rows, table, notes)
    res = result(session, spec, table, meta, filters, rows, total, notes)
    res["periodos"] = found
    return res


def compare_spec(spec, opener=None):
    """Download the live spec (no token) and report table/column changes against the bundled one."""
    request = urllib.request.Request(SPEC_URL, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with (opener or _OPENER.open)(request, timeout=60) as r:
            data = r.read(MAX_BYTES + 1)
    except (OSError, IndecError) as exc:
        raise IndecError(f"No se pudo leer la spec viva: {exc}") from None
    live = json.loads(data.decode("utf-8"))
    live = live.get("spec", live)

    def shape(s):
        return {p.strip("/"): set(table_meta(s, p.strip("/"))["columns"]) for p in s["paths"]}

    old, new = shape(spec), shape(live)
    changed = {t: {"nuevas": sorted(new[t] - old[t]), "quitadas": sorted(old[t] - new[t])}
               for t in sorted(old.keys() & new.keys()) if old[t] != new[t]}
    return {"spec_incluida": spec.get("_newsharness", {}).get("retrieved_at"), "sha256_viva": hashlib.sha256(data).hexdigest(),
            "tablas_nuevas": sorted(new.keys() - old.keys()), "tablas_quitadas": sorted(old.keys() - new.keys()),
            "columnas_cambiadas": changed,
            "sin_cambios_estructurales": not (new.keys() ^ old.keys()) and not changed}


def catalog_markdown(spec):
    """Human index of tables and columns, generated from the bundled spec."""
    info = spec.get("_newsharness", {})
    lines = ["# Catálogo de tablas · API INDEC", "",
             f"<!-- Generado con `python3 scripts/indec_api.py catalogo` desde config/indec/openapi.json "
             f"(spec consultada el {info.get('retrieved_at')}). No editar a mano. -->", "",
             f"Base: `{BASE}` · Spec: `{SPEC_URL}`", "",
             "Los nombres de columna **distinguen mayúsculas**: copiarlos tal cual.", "",
             "| Tabla | Qué es |", "|---|---|"]
    tables = [p.strip("/") for p in spec["paths"]]
    for t in tables:
        lines.append(f"| [`{t}`](#{t}) | {table_meta(spec, t)['summary']} |")
    for t in tables:
        m = table_meta(spec, t)
        lines += ["", f"## {t}", "", f"**{m['summary']}**", "", m["description"], "",
                  f"- Clave primaria (completa en `--order` para paginar): `{','.join(m['pk'])}`", "",
                  "| Columna | Tipo | Nulo | Descripción |", "|---|---|---|---|"]
        for name, c in m["columns"].items():
            pk = "**PK** " if name in m["pk"] else ""
            desc = c["description"].replace("|", "\\|")
            lines.append(f"| `{name}` | {c['type']} | {'sí' if c['nullable'] else ''} | {pk}{desc} |")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- CLI

def parser():
    p = argparse.ArgumentParser(description="Catálogo API-INDEC: tablas, columnas y consultas con procedencia. "
                                "Filtros estilo PostgREST: columna=operador.valor (periodo=gte.202401).")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("tablas", aliases=["tables"], help="Listar tablas y clave primaria (sin token)")
    c = sub.add_parser("columnas", aliases=["columns"], help="Columnas, tipos y descripción de una tabla (sin token)")
    c.add_argument("tabla")

    def common(c, rows=True):
        c.add_argument("tabla")
        c.add_argument("filtros", nargs="*")
        c.add_argument("--sin-validar", action="store_true", help="No validar columnas contra la spec incluida")
        if rows:
            c.add_argument("--max-filas", type=int, default=MAX_ROWS)
            c.add_argument("--salida", help="Archivo nuevo .csv (con .procedencia.json) o .json")
            c.add_argument("--mostrar", type=int, default=SHOW, help=f"Filas a mostrar en pantalla (por defecto {SHOW})")

    c = sub.add_parser("consultar", aliases=["get"], help="Consultar filas")
    common(c)
    c.add_argument("--select"); c.add_argument("--order")
    c.add_argument("--limit", type=int); c.add_argument("--offset", type=int)
    c.add_argument("--todo", action="store_true", help="Paginar hasta traer todo (ordena por la clave primaria)")
    c.add_argument("--etiquetas", action="store_true", help="Comercio exterior: agrega <col>_desc a cada *_cod")
    c = sub.add_parser("contar", aliases=["count"], help="Total de filas que cumplen los filtros")
    common(c, rows=False)
    c = sub.add_parser("valores", aliases=["distinct"], help="Combinaciones únicas de columnas (para descubrir textos exactos)")
    c.add_argument("tabla"); c.add_argument("columnas"); c.add_argument("filtros", nargs="*")
    c.add_argument("--sin-validar", action="store_true")
    c.add_argument("--max-filas", type=int, default=MAX_ROWS)
    c.add_argument("--salida"); c.add_argument("--mostrar", type=int, default=500)
    c = sub.add_parser("ultimos", aliases=["latest"], help="Filas de los últimos N períodos")
    common(c)
    c.add_argument("--periodos", type=int, default=1); c.add_argument("--select")
    c.add_argument("--etiquetas", action="store_true")
    sub.add_parser("comparar-spec", help="Comparar la spec incluida con la publicada hoy (sin token)")
    c = sub.add_parser("catalogo", help="Generar el catálogo Markdown de tablas en un archivo nuevo")
    c.add_argument("--salida", required=True)
    return p


ALIASES = {"tables": "tablas", "columns": "columnas", "get": "consultar", "count": "contar", "distinct": "valores",
           "latest": "ultimos"}


def main(argv=None):
    args = parser().parse_args(argv)
    command = ALIASES.get(args.command, args.command)
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    try:
        spec = load_spec()
        if command == "tablas":
            res = list_tables(spec)
        elif command == "columnas":
            res = describe_table(spec, args.tabla)
        elif command == "contar":
            res = count(spec, args.tabla, args.filtros, not args.sin_validar)
        elif command == "comparar-spec":
            res = compare_spec(spec)
        elif command == "catalogo":
            out = Path(args.salida)
            if out.exists():
                raise IndecError(f"{out} ya existe; no se sobrescribió.")
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("x", encoding="utf-8", newline="\n") as f:
                f.write(catalog_markdown(spec))
            res = {"salida": str(out.resolve())}
        else:
            if command == "consultar":
                res = query(spec, args.tabla, args.filtros, args.select, args.order, args.limit, args.offset, args.todo,
                            args.etiquetas, not args.sin_validar, args.max_filas)
            elif command == "valores":
                res = distinct(spec, args.tabla, args.columnas, args.filtros, not args.sin_validar, args.max_filas)
            else:
                res = latest(spec, args.tabla, args.filtros, args.periodos, args.select, args.etiquetas,
                             not args.sin_validar, args.max_filas)
            if args.salida:
                write_output(args.salida, res)
                res["salida"] = str(Path(args.salida).resolve())
            # Keep the chat short: the full table goes to --salida, not to the model.
            rows = res.pop("datos")
            res["muestra"] = rows[:max(args.mostrar, 0)]
            if len(rows) > len(res["muestra"]):
                res["avisos"].append(f"Se muestran {len(res['muestra'])} de {len(rows)} filas; el resto, con --salida.")
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    except IndecError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
