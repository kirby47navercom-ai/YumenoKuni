"""Verified labels: Korean patch -KrvYvqTaUA 17:02/17:05/17:08, 1:15:41/44.

Editable project-font lettering, not extracted original pixels.
"""
from pathlib import Path
import make_nonstop_intro_art as art

out=Path(__file__).resolve().parents[1]/'ui/v4/debate_feedback'
solved=art.lettering('해결',500,250,'#030308','#030308')
solved=solved.replace('<g fill=', '<g transform="rotate(-7 250 125)" fill=',1)
(out/'puzzle_solved.svg').write_text(solved,encoding='utf-8')
(out/'puzzle_complete.svg').write_text(art.lettering('COMPLETE',1200,300,'#37baff','#1379ec',True),encoding='utf-8')
art.FONT=art.ROOT/'fonts/gugi/Gugi-Regular.ttf'
(out/'mine_clear.svg').write_text(art.lettering('CLEAR!',1000,240,'none','#fff0a6',True).replace('stroke-width="1.5"','stroke-width="5"'),encoding='utf-8')
(out/'anagram_correct.svg').write_text(art.lettering('correct!',900,160,'none','#4deaff',True),encoding='utf-8')
