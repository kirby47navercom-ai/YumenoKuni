// Read-only diagnostics for the owned native test process.
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import readline from 'node:readline';
import {createRequire} from 'node:module';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {writeFileSync,appendFileSync,existsSync,renameSync} from 'node:fs';
import {startRecordingAudio,stopRecordingAudio} from './native-recording-audio.mjs';
const directory=process.env.YUMENO_NATIVE_QA_DIR;
// Publish complete diagnostic snapshots. A short cloud-sync lock may leave the
// previous snapshot available, but persistent I/O failure must still fail QA.
const snapshotFailures=new Map();
function publishSnapshot(name,value){
 const target=path.join(directory,name),next=target+'.qa-next';
 try{
  writeFileSync(next,JSON.stringify(value));renameSync(next,target);
  if(snapshotFailures.delete(name))process.stderr.write(`[QA snapshot recovered] ${name}\n`);
 }catch(error){
  if(!['UNKNOWN','EBUSY','EPERM','EACCES'].includes(error.code))throw error;
  const since=snapshotFailures.get(name)??Date.now();
  if(!snapshotFailures.has(name))process.stderr.write(`[QA snapshot temporarily locked] ${name}: ${error.code}\n`);
  snapshotFailures.set(name,since);
  if(Date.now()-since>2000)throw error;
 }
}
if(directory&&process.argv[1]?.replaceAll('\\','/').endsWith('/tools/native-game-runner.mjs')){
 if(process.env.YUMENO_NATIVE_WIRE_TRACE==='1'){
  const {NativeHost}=await import(pathToFileURL(path.join(path.dirname(process.argv[1]),'native-host.mjs')));
  const validate=NativeHost.prototype.validateReply;let largestStats=0;
  NativeHost.prototype.validateReply=function(session,request,result,...rest){try{if(request.nativeId==='Yumeno.Stats'&&typeof result.outputs?.result==='string'&&result.outputs.result.length>largestStats){largestStats=result.outputs.result.length;publishSnapshot('wire-budget.json',{nativeId:request.nativeId,maximumUTF16:largestStats,limit:4096});}return validate.call(this,session,request,result,...rest);}catch(error){appendFileSync(path.join(directory,'wire-failure.jsonl'),JSON.stringify({message:error.message,request,result})+'\n');throw error;}};
 }
 const ActualAggregateError=globalThis.AggregateError;
 globalThis.AggregateError=class extends ActualAggregateError{constructor(errors,...args){const rows=[...errors];super(rows,...args);appendFileSync(path.join(directory,'aggregate-errors.jsonl'),JSON.stringify({message:this.message,errors:rows.map(e=>({message:e?.message,stack:e?.stack}))})+'\n');}};
 process.on("uncaughtExceptionMonitor",error=>{const encode=e=>({message:e?.message,stack:e?.stack,errors:e?.errors?.map(encode),cause:e?.cause?encode(e.cause):undefined});writeFileSync(path.join(directory,"uncaught-runtime-error.json"),JSON.stringify(encode(error),null,2));});
 if(process.env.YUMENO_NATIVE_CPU_PROFILE==='1'){
  const {Session}=await import('node:inspector');const inspector=new Session();inspector.connect();const call=(name,args={})=>new Promise((resolve,reject)=>inspector.post(name,args,(error,value)=>error?reject(error):resolve(value)));await call('Profiler.enable');await call('Profiler.setSamplingInterval',{interval:1000});await call('Profiler.start');await fs.writeFile(path.join(directory,'script-profile-clock.json'),JSON.stringify({wallMS:Date.now(),monotonicUS:Number(process.hrtime.bigint()/1000n),scope:'CPU sampling clock anchor only; diagnostic process, never the unprofiled FPS baseline.'}));setTimeout(async()=>{const {profile}=await call('Profiler.stop');await fs.writeFile(path.join(directory,'script.cpuprofile'),JSON.stringify(profile));inspector.disconnect();},75000).unref();
 }
 const {NativeWidgetLayer}=await import(pathToFileURL(path.join(path.dirname(process.argv[1]),'native-widget-layer.mjs')));
 if(process.env.YUMENO_NATIVE_INPUT_TRACE==='1'){const input=NativeWidgetLayer.prototype.input;NativeWidgetLayer.prototype.input=function(packet){const result=input.call(this,packet);if(packet.pointer||/mouse/.test(String(packet.key).toLowerCase()))appendFileSync(path.join(directory,'ui-input.jsonl'),JSON.stringify({time:Date.now(),packet,result,pointer:this.pointer,hits:this.scrollHits.map(h=>({id:h.node.id,max:h.max,w:h.w,h:h.h,matrix:[h.matrix.a,h.matrix.b,h.matrix.c,h.matrix.d,h.matrix.e,h.matrix.f],offset:h.view.scrollOffsets.get(h.node.id),active:h.view.options.acceptInput()}))})+'\n');return result;};}
 const require=createRequire(process.argv[1]),{createCanvas,ImageData,loadImage}=require('@napi-rs/canvas');
 if(process.env.YUMENO_NATIVE_QA_SVG_ERRORS==='1'){const {NativeSVGImage}=await import(pathToFileURL(path.join(path.dirname(process.argv[1]),'native-webp-animation.mjs'))),prepare=NativeSVGImage.prototype.prepare;NativeSVGImage.prototype.prepare=async function(width,height){try{return await prepare.call(this,width,height);}catch(error){writeFileSync(path.join(directory,'svg-failure.json'),JSON.stringify({width,height,sourceWidth:this.width,sourceHeight:this.height,source:this.bytes?.toString('utf8').slice(0,400)},null,2));throw error;}};if(process.env.YUMENO_NATIVE_QA_SVG_MAIN==='1'){const {NativeWidgetRasterWorker}=await import(pathToFileURL(path.join(path.dirname(process.argv[1]),'native-widget-raster-worker.mjs')));NativeWidgetRasterWorker.prototype.supports=()=>false;}}
 const {BlueprintRuntime}=await import(pathToFileURL(path.join(path.dirname(process.argv[1]),'../prototype/blueprint-runtime.js')));
 let qaWidgetTiming={},qaWorld=null,qaLastStats=null;
 const qaIOProfile=process.env.YUMENO_NATIVE_QA_IO_PROFILE==='1',qaIOTimings=[];
 const profileQAWrite=(kind,frame,write)=>{if(!qaIOProfile)return write();const at=performance.now();try{return write();}finally{if(qaIOTimings.length<20000)qaIOTimings.push({kind,frame,time:Date.now(),ms:performance.now()-at});}};

 if(process.env.YUMENO_NATIVE_UI_PROFILE==='1'){
  const {WidgetSystem}=await import(pathToFileURL(path.join(path.dirname(process.argv[1]),'../prototype/ui-runtime.js')));
  for(const method of ['sync','operation','writeBatch','tick']){
   const original=WidgetSystem.prototype[method];if(!original)continue;
   if(['operation','writeBatch','tick'].includes(method))WidgetSystem.prototype[method]=async function(...args){const at=performance.now();try{return await original.apply(this,args);}finally{const row=qaWidgetTiming[method]??={calls:0,ms:0};row.calls++;row.ms+=performance.now()-at;}};
   else WidgetSystem.prototype[method]=function(...args){const at=performance.now();try{return original.apply(this,args);}finally{const row=qaWidgetTiming[method]??={calls:0,ms:0};row.calls++;row.ms+=performance.now()-at;}};
  }
 }
 const tick=BlueprintRuntime.prototype.tick;let sequence=0,lastTelemetry=0;
 BlueprintRuntime.prototype.tick=async function(...args){
  if(!this.qaLog){const log=this.hooks.log;this.hooks.log=(message,...rest)=>{let value;try{value=JSON.parse(message);}catch{}if(value?.mode&&value.options&&Object.hasOwn(value,'coins')){qaLastStats=value;publishSnapshot('stats.json',{sequence:++sequence,stats:value});return;}if(value?.physical&&value.desired&&Object.hasOwn(value,'gain')){publishSnapshot('aim.json',value);return;}return log?.(message,...rest);};this.qaLog=true;}
  if(performance.now()-lastTelemetry>1000){lastTelemetry=performance.now();const row=JSON.stringify({time:Date.now(),sequence,memory:process.memoryUsage(),widgetTiming:qaWidgetTiming});profileQAWrite('telemetry',sparseFrameSequence,()=>{writeFileSync(path.join(directory,'telemetry.json'),row);appendFileSync(path.join(directory,'telemetry.jsonl'),row+'\n');});qaWidgetTiming={};}
  const result=await tick.apply(this,args);qaWorld=this;if(process.env.YUMENO_NATIVE_INPUT_TRACE==='1')publishSnapshot('input-runtime.json',{time:Date.now(),input:this.inputSnapshot?.()});return result;
 };
 const pending=new Map();let serial=1000000000,first=true,lastFrameHeartbeat=0,sparseFrameSequence=0,lastUIProfile=0,lastCaptureProbe=0;
 const qaRenderProfile=process.env.YUMENO_NATIVE_QA_RENDER_PROFILE==='1',qaRenderPackets=[],qaRenderPending=new Map();let qaRenderFields;
 if(qaRenderProfile){const originalWrite=process.stdout.write;process.stdout.write=function(chunk,...args){if(typeof chunk==='string'){const match=/^\{"channel":"hb\.render","id":(\d+),"op":"([^"]+)"/.exec(chunk);if(match){const request={op:match[2],at:performance.now(),frame:sparseFrameSequence,bytes:Buffer.byteLength(chunk)};if(request.op==='upload'&&request.bytes>1024*1024){const packet=JSON.parse(chunk),data=packet.data;request.resources=(Array.isArray(data)?data:data.resources||[]).map(v=>({kind:v.kind,id:v.id,width:v.width,height:v.height,fields:Object.keys(v),payloadSizes:Object.fromEntries(Object.entries(v).filter(([,v])=>typeof v==='string'||Array.isArray(v)).map(([k,v])=>[k,v.length]))}));}qaRenderPending.set(+match[1],request);}}return originalWrite.call(this,chunk,...args);};}
 const profiledSVG=new WeakSet(),profiledCanvases=new WeakSet();
 const lines=readline.createInterface({input:process.stdin,crlfDelay:Infinity});
 lines.on('line',line=>{try{const p=JSON.parse(line),r=pending.get(p.id);if(qaRenderProfile&&p.channel==='hb.render'){const request=qaRenderPending.get(p.id);qaRenderPending.delete(p.id);if(request&&qaRenderPackets.length<20000){const v=p.value||{};if(request.op==='frame')qaRenderFields??=Object.keys(v);qaRenderPackets.push({op:request.op,frame:request.frame,time:Date.now(),elapsedMS:performance.now()-request.at,bytes:request.bytes,resources:request.resources,...Object.fromEntries(['renderViews','renderViewBytes','presents','gpuTimingFrame','gpuTimeMs','calls','uploads','drawUpdates','meshVertexUpdates','meshVertexUpdateBytes','meshBufferBytes','textureResourceBytes','textures','meshes','poseUpdates','deformations'].filter(k=>v[k]!==undefined).map(k=>[k,v[k]]))});}}if(p.channel==='hb.platform'&&r){pending.delete(p.id);clearTimeout(r.timer);p.ok?r.resolve(p.value):r.reject(Error(p.error));}}catch{}});
 const capture=()=>new Promise((resolve,reject)=>{const id=serial++,timer=setTimeout(()=>{pending.delete(id);reject(Error('QA renderer capture timeout'));},30000);pending.set(id,{resolve,reject,timer});process.stdout.write(JSON.stringify({channel:'hb.platform',op:'capture',data:{},id})+'\n');});
 const rawStarted=performance.now();let rawCaptured=0;
 // Opt-in recording of actual native frames. Never enabled in performance QA.
 const qaRecordingEnabled=process.env.YUMENO_NATIVE_QA_RECORD==='1';
 let recording=null,lastRecordProbe=0;
 async function recordFrame(layer){
  if(!qaRecordingEnabled)return;
  const now=performance.now();
  if(!recording&&now-lastRecordProbe<100)return;
  if(!recording){
   lastRecordProbe=now;const file=path.join(directory,'record.request');
   if(!existsSync(file))return;
   const request=JSON.parse(await fs.readFile(file,'utf8'));
   if(!/^[a-z0-9_-]{1,64}$/.test(request.name)||!(request.seconds>=1&&request.seconds<=(request.stream?900:90))||!(request.fps>=4&&request.fps<=30))throw Error('Invalid native recording request');
   const output=path.join(directory,'recordings',request.name);await fs.mkdir(output,{recursive:true});
   const audio=request.audio?await startRecordingAudio(qaWorld,process.argv[1],output,request.seconds):null;
   recording={...request,output,started:performance.now(),startedUnixMS:Date.now(),last:-Infinity,frames:[],audioCapture:audio};await fs.writeFile(path.join(output,'started.json'),JSON.stringify({startedUnixMS:recording.startedUnixMS,audioOnly:!!request.audioOnly}));await fs.unlink(file);
  }
  const r=recording,frameNow=performance.now();if(frameNow-r.last<1000/r.fps)return;r.last=frameNow;
  if(r.audioOnly){
   const stop=path.join(directory,'record.stop');
   if(frameNow-r.started>=r.seconds*1000||existsSync(stop)){
    if(existsSync(stop))await fs.unlink(stop);
    const audio=r.audioCapture?await stopRecordingAudio(r.audioCapture):null;
    await fs.writeFile(path.join(r.output,'recording.json'),JSON.stringify({name:r.name,audioOnly:true,audio:!!audio,audioCapture:audio,startedUnixMS:r.startedUnixMS,endedUnixMS:Date.now(),scope:'Actual game mixer PCM; video captured separately from the exact owned player window. No GPU JSON readback.'},null,2));recording=null;
   }
   return;
  }
  let surface=layer.canvas;
  if(layer.raster?.active){const bitmap=await layer.raster.capture();surface=createCanvas(bitmap.width,bitmap.height);surface.getContext('2d').drawImage(await loadImage(Buffer.from(bitmap.png)),0,0);}
  if(!surface)return;
  const frame=createCanvas(surface.width,surface.height),ctx=frame.getContext('2d');
  // An entirely opaque native UI already is the final picture. Reading the
  // occluded GPU world through a multi-megabyte JSON packet stalls recording.
  // Test every alpha byte; transparent gameplay still captures its real world.
  const pixels=surface.getContext('2d').getImageData(0,0,surface.width,surface.height).data;
  let opaque=true;for(let i=3;i<pixels.length;i+=4)if(pixels[i]!==255){opaque=false;break;}
  if(!opaque){const result=await capture();if(!result?.rgba)throw Error('Native video frame omitted pixels');ctx.putImageData(new ImageData(new Uint8ClampedArray(result.rgba),frame.width,frame.height),0,0);}
  ctx.drawImage(surface,0,0);
  const name='frame-'+String(r.frames.length).padStart(5,'0')+'.jpg',jpeg=frame.toBuffer('image/jpeg',88);
  if(r.stream){
   if(!r.encoder){
    r.video=path.join(r.output,'continuous.mp4');
    r.encoder=spawn('ffmpeg',['-hide_banner','-loglevel','error','-y','-use_wallclock_as_timestamps','1','-f','image2pipe','-framerate',String(r.fps),'-i','pipe:0','-fps_mode','vfr','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart','-an',r.video],{windowsHide:true,stdio:['pipe','ignore','pipe']});
    r.encoderError='';r.encoder.stderr.on('data',chunk=>{r.encoderError+=chunk;});r.encoderDone=once(r.encoder,'close');r.encoder.stdin.on('error',()=>{});
   }
   if(!r.encoder.stdin.write(jpeg))await once(r.encoder.stdin,'drain');
  }else await fs.writeFile(path.join(r.output,name),jpeg);
  r.frames.push({file:name,elapsed:(frameNow-r.started)/1000,sequence,width:frame.width,height:frame.height,worldReadback:!opaque,mode:qaLastStats?.mode,node:qaLastStats?.node,flashes:[...(layer.flashes||[])].map(f=>({color:f.color,alpha:f.alpha})),shake:qaWorld?.objects.find(o=>o.id==='Camera')?.cameraShake});
  const stop=path.join(directory,'record.stop');
  if(frameNow-r.started>=r.seconds*1000||existsSync(stop)){
   if(existsSync(stop))await fs.unlink(stop);
   if(r.stream){r.encoder.stdin.end();const [code]=await r.encoderDone;if(code!==0)throw Error('Native movie encoder: '+r.encoderError);}
   const audio=r.audioCapture?await stopRecordingAudio(r.audioCapture):null;
   await fs.writeFile(path.join(r.output,'recording.json'),JSON.stringify({name:r.name,requestedFPS:r.fps,requestedSeconds:r.seconds,frames:r.frames,video:r.video,stream:!!r.stream,audio:!!audio,audioCapture:audio,videoStarted:r.started,scope:'Actual sequential Win32/D3D11 + native UI frames and optional actual game mixer PCM. Capture timestamps retain recording cadence; capture overhead is not gameplay performance evidence.'},null,2));recording=null;
  }
 }
 const frameTrace=process.env.YUMENO_NATIVE_FRAME_TRACE==='1'?[]:null;
 if(frameTrace)process.on('exit',()=>writeFileSync(path.join(directory,'frame-cadence.json'),JSON.stringify({scope:'Diagnostic UI draw cadence, not GPU present latency',samples:frameTrace})));
 const original=NativeWidgetLayer.prototype.draw;
 NativeWidgetLayer.prototype.draw=async function(...args){
  const profiling=process.env.YUMENO_NATIVE_UI_PROFILE==='1',started=performance.now();
  if(process.env.YUMENO_NATIVE_QA_SPARSE!=='1')this.layout??=[];
  if(profiling){
   const layer=this;this.qaUIFrame={encodeMS:0,sendMS:0,svgMS:0,svgCalls:0,svgAssets:{}};
   if(!this.qaUISend){const send=this.send;this.send=async function(op,...rest){const at=performance.now();try{const result=await send.call(this,op,...rest);if(op==='ui')layer.qaUIFrame.nativeUI=result;return result;}finally{if(op==='ui')layer.qaUIFrame.sendMS+=performance.now()-at;}};this.qaUISend=true;}
   if(this.canvas&&!profiledCanvases.has(this.canvas)){const encode=this.canvas.encode,canvas=this.canvas;canvas.encode=async function(...args){const at=performance.now();try{return await encode.apply(this,args);}finally{layer.qaUIFrame.encodeMS+=performance.now()-at;}};profiledCanvases.add(canvas);}
   for(const[name,value]of this.images)if(value?.constructor?.name==='NativeSVGImage'&&!profiledSVG.has(value)){const prepare=value.prepare;value.prepare=async function(...args){const at=performance.now();try{return await prepare.apply(this,args);}finally{const ms=performance.now()-at,m=layer.qaUIFrame;m.svgMS+=ms;m.svgCalls++;const row=m.svgAssets[name]??={calls:0,ms:0,sizes:[]};row.calls++;row.ms+=ms;const size=args.map(v=>Math.round(v)).join('x');if(!row.sizes.includes(size))row.sizes.push(size);}};profiledSVG.add(value);}
  }
  const uploads=this.uiFrames;if(process.env.YUMENO_NATIVE_DIAGNOSTIC_NO_UI!=='1'||!this.canvas)await original.apply(this,args);if(!this.canvas&&!this.raster?.active)return;
  if(this.canvas&&process.env.YUMENO_NATIVE_RAW_PAIR==='1'&&performance.now()-rawStarted>30000&&rawCaptured<2){writeFileSync(path.join(directory,'frame-'+rawCaptured+'.rgba'),this.canvas.data());writeFileSync(path.join(directory,'frame-'+rawCaptured+'.size.json'),JSON.stringify({width:this.canvas.width,height:this.canvas.height,time:Date.now()}));rawCaptured++;}
  if(profiling&&this.uiFrames!==uploads&&performance.now()-lastUIProfile>1000){lastUIProfile=performance.now();const m=this.qaUIFrame,drawMS=performance.now()-started;appendFileSync(path.join(directory,'ui-profile.jsonl'),JSON.stringify({time:Date.now(),drawMS,encodeMS:m.encodeMS,sendMS:m.sendMS,nativeUI:m.nativeUI,paintAndBase64MS:drawMS-m.encodeMS-m.sendMS,svgMS:m.svgMS,svgCalls:m.svgCalls,worker:this.raster?.active?this.lastProfile:null,slowSVG:Object.entries(m.svgAssets).filter(([,v])=>v.ms>.1).sort((a,b)=>b[1].ms-a[1].ms).slice(0,8)})+'\n');}
  if(frameTrace&&frameTrace.length<30000)frameTrace.push([performance.now(),performance.now()-started,Date.now()]);
  if(qaRecordingEnabled)await recordFrame(this);
  if(process.env.YUMENO_NATIVE_IMPACT_TRACE==='1'){
   const camera=qaWorld?.objects.find(o=>o.id==='Camera'),shake=camera?.cameraShake;
   const flashes=[...(this.flashes||[])].map(f=>({color:f.color,alpha:f.alpha}));
   if(flashes.length||shake?.remaining>0)appendFileSync(path.join(directory,'impacts.jsonl'),JSON.stringify({sequence,time:performance.now(),task:qaLastStats?.taskId,hp:qaLastStats?.trialHp,flashes,shake,audio:qaWorld?.hooks.audioState?.()})+'\n');
  }
  if(process.env.YUMENO_NATIVE_QA_SPARSE==='1'){
   ++sparseFrameSequence; // uiFrames counts PNG uploads; a static UI may reuse its texture.
   if(performance.now()-lastFrameHeartbeat>1000){lastFrameHeartbeat=performance.now();const row=JSON.stringify({sequence:sparseFrameSequence,time:Date.now()});profileQAWrite('heartbeat',sparseFrameSequence,()=>{writeFileSync(path.join(directory,'frame-heartbeat.json'),row);appendFileSync(path.join(directory,'frame-heartbeat.jsonl'),row+'\n');});}
   if(performance.now()-lastCaptureProbe<50)return;lastCaptureProbe=performance.now(); // Capture requests need20Hz polling; heartbeat still counts every real frame.
   if(!profileQAWrite('captureProbe',sparseFrameSequence,()=>existsSync(path.join(directory,'capture.request'))))return;this.layout??=[]; // sparse 에서도 명시적 캡처 요청은 처리한다(Claude, 2026-11-02)
  }
  if(process.env.YUMENO_NATIVE_TRANSITION_TRACE==='1'&&qaLastStats){const views=[...this.views],cover=views.find(v=>v.state.instance==='loadingv4'),row={sequence,scene:qaWorld?.hooks.scenePath,loading:!!qaLastStats.scenes?.loading,warming:!!qaLastStats.gpuTrialHud?.warming,cover:!!cover,top:cover?views.at(-1)===cover:false,label:cover?.data.nodes.find(n=>n.id==='LoadingLabel')?.properties?.text,background:cover?.data.nodes.find(n=>n.id==='root')?.properties?.background};const signature=JSON.stringify({...row,sequence:0});if(signature!==this.qaTransitionSignature){this.qaTransitionSignature=signature;appendFileSync(path.join(directory,'transitions.jsonl'),JSON.stringify(row)+'\n');}}
  const captureRequest=await fs.readFile(path.join(directory,'capture.request'),'utf8').catch(()=>null);
  const metadataOnly=captureRequest?.startsWith('snapshot:');
  const request=metadataOnly?captureRequest.slice('snapshot:'.length):captureRequest;
  if(!first&&!request)return;if(request&&!/^[a-z0-9_-]{1,64}$/.test(request))throw Error('Invalid owned QA capture name');
  first=false;
  await fs.mkdir(directory,{recursive:true});
  const rects=this.layout.map(n=>({id:n.id,x:n.x,y:n.y,w:n.w,h:n.h}));
  const widgets=[...this.views].map(v=>({owner:v.state.owner,instance:v.state.instance,scrollOffsets:v.scrollOffsets?[...v.scrollOffsets]:null,nodes:v.data.nodes.map(n=>({id:n.id,name:n.name,type:n.type,parent:n.parent,slot:n.slot,properties:n.properties}))}));
  let surface=metadataOnly?{width:args[0],height:args[1]}:this.canvas;
  const stem=request||'initial';
  if(!metadataOnly){
   if(this.raster?.active){const bitmap=await this.raster.capture();surface=createCanvas(bitmap.width,bitmap.height);surface.getContext('2d').drawImage(await loadImage(Buffer.from(bitmap.png)),0,0);}
   const png=surface.toBuffer('image/png');
   await fs.writeFile(path.join(directory,'ui.png'),png);
   if(request)await fs.writeFile(path.join(directory,stem+'.ui.png'),png);
   if(request){const result=await capture();if(!result?.rgba)throw Error('Native capture omitted pixels');const canvas=createCanvas(surface.width,surface.height),ctx=canvas.getContext('2d');ctx.putImageData(new ImageData(new Uint8ClampedArray(result.rgba),canvas.width,canvas.height),0,0);ctx.drawImage(surface,0,0);await fs.writeFile(path.join(directory,stem+'.png'),canvas.toBuffer('image/png'));}
  }
  if(request)await fs.unlink(path.join(directory,'capture.request'));
  const snapshot=path.join(directory,stem+'.ui.json');await fs.writeFile(snapshot+'.tmp',JSON.stringify({qaRenderFields:qaRenderProfile?qaRenderFields:undefined,qaRenderPackets:qaRenderProfile?qaRenderPackets:undefined,qaIOTimings:qaIOProfile?qaIOTimings:undefined,renderViews:qaWorld?.hooks.game?.state?.renderViews,hostFrameRate:qaWorld?.hooks.game?.state?.runtimeSettings?.frameRate,trialSnapshot:qaLastStats?.trial,gpuSnapshot:qaLastStats?.gpuTrialHud,panicSnapshot:qaLastStats?.gpuPanicHud,noiseSnapshot:qaLastStats?.gpuNoiseHud,anagramSnapshot:qaLastStats?.anagramV4,showdownSnapshot:qaLastStats?.showdownV4,frames:this.uiFrames,width:surface.width,height:surface.height,rects,widgets,audio:qaWorld?.hooks.audioState?.(),scene:qaWorld?.hooks.scenePath,renderViews:qaWorld?.hooks.game?.state?.renderViews,world:qaWorld?.objects.filter(o=>!['widget','component'].includes(o.kind)).map(o=>({id:o.id,name:o.name,levelInstance:o.levelInstance,levelSourceId:o.levelSourceId,kind:o.kind,role:o.frameworkRole,parent:o.parentId||o.parent,visible:o.visible,position:o.position,rotation:o.rotation,scale:o.scale,sprite:o.components?.find(c=>c.type==='SpriteRenderer')?.properties,skin:o.components?.find(c=>c.type==='SpriteSkin')?.properties,skinRuntime:o.id?.startsWith('TrialBatch_')?qaWorld?.hooks.spriteSkinSnapshot?.(o.id):undefined,cameraFov:o.components?.find(c=>c.type==='Camera')?.properties?.fieldOfView,antialias:o.components?.find(c=>c.type==='PostProcessVolume')?.properties?.antiAliasing,mesh:o.components?.find(c=>c.type==='MeshRenderer')?.properties?.mesh,meshVisible:o.components?.find(c=>c.type==='MeshRenderer')?.properties?.visible}))}));await fs.rename(snapshot+'.tmp',snapshot);
 };
}
