"""Keep save addresses stable across the documented V5 dialogue-only revisions."""

from functools import lru_cache
import hashlib
import json
from pathlib import Path


REVISIONS = Path(__file__).resolve().parents[1] / 'data/revised_voice_polish.json'


@lru_cache(maxsize=1)
def address_overrides():
    overrides = {}
    if REVISIONS.exists():
        for row in json.loads(REVISIONS.read_text(encoding='utf-8'))['revisions']:
            before = row['before'].strip()
            after = row['after'].strip()
            key = (row['scene'], after)
            digest = hashlib.sha256(before.encode()).hexdigest()[:14]
            if key in overrides and overrides[key] != digest:
                raise ValueError(f'Conflicting V5 dialogue address: {row["scene"]}')
            overrides[key] = digest
    return overrides


def speech_address(scene_id, raw):
    raw = raw.strip()
    return address_overrides().get((scene_id, raw)) or hashlib.sha256(raw.encode()).hexdigest()[:14]
