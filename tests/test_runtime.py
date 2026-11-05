"""Offline regression tests. No network, package installs, or real ASR required."""
import argparse
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch, Mock
import wave

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("newsharness_runtime", ROOT / "scripts" / "newsharness.py")
newsharness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(newsharness)


def profile():
    return {"schema_version": 1, "newsroom": "Redacción de prueba",
            "journalist": {"name": "Ana Prueba", "signature": "Ana Prueba", "role": "Periodista",
                           "section": "Sociedad", "formats": ["noticia", "entrevista"]},
            "country": "AR", "language": "es", "timezone": "America/Argentina/Buenos_Aires",
            "privacy": {"allow_cloud_processing": False, "allow_public_archiving": False},
            "publication": {"human_approval_required": True}}


def report(available=4 * newsharness.GIB, disk=10 * newsharness.GIB, cores=8):
    return {"memory": {"available_bytes": available}, "cpu": {"logical_cores": cores},
            "disk": {"free_bytes": disk},
            "tools": {"tesseract": {"found": True, "languages": ["spa"]},
                      "ffmpeg": {"found": True}, "whisper-cli": {"found": False}},
            "optional_python": {"pypdfium2": {"found": True}, "PIL": {"found": True}}}


class TemporaryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="newsharness-test-")
        self.root = Path(self.temp.name).resolve()  # macOS /var -> /private/var; Windows 8.3 short names
        self.workspace = self.root / "workspace"
        self.profile_path = self.root / "profile.json"
        self.profile_path.write_text(json.dumps(profile()), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def init(self):
        return newsharness.initialize(self.workspace, self.profile_path)


class ProfileTests(TemporaryTest):
    def test_valid_expanded_editorial_profile(self):
        p = profile()
        p.update({"newsroom_url": "https://example.org", "style": {"tone": "sobrio"},
                  "bylines": [{"title": "Artículo", "url": "https://example.org/a", "published_at": "2026-01-01",
                               "consulted_at": "2026-11-01", "authorship_confirmed": True, "confidence": "high"}],
                  "rules": [{"rule": "Evitar adjetivos", "type": "inferred", "source_urls": ["https://example.org/a"],
                             "consulted_at": "2026-11-01T01:00:00Z", "approval": "pending", "evidence_limit": "Una sola muestra"}]})
        self.assertEqual(newsharness.validate_profile(p), p)

    def test_secret_top_level_rejected(self):
        p = profile(); p["api_key"] = "not-a-real-key"
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.validate_profile(p)

    def test_secret_nested_rejected(self):
        p = profile(); p["journalist"]["password"] = "not-a-real-password"
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.validate_profile(p)

    def test_credentials_in_url_rejected(self):
        for url in ("https://u:p@example.org/a", "https://example.org/a?api_key=secret"):
            p = profile(); p["newsroom_url"] = url
            with self.subTest(url=url), self.assertRaises(newsharness.NewsHarnessError):
                newsharness.validate_profile(p)

    def test_human_approval_cannot_be_disabled(self):
        p = profile(); p["publication"]["human_approval_required"] = False
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.validate_profile(p)

    def test_official_rule_requires_source(self):
        p = profile(); p["rules"] = [{"rule": "algo", "type": "explicit", "source_urls": [],
                                     "consulted_at": "2026-11-01", "approval": "approved"}]
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.validate_profile(p)

    def test_unknown_nested_keys_not_silently_ignored(self):
        p = profile(); p["privacy"]["upload_everything"] = True
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.validate_profile(p)

    def test_invalid_date_and_timezone(self):
        p = profile(); p["timezone"] = "../../etc/passwd"
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.validate_profile(p)
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.date_value("ayer", "consulted_at")

    def test_init_is_idempotent_and_refuses_different_profile(self):
        self.assertTrue(self.init()["created"])
        self.assertFalse(self.init()["created"])
        p = profile(); p["newsroom"] = "Otra"
        self.profile_path.write_text(json.dumps(p), encoding="utf-8")
        with self.assertRaises(newsharness.NewsHarnessError):
            self.init()
        self.assertEqual(json.loads((self.workspace / "profile.json").read_text(encoding="utf-8"))["newsroom"], "Redacción de prueba")


class PathTests(TemporaryTest):
    def test_traversal_and_absolute_refused(self):
        for path in ("../escape", "output/../../escape", "/tmp/escape", "..\\escape"):
            with self.subTest(path=path), self.assertRaises(newsharness.NewsHarnessError):
                newsharness.confined_path(self.root, path)

    def test_nested_relative_accepted_and_drive_relative_refused(self):
        # Regression: Windows renders nested Paths with "\", which must not count as a forbidden character.
        nested = newsharness.confined_path(self.root, Path("output") / "job" / "text.txt")
        self.assertEqual(nested, (self.root / "output" / "job" / "text.txt").resolve())
        if os.name == "nt":  # On POSIX "C:escape" is an ordinary file name.
            with self.assertRaises(newsharness.NewsHarnessError):
                newsharness.confined_path(self.root, "C:escape")

    @unittest.skipIf(os.name == "nt", "Symlink privileges vary on Windows")
    def test_escaping_symlink_refused(self):
        (self.root / "link").symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.confined_path(self.root, "link/escape")

    def test_existing_file_not_overwritten(self):
        f = self.root / "kept.txt"
        newsharness.write_new(f, "first")
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.write_new(f, "second")
        self.assertEqual(f.read_text(encoding="utf-8"), "first")

    def test_original_copy_is_content_addressed_and_reused(self):
        self.init()
        source = self.root / "audio.wav"
        source.write_bytes(b"original")
        first, digest = newsharness.preserve_original(self.workspace, source)
        second, digest2 = newsharness.preserve_original(self.workspace, source)
        self.assertEqual((first, digest), (second, digest2))
        self.assertEqual(source.read_bytes(), b"original")
        self.assertEqual(len(list((self.workspace / "originals").iterdir())), 1)

    def test_modified_copy_detected(self):
        self.init(); source = self.root / "a.wav"; source.write_bytes(b"original")
        dest, _ = newsharness.preserve_original(self.workspace, source)
        dest.write_bytes(b"tampered")
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.preserve_original(self.workspace, source)

    def test_external_tessdata_refused(self):
        self.init()
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.tessdata_path(self.workspace, self.root)

    def test_uninitialized_workspace_refused(self):
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.workspace_root(self.workspace)


class HardwareTests(unittest.TestCase):
    def test_linux_meminfo_fixture(self):
        memory = newsharness.parse_meminfo("MemTotal:       8000000 kB\nMemFree: 50000 kB\nMemAvailable: 2000000 kB\n")
        self.assertEqual(memory["total_bytes"], 8000000 * 1024)
        self.assertEqual(memory["available_bytes"], 2000000 * 1024)

    def test_unknown_available_not_confused_with_total(self):
        memory = newsharness.parse_meminfo("MemTotal: 8000000 kB\nMemFree: 10000 kB\n")
        self.assertIsNone(memory["available_bytes"])

    def test_macos_vm_stat_fixture(self):
        text = 'Mach Virtual Memory Statistics: (page size of 16384 bytes)\nPages free: 100.\nPages inactive: 200.\nPages speculative: 30.\n'
        self.assertEqual(newsharness.parse_vm_stat(text), 330 * 16384)
        self.assertIsNone(newsharness.parse_vm_stat("unknown"))

    def test_cgroup_limit_overrides_host_ram(self):
        result = newsharness.constrain_memory({"total_bytes": 64 * newsharness.GIB, "available_bytes": 32 * newsharness.GIB,
                                       "method": "linux"}, 4 * newsharness.GIB, 3 * newsharness.GIB)
        self.assertEqual(result["available_bytes"], newsharness.GIB)
        self.assertEqual(result["total_bytes"], 4 * newsharness.GIB)

    def test_unknown_container_used_stays_unknown(self):
        result = newsharness.constrain_memory({"total_bytes": 64 * newsharness.GIB, "available_bytes": 32 * newsharness.GIB,
                                       "method": "linux"}, 4 * newsharness.GIB, None)
        self.assertIsNone(result["available_bytes"])

    def test_default_base_with_known_ram(self):
        plan = newsharness.setup_plan(report())
        self.assertEqual(plan["quality"], "base")
        self.assertTrue(plan["needs_local_calibration"])
        self.assertEqual(plan["memory_status"], "provisional_ok")

    def test_unknown_ram_no_fabricated_readiness(self):
        plan = newsharness.setup_plan(report(available=None))
        self.assertEqual(plan["memory_status"], "unknown")
        self.assertEqual(plan["quality"], "base")

    def test_low_ram_never_silently_downgrades(self):
        plan = newsharness.setup_plan(report(available=1000), "small")
        self.assertEqual(plan["quality"], "small")
        self.assertEqual(plan["memory_status"], "insufficient_planning_headroom")
        self.assertFalse(plan["silent_downgrade"])

    def test_tiny_requires_explicit_consent(self):
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.setup_plan(report(), "tiny")
        self.assertEqual(newsharness.setup_plan(report(), "tiny", True)["quality"], "tiny")

    def test_cpu_unknown_and_disk_low(self):
        plan = newsharness.setup_plan(report(cores=None, disk=100))
        self.assertEqual(plan["threads"], 1)
        self.assertEqual(plan["disk_status"], "insufficient_planning_headroom")


class SubprocessTests(unittest.TestCase):
    def test_shell_string_refused(self):
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.run("echo unsafe; rm -f something")

    def test_timeout_actionable(self):
        with self.assertRaisesRegex(newsharness.NewsHarnessError, "excedió"):
            newsharness.run([sys.executable, "-c", "import time; time.sleep(3)"], timeout=0.05)

    @unittest.skipIf(os.name == "nt", "POSIX group regression; Windows uses taskkill tree")
    def test_outer_timeout_stops_nested_kit_process(self):
        with tempfile.TemporaryDirectory() as folder:
            marker = Path(folder) / "late.txt"
            payload = f"import time,pathlib; time.sleep(0.5); pathlib.Path({str(marker)!r}).write_text('late')"
            child = (f"import sys; sys.path.insert(0, {str(ROOT / 'scripts')!r}); import newsharness; "
                     f"newsharness.run([sys.executable,'-c',{payload!r}], timeout=5)")
            with self.assertRaises(newsharness.NewsHarnessError):
                newsharness.run([sys.executable, "-c", child], timeout=0.2)
            time.sleep(0.6)
            self.assertFalse(marker.exists())

    def test_shell_metacharacters_are_literal_arguments(self):
        result = newsharness.run([sys.executable, "-c", "import sys; print(sys.argv[1])", "literal;not-a-command"])
        self.assertEqual(result.stdout.strip(), "literal;not-a-command")

    def test_whisper_flags_cpu_no_translation_or_cloud(self):
        args = newsharness.whisper_command("whisper-cli", "/model.bin", "/audio.wav", "/out", "es", 4)
        self.assertIn("--no-gpu", args)
        self.assertIn("--output-srt", args)
        self.assertNotIn("--translate", args)
        self.assertNotIn("--no-timestamps", args)

    def test_unsafe_whisper_parameters_refused(self):
        for language in ("es --translate", "--help", "es;rm -f x"):
            with self.subTest(language=language), self.assertRaises(newsharness.NewsHarnessError):
                newsharness.whisper_command("whisper", "m", "a", "out", language, 4)
        for threads in (0, 10000, True, "4 --translate"):
            with self.subTest(threads=threads), self.assertRaises(newsharness.NewsHarnessError):
                newsharness.whisper_command("whisper", "m", "a", "out", "es", threads)

    def test_vad_only_when_model_explicit(self):
        self.assertNotIn("--vad", newsharness.whisper_command("w", "m", "a", "o", "es", 1))
        self.assertIn("--vad", newsharness.whisper_command("w", "m", "a", "o", "es", 1, "vad.bin"))


class ModelTests(TemporaryTest):
    def fake_model(self, quality="base", vocab=51865, ftype=2009):
        m = newsharness.MODELS[quality]
        path = self.root / m["filename"]
        path.write_bytes(struct.pack("<12i", 0x67676d6c, vocab, 1500, m["state"], m["heads"], m["layers"],
                                     448, m["state"], m["heads"], m["layers"], 80, ftype) + b"\x00" * 1_000_000)
        return path

    def test_quality_filename_mismatch(self):
        model = self.fake_model("small")
        with self.assertRaisesRegex(newsharness.NewsHarnessError, "no coincide"):
            newsharness.validate_model(model, "base")

    def test_renamed_small_model_rejected(self):
        model = self.fake_model("small")
        target = self.root / "ggml-base-q5_1.bin"; model.rename(target)
        with self.assertRaisesRegex(newsharness.NewsHarnessError, "arquitectura"):
            newsharness.validate_model(target, "base")

    def test_english_only_rejected_even_if_renamed(self):
        model = self.fake_model(vocab=51864)
        with self.assertRaisesRegex(newsharness.NewsHarnessError, "multilingüe"):
            newsharness.validate_model(model, "base")

    def test_wrong_quantization_rejected(self):
        model = self.fake_model(ftype=2008)
        with self.assertRaisesRegex(newsharness.NewsHarnessError, "Q5_1"):
            newsharness.validate_model(model, "base")

    def test_correct_header_is_not_enough_hash_must_match(self):
        model = self.fake_model()
        with self.assertRaisesRegex(newsharness.NewsHarnessError, "SHA256"):
            newsharness.validate_model(model, "base")

    def test_valid_header_with_mocked_official_hash(self):
        model = self.fake_model()
        digest = next(a["sha256"] for a in newsharness.read_json(ROOT / "config/toolchain.lock.json")["artifacts"] if a["filename"] == model.name)
        with patch.object(newsharness, "sha256", return_value=digest):
            self.assertEqual(newsharness.validate_model(model, "base"), model)


class ArtifactTests(TemporaryTest):
    def artifact(self):
        return copy.deepcopy(newsharness.read_json(ROOT / "config/toolchain.lock.json")["artifacts"][0])

    def test_all_shipped_artifacts_are_pinned_and_valid(self):
        for artifact in newsharness.read_json(ROOT / "config/toolchain.lock.json")["artifacts"]:
            self.assertIs(newsharness.validate_artifact(artifact), artifact)

    def test_missing_hash_or_revision_refused(self):
        for key in ("sha256", "revision"):
            artifact = self.artifact(); artifact[key] = ""
            with self.subTest(key=key), self.assertRaises(newsharness.NewsHarnessError):
                newsharness.validate_artifact(artifact)

    def test_mutable_or_arbitrary_url_refused(self):
        for url in ("http://example.org/model", "https://huggingface.co/evil/model/resolve/" + "a" * 40 + "/m.bin",
                    "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/m.bin"):
            artifact = self.artifact(); artifact["url"] = url
            with self.subTest(url=url), self.assertRaises(newsharness.NewsHarnessError):
                newsharness.validate_artifact(artifact)

    def test_download_filename_path_traversal_refused(self):
        artifact = self.artifact(); artifact["filename"] = "../escape.bin"
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.validate_artifact(artifact)

    def test_executable_artifact_refused(self):
        artifact = self.artifact(); artifact["filename"] = "installer.exe"
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.validate_artifact(artifact)

    def test_fetch_without_approval_does_not_open_network(self):
        with patch.object(newsharness.urllib.request, "build_opener") as network:
            with self.assertRaisesRegex(newsharness.NewsHarnessError, "autorización"):
                newsharness.fetch_artifact(self.workspace, "whisper-base-q5_1", False)
            network.assert_not_called()

    def test_unsafe_redirect_refused_before_contact(self):
        handler = newsharness.SafeRedirect()
        req = newsharness.urllib.request.Request("https://huggingface.co/ok")
        for url in ("http://cdn-lfs.huggingface.co/model", "https://evil.example/model", "https://127.0.0.1/model"):
            with self.subTest(url=url), self.assertRaises(newsharness.NewsHarnessError):
                handler.redirect_request(req, None, 302, "Found", {}, url)

    def test_download_verifies_before_save_and_reuses(self):
        self.init()
        payload = b"test model data"
        artifact = self.artifact()
        artifact.update(sha256=hashlib.sha256(payload).hexdigest(), size_bytes=len(payload), max_bytes=len(payload))
        actual_read = newsharness.read_json
        def read(path):
            return {"artifacts": [artifact]} if Path(path).name == "toolchain.lock.json" else actual_read(path)
        opener = Mock()
        opener.open.return_value = io.BytesIO(payload)
        with patch.object(newsharness, "read_json", side_effect=read), patch.object(newsharness.urllib.request, "build_opener", return_value=opener):
            result = newsharness.fetch_artifact(self.workspace, artifact["id"], True)
            self.assertTrue(result["sha256_verified"])
            self.assertEqual(Path(result["path"]).read_bytes(), payload)
            second = newsharness.fetch_artifact(self.workspace, artifact["id"], True)
            self.assertFalse(second["downloaded"])
            self.assertEqual(opener.open.call_count, 1)

    def test_bad_hash_leaves_no_model_or_partial_file(self):
        self.init()
        artifact = self.artifact(); artifact["max_bytes"] = 100
        actual_read = newsharness.read_json
        def read(path):
            return {"artifacts": [artifact]} if Path(path).name == "toolchain.lock.json" else actual_read(path)
        opener = Mock(); opener.open.return_value = io.BytesIO(b"tampered")
        with patch.object(newsharness, "read_json", side_effect=read), patch.object(newsharness.urllib.request, "build_opener", return_value=opener):
            with self.assertRaisesRegex(newsharness.NewsHarnessError, "SHA256"):
                newsharness.fetch_artifact(self.workspace, artifact["id"], True)
        self.assertEqual(list((self.workspace / "models").iterdir()), [])

    def test_failed_promotion_leaves_no_partial_and_retry_succeeds(self):
        self.init(); payload = b"test data"
        artifact = self.artifact()
        artifact.update(sha256=hashlib.sha256(payload).hexdigest(), size_bytes=len(payload), max_bytes=len(payload))
        actual_read = newsharness.read_json
        def read(path):
            return {"artifacts": [artifact]} if Path(path).name == "toolchain.lock.json" else actual_read(path)
        opener = Mock(); opener.open.side_effect = lambda *a, **k: io.BytesIO(payload)
        with patch.object(newsharness, "read_json", side_effect=read), patch.object(newsharness.urllib.request, "build_opener", return_value=opener):
            with patch.object(newsharness.os, "link", side_effect=OSError("disk full")):
                with self.assertRaises(newsharness.NewsHarnessError):
                    newsharness.fetch_artifact(self.workspace, artifact["id"], True)
            self.assertEqual(list((self.workspace / "models").iterdir()), [])
            self.assertTrue(newsharness.fetch_artifact(self.workspace, artifact["id"], True)["downloaded"])


class OCRTests(TemporaryTest):
    def test_nonempty_worker_directory_rejected_before_decoder(self):
        job = self.root / "job"; job.mkdir(); (job / "existing.txt").write_text("keep", encoding="utf-8")
        with patch.object(newsharness, "ocr_image") as decoder, self.assertRaises(newsharness.NewsHarnessError):
            newsharness.ocr_document(Path("a.png"), job, "spa", None, 10, 10)
        decoder.assert_not_called()
        self.assertEqual((job / "existing.txt").read_text(encoding="utf-8"), "keep")

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow not installed; without it OCR refuses images earlier")
    def test_text_disguised_as_image_rejected_before_tesseract(self):
        image = self.root / "not-image.png"; image.write_text("This is text, not an image.\n", encoding="utf-8")
        with patch.object(newsharness, "tool_required", return_value="tesseract"), patch.object(newsharness, "available_languages", return_value=["spa"]), patch.object(newsharness, "run") as decoder:
            with self.assertRaisesRegex(newsharness.NewsHarnessError, "Imagen inválida"):
                newsharness.ocr_image(image, self.root / "out", "spa", None, 10)
            decoder.assert_not_called()

    def test_missing_spanish_does_not_fallback_to_english(self):
        with patch.object(newsharness, "tool_required", return_value="tesseract"), patch.object(newsharness, "available_languages", return_value=["eng"]), patch.object(newsharness, "run") as run:
            with self.assertRaisesRegex(newsharness.NewsHarnessError, "no se sustituirá"):
                newsharness.ocr_image(Path("a.png"), Path("out"), "spa", None, 10)
            run.assert_not_called()

    def test_unsafe_ocr_language_rejected(self):
        with patch.object(newsharness, "tool_required", return_value="tesseract"):
            with self.assertRaises(newsharness.NewsHarnessError):
                newsharness.ocr_image(Path("a.png"), Path("out"), "spa --help", None, 10)

    def test_pdf_existing_text_does_not_invoke_ocr(self):
        textpage = Mock()
        textpage.__enter__ = Mock(return_value=textpage)
        textpage.__exit__ = Mock(return_value=False)
        textpage.get_text_range.return_value = "Texto existente 123"
        page = Mock()
        page.__enter__ = Mock(return_value=page)
        page.__exit__ = Mock(return_value=False)
        page.get_textpage.return_value = textpage
        pdf = Mock()
        pdf.__enter__ = Mock(return_value=pdf)
        pdf.__exit__ = Mock(return_value=False)
        pdf.__len__ = Mock(return_value=1)
        pdf.__getitem__ = Mock(return_value=page)
        fake = Mock(); fake.PdfDocument.return_value = pdf
        job = self.root / "job"; job.mkdir()
        with patch.dict(sys.modules, {"pypdfium2": fake}), patch.object(newsharness, "ocr_image") as ocr:
            pages = newsharness.ocr_document(Path("a.pdf"), job, "spa", None, 10, 10)
            ocr.assert_not_called()
        self.assertEqual(pages[0]["method"], "existing_text")
        self.assertIn("123", (job / "text.txt").read_text(encoding="utf-8"))
        textpage.close.assert_called_once()
        page.close.assert_called_once()


class AudioTests(TemporaryTest):
    def make_wav(self, data):
        path = self.root / "sample.wav"
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(16000)
            wav.writeframes(data)
        return path

    def test_digital_silence_detected_without_asr(self):
        self.assertTrue(newsharness.wav_is_digital_silence(self.make_wav(b"\x00\x00" * 16000)))

    def test_nonzero_audio_not_labeled_silence(self):
        self.assertFalse(newsharness.wav_is_digital_silence(self.make_wav(b"\x00\x00" * 16000 + b"\x01\x00")))

    def test_calibration_requires_representative_sample_length(self):
        with contextlib.redirect_stderr(io.StringIO()):
            status = newsharness.main(["calibrate", "--workspace", "missing", "--input", "missing", "--model", "missing", "--sample-seconds", "1"])
        self.assertEqual(status, 2)


class InstallationTests(TemporaryTest):
    def bundle(self):
        bundle = self.root / "bundle"
        (bundle / "skills/newsharness-example").mkdir(parents=True)
        (bundle / "skills/newsharness-example/SKILL.md").write_text("---\nname: newsharness-example\n---\nExample", encoding="utf-8")
        (bundle / "scripts").mkdir(); (bundle / "scripts/newsharness.py").write_text("# runtime", encoding="utf-8")
        (bundle / "config").mkdir(); (bundle / "config/toolchain.lock.json").write_text("{}", encoding="utf-8")
        for agent, filename in (("codex", "AGENTS.md"), ("claude", "CLAUDE.md"), ("opencode", "AGENTS.md")):
            (bundle / "adapters" / agent).mkdir(parents=True)
            (bundle / "adapters" / agent / filename).write_text("NewsHarness bridge", encoding="utf-8")
        return bundle

    def test_install_is_project_local_and_idempotent(self):
        bundle = self.bundle(); project = self.root / "project"
        with patch.object(newsharness, "ROOT", bundle):
            result = newsharness.install_skills(project, "codex")
            self.assertGreater(result["created_files"], 0)
            second = newsharness.install_skills(project, "codex")
            self.assertEqual(second["created_files"], 0)
        self.assertTrue((project / ".agents/skills/newsharness-example/SKILL.md").is_file())
        self.assertTrue((project / ".newsharness-kit/scripts/newsharness.py").is_file())

    def test_existing_project_bridge_preserved(self):
        bundle = self.bundle(); project = self.root / "project"; project.mkdir()
        (project / "AGENTS.md").write_text("User rules", encoding="utf-8")
        with patch.object(newsharness, "ROOT", bundle):
            result = newsharness.install_skills(project, "codex")
        self.assertTrue(result["manual_bridge_merge_required"])
        self.assertEqual((project / "AGENTS.md").read_text(encoding="utf-8"), "User rules")
        self.assertEqual((project / "NEWSHARNESS-CODEX.md").read_text(encoding="utf-8"), "NewsHarness bridge")

    def test_conflicting_skill_preflight_prevents_partial_install(self):
        bundle = self.bundle(); project = self.root / "project"
        target = project / ".claude/skills/newsharness-example/SKILL.md"
        target.parent.mkdir(parents=True); target.write_text("My edited skill", encoding="utf-8")
        with patch.object(newsharness, "ROOT", bundle), self.assertRaises(newsharness.NewsHarnessError):
            newsharness.install_skills(project, "claude")
        self.assertFalse((project / ".newsharness-kit").exists())
        self.assertEqual(target.read_text(encoding="utf-8"), "My edited skill")


class GlobalInstallationTests(TemporaryTest):
    bundle = InstallationTests.bundle

    def setUp(self):
        super().setUp()
        self.home = self.root / "home"; self.home.mkdir()
        self.src = self.bundle()
        patcher = patch.object(newsharness, "ROOT", self.src); patcher.start(); self.addCleanup(patcher.stop)
        env = patch.dict(os.environ, {}, clear=False); env.start(); self.addCleanup(env.stop)
        for key in ("CODEX_HOME", "XDG_CONFIG_HOME"):
            os.environ.pop(key, None)

    def test_global_install_idempotent_and_leaves_global_instructions_alone(self):
        (self.home / ".claude").mkdir(); (self.home / ".claude/CLAUDE.md").write_text("Mis reglas", encoding="utf-8")
        result = newsharness.install_global("claude", home=self.home)
        self.assertGreater(result["created_files"], 0)
        self.assertFalse(result["global_instructions_modified"])
        self.assertTrue((self.home / ".claude/skills/newsharness-example/SKILL.md").is_file())
        self.assertTrue((self.home / ".newsharness-kit/scripts/newsharness.py").is_file())
        self.assertEqual((self.home / ".claude/CLAUDE.md").read_text(encoding="utf-8"), "Mis reglas")
        again = newsharness.install_global("claude", home=self.home)
        self.assertEqual((again["created_files"], again["replaced_files"]), (0, 0))

    def test_agent_folders(self):
        newsharness.install_global("opencode", home=self.home)
        self.assertTrue((self.home / ".config/opencode/skills/newsharness-example/SKILL.md").is_file())
        os.environ["CODEX_HOME"] = str(self.root / "codex-home")
        newsharness.install_global("codex", home=self.home)
        self.assertTrue((self.root / "codex-home/skills/newsharness-example/SKILL.md").is_file())

    def test_new_version_requires_update_and_spares_user_edits(self):
        newsharness.install_global("claude", home=self.home)
        skill = self.src / "skills/newsharness-example/SKILL.md"
        skill.write_text("---\nname: newsharness-example\n---\nVersion 2", encoding="utf-8")
        with self.assertRaisesRegex(newsharness.NewsHarnessError, "--update"):
            newsharness.install_global("claude", home=self.home)
        result = newsharness.install_global("claude", update=True, home=self.home)
        self.assertEqual(result["replaced_files"], 2)  # agent skill + copy inside ~/.newsharness-kit
        installed = self.home / ".claude/skills/newsharness-example/SKILL.md"
        self.assertIn("Version 2", installed.read_text(encoding="utf-8"))
        installed.write_text("Editado por la periodista", encoding="utf-8")
        skill.write_text("---\nname: newsharness-example\n---\nVersion 3", encoding="utf-8")
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.install_global("claude", update=True, home=self.home)
        self.assertEqual(installed.read_text(encoding="utf-8"), "Editado por la periodista")

    def test_update_removes_unmodified_files_dropped_from_new_version(self):
        extra = self.src / "skills/newsharness-example/old.md"; extra.write_text("old", encoding="utf-8")
        newsharness.install_global("claude", home=self.home)
        extra.unlink()
        newsharness.install_global("claude", update=True, home=self.home)
        self.assertFalse((self.home / ".claude/skills/newsharness-example/old.md").exists())

    def test_uninstall_removes_only_unmodified_kit_files(self):
        newsharness.install_global("claude", home=self.home)
        newsharness.install_global("opencode", home=self.home)
        mine = self.home / ".claude/skills/mi-skill/SKILL.md"; mine.parent.mkdir(parents=True); mine.write_text("mía", encoding="utf-8")
        first = newsharness.install_global("claude", uninstall=True, home=self.home)
        self.assertFalse((self.home / ".claude/skills/newsharness-example").exists())
        self.assertTrue((self.home / ".newsharness-kit").is_dir(), "opencode still needs the kit")
        self.assertFalse(first["kit_removed"])
        (self.home / ".newsharness-kit/notas.txt").write_text("no es del kit", encoding="utf-8")
        newsharness.install_global("opencode", uninstall=True, home=self.home)
        self.assertTrue(mine.is_file())
        self.assertFalse((self.home / ".config/opencode/skills/newsharness-example").exists())
        self.assertTrue((self.home / ".newsharness-kit/notas.txt").is_file())
        self.assertFalse((self.home / ".newsharness-kit/scripts").exists())
        with self.assertRaises(newsharness.NewsHarnessError):
            newsharness.install_global("claude", uninstall=True, home=self.home)

    def test_update_flags_require_global(self):
        with contextlib.redirect_stderr(io.StringIO()):
            status = newsharness.main(["install-skills", "--project", str(self.root / "p"), "--agent", "claude", "--update"])
        self.assertEqual(status, 2)


if __name__ == "__main__":
    unittest.main()
