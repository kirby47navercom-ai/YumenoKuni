"""Synchronize the compact save point; never re-paste historical handoffs."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
latest=ROOT/'docs/analysis/v3_rebuild/UI_교정_재개점_20261030.md'
current=(ROOT/'CODEX_HANDOFF.md').read_text(encoding='utf-8')
match=re.search(r'`(docs/analysis/v3_rebuild/history/[^`]+/CODEX_HANDOFF.md)`',current)
archive=match.group(1) if match else 'docs/analysis/v3_rebuild/history/handoff_20261030_145446/CODEX_HANDOFF.md'
(ROOT/'CODEX_HANDOFF.md').write_text(latest.read_text(encoding='utf-8')+'\n과거 상세 기록: `'+archive+'`\n',encoding='utf-8')
result=json.loads((ROOT/'Game/build-result.json').read_text(encoding='utf-8'))
build=Path(result['executable']).parent.name
begin='<!-- V3_CURRENT_BEGIN -->';end='<!-- V3_CURRENT_END -->'
for name in ['HANDOFF.md','DEBUG_HANDOFF.md']:
 p=ROOT/name;text=p.read_text(encoding='utf-8');assert text.count(begin)==text.count(end)==1
 a=text.index(begin)+len(begin);b=text.index(end,a)
 text=text[:a]+'\n마지막 생성 성공 패키지: `'+build+'`. 실제 실행 합격 범위/진행 중 수정/다음 작업은 `CODEX_HANDOFF.md`의 현재 재개점을 따라요.\n'+text[b:]
 p.write_text(text,encoding='utf-8')
