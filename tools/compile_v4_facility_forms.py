"""Compact the current authored whole-exterior candidate without publishing it."""
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import compile_v4_rebuilt_environment as C
O=R/'art/space_v4/facility_forms_v3';(O/'models').mkdir(exist_ok=True);p=O/'manifest.json';m=json.loads(p.read_text(encoding='utf8'));previous=C.O;C.O=O
try:m['asset']=C.compile(m['rawAsset'])
finally:C.O=previous
p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('FORMS_CANDIDATE_COMPACTED',m['asset']['triangles'],m['asset']['materialPrimitives'],m['asset']['bytes'])
