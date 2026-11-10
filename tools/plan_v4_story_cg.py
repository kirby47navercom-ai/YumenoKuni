"""Explicit original-story CG briefs tied to authored manuscripts, never old case art."""
from pathlib import Path
import json,re,hashlib
from generate_tpose_nai import CHARACTERS
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/design/rewrite_v4';jobs=[]

def appearance(slug):
    desc=CHARACTERS[slug]
    desc=re.sub(r'\bsolo,?\s*','',desc)
    desc=re.sub(r'[^,]*(?:smile|grin|smirk|upright posture|notebook strapped|main heroine)[^,]*,?','',desc,flags=re.I)
    if slug=='mio':desc=desc.replace('violet eyes','warm amber eyes')
    if slug=='haruka':desc=desc.replace('lavender eyes','brown eyes')
    return desc.strip(' ,')

def add(identifier,source,scene,actors=(),negative=''):
    matches=list(D.glob(source+'*.md'));assert len(matches)==1,(source,matches)
    p=matches[0];text=p.read_text(encoding='utf8')
    captions=[]
    for i,(slug,action) in enumerate(actors):
        captions.append({'x':(i+.5)/len(actors),'description':appearance(slug)+', '+action})
    jobs.append({'id':identifier,'output':f'art/cg_v4/full/{identifier}.png','seed':1801000+len(jobs),'source':p.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scene':scene,'characters':captions,'negative':negative,'status':'brief only; generation/individual acceptance separate'})

add('p05_announcement','10_프롤로그_',
 '1 mascot, solo, deserted amusement park plaza announcement, a small pink stitched rabbit mascot stands in front of a dark dry fountain. Another flat monitor far behind displays only an indistinct duplicate pink silhouette, no text. Eye-level low angle, bright cheerful stage lighting against an unwelcoming empty park, sinister contradiction without gore. No human spectators in frame. Do not show a living real rabbit.',
 [('lappy','stitched plush rabbit mascot, one ear red stitches, unnervingly polite fixed expression, standing still')])
add('c1_tools_distance','11a_1장_',
 '2 people in a hotel service work area, a tall boy has stopped the shorter girl at a doorway while she holds an ordinary small tool pouch at her OWN hip. Uneasy space remains between them, nobody grabs or strikes anyone. The boy looks accusatory and protective, the girl openly annoyed. Not a heroic rescue. Chest-up composition, no invented injury or clue, ordinary tool shelf in background.',
 [('taiga','stern closed mouth, broad shoulders, confronting the girl to his right, hands lowered'),('rin','irritated face, looking up toward the boy, hand on own tool pouch')])
add('c1_room_exchange','11a2_1장_',
 '2 people in a quiet hotel corridor during room exchanges. A tall boy pauses with one ordinary folded carrying cloth in left hand, his RIGHT wrist wearing a newly fitted plain support brace. A lavender-haired girl watches his wrist with guarded concern. No medical miracle, no bloody injury, no touching faces. Both standing, natural unequal heights, side three-quarter crop, no name labels on doors.',
 [('taiga','closed mouth, uneasy rather than grinning, newly fitted support on RIGHT wrist, left hand lowered'),('nana','concerned closed mouth, white ribbon ONLY on her LEFT wrist, arms near own body')])
add('c1_contact_disagreement','11a3_1장_',
 '2 people by a service-office table with a short pile of blank application sheets. A tall navy-haired girl refuses to surrender the paper she already holds; a red-haired student organizer keeps her own notebook lowered. Both visibly distrustful, no handshake, no cheerful agreement, no legible writing. Medium close shot with deliberately empty space between them.',
 [('kaede','cool narrowed eyes, holds one plain folded paper close to herself, speaking firmly'),('koto','controlled tense expression, clipboard held against own torso, listening without smiling')])
add('c1_trial_pressure','11c2_1장_',
 '2 people in an original circular 3D-style trial chamber, opposing positions across the ring. Foreground protagonist at her independent podium points her spoken objection toward a much taller boy at a separate distant podium. The accused boy looks shaken and defensive. Waist-up side perspective, other seats remain outside the crop, no crowd or supernatural effects. Deep violet environment, strong directional cel shadows, no words or logos, never draw podium as part of their bodies.',
 [('mio','angry focused eyes, speaking toward the boy, one hand raised in objection'),('taiga','cornered defensive expression, jaw tight, both hands on own independent podium')])
add('c1_next_morning','11d_1장_',
 '1girl, solo, morning hotel dining room, a guarded protagonist stands beside an empty chair rather than sitting down. Her small closed pink notebook remains at her own side. The table has ordinary unmarked cups but no feast. Quiet unease after the first trial, no ghosts, no smiling departed people, no funeral portraits, no magical glow.',
 [('mio','exhausted guarded eyes looking at the empty chair, closed mouth, standing still')])
add('c2_kitchen_boundary','12a_2장_',
 '2 people at the doorway of a communal kitchen. A petite cook remains on the kitchen side with a plain ingredient tray held close to her waist; a boy stays outside the threshold, frustrated and trying to speak. Neither blocks the other with physical force. Everyday disagreement about sharing food, not a romantic meal. Clean counters and separate doorframe, no knives in hands, no text.',
 [('ai','guarded stubborn expression, holding plain food tray at own waist'),('yuu','hurt frustrated eyes, empty hands visible, speaking without a grin')])
add('c2_first_performance','12a3_2장_',
 '1boy, solo, small theme-park stage during an actual modest live performance. Boy faces an audience OUTSIDE THE FRAME, sings into a separate microphone on its independent stand, shoulders tense under attempted cheerfulness. Stage speakers remain separate in background. No magical concert effects, no mass cheering, no lyric text, no weapon, not an idol poster.',
 [('yuu','performing with strained friendly expression, mouth open singing, hand near microphone but not gripping base')])
add('c2_props_normal','12a6_2장_',
 'Object insert in theatre preparation room, original large rectangular BLUE wheeled equipment chest, lid fully OPEN on two side lid stays, two distinct external silver latches on front, no internal lock. Inside the otherwise empty chest lie ordinary metal stage weights and a separate heavy microphone base. No body, no human hand, no blood or injury, no skull, no text, no labels. Careful three-quarter overhead view, show interior capacity and real wheels.',negative='person, face, body, corpse, flower, toy chest')
add('c2_trial_voice','12c2_2장_',
 '2 people during a serious trial, protagonist and teenage boy at separate independent podiums in a circular chamber, facing each other. Boy is no longer projecting a cheerful performance, holds his jaw rigid and tries to answer. Protagonist listens with tense suspicion, not triumphant smile. No ghosts or audience, no magical notes, no text. Cinematic side angle and hard cel shadows.',
 [('mio','attentive guarded closed mouth, watching boy on right'),('yuu','strained wounded expression, speaking defensively, no smile')])
add('c2_unshared_table','12d_2장_',
 '1girl, solo, hotel dining room after a trial, lavender-haired girl sits apart at the far edge of an ordinary shared table. She holds her own sleeve near her LEFT wrist ribbon; hands stay empty. Many empty chairs visibly separate her from the edge of frame. A plain cup sits untouched, no elaborate meal. No peaceful smile, tears only restrained, no ghost, no corpse.',
 [('nana','emotionally withdrawn guarded expression, seated alone, eyes lowered toward own wrist')])
add('c3_mirror_demonstration','13a2_3장_',
 '2 people in a mirror-maze work alcove. A silver-haired boy watches his own ordinary reflection at an oblique angle while an orange-haired magician observes from the side with controlled skepticism. Reflection is physically aligned to the boy, not a second body or ghost. No swapping faces, no supernatural aura, no invented blood. Chest-up shot, angular mirror frame and one partition edge establish reflection versus direct view.',
 [('sora','uneasy polite closed mouth, looks into physical mirror at left'),('riku','skeptical narrowed eyes, hands empty and lowered, standing aside')])
add('c3_blindfold_test','13a6_3장_',
 '2 people during a controlled observation in a waiting room. Brown-haired boy sits in an ordinary chair wearing a plain black blindfold covering BOTH eyes; silver-haired boy stands off to his side, visibly tense. No restraints, no magic light, no physical attack, no weapon, no threatening surgical setting. Moderate distance between them, practical room with a clock but no legible time numbers.',
 [('ken','seated, eyes completely covered by simple black cloth blindfold, neutral mouth, hands resting on own thighs'),('sora','serious focused expression, standing beside chair without touching the seated boy')])
add('c3_information_custody','13a11_3장_',
 '2 girls in the mirror waiting-room doorway. Protagonist receives one completely CLOSED small plain envelope from a lavender-haired girl. Both see only the envelope exterior, no paper visible, no writing, no seal emblem. Their fingertips touch their OWN ends of envelope only. Quiet distrust and careful attention, no smile, no dramatic magic, no bloody objects.',
 [('mio','guarded eyes fixed on closed envelope, one hand receiving envelope'),('nana','grave closed-mouth expression, hands passing closed envelope without opening it')])
add('c3_trial_contradiction','13c2_3장_',
 '2 people at separate trial podiums. Protagonist speaks a deliberate challenge with an unsteady but resolved expression; a brown-haired boy reacts with sharp indignation and involuntary recognition. His body remains a single normal brown-haired boy, no ghost image, no second face, no silver-haired face overlaid, no possession aura. No paper text visible. Opposing close profiles with empty space between.',
 [('mio','strained resolute expression, speaking toward boy, no victory smile'),('ken','angry startled expression, answering impulsively, single normal human face')])
add('c3_after_two_absences','13d_3장_',
 '1girl, solo, hotel corridor after a trial, protagonist has stopped between two CLOSED unlabelled guestroom doors. Her body is small against the long corridor perspective; one hand keeps a closed pink notebook against her torso. Empty doors do not open, no spectral people, no silhouettes behind glass, no photographs of departed people. Severe quiet, cool morning light rather than a horror jump scare.',
 [('mio','exhausted closed mouth, lowered eyes, standing still rather than posing heroically')])
add('c4_historical_model','14a2_4장_',
 '2 girls beside a large OLD amusement-park architectural model under a partly opened glass display cover in a visitor exhibition room. Protagonist studies the miniature buildings without touching them; pink-haired girl studies a tiny blank-uniform mascot figure on the model, guarded rather than happily reminiscing. No readable map names, no arrows or current escape route, no invented photographs. Model is visibly miniature, not a real magical park.',
 [('mio','wary thoughtful expression, looking down at historical model'),('haruka','uneasy introspective closed mouth, looking at one small model figure')])
add('c4_workshop_alignment','14a8_4장_',
 '2 people at a maintenance workbench, a composed white-haired boy and a short green-haired girl compare an ordinary metal repair bracket to a simple unlabelled outline on paper. Both have genuine different opinions and focus, no friendly handshake, no magic creation effects, no measuring numbers on drawing. Bare metal part and ruler lie on desk, hands anatomically plausible and away from sharp edges.',
 [('rei','serious attentive expression, points at metal bracket without grabbing girl'),('rin','frowning critically, arms near own tool belt, looking at physical part')])
add('c4_own_senses','14a8_4장_',
 '1girl, solo, pink-haired student stands STILL beside a maintenance doorway, one hand near her own ear while concentrating on an actual distant sound. Eyes are closed and not tracking anything; no walking, no psychic visions, no floating text or magic target. Fully clothed cream uniform, ordinary dim workshop architecture behind her. She is deliberately choosing a sensory limitation, not sleeping or fainting.',
 [('haruka','focused concentrated expression, eyes gently closed, one hand near own ear, standing with both feet planted')])
add('c4_questioning_origin','14a7_4장_',
 '2 girls in a quiet hotel lounge. Pink-haired girl speaks directly with restrained anger and fear, facing the protagonist who cannot comfortably meet her gaze. The separation between their chairs matters. No hugs, no consolation smile, no touching hands, no disappearing limbs or ghost effects. Medium shot, closed pink notebook lies in protagonist own lap with no text.',
 [('haruka','hurt angry expression, speaking assertively, looking toward other girl'),('mio','conflicted guarded expression, looking slightly away while listening')])
add('c4_trial_late_alibi','14c3_4장_',
 '2 people at separate independent trial podiums, white-haired boy keeps an outwardly controlled face with visible tension while protagonist presses a question. Neither smiles. Side angle emphasizes a large physical gap, violet courtroom and ordinary lighting, no magical creation scene, no ghosts or hidden culprit symbols. Chest-up, no crowd.',
 [('mio','focused strained eyes, speaking without a triumphant grin'),('rei','controlled closed mouth, tense fingers resting on own podium, eyes avoiding direct gaze')])
add('c4_remaining_photograph','14d_4장_',
 '1girl, solo, protagonist sits at hotel desk holding one ordinary small photograph FACE DOWN so no content or people are shown. Her closed pink notebook remains beside her, fingers tense. Cool dawn light, no smiling reunion or apparition, no new object brought by the dead, no words on photo back. Focus is refusing to turn the photograph over, not a magic event.',
 [('mio','emotionally shut down expression, holds face-down blank-backed photo with both hands')])
add('c5_lines_not_answers','15a_5장_',
 '1girl, solo, red-haired student organizer has raised one sleeve just enough to show several very thin dark straight marks across the inner wrist. Marks are abstract, no letters, names, numbers, runes or glowing symbols; no open injury or blood. Her other hand holds the sleeve, tense face partly visible above. Quiet hotel lounge. Do not depict a weapon, self injury, bindings or cuffs.',
 [('koto','serious uneasy expression, exposing inner wrist deliberately, closed mouth')],negative='wound, blood, scar, self harm, glowing rune, chains')
add('c5_separate_promises','15a4_5장_',
 '2 girls at a small table in a hotel lounge, lavender-haired girl keeps a plain cup close to her own side while red-haired organizer has stopped reaching toward it. A few other ordinary cups stand apart, no poison, no visible powder or pills, no numbers or personal names. Both uneasy and aware of unequal choices, not a tea party. No physical contact, no supernatural effects.',
 [('nana','firm guarded expression, one hand around own plain cup'),('koto','controlled uneasy expression, empty hand withdrawn toward own notebook')])
add('c5_not_your_side','15a7_5장_',
 '2 girls in a record-room passage, a coral-haired tailor and a dark-haired reserved girl confront one another at arm length, both fully clothed in their established uniforms. Tailor looks defensive and hurt, other girl is serious and no longer automatically agreeable. No slap, no weapon, no hugging, no magical shadow hands. Shelves form a narrow ordinary background, no written clues.',
 [('akari','defensive tense expression, one hand near her own watch, no duplicated bracelets'),('satsuki','grave determined expression, empty hands lowered, looking directly at tailor')])
add('c5_trial_inconvenient_truth','15c2_5장_',
 '2 girls in a circular trial chamber at independent podiums, coral-haired girl answers with composed but exhausted defensiveness; protagonist listens without sympathy smile or victory. Bodies remain separate from podiums. No confession text, no poison bottle or new clue, no ghost, no exaggerated heart icons. Hard dark ink outlines and restrained saturated violet backdrop.',
 [('mio','wary narrowed eyes, listening with closed mouth'),('akari','strained controlled expression, speaking while fingers rest on own podium')])
add('c5_five_in_lobby','15d_5장_',
 'Five fully clothed surviving students in a hotel lobby after a trial, shown mostly FROM BEHIND at medium-long distance with faces outside frame. Their unequal spacing conveys mistrust, nobody touches or forms a team huddle. A black-haired girl holds her own small notebook, a green-haired girl stands by the exit, lavender-haired girl carries her own bag, reserved dark-haired girl stands apart, grey-clad medic remains near stairs. No other people, no silhouettes of absent friends, no celebration.',
 [('mio','back view, notebook in own hand'),('rin','back view, standing nearest exit'),('nana','back view, carries own bag'),('sho','back view, near stairs'),('satsuki','back view, stands separately')])
add('c6_descending_order','16a_6장_',
 'Five fully clothed students descend a narrow ordinary concrete service stairway, FROM BEHIND and above, no faces visible. Single-file order down stairs: dark-haired reserved girl first, grey-clad medic next, lavender-haired girl carrying own bag, black-bob protagonist, green-haired girl last checking doorway. Real handrails and overhead utility lights, no attack, no armed guards, no supernatural tunnel, no happy teamwork pose. Do not add people.',
 [('satsuki','back view, first down stairs'),('sho','back view, follows first girl'),('nana','back view, carries own bag'),('mio','back view, notebook close to body'),('rin','back view, last at doorway')])
add('c6_bench_remembered','16a_6장_',
 '2 girls in an old underground shelter reception room. Lavender-haired girl has stopped beside the SECOND ordinary bench location from the door and looks down; black-bob protagonist stands a pace away and watches her, angry at knowing less. No children, no flashback overlay, no ghosts, no reunited families. Folded camp beds sit against wall, no hospital emergency, no readable name labels.',
 [('nana','quiet grave expression, eyes on empty bench, arms near own bag'),('mio','guarded conflicted expression, standing a pace away')])
add('c6_current_and_old','16b1_6장_',
 '2 girls at a shelter reception terminal, green-haired girl works at the keyboard while black-bob protagonist waits with notebook open. The monitor shows two blank unlabelled panel areas only, NO names, times, answers or text; actual interface will be added separately by game. Both serious, not celebrating a discovery. Ordinary operating records, no magic all-knowing computer or futuristic hologram.',
 [('rin','critical concentrated expression, hand near ordinary keyboard'),('mio','tense patient expression, pen held still beside blank notebook')])
add('c6_final_question','16c3_6장_',
 '1girl, solo, protagonist at her independent trial podium in a mostly dark circular chamber. She is no longer addressing a visible person: gaze steady across the empty central floor, jaw tense, hands on her own blank notebook. No dead characters appear, no ghost, no heroic victory pose, no destroyed universe, no words or symbols. The composition emphasizes responsibility rather than triumphant revelation.',
 [('mio','grave resolved expression, looking across room, closed mouth')])
add('c6_outside_not_resolution','16d2_6장_',
 '1girl, solo, protagonist stands just beyond an industrial park service exit at grey dawn, side/back three-quarter angle. She holds a CLOSED pink notebook low at her own side and turns her head toward a person completely OUTSIDE the frame. No visible rescuers, police, family, crowds, vehicles or welcoming city. No happy smile, no crying embrace, no triumphant open arms. Bare ordinary pavement and unresolved overcast distance, open future rather than a celebratory escape ending.',
 [('mio','grave alert expression, slightly turned profile, closed notebook in lowered own hand')])

output=ROOT/'art/v4_production/full/story_cg_jobs.json';output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps({'scope':'original story event CG across prologue and chapters1-6; not entire CG acceptance','method':'V5 per-character captions; no unsupported reference/infill','jobs':jobs},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Authored',len(jobs),'event CG briefs with existing source hashes')
