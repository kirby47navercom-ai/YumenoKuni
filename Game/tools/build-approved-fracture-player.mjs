import fs from 'node:fs/promises';
import path from 'node:path';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {createHash} from 'node:crypto';
const game=path.resolve(import.meta.dirname,'..'),engine=path.resolve(game,'../../engineCreate');
const inputTrace=process.argv.includes('--input-trace');
const out=path.join(game,'Saved/game-trial-work-20261102/'+(inputTrace?'fracture-input-trace-20261106':'fracture-player-20261106')),exec=promisify(execFile),hash=b=>createHash('sha256').update(b).digest('hex');
await fs.mkdir(out,{recursive:true});
const headerPath='C:/Users/kirby/HBEngine/Versions/2d39ca554b5790b2/native/desktop/NativeWidgetWindow.hpp';
const original=await fs.readFile(headerPath,'utf8');
const header=original.replace('    double decodeMS=0,presentMS=0;','    double decodeMS=0,presentMS=0;\n    const std::vector<BYTE>& ownedPixels()const{return pixels;}\n    unsigned pixelWidth()const{return width;}unsigned pixelHeight()const{return height;}');
if(header===original)throw Error('Review installed UI header accessor point');
await fs.writeFile(path.join(out,'NativeWidgetWindow.hpp'),header);
let source=await fs.readFile(path.join(engine,'native/desktop/HBNativePlayer.cpp'),'utf8');
source=source.replace('#include "SceneRenderBridge.hpp"','#include '+JSON.stringify(path.join(engine,'native/desktop/SceneRenderBridge.hpp').replaceAll('\\','/')))
 .replace('#include "NativeWidgetWindow.hpp"','#include "NativeWidgetWindow.hpp"');
if(inputTrace){
 source=source.replace('void releaseMouse(){const auto held=','void releaseMouse(){log("QA_INPUT releaseMouse");const auto held=')
  .replace('const std::string& device="keyboard"){inputQueue.push','const std::string& device="keyboard"){if(device=="mouse")log("QA_INPUT key "+key+" "+std::to_string(down));inputQueue.push')
  .replace('case WM_CAPTURECHANGED:','case WM_CAPTURECHANGED:h->log("QA_INPUT WM_CAPTURECHANGED");')
  .replace('case WM_KILLFOCUS:','case WM_KILLFOCUS:h->log("QA_INPUT WM_KILLFOCUS");')
  .replace('case WM_CANCELMODE:','case WM_CANCELMODE:h->log("QA_INPUT WM_CANCELMODE");');
}
await fs.writeFile(path.join(out,'HBNativePlayer.cpp'),source);
const compiler='C:/msys64/ucrt64/bin/g++.exe',player=path.join(out,'HBNativePlayer.exe'),shaders=path.join(out,'panic-render-player-build/Shaders');
const files=['native/desktop/HBNativePlayer.cpp','native/desktop/ScreenFracture.hpp','native/desktop/SceneRenderBridge.hpp','native/desktop/NativeWidgetWindow.hpp','native/include/HBEngine/SceneRender.hpp','tools/native-game-runner.mjs'];
const sourceSHA256={};for(const f of files)sourceSHA256[f]=hash(await fs.readFile(path.join(engine,f)));
await exec(compiler,['-std=c++17','-O2','-s','-static','-municode','-mwindows','-I',path.join(engine,'native/include'),'-I',path.join(engine,'native/build/deps'),'-I',path.join(engine,'native/desktop'),path.join(out,'HBNativePlayer.cpp'),'-o',path.relative(engine,player).replaceAll('\\','/'),'-ld3d11','-ldxgi','-ld3dcompiler','-lole32','-lshell32','-luuid','-lwindowscodecs','-lcrypt32','-lgdi32','-ldwmapi','-ladvapi32','-lzstd'],{cwd:engine,windowsHide:true,timeout:240000,maxBuffer:2000000,env:{...process.env,PATH:path.dirname(compiler)+path.delimiter+process.env.PATH}});
await fs.mkdir(shaders,{recursive:true});await exec(player,['--prepare-shaders',shaders],{windowsHide:true,timeout:120000,maxBuffer:1000000});
for(const f of files)if(hash(await fs.readFile(path.join(engine,f)))!==sourceSHA256[f])throw Error('Engine source changed while compiling '+f);
await fs.writeFile(path.join(out,'receipt.json'),JSON.stringify({player,playerSHA256:hash(await fs.readFile(player)),inputTrace,privateHostSHA256:hash(source),sourceSHA256,uiTransport:{source:headerPath,sourceSHA256:hash(original),adapter:'Existing raw/tile transport, only read-only owned-pixel accessors added to private build copy; installed SDK unchanged'},authorization:'User: 화면 파손 기능에 한해 허용',shaders},null,2));
console.log(player);
