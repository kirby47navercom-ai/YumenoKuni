"""Own-game editable native UI: three outcomes, action feedback and modest HUD reskin."""
from pathlib import Path
import math, random
from make_nonstop_intro_art import lettering

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'ui/v4/debate_feedback'
OUT.mkdir(parents=True,exist_ok=True)
def svg(name,w,h,body):
    (OUT/(name+'.svg')).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*2}" height="{h*2}" viewBox="0 0 {w} {h}"><title>YumenoKuni original {name}</title>{body}</svg>',encoding='utf8')
def outlined(text,w,h,*args):
    return lettering(text,w,h,*args).replace(f'width="{w}" height="{h}"',f'width="{w*2}" height="{h*2}"',1)
svg('result_white',1,1,'<rect width="1" height="1" fill="#ffffff"/>')
svg('result_black',1,1,'<rect width="1" height="1" fill="#000000"/>')
svg('result_court_dim',1,1,'<rect width="1" height="1" fill="#12051f" fill-opacity="0.5019607843"/>')

for kind,word,color in [('refute','논파','#e94320'),('lie','위증','#bb42ed'),('agree','동의','#22ccff')]:
    (OUT/f'result_{kind}.svg').write_text(outlined(word,900,300,'#fff8eb',color,True),encoding='utf8')
    marks=''.join(f'<path d="M{x} 255l170-220h35L{x+35} 255z" fill="{color}" opacity=".13"/>' for x in range(-150,1500,115))
    # Rabbit crest links the established courtroom ornaments without copying reference pixels.
    crest=f'<g transform="translate(1130 76)" fill="none" stroke="{color}" stroke-width="3"><ellipse cx="32" cy="62" rx="30" ry="24"/><ellipse cx="17" cy="22" rx="8" ry="29" transform="rotate(-13 17 22)"/><ellipse cx="45" cy="22" rx="8" ry="29" transform="rotate(13 45 22)"/><path d="M19 58h4m18 0h4M29 68l4 4 4-4"/></g>'
    pattern={'refute':f'<path d="M-50 248L1340 32" stroke="{color}" stroke-width="8"/>', 'lie':f'<path d="M-40 224L330 90l245 140 185-185 230 163 350-160" fill="none" stroke="{color}" stroke-width="6"/>','agree':f'<g fill="none" stroke="{color}" stroke-width="4" opacity=".6"><ellipse cx="900" cy="140" rx="170" ry="96"/><ellipse cx="1020" cy="140" rx="170" ry="96"/></g>'}[kind]
    svg('result_band_'+kind,1280,280,f'<path d="M0 26L1280 0v252L0 280z" fill="#101329" fill-opacity=".96"/>{marks}{pattern}<path d="M0 26L1280 0M0 280l1280-28" stroke="{color}" stroke-width="3"/>{crest}')
    for i,char in enumerate(word):
        (OUT/f'result_{kind}_glyph{i}.svg').write_text(outlined(char,360,360,'#030308','#ffd32a' if kind=='refute' else color,True),encoding='utf8')
    for i,char in enumerate('Break'):
        (OUT/f'result_{kind}_break{i}.svg').write_text(outlined(char,220,240,color,color),encoding='utf8')
    rng=random.Random(73)
    # Full-canvas brush band: diagonal for refute/perjury, horizontal paired portrait for agreement.
    angle=0 if kind=='agree' else 16
    speed=''.join(f'<path d="M-300 {y}h1880" stroke="{rng.choice(["#ffffff","#040b2c",color])}" stroke-width="{rng.choice([1,2,3])}" opacity="{rng.uniform(.1,.35):.2f}"/>' for y in range(-170,171,5))
    ragged=''.join(f'<path d="M{x} {rng.randint(-205,-185)}l{rng.randint(25,85)} {rng.randint(-12,20)} -25 22 -75 -3z" fill="#03030b"/>' for x in range(-220,1520,58))
    spots=''.join(f'<circle cx="{rng.choice([-20,1240])+rng.randint(-70,70)}" cy="{rng.choice([-185,185])+rng.randint(-25,25)}" r="{rng.randint(3,20)}" fill="#03030b"/>' for _ in range(45))
    svg('result_scene_'+kind,1280,720,f'<g transform="translate(0 360) rotate({angle} 640 0)"><path d="M-300-190H1580V190H-300Z" fill="{color}"/>{speed}<path d="M-300-195H1580M-300 195H1580" stroke="#03030b" stroke-width="26"/>{ragged}<g transform="scale(1 -1)">{ragged}</g>{spots}</g>')
    lines=[];rings=[[],[],[]];origin=(610,340)
    for j in range(13):
        a=j*math.tau/13+rng.uniform(-.13,.13);points=[]
        for k,radius in enumerate([120,340,850]):
            angle=a+rng.uniform(-.12,.12);r=radius*rng.uniform(.85,1.15)
            pt=(origin[0]+r*math.cos(angle),origin[1]+r*math.sin(angle));points.append(pt);rings[k].append(pt)
        lines.append('<path d="M610 340'+''.join(f'L{x:.1f} {y:.1f}' for x,y in points)+'"/>')
    for ring in rings[:2]:
        for j,(x,y) in enumerate(ring):
            nx,ny=ring[(j+1)%len(ring)];lines.append(f'<path d="M{x:.1f} {y:.1f}L{nx:.1f} {ny:.1f}"/>')
    svg('result_crack_'+kind,1280,720,f'<g fill="none" stroke="{color}" stroke-width="8" opacity=".35">{"".join(lines)}</g><g fill="none" stroke="#ffffff" stroke-width="2">{"".join(lines)}</g>')
svg('result_bolt',1280,720,'<g fill="none" stroke="#ffce30" stroke-linejoin="miter"><path d="M700 20L445 390 725 246 565 700M840 60L610 352 895 190 710 600" stroke-width="24" opacity=".2"/><path d="M700 20L445 390 725 246 565 700M840 60L610 352 895 190 710 600" stroke="#fff28a" stroke-width="6"/></g>')
for i in range(6):
    points=[[(9,11),(151,30),(44,153)],[(20,5),(153,108),(61,148)],[(3,44),(119,9),(156,152)],[(7,18),(150,41),(114,154),(35,108)],[(19,4),(157,128),(51,153)],[(4,100),(105,4),(148,126) ]][i]
    poly=' '.join(f'{x},{y}' for x,y in points)
    svg('result_shard'+str(i),160,160,f'<defs><linearGradient id="glass"><stop stop-color="#e9faff" stop-opacity=".55"/><stop offset=".35" stop-color="#5475c0" stop-opacity=".06"/><stop offset="1" stop-color="#9af3ff" stop-opacity=".3"/></linearGradient></defs><polygon points="{poly}" fill="url(#glass)" stroke="#b8efff" stroke-width="1.5"/><path d="M20 36L106 122" stroke="#ffffff" stroke-width="2" opacity=".55"/>')
parts=[]
for i in range(12):
    a=i*math.tau/12+.13*math.sin(i*7);r=180+(i%3)*40;x=640+math.cos(a)*r;y=360+math.sin(a)*r
    shape=(OUT/f'result_shard{i%6}.svg').read_text(encoding='utf8').split('</defs>')[1].split('</svg>')[0]
    parts.append(f'<g transform="translate({x:.1f} {y:.1f}) rotate({i*37}) scale({.55+(i%4)*.13}) translate(-80 -80)">{shape}</g>')
svg('result_shatter',1280,720,'<defs><linearGradient id="glass"><stop stop-color="#e9faff" stop-opacity=".55"/><stop offset=".35" stop-color="#5475c0" stop-opacity=".06"/><stop offset="1" stop-color="#9af3ff" stop-opacity=".3"/></linearGradient></defs>'+''.join(parts))
rng=random.Random(99)
blots=''.join(f'<circle cx="{640+math.cos(a)*r:.1f}" cy="{360+math.sin(a)*r:.1f}" r="{rng.randint(28,120)}"/>' for a,r in [(j*.42,110+(j%5)*34) for j in range(45)])
svg('result_ink',1280,720,f'<g fill="#030207"><circle cx="640" cy="360" r="190"/>{blots}</g>')
svg('focus_veil',1280,720,'<defs><radialGradient id="v"><stop offset=".45" stop-color="#16192f" stop-opacity="0"/><stop offset="1" stop-color="#17133d" stop-opacity=".38"/></radialGradient></defs><rect width="1280" height="720" fill="url(#v)"/><g stroke="#c9b5ff" fill="none" opacity=".6"><path d="M0 80h120l30 30M1280 80h-120l-30 30M0 640h120l30-30M1280 640h-120l-30-30" stroke-width="2"/></g>')
svg('charge_ring',96,96,'<g fill="none" stroke="#bf86ff"><circle cx="48" cy="48" r="41" stroke-width="3" stroke-dasharray="31 12"/><circle cx="48" cy="48" r="31" stroke-width="1.5" opacity=".7"/><path d="M48 0v12m0 72v12M0 48h12m72 0h12" stroke-width="3"/></g>')
for kind,color in [('normal','#ffe5a3'),('lie','#c18bff')]:
    svg('shot_'+kind,280,18,f'<path d="M0 9h235" stroke="{color}" stroke-width="2" opacity=".6"/><path d="M70 9h176" stroke="{color}" stroke-width="7"/><path d="M225 3h35q15 0 20 6-5 6-20 6h-35z" fill="{color}"/><path d="M230 5h30" stroke="#fff9ef" stroke-width="2"/>')
svg('impact',160,160,'<g stroke="#fff0ca" fill="none"><circle cx="80" cy="80" r="53" stroke-width="3"/><path d="M80 0v30m0 100v30M0 80h30m100 0h30M22 22l21 21m74 74 21 21M22 138l21-21m74-74 21-21" stroke-width="4"/></g>')
for name,w,h in [('name',420,80),('status',330,116),('timer',330,64)]:
    svg('own_hud_'+name,w,h,f'<path d="M24 3H{w-4}L{w-24} {h-3}H4Z" fill="#131a31" fill-opacity=".96" stroke="#9b80bc" stroke-width="2"/><path d="M24 3H{w-4}M4 {h-3}h{w-28}" stroke="#d2b572" stroke-width="3"/><path d="M27 17l8 14-2-18 9 18-3 9H22z" fill="#d2b572"/><path d="M14 {h-13}h25M{w-56} 12h34" stroke="#b69adb" stroke-width="2"/>')
print('Own-game debate feedback: refute / lie / agree and3 HUD panels')
