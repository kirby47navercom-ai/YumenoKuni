import fs from'node:fs/promises';import path from'node:path';
export function applyTrialDialogueResponsive(widget){
 const by=id=>widget.nodes.find(n=>n.id===id);
 for(const id of ['DialogFrame','DialogueOrnament']){
  const original=by(id);for(const [part,anchors,offset]of [['Middle',[0,0,1,0],[340,0,280,720]],['Right',[1,0,1,0],[-280,0,280,720]]]){
   let node=by(id+part);if(!node){node=structuredClone(original);node.id=node.name=id+part;widget.nodes.splice(widget.nodes.indexOf(original)+1,0,node);}
   node.slot.anchors=anchors;node.slot.offset=offset;node.properties.visible=false;
  }
 }
 by('Body').slot.anchors=[.5,1,.5,1];by('Next').slot.anchors=[1,1,1,1];
 return widget;
}
export async function emitV3TrialDialogue({repo,write,layout,speakers}){
 const directory=path.join(repo,'ui/v4/trial_dialogue_source'),source=JSON.parse(await fs.readFile(path.join(directory,'layout.json'),'utf8')),prefix='Assets/Art/ui/v3/dialogue/source/';
 for(const name of await fs.readdir(directory))if(name.endsWith('.png'))await write(prefix+name,await fs.readFile(path.join(directory,name)));
 const trial=layout.trial;trial.body=[320,610,740,100];trial.name=[69.334635,412.001302,170.664062,170.664062];trial.icon=source.tiles.portrait.rect;trial.iconAssets={};
 for(const slug of 'mio rin ken nana taiga ai rei sora haruka sho koto akari riku satsuki yuu kaede lappy'.split(' '))trial.iconAssets[slug]=prefix+'portrait_'+slug+'.png';
 trial.nameAssets={};for(const speaker of speakers){const base=speaker.split('(')[0].trim(),name=source.tiles.names[speaker]||source.tiles.names[base];trial.nameAssets[speaker]=name?prefix+name.file:layout.nameAssets[speaker];}
 for(const[short,row]of Object.entries(source.tiles.names))trial.nameAssets[short]=prefix+row.file;
 trial.next=source.tiles.next.rect;trial.autoRect=source.tiles.auto.rect;trial.nextAsset=prefix+'next.png';trial.autoAsset=prefix+'auto.png';trial.bodyAsset=prefix+'body.png';trial.bodyPlainAsset=prefix+'body_plain.png';trial.framePlainAsset=prefix+'frame_plain.png';trial.frameAssets=Object.fromEntries(Array.from({length:6},(_,i)=>[String(i+1),prefix+'frame'+(i+1)+'.png']));
 trial.sourceRasters=true;trial.frameLineCount=0;trial.portraitInkScope=source.tiles.portrait.scope;trial.portraitProjection=source.tiles.portrait.referenceQuad512;
 trial.scope='User20261106 original trial frame/body/next rasters and provided blue-frame reference; own full family/personal name ink and own character projected portrait. Text region calibrated to supplied reference, preserving bounded pages. Original character artwork not used.';
 await write('Assets/Data/v4_story/dialogue_layout.json',layout);return layout;
}
