"""Explicit manuscript scene entries using this project's existing 3D geometry.

Only reviewed sections are bound. A room mesh does not assign a fictional room
number, reveal an unobserved scene, or turn a production note into dialogue.
"""
from pathlib import Path
import hashlib
import json
import re
from v4_scene_bindings_more import build_more
from v4_public_records import build_records
from v4_dedicated_spaces import apply_scene_bindings
from v4_prop_states import apply_scene_bindings as apply_props

ROOT = Path(__file__).resolve().parents[1]
MAIN = {
    '10': {'P-01':'plaza','P-02':'plaza','P-03':'plaza','P-04':'management_office',
           'P-05':'plaza','P-06':'plaza','P-06a':'plaza','P-07':'plaza','P-08':'hotel_corridor'},
    '11a': {'1-01':'hotel_corridor','1-02':'plaza','1-02b':'hotel_lobby','1-03':'plaza',
            '1-04':'hotel_lobby','1-04L1':'plaza','1-05':'plaza','1-05G':'park_main_gate',
            '1-06':'supply_store','1-07':'supply_store','1-07k':'clinic','1-08':'guest_room'},
    '11a2': {'1-09':'guest_room','1-10':'hotel_lobby','1-11':'hotel_corridor','1-12':'clinic',
             '1-13':'dining_room','1-14':'service_lounge','1-15':'service_lounge','1-16':'management_office',
             '1-17':'service_lounge','1-17g':'dining_room','1-17-F-SA02':'hotel_corridor','1-18':'clinic'},
    '11a3': {'1-19':'hotel_lobby','1-20':'hotel_lobby','1-21':'hotel_lobby','1-21a':'hotel_lobby',
             '1-22':'service_lounge','1-23':'service_lounge','1-24':'management_office','1-25':'service_lounge',
             '1-26':'dining_room','1-26a':'dining_room','1-27':'hotel_corridor','1-28':'service_lounge',
             '1-29':'hotel_corridor','1-30':'hotel_lobby','1-31':'clinic','1-32':'hotel_lobby','1-33':'service_lounge'},
    '65': {'1-07a':'dining_room'},
    '154': {'1-09a-01':'hotel_lobby'},
}


def build():
    world = json.loads((ROOT/'art/space_v4/runtime_v1/world.json').read_text(encoding='utf8'))
    sections = {}
    for prefix, bindings in MAIN.items():
        files = list((ROOT/'docs/design/rewrite_v4').glob(prefix+'_*.md'))
        if prefix == '10':
            files = [f for f in files if '프롤로그' in f.name]
        assert len(files) == 1, (prefix, files)
        path = files[0];raw = path.read_bytes();lines = raw.decode('utf8').splitlines()
        headings = {}
        for index, line in enumerate(lines):
            match = re.match(r'^#{2,3}\s+([A-Z0-9]+-[A-Za-z0-9-]+)\s+', line)
            if match:
                headings.setdefault(match[1], (index+1,line))
        for location, space in bindings.items():
            assert location in headings, (prefix, location)
            assert space in world['spaces'], space
            line, heading = headings[location]
            sections[path.name+':'+location] = {
                'space':space,'entry':'section-entry-only','source':{'file':path.name,'location':location,'line':line,
                'fileSha256':hashlib.sha256(raw).hexdigest(),'heading':heading},
                'geometryPolicy':'Reuse the authored room geometry; do not infer a room number, eyewitness or exact actor position.',
            }
    more=build_more(ROOT)
    for key,value in more['sections'].items():
        if key in sections and sections[key]['space']!=value['space']:raise ValueError('Conflicting reviewed scene '+key)
        sections[key]=value
    time_ranges=[]
    overrides={'10':{'P-01':'day','P-07':'evening','P-08':'night'},'11a':{'1-01':'day','1-08':'night'},'11a2':{'1-09':'night','1-09a':'day','1-09b':'day'},'11a3':{'1-19':'day'},'12a4':{'2-31':'day'},'12a6':{'2-51':'day'},'13a4':{'3-43':'night'},'14a10':{'4-134':'day'},'14a11':{'4-164':'night'},'15a4':{'5-64':'night'}}
    # Reviewed first-chapter inserts carry a real change of day part. They
    # cannot inherit the parent morning through an evening meal or next dawn.
    overrides['11a']['1-07k']='night'
    overrides['11a2'].update({'1-17g':'evening','1-18':'night'})
    overrides['11a3'].update({'1-26':'evening','1-28':'night'})
    overrides.update({'65':{'1-07a':'evening'},'120':{'1-07g':'night'},'154':{'1-09a-01':'day'}})
    for path in sorted((ROOT/'docs/design/rewrite_v4').glob('*.md')):
        prefix=path.name.split('_')[0]
        if not re.fullmatch(r'1[1-6][abd]\d*|10',prefix) and prefix not in ('65','120','154'):continue
        lines=path.read_text(encoding='utf8').splitlines();anchors={}
        match=re.search(r'\d+\s*일차\s*(새벽|아침|오전|정오|낮|오후|저녁|밤|야간|\d{1,2}(?:시|:\d\d))',' '.join(lines[:5]))
        if match:
            token=match[1];hour=re.match(r'\d+',token)
            anchors[1]='night' if token in ('밤','야간','새벽') or hour and (int(hour[0])<6 or int(hour[0])>=20) else 'evening' if token=='저녁' or hour and int(hour[0])>=18 else 'day'
        for index,line in enumerate(lines,1):
            heading=re.match(r'^#{2,3}\s+(\S+)\s',line)
            if heading and heading[1] in overrides.get(prefix,{}):anchors[index]=overrides[prefix][heading[1]]
        starts=sorted(anchors)
        for i,start in enumerate(starts):time_ranges.append({'source':{'file':path.name,'fileSha256':hashlib.sha256(path.read_bytes()).hexdigest()},'startLine':start,'endLineExclusive':starts[i+1] if i+1<len(starts) else len(lines)+1,'timeOfDay':anchors[start],'policy':'Own visual timeline from explicit current-day production metadata and reviewed section transitions; dialogue keywords do not set weather.'})
    result = {'version':1,'sections':sections,'sceneRanges':more['sceneRanges'],'timeRanges':time_ranges,'cgRanges':more['cgRanges'],'cgAudit':more.get('cgAudit',[]),'unbound':more.get('unbound',[]),'publicRecords':build_records(ROOT),'scope':'Reviewed source-addressed scene/CG ranges; geometry reuse does not grant character knowledge.'}
    apply_scene_bindings(result, ROOT)
    apply_props(result, ROOT)
    return result


if __name__ == '__main__':
    output=ROOT/'data/presentation/v4_scenes.json'
    data=build();output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'boundSections':len(data['sections']),'file':str(output)},ensure_ascii=False))
