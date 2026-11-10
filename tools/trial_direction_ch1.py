"""1장 재판 줄마다 연출(Claude 2026-11-04, 사양서 25). 한 줄씩 대사를 읽고 정했다.

debate 줄 : (pose, motion, yaw, shot, fx, font, size)   queue 줄 : (pose, fx, se)
pose  = 스프라이트 표(docs/spec/12) C01 기본 C02 미소 C03 웃음 C04 놀람 C05 화남 C06 슬픔 C07 통곡 C08 고민 C09 당황 C10 부끄 C11 공포
        C12 결의 C13 의심 C14 한숨 / T01 지목 T02 증언대 짚기 T03 끄덕임 T04 몰림 / U1~U6 인물 고유
motion= slide fly swirl slam wave shake assemble zoom rise type bounce spiral burst  (Game/Source/Debate.hpp)
shot  = 0 정면 밀기 1·2 좌우로 돌기 3 올려다보기 4 얼굴 가까이 5 높은 원경 6·7 크게 돌기 8 낮은 원경(옆 사람) 9 위에서 전체 10 낮은 옆 기울임 11 기운 클로즈업
yaw   = 글자 줄이 놓인 원근 판 각도(+ 오른쪽 끝이 멀다 / - 왼쪽 끝이 멀다)
"""
D = {}
Q = {}
def d(i, pose, motion, yaw=0, shot=-1, fx='', font=None, size=1.0):
    e = {'pose': pose, 'motion': motion}
    if yaw: e['yaw'] = yaw
    if shot >= 0: e['shot'] = shot
    if fx: e['fx'] = fx
    if font: e['font'] = font
    if size != 1.0: e['size'] = size
    D[i] = e
def q(i, pose, fx='', se=None):
    e = {'pose': pose}
    if fx: e['fx'] = fx
    if se: e['se'] = se
    Q[i] = e
P = 'v4:181:T1-NS-A0'
BH, DH, JU, PEN, GAE, SONG, SERIF = 'blackhansans/BlackHanSans-Regular.ttf', 'dohyeon/DoHyeon-Regular.ttf', 'jua/Jua-Regular.ttf', 'nanumpenscript/NanumPenScript-Regular.ttf', 'gaegu/Gaegu-Regular.ttf', 'songmyung/SongMyung-Regular.ttf', 'notoserifkr/NotoSerifKR-VF.ttf'

# ── NS-A01 넘어진 뒤의 압박 : 타이가가 사고로 덮으려 하고, 유우가 받아 넘긴다
d(P+'1:e:1d6afde9c0b0:1', 'C09', 'slide', -22, 8)                 # 타이가 「넘어졌을 수 있잖아」 땀 흘리며 서둘러 덮는다
d(P+'1:e:de33a528e958:1', 'U2', 'bounce', 18, 6)                  # 리쿠 동전 진자 흔들며 가볍게
d(P+'1:e:24a5765f0951:1', 'C02', 'slam', -14, 11, 'punch', DH, 1.1)  # 유우 약점 : 결론을 쾅 박는다
d(P+'1:e:152be6c0e755:1', 'C08', 'fly', 20, 7)                    # 소라 고민하며 다른 가능성
d(P+'1:e:40d6a08732f7:1', 'C13', 'slide', -26, 1)                 # 린 의심 곁눈질
d(P+'1:e:d9f4c1c3d4c1:1', 'C05', 'zoom', 0, 3, 'shake', BH, 1.1)   # 타이가 화를 내며 몰아붙임
q('v4:181:h-a27c42c646:e:48fb142da42a:1', 'U1')                   # 쇼 펜라이트 — 몸을 보라는 지적
q('v4:181:h-a27c42c646:e:72f98680c792:1', 'C13')

# ── NS-A02 서리에서 앞선 손까지 : 피해자를 먼저 공격한 사람으로 몰아감
d(P+'2:e:0333bd884b77:1', 'U3', 'bounce', 16, 8)
d(P+'2:e:de2b876c7983:1', 'U1', 'slide', -18, 2)                  # 아카리 약병 라벨 확인하듯 차분히
d(P+'2:e:8db2181eb5ca:1', 'T01', 'slam', 12, 11, 'punch', BH, 1.1)  # 타이가 약점 : 카에데에게 떠넘김
d(P+'2:e:2364e248b56f:1', 'C08', 'rise', -16, 6)
d(P+'2:e:3d00892faa66:1', 'U4', 'spiral', 0, 10, '', SERIF)       # 켄 손가락 튕기며 연극조 비꼼
d(P+'2:e:e432ddfba287:1', 'C14', 'type', 14, 4)                   # 린 한숨 — 말만 늘었다
q('v4:181:h-a27c42c646:e:c773014016be:1', 'U1')
q('v4:181:h-a27c42c646:e:32a69e89d50f:1', 'U4')

# ── NS-A03 시각이 없는 흔적과 문 기록 : 린이 동의점(문 기록)
d(P+'3:e:67110db471a1:1', 'U2', 'slide', -20, 8)                  # 코토 규칙 노트 펼침
d(P+'3:e:70f96074edf2:1', 'C13', 'bounce', 18, 1)
d(P+'3:e:649e148bd5bd:1', 'C09', 'shake', -12, 4)                 # 유우 불안 — 전부 모른다
d(P+'3:e:1830ada6783b:1', 'U2', 'fly', 22, 11, '', None, 1.05)    # 린 자물쇠 따는 손 — 문 기록은 남는다(동의점)
d(P+'3:e:67372888ab88:1', 'C08', 'rise', -14, 7)
d(P+'3:e:af6ebef1e726:1', 'C12', 'slide', 16, 5)
q('v4:181:h-a27c42c646:e:de0b0373d7d9:1', 'C13')
q('v4:181:h-a27c42c646:e:6cf4a8e83c73:1', 'C14')

# ── NS-A05 둘의 목격을 겹치기 전에
d(P+'5:e:727bd29e7e6f:1', 'U1', 'slide', -16, 8)                  # 코토 손뼉 쳐 정리 시작
d(P+'5:e:c3dac4c6a114:1', 'T02', 'slam', 10, 11, 'punch', BH, 1.1)  # 타이가 약점 : 증언대 짚고 단정
d(P+'5:e:d12c4f283996:1', 'C05', 'zoom', 0, 4, '', SONG)          # 사츠키 차갑게 끊음
d(P+'5:e:61a3f001d98c:1', 'U1', 'bounce', 20, 6)                  # 리쿠 카드 부채
d(P+'5:e:c4eb71210d85:1', 'U3', 'type', -12, 4)                   # 아카리 손목시계 — 합류 시각
d(P+'5:e:ef3dd68b65f5:1', 'C12', 'slide', 14, 5)
q('v4:181:h-a27c42c646:e:b2feb38d7895:1', 'U4')
q('v4:181:h-a27c42c646:e:2b804add1ca7:1', 'C12')

# ── NS-A06 대표가 사라지면 통화할 사람 : 쇼에게 동기를 씌움
d(P+'6:e:3574724e3fae:1', 'C13', 'bounce', 18, 1)
d(P+'6:e:b5bcbd414386:1', 'U5', 'type', -14, 4, '', SONG)         # 쇼 조용히 고개 숙이며
d(P+'6:e:87d6de621b87:1', 'U2', 'slide', 20, 7)
d(P+'6:e:90115dca00a0:1', 'C03', 'slam', -10, 11, 'punch', BH, 1.1)  # 타이가 약점 : 억지 웃음으로 밀어붙임
d(P+'6:e:b95d25e0a7fe:1', 'U4', 'slide', -18, 8)                  # 아카리 클립보드
d(P+'6:e:29b8d49c8cfd:1', 'C09', 'shake', 12, 4)
q('v4:181:h-a27c42c646:e:37a19df85e88:1', 'U5')
q('v4:181:h-a27c42c646:e:4803d9664cb3:1', 'U3')

# ── NS-A07 정리한 제목의 바깥 : 소라·타이가 순찰
d(P+'7:e:1da6357b9f88:1', 'U2', 'slide', -16, 8)                  # 소라 뒤통수 긁으며 해명
d(P+'7:e:a4d0da5c104e:1', 'C09', 'fly', 18, 6)
d(P+'7:e:d1f624bca2cc:1', 'C02', 'slam', -12, 11, 'punch', DH, 1.1)  # 유우 약점
d(P+'7:e:3f08a2a7dc86:1', 'U2', 'type', 14, 4)                    # 코토 원본 대조
d(P+'7:e:64c608be3472:1', 'C09', 'shake', -14, 7)
d(P+'7:e:79a4aa26c3e8:1', 'C13', 'slide', 18, 10)
q('v4:181:h-a27c42c646:e:18538afdc9b2:1', 'U2')
q('v4:181:h-a27c42c646:e:dc9d04387840:1', 'C05')

# ── NS-A08 같은 종이인 근거
d(P+'8:e:0666ebd30d9e:1', 'C09', 'slide', -20, 8)
d(P+'8:e:008a766f0b6b:1', 'C12', 'fly', 16, 2)
d(P+'8:e:e0a0df0d4672:1', 'U4', 'bounce', 20, 6)                  # 리쿠 동전이 사라지는 손 — 다시 뽑으면 생긴다
d(P+'8:e:4ce520b03800:1', 'T02', 'slam', -12, 11, 'punch', BH, 1.1)  # 타이가 약점
d(P+'8:e:7c84e3ae74b8:1', 'U2', 'type', 14, 4)                    # 나나 붕대 감듯 조심스레 펼침
d(P+'8:e:7d2010104ac1:1', 'U2', 'slide', -16, 1)
q('v4:181:h-a27c42c646:e:4abef47bb097:1', 'C13')
q('v4:181:h-a27c42c646:e:161b244d7569:1', 'U5')

# ── NS-A09 낮에 나눠 가졌다는 종이
d(P+'9:e:1c2dc559f254:1', 'U5', 'spiral', 0, 10, '', SERIF)       # 켄 객석 향해 팔 벌림
d(P+'9:e:0528a8885d4d:1', 'C09', 'shake', 14, 4)                  # 타이가 「언제 만졌는지도 모르는데」 흔들림
d(P+'9:e:6d4d73a5edca:1', 'C02', 'slam', -12, 11, 'punch', DH, 1.1)  # 유우 약점
d(P+'9:e:09733470bbc1:1', 'C12', 'slide', 16, 8)
d(P+'9:e:f7ad004de094:1', 'C13', 'bounce', -18, 6)
d(P+'9:e:b9b876dcd655:1', 'U2', 'slide', 14, 5)
q('v4:181:h-a27c42c646:e:9c6c108f7567:1', 'U4')
q('v4:181:h-a27c42c646:e:e8b2699aba08:1', 'C05')

# ── NS-A10 닫은 표찰이 확인한 것 : 타이가가 점점 몰린다
d(P+'10:e:4c147b0e2eef:1'.replace('A010', 'A10'), 'C12', 'slide', -16, 8)
d('v4:181:T1-NS-A10:e:4c147b0e2eef:1', 'C12', 'slide', -16, 8)   # 타이가 「그건 맞아」 버팀
d('v4:181:T1-NS-A10:e:6f722b6fcbc5:1', 'C13', 'fly', 18, 7)
d('v4:181:T1-NS-A10:e:935dc6933ea6:1', 'T02', 'slam', -10, 11, 'punch|shake', BH, 1.15)  # 약점 : 증언대를 내리치며 끝났다고
d('v4:181:T1-NS-A10:e:12f86db76853:1', 'U4', 'type', 14, 4, '', PEN)  # 나나 말을 삼키듯 작게
d('v4:181:T1-NS-A10:e:9f968f57c85f:1', 'T01', 'zoom', 0, 3)        # 린 지목
d('v4:181:T1-NS-A10:e:4d212a42a53e:1', 'C12', 'slide', -14, 4)     # 소라 진지하게
q('v4:181:h-a27c42c646:e:0192d492c766:1', 'C12')
q('v4:181:h-a27c42c646:e:7ebc92e32b78:1', 'T04', 'shake')
D.pop('v4:181:T1-NS-A10:e:4c147b0e2eef:1'.replace('T1-NS-A10', 'T1-NS-A010'), None)

# ── 인물 지목·증거·정답·지점 : 틀렸을 때 받아치는 사람, 맞았을 때 미오
q('v4:181:T1-PERSON-A01:e:089820e99fbc:1', 'C08')
q('v4:181:h-99b1a9b12b:e:207b72b93b60:1', 'U4')
q('v4:181:h-3ff4fcfcad:e:753668563d73:1', 'T01', '', 'v3se_305')
q('v4:181:h-99b1a9b12b:e:5c6c980201ba:1', 'C09')
q('v4:181:h-3ff4fcfcad:e:cd9665285a4d:1', 'T01', '', 'v3se_305')
q('v4:181:h-99b1a9b12b:e:cf78ecacda8f:1', 'U4')                   # 레이 차갑게 내려다봄
q('v4:181:h-3ff4fcfcad:e:82b51c9ba75c:1', 'T01', 'shake', 'v3se_305')  # 「타이가.」 지목
q('v4:181:h-99b1a9b12b:e:487fa566b502:1', 'C13')
q('v4:181:h-3ff4fcfcad:e:a203a4e55d9b:1', 'C12')
q('v4:181:h-99b1a9b12b:e:ff6dcb67cc0d:1', 'U4')
q('v4:181:h-99b1a9b12b:e:cd4ee7fe7707:1', 'C14')
q('v4:181:h-3ff4fcfcad:e:6d8e5eacfe9e:1', 'C12')
q('v4:181:h-99b1a9b12b:e:9fcdd812ce22:1', 'C13')
q('v4:181:h-3ff4fcfcad:e:be3c946a75b8:1', 'T03')

# ── PN-A02 패닉 : 조각이 증명한 동작
d('v4:181:T1-PN-A02:e:bf696f33c15a:1', 'T01', 'slide', -18)        # 소라가 타이가를 직접 가리킨다
d('v4:181:T1-PN-A02:e:7e5e871c5c4e:1', 'C05', 'slam', 10, -1, 'punch', DH, 1.1)  # 유우 약점 : 성급히 끝내자
d('v4:181:T1-PN-A02:e:d447f20d332d:1', 'U3', 'type', 14)          # 나나 고개 숙여
d('v4:181:T1-PN-A02:e:422502244c19:1', 'C06', 'shake', -14)        # 소라 감싸고 싶은 마음, 말끝 흐림
d('v4:181:T1-PN-A02:e:fcb0d356595f:1', 'C09', 'fly', 16)
d('v4:181:T1-PN-A02:e:20050e1e2e7f:1', 'C12', 'slide', -12)
q('v4:181:h-a27c42c646:e:ba76c8a1598c:1', 'C05')
q('v4:181:h-a27c42c646:e:5078808dff2c:1', 'C06')

# ── PN-A03 패닉 : 멎은 소리와 원래 고장
d('v4:181:T1-PN-A03:e:fd8c42942ad7:1', 'C09', 'shake', -16)
d('v4:181:T1-PN-A03:e:8c14a3115d25:1', 'U4', 'slide', 14, -1, '', SONG)  # 레이 차갑게
d('v4:181:T1-PN-A03:e:5b7daa8328cb:1', 'C05', 'slam', -10, -1, 'punch|shake', BH, 1.15)  # 타이가 약점 : 폭발
d('v4:181:T1-PN-A03:e:07e64542a36d:1', 'C13', 'fly', 16)
d('v4:181:T1-PN-A03:e:001d73d58466:1', 'U1', 'type', -12)          # 레이 회중시계
d('v4:181:T1-PN-A03:e:1816fea6ca89:1', 'C12', 'slide', 14)
q('v4:181:h-a27c42c646:e:b21f93ad2065:1', 'U4')
q('v4:181:h-a27c42c646:e:131f538b89b5:1', 'T04', 'shake')

# ── 반론 쇼다운·발굴·애너그램·추리 : 틀림/맞음 반응
q('v4:181:h-a27c42c646:e:79ca4198e804:1', 'C05', 'shake')          # 타이가 「그때 네가 아팠어?」
q('v4:181:h-a27c42c646:e:606b4a504fe1:1', 'U4')
q('v4:181:h-87b26dd186:e:3697a6904761:1', 'C08')
q('v4:181:h-87b26dd186:e:fbec8c6da60b:1', 'C12')
q('v4:181:h-87b26dd186:e:7711875c5f0f:1', 'C08')
q('v4:181:h-87b26dd186:e:401facf0e619:1', 'C12')

# ── FA-01 애너그램 성공 : 리쿠가 받아들이고 미오가 선을 긋는다
q('v4:163:T1-FA-01:e:70c4775ad2ea:1', 'T01', '', 'v3se_310')
q('v4:163:T1-FA-01:e:9ebe6136ec0b:1', 'U5')                         # 리쿠 드물게 진지한 얼굴
q('v4:163:T1-FA-01:e:780fdef1632e:1', 'C12')

# ── LIE-01 위증 논스톱 : 유우가 나나를 의심
d('v4:163:T1-LIE-01:e:f60f0091fcc8:1', 'C13', 'slide', -18, 8)
d('v4:163:T1-LIE-01:e:240765b8fce6:1', 'C13', 'type', 14, 4)
d('v4:163:T1-LIE-01:e:a1a476e5a82d:1', 'C08', 'fly', -14, 6)
d('v4:163:T1-LIE-01:e:e8d428dc5d57:1', 'T01', 'slam', 10, 11, 'punch', DH, 1.1)

# ── RS-01 반론 성공 뒤
q('v4:163:T1-RS-01:e:b3148485cede:1', 'C12')
q('v4:163:T1-RS-01:e:5ddbdf831026:1', 'C09')
q('v4:163:T1-RS-01:e:cc14633325dd:1', 'C08')
# ── AA-01 이론 무장 끝
q('v4:163:T1-AA-01:e:e08eec92939b:1', 'C12', 'shake', 'v3se_310')

# ── MG-01 클라이맥스 앞 : 타이가를 둘러싼 대화
q('v4:157:T1-MG-01:e:dca4f3dc7943:1', 'C12')
q('v4:157:T1-MG-01:e:c87d9facca95:1', 'C05', 'shake')               # 「내가 다 말했잖아」
q('v4:157:T1-MG-01:e:94a8187b27c8:1', 'C05')                        # 린 선을 긋는다
q('v4:157:T1-MG-01:e:0f7e49fe1608:1', 'C09')
q('v4:157:T1-MG-01:e:3d4090d64ade:1', 'T01')
q('v4:157:T1-MG-01:e:4d598ce2dd6e:1', 'U4')                         # 코토 곤란한 미소 — 고쳤다
q('v4:157:T1-MG-01:e:648d6b50f594:1', 'T03')
# ── MG-08 클라이맥스 뒤 : 타이가가 무너진다
q('v4:157:T1-MG-08:e:11dc2d6b85eb:1', 'C14')
q('v4:157:T1-MG-08:e:10ee6483ad66:1', 'U5')                         # 리쿠 진지
q('v4:157:T1-MG-08:e:c81d5c6aefc6:1', 'C05')
q('v4:157:T1-MG-08:e:8b6c88f3000b:1', 'U5')
q('v4:157:T1-MG-08:e:3027c4262d80:1', 'C06', 'shake')               # 「카에데도 바로 옆에 있었어」
q('v4:157:T1-MG-08:e:535933a3c9ca:1', 'C12')
q('v4:157:T1-MG-08:e:815e3b60f732:1', 'C07', 'shake')               # 울분 — 「그게 싫다고」
q('v4:157:T1-MG-08:e:7db681e6f04d:1', 'U6')                         # 아이 아주 작게 — 편하지 않다
q('v4:157:T1-MG-08:e:45b90712c138:1', 'C07')                        # 「그럼 틀려 줘」
q('v4:157:T1-MG-08:e:dd0793eebee4:1', 'C11', 'shake')               # 살고 싶다는 말 — 공포
q('v4:157:T1-MG-08:e:2cb61628ca4c:1', 'U6')                         # 하루카 멍하니 먼 곳(복선)
q('v4:157:T1-MG-08:e:f2b827ae927a:1', 'C14')
q('v4:157:T1-MG-08:e:a3d80bf23e82:1', 'C12')

# ── NS-T05e 문이 기록한 것과 사람 수
q('v4:11c1:h-a271c94da5:e:84ccd6ec1999:1', 'C13')
q('v4:11c1:h-a271c94da5:e:e48715c8417b:1', 'C08')
d('v4:11c1:h-37b313804d:e:deb78cc2b47e:1', 'U2', 'bounce', -16, 8)      # 하루카 셀카 들듯 가볍게
d('v4:11c1:h-37b313804d:e:86300ef0b5b8:1', 'C09', 'shake', 14, 4)
d('v4:11c1:h-37b313804d:e:1ff95f594396:1', 'U3', 'slide', -14, 2)
d('v4:11c1:h-37b313804d:e:73000eeee24d:1', 'U2', 'slide', 18, 5)
d('v4:11c1:h-37b313804d:e:fa8b97209393:1', 'C03', 'slam', -10, 11, 'punch', JU, 1.1)  # 하루카 약점 : 밝게 단정
d('v4:11c1:h-37b313804d:e:a540152a1212:1', 'C13', 'fly', 16, 6)
d('v4:11c1:h-37b313804d:e:54cf26baf1c5:1', 'T04', 'shake', -12, 4)

# ── MM-01 발굴 성공
q('v4:163:T1-MM-01:e:3110e30a4764:1', 'C12')
q('v4:163:T1-MM-01:e:9f610f61a2ca:1', 'C14')                        # 린 「그건 나도 틀렸어」

# ── SD-01 스크럼 앞뒤
q('v4:163:T1-SD-01:e:937915423b64:1', 'U3', '', None)               # 켄 반가면
q('v4:163:T1-SD-01:e:25782cb425c2:1', 'C05')
q('v4:163:T1-SD-08:e:7cf6e6f762df:1', 'U5')
q('v4:163:T1-SD-08:e:ac9aefc0bac3:1', 'U6')
q('v4:163:T1-SD-08:e:9f767228a509:1', 'T03')

# ── PD-01 패닉 : 둘 중 하나로 몰아감
q('v4:130:T1-PD-01:e:19f3f13be774:1', 'C12')
q('v4:130:T1-PD-01:e:c6a6c2c7e75d:1', 'U5')                         # 유우 조용해지면 불안
q('v4:130:T1-PD-01:e:05f1471dc310:1', 'C01')
q('v4:130:T1-PD-01:e:610ee96360be:1', 'C13')
q('v4:130:T1-PD-01:e:d9485ee6da1d:1', 'U4')                         # 아이 노려봄
q('v4:130:T1-PD-01:e:13e8c54e56db:1', 'U3')                         # 리쿠 혀 내밀고 윙크
q('v4:130:T1-PD-01:e:985f26027acf:1', 'C13')
q('v4:130:T1-PD-01:e:85b197954403:1', 'C02')
q('v4:130:T1-PD-01:e:e93046c37795:1', 'C14')
q('v4:130:T1-PD-01:e:73e872cca6e2:1', 'C08')
d('v4:130:T1-PD-01:e:82c72819f4eb:1', 'C09', 'shake', -14)
d('v4:130:T1-PD-01:e:f4adce243731:1', 'U2', 'slide', 16)
d('v4:130:T1-PD-01:e:fa2b6e30648a:1', 'U2', 'type', -12)            # 아이 졸린 눈 비비며
d('v4:130:T1-PD-01:e:7c7540fc4c76:1', 'C05', 'burst', 0, -1, 'punch|shake|swirl', BH, 1.15)  # 유우 약점 : 소리친다
d('v4:130:T1-PD-01:e:067d98bd2b87:1', 'C05', 'zoom', 0)
d('v4:130:T1-PD-01:e:b34c8d246102:1', 'U4', 'slide', 14)

def save():
    import json, pathlib
    root = pathlib.Path(__file__).resolve().parents[1]
    src = root / 'data/v4_story/trial_direction.json'
    cur = json.loads(src.read_text(encoding='utf-8')) if src.exists() else {'version': 1, 'debate': {}, 'queue': {}}
    cur['debate'].update(D); cur['queue'].update(Q)
    # 잘못된 id 를 막는다 : 실제 줄에 있는 id 만
    t = json.loads((root / 'data/v4_story/native_tasks.json').read_text(encoding='utf-8'))['tasks']
    ids = set()
    for v in t.values():
        for l in (v.get('debate') or {}).get('lines', []): ids.add(l['id'])
        for qq in v.get('queues', {}).values():
            for r in qq:
                if isinstance(r, dict) and r.get('eventId'): ids.add(r['eventId'])
    bad = [k for k in list(cur['debate']) + list(cur['queue']) if k not in ids]
    for k in bad: cur['debate'].pop(k, None); cur['queue'].pop(k, None)
    text = json.dumps(cur, ensure_ascii=False, indent=1) + '\n'
    src.write_text(text, encoding='utf-8')
    (root / 'Game/Assets/Data/v4_story/trial_direction.json').write_text(text, encoding='utf-8')
    print(len(cur['debate']), 'debate', len(cur['queue']), 'queue', 'dropped', bad)

if __name__ == '__main__':
    save()
