import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shlex
import tempfile
import unittest
from unittest import mock
import urllib.error
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("indec_api", ROOT / "scripts/indec_api.py")
I = importlib.util.module_from_spec(spec); spec.loader.exec_module(I)
SPEC = I.load_spec()
TOKEN = "aaa.bbb.ccc"


class FakeResponse(io.BytesIO):
    def __init__(self, data, content_range=None):
        super().__init__(data)
        self.headers = {"Content-Range": content_range} if content_range else {}
    def __enter__(self): return self
    def __exit__(self, *a): self.close()


class FakeApi:
    """Serves rows like PostgREST: eq/in filters, select, order is ignored, limit/offset paging."""

    def __init__(self, tables, fail=None):
        self.tables, self.fail, self.calls = tables, list(fail or []), []

    def __call__(self, request, timeout):
        self.calls.append(request)
        if self.fail:
            code = self.fail.pop(0)
            raise urllib.error.HTTPError(request.full_url, code, "x", {}, io.BytesIO(b'{"code":"x","token":"' + TOKEN.encode() + b'"}'))
        url = urllib.parse.urlsplit(request.full_url)
        rows = list(self.tables[url.path.rsplit("/", 1)[1]])
        params = urllib.parse.parse_qsl(url.query)
        for k, v in params:
            if k in ("select", "order", "limit", "offset"):
                continue
            op, _, value = v.partition(".")
            if op == "eq":
                rows = [r for r in rows if str(r.get(k)) == value]
            elif op == "in":
                wanted = {x.strip('"') for x in value.strip("()").split(",")}
                rows = [r for r in rows if str(r.get(k)) in wanted]
        total = len(rows)
        q = dict(params)
        offset, limit = int(q.get("offset", 0)), min(int(q.get("limit", 1000)), 1000)
        rows = rows[offset:offset + limit]
        if "select" in q:
            cols = q["select"].split(",")
            rows = [{c: r.get(c) for c in cols} for r in rows]
        cr = f"{offset}-{offset + len(rows) - 1}/{total}" if request.get_header("Prefer") else None
        return FakeResponse(json.dumps(rows).encode("utf-8"), cr)


def comex_rows(n):
    return [{"Anio": 2025, "Mes": 1, "Periodo": "202501", "rubro_cod": 1, "subrubro_cod": i, "pais_cod": 200,
             "valor_FOB": None if i % 10 == 0 else 1.5, "Peso_Neto": 1, "observaciones": "s" if i % 10 == 0 else None}
            for i in range(n)]


class IndecApiTests(unittest.TestCase):
    def session(self, api):
        return I.Session(opener=api, token=TOKEN)

    def test_bundled_spec_has_all_tables_with_primary_keys(self):
        tables = I.list_tables(SPEC)["tablas"]
        self.assertEqual(len(tables), 19)
        for t in tables:
            self.assertTrue(t["clave_primaria"], t["tabla"])

    def test_column_case_and_table_name_hints(self):
        with self.assertRaisesRegex(I.IndecError, "quiso decir 'periodo'"):
            I.query(SPEC, "ipc_nacional", ["Periodo=eq.202501"], session=self.session(FakeApi({})))
        with self.assertRaisesRegex(I.IndecError, "canasta-crianza"):
            I.table_meta(SPEC, "canasta_crianza")
        for bad in ("../ipc_nacional", "ipc_nacional?x=1", "", "a/b"):
            with self.subTest(bad=bad), self.assertRaises(I.IndecError):
                I.table_meta(SPEC, bad)

    def test_unvalidated_query_still_requires_known_table(self):
        with self.assertRaises(I.IndecError):
            I.query(SPEC, "otra_tabla", check=False, session=self.session(FakeApi({})))

    def test_paginates_by_primary_key_and_counts_secrecy_signs(self):
        api = FakeApi({"comercio_exterior_exportacion_bienes": comex_rows(2500)})
        res = I.query(SPEC, "comercio_exterior_exportacion_bienes", ["Anio=eq.2025"], everything=True, session=self.session(api))
        self.assertEqual(res["filas"], 2500)
        self.assertEqual(res["total_declarado"], 2500)
        self.assertEqual(len(api.calls), 3)
        order = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(api.calls[0].full_url).query))["order"]
        self.assertEqual(order, "Anio,Mes,Periodo,rubro_cod,subrubro_cod,pais_cod")
        self.assertEqual(res["observaciones"]["signos"]["s"], {"filas": 250, "significado": "secreto estadístico"})
        self.assertEqual(res["ultimo_periodo"], "202501")
        self.assertIn("INDEC, Catálogo API-INDEC, tabla comercio_exterior_exportacion_bienes, período 202501", res["cita_sugerida"])
        self.assertEqual(len(res["procedencia"]["sha256_respuestas"]), 64)

    def test_row_limit_stops_before_downloading(self):
        api = FakeApi({"comercio_exterior_exportacion_bienes": comex_rows(2500)})
        with self.assertRaisesRegex(I.IndecError, "2500 filas"):
            I.query(SPEC, "comercio_exterior_exportacion_bienes", everything=True, max_rows=2000, session=self.session(api))
        self.assertEqual(len(api.calls), 1)

    def test_distinct_and_latest(self):
        rows = [{"periodo": p, "region": r, "nivel": "General", "valor": 1.0, "observaciones": None}
                for p in ("202507", "202508", "202509") for r in ("A", "B")]
        api = FakeApi({"ipc_nacional": rows})
        res = I.distinct(SPEC, "ipc_nacional", "region", session=self.session(api))
        self.assertEqual(res["datos"], [{"region": "A"}, {"region": "B"}])
        self.assertEqual(res["filas_recorridas"], 6)
        api = FakeApi({"ipc_nacional": sorted(rows, key=lambda r: r["periodo"], reverse=True)})
        res = I.latest(SPEC, "ipc_nacional", periods=2, session=self.session(api))
        self.assertEqual(res["periodos"], ["202509", "202508"])
        self.assertEqual(res["filas"], 4)

    def test_labels_translate_trade_codes(self):
        api = FakeApi({"comercio_exterior_exportacion_bienes": comex_rows(2),
                       "comercio_exterior_nomenclaturas": [{"nombre_columna": "pais_cod", "codigo": 200, "codigo_descripcion": "Brasil"}]})
        res = I.query(SPEC, "comercio_exterior_exportacion_bienes", labels=True, session=self.session(api))
        self.assertEqual(res["datos"][0]["pais_desc"], "Brasil")

    def test_token_never_in_errors_and_missing_token_explained(self):
        api = FakeApi({}, fail=[401])
        with self.assertRaises(I.IndecError) as ctx:
            I.query(SPEC, "pobreza_eph", session=self.session(api))
        self.assertNotIn(TOKEN, str(ctx.exception))
        self.assertIn("<token>", str(ctx.exception))
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(I.IndecError, "Falta INDEC_TOKEN"):
                I.token_from_env()
        with mock.patch.dict(os.environ, {"INDEC_TOKEN": "pegado mal"}):
            with self.assertRaisesRegex(I.IndecError, "JWT") as ctx:
                I.token_from_env()
            self.assertNotIn("pegado mal", str(ctx.exception))

    def test_retries_rate_limit(self):
        api = FakeApi({"pobreza_eph": [{"periodo": "20251", "area_geografica_nom": "Total"}]}, fail=[429, 503])
        with mock.patch.object(I, "SLEEP", lambda s: None):
            res = I.query(SPEC, "pobreza_eph", session=self.session(api))
        self.assertEqual(res["filas"], 1)
        self.assertEqual(len(api.calls), 3)

    def test_redirects_are_refused(self):
        handler = I._NoRedirect()
        with self.assertRaisesRegex(I.IndecError, "redirección"):
            handler.redirect_request(None, None, 302, "Found", {}, "https://evil.example/")
        self.assertTrue(any(isinstance(h, I._NoRedirect) for h in I._OPENER.handlers))

    def test_csv_output_with_provenance_never_overwrites(self):
        api = FakeApi({"comercio_exterior_exportacion_bienes": comex_rows(3)})
        res = I.query(SPEC, "comercio_exterior_exportacion_bienes", session=self.session(api))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "expo.csv"
            I.write_output(out, res)
            self.assertTrue(out.read_text(encoding="utf-8").startswith("Anio,Mes,Periodo,"))
            meta = json.loads((Path(tmp) / "expo.procedencia.json").read_text(encoding="utf-8"))
            self.assertNotIn("datos", meta)
            self.assertNotIn(TOKEN, json.dumps(meta))
            with self.assertRaises(I.IndecError):
                I.write_output(out, res)

    def test_catalog_matches_bundled_spec(self):
        bundled = (ROOT / "skills/newsharness-indec/references/tablas.md").read_text(encoding="utf-8")
        self.assertEqual(bundled, I.catalog_markdown(SPEC))

    def test_documented_commands_use_real_tables_and_columns(self):
        docs = [ROOT / "skills/newsharness-indec/SKILL.md", ROOT / "skills/newsharness-indec/references/consultas.md"]
        commands = {"consultar", "valores", "ultimos", "contar", "columnas"}
        checked = 0
        for path in docs:
            text = path.read_text(encoding="utf-8").replace("\\\n", " ")
            for line in text.splitlines():
                m = re.search(r"(?:^I|scripts/indec_api\.py) (\w+) (.+)$", line.strip())
                if not m or m.group(1) not in commands:
                    continue
                parts = shlex.split(m.group(2).split("`")[0].split("#")[0])
                table = parts[0]
                if table.startswith("<"):
                    continue
                meta = I.table_meta(SPEC, table)
                names = []
                rest = iter(parts[1:])
                for part in rest:
                    if part in ("--select", "--order"):
                        names += [x.split(".")[0].split(":")[-1] for x in next(rest).split(",")]
                    elif part == "--salida":
                        next(rest)
                    elif "=" in part and not part.startswith("--"):
                        names.append(part.split("=")[0])
                    elif m.group(1) == "valores" and not part.startswith("--"):
                        names += part.split(",")
                with self.subTest(line=line):
                    I.check_columns(meta, table, names)
                checked += 1
        self.assertGreater(checked, 15)


if __name__ == "__main__":
    unittest.main()
