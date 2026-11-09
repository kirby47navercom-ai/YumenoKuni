import assert from 'node:assert/strict';

// Preserve paint order and every leaf/ancestor property; only the update owners differ.
export function mainWidgetParts(widget,chunk=8){
 const root=widget.nodes.find(n=>n.id==='root');assert(root);
 const containers=new Map(widget.nodes.filter(n=>n.parent==='root'&&widget.nodes.some(c=>c.parent===n.id)).map(n=>[n.id,n]));
 const groups=[];let pending=[];
 const flush=()=>{if(pending.length){groups.push(pending);pending=[];}};
 for(const node of widget.nodes.filter(n=>n.parent==='root')){
  if(!containers.has(node.id)){pending.push(node);if(pending.length===chunk)flush();continue;}
  flush();const children=widget.nodes.filter(n=>n.parent===node.id);
  assert(children.every(n=>!widget.nodes.some(c=>c.parent===n.id)),'Only existing flat Main child groups supported');
  if(children.length>chunk){assert.equal(node.properties.background,'#00000000');assert.equal(node.properties.borderWidth,0);}
  for(let at=0;at<children.length;at+=chunk)groups.push([node,...children.slice(at,at+chunk)]);
 }
 flush();const routes={},parts=groups.map((nodes,index)=>{
  const instance='mainpart'+String(index).padStart(2,'0'),asset='Assets/UI/MainPart'+String(index).padStart(2,'0')+'.hbwidget.json';
  const data=structuredClone({...widget,name:widget.name+'_'+index,nodes:[root,...nodes]});
  for(const n of data.nodes)(routes[n.id]??=[]).push(instance);
  return {instance,asset,data};
 });
 const before=widget.nodes.filter(n=>!containers.has(n.id)&&n.id!=='root'),after=parts.flatMap(p=>p.data.nodes.filter(n=>!containers.has(n.id)&&n.id!=='root'));
 assert.deepEqual(after,before,'Leaf paint order/properties changed');
 const header='#pragma once\n#include <map>\n#include <string>\n#include <vector>\n#include <utility>\nnamespace mainwidgetv4 {\ninline const std::vector<std::pair<std::string,std::string>>& parts(){static const std::vector<std::pair<std::string,std::string>> p{'+parts.map(p=>'{'+JSON.stringify(p.instance)+','+JSON.stringify(p.asset)+'}').join(',')+'};return p;}\ninline const std::vector<std::string>& instances(const std::string& id){static const std::map<std::string,std::vector<std::string>> r{'+Object.entries(routes).map(([id,list])=>'{'+JSON.stringify(id)+',{'+list.map(s=>JSON.stringify(s)).join(',')+'}}').join(',')+'};static const std::vector<std::string> none;auto it=r.find(id);return it==r.end()?none:it->second;}\n}\n';
 return {parts,routes,header,leaves:before.length};
}

export function addMainPartOwners(scene,parts){
 const result=structuredClone(scene);result.objects=result.objects.filter(o=>!/^UI_mainpart\d+$/.test(o.id));
 const at=result.objects.findIndex(o=>o.id==='UI_main');assert(at>=0,'Existing Main owner required');
 result.objects.splice(at+1,0,...parts.map(p=>({id:'UI_'+p.instance,name:p.instance+' UI',kind:'empty',position:[0,0,0],rotation:[0,0,0],scale:[1,1,1],visible:true,components:[]})));return result;
}

export function routedMainOwnerSource(source){
 let result=source.replace('#include <HBEngine/Game.hpp>','#include <HBEngine/Game.hpp>\n#include "MainWidgetLayoutV4.hpp"');
 const show=' static void Show(hb::Actor* a,const std::string& asset,const std::string& i){hb::UI::Show(Owner(a,i),asset,i);}';
 assert(result.includes(show));result=result.replace(show,' static void Show(hb::Actor* a,const std::string& asset,const std::string& i){if(i=="main"){for(const auto& p:mainwidgetv4::parts())hb::UI::Show(Owner(a,p.first),p.second,p.first);return;}hb::UI::Show(Owner(a,i),asset,i);}');
 const remove=' static void Remove(hb::Actor* a,const std::string& i){hb::UI::Remove(Owner(a,i),i);}';assert(result.includes(remove));
 result=result.replace(remove,' static void Remove(hb::Actor* a,const std::string& i){if(i=="main"){for(const auto& p:mainwidgetv4::parts())hb::UI::Remove(Owner(a,p.first),p.first);return;}hb::UI::Remove(Owner(a,i),i); }\n template<class F>static void Each(hb::Actor* a,const std::string& i,const std::string& e,F f){if(i=="main"){for(const auto& p:mainwidgetv4::instances(e))f(Owner(a,p),p);return;}f(Owner(a,i),i);}');
 let replaced=0;result=result.replace(/\{hb::UI::(Set\w+)\(Owner\(a,i\),i,e,v\);\}/g,(_all,fn)=>{replaced++;return '{Each(a,i,e,[&](hb::Actor* o,const std::string& p){hb::UI::'+fn+'(o,p,e,v);});}';});assert.equal(replaced,11);return result;
}
