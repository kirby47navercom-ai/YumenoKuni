"""재판 왼쪽 위 화자 띠 — 반투명 띠 + 위아래 가는 선 + 이름 아래 순서 점(지금 줄만 주황). Claude 2026-11-05.
근거 : V3 LP 1장(Update 31)·2장(Update 60) 화면 확대 — 논스톱·반론 쇼다운 모두 왼쪽 위는 기운 검은 탭이 아니라
       반투명 어두운 띠 위아래 가는 선, 얇고 넓은 자간의 이름, 그 아래 점(지금 줄 주황). (사양서 19 §2 의 「기울어진 검은 탭」 서술은 틀림)
출력 : Game/Assets/Art/ui/hud_name_dots/n{N}_{I}.svg (N=1..14 증언 수, I=0..N-1 지금 줄). 노드 크기 360x84.
"""
import pathlib
OUT = pathlib.Path(__file__).resolve().parents[1] / 'Game/Assets/Art/ui/hud_name_dots'


def svg(n, cur):
    step = min(18, 240 / max(1, n)); d = ''
    for i in range(n):
        x = 40 + i * step
        d += (f'<circle cx="{x:.1f}" cy="62" r="5" fill="#ff9a1f"/>' if i == cur
              else f'<circle cx="{x:.1f}" cy="62" r="3.2" fill="#ffffff" fill-opacity=".85"/>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="360" height="84" viewBox="0 0 360 84" preserveAspectRatio="none">'
            '<title>V3 trial name band (LP Ch1/Ch2: translucent band, thin lines, name + order dots)</title>'
            '<defs><linearGradient id="b" x2="1"><stop stop-color="#0a0a12" stop-opacity=".62"/><stop offset=".75" stop-color="#0a0a12" stop-opacity=".35"/><stop offset="1" stop-color="#0a0a12" stop-opacity="0"/></linearGradient></defs>'
            '<rect x="0" y="8" width="360" height="66" fill="url(#b)"/><path d="M14 8H350" stroke="#e8e8f0" stroke-opacity=".55" stroke-width="1.5"/><path d="M0 74H300" stroke="#e8e8f0" stroke-opacity=".4" stroke-width="1.2"/>'
            + d + '</svg>')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    k = 0
    for n in range(1, 15):
        for i in range(n):
            (OUT / f'n{n}_{i}.svg').write_text(svg(n, i), encoding='utf-8'); k += 1
    print(k, 'files')


if __name__ == '__main__':
    main()
