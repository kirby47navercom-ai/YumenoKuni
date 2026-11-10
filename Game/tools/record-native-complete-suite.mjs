// Sequential recordings in the one retained QA package; each task completes
// through actual inputs. A failed item stops here for inspection, not acceptance.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=path.resolve(import.meta.dirname,'..'),arg=p=>process.argv.find(x=>x.startsWith(p))?.slice(p.length);
const module=arg('--game-module=');assert(module,'Identify the frozen full game module');
const modulePath=path.resolve(root,module);assert(modulePath.startsWith(path.join(root,'Saved')+path.sep));
const moduleSHA256=createHash('sha256').update(await fs.readFile(modulePath)).digest('hex');
const packageRoot=path.join(root,'Saved/native-panic-views-1793690486425/package'),packageManifest=JSON.parse(await fs.readFile(path.join(packageRoot,'game.hbpack.json'),'utf8'));
const packageExecutableSHA256=createHash('sha256').update(await fs.readFile(path.join(packageRoot,packageManifest.windowsApplication.executable))).digest('hex');
const resume=arg('--resume='),work=resume?path.resolve(root,resume):path.join(root,'Saved/complete-presentation-suite-'+Date.now());assert(work.startsWith(path.join(root,'Saved')+path.sep));await fs.mkdir(work,{recursive:true});
const cases=[
 ['T6-MM-A03','physical-statement'],['T3-NS-A11','nonstop'],['T4-PN-A03','panic'],['T4-RS-A03','showdown'],['T4-MM-A03','mine-wall'],['T4-FA-A02','anagram'],['T4-SD-01','scrum'],['T4-AA-01','armament'],['T3-MG-01','climax'],['T4-VOTE-01','vote'],['T4-PERSON-A01','person'],['T4-CULPRIT-A01','culprit'],['T4-SPOT-A01','spot'],['T6-EVIDENCE-A01','evidence'],['T4-ANSWER-A01','choice'],['T4-RL-A02','reasoning'],['T3-LIE-01','lie'],
];
const only=arg('--only=')?.split(',');if(only){assert(only.length&&only.every(id=>cases.some(c=>c[0]===id)));cases.sort((a,b)=>{const x=only.indexOf(a[0]),y=only.indexOf(b[0]);return(x<0?999:x)-(y<0?999:y);});}
const file=path.join(work,'report.json'),report=await fs.readFile(file,'utf8').then(JSON.parse,e=>{if(e.code==='ENOENT')return {moduleSHA256,cases,results:[],accepted:false,scope:'Complete representative task sequences, not every chapter/branch or whole-game acceptance. Direct visual review required before video delivery.'};throw e;});assert.equal(report.moduleSHA256,moduleSHA256);
if(report.packageExecutableSHA256)assert.equal(report.packageExecutableSHA256,packageExecutableSHA256,'Runtime executable changed; start a separately identified suite');report.packageExecutableSHA256=packageExecutableSHA256;
const save=()=>fs.writeFile(file,JSON.stringify(report,null,2));
for(const [taskId,label]of cases){
 if(only&&!only.includes(taskId))continue;
 if(report.results.some(r=>r.taskId===taskId&&r.sequenceCompleted))continue;
 report.active={taskId,label};await save();
 const args=[path.join(root,'tools/record-native-complete-task.mjs'),'--task='+taskId,'--seconds=240','--game-module='+module,...(label==='mine-wall'?['--mine-wall=1']:[])];
 const child=spawn(process.execPath,args,{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});let log='';child.stdout.on('data',b=>log+=b);child.stderr.on('data',b=>log+=b);
 const code=await new Promise((resolve,reject)=>{child.once('error',reject);child.once('close',resolve);});await fs.writeFile(path.join(work,label+'.log'),log);
 let result;for(const line of log.trim().split(/\r?\n/)){try{const x=JSON.parse(line);if(x.taskId===taskId&&x.work)result=x;}catch{}}
 if(code!==0||!result?.sequenceCompleted){report.failure={taskId,label,code,log:path.join(work,label+'.log')};await save();throw Error('Incomplete native recording: '+taskId+'; inspect '+report.failure.log);}
 const taskReport=JSON.parse(await fs.readFile(path.join(result.work,'report.json'),'utf8'));assert(taskReport.movie?.audioPeak>0);assert(taskReport.movie.streams.some(s=>s.type==='video')&&taskReport.movie.streams.some(s=>s.type==='audio'));
 report.results.push({taskId,label,work:result.work,sequenceCompleted:true,accepted:false,duration:taskReport.movie.duration,movie:taskReport.movie.movie});delete report.failure;await save();console.log(JSON.stringify({taskId,label,duration:taskReport.movie.duration,work:result.work}));
}
delete report.active;report.requestedPassComplete=true;report.recordingPassComplete=cases.every(([id])=>report.results.some(r=>r.taskId===id&&r.sequenceCompleted));await save();console.log(JSON.stringify({work,representativeSequences:report.results.length,accepted:false}));
