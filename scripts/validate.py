"""Offline validation; duplicate candidates always require human review."""
import argparse
from collections import defaultdict
from datetime import datetime, date
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

ROOT = Path(__file__).resolve().parents[1]


def canonical_url(value):
    parts = urlsplit(value)
    if parts.scheme not in ('http', 'https') or not parts.hostname or parts.username:
        raise ValueError('evidence URL must be public HTTP(S) without credentials')
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith('utm_') and k.lower() not in ('gclid', 'fbclid')]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path,
                      urlencode(query), ''))


def check_schema(value, schema, label='event'):
    types = schema.get('type')
    if types:
        types = [types] if isinstance(types, str) else types
        mapping = {'object': dict, 'array': list, 'string': str,
                   'number': (int, float), 'null': type(None), 'boolean': bool}
        if not any(isinstance(value, mapping[t]) and
                   not (t == 'number' and isinstance(value, bool)) for t in types):
            raise ValueError(f'{label}: invalid type')
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError(f'{label}: invalid enum')
    if isinstance(value, dict):
        for key in schema.get('required', []):
            if key not in value:
                raise ValueError(f'{label}: missing {key}')
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False and value.keys() - props.keys():
            raise ValueError(f'{label}: unknown fields')
        for key, item in value.items():
            if key in props:
                check_schema(item, props[key], f'{label}.{key}')
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0):
            raise ValueError(f'{label}: too few items')
        for item in value:
            check_schema(item, schema.get('items', {}), label)
    if isinstance(value, str) and len(value) < schema.get('minLength', 0):
        raise ValueError(f'{label}: empty string')
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        if value < schema.get('minimum', float('-inf')):
            raise ValueError(f'{label}: negative amount')


def valid_date(value):
    if re.fullmatch(r'\d{4}', value):
        return 1 <= int(value) <= 9999
    if re.fullmatch(r'\d{4}-\d{2}', value):
        date.fromisoformat(value + '-01')
        return True
    date.fromisoformat(value)
    return True


def validate_event(event):
    schema = json.loads((ROOT / 'config/event.schema.json').read_text())
    check_schema(event, schema)
    if (event['amount_status'] == 'undisclosed') != (event['amount'] is None):
        raise ValueError('undisclosed amount must be null; disclosed amount must be numeric')
    if not re.fullmatch(r'[A-Z]{3}', event['currency']):
        raise ValueError('currency must be three uppercase letters (UNK if unknown)')
    for key in ('financing_date', 'disclosed_date'):
        if event[key] is not None:
            valid_date(event[key])
    stamp = datetime.fromisoformat(event['collected_at'].replace('Z', '+00:00'))
    if stamp.tzinfo is None:
        raise ValueError('collected_at requires timezone')
    for url in event['evidence_urls']:
        canonical_url(url)


def validate_events(events):
    seen = set()
    groups = defaultdict(list)
    for event in events:
        validate_event(event)
        if event['event_id'] in seen:
            raise ValueError('duplicate event_id: ' + event['event_id'])
        seen.add(event['event_id'])
        key = (event['company_id'], event['round_normalized'], event['event_type'])
        groups[key].append(event['event_id'])
    return [ids for ids in groups.values() if len(ids) > 1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--events', type=Path, default=ROOT / 'data/events.jsonl')
    args = parser.parse_args()
    sources = json.loads((ROOT / 'config/sources.json').read_text())['sources']
    ids = [s['id'] for s in sources]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate source id')
    for source in sources:
        if source['url'] is not None:
            canonical_url(source['url'])
        if source['enabled'] and ('pending' in source['access_status'] or
                                  source['priority'] != 'P0'):
            raise ValueError('source enabled before approved access: ' + source['id'])
    project = json.loads((ROOT / 'config/project.json').read_text())
    if project['schedule_enabled'] or project['mode'] != 'manual':
        raise ValueError('bootstrap must remain manual')
    for name in ('daily-runs', 'processed-urls', 'source-health'):
        json.loads((ROOT / f'state/{name}.json').read_text())
    events = [json.loads(line) for line in args.events.read_text().splitlines() if line.strip()]
    candidates = validate_events(events)
    print(json.dumps({'valid': True, 'sources': len(sources), 'events': len(events),
                      'duplicate_candidates': candidates}, ensure_ascii=False))
    if candidates:
        raise SystemExit('Review duplicate candidates before report delivery')


if __name__ == '__main__':
    main()
