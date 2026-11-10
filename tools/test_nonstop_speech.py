"""Exercise actual authored Korean utterances through the C++ speech renderer."""
import json, os, re, subprocess, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
work = root / 'Game/Saved/nonstop-rework-20261105'
work.mkdir(parents=True, exist_ok=True)
data = root / 'data/v4_story'
tasks = json.loads((data / 'native_tasks.json').read_text(encoding='utf-8'))['tasks']
direction = json.loads((data / 'trial_direction.json').read_text(encoding='utf-8'))
source = (root / 'Game/Source/Yumeno.cpp').read_text(encoding='utf-8')
voices = {m[0]: m[1] for m in re.findall(r'\{"(\w+)",\{"([^"\n]+\.(?:ttf|otf))","([^"\n]+\.(?:ttf|otf))"\}\}', source)}
cases = []
for tid, task in tasks.items():
    if task['stage']['kind'] != 'nonstop':
        continue
    for row in task['debate']['lines'] + direction['extra'].get(tid, []):
        entry = direction['debate'][row['id']]
        tone, cue, follow, phase, shot, yaw, font = entry['acting'].split('|')
        text, word, kind = row['text'], '', row.get('kind', 'plain')
        if row.get('weak'):
            word = row['weak']['word']
        if kind == 'agree':
            word = row.get('agreeTarget', {}).get('word', text)
        if entry.get('decoy'):
            kind, word = entry['decoy']['kind'], entry['decoy']['word']
        if kind == 'agree' and tid[1] == '1':
            kind = 'weak'
            if not entry.get('decoy'):
                text, word = entry['openingRefutation']['text'], entry['openingRefutation']['word']
        assert len(text) <= 48 and (not word or word in text), row['id']
        strings = [row['id'], text, word, kind, tone, cue, 'Assets/Fonts/' + (font or voices[row['actor']])]
        cases.append('{' + ','.join('u8' + json.dumps(s, ensure_ascii=False) for s in strings) + ',' + str(text.find(word) if word else 0) + ',' + yaw + '}')
fixture = 'struct Case{const char *id,*text,*word,*kind,*tone,*cue,*font;int start;float yaw;};\nCase cases[]={\n' + ',\n'.join(cases) + '\n};\n'
(work / 'speech-fixtures.hpp').write_text(fixture, encoding='utf-8')
if '--fixtures-only' in sys.argv:
    print('Generated current Korean host fixtures:', len(cases))
    sys.exit(0)
test = r'''
#include "../../Source/Debate.hpp"
#include "speech-fixtures.hpp"
#include <iostream>
int main(){int frames=0;for(const auto& c:cases){debate::Line l;l.text=c.text;l.word=c.word;l.kind=c.kind;l.start=c.start;l.performance=c.tone;l.composition=c.cue;l.font=c.font;l.yaw=c.yaw;l.readable=true;l.size=1.12f;
 for(float t:{.25f,.4f,.55f,.72f,.88f}){for(const auto& g:debate::place(l,t,1,54)){if(g.text==" ")continue;
  if(g.opacity<.99f||g.x-g.halfW<90||g.x+g.halfW>1190||g.y-g.halfH<120||g.y+g.halfH>560||!debate::inside(g,g.x,g.y,0)){std::cerr<<c.id<<" "<<c.cue<<" t="<<t<<" xy="<<g.x<<","<<g.y<<" half="<<g.halfW<<","<<g.halfH<<" alpha="<<g.opacity<<"\n";return 1;}}
  ++frames;}
 for(float t:{.4799f,.8099f,.9399f}){auto a=debate::place(l,t,1,54),b=debate::place(l,t+.0002f,1,54);for(size_t i=0;i<a.size();++i)if(std::hypot(a[i].x-b[i].x,a[i].y-b[i].y)>.2f){std::cerr<<c.id<<" discontinuity "<<t<<"\n";return 1;}}
 }std::cout<<"Actual Korean utterances="<<std::size(cases)<<" readable frames="<<frames<<"; bounds, visibility, rotated-plane aim and continuity PASS\n";}
'''
(work / 'speech-content-test.cpp').write_text(test, encoding='utf-8')
compiler = Path('C:/msys64/ucrt64/bin/g++.exe')
env = dict(os.environ, PATH=str(compiler.parent) + os.pathsep + os.environ.get('PATH', ''))
subprocess.run([str(compiler), '-std=c++17', str((work / 'speech-content-test.cpp').relative_to(root)), '-o', str((work / 'speech-content-test.exe').relative_to(root))], check=True, env=env, cwd=root)
subprocess.run([str(work / 'speech-content-test.exe')], check=True, env=env)
