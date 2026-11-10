"""Compare supplied reference GIF to actual own-game captures, using recorded times."""
from pathlib import Path
import sys,json,math,bisect
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
current=Path(sys.argv[1]); current=current if current.is_absolute() else R/current
old=R/(sys.argv[2] if len(sys.argv)>2 else 'Game/Saved/nonstop-intro-1793209209249')
ref=Image.open('C:/Users/kirby/Downloads/danganronpa-nonstop-debate.gif')
reference=[];times=[];clock=0
for i in range(ref.n_frames):
    ref.seek(i);times.append(clock);reference.append(ref.convert('RGB'));clock+=ref.info.get('duration',30)/1000
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
def data(p):return json.loads((p/'report.json').read_text(encoding='utf-8'))
new,prior=data(current),data(old)
def sample(folder,report,t):
    f=min(report['preview'],key=lambda v:abs(v['elapsed']-t))
    return Image.open(folder/f['file']).convert('RGB').resize((498,280)),f['elapsed']
contact=Image.new('RGB',(1494,8*312+36),'#12121a');d=ImageDraw.Draw(contact)
for j,label in enumerate(['사용자 GIF','이전 실제 실행','수정 실제 실행']):d.text((j*498+8,5),label,font=font,fill='white')
for i,t in enumerate([1.5,1.9,2.3,2.7,3.2,3.7,4.2,4.55]):
    ix=max(0,bisect.bisect_right(times,t)-1)
    images=[(reference[ix].resize((498,280)),times[ix]),sample(old,prior,t),sample(current,new,t)]
    for j,(im,stamp) in enumerate(images):
        contact.paste(im,(j*498,36+i*312));d.text((j*498+8,318+i*312),f'{stamp:.2f}s',font=font,fill='white')
contact.save(current/'reference-before-after.jpg',quality=90)
frames=[Image.open(current/v['file']).convert('RGB').resize((640,360)) for v in new['preview']]
dur=[max(20,round((new['preview'][i+1]['elapsed']-v['elapsed'])*1000)) if i+1<len(frames) else 100 for i,v in enumerate(new['preview'])]
frames[0].save(current/'nonstop-intro-runtime.gif',save_all=True,append_images=frames[1:],duration=dur,loop=0,optimize=False)
def metrics(report,base,width):
    samples=[x for x in report['samples'] if x['elapsed']>1.15]
    rates=[]
    for a,b in zip(samples,samples[1:]):
        dt=b['elapsed']-a['elapsed']
        if dt<=0:continue
        dy=(b['camera'][3]-a['camera'][3]+180)%360-180
        rates.append(abs(dy)/dt)
    return {'actual_camera_yaw_peak_degrees_per_second':max(rates),'camera_yaw_absolute_travel_degrees':sum(abs((b['camera'][3]-a['camera'][3]+180)%360-180) for a,b in zip(samples,samples[1:])),'samples':len(samples),'desk_ring_radius':base,'neighbor_center_distance':2*base*math.sin(math.pi/16),'desk_width':width,'simple_tangential_gap':2*base*math.sin(math.pi/16)-width}
prior_base=math.hypot(prior['samples'][-1]['desks'][0]['position'][0],prior['samples'][-1]['desks'][0]['position'][2])
stats={'before':metrics(prior,5.5 if prior_base>4.8 else 3.95,1.42 if prior_base>4.8 else 1.36),'after':metrics(new,3.95,1.36),'scope':'actual runtime irregular samples; peak is sampled not 60FPS performance proof','reference_seconds':clock}
(current/'motion-comparison.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
print(json.dumps(stats))
slugs='mio rin ken nana taiga ai rei sora haruka sho koto akari riku satsuki yuu kaede'.split()
plan=Image.new('RGB',(760,800),'#111421');d=ImageDraw.Draw(plan)
d.text((24,15),'16자리 배치 / 인물은 자기 의논석 방향 / 홀짝 안팎 이동',font=font,fill='white')
cx,cy,scale=380,410,58
for radius,color in [(3.95,'#5294a8'),(4.08,'#6b647c')]:
    r=radius*scale;d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=color,width=2)
for i,slug in enumerate(slugs):
    a=i*math.pi/8;s,c=math.sin(a),math.cos(a)
    x,y=cx+3.95*scale*s,cy+3.95*scale*c;r=.68*scale
    color='#57cfdf' if i%2==0 else '#d08be5'
    d.ellipse((x-r,y-r,x+r,y+r),outline=color,width=3)
    ax,ay=cx+4.08*scale*s,cy+4.08*scale*c
    d.ellipse((ax-7,ay-7,ax+7,ay+7),fill='white')
    # Arrow from actor toward own station; the actor never tracks the camera.
    ex,ey=ax-.42*scale*s,ay-.42*scale*c;d.line((ax,ay,ex,ey),fill='white',width=2)
    d.text((cx+5.65*scale*s-28,cy+5.65*scale*c-12),f'{i:02} {slug}',font=font,fill=color)
d.text((24,760),'의논석 반경 3.95m · 인물 반경 4.08m · 편차 ±0.24m · 최소 간격 0.181m',font=font,fill='white')
plan.save(current/'seat-layout.png')
