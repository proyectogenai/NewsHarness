import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('discourse', ROOT / 'scripts/validate_discourse.py')
D = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(D)
FIXTURE = ROOT / 'examples/discursos/ejercicio-sintetico'


class DiscourseTests(unittest.TestCase):
    def setUp(self):
        self.source = (FIXTURE / 'transcripcion.txt').read_bytes().decode('utf-8')
        self.inventory = json.loads((FIXTURE / 'inventario.json').read_text(encoding="utf-8"))
        self.report = json.loads((FIXTURE / 'informe-estructurado.json').read_text(encoding="utf-8"))

    def invalid(self, report=None, source=None, stage='research', contains=None):
        errors = D.validate(self.source if source is None else source, self.report if report is None else report, stage)
        self.assertTrue(errors)
        if contains:
            self.assertIn(contains, '\n'.join(errors))

    def test_inventory_and_reviewed_synthetic_fixtures(self):
        self.assertEqual(D.validate(self.source, self.inventory), [])
        self.assertEqual(D.validate(self.source, self.report, 'research'), [])
        self.assertEqual(D.validate(self.source, self.report, 'reviewed'), [])

    def test_real_case_is_partial_pending_not_fact_verified(self):
        folder = ROOT / 'examples/discursos/caso-real-ditella'
        source = (folder / 'extracto-oficial.txt').read_bytes().decode()
        report = json.loads((folder / 'inventario-fragmento.json').read_text(encoding="utf-8"))
        self.assertEqual(D.validate(source, report), [])
        self.assertEqual(report['coverage']['scope'], 'partial')
        self.assertIsNone(report['selection_decision_id'])
        self.assertIsNone(report['claims'][0]['assessment'])
        self.assertIsNone(report['claims'][0]['anchor']['time_start_seconds'])
        self.assertEqual(report['sources'][0]['independence_group'], report['sources'][1]['independence_group'])

    def test_original_hash_and_exact_quote(self):
        self.invalid(source=self.source + '\n', contains='original')
        self.report['claims'][0]['quote_original'] = 'Una cita mejorada inventada'
        self.invalid(contains='literalmente')

    def test_wrong_offset_and_paragraph(self):
        self.report['claims'][0]['anchor']['start'] += 1
        self.report['claims'][0]['anchor']['paragraph'] = 1
        self.invalid(contains='párrafo')

    def test_unknown_times_cannot_be_filled(self):
        self.report['claims'][0]['anchor']['time_start_seconds'] = 10
        self.invalid(contains='time_source')

    def timed(self):
        text = '[00:00] Introducción. [00:20] Frase de prueba. [00:25] Fin.'
        report = copy.deepcopy(self.inventory)
        report['source_sha256'] = hashlib.sha256(text.encode()).hexdigest()
        report['claims'] = [report['claims'][0]]
        claim = report['claims'][0]; quote = 'Frase de prueba.'
        claim['quote_original'] = quote
        claim['anchor'] = dict(start=text.index(quote), end=text.index(quote) + len(quote), paragraph=1,
                               time_start_seconds=20, time_end_seconds=25,
                               time_source=dict(start_cue='[00:20]', end_cue='[00:25]'))
        return text, report

    def test_literal_temporal_cues(self):
        text, report = self.timed()
        self.assertEqual(D.validate(text, report), [])

    def test_earlier_non_nearest_timecue_rejected(self):
        text, report = self.timed()
        anchor = report['claims'][0]['anchor']
        anchor['time_start_seconds'] = 0; anchor['time_source']['start_cue'] = '[00:00]'
        self.invalid(report, text, 'inventory', 'inicio temporal')

    def test_display_is_derived_not_rewritten(self):
        claim = self.inventory['claims'][0]; quote = claim['quote_original']
        claim.update(display_quote=quote[:7] + ' (…) ' + quote[25:], display_spans=[dict(start=0, end=7), dict(start=25, end=len(quote))], display_edit_note='Recorte visible de prueba, no reemplaza original.')
        self.assertEqual(D.validate(self.source, self.inventory), [])
        claim['display_quote'] += ' frase agregada'
        self.invalid(self.inventory, stage='inventory', contains='recortes')

    def test_no_research_without_selection(self):
        self.report['selection_decision_id'] = None
        self.invalid(contains='selección humana')

    def test_unselected_claim_kept_pending(self):
        self.report['human_decisions'][0]['claim_ids'].remove('C4')
        self.invalid(contains='no investigar')
        self.report['claims'][3]['assessment'] = None
        self.assertEqual(D.validate(self.source, self.report, 'research'), [])

    def test_agent_cannot_self_declare_human(self):
        self.report['human_decisions'][0]['actor'] = 'agente'
        self.invalid(contains='decisor humano')

    def test_synthetic_decision_cannot_be_reused_as_real(self):
        self.report['metadata']['provenance'] = 'user_supplied'
        self.invalid(contains='human_instruction')

    def test_missing_decision_reference(self):
        self.report['human_decisions'][0]['record_ref'] = {'locator': 'aquí'}
        self.invalid(contains='exactamente')

    def test_review_binds_content_version(self):
        self.report['claims'][0]['assessment']['rationale'] += ' Cambio posterior.'
        self.invalid(stage='reviewed', contains='cambió')

    def test_review_binds_selection_record(self):
        self.report['human_decisions'][0]['actor'] = 'Otra editora ficticia'
        self.invalid(stage='reviewed', contains='cambió')

    def test_earlier_review_cannot_hide_later_changes_requested(self):
        later = copy.deepcopy(self.report['human_decisions'][1])
        later.update(id='H3', outcome='changes_requested')
        self.report['human_decisions'].append(later)
        self.invalid(stage='reviewed', contains='posterior')

    def test_review_cannot_precede_selection_within_same_day(self):
        self.report['human_decisions'][0]['decided_at'] = '2026-11-01T18:00:00Z'
        self.report['human_decisions'][1]['decided_at'] = '2026-11-01T10:00:00Z'
        self.invalid(stage='reviewed', contains='antecede')

    def test_opinion_no_truth_score(self):
        self.report['claims'][3]['assessment']['status'] = 'supported'
        self.invalid(contains='not_fact_checked')

    def test_projection_not_scored_as_future_fact(self):
        self.report['claims'][1]['assessment']['status'] = 'contradicted'
        self.invalid(contains='awaiting_outcome')

    def test_future_promise_not_final_nonfulfillment(self):
        assessment = self.report['claims'][2]['assessment']
        assessment.update(status='not_fulfilled', temporal_basis='contemporaneous', evidence=[dict(source_id='S1', relation='contradicts', reason='Fixture solamente')])
        self.invalid(contains='plazo vencido')

    def test_missing_evidence_not_false(self):
        assessment = self.report['claims'][0]['assessment']
        assessment.update(status='contradicted', evidence=[])
        self.invalid(contains='ausencia de datos')

    def test_correlation_not_causal_proof(self):
        claim = self.report['claims'][0]
        claim['causal_claim'] = True
        claim['assessment'].update(causal_support='correlation_only', causal_limitations='No hay identificación causal.')
        self.invalid(contains='causalidad')

    def test_conclusion_needs_numeric_units_periods(self):
        self.report['sources'][0]['observations'] = []
        self.invalid(contains='valor/unidad/período')

    def test_later_publication_not_contemporaneous(self):
        self.report['sources'][0]['published_at'] = '2026-03-01'
        self.invalid(contains='posterior al discurso')

    def test_same_day_later_instant_not_contemporaneous(self):
        self.report['metadata']['emitted_at'] = '2026-02-01T10:00:00Z'
        self.report['sources'][0]['published_at'] = '2026-02-01T18:00:00Z'
        self.invalid(contains='posterior al discurso')

    def test_same_day_date_only_ambiguity_explicit(self):
        self.report['sources'][0]['published_at'] = '2026-02-01'
        self.invalid(contains='intradía')

    def test_later_revision_requires_note(self):
        assessment = self.report['claims'][0]['assessment']
        assessment['temporal_basis'] = 'later_revision'
        self.invalid(contains='revision_note')
        assessment['revision_note'] = 'Versión posterior: no afirmar que estaba disponible al hablar.'
        self.report['sources'][0]['published_at'] = '2026-03-01'
        self.assertEqual(D.validate(self.source, self.report, 'research'), [])

    def test_source_version_cycle(self):
        second = copy.deepcopy(self.report['sources'][0]); second.update(id='S2', supersedes='S1')
        self.report['sources'][0]['supersedes'] = 'S2'; self.report['sources'].append(second)
        self.invalid(contains='ciclo')

    def test_source_consulted_before_publication_same_day(self):
        self.report['sources'][0].update(published_at='2026-01-10T18:00:00Z', consulted_at='2026-01-10T10:00:00Z')
        self.invalid(contains='posterior a consulta')

    def test_references_no_traversal_or_credentials(self):
        for location in ({'file': '../secreto', 'locator': '1'}, {'url': 'https://u:p@example.org', 'locator': '1'}, {'url': 'https://example.org?token=x', 'locator': '1'}):
            with self.subTest(location=location):
                report = copy.deepcopy(self.report); report['sources'][0]['location'] = location
                self.invalid(report)

    def test_unknown_pattern_and_unsupported_pattern(self):
        claim = self.inventory['claims'][0]
        claim['patterns'] = [dict(id='excusa', hypothesis='No presumir intención', test='Buscar', alternative='Puede ser correcto', status='supported', source_ids=[])]
        self.invalid(self.inventory, stage='inventory', contains='valor no admitido')

    def test_expression_is_data_not_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            sentinel = Path(folder) / 'should-not-exist'
            self.report['claims'][0]['assessment']['calculations'][0]['expression'] = f"open({str(sentinel)!r}, 'w').write('never')"
            self.assertEqual(D.validate(self.source, self.report, 'research'), [])
            self.assertFalse(sentinel.exists())

    def test_unknown_keys_and_duplicate_ids(self):
        self.report['api_key'] = 'not-real'
        self.report['claims'].append(copy.deepcopy(self.report['claims'][0]))
        self.invalid(contains='desconocidos')

    def test_malformed_nested_values_return_errors(self):
        cases = [None, [], 'bad', True, {'x': 1}]
        for value in cases:
            for container, key in [('root', 'claims'), ('claim', 'kind'), ('assessment', 'status'), ('source', 'observations')]:
                report = copy.deepcopy(self.report)
                target = report if container == 'root' else report['claims'][0] if container == 'claim' else report['claims'][0]['assessment'] if container == 'assessment' else report['sources'][0]
                target[key] = value
                with self.subTest(container=container, value=value):
                    self.assertTrue(D.validate(self.source, report, 'research'))

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"id":"a","id":"b"}', object_pairs_hook=D.unique_object)

    def test_read_preserves_crlf_unicode_offsets(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'original.txt'
            original = 'Línea uno.\r\n\r\nLínea dos.\r\n'
            path.write_bytes(original.encode('utf-8'))
            self.assertEqual(D.read_limited(path), original)


if __name__ == '__main__':
    unittest.main()
