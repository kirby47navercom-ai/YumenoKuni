import fs from 'node:fs/promises';
import path from 'node:path';
export async function publishTrialGlyphHeader(sourceDir, header){
 const marker='inline constexpr Glyph entries[]={\n',start=header.indexOf(marker)+marker.length,end=header.indexOf('\n};',start);
 if(start<marker.length||end<0)throw Error('Invalid generated trial glyph header');
 const rows=header.slice(start,end).split('\n');
 // Includes stay inside the same array. Lookup order and every value are unchanged.
 const blocks=[];
 for(let i=0;i<rows.length;i+=8000)blocks.push(rows.slice(i,i+8000).join('\n')+'\n');
 const write=async(name,text)=>{const file=path.join(sourceDir,name);await fs.writeFile(file+'.tmp',text);await fs.rename(file+'.tmp',file);};
 const names=blocks.map((_,i)=>`GpuTrialAtlasRows${i}.inl`);
 for(const [i,block] of blocks.entries())await write(names[i],block);
 await write('GpuTrialAtlasDataV4.hpp',header.slice(0,start)+names.map(n=>`#include "${n}"`).join('\n')+header.slice(end));
 return names;
}
