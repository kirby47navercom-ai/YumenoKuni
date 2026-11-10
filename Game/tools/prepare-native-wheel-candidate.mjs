import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {createHash} from 'node:crypto';
import {jsonInclude} from '../../../engineCreate/tools/prepare-native.mjs';
import {activeInstalledVersions} from '../../../engineCreate/tools/install-editor.mjs';
const exec=promisify(execFile),root=path.resolve(import.meta.dirname,'..'),engine=path.resolve(root,'../../engineCreate'),work=path.join(root,'Saved/native-wheel-candidate-'+Date.now());await fs.mkdir(work,{recursive:true});
const active=await activeInstalledVersions('C:/Users/kirby/HBEngine');assert.equal(active.length,0,'Do not run a native compiler while the user is using an installed engine');
// Match the existing shipping base and preserve unrelated working DPI/fit edits.
const {stdout:source}=await exec('git',['show','23a3359c:native/desktop/HBNativePlayer.cpp'],{cwd:engine,maxBuffer:4*1024*1024});const sha=b=>createHash('sha256').update(b).digest('hex');assert.equal(sha(source),'0d6602ca35db809271e073d3dcb404e956c413867852ad746b7bb528e9ccf1ba');
const anchor='case WM_MOUSEMOVE:if(h->ready)h->pointer(l);return 0;',wheel='case WM_MOUSEWHEEL:if(h->ready){POINT at{short(LOWORD(l)),short(HIWORD(l))};if(ScreenToClient(window,&at)){h->pointer(MAKELPARAM(at.x,at.y));h->write({{"event","input"},{"packet",{{"key","mousewheelaxis"},{"value",std::clamp(double(short(HIWORD(w)))/WHEEL_DELTA,-1.0,1.0)},{"device","mouse"}}}});}}return 0;';assert(source.includes(anchor));
const failure='catch(const std::exception& e){log(e.what());}DWORD code=0;';assert(source.includes(failure));
const candidate=source.replace(anchor,anchor+wheel).replace(failure,'catch(const std::exception& e){failed=true;log(e.what());}DWORD code=0;'),file=path.join(work,'HBNativePlayer.cpp'),binary=path.join(work,'HBNativePlayer.exe');await fs.writeFile(file,candidate);await fs.access(path.join(jsonInclude,'nlohmann/json.hpp'));
const compiler=process.env.CXX||'C:/msys64/ucrt64/bin/g++.exe',env={...process.env,PATH:path.dirname(compiler)+path.delimiter+process.env.PATH};
await exec(compiler,['-std=c++17','-O2','-s','-static','-municode','-mwindows','-I',path.join(engine,'native/include'),'-I',path.join(engine,'native/desktop'),'-I',jsonInclude,path.basename(file),'-o',path.basename(binary),'-ld3d11','-ldxgi','-ld3dcompiler','-lole32','-lshell32','-luuid','-lwindowscodecs','-lcrypt32','-lgdi32','-ldwmapi','-ladvapi32'],{cwd:work,env,windowsHide:true,timeout:240000,maxBuffer:4*1024*1024});
await fs.writeFile(path.join(work,'report.json'),JSON.stringify({work,file,binary,sourceBase:'23a3359c',originalSourceSHA256:sha(source),candidateSourceSHA256:sha(candidate),binarySHA256:sha(await fs.readFile(binary)),activeInstalledVersions:active,engineOriginalOrDistOrInstallationModified:false,scope:'Owned candidate compiled from the exact existing shipping C++ source: WM_MOUSEWHEEL plus failure flag on the already reproduced packet-reader exception. Unrelated working DPI/fit changes excluded. Not installed or shipped.'},null,2));console.log(JSON.stringify({binary,work}));
