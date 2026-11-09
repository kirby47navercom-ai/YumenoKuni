"""Shared authored tiered dry-fountain geometry for prop, room and exterior instances."""
import math
def add_tiers(bpy,root):
    if root.get('tiered_dry_fountain_art_v1'):return
    scene=bpy.context.scene
    def lathe(name,profile,material):
        n=64;verts=[(r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n),z) for r,z in profile for i in range(n)]
        faces=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(profile)-1) for i in range(n)]
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();uv=mesh.uv_layers.new(name='UVMap')
        for p in mesh.polygons:
            for li in p.loop_indices:
                v=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(math.atan2(v.y,v.x)/math.tau,v.z/2)
        o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o);o.parent=root;o.hide_render=root.hide_render;o.data.materials.append(bpy.data.materials['yk_'+material]);return o
    lathe('tiered_center_column',[(0,.25),(.38,.25),(.42,.5),(.22,.65),(.18,1.3),(.2,1.4),(.13,2.05),(.16,2.15),(.09,2.75),(0,2.75)],'ivory')
    for z,r in [(.86,1.24),(1.69,.84),(2.34,.48)]:
        lathe('empty_stone_tier',[(0,z-.16),(.25*r,z-.16),(.42*r,z-.12),(.73*r,z-.04),(r,z+.09),(r,z+.17),(.93*r,z+.18),(.88*r,z+.10),(.68*r,z+.01),(.38*r,z-.06),(0,z-.06)],'paper')
        lathe('tier_ink_rim',[(r+.012,z+.09),(r+.012,z+.115),(r-.005,z+.115),(r-.005,z+.09),(r+.012,z+.09)],'ink')
        lathe('tier_brass_band',[(r*.5,z-.13),(r*.5,z-.10),(r*.49,z-.10),(r*.49,z-.13),(r*.5,z-.13)],'gold')
    lathe('dry_finial',[(0,2.72),(.14,2.72),(.21,2.86),(.13,3.03),(0,3.21)],'ivory')
    lathe('top_dry_nozzle',[(0,3.03),(.035,3.03),(.035,3.24),(0,3.24)],'gold')
    root['tiered_dry_fountain_art_v1']=True;root['water_enabled']=False;root['audio_source']='separate speaker; no running water mesh'
