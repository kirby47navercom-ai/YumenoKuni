# 1차 UI 에셋

기준 캔버스는 2560×1440(1280×720의 2배)이며 배치 좌표는 `layout.json`에 있다. 검정·흰색의 각진 프레임과 분홍 사선으로 구성했다. 대화창은 화면 하단, 기울어진 이름표는 오른쪽 위, 발언력·집중력은 화면 오른쪽 위, 실린더는 왼쪽 아래에 배치한다.

| 경로 | 본편 PNG 수 | 규격 |
|---|---:|---|
| `kotodama/frame_*.png` | 4 | 440×600, 증거 노랑·증언 파랑·규칙/마법 분홍·메모 회색 |
| `dialog/frame.png`, `dialog/nameplate.png` | 2 | 2240×340, 440×88 |
| `trial/heart_*.png` | 3 | 128×128, 가득 참·절반·비어 있음 |
| `trial/focus_track.png`, `trial/focus_fill.png` | 2 | 640×64 |
| `trial/bullet_cylinder.png` | 1 | 384×384, 5칸 |
| `trial/cutin_*.png` | 3 | 1536×512 |

발언력은 하트 5칸, 집중력은 100 막대이며 04 사양을 따른다. PNG는 sRGB / straight alpha로 가져온다. 집중력 채움은 `fill_rect`에 맞춰 왼쪽부터 자른다. 이름·대사·카드 내용·HUD 수치는 엔진에서 출력한다. 이름표 흰 영역은 화자 테마색을 적용할 수 있다. 카드 가운데 창은 실제 투명 영역이며 개별 카드 삽화·아이콘은 다음 범위다.

`preview.png`, `dialog/preview.png`, `trial/cutins_sheet.png`는 조립·가독성 검수용이며 본편 15장 수량에서 제외한다. 대화 예문에는 Windows 맑은 고딕을 사용했고 폰트 파일은 포함하지 않았다. 대화 안전 영역은 장식과 겹치지 않게 x=360부터 시작한다. 정적 PNG와 좌표 인계이며 엔진 애니메이션·실행 검증은 포함하지 않는다.

배치 참고는 [Nintendo 공식 게임 화면](https://www.nintendo.com/pt-br/store/products/danganronpa-v3-killing-harmony-anniversary-edition-switch/)과 [공개 리뷰의 대화 화면](https://www.3djuegos.com/juegos/danganronpa-v3-killing-harmony/analisis/rizando-el-rizo-171016-8118)이다. 납품 PNG는 모두 이미지 생성 도구로 새로 제작했다. 생성 프롬프트·원본 식별자·해시는 `art/PROVENANCE.json`에 기록한다.
