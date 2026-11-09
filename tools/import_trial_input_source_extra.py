"""Narrow additional choice/evidence UI carriers for the latest whole-UI correction."""
from pathlib import Path
import import_v3_trial_inputs_ui as importer
import build_v3_armament_layout as resolver
for n in ['t_choice','t_choice_time','t_ktdm_scroll','t_ktdm_detail','t_ktdm_detail_scroll']:
 path='flash/trial/'+n+'.spc'
 if path not in importer.SELECT['partition_data_win.cpk']:importer.SELECT['partition_data_win.cpk'].append(path)
path='flash/trial/t_ktdm_detail_img_US.spc'
if path not in importer.SELECT['partition_data_win_us.cpk']:importer.SELECT['partition_data_win_us.cpk'].append(path)
importer.run()
import json
manifest=importer.OUT/'manifest.json';data=json.loads(manifest.read_text(encoding='utf-8'));data['authorization']='Latest user20261107 requests all UI match V3; selected25 trial-input UI carriers only, no original execution/install/save change or general extraction permission.';manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
resolver.BANK=importer.OUT;resolver.ANIMATED_NAMES={'t_choice','t_choice_frame_US','t_tohyo_cursor','t_tohyo_frame','t_tohyo_time','t_tohyo_bt_US','t_tohyo_name_US','t_tohyo_title_US','t_sub_jinbutu_arrow','t_sub_jinbutu_focus','t_sub_jinbutu_pl','t_sub_jinbutu_zaseki_US','t_sub_title_US','t_sub_spot_bg','t_sub_spot_cursor','t_ktdm_scroll','t_ktdm_detail','t_ktdm_detail_scroll','t_ktdm_detail_img_US'}
(importer.OUT/'runtime-layout.json').write_text('{}',encoding='utf-8');resolver.build()
