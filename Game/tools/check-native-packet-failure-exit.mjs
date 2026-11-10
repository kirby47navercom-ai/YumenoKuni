import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {createOwnedNativePackage} from './native-owned-package.mjs';
const root=path.resolve(import.meta.dirname,'..'),build=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8')),work=path.join(root,'Saved/native-packet-exit-'+Date.now()),exec=promisify(execFile);await fs.mkdir(work,{recursive:true});const runner=path.join(work,'fault-runner.mjs');await fs.writeFile(runner,"process.stdout.write('x'.repeat(128*1024*1024+1024));\n");const rows=[];
const shipping=process.argv.includes('--shipping');
for(const[label,playerCandidate,expected]of shipping?[['shipping-fixed',undefined,1]]:[['shipping-baseline',undefined,0],['owned-failure-fix',process.argv[2],1]]){
 const directory=path.join(work,label);await fs.mkdir(directory);const prepared=await createOwnedNativePackage({source:build.output,work:directory,runnerCandidate:runner,playerCandidate}),env={...process.env,HB_NATIVE_TEST_STATE:path.join(directory,'State'),NODE_OPTIONS:''};delete env.YUMENO_NATIVE_QA_DIR;const child=spawn(prepared.executable,['--hidden'],{cwd:directory,env,windowsHide:true,stdio:'ignore'});let ended=false;const timer=setTimeout(()=>{if(!ended)void exec('taskkill.exe',['/PID',String(child.pid),'/T','/F'],{windowsHide:true}).catch(()=>{});},30000);
 try{const code=await new Promise((resolve,reject)=>{child.once('error',reject);child.once('close',code=>{ended=true;resolve(code);});});assert.equal(code,expected,label);const log=await fs.readFile(path.join(directory,'State/native-runtime.log'),'utf8');assert(log.includes('Native runtime packet budget exceeded'));rows.push({label,code,expected,packetBudgetExceptionLogged:true});}finally{clearTimeout(timer);if(!ended)await exec('taskkill.exe',['/PID',String(child.pid),'/T','/F'],{windowsHide:true}).catch(()=>{});}
}
await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,work,build:build.id,shippingEngine:shipping,rows,engineOriginalOrDistModified:false,scope:'Actual hidden Win32 native host protocol fault injection above the128MiB line cap. In shipping mode the actual packaged executable must exit1. Earlier candidate mode compares old exit0 to candidate exit1. No gameplay, save mutation, original V3, successful title or campaign claim.'},null,2));console.log(JSON.stringify({ok:true,work,rows}));
