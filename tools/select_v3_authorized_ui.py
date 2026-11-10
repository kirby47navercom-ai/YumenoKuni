"""Copy visually reviewed components from the user's supplied UI cache into source UI.

The supplied files are preserved byte-for-byte. Character names, original story
documents, publisher logos and bonus-mode buttons are not runtime UI selections.
"""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path('C:/Users/kirby/Downloads/v3_re/ui_authorized_20261029')
SELECT = {
    'pad_floor': ('techou_type_000_JP.spc', 'bg_000_DXT1.png'),
    'pad_circle': ('techou_type_000_JP.spc', 'circle_000.png'),
    'pad_bubble': ('techou_type_000_JP.spc', 'setumei_base_000.png'),
    'pad_map': ('techou_type_027_JP.spc', 'icon_map_DXT1.png'),
    'pad_bullet': ('techou_type_027_JP.spc', 'icon_kotodama_DXT1.png'),
    'pad_gift': ('techou_type_027_JP.spc', 'icon_present_DXT1.png'),
    'pad_card': ('techou_type_027_JP.spc', 'icon_tsusinbo_DXT1.png'),
    'pad_rules': ('techou_type_027_JP.spc', 'icon_rule_DXT1.png'),
    'pad_option': ('techou_type_027_JP.spc', 'icon_system_DXT1.png'),
    'title_new': ('titile_mainmenu_JP.spc', 'kanban_new_JP.png'),
    'title_load': ('titile_mainmenu_JP.spc', 'kanban_load_JP.png'),
    'title_option': ('titile_mainmenu_JP.spc', 'kanban_system_JP.png'),
    'title_new_focus': ('titile_mainmenu_JP.spc', 'kanban_new_ef_DXT1.png'),
    'title_load_focus': ('titile_mainmenu_JP.spc', 'kanban_load_ef_DXT1.png'),
    'title_option_focus': ('titile_mainmenu_JP.spc', 'kanban_system_ef_DXT1.png'),
    'option_slow': ('techou_system_option_tab_JP.spc', 's_slow_JP.png'),
    'option_fast': ('techou_system_option_tab_JP.spc', 's_fast_JP.png'),
    'option_on': ('techou_system_option_tab_JP.spc', 'm_on_JP.png'),
    'option_off': ('techou_system_option_tab_JP.spc', 'm_off_JP.png'),
    'option_arrow': ('techou_system_option_tab_JP.spc', 'yazirusi_000.png'),
}


def main():
    inventory = json.loads((CACHE / 'manifest.json').read_text(encoding='utf-8'))
    output = ROOT / 'ui/v3_authorized'
    output.mkdir(exist_ok=True)
    rows = {}
    for key, (container, resource) in SELECT.items():
        matches = [r for r in inventory['textures']
                   if r['container'].endswith('/' + container) and r['resource'] == resource]
        if len(matches) != 1:
            raise ValueError((key, len(matches)))
        row = matches[0]
        source = Path(row['path'])
        target = output / (key + '.png')
        shutil.copyfile(source, target)
        rows[key] = {**row, 'source_file': str(source),
                     'file': target.relative_to(ROOT).as_posix(),
                     'runtime': 'Assets/Art/ui/v3/' + target.name,
                     'file_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                     'reviewed': True, 'review_method': 'review-2/3/4.jpg contact sheets; native runtime pending',
                     'runtime_selected': True, 'adaptation': 'unchanged pixels; layout and text are owned by YumenoKuni'}
    manifest = {'authorization': inventory['authorization'], 'source_installation_read': False,
                'reviewed_sheets': ['review-2.jpg', 'review-3.jpg', 'review-4.jpg'],
                'visual_runtime_status': 'Not run', 'components': rows}
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'selected': len(rows), 'manifest': 'ui/v3_authorized/manifest.json'}))


if __name__ == '__main__':
    main()
