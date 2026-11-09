"""Use supplied Korean phase-start UI only; no original runtime, story or character access."""
from pathlib import Path
import json
import import_v3_trial_inputs_ui as importer
import build_v3_armament_layout as resolver
importer.CACHE=Path('C:/Users/kirby/Downloads/v3_re/ui_phase_start_source_20261107')
importer.OUT=importer.ROOT/'ui/v3_authorized/phase_start_source'
importer.SELECT={'partition_data_win_us.cpk':['flash/event/t_panic_start_US.spc']}
importer.run()
p=importer.OUT/'manifest.json';m=json.loads(p.read_text(encoding='utf-8'));assert all(c['providedKoreanCarrier']for c in m['containers'])
m['authorization']='User all-UI source correction, focused live Panic StartBand. Supplied Korean carrier only; no original-installation reads, game execution, character/story assets.';p.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
resolver.BANK=importer.OUT;resolver.ANIMATED_NAMES={'t_panic_start_US'};resolver.SOLID_NAMES={'t_panic_start_US'}
(importer.OUT/'runtime-layout.json').write_text('{}',encoding='utf-8');resolver.build()
