"""Use the project's image runtime, not Blender's Python, for lossless compaction."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import compile_v4_rebuilt_environment as C
from v4_lowpoly_glb import read
O=R/'art/space_v4/facility_architecture_v2';O.mkdir(exist_ok=True);file=O/'manifest.json'
if file.exists():m=json.loads(file.read_text())
else:
    # Recover the already successfully exported food pair after image-module
    # import failed. Do not reassemble or export completed geometry again.
    raw=R/'art/space_v4/rebuild_v1/raw/finish_context.glb';j,b=read(raw);rows=[]
    for n in j['nodes']:
        e=n.get('extras',{})
        if e.get('architectureVersion')==2:rows.append({'id':e['facilityIdentity'],'role':e['architectureFamily'],'features':e['purposeFeatures'],'size':e['nominalSize'],'roof':e['roofStyle']})
    assert len(rows)==2
    m={'architectureVersion':2,'allFacadesRebuilt':False,'rows':rows,'rawAsset':{'file':raw.relative_to(R).as_posix(),'runtime':'Assets/Art/explore3d/finish_context.glb','purposeArchitecture':30},'runtimeAccepted':False}
C.O=O;(O/'models').mkdir(exist_ok=True);m['asset']=C.compile(m['rawAsset']);file.write_text(json.dumps(m,indent=2)+'\n');print('ARCHITECTURE_CANDIDATE_COMPACTED',len(m['rows']))
