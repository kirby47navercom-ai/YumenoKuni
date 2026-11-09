"""Pure adapters for original, source-constrained dedicated production sets.

The caller owns saving/cooking and native testing. No Game, engine, Blender or
central story generator is launched here. A source-addressed set change never
creates knowledge, a historical camera, a route, an unlock, or an inventory item.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
OUTPUT='art/space_v4/dedicated_v1'
INSTANCE_ORIGINS={
 'core_external_inspection':[12,-5.76,-22],
 'hotel_indoor_garden':[-14,0,-24], 'garden_rest_area':[-14,0,-24],
 'souvenir_shop':[10,0,4], 'souvenir_forecourt':[10,0,4],
 'hotel_rest_lounge':[15,0,-24], 'hotel_washroom':[15,0,-35],
 'can_toss_booth':[15,0,12],
}
CORE_TARGETS={
 'v4:6:investigate:I6-03-04:spot':'current_replacement_label',
 'v4:6:investigate:I6-05-08:spot':'side_management_entry',
}
REST_SOURCES={'21','29','31','38','43','44','46','48','52','54','55','57','60','61','62','88','144','145','151','152'}


def _load(path):return json.loads(path.read_text(encoding='utf-8'))


def build(root=None):
    """Return checked world/copy metadata; all model identities are frozen by manifest."""
    root=Path(root) if root else ROOT
    folder=root/OUTPUT;manifest=_load(folder/'manifest.json')
    if manifest.get('builderSha256')!=hashlib.sha256((root/manifest['builder']).read_bytes()).hexdigest():
        raise ValueError('Dedicated builder changed; regenerate and inspect its models')
    extension=_load(folder/'world_extension.json');copies=_load(folder/'copy_manifest.json')
    if set(extension['spaces'])!=set(INSTANCE_ORIGINS):raise ValueError('Dedicated set identity changed')
    for record in manifest['spaces']:
        p=root/record['file'];raw=p.read_bytes()
        if raw[:4]!=b'glTF' or hashlib.sha256(raw).hexdigest()!=record['sha256']:
            raise ValueError('Dedicated model changed; rebuild/review '+record['id'])
    for row in copies:
        if not (root/row['from']).is_file():raise FileNotFoundError(row['from'])
    return {'spaces':extension['spaces'],'copies':copies,'manifest':manifest,
            'coordinateSystem':'runtime-world-xyz','productionLayout':True,
            'reaGeometryRecovered':False,'runtimeVerified':False}


def apply_world(world,root=None):
    """Extend the passed world in place. No new story-access connection is inferred."""
    data=build(root)
    for id,spec in data['spaces'].items():
        spec=deepcopy(spec)
        # This seated viewpoint otherwise faces a wall, leaving the actual
        # garden bench and foliage outside the dialogue camera's narrow FOV.
        if id=='garden_rest_area':spec['entry_yaw']=50
        if id in world.setdefault('spaces',{}) and world['spaces'][id]!=spec:
            raise ValueError('Would overwrite different space '+id)
        world['spaces'][id]=deepcopy(spec)
        instance={'space':id,'p':INSTANCE_ORIGINS[id],'label':spec['label'],
                  'rotation':0,'occupant':'','productionLayout':True,
                  'reaGeometryRecovered':False,'coordinateSystem':'runtime-world-xyz'}
        if id in world.setdefault('instances',{}) and world['instances'][id]!=instance:
            raise ValueError('Would overwrite different instance '+id)
        world['instances'][id]=deepcopy(instance)
    from v4_stair_enclosure import apply_world as enclose_stair
    stair_copies=enclose_stair(world)
    from v4_mirror_lighting import copies as mirror_light_copies
    return {'addedSpaces':len(data['spaces']),'copies':data['copies']+stair_copies+mirror_light_copies(world),
            'connectionsAdded':0,'unlocksAdded':0,'runtimeVerified':False}


def _space(prefix,line,old):
    # Only explicitly reviewed current-source room segments are replaced.
    # A lobby remains a lobby even when another paragraph calls a rest lounge.
    if prefix in REST_SOURCES and old=='hotel_lobby':
        if prefix=='55' and line<24:return old
        return 'hotel_rest_lounge'
    if prefix=='26' and 417<=line<501:return 'hotel_rest_lounge'
    if prefix=='27' and old=='park_garden':return 'hotel_indoor_garden'
    if prefix=='147' and old=='park_garden':return 'hotel_indoor_garden' if line<111 else 'garden_rest_area'
    if prefix in {'45','58'} and old=='park_garden':return 'garden_rest_area'
    if prefix=='37' and old=='laundry_room':return 'hotel_washroom'
    if prefix in {'42','59'} and old=='ticket_booth':return 'can_toss_booth'
    if prefix in {'20','28','150'} and old=='supply_store':return 'souvenir_shop'
    if prefix=='35' and old=='supply_store' and line>=410:return 'souvenir_shop'
    if prefix in {'30','41','90'} and old=='supply_store':return 'souvenir_forecourt'
    if prefix=='143' and line<91 and old=='supply_store':return 'souvenir_shop'
    if prefix=='148' and line>=85 and old=='supply_store':return 'souvenir_forecourt'
    if prefix=='34':
        if old=='supply_store':return 'souvenir_shop'
        if old=='park_garden':return 'souvenir_forecourt'
    if prefix=='87' and line>=45 and old=='park_garden':return 'souvenir_forecourt'
    return old


def _retarget(row,space):
    old=row['space'];row['space']=space
    if old!=space:
        row.update(productionLayout=True,meshOnly=False,previousProductionSet=old,
                   dedicatedProductionSet=True,reaGeometryRecovered=False,runtimeVerified=False,
                   geometryPolicy='Original authored production layout for this exact current manuscript setting. Dimensions and transforms are production choices; not original-game measurements or historical eyewitness facts.')
    return row


def apply_scene_bindings(scene_data,root=None):
    """Mutate reviewed ranges only, preserving all CG, perspective and source IDs."""
    root=Path(root) if root else ROOT;build(root)
    # Reuse the direct-reading table's frozen source checks, including final73
    # executable FTE graphs. This is not a substring/keyword room classifier.
    from v4_scene_bindings_more import build_more
    build_more(root)
    changed=0;ranges=[]
    for original in scene_data.get('sceneRanges',[]):
        prefix=Path(original['source']['file']).stem.split('_')[0]
        cuts=[original['startLine'],original['endLineExclusive']]
        for cut in {'55':[24],'147':[111]}.get(prefix,[]):
            if cuts[0]<cut<cuts[1]:cuts.append(cut)
        cuts.sort()
        for start,end in zip(cuts,cuts[1:]):
            row=deepcopy(original);row.update(startLine=start,endLineExclusive=end)
            new=_space(prefix,start,row['space'])
            if new!=row['space']:changed+=1
            _retarget(row,new)
            if start!=original['startLine']:
                p=root/'docs/design/rewrite_v4'/row['source']['file']
                line=p.read_text(encoding='utf-8-sig').splitlines()[start-1]
                row['source'].update(line=start,quote=line)
            ranges.append(row)
    # Current external inspection / side-entry source only. Nothing in this
    # range reenacts the old event or changes the current replacement guardrail.
    from v4_investigation_placements import build_placements
    core=build_placements(root)['spots'][next(iter(CORE_TARGETS))]['sourceProof']
    if not any(r.get('kind')=='dedicated-current-core-setting' for r in ranges):
        row={'space':'core_external_inspection','source':deepcopy(core),
             'startLine':25,'endLineExclusive':199,'perspective':'current-observation',
             'kind':'dedicated-current-core-setting','knowledgeGrant':False,
             'actorPositionsAssigned':False,'clearCgOnEntry':True,
             'scope':'only-when-these-source-nodes-actually-run'}
        row['productionLayout']=True;row['reaGeometryRecovered']=False
        ranges.append(row)
    scene_data['sceneRanges']=ranges
    # Main later-chapter table remains source-exact. FTEs are ranges, not global
    # room-name aliases; no broad hotel_lobby replacement is permitted.
    scene_data['dedicatedSets']={'count':6,'viewpointVariants':2,'changedSourceRanges':changed,
                                 'coordinateSystem':'runtime-world-xyz','runtimeVerified':False,
                                 'statefulPropsRequireRendererBinding':[
                                     'Current garden drawing/cleaning cloth/bucket only on the actual source route.',
                                     'Actual chosen toy ownership/repair; displayed cars and fish are neutral stock.',
                                     'Current go/ring board, photo/picture book and paper/card game states.',
                                     'Current washroom towel/tool use and return; actor reflection support.',
                                     'Current remaining cans/balls and source-specific throw animation.']}
    for row in scene_data.get('dedicatedSetNeeds',[]):
        row.update(productionMeshesReady=True,nativeRuntimeVerified=False,
                   dynamicPropStatesVerified=False)
    return scene_data['dedicatedSets']


def apply_placement_report(report,root=None):
    """Update a placement report or full build_placements layout, in place."""
    spaces=build(root)['spaces'];spec=spaces['core_external_inspection'];changed=0
    for id,target_id in CORE_TARGETS.items():
        t=next(t for t in spec['targets'] if t['id']==target_id)
        values={'space_id':spec['id'],'target_id':target_id,'world_pos':deepcopy(t['p']),
                'coordinateSystem':'runtime-world-xyz','placementKind':'dedicated-authored-mesh-target',
                'objectMeshMatched':True,'authoredTransform':True,'productionSetReuse':False,
                'needsDedicatedSet':False,'reaGeometryRecovered':False,'runtimeVerified':False,
                'physicalGeometryLimit':'Current authored replacement rail and side-entry geometry only. Historical camera, doorway occlusion, former rail strength and fall height remain source-document questions.'}
        if id in report.get('spots',{}):report['spots'][id].update(deepcopy(values));changed+=1
        for marker in report.get('markers',[]):
            if marker.get('spot_id')==id:
                marker.update(deepcopy(values));marker['kind']=values['placementKind'];changed+=1
    report['dedicatedSetsStillNeeded']=[r for r in report.get('dedicatedSetsStillNeeded',[]) if r.get('source')!='16b1:I6-03..08']
    report['dedicatedSetRuntimeVerified']=False
    return changed


def apply_placements(chapters,report=None,root=None):
    """After ordinary apply_placements, replace two exact current core targets."""
    from v4_investigation_placements import build_placements
    layout=build_placements(root);apply_placement_report(layout,root);found=[]
    for graph in chapters.values():
        for node in graph.get('nodes',{}).values():
            for spot in node.get('spots',[]) if node.get('type')=='investigate' else []:
                id=spot.get('id')
                if id not in CORE_TARGETS:continue
                binding=layout['spots'][id]
                if spot.get('sourceProof',{}).get('fileSha256')!=binding['sourceProof']['fileSha256']:
                    raise ValueError('Apply reviewed ordinary placement first '+id)
                spot.update(deepcopy(binding));found.append(id)
    if report is not None:apply_placement_report(report,root)
    return {'updatedCoreSpots':sorted(found),'expectedCoreSpots':sorted(CORE_TARGETS),
            'runtimeVerified':False}
