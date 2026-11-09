"""Resolve the authorized ending SFL bank with the shared source transform reader."""
import json
from pathlib import Path
import build_v3_armament_layout as source

if __name__ == '__main__':
    source.BANK = Path(__file__).resolve().parents[1] / 'ui/v3_authorized/endings'
    manifest = json.loads((source.BANK / 'manifest.json').read_text(encoding='utf-8'))
    source.ANIMATED_NAMES = set(manifest['timelines'])
    source.build()
