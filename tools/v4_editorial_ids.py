"""Keep published dialogue IDs when reviewed manuscript wording changes."""
import hashlib
import json
from pathlib import Path

_REVISIONS = None
_VOICE_REVISIONS = None
_VOICE_ROWS = None


def original_voice_line(source_file, source_line, current):
    """Resolve only a recorded, exact-current-line editorial replacement."""
    global _VOICE_ROWS
    if _VOICE_ROWS is None:
        path = Path(__file__).with_name('v4_voice_revisions_20261107.json')
        rows = json.loads(path.read_text(encoding='utf-8'))['revisions'] if path.exists() else []
        _VOICE_ROWS = {(r['file'],r['line'],r['after']):r['before'] for r in rows}
    return _VOICE_ROWS.get((source_file,source_line,current),current)
DELIVERY_POSES = {'크게웃음':'C03', '작게웃음':'C02', '분노':'C05',
                  '식은땀':'C09', '울먹임':'C06', '통곡':'C07'}


def validate_delivery(row):
    """An authored delivery may append a tag, never replace the speaker/body."""
    if row['before'].startswith(('(', '（')):
        assert row['after'].startswith(('(', '（')) and row['after'].endswith((')', '）')), row
        assert row.get('authoredDelivery') is None, row
        return
    before = row['before'].split(']', 1)[0]
    after = row['after'].split(']', 1)[0]
    marker = row.get('authoredDelivery')
    if marker is None:
        assert before == after, row
    else:
        assert marker in DELIVERY_POSES and '속말' not in before and '독백' not in before, row
        assert after == before + '·' + marker, row


def fingerprint(prefix, location, line, *, source_file=None, source_line=None):
    global _VOICE_REVISIONS
    if source_file is not None and source_line is not None:
        if _VOICE_REVISIONS is None:
            path = Path(__file__).with_name('v4_voice_revisions_20261107.json')
            rows = json.loads(path.read_text(encoding='utf-8'))['revisions'] if path.exists() else []
            _VOICE_REVISIONS = {(r['file'], r['line'], r['after']): r['fingerprint'] for r in rows}
            assert len(_VOICE_REVISIONS) == len(rows), 'Duplicate voice revision identity'
        saved = _VOICE_REVISIONS.get((source_file, source_line, line))
        if saved is not None:
            return saved
    global _REVISIONS
    if _REVISIONS is None:
        path = Path(__file__).with_name('v4_editorial_revisions.json')
        rows = json.loads(path.read_text(encoding='utf-8'))['revisions']
        _REVISIONS = {}
        for row in rows:
            key = (row['prefix'], row['location'], row['after'])
            assert key not in _REVISIONS, key
            assert row['before'] != row['after']
            validate_delivery(row)
            _REVISIONS[key] = hashlib.sha256(row['before'].encode()).hexdigest()[:12]
    return _REVISIONS.get((prefix, location, line), hashlib.sha256(line.encode()).hexdigest()[:12])
