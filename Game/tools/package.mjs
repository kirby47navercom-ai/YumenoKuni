// 배포 묶음 : release 빌드 → dist/YumenoKuni/ 로 복사 + 플레이 안내 + zip
// node tools/package.mjs   (결과 : ../dist/YumenoKuni-날짜.zip)
import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const repo=path.dirname(root);
execFileSync('node',[path.join(root,'tools/build.mjs'),'--release'],{stdio:'inherit',cwd:root});
const built=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const out=path.join(repo,'dist','YumenoKuni');
await fs.rm(out,{recursive:true,force:true});
await fs.cp(built.output,out,{recursive:true});
const exe=path.basename(built.executable);
await fs.writeFile(path.join(out,'유메노쿠니 시작.cmd'),`@echo off\r\ncd /d "%~dp0"\r\nstart "" "${exe}"\r\n`);
await fs.writeFile(path.join(out,'플레이 방법.txt'),[
 '『유메노쿠니』',
 '',
 '시작 : 「유메노쿠니 시작.cmd」 또는 '+exe,
 '',
 '조작',
 ' Enter / Space / 클릭   대사 넘기기, 고르기',
 ' Ctrl (누르고 있기)     빨리 넘기기',
 ' Tab                    래피 패드 (Q/E 로 탭 : 교칙·언령·선물·인연)',
 ' 1~9                    보기 고르기',
 ' G                      프리타임 중 캡슐 머신 (3코인)',
 ' C (타이틀)             이어하기 — 비트마다 자동 저장',
 '',
 '학급 재판',
 ' 마우스 조준, 왼클릭 발사 (길게 누르면 거짓 탄환), 우클릭 소음 제거',
 ' Q/E 언령 바꾸기, Shift 집중',
 '',
 '소리 : audio/cues.json 에 파일을 지정하면 다음 빌드부터 들어갑니다.',
 '',
 '비상업 팬 게임입니다. 글꼴 라이선스는 licenses/ 와 Content 의 각 글꼴 폴더 참고.',
].join('\r\n'));
const zip=path.join(repo,'dist',`YumenoKuni-${new Date().toISOString().slice(0,10)}.zip`);
await fs.rm(zip,{force:true});
execFileSync('tar',['-a','-c','-f',zip,'-C',path.join(repo,'dist'),'YumenoKuni'],{stdio:'inherit'});
console.log(JSON.stringify({folder:out,zip,bytes:(await fs.stat(zip)).size}));
