// Exact minimal transport candidate, stored only in this project's QA evidence.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const root=path.resolve(import.meta.dirname,'..'),sourceFile=path.resolve(root,'../../engineCreate/prototype/native-scene-renderer.js');
const source=await fs.readFile(sourceFile,'utf8'),needle="if(packet.resources.length)await send('upload',packet.resources);";assert(source.includes(needle));
const replacement="for(const resource of packet.resources)await send('upload',[resource]);",candidate=source.replace(needle,replacement),work=path.join(root,'Saved/native-renderer-candidate-'+Date.now());await fs.mkdir(work,{recursive:true});
const file=path.join(work,'native-scene-renderer.candidate.js');await fs.writeFile(file,candidate);const hash=s=>createHash('sha256').update(s).digest('hex');
await fs.writeFile(path.join(work,'report.json'),JSON.stringify({sourceFile,sourceSHA256:hash(source),candidate:file,candidateSHA256:hash(candidate),change:{before:needle,after:replacement},reason:'An initial frame batches all actual game textures/meshes into one upload exceeding the native128MiB packet limit. Preserve every resource and its order, send each existing protocol resource separately. Engine original and limits unchanged.',scope:'Candidate only; full native title verification pending. Oversized individual resources are not claimed supported.'},null,2));console.log(JSON.stringify({candidate:file,sourceSHA256:hash(source)}));
