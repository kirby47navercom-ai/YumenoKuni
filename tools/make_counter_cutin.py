"""반론 쇼다운 마무리 컷인 글자 「반」「론」 — Claude 2026-11-05.
근거 : V3 LP 2장 재판 반론 쇼다운 #1(lparchive Update 60) — 진실의 칼날로 벤 뒤 「Counter」 붓글씨 컷인(논스톱 「논파」와 다른 글자).
논파 글자(result_refute_glyph0/1.svg)와 같은 독도 글꼴·같은 노란 테 겹으로 그린다. 출력 : Game/Assets/Art/ui/result_counter_glyph0/1.svg
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from make_nonstop_intro_art import lettering
OUT = pathlib.Path(__file__).resolve().parents[1] / 'Game/Assets/Art/ui'
for i, c in enumerate('반론'):
    s = lettering(c, 360, 360, '#030308', '#ffd32a', glow=True).replace('width="360" height="360" viewBox', 'width="720" height="720" viewBox', 1)
    (OUT / f'result_counter_glyph{i}.svg').write_text(s, encoding='utf-8')
print('ok')
