"""Editable source-exact inspection aids, not invented discovered photographs.

Use only confirmed relations. Existing world coordinates anchor the two actual
waiting benches/mirror. Unmodelled hatch/sample relations remain unscaled
source diagrams; no actor-time/ray precision is claimed from their layout.
"""
from pathlib import Path
from html import escape
import hashlib,json,math
from PIL import Image
import make_v4_case1_documents as base
from build_v4_story import Source

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'ui/v4/investigation_diagrams_v4'
W,H,S=1600,1000,3
base.S=S
PAPER,INK,MUTED,BORDER=base.PAPER,base.INK,base.MUTED,base.BORDER
VIOLET,PALE,DARK='#766081','#e4d9e8','#ddd2c1'
SOURCE_PREFIXES=('11b','181','07','13b1','13b2','14b1','14b3','15b2','165','166','183','184','185')


class Doc(base.Drawing):
    def __init__(self,title,subtitle):
        super().__init__();self.title=title
        self.text(80,90,title,42);self.text(80,139,subtitle,24,MUTED)
        self.line([(80,168),(1520,168)],BORDER,2)
        self.text(80,954,'확인한 자료 · 유메노쿠니',21,MUTED)
    def poly(self,points,fill=PAPER,stroke=INK,width=2):
        self.parts.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in points)+f'" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
        self.draw.polygon([(x*S,y*S) for x,y in points],fill=fill)
        self.draw.line([(x*S,y*S) for x,y in points+[points[0]]],fill=stroke,width=width*S)
    def ellipse(self,x,y,w,h,fill=PAPER,stroke=INK,width=2):
        self.parts.append(f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
        self.draw.ellipse((x*S,y*S,(x+w)*S,(y+h)*S),fill=fill,outline=stroke,width=width*S)
    def arrow(self,a,b,color=VIOLET,width=3):
        self.line([a,b],color,width)
        ang=math.atan2(b[1]-a[1],b[0]-a[0]);size=13
        self.poly([b,(b[0]-size*math.cos(ang-.5),b[1]-size*math.sin(ang-.5)),(b[0]-size*math.cos(ang+.5),b[1]-size*math.sin(ang+.5))],color,color,1)
    def note(self,x,y,lines,size=25):
        for i,line in enumerate(lines):self.text(x,y+i*(size+15),line,size,MUTED)
    def save(self,name):
        path=OUT/name
        path.with_suffix('.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*S}" height="{H*S}" viewBox="0 0 {W} {H}"><rect width="1600" height="1000" fill="{PAPER}"/>'+''.join(self.parts)+'</svg>\n',encoding='utf-8')
        self.im.save(path.with_suffix('.webp'),'WEBP',lossless=True,method=6)
        return path.with_suffix('.webp').relative_to(ROOT).as_posix()


def rect(x,y,w,h):return [[x/W,y/H],[(x+w)/W,y/H],[(x+w)/W,(y+h)/H],[x/W,(y+h)/H]]
def poly(points):return [[x/W,y/H] for x,y in points]
def region(key,label,shape,correct=False):return {'id':key,'label':label,'polygon':shape,'correct':correct}


def make():
    OUT.mkdir(parents=True,exist_ok=True)
    sources={s.prefix:s for p in (ROOT/'docs/design/rewrite_v4').glob('*.md') if (s:=Source(p))}
    for prefix,expected in REVIEWED_SOURCE_HASHES.items():
        if sources[prefix].hash!=expected:raise ValueError('Re-read changed diagram source '+sources[prefix].name)
    world_path=ROOT/'art/space_v4/runtime_v1/world.json'
    world=json.loads(world_path.read_text(encoding='utf-8'))
    entries={}
    def refs(*rows):return [{**sources[p].ref(line),'quote':sources[p].lines[line-1]} for p,line in rows]
    def emit(key,d,regions,proofs,scope,coordinates=None,limitations=None):
        image=d.save(key)
        entries[key]={'title':d.title,'image':image,'sha256':hashlib.sha256((ROOT/image).read_bytes()).hexdigest(),'svg':str(Path(image).with_suffix('.svg')).replace('\\','/'),'coordinateSystem':'normalized-image-uv','regions':regions,'source':proofs,'inspectionScope':scope,'newEvidence':False,'presentation':'Source-confirmed inspection aid, not a newly discovered document/photo. Diagram distances and edge motifs are illustrative, not new measured clue values.','worldAnchors':coordinates or [],'limitations':limitations or [],'rasterSize':[W*S,H*S],'visualReview':'directly inspected 2026-10-29; legible source text, no correctness border, correct temporal scope; runtime not yet exercised'}
    # Canonical functional topology, not an invented metric projection of all maze rooms.
    d=Doc('반사와 통로','두 사람이 함께 확인한 관찰 범위')
    d.line([(240,430),(1120,430),(1120,700)],INK,35)
    d.line([(240,570),(980,570),(980,700)],INK,35)
    d.box(850,700,350,150,PALE,INK,3);d.text(910,760,'작업 홈 H',30)
    d.text(870,815,'뒤 · 옆은 벽',24,MUTED)
    d.line([(1090,380),(1180,470)],VIOLET,12);d.text(1230,410,'고정 거울 M',28)
    d.text(1010,350,'굽이 B',29)
    d.box(120,650,340,190,fill=PAPER,stroke=INK,width=3);d.text(165,720,'대기실 D',30)
    d.text(160,778,'공용 길로 이어짐',24,MUTED)
    d.line([(280,650),(280,570)],INK,5)
    d.text(310,380,'관찰 자리 A',29)
    d.ellipse(370,460,42,42,PALE,INK,2);d.ellipse(440,460,42,42,PALE,INK,2)
    d.text(350,540,'미오 · 린',25)
    d.arrow((480,480),(1100,447),VIOLET,3)
    d.arrow((1100,447),(1070,698),VIOLET,3)
    d.ellipse(1044,492,38,43,PALE,INK,2)
    d.line([(1000,590),(1008,559),(1030,546),(1065,557)],INK,5)
    d.text(1220,540,'반사된 머리',25);d.text(1220,583,'직접 나온 어깨',25)
    d.line([(1200,540),(1095,525)],BORDER,2);d.line([(1200,583),(1090,585)],BORDER,2)
    d.note(80,235,['같은 몸이 굽이를 지나는 동안 반사와 직접 시야가 겹쳤다.','첫 손잡이는 가려졌고,안쪽 바닥과 몸 뒤 전체를 본 것은 아니다.'])
    anchors=[]
    for n in world['spaces']['mirror_workbay']['nodes']:
        if n['id'] in ('fixed_mirror','work_partition'):anchors.append({'space':'mirror_workbay','node':n['id'],'p':n['p'],'box':n['box'],'role':'existing physical mirror/partition reference, not metric A/B/H mapping'})
    emit('c3_observation_plan',d,[region('overlap','반사와 직접 시야의 겹침',rect(990,475,130,165),True),region('work-inside','작업 홈 안쪽',rect(855,705,340,135)),region('waiting-door','대기실 문',rect(120,650,340,190)),region('entrance','미로 앞 통로',rect(240,435,250,130))],refs(('07',140),('07',150),('07',151),('07',152),('07',153),('13b1',555),('165',59),('165',61),('183',573)),'v4:3:knowledge:reflection-geometry',anchors,['Canonical source topology only; no new metric position/angle or full native ray/occlusion validation.'])
    # Waiting room uses actual native room bounds, bench seats and front door.
    room=world['spaces']['mirror_waiting'];x0,z0,x1,z1=room['bounds'];left,top,rw,rh=420,230,760,630
    def xy(x,z):return left+(x-x0)/(x1-x0)*rw,top+(z-z0)/(z1-z0)*rh
    benches=[]
    for side in ('left','right'):
        ns=[n for n in room['nodes'] if 'seat_slats' in n['id'] and (n['p'][0]<0 if side=='left' else n['p'][0]>0)]
        xs=[p[0] for n in ns for p in n['box']];zs=[p[2] for n in ns for p in n['box']]
        xa,ya=xy(min(xs),min(zs));xb,yb=xy(max(xs),max(zs));benches.append((side,xa,ya,xb-xa,yb-ya,ns))
    d=Doc('대기실의 두 벤치','생존을 확인했던 몸의 자리와 방향')
    d.box(left,top,rw,rh,stroke=INK,width=5)
    for side,x,y,bw,bh,ns in benches:d.box(x-15,y-10,bw+30,bh+20,DARK,INK,3)
    _,bx,by,bw,bh,_=benches[0]
    d.ellipse(bx+3,by+10,bw-6,42,PALE,INK,2);d.box(bx+6,by+58,bw-12,bh-75,PALE,INK,2)
    d.text(120,390,'왼쪽 벤치',28);d.text(120,435,'머리맡은 안쪽',25,MUTED);d.line([(310,420),(bx,by+30)],BORDER,2)
    d.text(1240,390,'오른쪽 벤치',28);d.text(1240,435,'비어 있던 자리',25,MUTED)
    d.text(690,520,'가운데 통로',27,MUTED)
    ex,ey=xy(0,4.5);d.box(ex-60,ey-13,120,26,PAPER,INK,3);d.text(ex-82,920,'입구 D',26)
    d.note(80,235,['문에서 안을 본 방향'])
    emit('c3_waiting_position',d,[region('left-body','왼쪽 벤치 본체',rect(bx-4,by+3,bw+8,bh-2),True),region('right-empty','오른쪽 빈 벤치',rect(benches[1][1]-15,benches[1][2]-10,benches[1][3]+30,benches[1][4]+20)),region('middle','가운데 통로',rect(670,390,260,300))],refs(('07',163),('13b2',95),('183',755),('183',757)),'v4:3:knowledge:file-second',[{'space':'mirror_waiting','bounds':room['bounds'],'projection':'top-down native x/z; entrance at +z, head points toward -z','nodes':[{'id':n['id'],'p':n['p'],'box':n['box']} for _,_,_,_,_,ns in benches for n in ns]}],['Historical living-body placement only. No injury/attack or cause inferred from this neutral silhouette.'])
    d=Doc('따로 둔 물건','제압과 확인 뒤의 보관 위치')
    d.box(390,230,840,520,stroke=INK,width=4);d.text(700,305,'대기실 D',32)
    d.box(480,350,100,240,DARK,INK,2);d.box(1040,350,100,240,DARK,INK,2);d.text(640,500,'가운데 통로',28,MUTED)
    d.box(720,735,160,30,PAPER,INK,3);d.text(705,815,'문턱',26)
    d.box(1030,790,320,80,DARK,INK,3);d.text(1080,845,'바깥 선반',28)
    d.line([(1090,802),(1230,802)],INK,8);d.box(1230,789,65,25,PALE,INK,2)
    d.note(100,880,['확인 뒤 분리해 둔 칼 · 환자를 누르던 도중 정리하러 이탈한 것이 아니다.'],23)
    emit('c3_knife_custody',d,[region('outside-shelf','대기실 바깥 선반',rect(1025,780,335,100),True),region('left-head','왼쪽 벤치 머리맡',rect(470,340,120,80)),region('middle','방 안 통로',rect(620,400,310,270))],refs(('13b2',203),('07',167),('183',783),('183',785)),'v4:3:knowledge:restraint-awake',[{'space':'mirror_waiting','doorP':[0,1.18,4.5],'doorNode':'front.022_leaf'}],['Outside shelf has source-exact relation only; native world has no dedicated shelf anchor, so no fabricated numeric shelf position.'])
    # Four: relational diagram/section, never a substitute first-hand photograph.
    d=Doc('닫혀 있던 때의 관찰','처음 확인한 손의 위치와 나중 개방을 나누어 둔다')
    d.box(120,250,920,610,fill=PAPER,stroke=INK,width=4)
    d.box(230,340,570,370,DARK,INK,4);d.text(390,535,'닫힌 덮개',34)
    hand=[(690,700),(710,663),(722,676),(732,648),(745,665),(758,651),(770,681),(792,676),(805,706),(793,734),(742,740),(711,728)]
    d.poly(hand,PALE,INK,3)
    d.text(845,755,'손',27);d.line([(835,735),(802,715)],BORDER,2)
    d.box(390,835,220,28,PAPER,INK,3);d.text(360,908,'정면 출입문',27)
    d.box(1130,280,330,270,DARK,INK,3);d.text(1170,390,'안쪽 구획',30);d.text(1200,445,'끝',30)
    d.note(1090,650,['수사에서 그린 관찰도','새로 찍은 사진이 아니다.'],25)
    emit('c4_hatch_hand_observation',d,[region('hand-edge','손이 보인 덮개 가장자리',poly(hand),True),region('front-door','정면 출입문',rect(390,820,220,60)),region('storage-end','안쪽 끝난 구획',rect(1130,280,330,270)),region('cover','덮개 가운데',rect(250,360,400,300))],refs(('14b1',55),('14b1',59),('14b1',67),('14b3',7),('184',544)),'v4:4:knowledge:first-hand',limitations=['Unscaled observation diagram. No exact injury/hand size, hinge side or native hatch coordinate is claimed.'])
    d=Doc('점검구 안팎의 구조','덮개를 내리는 일과 바깥에서 고정하는 일')
    d.text(130,260,'바깥',30);d.text(130,680,'안쪽',30)
    d.box(300,390,1030,65,DARK,INK,4)
    d.box(720,335,245,55,PALE,INK,3);d.text(725,292,'별도 외부 고정',29)
    d.line([(845,310),(845,330)],BORDER,2)
    d.box(300,455,90,330,DARK,INK,3);d.box(1240,455,90,330,DARK,INK,3)
    d.line([(400,680),(500,665),(600,680),(700,665),(800,680),(900,665),(1000,680),(1100,665),(1230,680)],VIOLET,4)
    d.text(1010,755,'물',27,MUTED);d.text(400,520,'덮개',28)
    d.note(140,870,['안쪽의 손으로 닿는 부분과 바깥의 별도 고정은 다르다.'],27)
    emit('c4_external_fastening',d,[region('external-fastener','외부 고정 부분',rect(715,325,260,80),True),region('water','물',rect(420,655,800,130)),region('inner-wall','안쪽 벽',rect(300,455,90,330)),region('cover','덮개',rect(300,390,1030,65))],refs(('14b1',55),('184',726),('184',728)),'v4:4:knowledge:external-fastening',limitations=['Relational section only. Rectangle denotes confirmed external fastening, not a newly specified physical lock, bolt count or construction recipe. Native world has no exact hatch anchor.'])
    d=Doc('안쪽 문 뒤에서 끝난 곳','직접 연 구획과 원래 건물의 경계를 대조한다')
    d.box(140,260,1320,550,PAPER,INK,4)
    d.box(990,260,470,550,DARK,INK,3)
    d.box(1420,260,40,550,INK,INK,2)
    d.box(965,445,50,180,PAPER,INK,3)
    d.text(320,400,'확인한 홀',34);d.text(1030,410,'수납 구획',34)
    d.text(1020,750,'뒤와 모서리는 막힘',26,MUTED)
    d.text(1465,330,'기존',24);d.text(1465,370,'외벽',24)
    d.text(780,670,'안쪽 문',28)
    d.box(340,560,260,170,DARK,INK,3);d.text(375,655,'점검구',30)
    d.note(120,875,['원도면 · 보호 기록 · 두 장소 사진 · 직접 연 구획을 같은 경계에 둔다.'],25)
    emit('c4_storage_boundary',d,[region('storage-and-wall','막힌 수납 구획과 기존 외벽',rect(990,260,470,550),True),region('hatch','점검구',rect(340,560,260,170)),region('front-hall','홀',rect(150,275,650,250)),region('inside-door','안쪽 문',rect(960,435,60,200))],refs(('14b1',107),('14b1',121),('14b3',195),('14b3',205),('166',109),('166',114)),'v4:4:knowledge:photo-comparison',limitations=['Source topology only. No invented external passage, metric room proportions, new room opening or interior photographic coverage.'])
    # Five: six inspected cells, actual paper fragment and two independent joins.
    d=Doc('보관실에서 기록한 칸','현재 남은 용기와 식별 종이의 위치')
    cell_regions=[]
    for ix,key in enumerate('ABCDEF'):
        x=110+(ix%3)*470;y=260+(ix//3)*275
        d.box(x,y,430,235,fill=PAPER,stroke=INK,width=3);d.text(x+25,y+43,key,31)
        if key!='D':
            d.box(x+175,y+75,90,125,fill=DARK,stroke=INK,width=3);d.box(x+166,y+60,108,30,fill=PALE,stroke=INK,width=2);d.box(x+165,y+95,110,55,fill=PAPER,stroke=BORDER,width=2)
        else:
            fragment=[(x+25,y+130),(x+115,y+130),(x+108,y+145),(x+124,y+159),(x+112,y+175),(x+122,y+189),(x+20,y+189)]
            d.poly(fragment,PALE,INK,3);d.text(x+29,y+169,'R-',22)
            cell_regions.append(region('D-fragment','D칸 가장자리 잔편',poly(fragment),True))
        cell_regions.append(region('cell-'+key,key+'칸',rect(x+145,y+55,150,150)))
    d.note(110,875,['용기가 없는 D칸 가장자리의 얇은 식별 종이를 먼저 기록했다.'],26)
    emit('c5_inventory_fragment',d,cell_regions,refs(('15b2',17),('15b2',29),('15b2',31),('15b2',37),('185',573)),'v4:E5-10',limitations=['Inventory comparison layout, not a newly taken photograph. The 3x2 UI arrangement is not asserted as metric shelf/case geometry. Only the actual fragment polygon is the answer, not the empty D cell.'])
    def paper_pair(d,y=330):
        left=[(180,y),(645,y),(620,y+45),(650,y+90),(625,y+135),(655,y+180),(635,y+225),(180,y+225)]
        right=[(700,y),(1120,y),(1120,y+225),(690,y+225),(710,y+180),(680,y+135),(705,y+90),(675,y+45)]
        d.poly(left,PAPER,INK,3);d.poly(right,PAPER,INK,3)
        # The same torn contour is translated horizontally, never a new measured tear value.
        for yy in (y+50,y+100,y+150):d.line([(230,yy),(600,yy)],BORDER,2);d.line([(735,yy),(1080,yy)],BORDER,2)
        return left,right
    d=Doc('회수한 포장의 표시','가방 쪽 종이와 보관실에서 가져온 조각')
    a,b=paper_pair(d,350)
    d.text(235,300,'가방 쪽 포장',30);d.text(760,300,'D칸 조각',30)
    d.box(235,440,300,85,fill=PAPER,stroke=PAPER,width=1);d.text(250,500,'식용 금지',42);d.text(805,500,'R-',36)
    d.line([(220,620),(1100,620)],BORDER,2);d.text(220,680,'접힌 선',26,MUTED)
    d.note(180,820,['현재 회수 뒤 읽은 문구다.준비대에서 미오가 읽었던 말로 바꾸지 않는다.'],24)
    emit('c5_packaging_warning',d,[region('warning','식용 금지 경고',rect(235,440,300,85),True),region('fold','접힌 빈 부분',rect(200,535,340,40)),region('D-paper','D칸 조각',poly(b))],refs(('15b2',285),('15b2',327),('185',757),('185',759)),'v4:E5-16',limitations=['The label is the exact already-read phrase only; paper contours/fold drawing are illustrative, not a new microscopic identification measurement.'])
    d=Doc('마개와 몸체 사이','회수한 띠의 끝과 실제 개봉 구조')
    d.box(1050,360,220,365,DARK,INK,3);d.box(1025,290,270,90,PALE,INK,3)
    d.box(1045,355,230,50,DARK,DARK,1)
    tear=[(1140,355),(1275,355),(1275,405),(1138,405),(1152,392),(1135,380),(1155,368)]
    d.poly(tear,PAPER,INK,3)
    d.poly([(430,355),(525,355),(540,368),(520,380),(537,392),(523,405),(430,405)],PALE,INK,3)
    d.text(395,300,'회수 띠 조각',28);d.text(1050,245,'회수D 마개',30)
    d.line([(450,380),(500,380)],BORDER,3);d.line([(1070,380),(1120,380)],BORDER,3)
    d.text(780,480,'끊긴 끝',27,MUTED);d.line([(880,460),(1140,395)],BORDER,2)
    d.text(1100,795,'몸체',28);d.note(180,865,['별도 몸체 파손이나 다시 이어 붙인 흔적은 확인되지 않았다.'],25)
    emit('c5_cap_strip',d,[region('strip-end','마개와 몸체를 잇던 띠의 끊긴 끝',rect(1128,345,42,70),True),region('bottle-bottom','병 바닥',rect(1050,675,220,50)),region('cap-top','마개 윗면',rect(1025,290,270,60)),region('recovered-strip','따로 회수한 띠',rect(420,345,130,70))],refs(('15b2',335),('15b2',337),('185',785),('185',787)),'v4:E5-17',limitations=['Schematic joint only; bottle form, motif and torn outline do not add dose/quantity, manufacturing details, new hole or repair.'])
    d=Doc('서로 이어지는 두 경계','종이의 접합과 마개 띠의 접합은 다른 비교다')
    d.box(100,230,1400,570,fill=PAPER,stroke=INK,width=2)
    a,b=paper_pair(d,330);d.text(220,280,'가방 포장 / D칸 조각',28)
    d.line([(650,615),(700,615)],BORDER,2)
    d.poly([(260,680),(580,680),(610,698),(585,717),(615,735),(260,735)],PALE,INK,3)
    d.poly([(705,680),(1075,680),(1075,735),(740,735),(710,717),(735,698)],PALE,INK,3)
    d.text(1110,700,'마개 띠 / 남은 끝',25)
    d.note(110,860,['인쇄와 찢긴 끝을 맞춘 현재 비교이며,잔에 넣는 순간의 목격은 아니다.'],25)
    # One comparison plate includes both already-confirmed pair boundaries.
    emit('c5_two_joining_boundaries',d,[region('paper-left-edge','포장 종이의 찢긴 경계',poly([(632,328),(653,328),(628,375),(658,420),(633,465),(663,510),(643,557),(627,557),(647,510),(617,465),(642,420),(612,375)]),True),region('paper-right-edge','D칸 종이의 찢긴 경계',poly([(692,328),(708,328),(683,375),(713,420),(688,465),(718,510),(698,557),(682,557),(702,510),(672,465),(697,420),(667,375)]),True),region('strip-left-edge','회수 띠의 찢긴 경계',poly([(573,677),(587,677),(617,698),(592,717),(622,737),(608,737),(578,717),(603,698)]),True),region('strip-right-edge','남은 띠의 찢긴 경계',poly([(698,677),(712,677),(742,698),(717,717),(747,737),(733,737),(703,717),(728,698)]),True),region('whole-paper','종이 전체 모양',rect(180,330,350,225)),region('right-paper','D칸 조각 전체',rect(790,330,330,225)),region('cap-strip-other','띠의 가운데',rect(270,680,230,55))],refs(('15b2',285),('15b2',327),('15b2',335),('167',103),('167',105)),'v4:E5-17',limitations=['One selectable comparison unit covers both joined pairs, not an invented requirement for two simultaneous inputs. No new trace or material is granted.'])
    # Root-generated new source-correct floor inspection; inspected here after HD delivery.
    image='art/inspection_v4/delivery/floor_ice_builtin_r1.webp'
    with Image.open(ROOT/image) as im:floor_size=list(im.size)
    entries['c1_floor_ice']={'title':'현장 바닥의 결빙','image':image,'sha256':hashlib.sha256((ROOT/image).read_bytes()).hexdigest(),'svg':None,'coordinateSystem':'normalized-image-uv','regions':[region('floor-ice','바닥의 실제 결빙',[[.267,.594],[.34,.54],[.385,.495],[.475,.454],[.529,.45],[.589,.479],[.644,.512],[.696,.532],[.672,.557],[.766,.586],[.812,.623],[.797,.67],[.809,.727],[.803,.762],[.739,.783],[.679,.816],[.626,.818],[.586,.791],[.524,.789],[.461,.762],[.404,.726],[.366,.69],[.312,.658]],True),region('table','테이블 위',[[0,0],[.38,.075],[.38,.15],[0,.075]]),region('sill','고정 창턱',[[.453,.073],[.768,.073],[.768,.104],[.453,.104]]),region('chair','의자 다리',[[.015,.315],[.083,.315],[.083,.618],[.045,.626]])],'source':refs(('11b',613),('11b',639),('181',716),('181',718)),'inspectionScope':'v4:E1-11','newEvidence':False,'presentation':'New original-project inspection illustration, same confirmed floor ice and room materials; no actor/time/injury evidence added.','worldAnchors':[],'limitations':['No identity, freezing time or neck-ice mechanism inferred. Outside ice is not a neck choice and does not play that source-specific wrong line.'],'rasterSize':floor_size,'visualReview':'Directly inspected HD floor-local ice, dry floor boundary, table/chair/window distinction; no people/new wounds.'}
    # Same earlier authored photo inspected before the comparison task. Neutral light does not assert a new time.
    image='art/inspection_v4/delivery/closed_hatch_earlier_builtin_r1.webp'
    with Image.open(ROOT/image) as im:hatch_size=list(im.size)
    entries['c4_closed_hatch_photo']={'title':'모임 전의 닫힌 점검구 사진','image':image,'sha256':hashlib.sha256((ROOT/image).read_bytes()).hexdigest(),'svg':None,'coordinateSystem':'normalized-image-uv','regions':[region('closed-cover','완전히 닫힌 금속 덮개',[[.475,.247],[.874,.374],[.773,.903],[.229,.591]],True),region('floor','덮개 바깥 바닥',[[.13,.34],[.29,.25],[.4,.33],[.24,.43]]),region('outer-frame','바깥 프레임',[[.89,.4],[.91,.415],[.818,.87],[.795,.87]])],'source':refs(('14b3',205),('184',754),('184',755),('184',756),('184',757)),'inspectionScope':'v4:4:knowledge:closed-photo','newEvidence':False,'presentation':'The same authored meeting-before closed-hatch photo, introduced during investigation before the later comparison.','worldAnchors':[],'limitations':['No dawn or other new exact capture time, hand, body, opened interior, new fastening or extra photo is implied. The actual face of the closed cover is selectable; generic misses do not pretend a nonexistent first-hand photograph was selected.'],'rasterSize':hatch_size,'visualReview':'Directly inspected HD closed cover, matching frame/hinges/handle, no interior/people/new fastener/number; neutral lighting does not define dawn. Native display not yet exercised.'}
    manifest={'schemaVersion':1,'worldSource':'art/space_v4/runtime_v1/world.json','worldSha256':hashlib.sha256(world_path.read_bytes()).hexdigest(),'sourceHashes':{sources[k].name:sources[k].hash for k in SOURCE_PREFIXES},'entries':entries,'unresolved':{},'hiddenInformation':['No culprit names, votes, private phrase, attack image, precise missing time, dose or source-unread document content.','Internal region IDs/correctness are runtime-only and never baked as answer borders or labels.'],'reviewStatus':'Ten full-page diagrams directly inspected; run verify_v4_investigation_diagrams.py for source/UV/return and binding validation. Native visual acceptance remains separate.'}
    from v4_inspection_illustrations import apply as apply_illustrations
    apply_illustrations(manifest['entries'])
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'createdDiagrams':len(entries),'rasterSize':[W*S,H*S],'out':str(OUT),'centralOutputsWritten':False},ensure_ascii=False))


REVIEWED_SOURCE_HASHES={"11b": "380913610b608fa861e229632bf4cba3f42d4d26cd74b79f9295c854c163d546", "181": "8c5c23ebced38ac4673085e16250648bd24baa31ef525cb34ef6211557222213",
    "07": "b1edfc7e7ae33647240f71f4c3bb6ee8a8ae27bcab32d33cc84ff8f5248326e7",
    "13b1": "c1ec9d751cbed8050d56f418944e6c4e24c6dc1d4165871634147ca30a3597ca",
    "13b2": "8ef70848c2b354c93edc7a688fad47f3570dc9f57ec2d4e92775a0106dbcd48a",
    "14b1": "a6d335c13d1eabf793ddc73d111261f25d5a2863f1c0105d9ab635ef5d09798d",
    "14b3": "c51bd17fb2849eb0afc0327c4db1ab0320a5d2b06e56e6d5c1e914df782c487d",
    "15b2": "e09dce136bc2d2d3b7f99d1778cc80a7b86852f65b6235baef3efaf6c1397f98",
    "165": "e9c619cb70d8c0431188b6a5199251f8897816edb343e02589c64c3e6ad1661e",
    "166": "58051c5ce7db9f74ceb50bb5b46abc6937ec2eead9f0653b68b0072ace1dbf24",
    "183": "904b0bf7b33583f1a8a982aaac47d8a80b24d5f66a5733f85e35560d23b2fbb7",
    "184": "76ae6735f1906216b9c8bb04e0ba257ab87548a0cb5902a357c4ddff47862803",
    "185": "e15c2df443fa2af33a2a0ba9509d79c734c21da7c846e63b035c15a04486fef0"
}
if __name__=='__main__':make()
