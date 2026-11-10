"""Source-exact, editable V4 comparison documents and existing-world plan.

The 16/17 delivery originals are preserved. These are player inspection aids,
not a newly discovered document, sensor result, or private-question disclosure.
"""
from pathlib import Path
import hashlib,json
from html import escape
from PIL import Image,ImageDraw,ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'ui/v4/documents_v4_runtime'
FONT=ROOT/'fonts/pretendard/Pretendard-Regular.otf'
W,H,S=1600,1000,2
PAPER,INK,MUTED,BORDER='#f3ead9','#29232e','#68616c','#b9ab9a'


class Drawing:
    def __init__(self):
        self.parts=[];self.im=Image.new('RGB',(W*S,H*S),PAPER);self.draw=ImageDraw.Draw(self.im)
        self.font=TTFont(FONT);self.glyphs=self.font.getGlyphSet();self.cmap=self.font.getBestCmap();self.upm=self.font['head'].unitsPerEm
    def box(self,x,y,w,h,fill=PAPER,stroke=BORDER,width=2):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
        self.draw.rectangle((x*S,y*S,(x+w)*S,(y+h)*S),fill=fill,outline=stroke,width=width*S)
    def line(self,points,fill=INK,width=2):
        self.parts.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in points)+f'" fill="none" stroke="{fill}" stroke-width="{width}"/>')
        self.draw.line([(x*S,y*S) for x,y in points],fill=fill,width=width*S)
    def text(self,x,y,text,size=30,fill=INK):
        font=ImageFont.truetype(str(FONT),size*S);self.draw.text((x*S,y*S),text,font=font,fill=fill,anchor='ls')
        scale=size/self.upm;cursor=x;paths=[]
        for c in text:
            name=self.cmap.get(ord(c))
            if name is None: raise ValueError('Unrenderable source character '+c)
            pen=SVGPathPen(self.glyphs);self.glyphs[name].draw(pen)
            paths.append(f'<path transform="translate({cursor},{y}) scale({scale},-{scale})" d="{pen.getCommands()}"/>')
            cursor+=self.glyphs[name].width*scale
        self.parts.append(f'<g data-label="{escape(text,quote=True)}" fill="{fill}">'+''.join(paths)+'</g>')
    def save(self,name):
        p=OUT/name
        p.with_suffix('.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*S}" height="{H*S}" viewBox="0 0 {W} {H}">'+''.join(self.parts)+'</svg>\n',encoding='utf-8')
        self.im.save(p.with_suffix('.webp'),'WEBP',lossless=True,method=6)
        return p.with_suffix('.webp').relative_to(ROOT).as_posix()


def proof(prefix,line,quote):
    p=next((ROOT/'docs/design/rewrite_v4').glob(prefix+'_*.md'));text=p.read_text(encoding='utf-8-sig')
    if quote not in text.splitlines()[line-1]: raise ValueError(f'Changed source {p.name}:{line}')
    return {'file':p.name,'line':line,'quote':quote,'sha256':hashlib.sha256(text.encode()).hexdigest()}


def polygon(x,y,w,h):
    return [[x/W,y/H],[(x+w)/W,y/H],[(x+w)/W,(y+h)/H],[x/W,(y+h)/H]]


def make():
    OUT.mkdir(parents=True,exist_ok=True)
    sources=[proof('11a3',360,'접속 시험 미완료'),proof('11a3',374,'통신 준비 완료'),proof('11a3',454,'통신 확인 안 됨, 원인 조사 중'),proof('11b',579,'작동 확인 불가'),proof('181',746,'작동 확인 칸/정상 보고 칸/개인 질문 부록/종이 번호')]
    d=Drawing();d.text(80,88,'확인한 자료',42);d.text(80,137,'작동 확인 · 공용 점검표 · 수정본',26,MUTED)
    d.box(80,195,680,270);d.text(110,246,'작동 확인',27);d.text(110,330,'접속 시험 미완료',42)
    d.box(840,195,680,270);d.text(870,246,'공용 점검표',27);d.text(870,330,'통신 준비 완료',42)
    d.box(80,510,680,390);d.text(110,565,'수정본 / 최종 보고서',27);d.text(110,642,'통신 확인 안 됨,',36);d.text(110,695,'원인 조사 중',36);d.text(110,786,'17',42);d.text(220,786,'작동 확인 불가',36)
    # An unopened fold, never the private question text.
    d.box(840,510,680,390);d.text(870,565,'개인 질문 부록',27);d.box(980,625,400,190);d.line([(980,625),(1180,710),(1380,625)],BORDER,3)
    image=d.save('contact_state_comparison')
    compare={'image':image,'coordinateSystem':'normalized-image-uv','answerRegionId':'normal-report','regions':[{'id':'operation-check','label':'작동 확인 칸','polygon':polygon(80,195,680,270),'correct':False},{'id':'normal-report','label':'정상 보고 칸','polygon':polygon(840,195,680,270),'correct':True},{'id':'private-appendix','label':'개인 질문 부록','polygon':polygon(840,510,680,390),'correct':False,'wrongVariant':'appendix'},{'id':'paper-number','label':'종이 번호','polygon':polygon(95,735,120,85),'correct':False}], 'source':sources,'notNewEvidence':True,'privateContentsShown':False,'notes':'Only verbatim already-observed fields. Comparison arrangement is UI, not an invented in-world original or a disclosed private question.'}
    world_path=ROOT/'art/space_v4/runtime_v1/world.json';world=json.loads(world_path.read_text(encoding='utf-8'))['spaces']['service_lounge'];targets={t['id']:t['p'] for t in world['targets']}
    d=Drawing();d.text(80,88,'직원 휴게실',42);d.text(80,137,'확인한 출입구와 고정 창',26,MUTED)
    # World x/z -> plan coordinates. A/B/window/print positions come from the
    # authored model. No alternate door, witness coordinate or route is added.
    x0,z0,x1,z1=world['bounds'];left,top,rw,rh=300,220,900,640
    d.box(left,top,rw,rh,stroke=INK,width=5)
    def pos(name):
        x,_,z=targets[name];return left+(x-x0)/(x1-x0)*rw,top+(z-z0)/(z1-z0)*rh
    regions=[]
    for key,label,width in [('door_A','전면 문 A',210),('door_B','뒤 보수문 B',225),('fixed_window','고정 창',175),('printer','프린터',150)]:
        x,y=pos(key);y=max(top+15,min(top+rh-75,y-25));x=max(left+10,min(left+rw-width-10,x-width/2))
        d.box(x,y,width,60,fill=PAPER,stroke=INK,width=2);d.text(x+16,y+42,label,28)
        regions.append({'id':key,'label':label,'polygon':polygon(x,y,width,60),'correct':key=='door_A'})
    image=d.save('service_lounge_access_plan')
    plan={'image':image,'coordinateSystem':'normalized-image-uv','answerRegionId':'door_A','regions':regions,'sourceWorld':'art/space_v4/runtime_v1/world.json','worldSha256':hashlib.sha256(world_path.read_bytes()).hexdigest(),'sourceTargets':targets,'notNewEvidence':True,'worldProjection':'x/z, exact existing room bounds and four existing targets; no witness positions or new opening'}
    (OUT/'manifest.json').write_text(json.dumps({'schemaVersion':1,'comparison':compare,'accessPlan':plan,'preservedOriginals':['ui/v4/documents_hd/report_16_excerpt.webp','ui/v4/documents_hd/report_17_excerpt.webp'],'rasterSize':[W*S,H*S],'vectorText':'real Pretendard glyph outlines; editable source script and SVG data-label strings'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'documents':2,'originalsPreserved':True,'output':str(OUT)},ensure_ascii=False))


if __name__=='__main__':make()
