"""Source-reviewed investigation affordances, independent of renderer/data cook.

Authored marker transforms are production staging in our existing meshes, not
measurements of V3 or new eyewitness/plot facts. The native cook must create the
visible marker/NPC before these geometryReady entries can be runtime-tested.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[1]

# Explicit collision-free production anchors, in the world.json coordinate
# system. Each investigate scope currently activates one spot; no arbitrary UI
# x/y or invisible click area substitutes for a world-space affordance.
AUTHORED_ANCHORS={
 'hotel_lobby':[0,1.25,3], 'hotel_corridor':[0,1.25,25],
 'service_lounge':[0,1.25,.72], 'management_office':[-1.65,1.25,1.9],
 'clinic':[0,1.25,1.06], 'hotel_multiuse':[0,1.25,1.4],
 'performance_stage':[0,1.25,5.2], 'theatre_preparation':[0,1.25,.72],
 'staff_passage':[0,1.25,6], 'cold_store':[0,1.25,.72],
 'mirror_workbay':[0,1.25,1.06], 'mirror_waiting':[0,1.25,1.06],
 'mirror_maze':[5,1.25,6], 'record_room':[0,1.25,3.2],
 'inspection_hall_normal':[0,1.25,2.08],
 'inspection_hall_changed':[0,1.25,2.08],
 'supply_store':[0,1.25,.72], 'central_control':[0,1.25,2.1],
 'operating_archive':[.283,1.25,1.683], 'lower_corridor':[0,1.25,8],
}

# Original broad placeholders are corrected only where current manuscript
# actually locates the entry. A multi-section scope may travel later; entry
# placement never asserts that the whole dialogue occurred at this marker.
SPACE_CORRECTIONS={
 'v4:11b:I-06':'staff_passage', 'v4:11b:I-11':'staff_passage',
 'v4:11b:I-12c':'staff_passage',
 'v4:2:investigate:I2-13:spot':'theatre_preparation',
 'v4:2:investigate:I2-18:spot':'staff_passage',
 'v4:2:investigate:I2-23:spot':'performance_stage',
 'v4:2:investigate:I2-25-26:spot':'performance_stage',
 'v4:2:investigate:I2-27-29:spot':'hotel_corridor',
 'v4:2:investigate:I2-32b-33:spot':'hotel_corridor',
 'v4:2:investigate:I2-34:spot':'hotel_corridor',
 'v4:2:investigate:I2-37:spot':'performance_stage',
 'v4:2:investigate:I2-38:spot':'performance_stage',
 'v4:2:investigate:I2-39:spot':'performance_stage',
 'v4:2:investigate:I2-40:spot':'performance_stage',
 'v4:2:investigate:I2-41:spot':'theatre_preparation',
 'v4:2:investigate:I2-42:spot':'theatre_preparation',
 'I3-05-rule':'mirror_maze', 'I3-40-record':'mirror_waiting',
 'v4:5:investigate:I19-20:spot':'supply_store',
 'v4:5:investigate:I21:spot':'supply_store',
 'v4:5:investigate:I22-23:spot':'supply_store',
 'v4:5:investigate:I24-25:spot':'supply_store',
 'v4:6:investigate:I6-03-04:spot':'lower_corridor',
 'v4:6:investigate:I6-05-08:spot':'lower_corridor',
}

# Only exact pre-existing targets that match the *entry* object are reused.
# A later question elsewhere in the source scope cannot relabel its entry.
EXISTING_TARGETS={
 'v4:11b:I-03':'printer', 'v4:11b:I-04':'door_A',
 'v4:11b:I-05':'door_B', 'v4:11b:I-12b':'printer',
 'I3-12-reflection':'mirror_surface',
 'I4-04-fastening':'external_fixing',
 'I4-09-rear':'inner_storage_door',
}

# These are actual currently present interviewees, not culprit hints. Lists
# describe the source's current participants; the neutral marker is not labelled
# with the as-yet-unacquired conclusion or answer to a trial question.
INTERVIEWEES={
 'v4:11b:I-06':['nana'], 'v4:11b:I-07':['koto','sora','taiga'],
 'v4:11b:I-08':['nana'], 'v4:11b:I-09':['sora'],
 'v4:11b:I-11':['sho'], 'v4:11b:I-12':['haruka','akari'],
 'v4:11b:I-12c':['akari','satsuki'], 'v4:11b:I-12d':['rei'],
 'v4:2:investigate:I2-05:spot':['sora','nana'],
 'v4:2:investigate:I2-06:spot':['yuu'],
 'v4:2:investigate:I2-07:spot':['yuu'],
 'v4:2:investigate:I2-08:spot':['haruka'],
 'v4:2:investigate:I2-10:spot':['yuu'],
 'v4:2:investigate:I2-16-17:spot':['rei','akari','satsuki'],
 'v4:2:investigate:I2-18:spot':['sora','nana'],
 'v4:2:investigate:I2-23:spot':['riku'],
 'v4:2:investigate:I2-25-26:spot':['rei','akari','satsuki'],
 'v4:2:investigate:I2-27-29:spot':['sho'],
 'v4:2:investigate:I2-31-32:spot':['yuu','haruka'],
 'v4:2:investigate:I2-32b-33:spot':['nana','sora'],
 'v4:2:investigate:I2-34:spot':['nana'],
 'v4:2:investigate:I2-35:spot':['yuu'],
 'v4:2:investigate:I2-36:spot':['yuu'],
 'v4:2:investigate:I2-37:spot':['satsuki'],
 'v4:2:investigate:I2-38:spot':['akari','satsuki'],
 'v4:2:investigate:I2-39:spot':['satsuki'],
 'v4:2:investigate:I2-43:spot':['yuu'],
 'v4:2:investigate:I2-44:spot':['yuu'],
 'v4:2:investigate:I2-45:spot':['sora'],
 'I3-05-rule':['lappy'], 'I3-09-first-scene':['sho','satsuki'],
 'I3-30-paper':['koto'], 'I3-33-memory':['nana'],
 'I3-36-observers':['rin','rei'], 'I3-46-morning':['akari'],
 'I3-51-two-files':['sho'],
 'I4-06-rewind':['akari','nana'], 'I4-14-observers':['akari'],
 'I4-19-locations':['koto'], 'I4-23-light':['satsuki'],
 'I4-31-testimony':['rei'], 'I4-43-meeting':['nana'],
 'v4:5:investigate:I11-12:spot':['nana'],
 'v4:5:investigate:I22-23:spot':['nana'],
 'v4:5:investigate:I24-25:spot':['nana','lappy'],
 'v4:5:investigate:I26-28:spot':['rin','nana'],
 'v4:5:investigate:I29-30:spot':['sho'],
 'v4:5:investigate:I31-34:spot':['satsuki'],
 'v4:5:investigate:I35-36:spot':['rin','akari'],
 'v4:5:investigate:I37-38:spot':['akari'],
 'v4:5:investigate:I42-44:spot':['sho','akari'],
 'v4:5:investigate:I45-46:spot':['akari'],
 'v4:5:investigate:I51:spot':['satsuki'],
 'v4:5:investigate:I52:spot':['sho','rin','nana'],
 'v4:5:investigate:I56:spot':['nana','satsuki'],
 'v4:6:investigate:I6-03-04:spot':['nana','rin'],
 'v4:6:investigate:I6-05-08:spot':['nana','rin'],
 'v4:6:investigate:I6-21-26:spot':['lappy','nana'],
 'v4:6:investigate:I6-33-36:spot':['rin','sho','lappy'],
 'v4:6:investigate:I6-37-40:spot':['nana'],
}


def _source(root,prefix):
    paths=list((root/'docs/design/rewrite_v4').glob(prefix+'_*.md'))
    if len(paths)!=1:raise ValueError('Investigation source missing/ambiguous '+prefix)
    p=paths[0];raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    if digest!=SOURCE_HASHES.get(prefix):raise ValueError('Investigation source changed; review placement '+p.name)
    source_hash=hashlib.sha256(p.read_text(encoding='utf-8-sig').encode('utf-8')).hexdigest()
    return p,raw.decode('utf-8-sig').splitlines(),source_hash


def build_placements(root=None):
    root=Path(root) if root else ROOT
    world=json.loads((root/'art/space_v4/runtime_v1/world.json').read_text(encoding='utf-8'))['spaces']
    spots={};markers=[]
    for spot_id,row in SPOT_ROWS.items():
        prefix,location,room,source_line=row
        room=SPACE_CORRECTIONS.get(spot_id,room)
        if room not in world:raise ValueError('Unbound actual investigation room '+spot_id)
        path,lines,digest=_source(root,prefix)
        heading=next((i for i in range(source_line,0,-1) if re.match(r'^#{2,5}\s+'+re.escape(location)+r'(?:\s|$)',lines[i-1])),None)
        if heading is None:raise ValueError('Investigation entry heading changed '+spot_id)
        proof_line=next((i for i in range(heading+1,min(len(lines)+1,heading+26)) if lines[i-1].startswith(('(','['))),source_line)
        target=EXISTING_TARGETS.get(spot_id)
        match=next((t for t in world[room]['targets'] if t['id']==target),None) if target else None
        # Source-specific absent props remain visibly authored markers instead
        # of relabelling an unrelated piece of existing mesh as the clue.
        if target and match is None:target=None
        kind='existing-mesh-target' if target else 'authored-interaction-marker'
        position=list(match['p']) if match else list(AUTHORED_ANCHORS[room])
        marker_id='v4-investigation-marker:'+spot_id
        if not target:target=marker_id
        value={'space_id':room,'target_id':target,'world_pos':position,'coordinateSystem':'runtime-world-xyz',
               'geometryReady':True,'needsSpaceBinding':False,'needsActorPlacement':False,
               'placementKind':kind,'placementPolicy':'Production interaction staging in this game. This is neither recovered V3 geometry nor new story evidence.',
               'sourceRoomVerified':True,'objectMeshMatched':bool(match),'reaGeometryRecovered':False,
               'authoredTransform':not bool(match),'visibleMarkerRequired':True,'runtimeVerified':False,
               'neutralLabel':'대화하기' if spot_id in INTERVIEWEES else '조사하기',
               'interviewActors':INTERVIEWEES.get(spot_id,[]),
               'sourceProof':{'file':path.name,'line':proof_line,'fileSha256':digest,'location':location,'quote':lines[proof_line-1]},
               'scope':'only-while-this-spot-is-active; source entry, return, conditions and acquisition remain unchanged'}
        if spot_id.startswith('v4:6:investigate:I6-03'):
            value.update(sourceSetting='현재 코어 홀 바깥 점검 구역',productionSetReuse=True,
                         objectMeshMatched=False,needsDedicatedSet=True,
                         physicalGeometryLimit='No current wall trim is renamed as the historical fall guardrail. This visible marker opens actual current-label/old-photo comparison; dedicated replacement railing geometry is still needed.')
        if spot_id.startswith('v4:6:investigate:I6-05'):
            value.update(sourceSetting='현재 코어 홀 옆 관리 출입 통로',productionSetReuse=True,
                         needsDedicatedSet=True,
                         physicalGeometryLimit='Current side-entry sight comparison only. Existing corridor mesh is a production set; exact old doorway angle/occlusion, fall height and topology are not proved.')
        spots[spot_id]=value
        markers.append({'id':marker_id,'spot_id':spot_id,'space_id':room,'world_pos':position,'coordinateSystem':'runtime-world-xyz',
                        'label':value['neutralLabel'],'interviewActors':value['interviewActors'],
                        'visibleWhenSpotActive':spot_id,'markerRequiredEvenIfExistingTarget':True,
                        'kind':kind,'target_id':target,'sourceProof':value['sourceProof'],
                        'authoredTransform':value['authoredTransform']})
    return {'version':1,'spots':spots,'markers':markers,
            'geometryReadinessMeaning':'Authored selectable affordance specification is ready for native cook; runtime display/click verification is separate.',
            'dedicatedSetsStillNeeded':[{'setting':'현재 코어 홀 외부 점검 구역/옆 관리 출입','source':'16b1:I6-03..08','constraints':['난간은 사고 후 교체됨; 현재 견고함으로 과거 상태 확정 금지','주 점검 통로와 나나가 있던 옆 관리 출입을 별도 동선으로 표시','현재 문 부품과 옛 문·가림의 차이를 구별','나나는 홀 안에 들어가지 않고 옆 출입 문틈에서 봄','현재 룸 mesh 좌표를 5년 전 실측/추락 높이로 주장 금지']}],
            'writesFiles':False}


def apply_placements(chapters,root=None):
    """Modify only matching passed dictionaries; caller owns save/cook order."""
    layout=build_placements(root);found=set()
    for chapter,graph in chapters.items():
        for node in graph.get('nodes',{}).values():
            if node.get('type')!='investigate':continue
            for spot in node.get('spots',[]):
                binding=layout['spots'].get(spot.get('id'))
                if not binding:continue
                ref=node.get('source') or graph.get('nodes',{}).get(spot.get('entry'),{}).get('source') or {}
                expected=SPOT_ROWS[spot['id']]
                if ref.get('file')!=binding['sourceProof']['file'] or ref.get('location')!=expected[1] or ref.get('fileSha256')!=binding['sourceProof']['fileSha256']:
                    raise ValueError('Current investigation graph source differs from reviewed placement '+spot['id'])
                original={k:deepcopy(spot.get(k)) for k in ['entry','returnTo','completionFlag','onReturnSet','required']}
                spot.update(deepcopy(binding));found.add(spot['id'])
                if any(spot.get(k)!=v for k,v in original.items()):raise AssertionError('Placement changed story routing '+spot['id'])
    return {'boundSpots':len(found),'availableSpots':len(layout['spots']),'unmatchedSpotIds':sorted(set(layout['spots'])-found),'markers':layout['markers'],'dedicatedSetsStillNeeded':layout['dedicatedSetsStillNeeded']}

# Frozen current source entry identities after direct scene review.
SPOT_ROWS={
 "v4:11b:I-12d": [
  "11b",
  "I-12d",
  "management_office",
  877
 ],
 "v4:11b:I-12c": [
  "11b",
  "I-12c",
  "service_lounge",
  825
 ],
 "v4:11b:I-12b": [
  "11b",
  "I-12b",
  "service_lounge",
  787
 ],
 "v4:11b:I-12": [
  "11b",
  "I-12",
  "hotel_lobby",
  673
 ],
 "v4:11b:I-11": [
  "11b",
  "I-11",
  "service_lounge",
  641
 ],
 "v4:11b:I-10": [
  "11b",
  "I-10",
  "service_lounge",
  613
 ],
 "v4:11b:I-09": [
  "11b",
  "I-09",
  "hotel_corridor",
  585
 ],
 "v4:11b:I-08": [
  "11b",
  "I-08",
  "clinic",
  525
 ],
 "v4:11b:I-07": [
  "11b",
  "I-07",
  "hotel_lobby",
  469
 ],
 "v4:11b:I-06": [
  "11b",
  "I-06",
  "service_lounge",
  431
 ],
 "v4:11b:I-05": [
  "11b",
  "I-05",
  "service_lounge",
  363
 ],
 "v4:11b:I-04": [
  "11b",
  "I-04",
  "service_lounge",
  321
 ],
 "v4:11b:I-03": [
  "11b",
  "I-03",
  "service_lounge",
  291
 ],
 "v4:11b:I-02": [
  "11b",
  "I-02",
  "service_lounge",
  74
 ],
 "v4:2:investigate:I2-45:spot": [
  "12b4",
  "I2-45",
  "hotel_lobby",
  205
 ],
 "v4:2:investigate:I2-44:spot": [
  "12b4",
  "I2-44",
  "hotel_lobby",
  177
 ],
 "v4:2:investigate:I2-43:spot": [
  "12b4",
  "I2-43",
  "hotel_lobby",
  157
 ],
 "v4:2:investigate:I2-42:spot": [
  "12b4",
  "I2-42",
  "performance_stage",
  141
 ],
 "v4:2:investigate:I2-41:spot": [
  "12b4",
  "I2-41",
  "performance_stage",
  127
 ],
 "v4:2:investigate:I2-40:spot": [
  "12b4",
  "I2-40",
  "hotel_lobby",
  109
 ],
 "v4:2:investigate:I2-39:spot": [
  "12b4",
  "I2-39",
  "cold_store",
  89
 ],
 "v4:2:investigate:I2-38:spot": [
  "12b4",
  "I2-38",
  "cold_store",
  63
 ],
 "v4:2:investigate:I2-37:spot": [
  "12b4",
  "I2-37",
  "cold_store",
  31
 ],
 "v4:2:investigate:I2-36:spot": [
  "12b4",
  "I2-36",
  "hotel_lobby",
  5
 ],
 "v4:2:investigate:I2-35:spot": [
  "12b3",
  "I2-35",
  "hotel_lobby",
  271
 ],
 "v4:2:investigate:I2-34:spot": [
  "12b3",
  "I2-34",
  "hotel_multiuse",
  249
 ],
 "v4:2:investigate:I2-32b-33:spot": [
  "12b3",
  "I2-32b",
  "hotel_multiuse",
  193
 ],
 "v4:2:investigate:I2-31-32:spot": [
  "12b3",
  "I2-31",
  "hotel_lobby",
  139
 ],
 "v4:2:investigate:I2-30:spot": [
  "12b3",
  "I2-30",
  "hotel_lobby",
  113
 ],
 "v4:2:investigate:I2-27-29:spot": [
  "12b3",
  "I2-27",
  "hotel_lobby",
  49
 ],
 "v4:2:investigate:I2-25-26:spot": [
  "12b3",
  "I2-25",
  "cold_store",
  5
 ],
 "v4:2:investigate:I2-24:spot": [
  "12b2",
  "I2-24",
  "cold_store",
  315
 ],
 "v4:2:investigate:I2-23:spot": [
  "12b2",
  "I2-23",
  "cold_store",
  291
 ],
 "v4:2:investigate:I2-19-22:spot": [
  "12b2",
  "I2-19",
  "performance_stage",
  193
 ],
 "v4:2:investigate:I2-18:spot": [
  "12b2",
  "I2-18",
  "performance_stage",
  139
 ],
 "v4:2:investigate:I2-16-17:spot": [
  "12b2",
  "I2-16",
  "staff_passage",
  93
 ],
 "v4:2:investigate:I2-15:spot": [
  "12b2",
  "I2-15",
  "staff_passage",
  73
 ],
 "v4:2:investigate:I2-14:spot": [
  "12b2",
  "I2-14",
  "staff_passage",
  53
 ],
 "v4:2:investigate:I2-13:spot": [
  "12b2",
  "I2-13",
  "performance_stage",
  31
 ],
 "v4:2:investigate:I2-10:spot": [
  "12b1",
  "I2-10",
  "hotel_lobby",
  278
 ],
 "v4:2:investigate:I2-09:spot": [
  "12b1",
  "I2-09",
  "hotel_multiuse",
  260
 ],
 "v4:2:investigate:I2-08:spot": [
  "12b1",
  "I2-08",
  "hotel_lobby",
  228
 ],
 "v4:2:investigate:I2-07:spot": [
  "12b1",
  "I2-07",
  "hotel_lobby",
  202
 ],
 "v4:2:investigate:I2-06:spot": [
  "12b1",
  "I2-06",
  "hotel_lobby",
  166
 ],
 "v4:2:investigate:I2-05:spot": [
  "12b1",
  "I2-05",
  "hotel_multiuse",
  138
 ],
 "v4:2:investigate:I2-04:spot": [
  "12b1",
  "I2-04",
  "hotel_multiuse",
  102
 ],
 "v4:2:investigate:I2-03:spot": [
  "12b1",
  "I2-03",
  "hotel_multiuse",
  58
 ],
 "I3-51-two-files": [
  "13b4",
  "I3-51",
  "mirror_waiting",
  193
 ],
 "I3-46-morning": [
  "13b4",
  "I3-46",
  "mirror_waiting",
  103
 ],
 "I3-40-record": [
  "13b4",
  "I3-40",
  "record_room",
  7
 ],
 "I3-36-observers": [
  "13b3",
  "I3-36",
  "mirror_waiting",
  169
 ],
 "I3-33-memory": [
  "13b3",
  "I3-33",
  "mirror_waiting",
  77
 ],
 "I3-30-paper": [
  "13b3",
  "I3-30",
  "mirror_waiting",
  7
 ],
 "I3-12-reflection": [
  "13b1",
  "I3-12",
  "mirror_workbay",
  555
 ],
 "I3-10-tools": [
  "13b1",
  "I3-10",
  "mirror_workbay",
  483
 ],
 "I3-09-first-scene": [
  "13b1",
  "I3-09",
  "mirror_workbay",
  221
 ],
 "I3-05-rule": [
  "13b1",
  "I3-05",
  "mirror_waiting",
  133
 ],
 "I4-49-capability": [
  "14b4",
  "I4-49",
  "inspection_hall_changed",
  7
 ],
 "I4-43-meeting": [
  "14b3",
  "I4-43",
  "inspection_hall_changed",
  225
 ],
 "I4-40-photos": [
  "14b3",
  "I4-40",
  "inspection_hall_changed",
  195
 ],
 "I4-31-testimony": [
  "14b2",
  "I4-31",
  "inspection_hall_changed",
  169
 ],
 "I4-28-routes": [
  "14b2",
  "I4-28",
  "inspection_hall_changed",
  127
 ],
 "I4-23-light": [
  "14b2",
  "I4-23",
  "inspection_hall_normal",
  61
 ],
 "I4-19-locations": [
  "14b2",
  "I4-19",
  "inspection_hall_changed",
  7
 ],
 "I4-14-observers": [
  "14b1",
  "I4-14",
  "inspection_hall_changed",
  165
 ],
 "I4-09-rear": [
  "14b1",
  "I4-09",
  "inspection_hall_changed",
  107
 ],
 "I4-06-rewind": [
  "14b1",
  "I4-06",
  "inspection_hall_changed",
  71
 ],
 "I4-04-fastening": [
  "14b1",
  "I4-04",
  "inspection_hall_changed",
  47
 ],
 "I4-02-file": [
  "14b1",
  "I4-02",
  "inspection_hall_changed",
  21
 ],
 "v4:5:investigate:I57:spot": [
  "15b3",
  "I5-57",
  "hotel_lobby",
  467
 ],
 "v4:5:investigate:I56:spot": [
  "15b3",
  "I5-56",
  "hotel_lobby",
  455
 ],
 "v4:5:investigate:I55:spot": [
  "15b3",
  "I5-55",
  "hotel_lobby",
  235
 ],
 "v4:5:investigate:I53-54:spot": [
  "15b3",
  "I5-53",
  "hotel_lobby",
  211
 ],
 "v4:5:investigate:I52:spot": [
  "15b3",
  "I5-52",
  "hotel_lobby",
  199
 ],
 "v4:5:investigate:I51:spot": [
  "15b3",
  "I5-51",
  "hotel_lobby",
  189
 ],
 "v4:5:investigate:I50:spot": [
  "15b3",
  "I5-50",
  "hotel_lobby",
  169
 ],
 "v4:5:investigate:I47-49:spot": [
  "15b3",
  "I5-47",
  "hotel_lobby",
  127
 ],
 "v4:5:investigate:I45-46:spot": [
  "15b3",
  "I5-45",
  "hotel_lobby",
  97
 ],
 "v4:5:investigate:I42-44:spot": [
  "15b3",
  "I5-42",
  "hotel_lobby",
  45
 ],
 "v4:5:investigate:I39-41:spot": [
  "15b3",
  "I5-39",
  "hotel_lobby",
  5
 ],
 "v4:5:investigate:I37-38:spot": [
  "15b2",
  "I5-37",
  "hotel_lobby",
  349
 ],
 "v4:5:investigate:I35-36:spot": [
  "15b2",
  "I5-35",
  "hotel_lobby",
  273
 ],
 "v4:5:investigate:I31-34:spot": [
  "15b2",
  "I5-31",
  "hotel_lobby",
  163
 ],
 "v4:5:investigate:I29-30:spot": [
  "15b2",
  "I5-29",
  "hotel_lobby",
  137
 ],
 "v4:5:investigate:I26-28:spot": [
  "15b2",
  "I5-26",
  "central_control",
  95
 ],
 "v4:5:investigate:I24-25:spot": [
  "15b2",
  "I5-24",
  None,
  67
 ],
 "v4:5:investigate:I22-23:spot": [
  "15b2",
  "I5-22",
  None,
  39
 ],
 "v4:5:investigate:I21:spot": [
  "15b2",
  "I5-21",
  None,
  27
 ],
 "v4:5:investigate:I19-20:spot": [
  "15b2",
  "I5-19",
  None,
  5
 ],
 "v4:5:investigate:I17-18:spot": [
  "15b1",
  "I5-17",
  "hotel_lobby",
  236
 ],
 "v4:5:investigate:I15-16:spot": [
  "15b1",
  "I5-15",
  "hotel_lobby",
  210
 ],
 "v4:5:investigate:I13-14:spot": [
  "15b1",
  "I5-13",
  "hotel_lobby",
  182
 ],
 "v4:5:investigate:I11-12:spot": [
  "15b1",
  "I5-11",
  "hotel_lobby",
  150
 ],
 "v4:5:investigate:I08-09:spot": [
  "15b1",
  "I5-08",
  "hotel_lobby",
  105
 ],
 "v4:5:investigate:I06-07:spot": [
  "15b1",
  "I5-06",
  "hotel_lobby",
  77
 ],
 "v4:5:investigate:I02-05:spot": [
  "15b1",
  "I5-02",
  "hotel_lobby",
  21
 ],
 "v4:6:investigate:I6-37-40:spot": [
  "16b2",
  "I6-37",
  "operating_archive",
  383
 ],
 "v4:6:investigate:I6-33-36:spot": [
  "16b2",
  "I6-33",
  "operating_archive",
  157
 ],
 "v4:6:investigate:I6-30-32:spot": [
  "16b2",
  "I6-30",
  "operating_archive",
  123
 ],
 "v4:6:investigate:I6-27-29:spot": [
  "16b2",
  "I6-27",
  "operating_archive",
  77
 ],
 "v4:6:investigate:I6-21-26:spot": [
  "16b2",
  "I6-21",
  "operating_archive",
  5
 ],
 "v4:6:investigate:I6-18-20:spot": [
  "16b1",
  "I6-18",
  "operating_archive",
  432
 ],
 "v4:6:investigate:I6-16-17:spot": [
  "16b1",
  "I6-16",
  "operating_archive",
  412
 ],
 "v4:6:investigate:I6-14-15:spot": [
  "16b1",
  "I6-14",
  "operating_archive",
  359
 ],
 "v4:6:investigate:I6-13:spot": [
  "16b1",
  "I6-13",
  "operating_archive",
  339
 ],
 "v4:6:investigate:I6-09-12:spot": [
  "16b1",
  "I6-09",
  "operating_archive",
  199
 ],
 "v4:6:investigate:I6-05-08:spot": [
  "16b1",
  "I6-05",
  "",
  47
 ],
 "v4:6:investigate:I6-03-04:spot": [
  "16b1",
  "I6-03",
  "",
  25
 ],
 "v4:6:investigate:I6-01-02:spot": [
  "16b1",
  "I6-01",
  "operating_archive",
  5
 ]
}

SOURCE_HASHES={
 "11b": "f8d045e001f974f3f9e191ff9148a6f16e7a19bcb519027f96013dffd348b440",
 "12b4": "c92988172538c793246bf99a3f145676b714d07f25697410b4cc29bf8f1fa144",
 "12b3": "75c3e6463227cb1d53f085712d574014368cebe0183f411c4be8ee446503ac06",
 "12b2": "048d002f839de495a281083fbd320ab74a35e568ddfc9b9cd5199abf13e3776d",
 "12b1": "2574cba1fd5e559572086a9d26ead0815ef6683601fec3d6dbf6216b6284a038",
 "13b4": "1642c7bdd2598a7504b4df4e17989dc83e6145e477d4cff266c4fe974ebb145b",
 "13b3": "e972c97d50a6c3ae07619a3942b458659c71998ae9e320f0e987c6d631de2784",
 "13b1": "ac8f9cd2ddd3908425f49e98b1e89f0e85df340cdfca2ed29e526e94e00e566d",
 "14b4": "ca2c42752f0ca48a383ea061e7274d7fc51cd6450c38a412f95a04d42f0373a8",
 "14b3": "0b07d49b5e9bb0bbcd1133ff7248244beb4fde975a794967105aded8bedae8e8",
 "14b2": "47b13067ba33ee4fa88b5121946b403150f20db7838f53ad5f5168b66111bb3e",
 "14b1": "3f15d267d63e3590b86548b34476a8a930fc19bccc8b795d971ec87d1c889242",
 "15b3": "03272fe532a1cad06636a76edabedc30269fd73dca7ae5562000ea12c283c46b",
 "15b2": "a827fd9f8d2fe2165f5859544b97ffa959fa889eee191faf1075f4c43728c4a7",
 "15b1": "c2860b29664e1322c5ac7feb9fd8b2fc1b7b98faf70325e72d2450e48a736efe",
 "16b2": "7c21e8c05339d824aee447ea5decc953974f27a369e48f9bbb681d611ccedb4e",
 "16b1": "1f9606f1aa1d0f464ba3dbfe82eb5a725afbf9dd7a908b9a4f4e6d4e7b19861a"
}
