import json
from pathlib import Path
from urllib.parse import urlsplit
import unittest
ROOT=Path(__file__).resolve().parents[1]
class RegionalCatalogTests(unittest.TestCase):
    def setUp(self):self.catalog=json.loads((ROOT/'config/medios.json').read_text(encoding="utf-8"))
    def test_unique_verified_outlets(self):
        items=self.catalog['outlets'];self.assertIsInstance(items,list)
        self.assertEqual(len({m['id'] for m in items}),len(items))
        self.assertEqual(len({urlsplit(m['official_url']).hostname for m in items}),len(items))
        self.assertTrue(all(urlsplit(m['official_url']).scheme=='https' for m in items))
    def test_requested_five_country_routes(self):
        codes={p.stem.upper() for p in (ROOT/'config/countries').glob('*.json')}
        self.assertEqual(codes,{'AR','MX','PE','CO','CR'})
    def test_homonym_guidance(self):
        text=(ROOT/'skills/newsharness-onboarding/references/medios.md').read_text(encoding='utf-8')
        self.assertIn('nacion.com',text);self.assertIn('dominio',text)
    def test_country_reference_files_present(self):
        base=ROOT/'skills/newsharness-factcheck/references'
        for code in ('pe','co','cr'):
            p=base/f'fuentes-{code}.md';self.assertTrue(p.is_file(),str(p))
            self.assertIn('2026-11-01',p.read_text(encoding="utf-8"))
if __name__=='__main__':unittest.main()
