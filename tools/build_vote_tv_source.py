"""Reference-calibrated original voting UI plane, with own world/cast slots."""
import json,hashlib,runpy
from pathlib import Path
from PIL import Image
from v4_character_sources import catalogue
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'ui/v4/vote_tv_source';OUT.mkdir(parents=True,exist_ok=True)
core=runpy.run_path(str(ROOT/'tools/build_trial_input_source_art.py'));g=core['comp'].__globals__;BANK=ROOT/'ui/v3_authorized/trial_inputs';g.update(L=json.loads((BANK/'layout.json').read_text(encoding='utf-8')),M=json.loads((BANK/'manifest.json').read_text(encoding='utf-8')))
records={}
def save(name,im,source):
 p=OUT/(name+'.png');im.save(p);records[name]={'file':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source':source}
def src(family,resource):
 r=core['res'](family,resource);return core['texture'](r['file'],resource).copy()
def main():
 # Existing own 3D enclosure, rendered offline. It is explicitly not claimed
 # as an original UI bitmap. The screen cut-out clips all UI motion to the TV.
 im=Image.open(OUT/'own_tv_model.png').convert('RGBA');background=Image.new('RGBA',(2560,1440),(0,0,0,255));background.alpha_composite(im);background.paste((0,0,0,0),(384,192,2176,1152));save('bezel',background,'Existing own screen_frame world mesh; see own_tv_model.json')
 header=core['comp'](g['L']['t_tohyo_title_US']['states']['fl_wait'],(640,360));header=header.crop(header.getbbox());save('title',header,'t_tohyo_title_US/fl_wait INCLUDING provided Korean t_tohyo_title_tx_JP: 투표 타임')
 save('timer_plate',src('t_tohyo_time','t_tohyo_time_pl_000.png'),'t_tohyo_time_pl_000.png original512x256; native caller calibrated vertical compression')
 save('timer_obi',src('t_tohyo_time','t_tohyo_time_obi_000.png'),'t_tohyo_time_obi_000.png original red strip')
 commit=core['comp'](g['L']['t_tohyo_bt_US']['states']['fl_wait'],(640,360));save('commit',commit.crop(commit.getbbox()),'t_tohyo_bt_US/fl_wait original Korean round vote button')
 portraits={};_,cast=catalogue(hd=True)
 for who in 'mio rin ken nana taiga ai rei sora haruka sho koto akari riku satsuki yuu kaede'.split():
  original=cast[who];im=Image.open(original).convert('RGBA');box=im.getchannel('A').point(lambda p:255 if p>24 else 0).getbbox();assert box
  upper=im.crop((box[0],box[1],box[2],round(box[1]+(box[3]-box[1])*.58)));upper.thumbnail((670,720),Image.Resampling.LANCZOS);canvas=Image.new('RGBA',(670,720));canvas.alpha_composite(upper,((670-upper.width)//2,0));name='upper_'+who;save(name,canvas,original.relative_to(ROOT).as_posix());portraits[who]='Assets/Art/ui/vote_tv_source/'+name+'.png'
 meta={'records':records,'screen':[192,96,896,480],'scale':[.7,2/3],'portrait':[610,0,670,720],'title':[426.666667,0,426.666667,106.666667],'timerPlate':[426.666667,598,426.666667,106.666667],'timerObi':[0,602.666667,1280,85.333333],'commit':[933.333333,576,293.333333,138.666667],'name':[630,468,500,60],'nameRotation':-10,'portraits':portraits,'scope':'UI plane calibrated against original ch4/ch5 actual voting input:4x4 source cards left, own upper-body right, provided Korean marquee, original bulb timer/obi and round button. Source local transforms are mapped to the television display. Silver enclosure is explicitly an existing own-world adapter, not original world pixels. Vote counts/calculation/timing/outcomes unchanged.','references':['Game/Saved/trial-inputs-20261107/reference/09-vote-ch4-input-6646.png','Game/Saved/trial-inputs-20261107/reference/09-vote-ch5-selection-7256.png'],'sourceFrame64Role':'RGB0, alpha4..255 black edge mask; not the silver 3D television bezel.'}
 (OUT/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8');print('VOTE_TV_SOURCE',len(records))
if __name__=='__main__':main()
