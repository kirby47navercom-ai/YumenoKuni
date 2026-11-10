"""Remove remaining generic booth/curtain/workbay forms; preserve room contracts."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import build_v4_rebuilt_environment as A
import v4_rebuilt_environment_kit as K
import v4_facility_identity as I
import v4_facility_architecture as F
O=A.O;p=O/'room-assembly.json';manifest=json.loads(p.read_text());changed=[]
only=next((set(s.split('=',1)[1].split(','))for s in sys.argv if s.startswith('--only=')),None)
for ident in ['ticket_booth','performance_stage','mirror_workbay','maintenance_workshop','supply_store']:
    if only and ident not in only:continue
    row=next(a for a in manifest['assets']if a['runtime'].endswith('/'+ident+'.glb'));A.clean();bpy.ops.import_scene.gltf(filepath=str(R/row['file']));I.setup();w,d,h=A.SPECS[ident]['size_m']
    if ident=='ticket_booth':
        # Keep the real counter and seat, replace the generic house shell only.
        root=bpy.data.objects['ticket_booth']
        old=[o for o in root.children if o.name.startswith(('coherent_hip_roof','continuous_structural','continuous_mitred_wall_shell','pierced_facade','inset_glazing','recessed_window','continuous_entrance','architectural_ticket_booth','public_ticket_window_frame','recessed_public_ticket_window'))]
        for o in old:A.erase(A.descendants(o))
        A.erase([o for o in bpy.data.objects if o.name.startswith(('paper_ticket_roll','ticket_roll_core','ticket_transaction_tray'))]);shell=F.build(ident,w,d,h,I);shell.parent=root
        # F.build owns the same physical aperture in room and park envelope.
        counter=next(o for o in bpy.data.objects if o.name=='reception_counter');bpy.context.view_layer.update();points=[o.matrix_world@Vector(v)for o in counter.children_recursive if o.type=='MESH'for v in o.bound_box];top=max(v.z for v in points);center=counter.matrix_world.translation
        for i in [-1,0,1]:
            x=center.x+i*.35;y=center.y-.12;z=top+.105
            K.tube('paper_ticket_roll',[(x-.12,y,z),(x+.12,y,z)],[.10]*2,'linen',None,16)
            K.tube('ticket_roll_core',[(x-.125,y,z),(x+.125,y,z)],[.028]*2,'iron',None,10)
        K.casework('ticket_transaction_tray',.55,.30,.045,None,'brass').location=(center.x+.68,center.y-.16,top+.012)
        I.plate(ident,root,(0,d/2-.29,2.90),width=2.15)
    elif ident=='performance_stage':
        parts=[o for o in bpy.data.objects if o.name.startswith(('curtain_fold','continuous_pleated_stage_curtain','continuous_stage_proscenium'))];A.erase(parts)
        for side in [-1,1]:
            x=side*w*.34;left=x-.78;right=x+.78;y=d/2-.34;bottom=.40;top=h-.22;v=[]
            for z in [bottom,top]:
                for i in range(33):v.append((left+(right-left)*i/32,y-.115*math.cos(i*math.pi/2),z))
            curtain=K.mesh('continuous_pleated_stage_curtain',v,[(i,i+1,i+34,i+33)for i in range(32)],'cloth');curtain.data.materials[0].use_backface_culling=False
        K.tube('continuous_stage_proscenium',[(x,-.34+d/2,h-.30+.10*math.sin((x/w+.5)*math.pi))for x in [-w/2+.30+i*(w-.60)/32 for i in range(33)]],[.085]*33,'brass',None,8)
    elif ident=='mirror_workbay':
        for o in [v for v in bpy.data.objects if v.name.startswith('glazing_A_frame_rack')]:A.erase(A.descendants(o))
        A.erase([o for o in bpy.data.objects if o.name.startswith(('glass_cutting_felt_mat','glass_cutting_straightedge'))])
        rack=F.glass_rack(None,(-w*.34,d/2-1.05,0));rack.rotation_euler.z=.10
        # Glass-cutting felt surface on the existing bench, not an unrelated box.
        table=next(o for o in bpy.data.objects if o.name=='mirror_workbay_meeting_table');bpy.context.view_layer.update();pts=[o.matrix_world@Vector(v)for o in table.children_recursive if o.type=='MESH'for v in o.bound_box];top=max(v.z for v in pts);c=table.matrix_world.translation
        K.rounded_solid('glass_cutting_felt_mat',1.85,.75,.012,'cloth',None,.015,(c.x,c.y,top+.008))
        K.tube('glass_cutting_straightedge',[(c.x-.72,c.y,top+.03),(c.x+.72,c.y+.1,top+.03)],[.012]*2,'brass',None,6)
    elif ident=='supply_store':
        A.erase([o for o in bpy.data.objects if o.name.startswith('book_row_with_varied_heights')])
    else:
        bpy.context.view_layer.update();old=[o for o in bpy.data.objects if o.name.startswith('ordinary_tool')];poses=[(o.name,o.matrix_world.translation.copy())for o in old];A.erase(old)
        for i,(name,position)in enumerate(poses):
            tool=K.root(name);tool.location=position
            if i%3==0:
                outline=[(-.035,-.24),(.035,-.24),(.035,.09),(.105,.18),(.09,.27),(.035,.20),(-.035,.20),(-.09,.27),(-.105,.18),(-.035,.09)]
                F.prism('forged_open_jaw_spanner',outline,.035,'brass',tool)
            elif i%3==1:
                K.tube('turned_hammer_handle',[(0,0,-.24),(0,0,.17)],[.027,.021],'wood',tool,8);K.soft_body('forged_hammer_head',.22,.07,.09,'brass',tool,(0,0,.19))
            else:
                K.soft_body('shaped_driver_grip',.09,.07,.20,'wood',tool,(0,0,.12));K.tube('driver_shaft',[(0,0,.03),(0,0,-.24)],[.012,.009],'brass',tool,6)
    A.freeze(list(bpy.data.objects));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'sources'/(ident+'.blend')),compress=True)
    new=A.export(list(bpy.data.objects),Path(row['file']).name,row['runtime'],{k:v for k,v in row.items()if k not in ['file','runtime','triangles','meshParts','rawBytes']});manifest['assets']=[new if a['runtime']==new['runtime']else a for a in manifest['assets']];changed.append(ident)
p.write_text(json.dumps(manifest,indent=2)+'\n');print('FUNCTION_FORMS_REFINED',changed)
