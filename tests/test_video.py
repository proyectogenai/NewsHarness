import importlib.util
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("video", ROOT / "scripts" / "video.py")
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)


def tok(text, a, b):
    return {"text": text, "offsets": {"from": a, "to": b}}


FULL = {"transcription": [
    {"offsets": {"from": 0, "to": 2600}, "text": " No vamos a subir las tarifas.",
     "tokens": [tok("[_BEG_]", 0, 0), tok(" No", 0, 300), tok(" vamos", 300, 700), tok(" a", 700, 800),
                tok(" sub", 800, 1000), tok("ir", 1000, 1200), tok(" las", 1200, 1500),
                tok(" tarifas", 1500, 2300), tok(".", 2300, 2400), tok("[_TT_120]", 2400, 2400)]},
    {"offsets": {"from": 3500, "to": 5000}, "text": " Este año, no.",
     "tokens": [tok(" Este", 3500, 3800), tok(" año", 3800, 4200), tok(",", 4200, 4250), tok(" no", 4300, 4700),
                tok(".", 4700, 4800)]},
]}
SEGMENTS = {"transcription": [
    {"timestamps": {"from": "00:00:00,000", "to": "00:00:02,600"}, "offsets": {"from": 0, "to": 2600},
     "text": " No vamos a subir las tarifas."},
    {"timestamps": {"from": "00:00:03,500", "to": "00:00:05,000"}, "offsets": {"from": 3500, "to": 5000},
     "text": " Este año, no."},
]}
SRT = "1\n00:00:00,000 --> 00:00:02,600\nNo vamos a subir las tarifas.\n\n2\n00:00:03,500 --> 00:00:05,000\nEste año, no.\n"


class VideoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, data):
        p = self.dir / name
        p.write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return p

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = V.main([str(a) for a in argv])
        return code, (json.loads(out.getvalue()) if code == 0 else None), err.getvalue()

    def test_parse_time_formats(self):
        self.assertEqual(V.parse_time("01:02"), 62.0)
        self.assertEqual(V.parse_time("00:01:02,500"), 62.5)
        self.assertEqual(V.parse_time("1:00:00.25"), 3600.25)
        self.assertEqual(V.parse_time(12.5), 12.5)
        for bad in ("-1", "1:xx", "", "1:2:3:4", True):
            with self.subTest(bad=bad), self.assertRaises(V.VideoError):
                V.parse_time(bad)

    def test_tokens_merge_into_words_and_skip_special(self):
        _, words, kind = V.load_transcript(self.write("t.json", FULL))
        self.assertEqual(kind, "whisper-json-full")
        self.assertEqual([w["text"] for w in words], ["No", "vamos", "a", "subir", "las", "tarifas.", "Este", "año,", "no."])
        subir = words[3]
        self.assertEqual((subir["start"], subir["end"]), (0.8, 1.2))

    def test_segment_json_and_srt_have_no_word_timing(self):
        for name, data, kind in (("s.json", SEGMENTS, "whisper-json"), ("s.srt", SRT, "srt")):
            segs, words, got = V.load_transcript(self.write(name, data))
            self.assertIsNone(words)
            self.assertEqual(got, kind)
            self.assertEqual(segs[1]["start"], 3.5)

    def test_karaoke_refused_without_word_timing_unless_estimated(self):
        t = self.write("s.json", SEGMENTS)
        code, _, err = self.run_cli("subtitulos", "--transcripcion", t, "--salida", self.dir / "a.ass")
        self.assertEqual(code, 2)
        self.assertIn("--palabras", err)
        code, res, _ = self.run_cli("subtitulos", "--transcripcion", t, "--salida", self.dir / "b.ass", "--estimar-palabras")
        self.assertEqual(code, 0)
        self.assertTrue(any("ESTIMADOS" in n for n in res["avisos"]))
        code, res, _ = self.run_cli("subtitulos", "--transcripcion", t, "--salida", self.dir / "c.ass", "--estilo", "frase")
        self.assertEqual(code, 0)

    def test_ass_header_resolution_and_literal_text(self):
        t = self.write("t.json", FULL)
        code, res, _ = self.run_cli("subtitulos", "--transcripcion", t, "--salida", self.dir / "r.ass", "--formato", "9:16")
        self.assertEqual(code, 0)
        text = (self.dir / "r.ass").read_text(encoding="utf-8")
        self.assertIn("PlayResX: 1080", text)
        self.assertIn("PlayResY: 1920", text)
        self.assertIn("{\\c&H00356BFF", text)  # #FF6B35 en orden BGR
        plain = " ".join(__import__("re").sub(r"\{[^}]*\}", "", l.split(",", 9)[9]).replace("\\N", " ")
                         for l in text.splitlines() if l.startswith("Dialogue")).split()
        self.assertIn("tarifas.", plain)
        self.assertEqual(res["palabras"], 9)

    def test_blocks_break_on_sentence_end_and_pause(self):
        _, words, _ = V.load_transcript(self.write("t.json", FULL))
        blocks = V.group_blocks(words, 22)
        self.assertEqual(blocks[0][-1]["text"], "tarifas.")
        self.assertEqual(blocks[1][0]["text"], "Este")

    def test_karaoke_durations_match_words(self):
        _, words, _ = V.load_transcript(self.write("t.json", FULL))
        text, n = V.build_ass(words[:3], estilo="karaoke")
        self.assertEqual(n, 1)
        self.assertIn("{\\kf30}No", text)
        self.assertIn("{\\kf40}vamos", text)

    def test_clip_shifts_times(self):
        t = self.write("t.json", FULL)
        code, _, _ = self.run_cli("palabras", "--transcripcion", t, "--salida", self.dir / "w.json", "--desde", "3", "--hasta", "4.5")
        self.assertEqual(code, 0)
        words = json.loads((self.dir / "w.json").read_text(encoding="utf-8"))
        self.assertEqual([w["text"] for w in words], ["Este", "año,", "no."])
        self.assertEqual(words[0]["id"], "w0")
        self.assertEqual(words[0]["start"], 0.5)
        self.assertLessEqual(words[-1]["end"], 1.5)

    def test_ass_control_characters_refused(self):
        bad = {"transcription": [{"offsets": {"from": 0, "to": 900}, "text": " a {b}",
                                  "tokens": [tok(" a", 0, 300), tok(" {\\b1}", 300, 900)]}]}
        code, _, err = self.run_cli("subtitulos", "--transcripcion", self.write("b.json", bad), "--salida", self.dir / "x.ass")
        self.assertEqual(code, 2)
        self.assertIn("llaves", err)

    def test_never_overwrites(self):
        t = self.write("t.json", FULL)
        existing = self.write("ya.ass", "original")
        code, _, err = self.run_cli("subtitulos", "--transcripcion", t, "--salida", existing)
        self.assertEqual(code, 2)
        self.assertEqual(existing.read_text(encoding="utf-8"), "original")

    def test_cut_plan_shows_context_and_does_not_run(self):
        media = self.write("entrevista.mp4", "no es un video real")
        cuts = self.write("cortes.json", {"cortes": [{"id": "c1", "desde": "00:00:00", "hasta": "00:00:02.6",
                                                      "cita": "No vamos a subir las tarifas."}]})
        code, res, _ = self.run_cli("cortes", "--fuente", media, "--lista", cuts, "--salida-dir", self.dir / "out",
                                    "--transcripcion", self.write("t.json", SEGMENTS), "--formato", "9:16")
        self.assertEqual(code, 0)
        self.assertFalse(res["ejecutado"])
        self.assertFalse((self.dir / "out").exists())
        item = res["cortes"][0]
        self.assertEqual(item["contexto"]["despues"], "Este año, no.")
        cmd = item["comando"]
        self.assertEqual(cmd[cmd.index("-ss") + 1], "0.000")
        self.assertEqual(cmd[cmd.index("-t") + 1], "2.600")
        self.assertIn("-n", cmd)
        self.assertIn("crop=1080:1920", cmd[cmd.index("-vf") + 1])
        self.assertEqual(len(res["original"]["sha256"]), 64)

    def test_cut_list_validation(self):
        media = self.write("m.mp4", "x")
        for cuts, msg in (({"cortes": [{"id": "a", "desde": 5, "hasta": 2}]}, "mayor"),
                          ({"cortes": [{"id": "a b", "desde": 0, "hasta": 2}]}, "inválido"),
                          ({"cortes": [{"id": "a", "desde": 0, "hasta": 1}, {"id": "a", "desde": 1, "hasta": 2}]}, "repetido"),
                          ({"cortes": []}, "cortes")):
            with self.subTest(msg=msg):
                code, _, err = self.run_cli("cortes", "--fuente", media, "--lista", self.write("c.json", cuts),
                                            "--salida-dir", self.dir / "o")
                self.assertEqual(code, 2)
                self.assertIn(msg, err)

    def test_burn_requires_simple_ass_name(self):
        video = self.write("v.mp4", "x")
        subs = self.write("mal nombre.ass", "x")
        code, _, err = self.run_cli("quemar", "--video", video, "--subtitulos", subs, "--salida", self.dir / "o.mp4")
        self.assertEqual(code, 2)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg no disponible")
class VideoFfmpegTests(unittest.TestCase):
    def test_real_cut_and_burn(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            src = d / "fuente.mp4"
            subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=gray:size=640x360:rate=25",
                            "-f", "lavfi", "-i", "sine=frequency=440", "-t", "6", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", str(src)], check=True, timeout=120)
            before = V.sha256(src)
            (d / "t.json").write_text(json.dumps(FULL), encoding="utf-8")
            (d / "c.json").write_text(json.dumps({"cortes": [{"id": "c1", "desde": 0, "hasta": 2.6, "cita": "x"}]}), encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(V.main(["cortes", "--fuente", str(src), "--lista", str(d / "c.json"), "--salida-dir",
                                         str(d / "out"), "--formato", "9:16", "--ejecutar"]), 0)
            clip = d / "out" / "c1.mp4"
            self.assertAlmostEqual(V.ffprobe_duration(clip), 2.6, delta=0.15)
            self.assertTrue((d / "out" / "registro-cortes.json").is_file())
            with redirect_stdout(io.StringIO()):
                self.assertEqual(V.main(["subtitulos", "--transcripcion", str(d / "t.json"), "--hasta", "2.6",
                                         "--salida", str(d / "out" / "c1.ass")]), 0)
                self.assertEqual(V.main(["quemar", "--video", str(clip), "--subtitulos", str(d / "out" / "c1.ass"),
                                         "--salida", str(d / "out" / "c1-subtitulado.mp4"), "--ejecutar"]), 0)
            self.assertTrue((d / "out" / "c1-subtitulado.mp4").stat().st_size > 0)
            self.assertEqual(V.sha256(src), before)


if __name__ == "__main__":
    unittest.main()
