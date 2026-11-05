#!/usr/bin/env python3
"""Valida estructura y trazabilidad, nunca la verdad de las afirmaciones."""
import argparse
import json
from pathlib import Path, PurePosixPath
import sys
from urllib.parse import urlsplit, parse_qsl

MAX_BYTES = 5_000_000
STATUSES = {'supported', 'needs_review', 'could_not_verify'}
REASONS = {'not_researched', 'inaccessible', 'reporter_material', 'inconclusive'}


def nonempty(x):
    return isinstance(x, str) and bool(x.strip())


def validate(source, report):
    errors = []
    if not isinstance(report, dict):
        return ['El informe debe ser un objeto JSON.']
    ids = report.get('extracted_claim_ids')
    claims = report.get('claims')
    if not isinstance(ids, list) or any(not nonempty(x) for x in ids):
        return ['extracted_claim_ids debe ser una lista de identificadores.']
    if len(ids) != len(set(ids)):
        errors.append('Hay identificadores de extracción duplicados.')
    if not isinstance(claims, list):
        return errors + ['claims debe ser una lista.']
    seen = []
    for i, claim in enumerate(claims):
        prefix = f'claims[{i}]'
        if not isinstance(claim, dict):
            errors.append(f'{prefix}: debe ser un objeto.'); continue
        cid = claim.get('id')
        if not nonempty(cid):
            errors.append(f'{prefix}: falta id.'); cid = f'INVALID-{i}'
        seen.append(cid)
        quote = claim.get('quote')
        if not nonempty(quote) or quote not in source:
            errors.append(f'{cid}: quote no coincide literalmente con el original.')
        status = claim.get('status')
        if not isinstance(status, str) or status not in STATUSES:
            errors.append(f'{cid}: status desconocido.')
        if not nonempty(claim.get('rationale')):
            errors.append(f'{cid}: falta explicación.')
        refs = claim.get('sources', [])
        if not isinstance(refs, list):
            errors.append(f'{cid}: sources debe ser una lista.'); refs = []
        if isinstance(status, str) and status in {'supported', 'needs_review'} and not refs:
            errors.append(f'{cid}: el estado requiere evidencia consultable.')
        if status == 'could_not_verify' and (not isinstance(claim.get('unresolved_reason'), str) or claim.get('unresolved_reason') not in REASONS):
            errors.append(f'{cid}: falta motivo válido de incertidumbre.')
        for j, ref in enumerate(refs):
            label = f'{cid}/sources[{j}]'
            if not isinstance(ref, dict):
                errors.append(f'{label}: debe ser un objeto.'); continue
            if not nonempty(ref.get('evidence')):
                errors.append(f'{label}: falta evidencia concreta.')
            url, file = ref.get('url'), ref.get('file')
            if bool(url) == bool(file):
                errors.append(f'{label}: usar url o file, no ambos ni ninguno.'); continue
            if url:
                if not isinstance(url, str):
                    errors.append(f'{label}: URL inválida.'); continue
                try:
                    u = urlsplit(url)
                    if u.scheme not in {'https', 'http'} or not u.hostname or u.username or u.password:
                        errors.append(f'{label}: URL no admitida o con credenciales.')
                    keys = {k.lower() for k, _ in parse_qsl(u.query)}
                    if keys & {'token', 'access_token', 'api_key', 'apikey', 'secret', 'password'}:
                        errors.append(f'{label}: la URL puede contener un secreto.')
                except ValueError:
                    errors.append(f'{label}: URL inválida.')
            else:
                if not isinstance(file, str) or '\\' in file:
                    errors.append(f'{label}: usar ruta relativa con separadores /.'); continue
                p = PurePosixPath(file)
                if p.is_absolute() or '..' in p.parts or ':' in file or not p.parts:
                    errors.append(f'{label}: ruta local fuera del proyecto o inválida.')
                if not nonempty(ref.get('locator')):
                    errors.append(f'{label}: falta página, fila o marca de tiempo.')
    if len(seen) != len(set(seen)):
        errors.append('Una afirmación aparece más de una vez en el informe.')
    if set(seen) != set(ids):
        errors.append('Los identificadores del informe no coinciden con la extracción.')
    return errors


def read_limited(path):
    p = Path(path)
    if p.stat().st_size > MAX_BYTES:
        raise ValueError(f'{p.name}: supera el límite de {MAX_BYTES} bytes.')
    return p.read_text(encoding='utf-8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', required=True)
    p.add_argument('--report', required=True)
    args = p.parse_args()
    try:
        errors = validate(read_limited(args.source), json.loads(read_limited(args.report)))
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'ok': False, 'errors': [str(exc)]}, ensure_ascii=False))
        return 2
    print(json.dumps({'ok': not errors, 'errors': errors,
                     'scope': 'estructura y anclajes; no valida verdad, independencia ni integridad de extracción'},
                    ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
