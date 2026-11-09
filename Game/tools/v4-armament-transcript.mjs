// Preserve the authored argument order; a note row is never a dialogue index.
export const normalizeArmamentText=text=>text.trim().replace(/\s+/gu,' ').replace(/([.!?。！？…])(?=[가-힣A-Za-z])/gu,'$1 ');
export function armamentTranscript(lines,maxLength=12){
 const result=[];
 for(let line=0;line<lines.length;line++){
  let part=0;
  for(const sentence of normalizeArmamentText(lines[line]).split(/(?<=[.!?。！？…])\s+/u)){
   const groups=[];let words=[];
   for(const word of sentence.split(' ')){
    if(words.length&&[...words.join(' ')+' '+word].length>maxLength){groups.push(words);words=[];}
    words.push(word);
   }
   if(words.length)groups.push(words);
   if(maxLength>=12&&groups.length>1){const tail=groups.at(-1),previous=groups.at(-2);while([...tail.join(' ')].length<6&&previous.length>1)tail.unshift(previous.pop());}
   for(const group of groups)result.push({line,part:part++,text:group.join(' ')});
  }
 }
 return result;
}
