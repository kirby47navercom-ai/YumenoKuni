from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=(root.parent/'engineCreate/prototype/ui-runtime.js').read_text(encoding='utf8')
helper='''// Reuse only byte-identical detached, frozen node snapshots. Mutable widget
// data never escapes into native transport; removed rows are not retained.
const widgetSnapshots=new WeakMap(),widgetDirtyNodes=new WeakMap();
function nativeWidgetSnapshot(state,localization,dirtyNodes){
 const prior=widgetSnapshots.get(state),rows=new Map(),entries=[];let changed=!prior||prior.rows.size!==state.data.nodes.length,index=0;
 for(const n of state.data.nodes){
  const old=prior?.rows.get(n.name);let row=old;
  if(!old||!dirtyNodes||dirtyNodes.has(n)||old.node!==n){const value={type:n.type,...n.properties,...n.properties.stringTable&&n.properties.textKey&&localization?{text:localization.format(n.properties.stringTable,n.properties.textKey,JSON.parse(n.properties.textArguments||'{}'),n.properties.text)}:{},slot:n.slot,value:n.type==='CheckBox'?Number(n.properties.checked):n.properties.value},text=JSON.stringify(value);row=old?.text===text?old:{node:n,text,snapshot:immutableNativeSnapshot(value)};}
  if(row!==old||prior?.names[index]!==n.name)changed=true;index++;rows.set(n.name,row);entries.push([n.name,row.snapshot]);
 }
 const snapshot=changed?immutableNativeSnapshot(Object.fromEntries(entries),{clone:false}):prior.snapshot;
 widgetSnapshots.set(state,{rows,names:entries.map(row=>row[0]),snapshot});return snapshot;
}
'''
source=source.replace('export class WidgetSystem {',helper+'\nexport class WidgetSystem {')
start=source.index('const snapshot=immutableNativeSnapshot(Object.fromEntries(state.data.nodes.map(')
end=source.index(';owner.gameplayDebug.ui=',start)
source=source[:start]+'const snapshot=nativeWidgetSnapshot(state,this.hooks.localization,dirtyNodes)'+source[end:]
source=source.replace('sync(state,vm){const owner=', 'sync(state,vm,dirtyNodes){const owner=')
source=source.replace('refresh(state,vm){if(this.batchDepth){this.dirty.add(state);return;}state.view?.update();this.sync(state,vm);}', 'refresh(state,vm,node,preserve=false){if(!preserve){if(!node)widgetDirtyNodes.set(state,null);else if(!widgetDirtyNodes.has(state))widgetDirtyNodes.set(state,new Set([node]));else widgetDirtyNodes.get(state)?.add(node);}if(this.batchDepth){this.dirty.add(state);return;}state.view?.update();const dirtyNodes=widgetDirtyNodes.get(state);widgetDirtyNodes.delete(state);this.sync(state,vm,dirtyNodes);}')
source=source.replace('===state)this.refresh(state,vm);}}}', '===state)this.refresh(state,vm,undefined,true);}}}')
source=source.replace("this.refresh(state,vm);if(key==='uiSetFont')", "this.refresh(state,vm,node);if(key==='uiSetFont')")
needle="else if(key.startsWith('uiSet')){\n      const n="
replacement="""else if(key.startsWith('uiSet')){
      // Equal, already validated values do not need another full node clone.
      // Changed or malformed requests still follow the complete validator.
      const scalar=key==='uiSetRotation'?'rotation':key==='uiSetOpacity'?'opacity':key==='uiSetFontSize'?'fontSize':'';
      if(scalar&&Number.isFinite(a[scalar])&&p[scalar]===a[scalar])return {};
      if(key==='uiSetScale'&&Array.isArray(a.scale)&&a.scale.length===2&&a.scale.every((v,i)=>Number.isFinite(v)&&v===p.scale?.[i]))return {};
      if(key==='uiSetPosition'||key==='uiSetSize'){const values=key==='uiSetPosition'?a.position:a.size,index=key==='uiSetPosition'?0:2;if(Array.isArray(values)&&values.length===2&&values.every((v,i)=>Number.isFinite(v)&&v===node.slot.offset[index+i]))return {};}
      const n="""
assert source.count(needle)==1;source=source.replace(needle,replacement)
(root/'Game/tools/ui-runtime-snapshot.candidate.mjs').write_text(source,encoding='utf8')
print('Created detached immutable node snapshot candidate')
