// Engine-owned plain JSON data only, never arbitrary user JS objects/proxies.
// Every scalar is checked, including in-place array/component edits.
export function sameRuntimeData(snapshot,current){
 let budget=16384;
 function equal(a,b,depth){
  if(--budget<0||depth>64)return false;if(a===b)return true;
  if(!a||!b||typeof a!=='object'||typeof b!=='object'||'toJSON'in b)return false;
  const array=Array.isArray(b),proto=Object.getPrototypeOf(b);if(Array.isArray(a)!==array||(array?proto!==Array.prototype:proto!==Object.prototype&&proto!==null))return false;
  if(array){if(a.length!==b.length)return false;for(let i=0;i<b.length;i++)if(!equal(a[i],b[i],depth+1))return false;return true;}
  let before=0,after=0;for(const k in a)if(Object.hasOwn(a,k))before++;
  for(const k in b)if(Object.hasOwn(b,k)){after++;if(!Object.hasOwn(a,k)||!equal(a[k],b[k],depth+1))return false;}
  return before===after;
 }
 return equal(snapshot,current,0);
}

// Native/headless JSON ownership is explicit. Keys are quoted as data, never
// executable input. Keep code size/cache bounded; unusual schemas use JSON.
export function runtimeDataMatcher(snapshot,cache,immutable){
 let fields=0;const statements=[];
 function emit(value,a,b,depth){
  if(++fields>1024||depth>16)throw Error('schema budget');
  if(value===null||typeof value!=='object'||immutable?.has(value)){statements.push(`if(${a}!==${b})return false;`);return;}
  if(Array.isArray(value)){statements.push(`if(!Array.isArray(${b})||${b}.length!==${value.length})return false;`);for(let i=0;i<value.length;i++)emit(value[i],a+'['+i+']',b+'['+i+']',depth+1);return;}
  const keys=Object.keys(value);statements.push(`if(!${b}||typeof ${b}!=="object"||Array.isArray(${b})||Object.keys(${b}).length!==${keys.length})return false;`);
  for(const key of keys){const quoted=JSON.stringify(key);statements.push(`if(!Object.hasOwn(${b},${quoted}))return false;`);emit(value[key],a+'['+quoted+']',b+'['+quoted+']',depth+1);}
 }
 try{emit(snapshot,'a','b',0);const source=statements.join('')+'return true;';if(source.length>65536)return null;let test=cache.get(source);if(!test){test=new Function('a','b',source);if(cache.size>=16)cache.delete(cache.keys().next().value);cache.set(source,test);}return {snapshot,test};}catch{return null;}
}
