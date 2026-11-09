// 배포 묶음: release 빌드를 보존하고 dist/YumenoKuni에 불변 파일을 공유해 내보낸다.
// 실행 파일은 엔진이 제품 이름을 찍은 HBGame_<프로젝트 ID>.exe (이름은 엔진의 창·저장 식별 규칙이라 바꾸지 않는다).
// node tools/package.mjs   (결과 : ../dist/YumenoKuni/, ../dist/YumenoKuni-날짜.zip)
import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {exportPackage} from './package-output.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const repo=path.dirname(root);
const resultFile=path.join(root,'build-result.json');
execFileSync('node',[path.join(root,'tools/build.mjs'),'--release'],{stdio:'inherit',cwd:root});
const built=JSON.parse(await fs.readFile(resultFile,'utf8'));
// Keep build-result pointing to the retained release build; export immutable files by hardlink.
console.log(JSON.stringify(await exportPackage(repo,built,{zip:!process.argv.includes('--no-zip')})));
