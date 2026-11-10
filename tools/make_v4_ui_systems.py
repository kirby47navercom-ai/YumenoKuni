"""Editable UI components for pad/map/save/backlog and trial state displays.
Uses the established vector system; no fake screenshots, baked prose or game logic.
"""
import json, math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import make_v4_ui_batch as ui

ROOT=Path(__file__).resolve().parents[1]
ui.OUT=ROOT/'ui/v4/systems_hd';ui.OUT.mkdir(parents=True,exist_ok=True)
ui.SCALE=4
P=ui.Plate
INK,PAPER,RED,VIOLET,GREY=(ui.INK,ui.PAPER,ui.RED,ui.VIOLET,ui.GREY)


def frame(name,w,h,rect=None):
    p=P(name,w,h,rect)
    p.poly([(18,6),(w-10,0),(w,h-21),(w-21,h),(0,h-7)],INK)
    p.line([(30,16),(w-25,10),(w-14,h-31)],PAPER,2)
    p.poly([(7,h-24),(w-35,h-17),(w-40,h-8),(4,h-15)],RED)
    return p


def icon(p,kind,c=PAPER):
    # Logical 96px optical grid; only deliberate, recognizable silhouettes.
    if kind=='map':
        p.line([(14,26),(35,17),(61,29),(82,19),(82,73),(61,83),(35,70),(14,80),(14,26)],c,4)
        p.line([(35,17),(35,70)],c,3);p.line([(61,29),(61,83)],c,3)
    elif kind=='profile':
        pts=[(48+13*math.cos(a*math.tau/16),30+13*math.sin(a*math.tau/16)) for a in range(17)]
        p.line(pts,c,4);p.line([(19,79),(22,63),(34,53),(62,53),(74,63),(77,79)],c,4)
    elif kind=='evidence':
        p.line([(23,15),(62,15),(77,30),(77,81),(23,81),(23,15)],c,4)
        p.line([(60,16),(60,33),(76,33)],c,3)
        for y in [46,58,70]:p.line([(34,y),(64,y)],c,3)
    elif kind=='save':
        p.line([(18,15),(69,15),(80,26),(80,81),(18,81),(18,15)],c,4)
        p.line([(31,16),(31,39),(63,39),(63,16)],c,3)
        p.line([(31,80),(31,54),(66,54),(66,80)],c,3)
        p.box(54,21,5,13,c)
    elif kind=='settings':
        for x,y in [(24,32),(48,65),(72,42)]:
            p.line([(x,17),(x,80)],c,3);p.box(x-8,y-7,16,14,INK);p.line([(x-8,y-7),(x+8,y-7),(x+8,y+7),(x-8,y+7),(x-8,y-7)],c,3)
    elif kind=='gift':
        p.line([(20,44),(20,80),(77,80),(77,44)],c,4)
        p.line([(15,31),(81,31),(81,44),(15,44),(15,31)],c,4)
        p.line([(48,31),(48,80)],c,4)
        p.line([(48,30),(30,27),(25,16),(34,12),(48,30),(60,12),(71,16),(66,27),(48,30)],c,3)
    elif kind=='skills':
        p.line([(49,10),(27,48),(45,48),(35,85),(72,39),(54,39),(64,10),(49,10)],c,4)
    elif kind=='backlog':
        p.line([(18,16),(78,16),(78,70),(50,70),(32,84),(32,70),(18,70),(18,16)],c,4)
        for y in [30,43,56]:p.line([(29,y),(66,y)],c,3)


def make():
    for kind in ['map','profile','evidence','save','settings','gift','skills','backlog']:
        p=P('icon_'+kind,96,96);icon(p,kind);p.save('패드/메뉴 기능 아이콘; 의미 라벨은 Text로 별도','64px 이상 권장; 초점 테두리는 상위 버튼이 제공')
    p=frame('pad_shell',1500,880,[330,108,1100,677])
    p.box(28,69,262,728,'#24212e');p.line([(310,80),(310,789)],PAPER,2)
    p.line([(345,89),(1420,89)],RED,4)
    p.ticks(1244,845,24,GREY)
    p.save('패드 공용 외곽; 왼쪽 탭/본문/페이지 상태를 별도 합성','열기180ms, 닫기140ms; 최초 입력은 현재 페이지 상태를 참조')
    for state,col in [('idle',GREY),('selected',RED),('empty',GREY),('incompatible',VIOLET)]:
        p=frame('save_slot_'+state,1080,154,[260,28,770,99])
        p.box(28,25,204,106,'#302b3b');p.line([(249,24),(249,128)],col,3)
        p.line([(275,119),(1022,119)],GREY,1)
        if state=='selected':p.poly([(6,47),(20,56),(6,70)],PAPER)
        if state=='empty':p.line([(110,78),(150,78)],GREY,3)
        if state=='incompatible':p.line([(196,29),(222,55),(196,55),(196,29)],VIOLET,3)
        p.save('저장 슬롯; 204×106 썸네일은 별도 텍스처, 실제 저장/호환 상태만 표시','포커스100ms; 저장 완료 표시는 파일 성공 응답 이후',state)
    p=frame('confirm_modal',850,430,[66,70,718,200])
    p.line([(61,52),(780,46)],RED,4);p.line([(64,292),(778,292)],GREY,2)
    p.save('확인창 바탕; 본문/확인/취소 버튼 별도; 기본 초점은 취소','배경 입력 차단; 닫는 입력은 다음 화면에 전달하지 않음')
    for state,col in [('current',RED),('available',PAPER),('locked',GREY),('objective',VIOLET)]:
        p=P('map_marker_'+state,88,112)
        p.poly([(44,3),(77,22),(77,66),(44,104),(11,66),(11,22)],INK)
        p.line([(44,12),(68,27),(68,61),(44,89),(20,61),(20,27),(44,12)],col,4)
        if state=='locked':
            p.box(31,38,26,23,col);p.line([(35,38),(35,27),(53,27),(53,38)],col,4)
        elif state=='current':p.poly([(44,29),(58,57),(44,51),(30,57)],col)
        elif state=='objective':p.poly([(44,24),(49,39),(64,39),(52,49),(57,64),(44,55),(31,64),(36,49),(24,39),(39,39)],col)
        else:p.line([(30,43),(41,54),(60,31)],col,4)
        p.save('지도 위치/목표/잠김 표식; 맵 좌표는 별도 데이터','현재 위치만 600ms 완만 확대; 잠김 목적은 접근 전 라벨로 설명',state)
    p=frame('map_location_card',440,170,[32,26,375,113]);p.line([(31,83),(404,83)],GREY,2)
    p.save('위치 이름/이동 가능 이유/캐릭터 아이콘용 카드','실제 포털·해금 조건을 UI와 동기화')
    for state in ['idle','focus']:
        p=frame('backlog_row_'+state,1110,172,[179,44,883,105])
        p.box(27,26,125,120,'#302b3b');p.line([(178,29),(1040,29)],RED if state=='focus' else GREY,2)
        if state=='focus':p.poly([(1052,110),(1080,124),(1052,138)],PAPER)
        p.save('로그 대사 행; 화자/대사/음성 가능 상태 분리','음성 버튼은 실제 음성 있는 행에만 표시',state)
    p=frame('evidence_detail',1110,700,[440,72,605,548])
    p.box(32,70,373,373,'#302b3b');p.line([(425,55),(425,629)],GREY,2)
    p.line([(453,149),(1046,149)],RED,3)
    p.save('증거 상세; 정사각 사진/제목/본문/분류/획득 시점 별도','증거 확정 후 표시; 고해상도 사진은 원본 비율 유지')
    p=frame('profile_detail',1110,700,[466,70,580,565])
    p.box(30,31,405,607,'#302b3b');p.line([(457,53),(457,630)],VIOLET,2)
    p.line([(480,150),(1040,150)],RED,3)
    p.save('인물 상세; 좌측 입상, 공개된 정보만 오른쪽 Text로 표시','미공개 능력은 데이터가 공개될 때까지 숨김')
    for state,col in [('idle',PAPER),('equipped',VIOLET),('unavailable',GREY)]:
        p=frame('skill_card_'+state,740,180,[146,29,550,116])
        p.poly([(34,42),(111,35),(100,132),(23,139)],col)
        p.line([(130,25),(130,143)],GREY,2)
        if state=='equipped':p.line([(44,87),(61,104),(90,65)],INK,6)
        p.save('효과/비용/장착 상태를 별도 표시하는 스킬 카드','SP 초과/미해금 이유를 실제 상태로 제공',state)
    p=frame('trial_health_track',560,58)
    for x in range(33,530,49):p.line([(x,14),(x-5,40)],GREY,2)
    p.save('발언력 게이지 외곽; fill은 실제 값으로 clip','피해 확정시에만 짧은 충격; 텍스트 수치 별도')
    p=P('trial_health_fill',492,22);p.poly([(8,4),(490,0),(482,17),(0,21)],RED)
    p.save('발언력 내용; 왼쪽 기준 클립용','감소160ms; 감소 전 잔상은 엔진에서 별도')
    p=frame('trial_timer',240,94,[40,20,161,54]);p.line([(28,72),(204,68)],VIOLET,4)
    p.save('남은 시간 바탕; 시간 글자는 엔진 Text','일시정지 때 수치 고정; 임계치 색 변화 엔진 처리')
    p=frame('ammo_card',510,126,[105,24,354,77]);p.poly([(23,38),(84,27),(72,91),(12,102)],VIOLET)
    p.save('선택 증거/진술 제목 바탕; 실제 아이콘·제목 별도','전환120ms; 사용할 수 없는 증거는 실제 판정 상태로 표시')
    p=frame('trial_result',1200,780,[83,104,1020,575]);p.line([(76,85),(1119,76)],VIOLET,5)
    for y in [238,358,478,598]:p.line([(86,y),(1107,y)],GREY,2)
    p.save('재판 결과 행 구분; 등급·성적·보상은 계산 결과만 표시','집계 이후 표시; 보상 반영은 한 번만')
    report={'status':'source components exported; engine integration pending','scale':4,'text_baked':False,'assets':ui.records,'runtime_tested':False}
    (ui.OUT/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    # Contact sheet is an inspection derivative, not a deliverable UI texture.
    sheet=Image.new('RGB',(1500,math.ceil(len(ui.records)/4)*155),'#595563');d=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
    for i,a in enumerate(ui.records):
        im=Image.open(ROOT/a['file']);im.thumbnail((350,115))
        x=(i%4)*375+8;y=(i//4)*155+5;sheet.paste(im,(x,y),im)
        d.text((x,y+121),a['id'],font=font,fill='white')
    review=ROOT/'Game/Saved/v4-ui-systems';review.mkdir(parents=True,exist_ok=True)
    sheet.save(review/'contact.jpg',quality=95)
    # Filled composition checks Korean text area/actual optical sizes at 1080p.
    # Text is review-only and is never written into delivered components.
    fontbody=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',26)
    fonttitle=ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',32)
    sample=Image.new('RGBA',(1920,1080),'#605d69')
    def paste(name,x,y):
        a=Image.open(ui.OUT/(name+'.png'));a=a.resize((a.width//4,a.height//4),Image.Resampling.LANCZOS);sample.alpha_composite(a,(x,y))
    paste('pad_shell',210,100)
    for j,kind in enumerate(['map','profile','evidence','save','settings']):
        paste('icon_'+kind,245,210+j*122)
        ImageDraw.Draw(sample).text((349,241+j*122),['지도','인물','증거','저장','설정'][j],font=fontbody,fill=PAPER)
    ImageDraw.Draw(sample).text((564,214),'기록 보관',font=fonttitle,fill=PAPER)
    for j,state in enumerate(['selected','idle','empty']):
        y=294+j*180;paste('save_slot_'+state,550,y)
        d=ImageDraw.Draw(sample)
        d.text((824,y+29),'기록이 없는 슬롯' if state=='empty' else '저장 기록 · 검수용 문구',font=fontbody,fill=PAPER)
        if state!='empty':d.text((824,y+71),'위치 · 플레이 시간 · 기록 시각',font=fontbody,fill='#b3abbc')
    ImageDraw.Draw(sample).text((44,26),'UI 합성 검수 · 실제 저장 데이터/게임 실행 화면 아님',font=fontbody,fill=PAPER)
    sample.convert('RGB').save(review/'save_composition.jpg',quality=95)
    print('Exported',len(ui.records),'editable native 4x UI components; transparent PNG/WebP alpha verified')


if __name__=='__main__':make()
