// Focused shipping regressions after an independently proven UI-only delta.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
const exec=promisify(execFile),root=path.resolve(import.meta.dirname,'..'),saved=path.join(root,'Saved'),build=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8')),plan=JSON.parse(await fs.readFile(path.join(saved,'native-ui-focused-plan-20261102.json'),'utf8'));
const resume=process.argv.find(a=>a.startsWith('--resume='))?.slice(9),work=resume?path.resolve(resume):path.join(saved,'native-ui-focused-'+Date.now());await fs.mkdir(work,{recursive:true});
const reportFile=path.join(work,'report.json'),report=await fs.readFile(reportFile,'utf8').then(JSON.parse,()=>({build:build.id,work,results:{},ok:false}));
if(report.build!==build.id){const evidence=process.argv.find(a=>a.startsWith('--inherit-ui-only='))?.slice(18);assert(evidence,'Changed builds need an explicit reviewed UI/binary-only inheritance proof');const file=path.resolve(evidence),delta=JSON.parse(await fs.readFile(file,'utf8'));assert(delta.ok&&delta.build===build.id&&delta.baselineBuild===report.build&&delta.allOtherPackageBytesExact&&delta.uiStateRasterKeyboardAndMouseButtonCodeUnchanged&&delta.sourceOnlyRestoresApprovedColdBranches);await fs.copyFile(reportFile,path.join(work,'report-before-'+report.build+'.json'));for(const row of Object.values(report.results))if(row.ok){row.validatedBuild=report.build;row.inheritedThrough=file;}report.previousBuild=report.build;report.build=build.id;report.inheritanceProof=file;}
await fs.writeFile(path.join(saved,'native-ui-focused-latest.json'),JSON.stringify({build:build.id,work},null,2));
const runs=async prefix=>(await fs.readdir(saved,{withFileTypes:true})).filter(e=>e.isDirectory()&&e.name.startsWith(prefix)).map(e=>e.name);
const cases=[['tasks','verify-native-all-tasks.mjs','native-all-tasks-',['--only='+plan.taskIds.join(',')]],['transformed','verify-native-all-tasks.mjs','native-all-tasks-',['--only='+plan.transformedTask,'--judgment=lie']],['menus','verify-native-choice-branches.mjs','native-all-choices-',['--only='+plan.choiceKeys.join(',')]],['canonical','verify-native-all-tasks.mjs','native-all-tasks-',['--only=T3-NS-A11']],['scrollResize','verify-native-scroll-live.mjs','native-scroll-live-',['--resize']],['endings','verify-native-ending-replay.mjs','native-ending-replay-',[]]];
for(const [key,script,prefix,args]of cases){
 if(report.results[key]?.ok)continue;
 const before=new Set(await runs(prefix));report.active=key;await fs.writeFile(reportFile,JSON.stringify(report,null,2));console.log(JSON.stringify({component:key,status:'running',work}));
 try{const result=await exec(process.execPath,[path.join(import.meta.dirname,script),...args],{cwd:root,windowsHide:true,timeout:1800000,maxBuffer:8388608});await fs.writeFile(path.join(work,key+'.stdout.txt'),result.stdout);await fs.writeFile(path.join(work,key+'.stderr.txt'),result.stderr);
  const added=(await runs(prefix)).filter(n=>!before.has(n));assert.equal(added.length,1);const proof=path.join(saved,added[0],'report.json'),row=JSON.parse(await fs.readFile(proof,'utf8'));assert(row.ok);assert.equal(row.build,build.id);report.results[key]={ok:true,report:proof};console.log(JSON.stringify({component:key,status:'passed',report:proof}));
 }catch(error){report.results[key]={ok:false,error:error.stack};if(error.stdout)await fs.writeFile(path.join(work,key+'.stdout.txt'),error.stdout);if(error.stderr)await fs.writeFile(path.join(work,key+'.stderr.txt'),error.stderr);await fs.writeFile(reportFile,JSON.stringify(report,null,2));throw error;}
 await fs.writeFile(reportFile,JSON.stringify(report,null,2));
}
report.ok=true;delete report.active;report.scope='Current shipping runtime,15 UI task families, one additional transformed route, ten menus across six chapters including13-row pagination, actual long text wheel/drag and three owned-window resizes, two actual ending restores/repeated paid-result checks. Original219/779/five branches remain attributed to their original build and the verified UI-only delta.';await fs.writeFile(reportFile,JSON.stringify(report,null,2));console.log(JSON.stringify({ok:true,work}));
