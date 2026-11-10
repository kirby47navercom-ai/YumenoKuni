"""Exercise authored interruptions against the actual Korean host glyphs."""
import json, os, subprocess, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
work = root/'Game/Saved/nonstop-rework-20261105'
work.mkdir(parents=True, exist_ok=True)
subprocess.run([sys.executable, str(root/'tools/test_nonstop_speech.py'), '--fixtures-only'], cwd=root, check=True)
rows = json.loads((root/'data/presentation/nonstop_noise_staging.json').read_text(encoding='utf-8'))['rows']
direction = json.loads((root/'data/v4_story/trial_direction.json').read_text(encoding='utf-8'))
assert {r['id'] for r in rows if not r.get('extra')} == {r['id'] for values in direction['noise'].values() for r in values}
assert all(r['actor'] != r['hostActor'] for r in rows)
assert not {r['task'] for r in rows} & {'T1-NS-A01','T1-NS-A02','T1-NS-A03'}
assert any(r['task']=='T1-NS-A05' for r in rows)
tasks=json.loads((root/'data/v4_story/native_tasks.json').read_text(encoding='utf-8'))['tasks']
for tid, task in tasks.items():
 if task['stage']['kind']!='nonstop' or tid in {'T1-NS-A01','T1-NS-A02','T1-NS-A03'}: continue
 main=task['debate']['lines']+direction['extra'].get(tid,[])
 bound=[r for r in rows if r['task']==tid]
 assert len(bound)>len(main) and {r['host'] for r in bound}=={l['id'] for l in main},tid
 for host in main:
  group=[r for r in bound if r['host']==host['id']]
  assert 1<=len(group)<=3 and sum(len(r['text']) for r in group)<=26,(tid,host['id'])
 assert len({r['text'] for r in bound})==len(bound),tid

fixture = 'struct R{const char *id,*text,*host;int hits;}; R rows[]={\n'
fixture += ',\n'.join('{'+','.join('u8'+json.dumps(r[k], ensure_ascii=False) for k in ('id','text','host'))+','+str(r['hits'])+'}' for r in rows)+'\n};'
code = r'''
#include "../../Source/SilencerV4.hpp"
#include "speech-fixtures.hpp"
#include <cassert>
#include <iostream>
FIXTURE
int main(){for(const char* id:{"T1-NS-A01","T1-NS-A02","T1-NS-A03"})assert(!debate::noiseEnabled(id));assert(debate::noiseEnabled("T1-NS-A05")&&debate::noiseEnabled("T1-NS-T05e")&&debate::noiseEnabled("T1-LIE-01")&&debate::noiseEnabled("T2-NS-A01"));int targetRows=0,blockedRows=0,partials=0;for(const auto& r:rows){
 const Case* host=nullptr;for(const auto& c:cases)if(std::string(c.id)==r.host)host=&c;assert(host);
 debate::Line l;l.id=host->id;l.text=host->text;l.word=host->word;l.kind=host->kind;l.start=host->start;l.performance=host->tone;l.composition=host->cue;l.font=host->font;l.yaw=host->yaw;l.readable=true;
 debate::Line n;n.id=r.id;n.text=r.text;n.kind="noise";n.font="Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf";n.noiseDurability=r.hits;n.noiseFor=0;n.noiseRewardSeconds=2;
 debate::State s;s.lines={l,n};s.noisePool=true;s.noiseAction=2;s.restartRows();const auto cue=debate::noiseCue(n.id,n.text);
 s.time=0;assert(s.noiseIndices().empty());assert(silencerv4::targets(s,silencerv4::Mode::Remote,640,330).empty());assert(silencerv4::targets(s,silencerv4::Mode::Blast,640,330).empty());
 s.time=cue.delay+.4f;auto settled=s.noiseGlyphs(1);s.time=cue.delay+1.0f;auto held=s.noiseGlyphs(1);assert(settled.size()==held.size());for(size_t k=0;k<held.size();++k){assert(settled[k].text==held[k].text);assert(settled[k].x==held[k].x&&settled[k].y==held[k].y&&settled[k].rotation==held[k].rotation);}
 auto anchorX=s.lines[1].noiseAnchorX,anchorY=s.lines[1].noiseAnchorY;s.lines[0].word="";s.bindNoiseAnchors();assert(s.lines[1].noiseAnchorX==anchorX&&s.lines[1].noiseAnchorY==anchorY);s.lines[0].word=l.word;bool visible=false,blocked=false,clear=false;float hitTime=-1;
 for(float t=0;t<debate::duration(l,54)-.01f;t+=.025f){s.time=t;float alpha=0;for(const auto& g:s.current())if(g.text!=" ")alpha=std::max(alpha,g.opacity);for(const auto& g:s.noiseGlyphs(1))if(g.text!=" ")assert(std::abs(g.opacity-alpha)<.0001f);for(const auto& g:s.noise())if(g.opacity>.9f&&g.text!=" "&&g.x>120&&g.x<1160&&g.y>150&&g.y<550){visible=true;hitTime=t;assert(debate::inside(g,g.x,g.y,0));}
  for(const auto& g:s.current())if(g.weak&&g.opacity>.99f&&g.text!=" "){if(s.noiseHit(g.x,g.y))blocked=true;else clear=true;}
 }
 assert(visible);if(!l.word.empty()){++targetRows;if(blocked)++blockedRows;}
 s.time=hitTime;s.noiseAction=cue.minAction-1;assert(s.noiseIndices().empty());s.noiseAction=cue.minAction;assert(!s.noiseIndices().empty());s.noiseAction=2;auto before=s.noiseGlyphs(1);float timer=90;
 auto hit=silencerv4::clear(s,1,timer,100);if(r.hits>1){assert(!hit.changed&&hit.damaged&&timer==90&&!s.silenced[1]);auto after=s.noiseGlyphs(1);assert(after.size()==before.size());int removed=0,kept=0;for(size_t i=0;i<after.size();++i){removed+=before[i].opacity>.3f&&after[i].opacity==0;kept+=after[i].opacity>.3f;}assert(removed>0&&kept>0);hit=silencerv4::clear(s,1,timer,100);++partials;}
 assert(hit.changed&&timer==92&&s.silenced[1]&&s.focus==100&&s.hearts==5);assert(!silencerv4::clear(s,1,timer,100).changed&&timer==92);assert(!s.noiseHit(640,330));
 s.next();assert(s.passes==1&&!s.silenced[1]&&s.noiseDamage[1]==0);s.time=hitTime;assert(!s.noiseIndices().empty());
 }

 // Concurrent rows must fit their real glyph budget and remain separately readable.
 int concurrent=0;
 for(const auto& host:cases){std::vector<const R*> group;for(const auto& r:rows)if(std::string(r.host)==host.id)group.push_back(&r);if(group.size()<2)continue;
  debate::Line l;l.id=host.id;l.text=host.text;l.word=host.word;l.kind=host.kind;l.start=host.start;l.performance=host.tone;l.composition=host.cue;l.font=host.font;l.yaw=host.yaw;l.readable=true;
  debate::State s;s.noisePool=true;s.noiseAction=2;s.lines.push_back(l);for(const auto* r:group){debate::Line n;n.id=r->id;n.text=r->text;n.kind="noise";n.font="Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf";n.noiseFor=0;s.lines.push_back(n);}s.restartRows();s.time=debate::duration(l,54)*.5f;assert(s.noiseIndices().size()==group.size());
  struct Box{float l=9999,t=9999,r=-9999,b=-9999;};std::vector<Box> boxes;
  for(int i=1;i<int(s.lines.size());i++){Box b;for(const auto& g:s.noiseGlyphs(i))if(g.text!=" "){float a=g.rotation*debate::PI/180,hx=std::abs(std::cos(a))*g.halfW+std::abs(std::sin(a))*g.halfH,hy=std::abs(std::sin(a))*g.halfW+std::abs(std::cos(a))*g.halfH;b.l=std::min(b.l,g.x-hx);b.r=std::max(b.r,g.x+hx);b.t=std::min(b.t,g.y-hy);b.b=std::max(b.b,g.y+hy);}boxes.push_back(b);}
  for(int i=0;i<int(boxes.size());i++)for(int j=0;j<i;j++){const auto&a=boxes[i];const auto&b=boxes[j];assert(a.r<b.l||b.r<a.l||a.b<b.t||b.b<a.t);}
  ++concurrent;
 }
 assert(concurrent>0);
 // A long authored Panic interruption cannot vanish into the ordinary
 // 26-glyph concurrent-noise budget and let its next beat pass silently.
 {
  debate::State s;s.noisePool=true;s.authoredPanicBeats=true;
  for(int i=0;i<6;++i){debate::Line l;l.kind="plain";l.id=std::to_string(i);l.text="Observed";s.lines.push_back(l);}
  debate::Line n;n.kind="noise";n.id="long-panic";n.text="A complete authored interruption longer than twenty six glyphs";
  n.noiseLoud=true;n.noiseFor=4;s.lines.push_back(n);
  s.lanes={{0,1},{2,3},{4,5}};s.restartRows();
  assert(s.noiseIndices()==std::vector<int>{6});
  s.tick(100);assert(s.laneAt==std::vector<int>({0,0,0}));
  s.silenced[6]=true;s.tick(.1f);assert(s.laneAt==std::vector<int>({1,1,1}));
 }
 assert(targetRows>0);std::cout<<std::size(rows)<<" rows: distinct speakers, statement-synchronized lifetime, rendered glyph hit, variable 1-3 concurrent responses, all utterances covered with independent placement, partial durability, once-only timer reward, cycle respawn PASS; targetRows="<<targetRows<<" blocked="<<blockedRows<<" partial="<<partials<<"\n";
 // A noise word behind the target must not win simply because it is pink.
 debate::Glyph g;g.x=640;g.y=330;g.depth=700;g.halfW=30;g.halfH=30;g.yaw=12;float z=0;assert(debate::inside(g,640,330,0,&z)&&z>0);assert(!debate::inside(g,100,100,0,&z));
}
'''.replace('FIXTURE', fixture)
(work/'noise-gameplay.cpp').write_text(code, encoding='utf-8')
env = os.environ.copy(); env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
subprocess.run(['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-O2','Game/Saved/nonstop-rework-20261105/noise-gameplay.cpp','-o','Game/Saved/nonstop-rework-20261105/noise-gameplay.exe'],cwd=root,env=env,check=True)
subprocess.run([str(work/'noise-gameplay.exe')],cwd=root,env=env,check=True)
