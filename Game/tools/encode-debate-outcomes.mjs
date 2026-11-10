// Actual compositor captures only. Omit the opening claim from public previews.
import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
const work=path.resolve(process.argv[2]),combined=['ffconcat version 1.0'],summary=[];
const quote=p=>p.replaceAll('\\','/').replaceAll("'","'\\''");
const encode=(input,output)=>execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-safe','0','-i',input,'-filter_complex','fps=50,scale=768:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3','-loop','0','-y',output],{stdio:'inherit'});
for(const kind of ['refute','lie','agree']){
 const folder=path.join(work,'media',kind),record=JSON.parse(await fs.readFile(path.join(folder,'capture.json'),'utf8'));
 const frames=record.frames.filter(f=>f.elapsed>=1.20&&f.elapsed<5.25);assert(frames.length>40);
 const lines=['ffconcat version 1.0'];let seconds=0;
 for(let i=0;i<frames.length;i++){
  const duration=Math.max(.001,(frames[i+1]?.elapsed??Math.min(5.25,frames[i].elapsed+1/60))-frames[i].elapsed);
  const row=[`file '${quote(path.join(folder,frames[i].file))}'`,`duration ${duration.toFixed(6)}`];lines.push(...row);combined.push(...row);seconds+=duration;
 }
 lines.push(`file '${quote(path.join(folder,frames.at(-1).file))}'`);
 const concat=path.join(work,`${kind}-preview.ffconcat`),gif=path.join(work,`${kind}-runtime.gif`);await fs.writeFile(concat,lines.join('\n')+'\n');encode(concat,gif);
 summary.push({kind,actual_frames:frames.length,seconds,measured_capture_fps:(frames.length-1)/(frames.at(-1).elapsed-frames[0].elapsed),gif});
}
const concat=path.join(work,'three-outcomes.ffconcat'),gif=path.join(work,'three-outcomes-reference-runtime.gif');await fs.writeFile(concat,combined.join('\n')+'\n');encode(concat,gif);
await fs.writeFile(path.join(work,'media/preview-summary.json'),JSON.stringify({source:'Actual own-game compositor frames; 1.20..5.25seconds of each result, retaining the complete cutin entrance but no opening testimony/claim or following dialogue.50FPS output resamples/holds captured frames; no invented motion interpolation and not a gameplay FPS measurement.',outcomes:summary,combined:gif},null,2)+'\n');console.log(JSON.stringify({gif,outcomes:summary.map(({kind,actual_frames,seconds})=>({kind,actual_frames,seconds}))}));
