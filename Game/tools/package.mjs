// 배포 묶음 : 엔진 패키징(release 빌드)의 결과 폴더를 그대로 dist/YumenoKuni 로 옮기고 zip 으로 묶는다.
// 실행 파일은 엔진이 제품 이름을 찍은 HBGame_<프로젝트 ID>.exe (이름은 엔진의 창·저장 식별 규칙이라 바꾸지 않는다).
// node tools/package.mjs   (결과 : ../dist/YumenoKuni/, ../dist/YumenoKuni-날짜.zip)
import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const repo=path.dirname(root);
const resultFile=path.join(root,'build-result.json');
const devResult=await fs.readFile(resultFile,'utf8').catch(()=>null); // 개발 빌드 기록(검증 스크립트가 쓴다)은 되돌려 둔다
execFileSync('node',[path.join(root,'tools/build.mjs'),'--release'],{stdio:'inherit',cwd:root});
const built=JSON.parse(await fs.readFile(resultFile,'utf8'));
if(devResult)await fs.writeFile(resultFile,devResult);
const out=path.join(repo,'dist','YumenoKuni');
await fs.rm(path.join(repo,'dist'),{recursive:true,force:true});
await fs.mkdir(path.dirname(out),{recursive:true});
await fs.rename(built.output,out);
const zip=path.join(repo,'dist',`YumenoKuni-${new Date().toISOString().slice(0,10)}.zip`);
execFileSync(process.platform==='win32'?'C:/Windows/System32/tar.exe':'tar',['-a','-c','-f',zip,'-C',path.join(repo,'dist'),'YumenoKuni'],{stdio:'inherit'});
console.log(JSON.stringify({folder:out,executable:path.join(out,path.basename(built.executable)),zip,bytes:(await fs.stat(zip)).size}));
