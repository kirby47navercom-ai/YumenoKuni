import {sourceRows,sourceSvg} from './v3-source-svg.mjs';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const source=await fs.readFile(new URL('../Source/SpotLayoutV4.hpp',import.meta.url),'utf8'),match=/Rect\{\{([\d.f,\s]+)\}\}/.exec(source);
if(!match)throw Error('Review the shared spot rectangle declaration');
export const SPOT_RECT=match[1].split(',').map(v=>Number(v.trim().replace(/f$/,'')));
if(SPOT_RECT.length!==4||SPOT_RECT.some(v=>!Number.isFinite(v)))throw Error('Invalid shared spot rectangle');
// Official V3 manual p15: green axes with a centered diamond reticle.
// Original spot cursor/axis raster and display-list transform.
export async function emitSpotVisuals({write}){
 const repo=fileURLToPath(new URL('../../',import.meta.url));
 const {loadImage}=createRequire(path.join(repo,'../engineCreate/package.json'))('@napi-rs/canvas');
 const {tasks}=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8'));
 const aspects={};
 for(const [id,task] of Object.entries(tasks)){
  if(task.stage.kind!=='spot')continue;
  const image=await loadImage(path.join(repo,task.stage.image));
  aspects[id]=image.width/image.height;
 }
 await write('Assets/Data/v4_story/spot_image_aspects.json',aspects);
 const bytes=await fs.readFile(new URL('../../ui/v4/v3_reference/spot_title_ko.png',import.meta.url));
 if(createHash('sha256').update(bytes).digest('hex')!=='3f5e2fa7fdfc6e00d359b5b8357bbd19ee7e8723bd7f30a959ade3786b63f0c3')throw Error('Changed reviewed Korean spot title');
 await write('Assets/Art/ui/v3/spot/spot_title_ko.png',bytes);
 const backdrop=(await sourceRows('t_sub_spot_bg')).filter(r=>r.path!=='p_scr_img/1');
 await write('Assets/Art/ui/spot_frame.svg',await sourceSvg(backdrop));
 const rows=await sourceRows('t_sub_spot_cursor');
 await write('Assets/Art/ui/spot_reticle.svg',await sourceSvg(rows.filter(r=>!r.path.includes('cursor_line')),{bounds:[-30,-30,60,60]}));
 const line=rows.find(r=>r.path.includes('cursor_line_001'));
 if(!line?.texture)throw Error('Missing original spot axis');
 const png=await fs.readFile(new URL('../../'+line.texture,import.meta.url));
 await write('Assets/Art/ui/spot_axis.png',png);
 const bank=JSON.parse(await fs.readFile(new URL('../../ui/v3_authorized/trial_inputs/layout.json',import.meta.url),'utf8'));
 const question=bank.t_sub_mondai.frames[bank.t_sub_mondai.labels.fl_open_wait-1].filter(r=>r.resource==='t_sub_mondai_pl_000.png');
 if(question.length!==1)throw Error('Missing source question panel');
 await write('Assets/Art/ui/sub_question_source.svg',await sourceSvg(question,{bounds:question[0].rect}));

}
export function applySpotStage(widget){
 const image=widget.nodes.find(n=>n.id==='SpotImg');if(!image)throw Error('Missing spot image');
 // The runtime fits the original image inside this aperture and maps the
 // authored polygons to that same image rectangle.
 image.properties.imageFit='fill';
 image.slot.offset=[...SPOT_RECT];
 const frame=widget.nodes.find(n=>n.id==='SpotFrame');frame.slot.offset=[0,0,1280,720];
 widget.nodes=widget.nodes.filter(n=>n.id!=='SpotFrame');widget.nodes.splice(widget.nodes.findIndex(n=>n.id==='SpotImg'),0,frame);
 const band=widget.nodes.find(n=>n.id==='QBand'),question=widget.nodes.find(n=>n.id==='QText');
 band.type='Image';band.slot.offset=[.333333,541.333333,836.75,105];band.slot.zIndex=80;
 Object.assign(band.properties,{texture:'Assets/Art/ui/sub_question_source.svg',imageFit:'fill',background:'#00000000'});
 question.slot.offset=[25,552,790,82];question.slot.zIndex=81;
 Object.assign(question.properties,{fontSize:26,color:'#ffffff',wrap:true,padding:0});
 const horizontal=widget.nodes.find(n=>n.id==='CrossH'),vertical=widget.nodes.find(n=>n.id==='CrossV');
 for(const n of [horizontal,vertical]){n.type='Image';n.properties.texture='Assets/Art/ui/spot_axis.png';n.properties.imageFit='fill';n.properties.background='#00000000';}
 horizontal.slot.offset=[SPOT_RECT[0],SPOT_RECT[1]+SPOT_RECT[3]/2,SPOT_RECT[2],1];vertical.slot.offset=[SPOT_RECT[0]+SPOT_RECT[2]/2,SPOT_RECT[1],1,SPOT_RECT[3]];
 const title=widget.nodes.find(n=>n.id==='SpotTitle');if(!title)throw Error('Missing spot title');
 title.slot.offset=[124,-3.333333,341.333333,170.666667];title.slot.zIndex=10;
 title.properties.texture='Assets/Art/ui/v3/spot/spot_title_ko.png';title.properties.imageFit='fill';
 return widget;
}
