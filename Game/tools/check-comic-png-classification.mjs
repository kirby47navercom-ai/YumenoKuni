import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),bank=path.join(repo,'art/v4_production/comic_revisions_20261104'),selection=JSON.parse(await fs.readFile(path.join(bank,'selection.json'),'utf8'));
const {nativeWidgetImage,NativeSVGImage}=await import(pathToFileURL(path.join(root,'Saved/native-panic-views-1793690486425/package/tools/native-webp-animation.mjs')));
const cases=[];
for(const row of selection.rows){const raw=await fs.readFile(path.join(repo,row.original)),runtime=await fs.readFile(path.join(repo,row.image));assert(raw.subarray(0,8).equals(runtime.subarray(0,8)));const before=await nativeWidgetImage(raw),after=await nativeWidgetImage(runtime);assert(before instanceof NativeSVGImage);assert(!(after instanceof NativeSVGImage));cases.push({id:row.slotId+row.optionId,originalPNGWasMisclassified:true,runtimeStaticImage:true});before.dispose();after.dispose?.();}
await fs.writeFile(path.join(bank,'engine-classification-proof.json'),JSON.stringify({ok:true,engineModified:false,scope:'Actual retained native image loader, six original PNGs vs metadata-only runtime copies; no game outcome or performance claim',engineFault:'tools/native-webp-animation.mjs:46 scans for <svg in first4096 bytes without checking PNG signature first',cases},null,2));console.log(JSON.stringify({ok:true,cases:cases.length,engineModified:false}));
