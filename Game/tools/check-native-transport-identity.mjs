import assert from 'node:assert/strict';
import {NativeHost} from "file:///C:/Users/kirby/OneDrive/%EB%B0%94%ED%83%95%20%ED%99%94%EB%A9%B4/git/engineCreate/tools/native-host.mjs";
import {NativeWorldClient,nativeWorldClient,worldPatch,applyWorldPatch,immutableNativeSnapshot} from './native-transport-identity.candidate.mjs';

const snapshot=value=>JSON.parse(JSON.stringify(value));
const object=(id,x)=>({id,position:[x,0,.1],rotation:[0,0,0],scale:[1,1,1],nested:{'a~/b':[1,2],keep:{flag:true}}});
const old=[object('a',1),object('b',2)],next=snapshot(old);
next[0].position[0]=3;next[0].nested['a~/b'][1]=7;delete next[0].nested.keep;next[0].nested.added=[8,9];
const patched=applyWorldPatch(old,snapshot(worldPatch(old,next)));
assert.deepEqual(patched,next);assert.deepEqual(old,[object('a',1),object('b',2)]);
assert.equal(patched[1],old[1],'unchanged objects share immutable snapshot storage');
assert.throws(()=>applyWorldPatch(old,[{op:'replace',path:'/0/position',value:[9,0,0]},{op:'remove',path:'/missing'}]));
assert.equal(old[0].position[0],1,'invalid later operation cannot mutate the committed world');
assert.throws(()=>applyWorldPatch(old,[{op:'replace',path:'/0/nested/a~2b',value:1}]),/Pointer/);
assert.throws(()=>applyWorldPatch(old,[{op:'replace',path:'/0/__proto__/polluted',value:true}]),/parent/);
assert.throws(()=>applyWorldPatch(old,Array(4097).fill({op:'replace',path:'',value:[]})),/limit/);
const proto=applyWorldPatch(old,[{op:'add',path:'/0/__proto__',value:{polluted:true}}]);
assert.equal(Object.prototype.polluted,undefined);assert.equal(Object.getPrototypeOf(proto[0]),Object.prototype);
assert.ok(Object.hasOwn(proto[0],'__proto__'));
assert.deepEqual(applyWorldPatch([1,2,3],[{op:'remove',path:'/1'},{op:'add',path:'/1',value:4}]),[1,4,3]);
assert.deepEqual(applyWorldPatch([1,2,3,4,5],snapshot(worldPatch([1,2,3,4,5],[1,undefined,3,4,5]))),[1,null,3,4,5]);
let deep={value:1};for(let i=0;i<70;i++)deep={child:deep};const deepNext=snapshot(deep);let leaf=deepNext;for(let i=0;i<70;i++)leaf=leaf.child;leaf.value=2;
assert.equal(worldPatch(deep,deepNext),null,'deep custom JSON falls back to full transport');
const owner={},build={token:'same'};
assert.equal(nativeWorldClient(build,owner),nativeWorldClient({...build},owner),'BP paths sharing one worker share one sequence');
assert.notEqual(nativeWorldClient(build,owner),nativeWorldClient(build,{}),'new play world owns a new snapshot');
for(const workerProtocol of [undefined,1,2]){
  const request={objects:old},client=new NativeWorldClient({hooks:{nativeRowReuse:true}});
  await client.call(request,{workerProtocol},async packet=>{assert.equal(packet,request);assert.equal(packet.worldTransport,undefined);return {};});
}
{
  const client=new NativeWorldClient({hooks:{nativeRowReuse:true}}),ui=immutableNativeSnapshot({hud:{text:'한글',value:1}}),objects=[{...object('ui',0),gameplayDebug:{ui}}],packets=[];
  const send=async packet=>{packets.push(snapshot(packet));return {worldSequence:packet.worldSequence,objects:[],worldCommitted:[]};};
  await client.call({objects},{workerProtocol:3},send);const saved=client.world[0].gameplayDebug.ui;
  objects[0].position[0]=2;await client.call({objects},{workerProtocol:3},send);
  assert.equal(client.world[0].gameplayDebug.ui,saved,'unchanged immutable UI shares detached wire storage during actor movement');
  assert.deepEqual(packets.at(-1).objectPatch,[{op:'replace',path:'/0/position/0',value:2}]);
  objects[0].gameplayDebug.ui=immutableNativeSnapshot({hud:{text:'변경',value:2}});await client.call({objects},{workerProtocol:3},send);
  assert.equal(client.world[0].gameplayDebug.ui.hud.text,'변경');assert.equal(saved.hud.text,'한글');assert.equal(ui.hud.value,1);
}

{
 const map=immutableNativeSnapshot({layers:[{tiles:Array.from({length:16384},(_,i)=>({x:i%128,y:Math.floor(i/128),index:0}))}]},{clone:false}),client=new NativeWorldClient({hooks:{nativeRowReuse:true}}),objects=[{...object('tiles',0),runtimeTilemap:map,gameplayDebug:{ui:immutableNativeSnapshot({hud:{text:'한글'}})}}],packets=[];const send=async packet=>{packets.push(snapshot(packet));return {worldSequence:packet.worldSequence,objects:[],worldCommitted:[]};};await client.call({objects},{workerProtocol:3},send);const first=client.world[0].runtimeTilemap;assert.equal(first,map);objects[0].position[0]=3;await client.call({objects},{workerProtocol:3},send);assert.equal(client.world[0].runtimeTilemap,first);assert.deepEqual(packets.at(-1).objectPatch,[{op:'replace',path:'/0/position/0',value:3}]);assert.throws(()=>{map.layers[0].tiles[0].index=9;},TypeError);const next={...map,layers:[{...map.layers[0],tiles:[{...map.layers[0].tiles[0],index:9},...map.layers[0].tiles.slice(1)]}]};objects[0].runtimeTilemap=immutableNativeSnapshot(next,{clone:false});await client.call({objects},{workerProtocol:3},send);assert.equal(client.world[0].runtimeTilemap.layers[0].tiles[0].index,9);assert.equal(map.layers[0].tiles[0].index,0);assert.deepEqual(packets.at(-1).objectPatch,[{op:'replace',path:'/0/runtimeTilemap/layers/0/tiles/0/index',value:9}]);
}
const host=new NativeHost();
try {
  const header='#include <HBEngine/Game.hpp>\nHB_CLASS()\nclass TransportProbe : public hb::Library { public: HB_FUNCTION(BlueprintPure) static hb::Vec3 Read(hb::Actor* target); HB_FUNCTION(BlueprintPure) static int Nested(); HB_FUNCTION(BlueprintPure) static bool Unsigned(); HB_FUNCTION(BlueprintPure) static int WorldOnConstruct(); HB_FUNCTION(BlueprintCallable) static void Retype(); HB_FUNCTION(BlueprintCallable) static void Tamper(bool erase); HB_FUNCTION(BlueprintCallable) static void Fail(); };\nHB_CLASS()\nclass TransportActor : public hb::Actor { public: TransportActor(); HB_PROPERTY(BlueprintReadWrite) int Count=0; HB_FUNCTION(BlueprintCallable) void Mutate(); };\nHB_CLASS() class RoundingActor : public hb::Actor { public: HB_PROPERTY(BlueprintReadWrite) double Value=0; HB_FUNCTION(BlueprintCallable) void SetValue(double value); HB_FUNCTION(BlueprintPure) double ReadValue(); };';
  const source='#include "User.h"\nint constructedWorldSize=-1;\nint TransportProbe::WorldOnConstruct(){return constructedWorldSize;}\nhb::Vec3 TransportProbe::Read(hb::Actor* target){return target->transform.position;}\nint TransportProbe::Nested(){return hb::bridgeWorld.at(0).at("nested").at("a~/b").at(1).get<int>();}\nbool TransportProbe::Unsigned(){return hb::bridgeWorld.at(0).at("nested").at("a~/b").at(0).is_number_unsigned();}\nvoid TransportProbe::Retype(){hb::bridgeWorld.at(0)["nested"]["a~/b"][0]=1.0;}\nvoid TransportProbe::Tamper(bool erase){if(erase)hb::bridgeWorld.clear();else{hb::bridgeWorld.at(0)["nested"]["a~/b"][1]=999;hb::bridgeWorld.at(1)["extra"]=true;}}\nvoid TransportProbe::Fail(){throw std::runtime_error("transport probe failure");}\nTransportActor::TransportActor(){constructedWorldSize=static_cast<int>(hb::bridgeWorld.size());hb::bridgeWorld.clear();}\nvoid TransportActor::Mutate(){Count++;transform.position.x+=5;}\nvoid RoundingActor::SetValue(double value){Value=value;} double RoundingActor::ReadValue(){return Value;}';
  const built=await host.build(header,source),client=new NativeWorldClient({hooks:{nativeRowReuse:true}}),packets=[];
  let objects=Array.from({length:480},(_,i)=>object('actor'+i,i));
  Object.assign(objects[0],{nativeClass:'TransportActor',nativeProperties:{Count:0}});
  const send=async packet=>{const wire=snapshot(packet);packets.push(wire);return snapshot(await host.call(built.token,wire));};
  const request=(nativeId='TransportProbe.Read',args={target:'actor0'})=>({key:'nativeCall',nativeId,args,objects});
  const call=(nativeId,args)=>client.call(request(nativeId,args),built.metadata,send);
  let reply=await call();assert.deepEqual(reply.outputs.result,[0,0,Math.fround(.1)]);assert.deepEqual(reply.objects,[],'pure read avoids returning all transforms');
  for(const key of ['parseMs','patchMs','syncMs','invokeMs','snapshotMs','workerMs','decodeMs','validateMs','replyValidationMs'])assert.ok(Number.isFinite(reply.transport[key])&&reply.transport[key]>=0,'native timing: '+key);
  for(const [index,invalid] of [[0,{Count:'wrong'}],[0,{Unknown:7}],[200,{Count:1}]]){
    const saved=objects[index].nativeProperties;objects[index].nativeProperties=invalid;await assert.rejects(call(),/C\+\+ 속성 자료형 오류/);if(saved===undefined)delete objects[index].nativeProperties;else objects[index].nativeProperties=saved;
    reply=await call();assert.equal(reply.transport.upstreamMode,'full');assert.deepEqual(reply.outputs.result,[0,0,Math.fround(.1)],'invalid properties never reach user C++ or mutate its actor');
  }
  const savedPosition=objects[201].position;objects[201].position=[NaN,0,0];await assert.rejects(call(),/C\+\+ 객체 상태 오류/);objects[201].position=savedPosition;reply=await call();assert.equal(reply.transport.upstreamMode,'full','plain actor transforms remain validated and recover without a typed property dictionary');
  objects[200].position[0]+=.25;objects[0].nested['a~/b'][1]=7;objects[0].omit=undefined;
  reply=await call('TransportProbe.Nested',{});assert.equal(reply.outputs.result,7);assert.equal(reply.transport.upstreamMode,'patch');
  assert.ok(reply.transport.upstreamBytes<JSON.stringify(objects).length/100,'HTTP and worker both carry the changed paths');
  assert.equal(reply.transport.mode,'patch');assert.deepEqual(reply.objects,[]);
  reply=await client.call({command:'frame',delta:.01,objects:[]},built.metadata,send);assert.equal(reply.transport.mode,'clock');
  reply=await call();assert.deepEqual(packets.at(-1).objectPatch,[],'clock preserves the committed input world');
  for(const erase of [false,true]){await call('TransportProbe.Tamper',{erase});reply=await call('TransportProbe.Nested',{});assert.equal(reply.outputs.result,7,'temporary C++ JSON mutation does not corrupt the authoritative input cache');assert.equal(reply.transport.mode,'patch');}
  assert.equal((await call('TransportProbe.Unsigned',{})).outputs.result,true);await call('TransportProbe.Retype',{});assert.equal((await call('TransportProbe.Unsigned',{})).outputs.result,true,'equal numeric values with different JSON types must still restore');
  Object.assign(objects[1],{nativeClass:'TransportActor',nativeProperties:{Count:4}});assert.equal((await call('TransportProbe.Nested',{})).outputs.result,7,'new C++ constructors cannot alter the authoritative world used by the function');
  reply=await call('TransportActor.Mutate',{target:'actor0'});assert.equal(reply.objects.length,1);assert.equal(reply.objects[0].nativeProperties.Count,1);assert.equal(reply.objects[0].position[0],5);
  assert.deepEqual(reply.worldCommitted,['actor0']);Object.assign(objects[0],reply.objects[0]);reply=await call();assert.deepEqual(packets.at(-1).objectPatch,[],'returned C++ writes are not echoed in the next request');assert.equal(reply.outputs.result[0],5);assert.deepEqual(reply.objects,[],'unchanged float32 conversion does not write all objects back');
  const beforeFailure=packets.length;await assert.rejects(call('TransportProbe.Fail',{}),/probe failure/);assert.equal(packets.length,beforeFailure+1,'side effects are never automatically retried');
  reply=await call();assert.equal(reply.transport.upstreamMode,'full');assert.equal(reply.outputs.result[0],5);
  const child=host.sessions.get(built.token).process;await new Promise(resolve=>{child.once('exit',resolve);child.kill();});
  objects[0].position[0]=6;reply=await call();assert.equal(reply.outputs.result[0],6);assert.equal(reply.transport.upstreamMode,'patch');assert.equal(reply.transport.mode,'full','worker restart rebuilds its world from the decoded client delta');
  const beforeDrop=packets.length;
  await assert.rejects(client.call(request(),built.metadata,async packet=>{await send(packet);throw Error('response dropped');}),/dropped/);
  assert.equal(packets.length,beforeDrop+1);reply=await call();assert.equal(reply.transport.upstreamMode,'full','lost response forces explicit full resynchronization');
  await assert.rejects(client.call(request(),built.metadata,async packet=>{const r=await send(packet);return {...r,worldSequence:r.worldSequence+1};}),/acknowledgment/);
  reply=await call();assert.equal(reply.transport.upstreamMode,'full');
  const other=new NativeWorldClient({hooks:{nativeRowReuse:true}});await other.call(request(),built.metadata,send);
  await assert.rejects(call(),/sequence mismatch/,'different world identity cannot silently patch the wrong world');reply=await call();assert.equal(reply.transport.upstreamMode,'full');
  const forged={...packets.at(-1),objects:undefined,baseSequence:1,worldSequence:2,objectPatch:[{op:'replace',path:'/0/position',value:[99,0,0]},{op:'remove',path:'/noSuchObject'}]};
  await assert.rejects(host.call(built.token,snapshot(forged)),/array index/);assert.equal(client.world[0].position[0],6);await assert.rejects(call(),/sequence mismatch/);assert.equal((await call()).outputs.result[0],6);
  delete objects[1].nativeClass;delete objects[1].nativeProperties;await client.call({command:'reset',objects:[]},built.metadata,send);reply=await call();assert.equal(reply.transport.upstreamMode,'full');assert.equal((await call('TransportProbe.WorldOnConstruct',{})).outputs.result,0,'reset releases the previous C++ JSON world before new constructors run');
  const concurrent=await Promise.all([call('TransportProbe.Nested',{}),call()]);assert.equal(concurrent[0].outputs.result,7);assert.equal(concurrent[1].outputs.result[0],6);
  assert.equal(packets.at(-1).worldSequence,packets.at(-2).worldSequence+1);
  // Existing hosts/headless callers still use mutable full snapshots.
  objects[0].position[0]=8;assert.equal((await host.call(built.token,request())).outputs.result[0],8);
  Object.assign(objects[2],{nativeClass:'RoundingActor',nativeProperties:{Value:0}});
  for(const value of [1,-1,1.25,1e22]){reply=await call('RoundingActor.SetValue',{target:'actor2',value});assert.deepEqual(reply.worldCommitted,['actor2']);Object.assign(objects[2],reply.objects[0]);reply=await call('RoundingActor.ReadValue',{target:'actor2'});assert.equal(reply.outputs.result,value);assert.deepEqual(packets.at(-1).objectPatch,[],'numeric output acknowledgment uses the JSON wire representation');}
  objects[2].nativeProperties.Value=2;assert.equal(client.world[2].nativeProperties.Value,1e22,'returned property dictionaries are detached from mutable gameplay state');assert.equal((await call('RoundingActor.ReadValue',{target:'actor2'})).outputs.result,2);
  const unsafe=1000000000000000100;reply=await call('RoundingActor.SetValue',{target:'actor2',value:unsafe});assert.deepEqual(reply.worldCommitted,[],'ambiguous large integral decimals use the original input transport');Object.assign(objects[2],reply.objects[0]);assert.equal((await call('RoundingActor.ReadValue',{target:'actor2'})).outputs.result,unsafe);assert.ok(packets.at(-1).objectPatch.length>0);
  console.log('C++ client→JSON wire→host→worker: deltas, immutable snapshots, changed replies, shared tokens, clock/reset, queue, rejection/lost reply/restart recovery and legacy full callers passed');
} finally {host.close();}
