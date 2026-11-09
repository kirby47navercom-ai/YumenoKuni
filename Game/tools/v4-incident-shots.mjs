// Discovery CG ownership is an explicit story event, never a victim-name scan.
// Keep the selected image through the first authored reaction; do not grant
// evidence, show the killer, or retain the image over an interactive hub.
const incidents = new Map([
 ['11a3','incident_c1'], ['12a7','incident_c2'],
 ['13a12','incident_c3a'], ['13b2','incident_c3b'],
 ['14a13','incident_c4'], ['15a11','incident_c5'],
]);

export function incidentShots(graphs, selected) {
 const byNode=new Map(),events=[],seen=new Set();
 for(const [file,graph] of Object.entries(graphs)){
  if(!file.startsWith('chapters/'))continue;
  const nodes=graph.nodes;
  for(const node of Object.values(nodes)){
   if(!node.presentation?.actions?.includes('body_reveal'))continue;
   const prefix=node.source?.file?.split('_')[0],logical=incidents.get(prefix);
   if(!logical||seen.has(logical))throw Error('Unreviewed or duplicate discovery event: '+node.id);
   const art=selected.overrides?.[logical];
   if(!art?.delivery)throw Error('Selected incident art missing: '+logical);
   const image=art.delivery.replaceAll('\\','/');
   if(!image.startsWith('art/cg_v4/delivery/'))throw Error('Incident image must use the selected delivery: '+logical);
   const chain=[],visited=new Set();let at=node,held=false;
   while(at&&!visited.has(at.id)){
    visited.add(at.id);
    if(!['stage','say'].includes(at.type)||at.showRecord||at.source?.file!==node.source.file)break;
    chain.push(at.id);
    if(at.type==='say'){held=true;break;}
    at=nodes[at.next];
   }
   if(!held)throw Error('Discovery lacks a held authored reaction before interaction: '+node.id);
   const shot={image,perspective:'current-observation',incident:logical,knowledgeGrant:false};
   for(const id of chain){
    if(byNode.has(id))throw Error('Overlapping incident shot: '+id);
    byNode.set(id,shot);
   }
   seen.add(logical);events.push({logical,event:node.id,heldReaction:chain.at(-1),nodes:chain,image});
  }
 }
 for(const logical of incidents.values())if(!seen.has(logical))throw Error('Authored discovery event missing: '+logical);
 return {byNode,events};
}
