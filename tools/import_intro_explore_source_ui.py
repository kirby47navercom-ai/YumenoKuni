"""Narrow UI-only continuation of the user's all-V3-UI correction."""
import json
from pathlib import Path
import import_v3_trial_inputs_ui as importer
import build_v3_armament_layout as resolver
importer.CACHE=Path('C:/Users/kirby/Downloads/v3_re/ui_intro_explore_source_20261107')
importer.OUT=importer.ROOT/'ui/v3_authorized/intro_explore_source'
importer.SELECT={'partition_data_win.cpk':['flash/adv/adv_search_target.spc','flash/adv/adv_search_3d.spc','flash/adv/adv_map_base.spc','flash/adv/adv_search_name.spc','flash/techou/techou_top.spc'],'partition_data_win_us.cpk':['flash/adv/adv_map_north_US.spc','flash/event/t_nonstop_start_US.spc']}
importer.run()
p=importer.OUT/'manifest.json';m=json.loads(p.read_text(encoding='utf-8'));m['authorization']='User20261107 allUI source-equivalent request, focused Intro/Explore/PadHome followup: exact7 UI carriers only, provided Korean t_nonstop_start_JP preferred; no original execution, installation/save change, story/character extraction.';p.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
resolver.BANK=importer.OUT;resolver.ANIMATED_NAMES={'adv_search_target','adv_search_3d','adv_map_north_US','t_nonstop_start_US','techou_top','adv_map_base','adv_search_name'}
(importer.OUT/'runtime-layout.json').write_text('{}',encoding='utf-8');resolver.build()
