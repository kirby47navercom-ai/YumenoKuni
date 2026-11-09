"""Authored daily-life routes; never concatenate mutually exclusive replies."""

import re

from build_v4_story import SPEAKERS


BRANCH = re.compile(r'^(?:#{3,4} |\*\*)([ABC])\. (.+?)(?:\*\*)?$')

FIRST_SPACES = {
    '01-D00':'dining_room', '01-D01':'hotel_corridor', '01-D01a':'maintenance_workshop',
    '01-D01e':'hotel_corridor', '01-D01g':'hotel_corridor', '01-D01b':'hotel_corridor',
    '01-D01d':'hotel_lobby', '01-D01c':'hotel_lobby', '01-D01f':'hotel_corridor',
    '01-D01j':'hotel_lobby', '01-D01h':'hotel_lobby', '01-D01i':'park_main_gate',
    '01-D02':'hotel_corridor', '01-D02g':'hotel_lobby', '01-D02b':'service_lounge',
    '01-D02h':'dining_room', '01-D02i':'plaza', '01-D02a':'hotel_lobby',
    '01-D02e':'hotel_lobby', '01-D02c':'hotel_lobby', '01-D02j':'clinic',
    '01-D02d':'staff_passage', '01-D02m':'staff_passage', '01-D02f':'dining_room',
    '01-D02k':'plaza', '01-D02l':'park_main_gate', '01-D02n':'hotel_corridor',
    '01-D03k':'hotel_lobby', '01-D02o':'dining_room', '01-D03m':'hotel_lobby',
    '01-D03j':'hotel_lobby', '01-D03i':'hotel_lobby', '01-D03f':'dining_room',
    '01-D03d':'dining_room', '01-D03e':'service_lounge', '01-D03a':'staff_passage',
    '01-D03b':'service_lounge', '01-D03h':'service_lounge', '01-D03l':'hotel_corridor',
    '01-F02':'hotel_lobby', '01-F03':'dining_room', '01-F04':'plaza',
    '01-F05':'service_lounge', '01-F06':'maintenance_workshop',
    '01-F07':'hotel_corridor', '01-F08':'dining_room',
}

FIRST_JOINS = {
    '01-D00':'### 식기를 돌려놓을 때', '01-D01j':'### 식사 전의 다른 길',
    '01-D01h':'### 지금 안 바꾸고 두는 것', '01-D02e':'### 잘 자라는 말 앞에서',
    '01-D02k':'### 합류', '01-F06':'### 합류와 뒤에서 듣는 대답',
    '01-F07':'### 합류', '01-F08':'### 각자가 치우는 것',
}

FIRST_SPACES.update({
    '02-D01':'dining_room','02-D02':'performance_stage','02-D02f':'dining_room',
    '02-D02a':'dining_room','02-D02h':'hotel_corridor','02-D02b':'dining_room',
    '02-D02c':'dining_room','02-D02d':'dining_room','02-D02e':'hotel_corridor',
    '02-D02i':'hotel_corridor','02-D02g':'dining_room','02-D03':'maintenance_workshop',
    '02-D03a':'dining_room','02-D03b':'maintenance_workshop','02-D03c':'performance_stage',
    '02-D03d':'hotel_lobby','02-D03e':'performance_stage','02-D03f':'staff_passage',
    '02-D04':'performance_stage','02-D04r':'performance_stage','02-D04a':'performance_stage',
    '02-D04l':'dining_room','02-D04t':'dining_room','02-D04b':'performance_stage',
    '02-D04e':'performance_stage','02-D04h':'performance_stage','02-D04g':'performance_stage',
    '02-D04i':'dining_room','02-D04f':'hotel_corridor','02-D04v':'performance_stage',
    '02-D04x':'performance_stage','02-D04j':'performance_stage','02-D04m':'hotel_corridor',
    '02-D04k':'maintenance_workshop','02-D04s':'dining_room','02-D04u':'park_garden',
    '02-D04w':'dining_room','02-D04c':'operating_archive','02-D04d':'performance_stage',
    '02-D05':'performance_stage','02-D05a':'performance_stage','02-D05b':'performance_stage',
    '02-D05c':'dining_room','02-D06a':'theatre_preparation','02-D06':'theatre_preparation',
    '02-D07':'performance_stage','02-F02':'dining_room','02-F03':'hotel_lobby',
    '02-F04':'can_toss_booth','02-F05':'hotel_rest_lounge','02-F06':'maintenance_workshop',
    '02-F07':'hotel_lobby','02-F08':'performance_stage','02-F09':'park_garden','02-F10':'hotel_lobby',
})
FIRST_JOINS.update({
    '02-D02b':'**합류.**','02-F06':'### 합류와 뒤에서 듣는 대답',
    '02-F07':'### 합류','02-F09':'### 낮은 담이 가려지는 쪽','02-F10':'### 재단을 마친 뒤',
})

SECOND_COMPACT = {
    '02-D02f':[
        ('아이에게 지금 모자라는 몫을 먼저 확인한다.','미오','빈 포장과 남은 양을 따로 봤다. 린은 직접 기억하는 수만 자기 손으로 적었다.',True),
        ('린에게 같이 갔던 사람에게도 먼저 묻자고 한다.','미오','린은 물을 수는 있지만 같이 있었던 이유를 공용 줄에 올리지는 말라고 했다. 받은 사람의 이름을 공개하지 않았다.',True),
        ('코토가 붙이려던 새 행을 뒤집어 둔다.','미오','코토는 자기 이름만 적어 뒀다고 했다. 그 이름을 남의 허락으로 쓰지 않고 빈 접수 줄을 뒤집었다.',True)],
    '02-D02h':[
        ('작은 유리만 천으로 가린다.','미오','계단에서는 바닥 길만 보이고 유리 뒤 사람은 보이지 않았다. 린이 천 끝의 먼지 묻은 쪽을 안으로 접었다.',True),
        ('유리를 그대로 두고 밤에 안으로 부르지 않기로 한다.','미오','아이는 자기 방에서 누가 두드리면 직접 답하겠다고 했다. 린은 불이 켜져 있어도 놀이가 다시 시작한 건 아니라고 했다.',True),
        ('잠깐만 껐다가 낮은 쪽을 걸어 본다.','미오','린이 아랫길을 걸었다. 어두우면 바닥 턱을 못 찾을 수 있어 불을 다시 켰다. 켄은 어두운 쪽으로 더 가지 않았다.',True)],
    '02-D02i':[
        ('유우가 지금 먼저 내려오게 한다.','미오','아이는 이름을 부르지 않고 비켰다. 유우가 상자에 손대지 않고 자기 속도로 내려왔다.',True),
        ('아이에게 상자를 어디에 두고 싶었는지 묻는다.','미오','아이는 아래의 발을 미리 봤으면 상자를 바깥으로 돌렸을 거라고 했다. 다른 사람에게도 능력을 말하겠다는 뜻은 아니었다.',True),
        ('똑같이 한 번 더 보자고 한다.','유우','똑같이 안 된다고 했으면 네가 이번에 안 한 게 보이잖아. 나는 싫어.',False)],
    '02-D03a':[
        ('물러난다.','미오','난간으로 나와 빈 접시를 받쳤다. 종이 구기는 소리는 들렸지만 받는 사람은 못 봤다. 건넨 봉투 하나만 기록했다.',True),
        ('남는다.','미오','봉투를 받은 사람이 기둥 뒤에서 나와 나와 눈이 마주쳤다. 지금 묻지는 않겠다고 했다. 공용 기록에는 봉투 하나만 남겼다.',True)],
    '02-D03f':[
        ('가까운 턱을 따라 걷는다.','미오','발이 낮아지는 곳과 서로 지나갈 폭을 봤다. 끝의 가려진 문은 열리지 않았다.',True),
        ('아이가 돌아설 때까지 비킨다.','미오','아이와 린이 받침을 함께 들었다. 둘이 옆으로 비키자 빈 통을 든 다른 사람이 지나갔다.',True),
        ('닫힌 쪽을 먼저 묻는다.','미오','린은 왜 자기에게만 묻느냐고 했다. 아이는 바구니를 그쪽으로 가져갈 필요는 없다고 했다. 닫힌 곳 뒤에 또 문이 있는지는 못 봤다.',True)],
    '02-D04a':[
        ('입구 쪽을 비운다.','미오','리쿠는 위에서 준비실 쪽을 가리켰지만 내려와 의상실 표찰을 읽고 고쳤다. 위와 아래에서 가리키는 문이 달랐다.',True),
        ('안쪽 벽으로 옮긴다.','유우','아직이야. 나 기타 들고 앞에 서면 그때 들어와.',False)],
    '02-D04l':[
        ('빈 자리.','아이','제가 자리 맡아 드리는 데까지는 안 할래요. 오늘 여기 계신 분 거부터 주세요.',False),
        ('그대로.','미오','유우는 아이에게도 말할지 다음날 생각하겠다고 했다. 아이는 무슨 말이었는지 묻지 않고 먹던 것을 마저 먹었다.',True),
        ('그릇.','미오','켄이 다 먹었다는 표를 붙여 달라고 했다. 아이는 평가할 생각은 없다며 빈 그릇을 받았다.',True)],
    '02-D04x':[
        ('차례 티켓을 벽 바깥으로 옮긴다.','미오','소라가 자기가 가지러 가겠다고 하자 유우가 옆 기둥에 티켓을 끼웠다. 두 문을 구분해 본 것은 아직 아니었다.',True),
        ('배식표를 먼저 꺼낸다.','아이','이쪽 칸은 한 사람 대답을 받았어요. 그 밑에 누구도 아직 와 보지 않았고요.',False),
        ('리쿠에게 빈 티켓을 준다.','미오','리쿠가 린에게 먼저 가져가라 했지만 린이 돌려줬다. 소라가 떨어진 티켓을 주워 자기 쪽에 들었다.',True)],
    '02-D04k':[
        ('린 열쇠.','린','그건 내 이름 옆에 일 붙인 거고.',False),
        ('열리는 집.','린','문 수리야? 부동산이야?',False),
        ('간판은 린이 정할 때까지 기다린다.','린','나중에 내가 별로인 거 정해도 손님이면 별로라고 해.',False)],
    '02-D05c':[
        ('아이가 공용 표를 먼저 작성하게 둔다.','미오','린이 적힌 수를 직접 봤다. 다른 사람도 길을 찾도록 적은 문서까지 보여 주겠다고 하지는 않았다.',True),
        ('린이 먼저 주었던 물건의 내역을 확인한다.','미오','린이 직접 본 두 번의 일을 말했다. 그 사람이 실제로 어디 갔는지는 모른다고 덧붙였다.',True),
        ('이 자리에서 이름을 먼저 묻지 않는다.','미오','두 사람이 받은 것을 어떻게 정할지 들었다. 아이가 다시 묻겠다고 해도 이미 대신 확인했다고 쓰지 않았다.',True)],
    '02-F02':[
        ('비워 둔다.','아이','제가 빈 그릇을 내려놓을게요. 그분이 가져가시려면 제가 없을 때도 되게.',False),
        ('직접 다시 묻는다.','아이','다음 배식 전에 제가 한 번만 물을게요. 미오 씨가 같이 서 있으면 이미 정해 놓고 온 것처럼 보일 수 있어요.',False)],
}

# Compact manuscript choices contain action directions rather than dialogue blocks.
# These are the visible observations for the selected action only.
FIRST_COMPACT = {
    '01-D02':[
        ('당사자에게 돌린다.','카에데','내 번호는 내가 옮겨 적을게. 다른 사람 번호까지 밖에 붙일 거야?',False),
        ('반납 안내를 붙인다.','미오','공개판에서 방 번호와 이름을 떼고 반납 위치만 남겼다. 나나는 자기 방에 와도 되는지 다시 물으면 직접 답하겠다고 했다.',True)],
    '01-D02i':[
        ('바깥에서 오는 사람을 기다린다.','미오','리쿠가 돌아와 뒤가 비었다고 손짓할 때까지 둘은 끈을 놓지 않았다. 바깥에서 누가 실제로 왔는지는 아직 보지 못했다.',True),
        ('받침을 안으로 함께 민다.','미오','바닥의 받침이 닿는 쪽을 짚었다. 카에데가 놓기 전에 유우가 이제 팔이 덜 당긴다고 말했다.',True),
        ('리쿠에게 실제 길을 안내해 달라고 한다.','미오','리쿠는 우회할 쪽을 짚고 자기가 돌아갈 방향부터 말했다. 나는 그가 가는 끝까지 본 것은 아니었다.',True)],
    '01-D02l':[
        ('‘안에서 문을 열 수 없어요’라고 쓴다.','미오','우리가 확인한 철문이 닫혀 있다는 말만 썼다. 다른 방의 문까지 전부 열리지 않는다고 적지는 않았다.',True),
        ('‘밖에서 이쪽으로 연락해 주세요’라고 쓴다.','미오','전화번호는 몰랐다. 아무 숫자도 쓰지 않고 이쪽 위치를 표시했다. 실제 신호나 답이 생긴 것은 아니었다.',True),
        ('글자는 쓰지 않고 천이 가려지는 면부터 정리한다.','미오','사츠키가 낮은 쪽에서 시야를 확인했다. 하루카는 아직 쓰지 않은 거지 글을 못 쓰게 한 것은 아니라고 말했다.',True)],
    '01-D02n':[
        ('무슨 소리를 먼저 확인할지 적는다.','미오','외부 사람의 대답과 내부 안내를 구별해 듣는 방법만 썼다. 이름과 방 번호는 추가하지 않았다.',True),
        ('깨워 달라고 실제로 말한 사람을 남긴다.','미오','타이가와 나나는 누구에게 언제 말할지 따로 정했다. 옆에 앉아 있던 켄에게도 같은 부탁을 했다고 쓰지는 않았다.',True),
        ('지금은 아무 명단도 만들지 않는다.','타이가','그때 가서 다른 데 있을 수 있으니까, 내가 안 보이면 이쪽부터 봐.',False)],
    '01-D02o':[
        ('두 사람이 더 올 수 있게 열어 둔다.','미오','손을 놓자 문이 닫혔다. 다시 오는 사람은 손잡이를 잡아야 했다. 아이는 자기가 섰을 때 두 자리가 남았다고 했다.',True),
        ('닫고 밥을 먹는다.','미오','문 밖 대사가 작아지고 카에데 말이 들렸다. 유우는 누가 나가는지 끝까지 보지는 않았다.',True),
        ('문 대신 자기 그릇을 옮긴다.','미오','카에데가 통로를 비워 직접 앉았다. 유우가 말을 걸려 하자 먹고 나서 말하겠다고 손짓했다.',True)],
    '01-D03m':[
        ('먼저 읽어도 될지 묻는다.','리쿠','지금은 안 돼. 네가 답할 수 있는 말도 아니야.',False),
        ('쓸 거 없으면 남는 종이를 치운다.','미오','사츠키는 빈 종이만 거뒀다. 이름을 못 봤다고 접힌 것까지 버리지는 않았다.',True),
        ('카에데한테 자기가 하고 싶은 말을 물어본다.','미오','카에데는 먼저 넣을 이야기를 알아서 고르겠다고 했다. 다른 사람의 질문을 빼겠다는 말은 아니었다.',True)],
    '01-D03h':[
        ('창구에 둔다.','미오','지나갈 때 쓰도록 두고 간다고 말했다. 아카리는 손잡이를 자기 쪽으로 돌렸지만 전원을 켜지는 않았다.',True),
        ('나나에게 준다.','나나','돌려주신 곳은 적을게요. 그 전에 무슨 일이 있어서 가져오셨는지는 아까도 안 물었어요.',False),
        ('쇼에게 돌려준다.','쇼','알겠습니다. 저도 받는 사람의 대답이 있었다고 적지는 않겠습니다.',False)],
}


FIRST_COMPACT.update(SECOND_COMPACT)

FIRST_SPACES.update({
    '03-D01':'dining_room','03-D01i':'dining_room','03-D01a':'maintenance_workshop',
    '03-D01g':'maintenance_workshop','03-D01b':'theatre_preparation','03-D01c':'garden_rest_area',
    '03-D01d':'performance_stage','03-D01r':'hotel_corridor','03-D01l':'mirror_maze',
    '03-D01u':'mirror_maze','03-D01w':'mirror_maze','03-D01f':'mirror_maze',
    '03-D01h':'hotel_lobby','03-D01k':'mirror_waiting','03-D01m':'hotel_lobby',
    '03-D01o':'dining_room','03-D0C':'garden_rest_area','03-D01p':'dining_room',
    '03-D01n':'can_toss_booth','03-D01q':'performance_stage','03-D01s':'hotel_lobby',
    '03-D01y':'record_room','03-D01z':'record_room','03-D0B':'hotel_rest_lounge',
    '03-D0E':'ticket_booth','03-D0F':'ticket_booth','03-D01v':'hotel_lobby',
    '03-D0D':'hotel_corridor','03-D01x':'hotel_corridor','03-F01':'performance_stage',
    '03-F02':'performance_stage','03-F03':'park_garden','03-F04':'theatre_preparation',
    '03-F05':'mirror_maze','03-F06':'hotel_lobby',
})
FIRST_JOINS['03-F04']='### 합류'
FIRST_COMPACT.update({
    '03-D0C':[
        ('그늘에 남은 의자만 가리킨다.','미오','소라가 직접 걸어가 앉았다. 의자가 흔들리자 두 손으로 받쳤다. 하루카가 모래를 치우고 다시 앉아 보라고 했다.',True),
        ('하루카가 쓰던 자리를 되돌린다.','하루카','둘이 한 번에 옮기자. 내가 지금 부탁했어.',False),
        ('잠깐 자리를 비운다.','미오','물을 가져왔다. 돌아오자 사츠키가 자기가 더운 데 먼저 앉았다고 말해 줬다. 그동안의 대화를 내가 직접 들은 것은 아니었다.',True)],
    '03-D01s':[
        ('리쿠가 그린 얼굴을 보이게 놓는다.','미오','그림을 세우려다 밑이 기울어 넘어졌다. 리쿠가 한 번 받쳐 달라고 했다. 내가 받치자 웃는 입이 바깥을 향했다.',True),
        ('사츠키가 그린 얼굴을 보이게 놓는다.','사츠키','너도 잠 안 오면 그쪽 얼굴 해.',False),
        ('두 얼굴을 눕혀 둔다.','미오','평평한 면에 두 그림을 눕혔다. 리쿠는 마지막으로 그린 면을 아래로 돌려 두고 먼저 온 사람이 보면 된다고 했다.',True)],
    '03-D01y':[
        ('둘이 먼저 말할 때까지 남는다.','미오','한 사람씩 지날 폭부터 비웠다. 리쿠는 처음 와서 읽으려던 자료가 있다고만 했다. 번호나 새 실험 문장을 묻지는 않았다.',True),
        ('나나와 좁은 길을 먼저 건너 본다.','미오','벽 쪽에서 나나의 발을 봤다. 둘 다 안쪽까지 들어가지는 않았다. 켄이 따라오지 않았다고 이 길을 모른다고 할 수는 없었다.',True),
        ('의자를 놓을 곳만 정하고 먼저 떠난다.','미오','리쿠가 왜 앞에서 기다리게 했는지 물었다. 켄도 자기 뜻으로 서 있다고 답했다. 헤어진다고 자료실 사용을 금지한 것은 아니었다.',True)],
    '03-D01z':[
        ('안쪽으로 한 개만 먼저 가져간다.','소라','끝나면 네가 들어오고 싶은지 물어볼게.',False),
        ('둘 다 밖에 둔다.','미오','유우는 공연 사진을 보고 싶었다는 말을 취소하지 않았다. 소라가 먼저 보는 동안 문틈으로 들여다보지도 않았다.',True),
        ('소라가 끄기 전에는 아무도 손대지 않게 한다.','미오','소라는 자기가 멈추고 먼저 나갈 수도 있지 않느냐고 물었다. 셋이 같은 때까지 꼭 앉아 있겠다는 약속은 하지 않았다.',True)],
    '03-D0B':[
        ('책을 사츠키에게 준다.','미오','사츠키는 책에 쓴 대로 가야 할 것 같아 싫다고 했다. 벤치에 두면 자기 마음대로 펼쳐 보겠다고 했다.',True),
        ('하루카에게 마지막 문장만 읽어 준다.','미오','하루카가 원래 어디에 살던 사람이냐고 물었다. 나도 그 이름은 못 봤다고 했다. 마지막에 누가 문을 열었는지는 적혀 있지 않았다.',True),
        ('먼저 주운 곳에 두고 나간다.','미오','사츠키가 안에 있던 사람이 누구를 먼저 들였는지는 모른다고 했다. 출판 정보 뒤에서 다른 메시지를 찾지는 않았다.',True)],
    '03-D0E':[
        ('하루카의 처음 찍은 쪽을 묻는다.','미오','하루카가 방금 찍은 입구의 꺾인 바닥을 보여 줬다. 카메라에 어릴 때 사진은 없었다.',True),
        ('나나가 비켜 준 자리에 앉는다.','미오','나나가 왜 앉았는지 물었다. 조금 쉬려고 왔다고 했다. 나나는 쓰던 날짜를 마저 적었다.',True),
        ('아무도 안 나오면 먼저 나간다.','미오','하루카는 같이 걷다 자료실 전에 갈라지겠다고 했다. 나나는 하던 일을 끝내고 오겠다고 했다.',True)],
    '03-D0D':[
        ('켄이 서 있던 곳으로 돌아간다.','미오','난간 옆으로 들어갔다. 그 자리에서는 색지에 글이 없는 것이 보였다. 켄도 자기가 잘 보고 들어왔다는 말을 더 하지는 않았다.',True),
        ('유우가 멈췄던 곳에 선다.','미오','종이가 걸린 모양만 보이고 팔에 일부 가렸다. 나도 표가 있는 줄 알았다고 말했다. 그 뒤의 글까지 읽은 것은 아니었다.',True),
        ('난간을 옆으로 치운다.','미오','코토와 양끝을 들어 길을 비웠다. 켄은 치우러 오지 않았다. 색지는 아직 그의 손에 있었다.',True)],
    '03-F01':[
        ('묻는다.','유우','한 번은 물어도 돼? 싫다고 하면 더 안 물을게.',False),
        ('그대로 둔다.','미오','네가 안 물어본 건 알아. 안 물어보고 기다렸다는 건 내가 쓸 수 있어.',False)],
})

FIRST_SPACES.update({
    '04-D00':'maintenance_workshop','04-D00a':'hotel_rest_lounge','04-D00e':'hotel_rest_lounge',
    '04-D00h':'hotel_rest_lounge','04-D00i':'maintenance_workshop','04-D00m':'maintenance_workshop',
    '04-D00l':'maintenance_workshop','04-D00g':'hotel_rest_lounge','04-D00b':'ticket_booth',
    '04-D00j':'ticket_booth','04-D00c':'dining_room','04-D00n':'dining_room',
    '04-D00d':'garden_rest_area','04-D00o':'garden_rest_area','04-D00f':'maintenance_workshop',
    '04-D00k':'hotel_rest_lounge','04-D00r':'dining_room','04-D00p':'dining_room',
    '04-D00q':'can_toss_booth','04-D00s':'park_garden','04-D01a':'inspection_hall_normal',
    '04-D01d':'inspection_hall_normal','04-D01e':'inspection_hall_changed',
    '04-D01i':'maintenance_workshop','04-D01f':'dining_room','04-D01k':'maintenance_workshop',
    '04-D01j':'garden_rest_area','04-D01n':'park_garden','04-D01c':'inspection_hall_changed',
    '04-D01g':'dining_room','04-D01h':'maintenance_workshop','04-D01m':'maintenance_workshop',
    '04-D01l':'park_garden','04-D01o':'maintenance_workshop','04-F02':'garden_rest_area',
    '04-F03':'hotel_rest_lounge','04-F04':'garden_rest_area','04-F05':'hotel_rest_lounge',
    '04-F06':'maintenance_workshop',
})
FIRST_JOINS.update({'04-D00a':'### 공통 — 웃는 것을 본 사람','04-D00g':'### 이긴 사람 앞의 자리',
    '04-D01m':'### 두 길에 다시 발을 놓는다','04-D01l':'### 공통','04-F05':'### 합류'})
FIRST_COMPACT.update({
    '04-D00m':[
        ('거둔다.','미오','네가 방금 부탁했다고 한 말은 내가 더 붙였어. 지금 네가 물은 건 거기서 뭐라고 생각했냐는 거였어.',False),
        ('다시 적는다.','미오','둘을 나란히 세우지 않고 하루카가 쇼에게 물었다고 적었다. 내 이야기를 그 질문 안에 넣지는 않았다.',True),
        ('기다린다.','쇼','봤던 곳은 분수 앞입니다. 그전에 함께 오셨다고 생각한 것은 그때의 추측이었습니다.',False)],
    '04-D00o':[
        ('판과 빛만 찍는다.','미오','하루카가 판과 빛만 찍었다. 쇼는 화면 밖에 있었다. 사진에 없다고 그때 이곳에 없었던 것은 아니었다.',True),
        ('미오와 하루카가 판 옆에 한 장 남긴다.','미오','하루카가 타이머를 켜고 내 옆에 섰다. 같이 찍힌 한 장은 나중에 면담을 기록하는 사진과 별개였다.',True),
        ('오늘은 찍지 않는다.','미오','오늘은 찍지 않았다. 얼굴을 카메라로 확인하지도 않았다. 내 손에 검은 칠이 묻은 것만 보았다.',True)],
    '04-D00s':[
        ('레이가 아직 서 있는 자리를 남겨 둔다.','레이','저는 여기에서 기다릴 수 있습니다. 찍으실 분을 먼저 고르십시오.',False),
        ('유우 옆에 앉는다.','미오','나나가 다른 쪽을 골라도 유우는 옆에 남으라고 하지 않았다. 다음에 만나면 먼저 앉고 싶은지 다시 묻겠다고 했다.',True),
        ('사츠키가 먼저 나갈 자리를 비운다.','사츠키','너 때문에 간다고 쓰려는 건 아니야.',False)],
    '04-D01n':[
        ('난간 끝에 서서 화면에 없는 사람도 기다린다.','하루카','기다릴 사람을 모르게 찍으면 나중에 아무도 없었다고 생각하겠네.',False),
        ('하루카가 다시 셔터를 누를 동안 얼굴을 돌린다.','레이','같이 보지 않는 쪽이 좋으실 수도 있다고 생각했습니다.',False),
        ('지금 찍으려던 곳이 아닌, 누가 자기 쪽을 보고 있는지 먼저 묻는다.','미오','코토가 자기 발로 선 곳과 보려던 것을 말했다. 내가 대신 답하지 않고 끝까지 들었다.',True)],
    '04-D01o':[
        ('원래 시험 기간과 바뀐 날짜를 같이 읽는다.','미오','하루카가 두 숫자를 한 장에 찍었다. 일정이 바뀐 줄의 사본이었다. 최종 점검본이나 사고 보고 원문을 얻은 것은 아니었다.',True),
        ('누구 서명인지 레이에게 먼저 묻는다.','미오','후원의 결정과 다른 사람이 확인한 줄이 따로 있었다. 익숙한 이름을 보고 결정한 순간까지 보았다고 할 수는 없었다.',True),
        ('지금 누가 사본을 보관할지 정한다.','미오','하루카가 본 부분을 다시 읽고 싶다고 했다. 레이는 자기 이름이 있는 쪽을 달라고 요구하지 않았다.',True)],
})


def second_large_meeting(graph,scene,tail):
    body=scene.body
    def choice(key,question,starts,join,target):
        options=[]
        for flag,at,stop in zip('ABC',starts,[*starts[1:],join],strict=True):
            to=graph.lines(scene,at+1,stop,target)
            label=body[at].removeprefix('### ')
            label=re.sub(r'^[ABC][123]?\. ','',label)
            options.append({'id':flag,'label':label,'to':to,'set':{key:flag}})
        return graph.add('rev:'+key+':choice',type='menu',q=question,options=options,
            source=scene.source(scene.line+starts[0]+1))
    if scene.id=='02-F04':
        last=body.index('### SORA-02A A/C'); other=body.index('### SORA-02A B')
        a=graph.lines(scene,last+1,other,tail);b=graph.lines(scene,other+1,len(body),tail)
        tail=graph.add('rev:02-F04:distance-memory',type='branch',cases=[
            {'flag':'02-F04','equals':flag,'to':a} for flag in 'AC']+[
            {'flag':'02-F04','equals':'B','to':b}],default=tail)
        end=body.index('### 끝 — 사진의 다음 장')
        tail=graph.lines(scene,end+1,last,tail)
        second=body.index('### 선택 SORA-02B — 다음 판의 자리')
        starts=[i for i,r in enumerate(body) if BRANCH.fullmatch(r)]
        assert len(starts)==6
        tail=choice('02-F04:next','다음 판에는 어디에 있을까?',starts[3:],end,tail)
        common=body.index('### 구경꾼이 왔을 때')
        tail=graph.lines(scene,common+1,second,tail)
        tail=choice(scene.id,'첫 세 번의 규칙을 어떻게 정할까?',starts[:3],common,tail)
        return graph.lines(scene,0,body.index('### 선택 SORA-02A — 첫 세 번'),tail)
    end=body.index('### 마지막에 자리를 떠날 때')
    tail=graph.lines(scene,end+1,len(body),tail)
    second=body.index('### 선택 F-AI02-B — 남은 시간의 약속')
    starts=[body.index(title) for title in ('### B1. 같이 주방으로 가자고 한다',
        '### B2. 여기서 하던 일을 끝낸다','### B3. 미오가 먼저 다른 곳으로 간다')]
    b2=starts[1]; puzzle=body.index('#### F-AI02-A1/A3:퍼즐 진행 경로')
    book=body.index('#### F-AI02-A2:공동 사진집 경로')
    puzzle_path=graph.lines(scene,puzzle+1,book,tail)
    book_path=graph.lines(scene,book+1,starts[2],tail)
    b2path=graph.add('rev:02-F05:activity-memory',type='branch',cases=[
        {'flag':scene.id,'equals':flag,'to':puzzle_path} for flag in 'AC']+[
        {'flag':scene.id,'equals':'B','to':book_path}],default=tail)
    b2path=graph.lines(scene,b2+1,puzzle,b2path)
    options=[]
    for flag,at,stop in zip('ABC',starts,[b2,starts[2],end],strict=True):
        to=b2path if flag=='B' else graph.lines(scene,at+1,stop,tail)
        options.append({'id':flag,'label':re.sub(r'^### B[123]\. ','',body[at]),'to':to,
            'set':{'02-F05:next':flag}})
    tail=graph.add('rev:02-F05:next:choice',type='menu',q='남은 시간은 어떻게 보낼까?',options=options,
        source=scene.source(scene.line+second+1))
    common=body.index('### 기억하는 그림과 있는 물건')
    tail=graph.lines(scene,common+1,second,tail)
    first=body.index('### 선택 F-AI02-A — 어느 쪽을 보고 있을까')
    starts=[body.index(title) for title in ('### A1. 퍼즐을 하며 다른 이야기를 한다',
        '### A2. 퍼즐 대신 사진집을 같이 본다','### A3. 각자 말없이 한다')]
    tail=choice(scene.id,'지금은 어느 쪽을 보고 있을까?',starts,common,tail)
    return graph.lines(scene,0,first,tail)


def fourth_large_meeting(graph,scene,tail):
    body=scene.body
    def choose(key,title,starts,join,target):
        options=[]
        for flag,at,stop in zip('ABC',starts,[*starts[1:],join],strict=True):
            label=re.sub(r'^(?:### |\*\*)[AB][123]\. ','',body[at]).strip('*「」')
            to=graph.lines(scene,at+1,stop,target)
            options.append({'id':flag,'label':label,'to':to,'set':{key:flag}})
        return graph.add('rev:'+key+':choice',type='menu',q=title,options=options,
            source=scene.source(scene.line+starts[0]+1))
    if scene.id=='04-F03':
        tail=graph.lines(scene,344,len(body),tail)
        tail=choose(scene.id+':next','머리를 다듬고 난 뒤, 무슨 말을 할까?',[299,313,325],343,tail)
        tail=graph.lines(scene,204,297,tail)
        tail=choose(scene.id,'거울 앞에서 어떻게 대답할까?',[45,113,155],203,tail)
        return graph.lines(scene,0,43,tail)
    seen=graph.lines(scene,334,347,tail)
    tail=graph.add('rev:04-F04:draft-memory',type='branch',cases=[
        {'flag':'04-F04:next','equals':flag,'to':seen} for flag in 'AB'],default=tail)
    tail=choose(scene.id+':next','이 그림으로 무엇을 할까?',[269,291,313],331,tail)
    tail=graph.lines(scene,198,267,tail)
    tail=choose(scene.id,'고쳐 달라는 부탁에 어떻게 답할까?',[135,159,177],197,tail)
    tail=graph.lines(scene,48,133,tail)
    a=graph.lines(scene,30,37,tail);b=graph.lines(scene,38,47,tail)
    tail=graph.add('rev:04-F04:previous-garden',type='branch',cases=[
        {'flag':'04-F02','equals':'A','to':a},{'flag':'04-F02','equals':'B','to':b}],default=tail)
    return graph.lines(scene,0,27,tail)


def first_scene(graph, scene, tail):
    tail = graph.finish_free_time(scene,tail)
    body = scene.body
    starts = [(i, BRANCH.fullmatch(row)) for i,row in enumerate(body) if BRANCH.fullmatch(row)]
    if scene.id in ('04-F03','04-F04'):
        tail=fourth_large_meeting(graph,scene,tail)
    elif scene.id=='04-D00l':
        options=[]
        for flag,label,text in [
            ('A','사츠키 옆에 남아 문을 본다','사츠키는 문을 잠그지 않았다. 안쪽을 비운 뒤에도 내가 본 범위가 그 문 앞까지였다는 것만 남았다.'),
            ('B','사람들을 따라 로비로 간다','코토는 다른 사람을 새 당번표에 넣기 전에 실제 자리를 물었다. 내가 같이 간 것이 그 앞문을 계속 지켰다는 뜻은 아니었다.')]:
            to=graph.add('rev:04-D00l:response:'+flag,type='say',actor='mio',speaker='미오',mono=True,
                text=text,source=scene.source(scene.line+106),next=tail)
            options.append({'id':flag,'label':label,'to':to,'set':{scene.id:flag}})
        tail=graph.add('rev:04-D00l:choice',type='menu',q='지금은 어디에 있을까?',options=options,
            source=scene.source(scene.line+106))
        tail=graph.lines(scene,0,105,tail)
    elif scene.id=='03-D01b':
        tail=graph.lines(scene,287,len(body),tail)
        starts=[body.index('### '+flag+' 경로') for flag in 'ABC']
        cases=[{'flag':scene.id,'equals':flag,'to':graph.lines(scene,at+1,stop,tail)} for flag,at,stop in
            zip('ABC',starts,[starts[1],starts[2],286],strict=True)]
        tail=graph.add('rev:03-D01b:audience-memory',type='branch',cases=cases,default=tail)
        tail=graph.lines(scene,249,starts[0],tail)
        starts=[i for i,r in enumerate(body) if BRANCH.fullmatch(r)]
        assert len(starts)==3
        tail=graph.menu(scene,'누가 가게 앞에 설까?',[(BRANCH.fullmatch(body[at])[2],at+1,stop,'')
            for at,stop in zip(starts,[*starts[1:],248],strict=True)],tail)
        tail=graph.lines(scene,0,84,tail)
    elif scene.id=='03-D01c':
        starts=[body.index('### '+flag+' 경로') for flag in 'ABC']
        cases=[{'flag':'03-D01b','equals':flag,'to':graph.lines(scene,at+1,stop,tail)} for flag,at,stop in
            zip('ABC',starts,[*starts[1:],len(body)],strict=True)]
        tail=graph.add('rev:03-D01c:shop-memory',type='branch',cases=cases,default=tail)
    elif scene.id in ('02-F04','02-F05'):
        tail=second_large_meeting(graph,scene,tail)
    elif scene.id=='02-D02c':
        tail=graph.lines(scene,78,len(body),tail)
        a=graph.lines(scene,70,73,tail);b=graph.lines(scene,74,77,tail)
        tail=graph.add('rev:02-D02c:breakfast-memory',type='branch',cases=[
            {'flag':'02-D02b','equals':'A','to':a},{'flag':'02-D02b','equals':'B','to':b}],default=tail)
        tail=graph.lines(scene,60,69,tail)
        a=graph.lines(scene,4,33,tail);b=graph.lines(scene,34,59,tail)
        tail=graph.add('rev:02-D02c:opening-memory',type='branch',cases=[
            {'flag':'02-D02b','equals':'A','to':a},{'flag':'02-D02b','equals':'B','to':b}],default=tail)
    elif scene.id in ('02-D05a','02-F08','03-F05','03-F06','04-F06'):
        starts=([body.index(x) for x in ('#### 객석 사진을 먼저 찍는다','#### 반환대에 카메라를 놓는다',
            '#### 막 뒤에서 나오는 사람들을 기다린다')] if scene.id=='02-D05a' else
            [body.index(x) for x in ('### 객석에 남아 끝을 기다린다','### 통로에 서서 기사 역을 맡는다','### 다음 약속으로 먼저 나간다')]
            if scene.id=='02-F08' else [i for i,r in enumerate(body) if r.startswith('### ')][:3])
        join=(body.index('#### 무대가 다시 보일 때') if scene.id=='02-D05a' else
            body.index('### 둘이 떨어지는 곳') if scene.id=='03-F06' else
            body.index('### 바깥에서 다시 부를 때') if scene.id=='04-F06' else len(body))
        tail=graph.lines(scene,join+1,len(body),tail)
        tail=graph.menu(scene,scene.title,[(body[at].lstrip('# '),at+1,stop,'')
            for at,stop in zip(starts,[*starts[1:],join],strict=True)],tail)
        tail=graph.lines(scene,0,starts[0],tail)
    elif scene.id in ('02-D01','02-D02g','02-D04w','03-D01w','03-D01x','04-D00q','04-D01k'):
        offsets=[i for i,r in enumerate(body) if r.startswith('- **')]
        prefix={'02-D01':'공통. 린은','02-D02g':'어느 경로든 아이가','02-D04w':'합류 뒤 소라는',
            '03-D01w':'(세 경로가 합쳐지면','03-D01x':'### 합류',
            '04-D00q':'합류할 때 코토는','04-D01k':'### 종이로 볼 수 있는 데까지'}[scene.id]
        join=next(i for i,r in enumerate(body) if r.startswith(prefix))
        tail=graph.lines(scene,join+1,len(body),tail)
        tail=graph.menu(scene,scene.title,[(body[at].split('**')[1],at+1,stop,'')
            for at,stop in zip(offsets,[*offsets[1:],join],strict=True)],tail)
        tail=graph.lines(scene,0,offsets[0],tail)
    elif scene.id=='01-D03k':
        offsets = [body.index(title) for title in ('### 미오가 썼으면','### 카에데가 썼으면','### 리쿠가 썼으면')]
        cases = []
        for flag,start,stop in zip('ABC',offsets,[*offsets[1:],len(body)],strict=True):
            cases.append({'flag':'01-D01j','equals':flag,'to':graph.lines(scene,start+1,stop,tail)})
        tail=graph.add('rev:'+scene.id+':cushion-memory',type='branch',cases=cases,default=tail,
            source=scene.source(scene.line))
    elif starts:
        assert [match[1] for _,match in starts] in (list('AB'),list('ABC')),scene.id
        join=body.index(FIRST_JOINS[scene.id]) if scene.id in FIRST_JOINS else len(body)
        tail=graph.lines(scene,join+1,len(body),tail)
        alternatives=[(match[2].rstrip('*'),at+1,stop,'') for (at,match),stop in
            zip(starts,[*[i for i,_ in starts[1:]],join],strict=True)]
        tail=graph.menu(scene,scene.title,alternatives,tail)
        tail=graph.lines(scene,0,starts[0][0],tail)
    elif scene.id in FIRST_COMPACT:
        offsets=[i for i,row in enumerate(body) if row.startswith('- **')]
        responses=FIRST_COMPACT[scene.id]
        assert len(offsets)==len(responses),scene.id
        join=next((i for i in range(offsets[-1]+1,len(body)) if body[i].startswith('### ') or
            re.match(r'^\s*\*\*[^*]+\*\*　',body[i])),len(body))
        tail=graph.lines(scene,join,len(body),tail)
        choices=[]
        for index,(at,(label,speaker,text,mono)) in enumerate(zip(offsets,responses,strict=True)):
            assert label in body[at],(scene.id,label)
            flag=chr(65+index)
            answer=graph.add(f'rev:{scene.id}:response:{flag}',type='say',actor=SPEAKERS[speaker],
                speaker=speaker,text=text,mono=mono,source=scene.source(scene.line+at+1),next=tail)
            choices.append({'id':flag,'label':label,'set':{scene.id:flag},'to':answer})
        tail=graph.add('rev:'+scene.id+':choice',type='menu',q=scene.title,options=choices,
            source=scene.source(scene.line+offsets[0]+1))
        tail=graph.lines(scene,0,offsets[0],tail)
    elif scene.id=='01-D03l':
        offsets=[i for i,row in enumerate(body) if row.startswith('- **')]
        assert len(offsets)==2
        join=next(i for i,row in enumerate(body) if row.startswith('둘 다 종이는'))
        tail=graph.lines(scene,join+1,len(body),tail)
        tail=graph.menu(scene,'복도에서 어디에 남을까?',[(body[at].split('**')[1],at+1,stop,'')
            for at,stop in zip(offsets,[offsets[1],join],strict=True)],tail)
        tail=graph.lines(scene,0,offsets[0],tail)
    else:
        tail=graph.lines(scene,0,len(body),tail)
    if scene.id=='01-D02':
        cases=[]
        for flag,text in [
            ('A','숫자는 바닥 내려가서 세는 거야. 아직 들지도 않았잖아.'),
            ('B','오늘도 네가 몇 개 했는지 먼저 세지는 마.'),
            ('C','계단에 내가 계속 있기로 한 거 아니야. 지금 짐을 들어야 하니까 여기 있어.')]:
            to=graph.add('rev:01-D02:stair-memory:'+flag,type='say',actor='taiga',speaker='타이가',
                text=text,source=scene.source(scene.line+4),next=tail)
            cases.append({'flag':'01-F07','equals':flag,'to':to})
        tail=graph.add('rev:01-D02:stair-memory',type='branch',cases=cases,default=tail)
    callbacks={
        '02-D03d':[('02-F07',1,['아카리']*3)],
        '02-D05':[('02-D04l',1,['아이','유우']),('02-F02',3,['아이']*2)],
    }
    for flag,at,speakers in reversed(callbacks.get(scene.id,[])):
        quotes=re.findall(r'“([^”]+)”',body[at]);assert len(quotes)==len(speakers),(scene.id,at)
        cases=[]
        for key,speaker,text in zip('ABC',speakers,quotes):
            to=graph.add(f'rev:{scene.id}:memory:{flag}:{key}',type='say',actor=SPEAKERS[speaker],
                speaker=speaker,text=text,source=scene.source(scene.line+at+1),next=tail)
            cases.append({'flag':flag,'equals':key,'to':to})
        tail=graph.add(f'rev:{scene.id}:memory:{flag}',type='branch',cases=cases,default=tail)
    for ident,previous,speaker in [('04-D00c','04-F04:next','레이'),('04-D01c','04-D00m','하루카')]:
        if scene.id==ident:
            text=re.findall(r'“([^”]+)”',body[1])[0]
            recall=graph.add(f'rev:{ident}:meeting-memory:A',type='say',actor=SPEAKERS[speaker],speaker=speaker,
                text=text,source=scene.source(scene.line+2),next=tail)
            tail=graph.add(f'rev:{ident}:meeting-memory',type='branch',cases=[
                {'flag':previous,'equals':'A','to':recall}],default=tail)
    music=('bgm_freetime' if '-F' in scene.id else 'bgm_night' if scene.id in
        ('01-D01f','01-D02e','01-D02c','01-D02j','01-D03e','01-D03a','01-D03b','01-D03h','01-D03l') else 'bgm_daily_pro')
    if scene.id.startswith('02-D'):
        music='bgm_night' if scene.id in ('02-D02h','02-D02b') else 'bgm_daily_summer'
    return graph.add('rev:'+scene.id+':life-entry',type='stage',scene={'space':FIRST_SPACES[scene.id]},
        source=scene.source(scene.line),next=tail,
        presentation={'music':{'operation':'play','cue':music}})


FIRST_MEETINGS = {
    '01-D01d': [('01-F02','소라와 창문 끈을 살펴본다','')],
    '01-D01i': [('01-F04','분수에서 돌아오는 타이가에게 말을 건다',''),
                 ('01-F07','낮은 계단의 타이가를 찾아간다','')],
    '01-D02g': [('01-F03','점심 전 조리대의 아이에게 말을 건다',''),
                 ('01-F05','휴게실의 나나를 찾아간다','')],
    '01-D02m': [('01-F06','공방 앞의 린에게 말을 건다','')],
    '01-D02o': [('01-F08','카에데의 연습 받침을 보러 간다','01-F01')],
}


SECOND_MEETINGS = {
    '02-D02g':[('02-F09','호텔 뒤뜰에서 사츠키를 만난다','')],
    '02-D03b':[('02-F10','라운지의 코토에게 말을 건다','')],
    '02-D03e':[('02-F08','빈 객석에서 켄을 만난다','')],
    '02-D04r':[('02-F04','부스의 소라를 다시 찾아간다','01-F02')],
    '02-D04a':[('02-F03','기념품점 탁자의 리쿠를 만난다','')],
    '02-D04b':[('02-F05','휴게실에서 아이와 다시 만난다','02-F02')],
    '02-D04w':[('02-F06','공연 전에 공방의 린을 만난다','')],
}


THIRD_MEETINGS = {
    '03-D01d':[('03-F01','공연장 바깥에서 유우를 만난다','')],
    '03-D01r':[('03-F04','의상실 바깥의 소라에게 말을 건다','')],
    '03-D01n':[('03-F05','아케이드 벤치의 리쿠를 다시 만난다','02-F03')],
    '03-D01y':[('03-F06','열린 매점 바깥에서 리쿠와 다시 이야기한다','03-F05')],
}


FOURTH_MEETINGS = {
    '04-D00':[('04-F03','휴게실에서 하루카를 다시 만난다','03-F03')],
    '04-D00g':[('04-F02','실내 정원 벤치의 레이를 만난다','')],
    '04-D00j':[('04-F04','정원에서 레이의 그림을 함께 본다','04-F02')],
    '04-D01e':[('04-F05','면담 전에 나나를 찾아간다','')],
    '04-D01k':[('04-F06','빈 작업대의 사츠키에게 말을 건다','02-F09')],
}


MEETINGS = {**FIRST_MEETINGS, **SECOND_MEETINGS, **THIRD_MEETINGS, **FOURTH_MEETINGS}
MEETING_GROUPS = {
    '02-D01': ('rev:02:free-after-breakfast', '반납 확인 전에 어디로 갈까?', '다음 장소로 간다',
                [('02-F02','식사 준비대에서 아이를 만난다'),('02-F07','라운지의 아카리에게 말을 건다')]),
    '03-D01c': ('rev:03:free-before-screening', '상영 전에 누구에게 말을 걸까?', '상영장으로 간다',
                [('03-F02','낮은 무대 의자의 켄을 만난다'),('03-F03','카메라 타이머를 보던 하루카를 찾아간다')]),
}


def life_route(graph, scenes, ids, tail):
    for ident in reversed(ids):
        if ident in MEETING_GROUPS:
            menu, question, skip, people = MEETING_GROUPS[ident]
            options = [{'id': free, 'label': label, 'to': first_scene(graph, scenes[free], tail)}
                       for free, label in people]
            tail = graph.add(menu, type='menu', q=question,
                             options=options + [{'id': 'skip', 'label': skip, 'to': tail}])
        for free, label, prior in reversed(MEETINGS.get(ident, [])):
            following = tail
            talk = first_scene(graph, scenes[free], tail)
            skip = '지금은 다음 장소로 간다' if ident.startswith('01-') else '다음 장소로 간다'
            tail = graph.add('rev:' + free + ':visit', type='menu', q='자유행동', options=[
                {'id': 'meet', 'label': label, 'to': talk}, {'id': 'skip', 'label': skip, 'to': following}])
            if prior:
                flags = 'AB' if ident.startswith('01-') else 'ABC'
                tail = graph.add('rev:' + free + ':available', type='branch', cases=[
                    {'flag': prior, 'equals': flag, 'to': tail} for flag in flags], default=following)
        tail = first_scene(graph, scenes[ident], tail)
    return tail
