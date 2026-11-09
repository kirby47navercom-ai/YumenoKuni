// Bind the already approved render bridge without replacing the user's SDK.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
export async function approvedPanicBuilder({root,engineRoot,player,compileMs=0}){
 player=await fs.realpath(player);assert(player.startsWith(path.join(root,'Saved')+path.sep));
 const bytes=await fs.readFile(player);assert(bytes.includes(Buffer.from('renderViews'))&&bytes.includes(Buffer.from('Render view count invalid')),'Native executable must implement the approved render protocol');
 const shaders=path.join(path.dirname(player),'panic-render-player-build/Shaders');await fs.access(shaders);
 const file=path.join(engineRoot,'tools/build-native-game.mjs');let source=await fs.readFile(file,'utf8');
 const replacements=[
  ["path.resolve(import.meta.dirname,'..')",JSON.stringify(engineRoot)],
  ["player=path.join(desktop,'HBNativePlayer.exe')",'player='+JSON.stringify(player)],
  ["path.join(desktop,'Shaders')",JSON.stringify(shaders)],
  ["path.join(desktop,'Shaders',entry.name)",'path.join('+JSON.stringify(shaders)+',entry.name)'],
 ];
 for(const[from,to]of replacements){assert.equal(source.split(from).length,2,'SDK builder changed; review the exact adapter: '+from);source=source.replace(from,to);}
 source=source.replace(/from (['"])(\.\.?\/[^'"]+)\1/g,(_,q,relative)=>'from '+JSON.stringify(pathToFileURL(path.resolve(path.dirname(file),relative)).href));
 if(compileMs){
  const hostFile=path.join(engineRoot,'tools/native-host.mjs');
  let host=await fs.readFile(hostFile,'utf8');
  const deadline='performance.now()+nativeBuildTimeoutMs(generated.sourceFiles.length)';
  assert.equal(host.split(deadline).length,2,'SDK compile deadline changed');
  host=host.replace(deadline,'performance.now()+Math.max('+compileMs+',nativeBuildTimeoutMs(generated.sourceFiles.length))').replace("path.resolve(import.meta.dirname,'..')",JSON.stringify(engineRoot));
  host=host.replace(/from (['"])(\.\.?\/[^'"]+)\1/g,(_,q,relative)=>'from '+JSON.stringify(pathToFileURL(path.resolve(path.dirname(hostFile),relative)).href));
  const ownedHost=path.join(root,'Saved/game-trial-work-20261102/approved-panic-host.generated.mjs');
  await fs.writeFile(ownedHost,host);
  const hostUrl=JSON.stringify(pathToFileURL(hostFile).href);assert.equal(source.split(hostUrl).length,2);
  source=source.replace(hostUrl,JSON.stringify(pathToFileURL(ownedHost).href));
 }
 const output=path.join(root,'Saved/game-trial-work-20261102/approved-panic-build.generated.mjs');await fs.writeFile(output,source);
 return {build:(await import(pathToFileURL(output))).buildNativeGame,provenance:{player,playerSHA256:createHash('sha256').update(bytes).digest('hex'),builderSource:file,builderSourceSHA256:createHash('sha256').update(await fs.readFile(file)).digest('hex'),sourceOrInstalledSDKModified:false}};
}
