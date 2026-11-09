"""Shared lightweight closed gate; loaded only by the initial park scene."""
import bpy,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import v4_rebuilt_environment_kit as K
import build_v4_rebuilt_environment as A
O=R/'art/space_v4/park_levels_v1';bpy.ops.wm.read_factory_settings(use_empty=True);K.setup_materials();root=K.root('closed_park_gate')
for side in [-1,1]:
    panel=K.root('hinged_gate_leaf',root)
    for k in range(9):
        x=side*(.2+k*.38);K.tube('forged_gate_bar',[(x,0,.2),(x,0,2.55)],[.035,.035],'iron',panel,6)
    for z in [.35,1.15,2.35]:K.tube('gate_cross_rail',[(side*.12,0,z),(side*3.42,0,z)],[.055,.055],'brass',panel,8)
    K.tube('gate_bracing_diagonal',[(side*.18,0,.4),(side*3.37,0,2.3)],[.035,.035],'iron',panel,6)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'gate-source.blend'),compress=True);A.O=O
row=A.export([root,*root.children_recursive],'gate.glb','Assets/Art/park_levels/gate.glb',{'function':'chapter-locked public gate, hidden when opened'})
(O/'gate-raw.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf8')
