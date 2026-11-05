import copy
import importlib.util
from pathlib import Path
import unittest
spec = importlib.util.spec_from_file_location('validator', Path(__file__).parents[1]/'scripts'/'validate_report.py')
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)

class ReportValidationTests(unittest.TestCase):
    def setUp(self):
        self.source = 'El presupuesto pasó de 100 a 125 millones.'
        self.report = {'extracted_claim_ids':['c1'], 'claims':[{'id':'c1','quote':self.source,'status':'supported','rationale':'Coincide con el documento ficticio.','sources':[{'file':'evidencias.txt','locator':'línea 3','evidence':'100 y 125 millones'}]}]}
    def test_valid_local(self): self.assertEqual(v.validate(self.source,self.report),[])
    def test_wrong_quote(self):
        self.report['claims'][0]['quote']='El presupuesto fue de 200.'
        self.assertTrue(v.validate(self.source,self.report))
    def test_missing_claim(self):
        self.report['extracted_claim_ids'].append('c2'); self.assertTrue(v.validate(self.source,self.report))
    def test_duplicate(self):
        self.report['claims']*=2; self.assertTrue(v.validate(self.source,self.report))
    def test_unsupported_no_evidence(self):
        self.report['claims'][0]['sources']=[]; self.assertTrue(v.validate(self.source,self.report))
    def test_unresolved_requires_reason(self):
        c=self.report['claims'][0]; c['status']='could_not_verify';c['sources']=[]
        self.assertTrue(v.validate(self.source,self.report));c['unresolved_reason']='not_researched'
        self.assertEqual(v.validate(self.source,self.report),[])
    def test_local_traversal(self):
        self.report['claims'][0]['sources'][0]['file']='../secret.txt';self.assertTrue(v.validate(self.source,self.report))
    def test_url_credentials(self):
        self.report['claims'][0]['sources']=[{'url':'https://a:b@example.org','evidence':'x'}]
        self.assertTrue(v.validate(self.source,self.report))
    def test_url_token(self):
        self.report['claims'][0]['sources']=[{'url':'https://example.org/?token=secret','evidence':'x'}]
        self.assertTrue(v.validate(self.source,self.report))
    def test_javascript(self):
        self.report['claims'][0]['sources']=[{'url':'javascript:alert(1)','evidence':'x'}]
        self.assertTrue(v.validate(self.source,self.report))
    def test_malformed_report(self): self.assertTrue(v.validate(self.source,[]))
    def test_unhashable_status(self):
        self.report['claims'][0]['status']=[];self.assertTrue(v.validate(self.source,self.report))
    def test_unhashable_reason(self):
        self.report['claims'][0]['status']='could_not_verify';self.report['claims'][0]['unresolved_reason']={}
        self.assertTrue(v.validate(self.source,self.report))
    def test_unknown_status(self):
        self.report['claims'][0]['status']='true';self.assertTrue(v.validate(self.source,self.report))

if __name__=='__main__': unittest.main()
