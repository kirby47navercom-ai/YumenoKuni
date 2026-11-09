"""First revised case: pair each reviewed image with its manuscript panel."""

import json
import re
from pathlib import Path

from v4_comic_geometry import project, slot_quad


ROOT = Path(__file__).resolve().parents[1]
STORY = ROOT / 'docs/design/rewrite_v5/07_1_3_4_5_6장_클라이맥스_콘티와_낭독.md'
ART = ROOT / 'art/revision_comic/chapter1'
ID = 'T1-CM-REV01'
BOOK = 'Assets/Data/revision_comic/chapter1.json'

CLUES = (
    ('새 보호대를 끼우다', '갈아 끼우기 전에 무엇을 뺐지?'),
    ('보수문의 바깥 고정판', '이 문이 실제로 열릴 수 있는지 어디를 봤지?'),
    ('내선의 정상 점검', '외부 발신기와 따로 움직인 건?'),
    ('정상이라고 적힌 줄', '반응하지 않은 장비 옆에는 뭐라고 적혔지?'),
    ('갈라지는 두 동선', '이때 두 사람은 각자 어느 쪽으로 갔지?'),
    ('마지막 출력 16번', '이때 출력 목록이 어디서 끝났지?'),
    ('앞문으로 들어간 카에데', '복도에서 먼저 본 사람은 누구였지?'),
    ('17번 출력', '빈 받침 위에 다음으로 나온 것은?'),
    ('마당에서 보인 한 사람', '이 자리에서 몇 명까지 볼 수 있었지?'),
    ('내선이 끊긴 때', '방과 창구 사이에서 무엇이 끊겼지?'),
    ('보고서의 뜯긴 끝', '두 사람이 붙든 종이는 어디가 찢어졌지?'),
    ('표찰을 바꾸고 합류', '나간 사람이 합류하기 전 문에 손댄 것은?'),
    ('벗긴 보호대에서 나온 조각', '발견 전에 어디에서 조각을 거뒀지?'),
    ('고정물과 압박의 대조', '고정물이 그 압박을 만들 수 있었나?'),
    ('17번에 들어맞는 조각', '모서리가 맞는 번호는 어느 쪽이지?'),
)

GATES = ('', '', '', '', '', '', 'AC', 'AC', 'BF', 'BF', 'GHI', 'GHI',
         'JKL', 'JKL', 'MN')

# These remain fixed on the sheet. Their paths are separate from the answer
# art, even when they show the same physical object at an earlier/later time.
CONTEXT = (
    ('ctxA', 'right_wrist_brace'), ('door_B_fixed_window', 'door_A_sensor'),
    ('contact_equipment', 'ctxH'), ('contact_equipment', 'patrol_two_versions'),
    ('patrol_two_versions', 'door_A_sensor'), ('door_A_sensor', 'printer_output'),
    ('door_A_sensor', 'ctxA'), ('ctxH', 'printer_output'),
    ('door_A_sensor', 'door_B_fixed_window'), ('contact_equipment', 'door_A_sensor'),
    ('printer_output', 'right_wrist_brace'), ('report_torn_edge', 'door_A_sensor'),
    ('right_wrist_brace', 'ctxA'), ('furniture_frost_detail', 'floor_ice_builtin_r1'),
    ('report_torn_edge', 'right_wrist_brace'),
)


def review_rows():
    lines = STORY.read_text(encoding='utf-8').splitlines()
    start = lines.index('## 1장 — 한 번 열었던 문')
    stop = next(i for i in range(start + 1, len(lines)) if lines[i].startswith('## '))
    rows = []
    for line in range(start, stop):
        match = re.fullmatch(r'\| (\d+) ([A-O]) \| (.+) \| “(.+)” \|', lines[line])
        if match:
            number, letter, _, narration = match.groups()
            assert int(number) == len(rows) + 1 and letter == chr(65 + len(rows))
            rows.append((line + 1, narration))
    assert len(rows) == len(CLUES)
    recap = next(i for i in range(start, stop) if lines[i].startswith('추가 복기.'))
    return rows, (recap + 1, re.findall(r'“([^”]+)”', lines[recap])[0])


def comic_stage():
    """Return no live task until all panel and context images are reviewed."""
    manifest = ART / 'reviewed.json'
    if not manifest.is_file():
        return None
    data = json.loads(manifest.read_text(encoding='utf-8'))
    fixed = set().union(*CONTEXT)
    required = {chr(65+i) for i in range(len(CLUES))} | {'decoy1', 'decoy2', 'recap'}
    source = {}
    for key in required | fixed:
        if key in data:
            filename = data[key]
            assert filename == f'{key}.webp' and (ART / filename).is_file(), key
            source[key] = f'Assets/Art/revision_comic/chapter1/{filename}'
        else:
            assert key not in required and not key.startswith('ctx'), key
            assert (ROOT / f'art/inspection_v4/delivery/{key}.webp').is_file(), key
            source[key] = f'Assets/Art/revision_comic/chapter1/{key}.webp'
    rows, recap = review_rows()

    def spoken(key, authored):
        line, text = authored
        return [{'type': 'say', 'id': f'{ID}:{key}:recap', 'actor': 'mio',
                 'speaker': '미오', 'text': text,
                 'source': {'file': STORY.name, 'location': '01-T06', 'line': line}}]

    slots, pages, stock = [], [], []
    for i, ((label, hint), requires, contexts) in enumerate(zip(CLUES, GATES, CONTEXT)):
        letter = chr(65+i)
        slots.append({'id': letter, 'answer': letter, 'holeHint': hint,
                      'options': [{'id': letter, 'label': label, 'image': source[letter],
                                   'response': spoken(letter, rows[i])}]})
        pages.append({'slots': [i], 'contexts': [source[key] for key in contexts],
                      'screenQuads': {str(i): slot_quad([i], i, len(contexts))}})
        stock.append({'originSlot': i, 'requires': [ord(key) - 65 for key in requires]})
    stock.insert(2, {'originSlot': -1, 'requires': [], 'image': source['decoy1'],
                     'label': '서랍에 놓인 보호대'})
    stock.insert(9, {'originSlot': -1, 'requires': [0, 2], 'image': source['decoy2'],
                     'label': '온전한 16번의 끝'})
    return {
        'id': ID, 'kind': 'climax', 'v4': True, 'title': '한 번 열었던 문', 'slots': slots,
        'comicPresentation': {'bookFile': BOOK, 'board': {}, 'pages': pages,
                              'slots': [{'holeHint': slot['holeHint']} for slot in slots],
                              'storyStock': stock, 'unlock': {'initialAutoFillEligibleSlots': list(range(6))},
                              'recap': spoken('records', recap), 'recapImage': source['recap'],
                              'completion': {'owner': 'task-success-queue'}},
        'presentation': {'music': {'operation': 'play', 'cue': 'bgm_trial_climax'}},
    }


def chapter_two_comic_stage(scene):
    """A staged book becomes playable only when the chapter art is complete."""
    art = ROOT / 'art/revision_comic/chapter2'
    manifest = art / 'reviewed.json'
    if not manifest.is_file():
        return None
    labels = (
        ('객석에서 겹친 문', '두 문이 겹쳐 보인 자리는 어디였지?'),
        ('공방에서 건넨 도면', '처음에 종이 한 장을 어느 쪽으로 밀었지?'),
        ('전날 시험한 반납판', '이때는 누가 안에서 문을 열어 봤지?'),
        ('점검 띠를 붙인 순간', '촬영기는 이때 무엇을 찍고 있었지?'),
        ('빌린 체크 겉옷', '누가 겉옷을 받았고 주머니는 누가 그대로 뒀지?'),
        ('반납판에 남은 열쇠', '실제로 열쇠를 받아서 표시한 사람은?'),
        ('안에서 열어 준 앞문', '예비 열쇠 없이 들어가게 해 준 건 누구였지?'),
        ('의상실 쪽의 체크 소매', '소매가 지나간 문은 기둥의 어느 쪽이었지?'),
        ('창구를 지나간 접시', '살아 있는 사람을 마지막으로 본 순간에 고리는 어디 있었지?'),
        ('점검표를 건넨 교대', '누가 종이를 받기까지 앞문 쪽에 남았지?'),
        ('서로 잡은 사본', '두 사람이 종이를 다시 놓으라고 했을 때 받침은 어디에 있었지?'),
        ('떨어진 작은 고리', '접시가 넘어지기 전에 바닥에 떨어진 것은?'),
        ('받침과 넘어진 접시', '접시 아래에 들어간 흔적은 어느 일이 먼저였는지 보여 줘.'),
        ('닫힌 덮개와 사본', '이때도 점검 띠는 그대로였어. 사본은 어느 쪽으로 갔지?'),
        ('앞문으로 실제 퇴실', '앞문을 나오는 사람에게 체크 겉옷과 고리가 있었나?'),
        ('예비 열쇠로 열린 문', '발견 직전에 문을 연 쪽은 안이었나, 밖이었나?'),
    )
    gates = ('','','','','','','AB','AB','CF','DG','EHI','EHI','KLJ','KLJ','MN','OD')
    page_slots = [[i] for i in range(10)] + [[10,11]] + [[i] for i in range(12,16)]
    # Fixed context must be independent of the solution art and readable
    # even when the corresponding stock pieces are still locked.
    contexts = (
        ('thresholds','stairs'), ('bench','pouch'), ('board','door-inside'), ('hatch','camera'),
        ('costume','pouch'), ('board','return-counter'), ('door-inside','hall'), ('stairs','low-tape'),
        ('tray','pouch'), ('watch','hall'), ('bench','tray'), ('floor','tray'),
        ('hatch','hall'), ('watch','door-inside'), ('hall','spare'),
    )
    required = {chr(65+i) for i in range(16)} | {key for pair in contexts for key in pair} | {'recap'}
    paths = json.loads(manifest.read_text(encoding='utf-8'))
    if set(paths) != required:
        raise ValueError('Chapter 2 reviewed comic manifest must name every panel and context')
    for key, filename in paths.items():
        if filename != f'{key}.webp' or not (art / filename).is_file():
            raise ValueError(f'Chapter 2 reviewed image not found: {key}')

    def picture(key):
        return 'Assets/Art/revision_comic/chapter2/' + paths[key]

    narration = []
    for offset, raw in enumerate(scene.body):
        if match := re.fullmatch(r'\d+\. .*\*\*미오\*\*\s+“([^”]+)”', raw):
            narration.append((scene.line + offset + 1, match[1]))
    assert len(narration) == 16
    both_line, both = narration[10]
    before, ring = both.rsplit('. ', 1)
    narration[10:11] = [(both_line, before + '.'), (both_line, ring)]
    ident = 'T2-CM-REV01'

    def spoken(index):
        line, text = narration[index]
        parts = [text]
        if index == 16:
            before, after = text.split('그것 때문에', 1)
            parts = [before.strip(), '그것 때문에'+after]
        return [{'type':'say','id':f'{ident}:{index}:recap:{part}','actor':'mio','speaker':'미오',
                 'text':words,'source':scene.source(line)} for part,words in enumerate(parts)]

    slots = []
    for index, (label, hint) in enumerate(labels):
        key = chr(65+index)
        slots.append({'id':key,'answer':key,'holeHint':hint,
                      'options':[{'id':key,'label':label,'image':picture(key),'response':spoken(index)}]})
    pages = []
    for indices, fixed in zip(page_slots,contexts,strict=True):
        rectangles = ([(542,14,544,622),(14,14,516,290),(14,316,516,320)] if len(indices)==1 else
                      [(14,14,516,486),(542,14,544,486),(14,512,516,124),(542,512,544,124)])
        quads = {}
        for index, (x,y,w,h) in zip(indices,rectangles):
            quads[str(index)] = project([(x,y),(x+w,y),(x+w,y+h),(x,y+h)])
        pages.append({'slots':indices,'contexts':[picture(key) for key in fixed],
                      'panelRects':rectangles,'screenQuads':quads})
    stock = [{'originSlot':i,'requires':[ord(key)-65 for key in gate]} for i,gate in enumerate(gates)]
    return {'id':ident,'kind':'climax','v4':True,'title':'공연이 끝나기 전에','slots':slots,
            'comicPresentation':{'bookFile':'Assets/Data/revision_comic/chapter2.json','board':{},
                                  'pages':pages,'slots':[{'holeHint':slot['holeHint']} for slot in slots],
                                  'storyStock':stock,'unlock':{'initialAutoFillEligibleSlots':list(range(6))},
                                  'recap':spoken(16),'recapImage':picture('recap'),
                                  'completion':{'owner':'task-success-queue'}},
            'presentation':{'music':{'operation':'play','cue':'bgm_trial_climax'}}}


def chapter_five_comic_stage():
    contexts = (('counter','copies'),('copies','pages'),('lock','notice'),('slot','seal'),('door','bandage'),
        ('bandage','door'),('window','cups'),('corridor','lock'),('slot','pouch'),('cups','pot'),
        ('preparation','seal'),('satchel','pages'),('satchel','counter'),('pouch','preparation'),('copies','notice'))
    labels = [('두 장만 받은 사츠키','처음에 실제로 읽을 수 있었던 쪽은 몇 장이지?'),
        ('현재 조건에 동의한 두 사람','오래전의 침묵과 구별되는 새 약속은?'),
        ('열기 전에 확인한 주의와 수량','보관실에 들어가기 전에 무슨 내용을 읽었지?'),
        ('처음 D에 남아 있던 봉함','열기 전에는 물건이 어떤 상태였지?'),
        ('복도에서 생긴 팔꿈치 상처','잔보다 앞서 일어난 충돌은?'),
        ('대답할 수 있었던 상태','팔을 살펴볼 때 쇼가 실제 확인한 것은?'),
        ('나중에 가져다 달라는 부탁','아직 잔을 건네지 않았을 때에는 무슨 말을 했지?'),
        ('같이 보관실로 향한 두 사람','처음 자료를 보러 함께 떠난 사람은?'),
        ('처음 자리와 나중에 빠진 물건','누가 갔는지와 구분해 대조할 실제 위치는?'),
        ('창가로 전달된 표식 잔','부탁 뒤에 실제로 잔이 건너간 때는?'),
        ('열 초보다 앞선 음용','되돌리기 전에 이미 끝난 일은?'),
        ('아카리가 보고한 열 초','누구의 기억으로만 남은 움직임인지 구별하자.'),
        ('발견 뒤 옮겨진 용기','처음 준비와 다른 시점의 손은?'),
        ('D 위치와 맞물린 실제 파단면','번호 외에 회수한 두 물건이 맞는 근거는?'),
        ('세 번째 쪽 전체를 공개한 때','사망 확인과 별개로 약속을 끝낸 조건은?')]
    return late_comic_stage(5,'차가 있던 시간','05-T04',contexts,labels)


def chapter_six_comic_stage():
    contexts = (('inspection','low-rail'),('low-rail','high-rail'),('doorway','sleeve'),
        ('sleeve','low-rail'),('doorway','corridor'),('low-rail','corridor'),
        ('doorway','report-desk'),('report-desk','reports'),('shelter','wrist'),
        ('reports','inspection'),('wrist','shelter'),('prototype','terminal'),
        ('wrist','notebook'),('motion','doorway'),('terminal','gate'))
    labels = [('시설 승인과 당시 위험','처음 시설을 열 때 실제로 남아 있던 선택은?'),
        ('옛 난간과 현재 난간','지금의 높이를 그대로 넣으면 무엇이 달라지지?'),
        ('첫 접촉이 기록된 때','옆문의 목격과 별개로 확인한 접촉은?'),
        ('먼저 붙잡았던 손을 놓은 뒤','두 움직임 사이에 손은 어떻게 됐지?'),
        ('옆문에서 보인 두 손','가림이 시작된 뒤에도 직접 볼 수 있었던 것은?'),
        ('난간 쪽으로 간 힘과 손','먼저 닿은 팔과 다른 위치에 남은 관찰은?'),
        ('얼굴을 보았을 때와 위치','보이는 움직임에 이름을 붙이려면 어느 때를 볼까?'),
        ('먼저 접수된 진술','나중의 요약에 그대로 남지 않은 문장은?'),
        ('먼저 대피한 자리에서 확인한 범위','대상마다 기억이 달라진 때를 어떻게 구분하지?'),
        ('같은 번호의 다른 문장','원본에서 요약이 되며 어떤 행위가 따로 일어났지?'),
        ('현재까지 남은 침묵 조건','기억의 삭제와 별개인 지속 효과는?'),
        ('시제품과 현재의 운영','현재의 선택과 안내자의 기원을 어떻게 구분하지?'),
        ('지금 적은 보호 페이지','그날 기억 대신 지금 확인해 적은 것은?'),
        ('과거의 직접 행위 확인','문서가 바뀐 일과 달리 당시의 손을 입증할 조합은?'),
        ('기원을 읽은 뒤의 재승인','처음 승인 이후에 별도 선택을 남긴 때는?')]
    return late_comic_stage(6,'옛 손과 현재의 문','06-R00',contexts,labels)


def late_comic_stage(chapter,title,location,contexts,labels):
    directory = f'chapter{chapter}'
    art = ROOT/'art/revision_comic'/directory
    manifest = art/'reviewed.json'
    if not manifest.is_file():
        return None
    images = json.loads(manifest.read_text(encoding='utf-8'))
    assert set(images) == set('ABCDEFGHIJKLMNO') | {key for pair in contexts for key in pair} | {'recap'}
    assert all(filename==key+'.webp' and (art/filename).is_file() for key,filename in images.items())
    lines = STORY.read_text(encoding='utf-8').splitlines()
    first = lines.index(f'## {chapter}장 — {title}')
    stop = next((i for i in range(first+1,len(lines)) if lines[i].startswith('## ')),len(lines))
    rows = []
    for at in range(first,stop):
        if match := re.fullmatch(r'\| (\d+) ([A-O]) \| (.+) \| “(.+)” \|',lines[at]):
            number,key,_,text = match.groups()
            assert int(number)==len(rows)+1 and key==chr(65+len(rows))
            rows.append((at+1,text))
    assert len(rows)==15
    recap = next(i for i in range(first,stop) if lines[i].startswith('추가 복기.'))
    recap_text, = re.findall(r'“([^”]+)”',lines[recap])
    gates = ('','','','','','','AD','AD','BC','FHI','FHI','EGK','EGK','LM','LM')
    ident = f'T{chapter}-CM-REV01'
    slots,pages,stock = [],[],[]
    rects = [(542,14,544,622),(14,14,516,290),(14,316,516,320)]

    def picture(key):
        return f'Assets/Art/revision_comic/{directory}/'+images[key]

    def spoken(key,line,text):
        return [{'id':f'{ident}:{key}:recap','type':'say','actor':'mio','speaker':'미오','text':text,
                 'source':{'file':STORY.name,'location':location,'line':line}}]

    for i,((label,hint),(line,text),fixed,gate) in enumerate(zip(labels,rows,contexts,gates,strict=True)):
        key = chr(65+i)
        slots.append({'id':key,'answer':key,'holeHint':hint,'options':[{'id':key,'label':label,
            'image':picture(key),'response':spoken(key,line,text)}]})
        x,y,w,h = rects[0]
        pages.append({'slots':[i],'contexts':[picture(name) for name in fixed],'panelRects':rects,
                      'screenQuads':{str(i):project([(x,y),(x+w,y),(x+w,y+h),(x,y+h)])}})
        stock.append({'originSlot':i,'requires':[ord(letter)-65 for letter in gate]})
    return {'id':ident,'kind':'climax','v4':True,'title':title,'slots':slots,
        'comicPresentation':{'bookFile':f'Assets/Data/revision_comic/{directory}.json','board':{},'pages':pages,
            'slots':[{'holeHint':slot['holeHint']} for slot in slots],'storyStock':stock,
            'unlock':{'initialAutoFillEligibleSlots':list(range(6))},'recap':spoken('last',recap+1,recap_text),
            'recapImage':picture('recap'),'completion':{'owner':'task-success-queue'}},
        'presentation':{'music':{'operation':'play','cue':'bgm_trial_climax'}}}


def chapter_four_comic_stage():
    art=ROOT/'art/revision_comic/chapter4'
    manifest=art/'reviewed.json'
    if not manifest.is_file():return None
    contexts=(('hall','door'),('hatch','support'),('cloth','support'),('floor','wall'),
              ('cup','door'),('door','floor'),('voice','strap'),('deadend','grille'),
              ('water','hatch'),('support','strap'),('door','stairs'),('deadend','hatch'),
              ('rescue','water'),('photo','rescue'),('cloth','strap'))
    images=json.loads(manifest.read_text(encoding='utf-8'))
    assert set(images)==set('ABCDEFGHIJKLMNO')|{key for pair in contexts for key in pair}|{'recap'}
    assert all(filename==key+'.webp' and (art/filename).is_file() for key,filename in images.items())
    lines=STORY.read_text(encoding='utf-8').splitlines();start=lines.index('## 4장 — 보이지 않는 곳에서 닫힌 것')
    stop=next(i for i in range(start+1,len(lines)) if lines[i].startswith('## '));rows=[]
    for at in range(start,stop):
        if match:=re.fullmatch(r'\| (\d+) ([A-O]) \| (.+) \| “(.+)” \|',lines[at]):
            number,key,_,text=match.groups();assert int(number)==len(rows)+1 and key==chr(65+len(rows));rows.append((at+1,text))
    assert len(rows)==15
    recap=next(i for i in range(start,stop) if lines[i].startswith('추가 복기.'));recap_text,=re.findall(r'“([^”]+)”',lines[recap])
    labels=(('새 벽이 없던 원래 홀','전날의 사진에서 확인한 원래 공간은?'),
        ('원래 덮개와 바깥 고정','새 방이 생기기 전부터 있던 설비는?'),
        ('두 접촉 위치의 점검 천','서로 다른 폭의 자국이 남는 두 동작은?'),
        ('원래 설비를 둘러싼 새 공간','새 벽이 생겨도 원래 남은 것은?'),
        ('면담 전에 받은 종이컵','안으로 들어가기 전 본인의 대답은 어디서 나왔지?'),
        ('같이 들어간 레이와 하루카','실제로 문을 넘은 두 사람은?'),
        ('입실 때 이미 걸린 손목 고리','밖의 말과 나중 사진 사이에 이어진 물건은?'),
        ('안쪽 문 뒤의 막힌 끝','문이 있다는 말과 실제로 퇴실하는 길은 같았을까?'),
        ('물속에서 가장자리로 올린 손','끝 고정 이전 살아 있던 몸은 어디 있었지?'),
        ('받침을 다시 넘어 끝 고정','첫 멈춤 뒤 따로 필요한 동작은?'),
        ('홀을 나온 뒤 계단에서 합류','유우가 실제로 본 동행은 어디서 시작됐지?'),
        ('뒤 길을 찾다가 발견한 손','미오와 나나가 안쪽에서 실제 확인한 것은?'),
        ('아카리의 보고와 현재의 재구조','되돌린 구조와 그보다 앞선 고정을 구별하자.'),
        ('꺼낸 뒤 남아 있던 생명','발견과 구조, 마지막 확인은 어느 순서였지?'),
        ('점검 천과 실제 끈의 두 눌림','입실·퇴실과 실제 고정의 자국을 함께 맞추자.'))
    gates=('','','','','','','AB','AB','CD','EFI','EFI','HJK','HJK','LM','LM')
    ident='T4-CM-REV01';slots=[];pages=[];stock=[];rects=[(542,14,544,622),(14,14,516,290),(14,316,516,320)]
    def picture(key):return 'Assets/Art/revision_comic/chapter4/'+images[key]
    def spoken(key,line,text):return [{'id':ident+':'+key+':recap','type':'say','actor':'mio','speaker':'미오','text':text,
        'source':{'file':STORY.name,'location':'04-T03a','line':line}}]
    for i,((label,hint),(line,text),fixed,gate) in enumerate(zip(labels,rows,contexts,gates,strict=True)):
        key=chr(65+i);slots.append({'id':key,'answer':key,'holeHint':hint,'options':[{'id':key,'label':label,'image':picture(key),'response':spoken(key,line,text)}]})
        x,y,w,h=rects[0];pages.append({'slots':[i],'contexts':[picture(key) for key in fixed],'panelRects':rects,
            'screenQuads':{str(i):project([(x,y),(x+w,y),(x+w,y+h),(x,y+h)])}})
        stock.append({'originSlot':i,'requires':[ord(key)-65 for key in gate]})
    return {'id':ident,'kind':'climax','v4':True,'title':'보이지 않는 곳에서 닫힌 것','slots':slots,
        'comicPresentation':{'bookFile':'Assets/Data/revision_comic/chapter4.json','board':{},'pages':pages,
            'slots':[{'holeHint':slot['holeHint']} for slot in slots],'storyStock':stock,
            'unlock':{'initialAutoFillEligibleSlots':list(range(6))},'recap':spoken('last',recap+1,recap_text),
            'recapImage':picture('recap'),'completion':{'owner':'task-success-queue'}},
        'presentation':{'music':{'operation':'play','cue':'bgm_trial_climax'}}}


def chapter_three_comic_stage():
    art = ROOT/'art/revision_comic/chapter3'
    manifest = art/'reviewed.json'
    if not manifest.is_file():
        return None
    contexts = (
        ('tools','ledger'),('glass','corridor'),('blindfold','paper'),('bench','clock'),
        ('envelope','door'),('clock','bench'),('glass','workshop'),('camera','corridor'),
        ('broadcast','workshop'),('bench','breathing'),('door','care'),('bench','door'),
        ('bench','podium'),('envelope','paper'),('glass','corridor'),('podium','ledger'),
    )
    required = {chr(65+i) for i in range(16)}|{key for pair in contexts for key in pair}|{'recap'}
    images = json.loads(manifest.read_text(encoding='utf-8'))
    assert set(images)==required,'Chapter 3 needs every reviewed answer and independent context'
    for key,filename in images.items():
        assert filename==key+'.webp' and (art/filename).is_file(),key
    lines = STORY.read_text(encoding='utf-8').splitlines()
    start = lines.index('## 3장 — 두 번째 확인')
    stop = next(i for i in range(start+1,len(lines)) if lines[i].startswith('## '))
    rows = []
    for at in range(start,stop):
        if match:=re.fullmatch(r'\| (\d+) ([A-P]) \| (.+) \| “(.+)” \|',lines[at]):
            number,letter,_,text = match.groups()
            assert int(number)==len(rows)+1 and letter==chr(65+len(rows))
            rows.append((at+1,text))
    assert len(rows)==16
    recap = next(i for i in range(start,stop) if lines[i].startswith('추가 복기.'))
    recap_text, = re.findall(r'“([^”]+)”',lines[recap])
    ident = 'T3-CM-REV01'
    def picture(key):
        return 'Assets/Art/revision_comic/chapter3/'+images[key]
    def spoken(key,line,text):
        return [{'id':f'{ident}:{key}:recap','type':'say','actor':'mio','speaker':'미오','text':text,
                 'source':{'file':STORY.name,'location':'03-T03','line':line}}]
    labels = (
        ('공용 칼을 꺼낸 리쿠','공용 대여 줄이 가리키는 순간은?'),
        ('직접 돌아본 실제 통로','반사 속 방향과 실제로 걸은 길은 어떻게 달랐지?'),
        ('가린 눈 앞에서 새로 쓴 값','누가 볼 수 있었고 누가 읽지 않았지?'),
        ('잠든 본체와 움직이는 몸','진입 뒤 실제로 움직인 몸은 어느 쪽이지?'),
        ('떠난 뒤 전달된 봉투','봉투를 넘길 때 두 사람은 어디 있었지?'),
        ('돌아왔다고 한 대답','시계가 지난 것 말고 어느 몸이 움직였지?'),
        ('미로에서 일어난 첫 공격','처음 손을 댄 장소와 그 뒤 이동은?'),
        ('사진 밖을 이은 관찰','실제 복도에서 누가 발언의 시작과 끝을 이어 봤지?'),
        ('첫 방송 뒤의 수사','이때 확인한 피해자는 어느 현장에 있었지?'),
        ('다시 확인한 호흡','첫 방송 뒤에도 무엇이 남아 있었지?'),
        ('보호와 수사로 나뉜 자리','두 번째 공격 전에 누가 어디 남았지?'),
        ('대기실에서 일어난 두 번째 공격','첫 현장과 다른 곳에서 다친 몸은?'),
        ('돌아오지 못한 원래 주인','본체 사망 뒤 무엇이 고정됐지?'),
        ('공개보다 먼저 나온 원문','거짓으로 읽은 말과 실제 종이는 어느 순서였지?'),
        ('두 공격 사이 같은 몸의 경로','새로 들어오는 가설이 설명해야 할 관찰은?'),
        ('외형과 구별한 투표 이름','마지막에 책임을 물을 이름은 어느 쪽이지?'),
    )
    gates = ('','','','','','','ACE','ACE','BDF','BDF','HIJ','HIJ','KLG','KLG','MN','MN')
    slots,pages,stock = [],[],[]
    rectangles = [(542,14,544,622),(14,14,516,290),(14,316,516,320)]
    for i,((label,hint),(line,text),fixed,gate) in enumerate(zip(labels,rows,contexts,gates,strict=True)):
        key = chr(65+i)
        slots.append({'id':key,'answer':key,'holeHint':hint,'options':[
            {'id':key,'label':label,'image':picture(key),'response':spoken(key,line,text)}]})
        x,y,w,h = rectangles[0]
        pages.append({'slots':[i],'contexts':[picture(name) for name in fixed],'panelRects':rectangles,
                      'screenQuads':{str(i):project([(x,y),(x+w,y),(x+w,y+h),(x,y+h)])}})
        stock.append({'originSlot':i,'requires':[ord(letter)-65 for letter in gate]})
    return {'id':ident,'kind':'climax','v4':True,'title':'두 번째 확인','slots':slots,
        'comicPresentation':{'bookFile':'Assets/Data/revision_comic/chapter3.json','board':{},'pages':pages,
            'slots':[{'holeHint':slot['holeHint']} for slot in slots],'storyStock':stock,
            'unlock':{'initialAutoFillEligibleSlots':list(range(6))},
            'recap':spoken('last',recap+1,recap_text),'recapImage':picture('recap'),
            'completion':{'owner':'task-success-queue'}},
        'presentation':{'music':{'operation':'play','cue':'bgm_trial_climax'}}}
