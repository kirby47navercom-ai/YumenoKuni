"""Author original editable UI plates; no Game data or old assets are overwritten."""
from pathlib import Path
import json,os
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / os.environ.get('V4_UI_OUT','ui/v4/batch01')
SCALE = int(os.environ.get('V4_UI_SCALE','2'))
assert SCALE in (2,4)
OUT.mkdir(parents=True, exist_ok=True)
INK, PAPER, RED, VIOLET, GREY = '#14131b', '#f3ead9', '#d34c66', '#9770cf', '#77737f'
records = []


class Plate:
    def __init__(self, name, w, h, text_rect=None):
        self.name, self.w, self.h = name, w, h
        self.text_rect = text_rect
        self.im = Image.new('RGBA', (w * SCALE, h * SCALE))
        self.draw = ImageDraw.Draw(self.im)
        self.svg = []

    def poly(self, pts, color):
        self.draw.polygon([(round(x*SCALE), round(y*SCALE)) for x, y in pts], fill=color)
        self.svg.append('<polygon points="' + ' '.join(f'{x},{y}' for x,y in pts) + f'" fill="{color}"/>')

    def line(self, pts, color, width=1):
        self.draw.line([(round(x*SCALE), round(y*SCALE)) for x,y in pts], fill=color, width=round(width*SCALE))
        self.svg.append('<polyline points="' + ' '.join(f'{x},{y}' for x,y in pts) + f'" fill="none" stroke="{color}" stroke-width="{width}"/>')

    def box(self, x, y, w, h, color):
        self.poly([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],color)

    def ticks(self, x, y, n, color):
        for k in range(n):
            self.line([(x+k*7,y),(x+k*7+4,y-7)],color,1)

    def save(self, role, motion, state='base'):
        f = OUT / self.name
        f.with_suffix('.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w*SCALE}" height="{self.h*SCALE}" viewBox="0 0 {self.w} {self.h}">' + ''.join(self.svg) + '</svg>\n',encoding='utf8')
        self.im.save(f.with_suffix('.png'))
        self.im.save(f.with_suffix('.webp'), 'WEBP', lossless=True, exact=True, method=6)
        assert self.im.getchannel('A').getextrema() == (0,255), self.name
        assert Image.open(f.with_suffix('.webp')).getchannel('A').tobytes() == self.im.getchannel('A').tobytes()
        records.append(dict(id=self.name, source=f.with_suffix('.svg').relative_to(ROOT).as_posix(), file=f.with_suffix('.webp').relative_to(ROOT).as_posix(), logical_size=[self.w,self.h], texture_size=list(self.im.size), text_rect=self.text_rect, role=role, motion=motion, state=state, text_baked=False, runtime_integrated=False))
        return self


def make():
    for kind, accent in [('daily',RED),('thought',VIOLET),('trial',PAPER)]:
        p=Plate('dialogue_'+kind,1720,224,[94,42,1528,135])
        p.poly([(22,18),(1668,6),(1712,50),(1684,208),(0,220)],INK)
        p.poly([(35,28),(1660,17),(1693,52),(1669,193),(16,206)],PAPER)
        p.poly([(20,192),(1670,181),(1669,193),(16,206)],accent)
        p.poly([(25,31),(65,31),(48,181),(9,182)],INK)
        for y in range(50,175,22):
            p.line([(27,y),(44,y-5)],accent,2)
        p.line([(83,28),(81,185)],INK,2)
        p.ticks(1510,207,18,accent)
        p.save('대화 본문 바탕; 글자는 엔진 Text로 분리','진입 140ms 이동 14px/퇴장100ms; 대사 중 흔들지 않음',kind)
    for kind,accent in [('daily',RED),('trial',VIOLET)]:
        p=Plate('nameplate_'+kind,390,68,[42,15,295,40])
        p.poly([(19,3),(377,3),(360,61),(1,66)],INK)
        p.poly([(25,10),(369,10),(355,54),(14,59)],accent)
        p.line([(36,12),(342,12)],PAPER,2)
        p.box(15,20,7,24,PAPER)
        p.save('화자 이름; 긴 이름은 글자크기 축소보다 너비 조정','화자 변경시 90ms 교체; 본문과 별도 층',kind)
    for state in ['idle','focus','pressed','disabled']:
        p=Plate('choice_'+state,920,96,[100,23,728,50])
        base = INK if state in ('idle','disabled') else RED
        edge = GREY if state=='disabled' else PAPER
        p.poly([(22,5),(910,0),(890,83),(2,95)],INK)
        p.poly([(30,13),(900,9),(880,74),(15,85)],base)
        p.line([(43,19),(865,14)],edge,2)
        p.poly([(39,34),(68,46),(38,60)],edge)
        if state=='focus':
            p.poly([(7,7),(17,5),(0,66),(0,30)],PAPER)
            p.line([(105,76),(844,67)],PAPER,3)
        if state=='pressed': p.line([(109,29),(857,23)],INK,4)
        if state=='disabled': p.line([(48,36),(33,59)],PAPER,3)
        p.save('선택지; 번호/문장은 별도 텍스트','포커스100ms/누름70ms; disabled는 선택불가 상태와 연결',state)
    for state in ['idle','target','locked']:
        p=Plate('reticle_'+state,100,100)
        col=RED if state=='target' else (GREY if state=='locked' else PAPER)
        for pts in [[(18,35),(18,18),(35,18)],[(65,18),(82,18),(82,35)],[(82,65),(82,82),(65,82)],[(35,82),(18,82),(18,65)]]:
            p.line(pts,INK,7);p.line(pts,col,3)
        if state=='locked':
            p.box(40,44,20,18,col);p.line([(43,44),(43,36),(57,36),(57,44)],col,3)
        else:
            p.poly([(50,42),(58,50),(50,58),(42,50)],col)
        p.save('조준점; 실제 선택가능/잠김 상태에 연결','대상획득120ms 축소; 지속 점멸 없음',state)
    for state,col in [('new',RED),('review',VIOLET)]:
        p=Plate('evidence_'+state,980,180,[116,37,773,112])
        p.poly([(28,9),(961,0),(938,165),(0,180)],INK)
        p.poly([(38,19),(947,13),(925,152),(15,166)],PAPER)
        p.poly([(30,20),(99,18),(79,155),(14,166)],col)
        p.poly([(43,56),(72,55),(66,99),(37,100)],INK)
        p.line([(44,66),(65,66)],PAPER,2);p.line([(42,76),(62,76)],PAPER,2)
        p.ticks(811,162,16,col)
        p.save('증거 획득/다시 보기; 실제 증거 그림과 제목/내용은 별도','획득상태 확정 뒤160ms 진입; 닫기 전 입력소비',state)
    p=Plate('focus_track',450,48)
    p.poly([(12,4),(448,0),(435,39),(0,47)],INK)
    p.poly([(19,10),(435,7),(426,32),(10,39)],PAPER)
    p.poly([(25,15),(426,12),(420,27),(18,34)],INK)
    p.save('집중 게이지 외곽','fill만 실제 집중값으로 조절')
    p=Plate('focus_fill',400,20)
    p.poly([(8,4),(397,0),(391,15),(0,19)],VIOLET)
    for x in range(35,390,35):p.line([(x,2),(x-4,16)],INK,2)
    p.save('집중 게이지 내용; 왼쪽 기준 clip 필요','임의 점수 연출 금지; 소모/회복에만 반응')
    for state in ['idle','selected','disabled']:
        p=Plate('pad_tab_'+state,300,76,[51,19,205,40])
        c=RED if state=='selected' else (GREY if state=='disabled' else INK)
        p.poly([(14,3),(299,0),(280,65),(0,75)],c)
        p.line([(36,12),(267,8)],PAPER,2)
        p.poly([(21,27),(32,37),(19,48),(9,37)],PAPER)
        if state=='selected':p.line([(50,60),(255,53)],PAPER,4)
        p.save('패드 탭; 문구와 선택상태 분리','선택100ms; 실제 페이지 표시 후 확정',state)
    p=Plate('continue_mark',48,36)
    p.poly([(3,5),(43,14),(18,32)],INK)
    p.poly([(9,9),(36,15),(19,26)],PAPER)
    p.save('본문 출력 완료 표시','타이핑 종료 뒤 표시; 자동 진행/스킵 입력과 별개')
    (OUT/'manifest.json').write_text(json.dumps({'status':'authored source assets; runtime integration pending','palette':{'ink':INK,'paper':PAPER,'red':RED,'violet':VIOLET},'assets':records},ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def preview():
    # Inspection composition only; this is not a runtime screenshot or a new game background.
    im=Image.new('RGBA',(1920,1080),'#66636e');draw=ImageDraw.Draw(im)
    for x in range(0,1920,80):draw.line([(x,0),(x,1080)],fill='#77737e')
    for y in range(0,1080,80):draw.line([(0,y),(1920,y)],fill='#77737e')
    sprite=Image.open(ROOT/'art/sprites_v4/mio/mio_guarded.webp')
    sprite.thumbnail((640,1000));im.alpha_composite(sprite,(1000,30))
    for name,xy in [('dialogue_daily',(100,822)),('nameplate_daily',(138,771))]:
        plate=Image.open(OUT/(name+'.png'));plate=plate.resize((plate.width//2,plate.height//2),Image.Resampling.LANCZOS);im.alpha_composite(plate,xy)
    draw=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',36)
    bold=ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',30)
    draw.text((185,786),'미오',font=bold,fill=PAPER)
    draw.text((194,866),'읽었냐고 안 물었어.',font=font,fill=INK)
    draw.text((55,35),'합성 검수용 · 게임 실행 화면 아님',font=bold,fill=PAPER)
    folder=ROOT/'Game/Saved/v4-asset-batch01';folder.mkdir(parents=True,exist_ok=True)
    im.convert('RGB').save(folder/'dialogue_composition.jpg',quality=94)
    thumbs=Image.new('RGB',(1400,((len(records)+2)//3)*150),'#686570');dr=ImageDraw.Draw(thumbs)
    for i,a in enumerate(records):
        tile=Image.open(ROOT/a['file']);tile.thumbnail((450,105));x=(i%3)*465;y=(i//3)*150
        thumbs.paste(tile,(x+5,y+5),tile);dr.text((x+8,y+115),a['id'],font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20),fill='white')
    thumbs.save(folder/'ui_contact_sheet.jpg',quality=94)


if __name__=='__main__':
    make()
    if SCALE==2:preview()
    print(f'Authored {len(records)} UI state plates at {SCALE}x (SVG + PNG + lossless WebP); alpha export checks passed')
