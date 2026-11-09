// Metadata-only PNG compatibility for the retained native widget image loader.
// Original source files, compressed pixels and every non-caBX chunk stay intact.
import assert from 'node:assert/strict';
const signature=Buffer.from([137,80,78,71,13,10,26,10]);
export function nativeWidgetPng(bytes){
 assert(Buffer.isBuffer(bytes)&&bytes.subarray(0,8).equals(signature),'Expected an actual PNG');
 const parts=[bytes.subarray(0,8)];let at=8,ended=false;
 while(at<bytes.length){assert(at+12<=bytes.length,'Truncated PNG chunk');const size=bytes.readUInt32BE(at),end=at+size+12;assert(end<=bytes.length,'PNG chunk exceeds file');const kind=bytes.toString('ascii',at+4,at+8);if(kind!=='caBX')parts.push(bytes.subarray(at,end));at=end;if(kind==='IEND'){assert(size===0&&at===bytes.length,'Invalid PNG end');ended=true;}}
 assert(ended,'Missing PNG end');const result=Buffer.concat(parts);
 assert(!/<svg(?:\s|>)/i.test(result.subarray(0,4096).toString('utf8')),'Remaining metadata would be misclassified as SVG');
 return result;
}
