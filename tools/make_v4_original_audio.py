"""Deterministic original DSP cues/ambience. No API, recordings, voice clone or borrowed music."""
from pathlib import Path
import numpy as np,math,json,wave,hashlib,subprocess,shutil
R=Path(__file__).resolve().parents[1];O=R/'audio/v4_original';O.mkdir(parents=True,exist_ok=True)
SR=48000;rng=np.random.default_rng(428017);records=[]
def noise(n,lo,hi):
 f=np.fft.rfftfreq(n,1/SR);spec=np.fft.rfft(rng.normal(size=n));mask=(f>=lo)&(f<=hi);x=np.fft.irfft(spec*mask,n=n);return x/(np.std(x)+1e-9)
def pulse(sec,tones,decay=12,broad=.1):
 t=np.arange(round(sec*SR))/SR;n=len(t);x=sum(a*np.sin(2*np.pi*f*t)*np.exp(-t*d) for f,a,d in tones)
 return (x+broad*noise(n,300,9000)*np.exp(-t*decay))*np.minimum(1,t/.003)
def save(ident,x,use,loop=False,target=-19):
 x=np.asarray(x,dtype=float);x-=x.mean()
 rms=np.sqrt(np.mean(x*x));x*=10**(target/20)/(rms+1e-12);x*=min(1,.70/(np.max(np.abs(x))+1e-9))
 if not loop:
  fade=min(512,len(x)//8);x[:fade]*=np.linspace(0,1,fade);x[-fade:]*=np.linspace(1,0,fade)
 # Very small, fixed interaural delay for ambience only; periodic roll preserves loops.
 stereo=np.stack([x,np.roll(x,13) if loop else x],axis=1);raw=np.round(stereo*32767).astype('<i2');p=O/(ident+'.wav')
 with wave.open(str(p),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(raw.tobytes())
 q=p.with_suffix('.ogg');subprocess.run([shutil.which('ffmpeg'),'-y','-loglevel','error','-i',str(p),'-c:a','libvorbis','-q:a','5',str(q)],check=True)
 entry={'id':ident,'file':p.relative_to(R).as_posix(),'ogg':q.relative_to(R).as_posix(),'source':'original deterministic synthesis in tools/make_v4_original_audio.py','usage':use,'sample_rate':SR,'channels':2,'samples':len(x),'duration_seconds':len(x)/SR,'peak_dbfs':round(20*np.log10(np.max(np.abs(x))+1e-12),3),'rms_dbfs':round(20*np.log10(np.sqrt(np.mean(x*x))+1e-12),3),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'loop':{'start_sample':0,'end_sample_exclusive':len(x),'seam_delta':float(abs(x[-1]-x[0]))} if loop else None,'runtime_integrated':False}
 assert entry['peak_dbfs']<=-3
 if loop:assert entry['loop']['seam_delta']<.035,ident
 records.append(entry)

save('clock_tick',pulse(.18,[(1800,.4,55),(3900,.15,70)],90,.3),'quiet wall clock: trigger once per actual timer second, never use as universal BGM',target=-28)
save('clock_tock',pulse(.2,[(1250,.4,45),(3100,.16,65)],80,.3),'alternate clock tick, same clock source',target=-28)
save('distant_bell',pulse(4.8,[(523.25,.48,.9),(1048,.2,1.5),(1537,.1,2.1),(2725,.07,3)],16,.015),'single original offscreen bell resonance; no borrowed melody',target=-25)
save('musicbox_single',pulse(2.8,[(783.99,.3,1.8),(1576,.12,3),(2359,.05,5)],20,.01),'one original toy-music-box pluck; authored sequence separate',target=-27)
for label,low,hi,thump in [('tile',1000,6500,160),('wood',250,2800,95),('metal',1700,11000,250),('cloth',300,2500,75)]:
 for var in [1,2]:
  x=pulse(.36,[(thump*(1+.03*var),.7,28)],40,.65);x+=noise(len(x),low,hi)*np.exp(-np.arange(len(x))/SR*32)*.2
  save(f'footstep_{label}_{var}',x,f'{label} footstep variation; trigger foot-contact event, alternate without machine-gun repetition',target=-22)
for ident,freq,use in [('ui_focus',880,'focus CHANGED event only, never every frame'),('ui_confirm',1174,'accepted decision after permission check'),('ui_cancel',587,'return/back accepted'),('ui_reject',220,'disabled/invalid request rejected, no state advance'),('evidence_acquired',1568,'first acquisition complete, not hover'),('evidence_revised',1047,'same evidence version updated, not duplicated acquisition')]:
 save(ident,pulse(.24,[(freq,.45,18),(freq*1.5,.10,26)],30,.03),use,target=-24)
save('paper_turn',pulse(.48,[],8,.7),'page-turn start; throttle on fast backlog scrolling',target=-25)
save('paper_insert',pulse(.3,[(430,.1,25)],16,.6),'comic piece successfully inserted after placement validation',target=-24)
save('cloth_rustle',pulse(.65,[],6,.6),'clothing/brace handling; no gore implication',target=-28)
save('metal_latch_release',pulse(.27,[(950,.4,32),(2100,.2,48)],48,.45),'external latch-release animation contact',target=-21)
save('metal_latch_close',pulse(.30,[(640,.5,30),(1840,.2,42)],32,.4),'latch seats, after closed pose actually reached',target=-21)
save('door_wood_close',pulse(.55,[(92,.65,13),(190,.18,19)],16,.35),'door-leaf close contact, not open permission event',target=-21)
save('door_hinge',pulse(1.1,[(380,.22,2.5),(567,.08,4)],10,.05),'quiet stylized hinge movement, trim/fade on interrupted animation',target=-30)
save('ink_impact',pulse(.55,[(70,.6,12),(144,.14,22)],24,.6),'single decisive hit feedback, never overwrite logical hit test',target=-19)
save('ink_slice',pulse(.32,[(1500,.10,18)],18,.8),'single ink slash gesture, no real injury sound',target=-22)
save('miss_brush',pulse(.35,[(390,.13,18)],18,.35),'non-hit deflection, distinct from successful impact',target=-25)
save('memory_scan',pulse(.95,[(370,.17,2),(742,.08,4)],8,.05),'one rewind/readback transition, no extra use or success claim',target=-28)
save('camera_shutter',pulse(.16,[(1400,.14,65)],75,.55),'physical camera shutter only when story permits real capture',target=-24)
for ident,low,hi,use in [('room_air',40,600,'quiet occupied interior air'),('outside_wind',45,2100,'park air, no implied live machinery'),('machine_hum',45,220,'powered maintenance equipment, stop when disconnected')]:
 n=SR*16;t=np.arange(n)/SR;x=noise(n,low,hi)*(.75+.10*np.cos(2*np.pi*t/8))
 if ident=='machine_hum':x+=.28*np.sin(2*np.pi*60*t)+.13*np.sin(2*np.pi*120*t)
 save('amb_'+ident,x,use,True,-36)
n=SR*16;t=np.arange(n)/SR;x=noise(n,200,6500)*(.62+.11*np.sin(2*np.pi*t/4))+.18*noise(n,100,700)
save('amb_water_flow',x,'actual running-water emitter only. Dry fountain MUST NOT receive this cue; use existing recorded fountain-speaker story cue separately.',True,-31)
(O/'manifest.json').write_text(json.dumps({'authoring':'original local DSP, no external/paid request','license':'Original project-authored generated sound, no third-party recording or composition','assets':records,'voice_or_music_claim':'No character voice or full soundtrack fabricated; supplied music remains separate','runtime_integrated':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Created',len(records),'original WAV/OGG cues, peak/loop checks PASS')
