// QA chooses a physical Q/E edge; it never selects or grants game evidence.
export function bulletCycleKey(ids,current,target){
 const at=ids.indexOf(current),to=ids.indexOf(target);
 if(at<0||to<0)throw Error('Live debate evidence is absent from the actual saved inventory');
 if(at===to)return null;
 return (to-at+ids.length)%ids.length<=(at-to+ids.length)%ids.length?'e':'q';
}
