from pathlib import Path
import re
import json
import importlib.util
import unittest
ROOT=Path(__file__).resolve().parents[1]
class ContentContractTests(unittest.TestCase):
    def test_ten_skills_have_frontmatter(self):
        paths=list((ROOT/'skills').glob('*/SKILL.md'));self.assertEqual(len(paths),10)
        for p in paths:
            text=p.read_text(encoding="utf-8");self.assertTrue(text.startswith('---\n'),p)
            front=text.split('---',2)[1]
            self.assertRegex(front,r'(?m)^name: [a-z0-9-]+\s*$')
            self.assertRegex(front,r'(?m)^description:')
    def test_skill_relative_links_resolve(self):
        for p in (ROOT/'skills').rglob('*.md'):
            for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding="utf-8")):
                if '://' in link or link.startswith('#') or link.startswith('mailto:'):continue
                link=link.split('#')[0]
                self.assertTrue((p.parent/link).exists(),f'{p}: {link}')
    def test_expected_technical_fixtures(self):
        for name in ('ocr-es.png','mixto-es.pdf','silencio-10s.wav'):
            self.assertTrue((ROOT/'examples'/'pruebas-tecnicas'/name).is_file())
    def test_no_models_in_distribution(self):
        self.assertEqual(list(ROOT.rglob('*.bin')),[])
        self.assertEqual(list(ROOT.rglob('*.traineddata')),[])
if __name__=='__main__':unittest.main()
