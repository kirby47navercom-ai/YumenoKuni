// create-project.mjs: after const repo=... and helpers copy/write have been declared:
execFileSync('python',['-X','utf8',path.join(repo,'tools/build_v4_exploration.py')],{stdio:'inherit'});
const exploreWorldRoot='art/space_v4/runtime_v1';
const exploreCopy=JSON.parse(await fs.readFile(path.join(repo,exploreWorldRoot,'copy_manifest.json'),'utf8'));
for(const c of exploreCopy)await copy(c.from,c.to);
await copy(exploreWorldRoot+'/world.json','Assets/Data/explore_world.json');

// create-project.mjs: after const scene=... and const model=..., before final write(scene):
const exploreGeometry=model('ExploreGeometry','',[300,0,0]);
exploreGeometry.components[0].properties.visible=false;
scene.objects.push(exploreGeometry);
for(let i=0;i<16;i++){
 const person=sprite('ExplorePerson'+i,'Assets/Art/figure/rin.webp',[300,.9,0],.83,1.8,{visible:false,billboard:true,blendMode:'masked',alphaCutoff:.08,castShadow:false});
 scene.objects.push(person);
}

// W_Explore before write: retain existing IDs/node count, do not add new Main nodes.
// MapImg properties.imageFit='contain' (atlas must not crop).
// Mini properties.imageFit='fill', slot.offset=[1080,500,180,180].
// Spark0..9 properties.opacity=.7 (currently .0).
// ExHint slot.offset=[24,676,1080,30], properties.fontSize=16.
// Same approved figure textures remain Assets/Art/figure/<slug>.webp.

// Yumeno.h: #include "ExploreWorld.hpp"; private: exworld::State world;
// Stats(): s["world"]=exworld::stats(world); (small payload)
// saveFlow JSON: {"world",exworld::save(world)}
// loadFlow before restored enterRoom: exworld::load(world); if(s.contains("world"))exworld::restore(world,s["world"]);
// newGame: world.history.clear(); world.id.clear(); world.active=false;
// Do not count unlocated target entries as verified forensic geometry.
