// Rebuild only the previously approved multiview player into this game's Saved.
// The source engine and installed SDK remain read-only.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import os from 'node:os';
const root=path.resolve(import.meta.dirname,'..'),engineRoot=path.resolve(root,'../../engineCreate'),work=path.join(root,'Saved/game-trial-work-20261102'),build=path.join(work,'panic-render-player-build');
const versions=path.join(os.homedir(),'HBEngine/Versions'),installed=(await fs.readdir(versions,{withFileTypes:true})).filter(e=>e.isDirectory());assert.equal(installed.length,1,'Select the exact installed raw UI transport version');
const installedRoot=path.join(versions,installed[0].name),header=path.join(installedRoot,'native/desktop/NativeWidgetWindow.hpp'),source=path.join(engineRoot,'native/desktop/HBNativePlayer.cpp');
const cpp=await fs.readFile(source,'utf8'),needle='#include "NativeWidgetWindow.hpp"';assert.equal(cpp.split(needle).length,2);
const bridge=await fs.readFile(path.join(engineRoot,'native/desktop/SceneRenderBridge.hpp'),'utf8');assert(bridge.includes('renderViews.resize(views.size())')&&bridge.includes('compositeView'));
const ui=await fs.readFile(header,'utf8');assert(ui.includes('updateRaw(')&&ui.includes('updateRawTiles('),'Match the already installed raw/tile UI transport');
await fs.mkdir(build,{recursive:true});const adapted=path.join(build,'HBNativePlayer.cpp');await fs.writeFile(adapted,cpp.replace(needle,'#include '+JSON.stringify(header.replaceAll('\\','/'))));
const compiler=process.env.CXX||'C:/msys64/ucrt64/bin/g++.exe',env={...process.env,PATH:path.dirname(compiler)+path.delimiter+process.env.PATH};
const {jsonInclude}=await import(pathToFileURL(path.join(engineRoot,'tools/prepare-native.mjs')));await fs.access(path.join(jsonInclude,'nlohmann/json.hpp'));
const binary=path.join(work,'panic-render-player-20261104.exe'),exec=promisify(execFile);
const args=['-std=c++17','-O2','-s','-static','-municode','-mwindows','-I',path.join(engineRoot,'native/include'),'-I',jsonInclude,'-I',path.join(engineRoot,'native/desktop'),adapted,'-o',binary,...['d3d11','dxgi','d3dcompiler','ole32','shell32','uuid','windowscodecs','crypt32','gdi32','dwmapi','advapi32','zstd'].map(n=>'-l'+n)];
await exec(compiler,args,{cwd:engineRoot,env,windowsHide:true,timeout:240000,maxBuffer:4194304});
await exec(binary,['--prepare-shaders',path.join(build,'Shaders')],{cwd:build,env,windowsHide:true,timeout:120000,maxBuffer:1000000});
const hash=b=>createHash('sha256').update(b).digest('hex'),bytes=await fs.readFile(binary);assert(bytes.includes(Buffer.from('Render view count invalid')));
const receipt={binary,binarySHA256:hash(bytes),compiler,args,source,sourceSHA256:hash(Buffer.from(cpp)),rawUIHeader:header,rawUIHeaderSHA256:hash(Buffer.from(ui)),bridgeSHA256:hash(Buffer.from(bridge)),sourceOrInstalledSDKModified:false,scope:'Existing approved renderViews feature, compiled into game-owned Saved with the installed raw UI header. No general engine change or whole-game acceptance.'};
await fs.writeFile(path.join(build,'compile-receipt.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify(receipt));
