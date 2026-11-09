"""Resolve the authorized final obscurer timelines, preserving source depth masks."""
import json, math
from pathlib import Path
import build_v3_armament_layout as layout
ROOT=Path(__file__).resolve().parents[1];BANK=ROOT/'ui/v3_authorized/armament_final'
code=Path(layout.__file__).read_text(encoding='utf8')
code=code[code.index('def build():'):code.index("if __name__=='__main__'")]
code=code.replace('def mainframe(at):','def mainframe(at,extra=0):')
code=code.replace("max(0,at-o['born']),matrix", "max(0,at-o['born'])+extra,matrix")
code=code[:code.index(" (BANK/'layout.json')")]+" return out\n"
code=code.replace("frame=min(age,stops[0]) if stops else age%len(s);frame=min(frame,len(s)-1);result=[]", "frame=source_frame(s,age);result=[]")
def source_frame(seq,age):
 labels={q['name']:i for i,q in enumerate(seq)if q['name']}
 for i,q in enumerate(seq):
  acts=[a for op in q['operations']for a in op.get('decoded',{}).get('actions',[])]
  for a in acts:
   target=labels.get(a.get('strings',[None])[0])if a['name']=='GoToLabel' else a.get('frame')if a['name']=='GotoFrame' else None
   if target is not None and target<i and age>=i:return target+(age-target)%(i-target)
  if any(a['name']=='Stop'for a in acts):return min(age,i)
 return min(age,len(seq)-1)
code=code.replace("if name in ANIMATED_NAMES:out[name]['frames']=[mainframe(i) for i in range(labels.get('fl_in',0),len(seq))]", "out[name]['waitLead']=30;out[name]['waitPeriod']=38 if name=='t_riron_kakusi6' else 792;out[name]['tracks']={'in':[mainframe(i) for i in range(labels['fl_in'],labels['fl_wait'])],'wait':[mainframe(labels['fl_wait'],i) for i in range(out[name]['waitLead']+out[name]['waitPeriod'])],'out':[mainframe(i) for i in range(labels['fl_out'],len(seq))]}")
env={**vars(layout),'BANK':BANK,'source_frame':source_frame};exec(code,env)
out=env['build']();out={k:v for k,v in out.items()if k in ['t_riron_kakusi6','t_riron_kakusi_s6_US']}
(BANK/'frames.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')),encoding='utf8')
print(json.dumps({k:{'frames':{t:len(a)for t,a in v['tracks'].items()},'rects':v['states']['fl_wait']}for k,v in out.items()},ensure_ascii=True)[:3000])
