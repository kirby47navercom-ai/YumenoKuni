"""Original trial/minigame UI art states. Runtime text, answers, timing and fills stay separate."""
import json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import make_v4_ui_batch as ui

ROOT=Path(__file__).resolve().parents[1];ui.OUT=ROOT/'ui/v4/trial_hd';ui.OUT.mkdir(parents=True,exist_ok=True);ui.SCALE=4
P=ui.Plate;INK,PAPER,RED,VIOLET,GREY=ui.INK,ui.PAPER,ui.RED,ui.VIOLET,ui.GREY


def make():
    for state,col in [('idle',PAPER),('focus',VIOLET),('confirmed',RED),('wrong',GREY)]:
        p=P('letter_tile_'+state,110,130,[20,23,70,79])
        p.poly([(9,8),(104,0),(101,117),(0,129)],INK)
        p.poly([(17,17),(94,10),(91,107),(10,117)],col)
        p.line([(23,101),(84,96)],INK,3)
        if state=='focus':p.line([(1,26),(2,7),(22,4)],PAPER,3)
        if state=='wrong':p.line([(21,36),(83,90)],INK,5)
        p.save('글자 조립 타일; 실제 문자/정답은 Text와 판정 데이터','선택90ms; 확정/오답 판정 이후 상태 교체',state)
    for state,col in [('normal',PAPER),('weak',RED),('selected',VIOLET)]:
        p=P('statement_band_'+state,1040,118,[78,24,884,70])
        p.poly([(25,13),(1024,0),(1000,103),(0,118)],INK)
        p.line([(67,104),(983,88)],col,4)
        p.poly([(22,27),(46,24),(30,88),(7,93)],col)
        if state=='selected':p.line([(66,12),(1004,2)],PAPER,3)
        p.save('의논 발언 바탕; 약점 강조/선택 상태를 실제 발언에 연결','이동·회전은 엔진에서 텍스트와 함께 적용',state)
    for state,col in [('candidate',PAPER),('target',RED),('matched',VIOLET)]:
        p=P('scrum_endpoint_'+state,92,92)
        p.poly([(46,3),(88,46),(46,89),(3,46)],INK)
        p.line([(46,14),(77,46),(46,78),(14,46),(46,14)],col,4)
        if state=='matched':p.line([(28,45),(41,59),(66,32)],col,5)
        else:p.poly([(46,33),(59,46),(46,59),(33,46)],col)
        p.save('대립 의논 연결 끝점; 선은 엔진에서 두 점 사이에 생성','실제 대응 선택/판정 상태만 표시',state)
    for side,col in [('left',RED),('right',VIOLET)]:
        p=P('scrum_team_'+side,670,130,[70,28,530,75])
        pts=[(5,9),(624,0),(669,65),(625,118),(0,129)]
        if side=='right':pts=[(670-x,y) for x,y in pts]
        p.poly(pts,INK);p.line([(35,110),(612,100)],col,6)
        p.save('대립 의논 양 팀 제목; 소속/참가자 얼굴은 별도','팀 확정 후 진입180ms; 좌우 색 외에 문구로도 구분',side)
    for lane in range(3):
        p=P('panic_lane_'+str(lane),760,260,[77,46,599,166])
        p.poly([(25,0),(759,25),(730,259),(0,228)],INK)
        p.line([(38,12),(747,36)], [RED,VIOLET,PAPER][lane],5)
        p.line([(20,214),(712,244)],GREY,2)
        p.save('다중 의논 화자 창; 마스크 안 얼굴·발언은 별도','현재 입력받는 창만 전면/강조; 음성 우선순위는 엔진에서 처리',str(lane))
    for state,col in [('empty',GREY),('focus',VIOLET),('placed',PAPER),('wrong',RED)]:
        p=P('comic_slot_'+state,430,330,[31,30,367,264])
        p.poly([(7,9),(426,0),(416,324),(0,329)],INK)
        p.line([(21,22),(410,14),(401,309),(14,313),(21,22)],col,4)
        if state=='focus':
            for x,y in [(22,24),(380,25),(20,278),(378,277)]:p.line([(x,y+25),(x,y),(x+25,y)],PAPER,5)
        if state=='wrong':p.line([(181,135),(235,189)],RED,5);p.line([(235,135),(181,189)],RED,5)
        p.save('사건 재구성 만화 칸; 개별 사건 그림/정답은 별도','그림 배치 후 확정 결과를 전달받아 테두리 상태 교체',state)
    p=P('comic_caption',600,170,[40,30,515,89])
    p.poly([(12,9),(580,0),(599,120),(155,130),(103,166),(102,131),(0,139)],INK)
    p.poly([(24,20),(569,12),(582,107),(142,117),(115,140),(115,119),(14,126)],PAPER)
    p.save('사건 재구성 말풍선; 글자는 별도','페이지 안 그림/문구를 같은 순서로 표시')
    for state,col in [('waiting',GREY),('active',PAPER),('hit',VIOLET),('miss',RED)]:
        p=P('rhythm_ring_'+state,180,180)
        def ring(radius,color,width):p.line([(90+radius*math.cos(i*math.tau/48),90+radius*math.sin(i*math.tau/48)) for i in range(49)],color,width)
        ring(77,INK,15);ring(77,col,5);ring(55,col,2)
        for a in range(4):
            t=a*math.pi/2;p.line([(90+65*math.cos(t),90+65*math.sin(t)),(90+86*math.cos(t),90+86*math.sin(t))],col,4)
        if state=='hit':p.line([(66,89),(84,107),(118,69)],VIOLET,6)
        if state=='miss':p.line([(72,73),(109,110)],RED,5);p.line([(109,73),(72,110)],RED,5)
        p.save('리듬 판정 목표 원; 축소 접근 원/박자/키 라벨은 별도','판정 창 기준으로 상태 갱신; 수동 랜덤 점멸 없음',state)
    for side in ['left','right']:
        p=P('route_prompt_'+side,250,120,[90,25,125,68])
        p.poly([(14,8),(244,0),(231,107),(0,119)],INK)
        pts=[(27,60),(66,29),(66,48),(85,46),(82,72),(62,74),(62,94)]
        if side=='right':pts=[(111-x,y) for x,y in pts]
        p.poly(pts,VIOLET)
        p.save('질문 경로 선택 방향 HUD; 길/차량 3D는 별도','입력 유효 구간만 표시; 선택 확정 뒤 소거',side)
    (ui.OUT/'manifest.json').write_text(json.dumps({'status':'original trial/minigame art, runtime integration pending','scale':4,'text_baked':False,'assets':ui.records,'runtime_tested':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    sheet=Image.new('RGB',(1500,math.ceil(len(ui.records)/4)*165),'#595563');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
    for i,a in enumerate(ui.records):
        im=Image.open(ROOT/a['file']);im.thumbnail((345,122));x=i%4*375+8;y=i//4*165+6
        sheet.paste(im,(x,y),im);d.text((x,y+130),a['id'],font=font,fill='white')
    folder=ROOT/'Game/Saved/v4-ui-trial';folder.mkdir(parents=True,exist_ok=True);sheet.save(folder/'contact.jpg',quality=95)
    print('Exported',len(ui.records),'native 4x trial/minigame UI states')


if __name__=='__main__':make()
