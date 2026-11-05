#!/usr/bin/env python3
"""Comprueba estructura/anclajes de discursos; no verifica verdad ni identidad humana.

No ejecuta expresiones, abre enlaces, escribe archivos ni autoriza publicación.
Los offsets son caracteres Unicode del original exacto, no bytes ni texto editado.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import parse_qsl, urlsplit

MAX_BYTES = 5_000_000
PATTERNS = {
    'comparative_base', 'series_and_vintage', 'denominator_and_units', 'coverage',
    'causal_attribution', 'stocks_flows_overlap', 'forecast_vs_observed',
    'definition', 'international_comparability',
}
STATUSES = {
    'fact': {'supported', 'contradicted', 'needs_context', 'unresolved'},
    'projection': {'methods_assessed', 'awaiting_outcome', 'unresolved'},
    'promise': {'tracking', 'fulfilled', 'partly_fulfilled', 'not_fulfilled', 'unresolved'},
    'opinion': {'not_fact_checked'},
}
CONCLUSIONS = {'supported', 'contradicted', 'needs_context', 'methods_assessed',
               'fulfilled', 'partly_fulfilled', 'not_fulfilled'}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def iso_date(value):
    if not isinstance(value, str):
        return None
    try:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:T.+)?', value):
            return None
        parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        if 'T' in value and parsed.tzinfo is None:
            return None
        return parsed.date()
    except ValueError:
        return None


def temporal_compare(left, right):
    """Return -1/0/1 where precision supports it, None for same-day date-only ambiguity."""
    a, b = iso_date(left), iso_date(right)
    if not a or not b:
        return None
    if 'T' in left and 'T' in right:
        x = dt.datetime.fromisoformat(left.replace('Z', '+00:00'))
        y = dt.datetime.fromisoformat(right.replace('Z', '+00:00'))
        return (x > y) - (x < y)
    if a != b:
        return (a > b) - (a < b)
    return None


def cue_seconds(cue):
    if not isinstance(cue, str):
        return None
    match = re.fullmatch(r'\[(?:(\d{1,3}):)?(\d{1,3}):(\d{2})(?:\.(\d{1,3}))?\]', cue)
    if not match:
        return None
    hours, minutes, seconds, fraction = match.groups()
    if int(seconds) >= 60 or (hours is not None and int(minutes) >= 60):
        return None
    return int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds) + float('0.' + (fraction or '0'))


def paragraph_ranges(source):
    starts, cursor = [], 0
    for separator in re.finditer(r'\n[ \t\r]*\n(?:[ \t\r]*\n)*', source):
        starts.append((cursor, separator.start()))
        cursor = separator.end()
    starts.append((cursor, len(source)))
    return [(a, b) for a, b in starts if source[a:b].strip()]


def review_snapshot_sha256(report):
    """Bind recorded review to content+selection, excluding review records themselves."""
    content = {key: value for key, value in report.items() if key not in ('human_decisions', 'review_decision_id')}
    decisions = report.get('human_decisions', [])
    content['selection_record'] = next((record for record in decisions if isinstance(record, dict)
                                        and record.get('id') == report.get('selection_decision_id')), None) if isinstance(decisions, list) else None
    data = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(data).hexdigest()


class Validator:
    def __init__(self, source, stage):
        self.source, self.stage, self.errors = source, stage, []
        self.sources, self.claims, self.decisions = {}, {}, {}
        self.selected = set()
        self.as_of = self.emitted = None
        self.synthetic = False
        self.duration = None
        self.emitted_raw = self.as_of_raw = None

    def error(self, path, message):
        self.errors.append(f'{path}: {message}')

    def obj(self, value, required, optional, path):
        if not isinstance(value, dict):
            self.error(path, 'debe ser un objeto.'); return False
        missing, extra = set(required) - value.keys(), value.keys() - set(required) - set(optional)
        if missing:
            self.error(path, f'faltan campos {sorted(missing)}.')
        if extra:
            self.error(path, f'campos desconocidos {sorted(extra)}; no guardar secretos.')
        return not missing

    def text(self, value, path, nullable=False):
        if value is None and nullable:
            return True
        if not nonempty(value) or len(value) > 100_000:
            self.error(path, 'requiere texto no vacío acotado.'); return False
        return True

    def enum(self, value, allowed, path):
        if not isinstance(value, str) or value not in allowed:
            self.error(path, f'valor no admitido; opciones {sorted(allowed)}.'); return False
        return True

    def date(self, value, path, nullable=False):
        if value is None and nullable:
            return None
        result = iso_date(value)
        if result is None:
            self.error(path, 'fecha ISO requerida; desconocida debe ser null donde esté permitido.')
        return result

    def array(self, value, path):
        if not isinstance(value, list) or len(value) > 10000:
            self.error(path, 'requiere una lista acotada.'); return []
        return value

    def refs(self, value, registry, path):
        refs = self.array(value, path)
        good = []
        for item in refs:
            if not isinstance(item, str) or item not in registry:
                self.error(path, 'referencia desconocida o no textual.')
            else:
                good.append(item)
        if len(good) != len(set(good)):
            self.error(path, 'referencias duplicadas.')
        return good

    def location(self, value, path):
        if not self.obj(value, {'locator'}, {'url', 'file'}, path):
            return
        self.text(value.get('locator'), path + '.locator')
        url, file = value.get('url'), value.get('file')
        if bool(url) == bool(file):
            self.error(path, 'usar exactamente una URL o un archivo relativo.'); return
        if url:
            try:
                parsed = urlsplit(url)
                if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password:
                    raise ValueError()
                if any(re.search(r'token|secret|password|api.?key|signature', key, re.I)
                       for key, _ in parse_qsl(parsed.query)):
                    raise ValueError()
            except (ValueError, TypeError, AttributeError):
                self.error(path, 'URL inválida, no pública o con posibles credenciales.')
        else:
            if (not isinstance(file, str) or '\\' in file or ':' in file or
                    PurePosixPath(file).is_absolute() or '..' in PurePosixPath(file).parts or not PurePosixPath(file).parts):
                self.error(path, 'ruta relativa inválida o fuera del expediente.')

    def index(self, items, target, path):
        for index, item in enumerate(self.array(items, path)):
            if not isinstance(item, dict) or not nonempty(item.get('id')):
                self.error(f'{path}[{index}]', 'falta id textual.'); continue
            if item['id'] in target:
                self.error(path, 'identificador duplicado: ' + item['id'])
            target[item['id']] = item

    def anchor(self, claim, path):
        quote, anchor = claim.get('quote_original'), claim.get('anchor')
        if not self.text(quote, path + '.quote_original'):
            return
        fields = {'start', 'end', 'paragraph', 'time_start_seconds', 'time_end_seconds', 'time_source'}
        if not self.obj(anchor, fields, set(), path + '.anchor'):
            return
        start, end, para = anchor['start'], anchor['end'], anchor['paragraph']
        ranges = paragraph_ranges(self.source)
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(self.source):
            self.error(path, 'offsets inválidos.'); return
        if self.source[start:end] != quote:
            self.error(path, 'la cita no coincide literalmente con los offsets del original.')
        if type(para) is not int or not 1 <= para <= len(ranges):
            self.error(path, 'párrafo inexistente.'); return
        a, b = ranges[para - 1]
        if not a <= start < end <= b:
            self.error(path, 'la cita debe estar en el párrafo anclado, sin unir momentos distintos.')
        t0, t1, origin = anchor['time_start_seconds'], anchor['time_end_seconds'], anchor['time_source']
        if t0 is None:
            if t1 is not None or origin is not None:
                self.error(path, 'tiempo desconocido: ambos tiempos y time_source deben ser null.')
        else:
            if not number(t0) or t0 < 0 or (t1 is not None and (not number(t1) or t1 < t0)):
                self.error(path, 'tiempos inválidos.'); return
            if number(self.duration) and (t0 > self.duration or (t1 is not None and t1 > self.duration)):
                self.error(path, 'el tiempo supera la duración declarada.')
            if not self.obj(origin, {'start_cue', 'end_cue'}, set(), path + '.time_source'):
                return
            cue = origin['start_cue']
            previous_cues = re.findall(r'\[(?:\d{1,3}:)?\d{1,3}:\d{2}(?:\.\d{1,3})?\]', self.source[a:start])
            if cue_seconds(cue) != t0 or not isinstance(cue, str) or not previous_cues or previous_cues[-1] != cue:
                self.error(path, 'inicio temporal sin marca literal concordante anterior a la cita en su párrafo.')
            endcue = origin['end_cue']
            if t1 is None:
                if endcue is not None:
                    self.error(path, 'sin tiempo final, end_cue debe ser null.')
            else:
                following_cues = re.findall(r'\[(?:\d{1,3}:)?\d{1,3}:\d{2}(?:\.\d{1,3})?\]', self.source[end:])
                if cue_seconds(endcue) != t1 or not isinstance(endcue, str) or not following_cues or following_cues[0] != endcue:
                    self.error(path, 'final temporal sin la siguiente marca literal concordante; no inventar precisión de palabra.')
        display, spans = claim.get('display_quote'), self.array(claim.get('display_spans'), path + '.display_spans')
        if display is None:
            if spans or claim.get('display_edit_note') is not None:
                self.error(path, 'sin edición, display_quote/display_edit_note null y display_spans vacío.')
            return
        self.text(display, path + '.display_quote')
        self.text(claim.get('display_edit_note'), path + '.display_edit_note')
        pieces, last = [], 0
        for span in spans:
            if not self.obj(span, {'start', 'end'}, set(), path + '.display_spans[]'):
                continue
            left, right = span['start'], span['end']
            if type(left) is not int or type(right) is not int or not last <= left < right <= len(quote):
                self.error(path, 'recortes inválidos, reordenados o solapados.'); continue
            pieces.append(quote[left:right]); last = right
        if not pieces or display != ' (…) '.join(pieces):
            self.error(path, 'display_quote debe derivarse literalmente de los recortes, separados por (…).')

    def source_record(self, source, path):
        fields = {'id', 'publisher', 'title', 'location', 'published_at', 'consulted_at', 'reference_period',
                  'version', 'valid_as_of', 'supersedes', 'limitations', 'independence_group', 'role', 'excerpt', 'observations'}
        if not self.obj(source, fields, set(), path):
            return
        for key in ('publisher', 'title', 'version', 'limitations', 'independence_group', 'excerpt'):
            self.text(source[key], path + '.' + key)
        self.text(source['reference_period'], path + '.reference_period', nullable=True)
        self.enum(source['role'], {'primary', 'secondary'}, path + '.role')
        self.location(source['location'], path + '.location')
        published = self.date(source['published_at'], path + '.published_at', nullable=True)
        consulted = self.date(source['consulted_at'], path + '.consulted_at')
        valid = self.date(source['valid_as_of'], path + '.valid_as_of')
        if published and consulted and temporal_compare(source['published_at'], source['consulted_at']) == 1:
            self.error(path, 'publicación posterior a consulta.')
        if self.as_of and ((consulted and temporal_compare(source['consulted_at'], self.as_of_raw) == 1) or
                           (valid and temporal_compare(source['valid_as_of'], self.as_of_raw) == 1)):
            self.error(path, 'consulta/vigencia posterior a analysis_as_of.')
        previous = source['supersedes']
        if previous is not None and (not isinstance(previous, str) or previous not in self.sources or previous == source['id']):
            self.error(path, 'supersedes no refiere a otra versión conocida.')
        for observation in self.array(source['observations'], path + '.observations'):
            if self.obj(observation, {'value', 'unit', 'period', 'locator'}, set(), path + '.observations[]'):
                for key, value in observation.items():
                    self.text(value, path + '.observations.' + key)

    def decision(self, decision, path):
        fields = {'id', 'kind', 'actor', 'decided_at', 'record_ref', 'recorded_from', 'claim_ids', 'outcome', 'snapshot_sha256'}
        if not self.obj(decision, fields, set(), path):
            return
        self.enum(decision['kind'], {'selection', 'review'}, path + '.kind')
        self.text(decision['actor'], path + '.actor')
        if isinstance(decision['actor'], str) and decision['actor'].strip().lower() in {'agent', 'assistant', 'agente', 'asistente', 'ia', 'chatgpt', 'codex', 'claude', 'opencode'}:
            self.error(path, 'el agente no puede figurar como decisor humano.')
        date = self.date(decision['decided_at'], path + '.decided_at')
        if date and self.as_of and temporal_compare(decision['decided_at'], self.as_of_raw) == 1:
            self.error(path, 'decisión posterior a analysis_as_of.')
        expected = 'synthetic_fixture' if self.synthetic else 'human_instruction'
        self.enum(decision['recorded_from'], {expected}, path + '.recorded_from')
        self.location(decision['record_ref'], path + '.record_ref')
        self.refs(decision['claim_ids'], self.claims, path + '.claim_ids')
        outcomes = {'selected'} if decision['kind'] == 'selection' else {'approved', 'changes_requested'}
        self.enum(decision['outcome'], outcomes, path + '.outcome')
        snapshot = decision['snapshot_sha256']
        if decision['kind'] == 'selection' and snapshot is not None:
            self.error(path, 'selección no requiere hash de revisión; usar null.')
        if decision['kind'] == 'review' and (not isinstance(snapshot, str) or not re.fullmatch(r'[0-9a-f]{64}', snapshot)):
            self.error(path, 'la revisión debe identificar snapshot_sha256 de la versión examinada.')

    def assessment(self, claim, path):
        assessment, kind = claim.get('assessment'), claim.get('kind')
        selected = claim['id'] in self.selected
        if assessment is None:
            if selected and self.stage != 'inventory':
                self.error(path, 'afirmación elegida sin evaluación o estado pendiente explícito.')
            return
        if not selected or self.stage == 'inventory':
            self.error(path, 'no investigar/evaluar sin selección humana registrada; inventory sólo inventaría.')
        fields = {'status', 'rationale', 'evidence', 'unresolved_reason', 'temporal_basis', 'revision_note',
                  'causal_support', 'causal_limitations', 'calculations'}
        if not self.obj(assessment, fields, set(), path + '.assessment'):
            return
        status = assessment['status']
        self.enum(status, STATUSES.get(kind, set()) if isinstance(kind, str) else set(), path + '.status')
        self.text(assessment['rationale'], path + '.rationale')
        self.enum(assessment['temporal_basis'], {'contemporaneous', 'later_revision', 'mixed', 'not_applicable'}, path + '.temporal_basis')
        if status in ('unresolved', 'awaiting_outcome', 'tracking'):
            self.text(assessment['unresolved_reason'], path + '.unresolved_reason')
        elif assessment['unresolved_reason'] is not None:
            self.text(assessment['unresolved_reason'], path + '.unresolved_reason')
        evidence, relations, used = self.array(assessment['evidence'], path + '.evidence'), [], []
        for ref in evidence:
            if not self.obj(ref, {'source_id', 'relation', 'reason'}, set(), path + '.evidence[]'):
                continue
            ids = self.refs([ref['source_id']], self.sources, path + '.evidence.source_id')
            self.enum(ref['relation'], {'supports', 'contradicts', 'context', 'methodology'}, path + '.evidence.relation')
            self.text(ref['reason'], path + '.evidence.reason')
            relations.append(ref['relation']); used.extend(ids)
        if isinstance(status, str) and status in CONCLUSIONS and not used:
            self.error(path, 'conclusión sin evidencia; ausencia de datos no es falsedad.')
        if status in ('supported', 'fulfilled') and 'supports' not in relations:
            self.error(path, 'falta evidencia de respaldo explícita.')
        if status in ('contradicted', 'not_fulfilled') and 'contradicts' not in relations:
            self.error(path, 'falta evidencia contradictoria; no basta no encontrar fuentes.')
        if claim.get('numeric') is True and isinstance(status, str) and status in CONCLUSIONS:
            if not any(isinstance(self.sources[s].get('observations'), list) and self.sources[s]['observations'] for s in used):
                self.error(path, 'afirmación numérica concluida sin valor/unidad/período/localizador de evidencia.')
        basis = assessment['temporal_basis']
        if isinstance(status, str) and status in CONCLUSIONS and kind != 'opinion':
            if not self.emitted:
                self.error(path, 'sin fecha de emisión no concluir una comparación histórica; mantener pendiente.')
            if basis == 'not_applicable':
                self.error(path, 'la conclusión requiere criterio temporal explícito.')
            for source_id in used:
                published = iso_date(self.sources[source_id].get('published_at'))
                if not published:
                    self.error(path, 'evidencia decisiva sin fecha de publicación conocida.')
                if basis == 'contemporaneous' and published and self.emitted:
                    order = temporal_compare(self.sources[source_id].get('published_at'), self.emitted_raw)
                    if order == 1:
                        self.error(path, 'dato posterior al discurso presentado como disponible entonces.')
                    elif order is None:
                        self.error(path, 'fechas del mismo día sin horas comparables: no asegurar disponibilidad previa intradía; obtener horas o explicar revisión/criterio mixto.')
        if basis in ('later_revision', 'mixed'):
            self.text(assessment['revision_note'], path + '.revision_note')
        elif assessment['revision_note'] is not None:
            self.text(assessment['revision_note'], path + '.revision_note')
        self.enum(assessment['causal_support'], {'not_causal', 'correlation_only', 'causal_evidence', 'not_established'}, path + '.causal_support')
        if claim.get('causal_claim') is True:
            self.text(assessment['causal_limitations'], path + '.causal_limitations')
            if status in ('supported', 'contradicted') and assessment['causal_support'] != 'causal_evidence':
                self.error(path, 'correlación/no evidencia causal no permite confirmar ni refutar causalidad.')
        elif assessment['causal_support'] != 'not_causal':
            self.error(path, 'marcar causal_claim antes de evaluar causalidad.')
        if kind == 'promise' and status in ('not_fulfilled', 'partly_fulfilled'):
            due = iso_date(claim.get('due_at'))
            if not due or not self.as_of or temporal_compare(claim.get('due_at'), self.as_of_raw) not in (-1, 0):
                self.error(path, 'no declarar incumplimiento final de una promesa sin plazo vencido.')
        for calculation in self.array(assessment['calculations'], path + '.calculations'):
            if not self.obj(calculation, {'expression', 'inputs', 'result', 'unit', 'note'}, set(), path + '.calculations[]'):
                continue
            for key in ('expression', 'result', 'unit', 'note'):
                self.text(calculation[key], path + '.calculation.' + key)
            inputs = self.array(calculation['inputs'], path + '.calculation.inputs')
            if not inputs:
                self.error(path, 'cálculo sin insumos trazables.')
            for item in inputs:
                if not self.obj(item, {'source_id', 'observation_index'}, set(), path + '.calculation.input'):
                    continue
                ids = self.refs([item['source_id']], self.sources, path + '.calculation.source_id')
                index = item['observation_index']
                if ids:
                    observations = self.sources[ids[0]].get('observations')
                    if not isinstance(observations, list) or type(index) is not int or not 0 <= index < len(observations):
                        self.error(path, 'índice de observación inexistente.')

    def validate(self, report):
        fields = {'schema_version', 'source_sha256', 'metadata', 'analysis_as_of', 'coverage', 'human_decisions',
                  'selection_decision_id', 'review_decision_id', 'sources', 'claims'}
        if not self.obj(report, fields, set(), 'report'):
            return self.errors
        if type(report['schema_version']) is not int or report['schema_version'] != 1:
            self.error('schema_version', 'esta versión requiere 1.')
        if report['source_sha256'] != hashlib.sha256(self.source.encode('utf-8')).hexdigest():
            self.error('source_sha256', 'el original no corresponde a esta versión del expediente.')
        self.as_of_raw = report['analysis_as_of']
        self.as_of = self.date(self.as_of_raw, 'analysis_as_of')
        metadata = report['metadata']
        mfields = {'title', 'speaker', 'medium', 'program', 'interviewer', 'emitted_at', 'source_url', 'duration_seconds', 'provenance'}
        if self.obj(metadata, mfields, set(), 'metadata'):
            for key in ('title', 'speaker', 'medium', 'program', 'interviewer'):
                self.text(metadata[key], 'metadata.' + key, nullable=key != 'title')
            self.emitted_raw = metadata['emitted_at']
            self.emitted = self.date(self.emitted_raw, 'metadata.emitted_at', nullable=True)
            self.enum(metadata['provenance'], {'user_supplied', 'primary_source_verified', 'synthetic_fixture'}, 'metadata.provenance')
            self.synthetic = metadata['provenance'] == 'synthetic_fixture'
            self.duration = metadata['duration_seconds']
            if self.duration is not None and (not number(self.duration) or self.duration <= 0):
                self.error('metadata.duration_seconds', 'duración positiva conocida o null.')
            if metadata['source_url'] is not None:
                self.location({'url': metadata['source_url'], 'locator': 'pieza original'}, 'metadata.source_url')
            if self.emitted and self.as_of and temporal_compare(self.emitted_raw, self.as_of_raw) == 1:
                self.error('metadata.emitted_at', 'emisión posterior al análisis.')
        coverage = report['coverage']
        if self.obj(coverage, {'scope', 'limitations'}, set(), 'coverage'):
            self.enum(coverage['scope'], {'full_source', 'partial'}, 'coverage.scope')
            for item in self.array(coverage['limitations'], 'coverage.limitations'):
                self.text(item, 'coverage.limitations[]')
            if coverage['scope'] == 'partial' and not coverage['limitations']:
                self.error('coverage', 'una cobertura parcial requiere explicar qué falta.')
        self.index(report['sources'], self.sources, 'sources')
        self.index(report['claims'], self.claims, 'claims')
        self.index(report['human_decisions'], self.decisions, 'human_decisions')
        for sid, source in self.sources.items():
            self.source_record(source, 'sources/' + sid)
        # Detect revision loops; registry reuse is not automatic verdict reuse.
        for sid in self.sources:
            visited, cursor = set(), sid
            while isinstance(cursor, str) and cursor in self.sources:
                if cursor in visited:
                    self.error('sources/' + sid, 'ciclo entre versiones supersedes.'); break
                visited.add(cursor); cursor = self.sources[cursor].get('supersedes')
        for did, decision in self.decisions.items():
            self.decision(decision, 'human_decisions/' + did)
        selection_id = report['selection_decision_id']
        selection = self.decisions.get(selection_id) if isinstance(selection_id, str) else None
        if selection_id is not None:
            if not selection or selection.get('kind') != 'selection' or selection.get('outcome') != 'selected':
                self.error('selection_decision_id', 'decisión humana de selección inexistente.')
            else:
                self.selected = set(self.refs(selection.get('claim_ids'), self.claims, 'selection.claim_ids'))
        if self.stage != 'inventory' and not self.selected:
            self.error('selection', 'investigar requiere selección humana explícita no vacía.')
        cfields = {'id', 'kind', 'quote_original', 'anchor', 'display_quote', 'display_spans', 'display_edit_note',
                   'numeric', 'causal_claim', 'reference_period', 'due_at', 'patterns', 'assessment'}
        for cid, claim in self.claims.items():
            path = 'claims/' + cid
            if not self.obj(claim, cfields, set(), path):
                continue
            self.enum(claim['kind'], STATUSES, path + '.kind')
            for key in ('numeric', 'causal_claim'):
                if type(claim[key]) is not bool:
                    self.error(path + '.' + key, 'requiere booleano.')
            self.text(claim['reference_period'], path + '.reference_period', nullable=True)
            self.date(claim['due_at'], path + '.due_at', nullable=True)
            if claim['kind'] != 'promise' and claim['due_at'] is not None:
                self.error(path, 'due_at se reserva al seguimiento de promesas.')
            self.anchor(claim, path)
            for pattern in self.array(claim['patterns'], path + '.patterns'):
                pfields = {'id', 'hypothesis', 'test', 'alternative', 'status', 'source_ids'}
                if not self.obj(pattern, pfields, set(), path + '.patterns[]'):
                    continue
                self.enum(pattern['id'], PATTERNS, path + '.pattern.id')
                self.enum(pattern['status'], {'untested', 'supported', 'not_supported', 'inconclusive'}, path + '.pattern.status')
                for key in ('hypothesis', 'test', 'alternative'):
                    self.text(pattern[key], path + '.pattern.' + key)
                refs = self.refs(pattern['source_ids'], self.sources, path + '.pattern.source_ids')
                if pattern['status'] != 'untested' and (cid not in self.selected or self.stage == 'inventory'):
                    self.error(path, 'no probar patrón sin selección humana registrada.')
                if pattern['status'] in ('supported', 'not_supported') and not refs:
                    self.error(path, 'un patrón no se da por probado/descartado sin evidencia.')
            self.assessment(claim, path)
        review_id = report['review_decision_id']
        review = self.decisions.get(review_id) if isinstance(review_id, str) else None
        if review_id is not None and (not review or review.get('kind') != 'review'):
            self.error('review_decision_id', 'registro de revisión inexistente.')
        if self.stage == 'reviewed':
            if not review or review.get('outcome') != 'approved':
                self.error('review', 'falta decisión humana explícita aprobatoria registrada.')
            elif set(self.refs(review.get('claim_ids'), self.claims, 'review.claim_ids')) != self.selected:
                self.error('review', 'la revisión no cubre exactamente la selección del informe.')
            if review and selection and temporal_compare(review.get('decided_at'), selection.get('decided_at')) == -1:
                self.error('review', 'la revisión antecede a la selección.')
            if review and review.get('snapshot_sha256') != review_snapshot_sha256(report):
                self.error('review', 'contenido o selección cambió después de la revisión registrada; requiere nueva revisión humana.')
            review_records = [item for item in self.decisions.values() if item.get('kind') == 'review']
            if review and review_records and review is not review_records[-1]:
                self.error('review', 'hay una revisión posterior en el registro; no reutilizar una aprobación anterior.')
        return self.errors


def validate(source, report, stage='inventory'):
    if stage not in ('inventory', 'research', 'reviewed'):
        return ['Etapa desconocida.']
    if not isinstance(source, str):
        return ['El original debe ser texto UTF-8.']
    return Validator(source, stage).validate(report)


def read_limited(path):
    with Path(path).open('rb') as file:
        data = file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError(f'{Path(path).name}: supera el límite de {MAX_BYTES} bytes.')
    return data.decode('utf-8')  # preserve CRLF and every Unicode character


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Clave JSON duplicada: ' + key)
        result[key] = value
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--report', required=True)
    parser.add_argument('--stage', choices=('inventory', 'research', 'reviewed'), default='inventory')
    parser.add_argument('--print-review-hash', action='store_true', help='Imprimir hash de versión para una revisión humana; no aprueba nada')
    args = parser.parse_args(argv)
    try:
        report = json.loads(read_limited(args.report), object_pairs_hook=unique_object)
        errors = validate(read_limited(args.source), report, args.stage)
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        errors = [str(exc)]
        print(json.dumps({'ok': False, 'errors': errors}, ensure_ascii=False)); return 2
    result = {'ok': not errors, 'stage': args.stage, 'errors': errors,
                      'scope': 'estructura/anclajes/consistencia declarada; no verdad, cobertura exhaustiva, autenticidad de fuentes o identidad humana',
                      'synthetic_fixture': isinstance(report, dict) and isinstance(report.get('metadata'), dict) and report['metadata'].get('provenance') == 'synthetic_fixture',
                      'human_review_authenticated': False, 'publication_authorized': False,
                      'network_used': False, 'files_written': False}
    if args.print_review_hash and isinstance(report, dict):
        result['review_snapshot_sha256'] = review_snapshot_sha256(report)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
