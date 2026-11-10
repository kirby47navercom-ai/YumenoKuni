"""Five original six-panel reconstruction pages; atlas UVs remain explicit for UI authoring."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];folder=ROOT/'art/v4_production/full/builtin_jobs'
base=('ONE original game reconstruction-COMIC PAGE,16:9 full-bleed widescreen target1920x1080. EXACT THREE COLUMNS by TWO ROWS, six rectangular equal panels with thin straight black gutters. '
 'No speech balloons, lettering, numerals, captions or arrows. Each attachment is exact named character identity and fine angular ink/cel style reference, not a pose to paste. '
 'Preserve each exact eye/hair color, face, hair accessories and costume, draw distinct actions and expressions rather than six identical portraits. Clean varied ink, thin hair strands, hard cel shading, pale ivory/violet/walnut environment. '
 'Original fictional mystery reconstruction; non-graphic, fully clothed, no sexualization, no exposed injuries, no organs, dismemberment or red blood. No magic effects, ghosts, gore or invented evidence. '
 'Each panel is a different chronological moment, LEFT TO RIGHT TOP ROW then LEFT TO RIGHT BOTTOM ROW. Do not merge panels or add seventh panel. ')
items=[
(1,'03_1장_',['taiga','kaede'],[
'Normal service lounge: small printer, independent closed front door A, rear maintenance door with external reinforcement board; no letters or people.',
'Kaede alone prints ordinary blank-looking report sheets at small printer, navy hair/lightblue coat exact reference.',
'Taiga and Kaede confront each other across a report, both angry and afraid, hands away from neck, no physical attack or contact shown.',
'After unseen incident: loose crumpled blank report on floor beside ordinary chair; no person or violent act pictured.',
'Taiga alone has returned to an ordinary patrol corridor, glances back with guilty panic, RIGHT wrist brace visible; no heroic pose.',
'Close independent evidence: a small plain paper strip placed BESIDE the removed plain wrist brace, tiny geometric printed marks only, no readable numbers or text; no person.']),
(2,'05_2장_',['yuu','ai'],[
'Yuu alive at modest performance stage singing into a complete microphone on independent stand; no cheering crowd.',
'Separate ordinary playback device and speaker left active in EMPTY stage area, no person, no text or musical magic.',
'Yuu and Ai argue in backstage preparation room, each fully clothed and separate, no strike shown; a separate heavy microphone base lies untouched on shelf.',
'Object-only original BLUE wheeled equipment chest with two external latches OPEN and lid held by two stays; plain cloth and stage weights inside, no body pictured.',
'Same blue chest CLOSED in staff passage, real wheels and two external latches clearly present, no invented inside lock.',
'After discovery, same chest OPEN in hotel multiuse room, no body visible from this low angle: one lid stay and loose black plastic cord-loop fragment on edge; no invented weapon.']),
(3,'07_3장_',['sora','ken','riku'],[
'Sora blond/orange jacket and Ken burgundy/green suit stand separately before a normal mirror, visibly distinct physical bodies and outfits, no magic overlay.',
'Sora ORIGINAL blond body rests on waiting-room bench during controlled observation; Ken physical body remains standing elsewhere in same room, no blade or attack.',
'Mirror-workbay oblique reflection shows Ken PHYSICAL body approaching orange-haired magician Riku, partition blocks direct view; no physical attack shown.',
'Object-only scattered plain marker fragments in mirror-workbay alcove between wall and workbench, no body or violent contact.',
'Wide waiting-room layout, blond body on bench and burgundy-haired physical body at bench foot, both clearly distinct, no attack or blood shown.',
'Trial: only Ken PHYSICAL burgundy-haired body angrily reacts at his independent podium; no second face, no ghost, no blond overlay or identity labels.']),
(4,'09_4장_',['rei','haruka'],[
'Normal empty inspection hall with ONE real exit, narrow fixed equipment window and CLOSED metal floor hatch; no extra room yet.',
'Same physical hall contains an added cream partition room with one front door and second small blind-storage door; existing hatch still physically inside hall.',
'Rei white uniform and Haruka pinkbob/cream blazer talk tensely inside added room, separate bodies, no violence or water peril shown.',
'Object-only CLOSED metal floor hatch with outside fixing visible; no body, hand or violent contact.',
'Rei alone leaves real front door with ordinary blank papers while glanced backward, no secret rear exit or teleport.',
'After rescue: OPEN floor hatch, wet treatment cloth and separate camera bag on solid floor; no person, no new door or gore.']),
(5,'10_5장_',['akari','koto'],[
'Seven SEPARATE plain empty cups on ordinary lounge preparation surface, blank simple shapes without labels; no ingredient, drug or recipe.',
'Akari exact auburn hair/green uniform hands Koto exact longblonde hair/cream cardigan a plain cup; both serious, no vial or secret substance pictured.',
'Koto alive drinks from her OWN plain cup at table, previously bandaged elbow present, no new injury or happy tea party.',
'Mio not in frame: object-only TWO open paper sheets on same desk; one has faint geometric ruled marks in one region, counterpart region blank, no readable text or magical glow.',
'The used cup remains untouched on table beside pushed-back chair and fallen allocation paper; no person or violent scene.',
'Akari alone at independent trial podium, exhausted and defensive, watch ONLY on anatomical RIGHT wrist, no happy victory or extra band.'])]
refs={}
for j in json.loads((ROOT/'art/v4_production/full/builtin_jobs.json').read_text(encoding='utf8'))['jobs']:
 for slug,path in zip(j['characters'],j['references']):refs[slug]=path
jobs=[]
for ch,source,cast,panels in items:
 p=next((ROOT/'docs/design/rewrite_v4').glob(source+'*.md'))
 mapping=' '.join(f'Image{i+1} is {s}.' for i,s in enumerate(cast))
 prompt=base+mapping+' '.join(f'PANEL{i+1}: {s}' for i,s in enumerate(panels))
 j={'id':f'climax_c{ch}_page_builtin_r1','source':p.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'characters':cast,'references':[refs[s] for s in cast],'prompt':prompt,'kind':'climax_page','panel_grid':[3,2],'panel_uv_rectangles':[[c/3,r/2,(c+1)/3,(r+1)/2] for r in range(2) for c in range(3)],'panels':panels,'visual_status':'not generated','runtime_integrated':False}
 (folder/(j['id']+'.json')).write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf8');jobs.append(j)
(ROOT/'art/v4_production/full/climax_page_jobs.json').write_text(json.dumps({'tool':'built-in image_gen only','scope':'5 original illustrated reconstruction pages,30 panels; not game integration or final case-logic validation','jobs':jobs},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Prepared',len(jobs),'original six-panel page briefs')
