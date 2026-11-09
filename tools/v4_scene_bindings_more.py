"""Reviewed later-chapter scene entries and bounded, source-addressed CG shots.

No file writes, engine calls, source rewriting or implicit CG-to-whole-chapter
fallback. A reused mesh describes a visual set, not a newly proved location.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[1]
# Each row starts a reviewed run, ending immediately before the next row.
# This is an explicit reading table, not a keyword-to-room classifier.
RUNS={
 '12a':[('2-01','hotel_lobby'),('2-02','pool_edge'),('2-03','refreshment_store'),('2-05','park_garden'),('2-05b','hotel_lobby'),('2-06','kitchen'),('2-07','hotel_lobby'),('2-08','kitchen'),('2-08B','hotel_lobby'),('2-10','kitchen'),('2-11','dining_room'),('2-12','kitchen')],
 '12a2':[('2-13','kitchen'),('2-16','laundry_room'),('2-17','hotel_lobby'),('2-18','performance_stage'),('2-20','park_garden')],
 '12a3':[('2-21','dining_room'),('2-22','performance_stage'),('2-26B','hotel_corridor'),('2-27','kitchen'),('2-28','dining_room'),('2-30','hotel_corridor')],
 '12a4':[('2-31','kitchen'),('2-32','hotel_lobby'),('2-36','service_lounge'),('2-40','hotel_corridor'),('2-41','performance_stage'),('2-42','dining_room')],
 '12a5':[('2-43','service_lounge'),('2-44','kitchen'),('2-45','hotel_corridor'),('2-46','hotel_lobby'),('2-48','hotel_multiuse'),('2-49','hotel_lobby'),('2-50','guest_room')],
 '12a6':[('2-51','hotel_multiuse'),('2-52','theatre_preparation'),('2-53','performance_stage'),('2-56','cold_store'),('2-57','theatre_preparation'),('2-58','staff_passage'),('2-59','performance_stage')],
 '12a7':[('2-62','performance_stage'),('2-63','theatre_preparation'),('2-64','refreshment_store'),('2-65','hotel_corridor'),('2-67','hotel_lobby'),('2-69','hotel_multiuse')],
 '13a':[('3-01','hotel_lobby'),('3-06','mirror_maze')],
 '13a2':[('3-11','mirror_maze'),('3-19','park_garden'),('3-20','dream_lobby')],
 '13a3':[('3-21','dream_lobby'),('3-25','theatre_preparation'),('3-30','dream_lobby')],
 '13a4':[('3-33','dream_lobby'),('3-34','screening_room'),('3-39','dream_lobby'),('3-43','park_garden')],
 '13a5':[('3-44','hotel_lobby')],
 '13a6':[('3-54','hotel_lobby')],
 '13a7':[('3-65','hotel_lobby'),('3-72','dream_lobby'),('3-73','staff_passage'),('3-74','dream_lobby'),('3-75','hotel_lobby')],
 '13a8':[('3-76','mirror_maze'),('3-77','mirror_workbay'),('3-81','mirror_maze'),('3-83','dream_lobby'),('3-86','mirror_waiting'),('3-87','dining_room')],
 '13a9':[('3-88','hotel_lobby'),('3-95','hotel_corridor'),('3-96','hotel_lobby'),('3-98','guest_room')],
 '13a10':[('3-100','hotel_lobby')],
 '13a11':[('3-109','mirror_maze'),('3-110','mirror_workbay'),('3-111a','mirror_maze'),('3-112','mirror_waiting'),('3-116','hotel_lobby'),('3-118','mirror_waiting'),('3-119','mirror_workbay'),('3-120','mirror_waiting')],
 '13a12':[('3-121','mirror_waiting'),('3-125','mirror_maze'),('3-129','mirror_workbay'),('3-130','mirror_maze'),('3-131','mirror_workbay')],
 '14a':[('4-01','hotel_lobby'),('4-05','management_office'),('4-06','supply_store'),('4-08','staff_passage'),('4-09','staff_passage'),('4-10','reading_room'),('4-11','dining_room'),('4-12','reading_room')],
 '14a2':[('4-13','dining_room'),('4-15','exhibition_room')],
 '14a3':[('4-27','exhibition_room'),('4-35','staff_passage')],
 '14a4':[('4-41','staff_passage'),('4-45','hotel_lobby'),('4-49','dining_room'),('4-51','hotel_lobby'),('4-54','guest_room')],
 '14a5':[('4-57','guest_room'),('4-67','hotel_lobby'),('4-68','guest_room'),('4-70','hotel_lobby')],
 '14a6':[('4-71','hotel_lobby')],
 '14a7':[('4-83','dining_room'),('4-96','hotel_corridor')],
 '14a8':[('4-99','maintenance_workshop'),('4-102','inspection_hall_normal'),('4-109','staff_passage'),('4-110','service_lounge'),('4-111','hotel_lobby')],
 '14a9':[('4-115','hotel_lobby'),('4-120','loading_gate'),('4-126','hotel_lobby'),('4-127','dining_room')],
 '14a10':[('4-131','operating_archive'),('4-134','dining_room'),('4-143','hotel_corridor'),('4-145','dining_room'),('4-146','maintenance_workshop')],
 '14a11':[('4-147','maintenance_workshop'),('4-149','operating_archive'),('4-151','service_lounge'),('4-153','maintenance_workshop'),('4-160','dining_room'),('4-163','guest_room'),('4-164','hotel_lobby')],
 '14a12':[('4-165','hotel_lobby'),('4-166','inspection_hall_normal'),('4-167','inspection_hall_changed'),('4-173','dining_room'),('4-175','inspection_hall_changed')],
 '14a13':[('4-181','inspection_hall_changed')],
 '15a':[('5-01','dining_room')],
 '15a2':[('5-15','dining_room'),('5-18','loading_gate'),('5-22','operating_archive'),('5-29','dining_room')],
 '15a3':[('5-33','service_lounge'),('5-40','operating_archive'),('5-47','hotel_corridor')],
 '15a4':[('5-49','central_control'),('5-52','staff_passage'),('5-55','dining_room'),('5-64a','operating_archive'),('5-65','hotel_corridor'),('5-66','guest_room')],
 '15a5':[('5-69','dining_room'),('5-71','central_control'),('5-74','supply_store'),('5-77','operating_archive'),('5-82','dining_room'),('5-86','operating_archive')],
 '15a6':[('5-89','operating_archive'),('5-105','dining_room')],
 '15a7':[('5-109','hotel_corridor'),('5-122','operating_archive'),('5-125','hotel_lobby'),('5-126','kitchen')],
 '15a8':[('5-127','operating_archive'),('5-140','hotel_corridor'),('5-141','dining_room'),('5-143','hotel_corridor'),('5-144','dining_room')],
 '15a9':[('5-145','supply_store'),('5-151','park_garden'),('5-154','hotel_lobby'),('5-161','hotel_corridor'),('5-162','hotel_lobby')],
 '15a10':[('5-163','theatre_preparation'),('5-167','park_garden'),('5-173','hotel_corridor'),('5-175','guest_room'),('5-176','hotel_lobby')],
 '15a11':[('5-185','hotel_lobby')],
 '187':[('6-L01','lower_stairway')],
 '188':[('6-D01','hotel_corridor')],
 '16a':[('6-01','lower_stairway'),('6-04','lower_corridor'),('6-07','shelter_reception'),('6-14','shelter_inner'),('6-17','operating_archive')],
 '16a2':[('6-21','operating_archive')],
 '16a3':[('6-41','operating_archive')],
 '16a4':[('6-61','operating_archive')],
 '16a5':[('6-81','operating_archive')],
 '194':[('6-M01','operating_archive')],
 '11d':[('R-05','trial_elevator'),('R-06','service_lounge'),('R-07','dining_room'),('R-08','hotel_lobby'),('R-10','guest_room'),('R-11','hotel_lobby')],
 '12d':[('R2-04','trial_elevator'),('R2-05','hotel_multiuse'),('R2-06','kitchen'),('R2-08','hotel_lobby'),('R2-10','hotel_lobby'),('R2-11','kitchen'),('R2-12','guest_room')],
 '13d':[('R3-04','trial_elevator'),('R3-05','hotel_lobby'),('R3-11','hotel_corridor'),('R3-12','kitchen'),('R3-13','hotel_lobby')],
 '14d':[('R4-07','inspection_hall_normal'),('R4-11','hotel_lobby'),('R4-14','maintenance_workshop'),('R4-15','dining_room')],
 '15d':[('R5-04','trial_elevator'),('R5-06','hotel_lobby'),('R5-10','dining_room'),('R5-11','guest_room'),('R5-12','hotel_corridor'),('R5-14','guest_room'),('R5-17','hotel_lobby')],
 '16d1':[('R6-01','operating_archive'),('R6-13','loading_gate'),('R6-14','outside_threshold'),('R6-16','operating_archive')],
 '16d2':[('R6-21','operating_archive'),('R6-31','loading_gate'),('R6-32','operating_archive'),('R6-34','lower_corridor'),('R6-35','operating_archive'),('R6-36','loading_gate'),('R6-37','outside_threshold')],
}

# Source-only contexts. These never grant first-person knowledge or inventory.
CONTEXT={
 ('13a4','3-35'):'viewed-recording',('13a4','3-36'):'viewed-recording',('13a4','3-37'):'viewed-recording',('13a4','3-38'):'viewed-recording',
 ('14a5','4-64'):'current-observation',('14a5','4-69'):'objective-other-person',
 ('14a11','4-147a'):'objective-unseen-by-mio',('14a11','4-148'):'objective-unseen-by-mio',('14a11','4-151'):'objective-unseen-by-mio',('14a11','4-152'):'objective-unseen-by-mio',('14a11','4-163'):'objective-unseen-by-mio',
 ('15a2','5-18'):'objective-unseen-by-mio',('15a2','5-19'):'objective-unseen-by-mio',
 ('15a6','5-90'):'reported-memory-nana',('15a4','5-66'):'objective-unseen-by-mio',
 ('15a10','5-168'):'objective-unheard-by-mio',('15a10','5-169'):'objective-unheard-by-mio',('15a10','5-170'):'objective-unheard-by-mio',('15a10','5-171'):'objective-unheard-by-mio',('15a10','5-172'):'objective-unheard-by-mio',('15a10','5-175'):'objective-unseen-by-mio',
 ('14d','R4-03'):'belief-release-not-memory-restoration',
}

# Nothing in this paragraph locates the preparation in a guest room. Do not
# manufacture one simply because the next section returns to the interview.
UNPLACED={('14a12','4-174'):'Preparing her papers/camera is explicit; the room where she prepares them is not.'}

# Reviewed shots. Ranges are one-based, end-exclusive, and only apply to nodes
# whose actual source runs. A later range never makes an unchosen route happen.
# Multiple ranges for one CG are intentional (e.g. a song interrupted by talk).
CG_SHOTS=[
 ('c2_first_performance','12a3',236,280,'current-observation','The first solo song is actually performed, before the premature applause.'),
 ('c2_first_performance','12a3',290,298,'current-observation','The same first song resumes; clear before he lowers the microphone.'),
 ('c2_trial_voice','12c2',584,592,'current-trial','Mio and Yuu discuss the still-unfilled interval; no file playback or confession is depicted.'),
 ('c3_blindfold_test','13a12',36,56,'current-observation','Ken is still blindfolded and Sora is awake on the opposite bench. Clear before the actual entry.'),
 ('c3_information_custody','13a12',78,90,'current-observation','Nana hands over the still-closed envelope after the two departing bodies cannot see inside. Catalog source 13a11 is superseded by this exact current source.'),
 ('c3_mirror_demonstration','13a2',78,86,'current-observation','The ordinary mirror shows Sora as Sora; physical bodies do not transform. Clear before the camera shot.'),
 ('c3_trial_contradiction','13c2',123,141,'current-trial','The physical Ken body reacts and corrects the unspoken original words. The responding controller is Sora, not a second ghost or returning Ken.'),
 ('c4_historical_model','14a2',49,179,'current-observation','The old miniature park is observed as an old display; it is not the exact present escape plan.'),
 ('c4_own_senses','14a8',7,39,'current-observation','Haruka stands still by the doorway, listening while sight is unavailable. Clear before Mio takes her hand.'),
 ('c4_remaining_photograph','14d',469,477,'current-observation','Mio checks the borrowed camera, not a paper photograph. Clear before optional painting/footboard callbacks.'),
 ('c4_trial_late_alibi','14c3',7,45,'current-trial','Mio presses Rei at separate podiums; no invented creation flashback or alibi proof.'),
 ('c4_workshop_alignment','14a8',236,254,'current-observation','Rin and Rei carry the ordinary closed parts box; Mio/Haruka carry their different empty document case.'),
 ('c5_five_in_lobby','15d',518,530,'current-observation','The actual five prepare the same route with separate purposes. The wide shot neither invents a vow nor erases Nana from the living roster.'),
 ('c5_not_your_side','15a7',273,311,'objective-unheard-by-mio','Akari and Satsuki confront one another after the others move away. Do not grant Mio the unheard dialogue.'),
 ('c5_trial_inconvenient_truth','15c2',653,661,'current-trial','Akari answers Mio about the cause before the unavailable rewind; no new poison or clue is shown.'),
 ('c6_bench_remembered','16a',85,181,'current-observation','Present-day Nana/Mio at the second bench position. It is a current explanation, not a childhood reenactment or shared memory download.'),
 ('c6_current_and_old','16a',199,207,'current-observation','Rin reads the adjacent operating notice before touching the terminal. No past screen is falsely shown as a current interaction.'),
 ('c6_final_question','16c3',543,547,'current-trial','Mio keeps her own protected page and adds an ordinary note as the others prepare to leave. The solo framing does not claim the chamber is otherwise empty.'),
 ('c6_outside_not_resolution','16d2',512,518,'current-observation','Mio physically crosses the actual exit and follows Satsuki footsteps. Clear before the adult responders arrive; this shot promises no celebration or resolved future.'),
 ('c6_support_keep','16d2',380,392,'conditional-current-observation','Only support-B: Nana writes at the counter while the currently responsive Lappy stands independently nearby.'),
 ('c6_support_stop','16d2',326,338,'conditional-current-observation','Only support-A: Rin places the now-unresponsive physical body in the open ordinary carrying box. No present memorial portrait is substituted.'),
 ('execution_c1_01','11d',100,102,'observed-execution','Entrance inspection corridor and lamps, before bracing the descending gates.'),
 ('execution_c1_02','11d',102,110,'observed-execution','The injured right wrist cannot hold the gate; the body is visibly still active.'),
 ('execution_c1_03','11d',120,124,'observed-execution','He returns and strikes the transparent physical barrier, not a magical farewell.'),
 ('execution_c1_04','11d',144,146,'observed-execution','The opaque last gate hides the body; impact is not newly shown through it.'),
 ('execution_c1_05','11d',146,154,'observed-execution','Only after the impact: the visibly unresponsive body and restrained purple stain.'),
 ('execution_c2_01','12d',28,56,'viewed-live-execution-screen','Yuu remains active at the stage microphone while delayed feedback continues.'),
 ('execution_c2_02','12d',56,62,'viewed-live-execution-screen','The complete microphone drops as he backs away; not a detached crime-scene base.'),
 ('execution_c2_03','12d',62,70,'viewed-live-execution-screen','The closed exit and moving flat wall. Clear for the cut to the surviving observers.'),
 ('execution_c2_04','12d',72,80,'viewed-live-execution-screen','He hangs from the low railing while the stage tilts, before the fall.'),
 ('execution_c2_05','12d',82,84,'viewed-live-execution-screen','The unresponsive body is visible after the fall. Clear for the separate microphone/recording insert.'),
 ('execution_c3_01','13d',43,49,'observed-execution','The added orange rescue jacket falls over the actual Ken body, currently controlled by Sora.'),
 ('execution_c3_02','13d',49,61,'observed-execution','He releases the ordinary training prop and turns toward the closed exit; the belt coins do not become rescue targets.'),
 ('execution_c3_03','13d',85,89,'observed-execution','He lowers his body and holds the added jacket near his face in ordinary smoke.'),
 ('execution_c3_04','13d',89,117,'observed-execution','The still-active body strikes the physical transparent barrier and seeks an opening; no outside hand is added to the shot.'),
 ('execution_c3_05','13d',119,123,'observed-execution','After ventilation the dead body remains and the added jacket is separately on the floor. No physical Ken resurrection is implied.'),
 ('execution_c4_01','14d',27,37,'observed-execution','The old park train and forced ceremony precede removal of the ribbon.'),
 ('execution_c4_03','14d',57,63,'observed-execution','Rei tries the closed exit and drops the papers. No newly opened escape path.'),
 ('execution_c4_04','14d',69,77,'observed-execution','The old park train runs toward the unfinished end while he tries to leave the seat; clear before the view is occluded.'),
 ('execution_c4_05','14d',85,91,'observed-execution','Only after the occluded impact the stopped carriage and unresponsive body are visible.'),
 ('execution_c5_01','15d',13,31,'viewed-live-execution-screen','Akari stamps the ordinary forms inside the inspection box. Her fallen hairpin is absent.'),
 ('execution_c5_02','15d',33,41,'viewed-live-execution-screen','She stops accepting the form sequence. Clear before she moves to the exit.'),
 ('execution_c5_03','15d',49,59,'viewed-live-execution-screen','She pushes against the box/exit as packaging advances. No rescue appears.'),
 ('execution_c5_04','15d',59,63,'viewed-live-execution-screen','The large packaging plate approaches and the impact is occluded. No living success follows.'),
 ('execution_c5_05','15d',63,69,'viewed-live-execution-screen','The unresponsive body is confirmed before the cut back to Satsuki at her podium.'),
]

# Every catalog CG is audited, including deliberately unbound ones. Incompatible
# art never becomes true merely because a renderer needs a background image.
CG_EXCLUSIONS={
 'c2_props_normal':('pixel-story-conflict','An ordinary earlier props chest is required at 12a6:275, but the inspected image puts the later detached round crime-base inside it.'),
 'c6_descending_order':('pixel-story-conflict','The inspected image puts Satsuki first and Rin last; current 16a:31 explicitly orders Rin, Sho, Nana, Mio, Satsuki.'),
 'execution_c4_02':('pixel-story-conflict','The inspected image places Rei holding the checklist inside the carriage. Current 14d:61 drops those papers before he is dragged into that carriage at 67.'),
 'c2_kitchen_boundary':('no-exact-current-shot','The inspected tray-at-doorway shot does not match current A at 12a:364, which starts with a pot and a hand reaching for its handle. Do not relabel the picture as a record of that act.'),
 'c2_unshared_table':('no-exact-current-shot','No exact current 12d shot puts Nana alone with an untouched cup at this dining table. R2-07 explicitly says she is absent; do not place her there.'),
 'c3_after_two_absences':('no-exact-current-shot','Current 13d does not specify Mio alone between two closed empty-room doors. R3-11 is instead a half-open conversation with living Nana.'),
 'c4_questioning_origin':('no-exact-current-shot','Current 14a7 disclosure is standing at the dining-room entrance and in front of other participants. Do not replace it with this private seated two-person lounge conversation.'),
 'c5_lines_not_answers':('no-exact-current-shot','Current 15a:7..333 explicitly keeps Koto wrist exposed; the inspected reaction CG covers both wrists with sleeves.'),
 'c5_separate_promises':('no-exact-current-shot','The inspected Nana/Koto cup-reaching gesture is not the current 15a4 action. The actual spare-cup mistake is Mio stopping Nana, not Koto; 5-59 concerns a plate.'),
}

# Actual personal-time locations, including separate late-calendar callbacks.
# Anonymous heading IDs vary with edits, so these use reviewed source lines.
# A skipped branch never runs a range belonging to it.
FTE_RUNS={
 '20':[(8,'supply_store')], '21':[(8,'hotel_lobby')],
 '22':[(8,'dining_room')], '23':[(8,'park_garden'),(210,'clinic'),(214,'park_garden')],
 '24':[(10,'plaza')], '25':[(9,'kitchen')],
 '26':[(8,'laundry_room'),(417,'hotel_lobby'),(501,'laundry_room')],
 '27':[(7,'park_garden')], '28':[(7,'supply_store')],
 '29':[(9,'hotel_lobby')], '30':[(9,'supply_store')],
 '31':[(8,'hotel_lobby'),(16,'park_garden'),(20,'hotel_lobby')],
 '32':[(7,'park_garden')], '33':[(8,'plaza')],
 '34':[(10,'park_garden'),(324,'supply_store'),(492,'park_garden')],
 '35':[(8,'hotel_lobby'),(410,'supply_store')], '37':[(7,'laundry_room')], '38':[(9,'hotel_lobby')],
 '36':[(8,'laundry_room'),(138,'staff_passage'),(150,'supply_store'),(216,'laundry_room'),(226,'supply_store'),(256,'laundry_room'),(306,'hotel_corridor')],
 '39':[(9,'guest_room'),(13,'laundry_room'),(19,'guest_room'),(27,'hotel_lobby')],
 '40':[(7,'dining_room')], '41':[(7,'supply_store')],
 '42':[(7,'ticket_booth'),(363,'park_garden')], '43':[(9,'hotel_lobby'),(333,'kitchen'),(345,'hotel_lobby')],
 '44':[(7,'hotel_corridor'),(23,'hotel_lobby'),(61,'hotel_corridor'),(75,'hotel_lobby'),(85,'hotel_corridor'),(91,'hotel_lobby'),(487,'hotel_corridor')],
 '45':[(7,'park_garden'),(369,'park_garden')], '46':[(7,'hotel_lobby'),(435,'hotel_corridor')],
 '47':[(7,'park_garden')], '48':[(9,'hotel_lobby')],
 '49':[(7,'park_garden'),(273,'plaza'),(361,'park_garden'),(367,'plaza'),(381,'hotel_lobby'),(421,'park_garden'),(445,'park_garden'),(457,'hotel_corridor'),(469,'guest_room')],
 '50':[(7,'dining_room'),(565,'guest_room')], '51':[(7,'plaza'),(379,'plaza')],
 '52':[(7,'hotel_lobby'),(215,'kitchen'),(257,'hotel_corridor'),(263,'kitchen')],
 '53':[(9,'hotel_lobby')],
 '54':[(8,'hotel_corridor'),(118,'hotel_lobby'),(132,'hotel_corridor'),(158,'hotel_lobby'),(174,'hotel_corridor'),(192,'hotel_lobby')],
 '55':[(8,'hotel_lobby'),(510,'hotel_corridor')],
 '56':[(8,'hotel_lobby'),(438,'hotel_corridor')],
 '57':[(8,'hotel_lobby'),(122,'hotel_corridor'),(132,'hotel_lobby'),(144,'hotel_corridor'),(158,'hotel_lobby'),(380,'hotel_corridor'),(382,'hotel_lobby'),(418,'hotel_corridor')],
 '58':[(8,'park_garden'),(568,'hotel_corridor')],
 '59':[(8,'ticket_booth'),(278,'park_garden'),(280,'ticket_booth'),(306,'park_garden'),(318,'ticket_booth'),(338,'park_garden'),(340,'ticket_booth'),(390,'park_garden')],
 '60':[(8,'hotel_lobby'),(334,'hotel_corridor')],
 '61':[(7,'hotel_lobby'),(369,'hotel_corridor')],
 '62':[(7,'hotel_lobby')],
 '63':[(9,'park_garden'),(33,'hotel_lobby'),(43,'park_garden'),(351,'plaza'),(447,'park_garden'),(459,'guest_room')],
 '64':[(7,'plaza')],
 '87':[(9,'hotel_lobby'),(45,'park_garden')],
 '88':[(9,'hotel_lobby')],
 '89':[(7,'park_garden'),(31,'plaza')], '90':[(9,'supply_store')],
 '143':[(7,'supply_store'),(91,'hotel_lobby'),(111,'hotel_corridor')],
 '144':[(7,'hotel_lobby')], '145':[(7,'kitchen'),(91,'hotel_lobby')],
 '146':[(7,'laundry_room')], '147':[(7,'park_garden')],
 '148':[(7,'park_garden'),(85,'supply_store')], '149':[(7,'park_garden'),(71,'hotel_corridor')],
 '150':[(7,'supply_store')],
 '151':[(7,'hotel_lobby'),(47,'laundry_room'),(51,'guest_room'),(55,'hotel_lobby')],
 '152':[(7,'plaza'),(41,'hotel_lobby')], '153':[(7,'dining_room')],
}

# Some prose paragraphs explicitly summarize more than one physical stop. The
# displayed set is their current/final stop; preserve, rather than invent, the
# intermediate stops for a future directed transition sequence.
IN_PARAGRAPH_PLACES={
 ('23',210):['clinic','park_garden'],
 ('63',33):['guest_room','hotel_lobby'],
 ('63',337):['guest_room','park_garden'],
 ('149',63):['guest_room','hotel_lobby','park_garden'],
 ('151',47):['guest_room','laundry_room'],
}

FTE_SET_LIMITS={
 'supply_store':'Gift/toy shop or its adjacent display/table uses a common existing set. Dedicated shop/display geometry remains production work; no stock-room story identity, hidden lock or new clue follows.',
 'park_garden':'The exact manuscript may specify hotel yard, bench, indoor glass-roof garden or garden-side rest area. This existing garden is a visual set; a glass-roof indoor-garden/rest-area set is still needed for its literal architecture.',
 'hotel_lobby':'Hotel lounge/rest space uses the hotel common-room mesh. It is not the employee crime-scene service_lounge and does not assign a new meeting-room number.',
 'ticket_booth':'The existing booth geometry is reused as the source ordinary can-toss game booth; no new ticket/exit permission is implied.',
}


def _source(path):
    raw=path.read_bytes()
    return raw.decode('utf-8-sig').splitlines(),hashlib.sha256(raw).hexdigest()


def _reviewed_source(root,prefix):
    paths=list((root/'docs/design/rewrite_v4').glob(prefix+'_*.md'))
    if len(paths)!=1:raise ValueError('Missing/ambiguous reviewed scene source '+prefix)
    path=paths[0];lines,digest=_source(path)
    if digest!=REVIEWED_SOURCE_HASHES.get(prefix):
        raise ValueError('Reviewed scene manuscript changed; re-read before rebinding: '+path.name)
    # Story Source hashes decoded text with universal-newline normalization.
    # Freeze the actual bytes above, expose the same source identity as it does.
    source_hash=hashlib.sha256(path.read_text(encoding='utf-8-sig').encode('utf-8')).hexdigest()
    return path,lines,source_hash


def _heads(lines):
    result=[]
    for i,line in enumerate(lines,1):
        m=re.match(r'^## ((?:[2-6]-|R[1-6]?-)[A-Za-z0-9-]+)\s',line)
        if m: result.append((i,m[1],line))
    return result


def build_more(root=None):
    root=Path(root) if root else ROOT
    world=json.loads((root/'art/space_v4/runtime_v1/world.json').read_text(encoding='utf-8'))['spaces']
    sections={};ranges=[];unbound=[]
    for prefix,runs in RUNS.items():
        path,lines,digest=_reviewed_source(root,prefix);heads=_heads(lines);tokens=[h[1] for h in heads]
        if any(token not in tokens for token,_ in runs):raise ValueError('Reviewed scene section changed '+prefix)
        starts={token:space for token,space in runs};space=None
        for index,(line,location,heading) in enumerate(heads):
            space=starts.get(location,space)
            end=heads[index+1][0] if index+1<len(heads) else len(lines)+1
            ref={'file':path.name,'location':location,'line':line,'fileSha256':digest,'heading':heading}
            if (prefix,location) in UNPLACED:
                unbound.append({'kind':'unplaced-setting','source':ref,'reason':UNPLACED[(prefix,location)]})
                continue
            if space is None:
                unbound.append({'kind':'no-trial-mesh','source':ref,'reason':'Result/trial/execution shot has no ordinary exploration-room mapping. It must keep the actual trial renderer or its bounded execution CG.'})
                continue
            if space not in world:raise ValueError('Missing existing mesh '+space)
            context=CONTEXT.get((prefix,location),'current-observation')
            if prefix=='15a3' and tokens.index(location)<tokens.index('5-47'):context='objective-unseen-by-mio'
            if prefix=='15a9' and tokens.index(location)<tokens.index('5-151'):context='nana-current-observation-mio-absent'
            first=next(({'line':i,'quote':lines[i-1]} for i in range(line+1,end) if lines[i-1].startswith('(')),None)
            value={'space':space,'entry':'section-entry-only','source':ref,'sourceSpan':{'startLine':line,'endLineExclusive':end},'perspective':context,'knowledgeGrant':False,'actorPositionsAssigned':False,'meshOnly':True,'geometryPolicy':'Reuse existing geometry as a visual set only. Preserve the source setting and viewpoint; no room number, exact actor position, wall topology, unseen movement or additional knowledge follows from this mesh.','settingProof':first}
            sections[path.name+':'+location]=value
    # Concrete within-section changes; no generic search for remembered places.
    for prefix,start,end,space,perspective,reason in [
        ('15a5',47,149,'dining_room','objective-unheard-by-mio','Mio has gone upstairs; the remaining breakfast exchange is not her memory.'),
        ('16d2',572,620,'operating_archive','nana-current-observation-mio-absent','Support-B only: an actual external checker enters the current counter; Mio remains outside.'),
        ('16d2',620,626,'outside_threshold','current-observation','The manuscript explicitly returns to outside Mio; Nana remains alive at the counter.'),
        ('15a8',99,173,'kitchen','conditional-current-observation','Only actually routed A follows Mio to call the kitchen; B/C do not play this source range.'),
    ]:
        p,ls,digest=_reviewed_source(root,prefix)
        if start>len(ls) or end>len(ls)+1:raise ValueError('Reviewed scene transition changed '+prefix)
        ranges.append({'space':space,'source':{'file':p.name,'line':start,'fileSha256':digest,'quote':ls[start-1]},'startLine':start,'endLineExclusive':end,'perspective':perspective,'knowledgeGrant':False,'reason':reason,'clearCgOnEntry':True,'scope':'only-when-these-source-nodes-actually-run'})
    fte_ranges,fte_unbound=_freetime_ranges(root,world)
    ranges.extend(fte_ranges);unbound.extend(fte_unbound)
    cg_ranges,cg_audit=_cg_ranges(root)
    unbound.extend(x for x in cg_audit if x['status']!='bound-source-shot')
    return {'version':1,'sections':sections,'sceneRanges':ranges,'cgRanges':cg_ranges,'cgAudit':cg_audit,'unbound':unbound,'freetimeReviewedSourceCount':len(FTE_RUNS),'inParagraphPlaces':[{'file':next((root/'docs/design/rewrite_v4').glob(prefix+'_자유시간*.md')).name,'line':line,'explicitPlaceSequence':places,'policy':'All stops are explicit within one authored paragraph. Current renderer uses the bounded primary set, not an invented intermediate dialogue/event.'} for (prefix,line),places in IN_PARAGRAPH_PLACES.items()],'dedicatedSetNeeds':[
        {'setting':'호텔 옆 유리지붕 실내정원/정원 옆 휴게공간','sources':['27:7','45:7','58:8','147:7'],'constraints':['유리문/유리지붕, 화분 줄과 닦는 천·양동이','앉는 벤치와 그림을 보는 별도 탁자/게시판','실제 식물/조화 여부와 그림 속 사물을 현장 물건으로 혼합하지 않음']},
        {'setting':'기념품점/완구점과 인접 진열·탁자','sources':['20:8','28:7','30:9','34:324','41:7','143:7','150:7'],'constraints':['진열장 아래 선반과 장식용 열쇠','태엽 토끼/자동차·금붕어 인형은 날짜·소유·수리상태에 따라 다름','공용 stock-room mesh 재사용이 범행용 수납함/출입권의 새 사실이 아님']},
        {'setting':'호텔 작은 휴게·놀이공간/공용 세면실','sources':['29:9','37:7','38:9','43:9','52:7','57:8'],'constraints':['호텔 공용 공간이며 직원 휴게실 사건현장과 구별','오목판/고리판/사진집/숨은그림책은 실제 현재 만남일 때만','세면실 거울·수건·가위집은 원문에 정한 실제 사용/반납 범위만']},
        {'setting':'공원 깡통 놀이부스','sources':['42:7','59:8'],'constraints':['깡통 여섯·부드러운 공 세개·카운터·동일 출발선','새 티켓 통행권/출구 해금이나 구조훈련으로 바꾸지 않음']},
    ],'scope':'Explicit reviewed chapter2..6 living scenes, chapter1..6 aftermath entries and reviewed personal-time manuscripts. Shared meshes are visual sets, never new location/actor facts. CGs only cover the exact source nodes in their bounded range.','lifecycle':{'match':'actual node source.file and source.line in [startLine,endLineExclusive)','priority':'bounded sceneRanges override section entry only for those actually played source nodes','cgClear':'On every node entry clear prior image unless that new node itself matches an inspected cgRange. Clear on task/menu/document, scene change, source exit, load and return. Never carry a CG across a source insertion/call.','knowledge':'No scene/CG binding sets story flags, inventory, unseen dialogue knowledge, actor world coordinates or branch outcomes.'}}


def _cg_ranges(root):
    catalog=json.loads((root/'art/v4_production/completion/final_catalog.json').read_text(encoding='utf-8'))['story_cg']
    selected={r['logical_id']:r for r in catalog}
    if len(selected)!=len(catalog):raise ValueError('Duplicate CG identity in current catalog')
    result=[];audit=[];shots={x[0] for x in CG_SHOTS}
    for logical,review in REVIEWED_CG.items():
        actual=selected.get(logical)
        if actual is None:
            audit.append({'kind':'cg','logical_id':logical,'status':'missing-current-art','reason':'Previously inspected CG disappeared from current catalog.'})
            continue
        image_path=root/actual['webp'];image_hash=hashlib.sha256(image_path.read_bytes()).hexdigest()
        unchanged=actual['webp']==review['image'] and image_hash==review['imageSha256']
        if not unchanged:
            audit.append({'kind':'cg','logical_id':logical,'status':'changed-art-needs-pixel-review','image':actual['webp'],'reason':'Current image differs from the actual pixels reviewed for this module. A replacement does not inherit approval.'})
            continue
        if logical not in shots:
            status,reason=CG_EXCLUSIONS.get(logical,('outside-owned-shot-scope','Prologue/case-one living shot or separately owned incident inspection. Keep its existing owner; this later-scene module does not invent an additional placement.'))
            audit.append({'kind':'cg','logical_id':logical,'status':status,'reason':reason,'image':review['image'],'imageSha256':image_hash})
            continue
        audit.append({'kind':'cg','logical_id':logical,'status':'bound-source-shot','image':review['image'],'imageSha256':image_hash})
        for cg,prefix,start,end,perspective,reason in CG_SHOTS:
            if cg!=logical:continue
            p,lines,digest=_reviewed_source(root,prefix)
            if not (1<=start<end<=len(lines)+1):raise ValueError('CG source range changed '+logical)
            result.append({'logical_id':logical,'image':review['image'],'imageSha256':image_hash,'catalogMetadata':review['metadata'],'source':{'file':p.name,'line':start,'fileSha256':digest,'quote':lines[start-1]},'startLine':start,'endLineExclusive':end,'perspective':perspective,'knowledgeGrant':False,'actorPositionsAssigned':False,'reason':reason,'clearOnExit':True,'clearOnInteractive':True,'scope':'actual-source-nodes-only','presentation':'full-frame-story-shot-not-an-investigation-answer','catalogSourceMatchesCurrentBinding':Path(actual.get('manuscript','')).name==p.name})
    # New catalog rows are also visible as unreviewed, never silently imported.
    for logical in sorted(set(selected)-set(REVIEWED_CG)):
        audit.append({'kind':'cg','logical_id':logical,'status':'new-art-needs-pixel-review','reason':'No reviewed pixels/source shot yet.'})
    return result,audit


def _freetime_ranges(root,world):
    result=[];unbound=[]
    for prefix,runs in FTE_RUNS.items():
        paths=list((root/'docs/design/rewrite_v4').glob(prefix+'_자유시간*.md'))
        if len(paths)!=1:raise ValueError('Missing reviewed personal-time manuscript '+prefix)
        p=paths[0];raw=p.read_bytes();raw_hash=hashlib.sha256(raw).hexdigest()
        if raw_hash!=REVIEWED_FTE_HASHES.get(prefix):raise ValueError('Reviewed personal-time source changed '+p.name)
        text=p.read_text(encoding='utf-8-sig');lines=text.splitlines();digest=hashlib.sha256(text.encode('utf-8')).hexdigest()
        for index,(start,space) in enumerate(runs):
            end=runs[index+1][0] if index+1<len(runs) else len(lines)+1
            if not (1<=start<end<=len(lines)+1) or space not in world:raise ValueError('Invalid reviewed personal-time scene range '+prefix)
            perspective='objective-unseen-by-mio' if (prefix=='51' and start>=379) or (prefix=='45' and start>=369) else 'current-observation'
            result.append({'space':space,'source':{'file':p.name,'line':start,'fileSha256':digest,'quote':lines[start-1]},'startLine':start,'endLineExclusive':end,'perspective':perspective,'knowledgeGrant':False,'actorPositionsAssigned':False,'kind':'freetime-current-setting','clearCgOnEntry':True,'scope':'only-when-these-source-nodes-actually-run','meshOnly':True,'geometryPolicy':FTE_SET_LIMITS.get(space,'Existing visual set only; source determines the actual setting and who is present. No numbered guest room or extra world fact is assigned.')})
    # Report future new meetings instead of accidentally using the previous
    # scene or guessing from an actor name/title. No generated file is edited.
    index_path=root/'data/v4_story/freetime/index.json'
    if index_path.exists():
        index=json.loads(index_path.read_text(encoding='utf-8'))['meetings']
        for key,entry in index.items():
            g=json.loads((root/'data/v4_story'/entry['path']).read_text(encoding='utf-8'))
            for file in {g.get('sourceFile'),g.get('baseSourceFile')} - {None,''}:
                if file.split('_')[0] not in FTE_RUNS:
                    unbound.append({'kind':'freetime-source-needs-scene-review','meeting':key,'source':{'file':file},'reason':'New personal-time source has no reviewed physical scene range; do not default to plaza or previous scene.'})
    return result,unbound

# Frozen after direct manuscript and 72-image pixel inspection, 2026-10-29.
REVIEWED_SOURCE_HASHES={
 '194': '1e8186c67871ad20d087c7a2bd9589781c6dac12b85cd6969fdb52040917b287',
 '187':'a330de709587dd08380bb44ab76964af749c47becf37d017149c6bba6227d7b0',
 '188':'da96d7a4ee54c414bba976401edac64c164a61192de7ac1171c08794b3913e81',
 "11d": "a2f38a3df9af4ecc2761053064d311c4a1c8936781eebb1cbb5ba6d071031db1",
 "12a": "76c22ed512dcabe991230b1d8f153d0e25065a0c96ecb487e3f229c90a6317e0",
 "12a2": "1af5c5d17845bf37be42e4b295707d06b4bc6ac2e1d731a29f33c1b0df61b967",
 "12a3": "79cc5431884bc10f2cf27ece2b8812d0eaec4be6042433acdcd49b28c8570ac7",
 "12a4": "9b19a07bdb9a869843fe3e17ea82f9300845a039bf04ac80b7ab886ce6c56475",
 "12a5": "5856664778f76feae589de7a5cc163f9748a86255da86540e9e8685bd8d456ef",
 "12a6": "fff7e39e996a021d6f1c6b443278aa3a09a8c6271e17a8e807d7ea72a2169f9f",
 "12a7": "89c8012962fd168540f93a1b5283f2d99eb10284e782da55b9b2d562d0179af1",
 "12c2": "58e1eb66bced8fa72e1abe3c3d2639e9b2360ee5f9a856400f08ac95f4dcb1d7",
 "12d": "575b97dd1832b8b51351b856a20504ddf574e6620f12a68fab04d052f7b9e393",
 "13a": "6aed86ad5420d00f7ffd6f708fe2c1e71a50449b7d9ae747791ad200b0c567f5",
 "13a10": "6f01f79e8124a33ee56b7351ea32caeca6f0b4957d688b5f1cb40f190f3cf148",
 "13a11": "2aa93bc08d55b1da65ca2881eef989658a51c3e99706478e36ae64f4c7d60237",
 "13a12": "8ac013b445c89cf40b7c59695801a415b32705b5cb38cfa407651c080f2d8c3d",
 "13a2": "710270922502f32c190581d7e597c33cfb263a2a2f81784ad460b176a11233f5",
 "13a3": "71d49f7d08a4944290f9e8b951779bc06e06aecaa1dff417d4036f40351ddb63",
 "13a4": "84fb7d77d5321d7c12cf604fcc8203b46a70e2d32e7c5b29b0f1cf743fee3ca7",
 "13a5": "7506b3f9ed2d8ac5db57852eda63e689cddd168a1365e1940334cdb2d622d7bc",
 "13a6": "a27fd940d3aed1e384ecdbd4fbf7147508334de1314efa75027eb8f6a17dc864",
 "13a7": "5d6a54d97508c6aba659cc508a75371cb5054dfef7dc57ce204db6aa3e0673bd",
 "13a8": "c7bbbc091bdb3b6d02e0ae6da5672d68275599dd6686000b1ef7cb4931827801",
 "13a9": "93954641978a6b9cf8afb1fa60136c0bd10e8108d1904f94e6563137b1fd05bd",
 "13c2": "ed18a9100c700d8f580c35aa4ac8c90e25ca89f77b34fdfce48f4de837ac414d",
 "13d": "51548037dfaac7a8e6c42dec0aea35d1ecdfc51739358d6523f66d8e2a1bdc4c",
 "14a": "89937179f250e4bf5bb286e835328b92b3b2ca2a56da270fb260d052187cf444",
 "14a10": "f6479185ff87a9b7fd33acc04d14dd8e0efc7ec46893db950c3d90731741277d",
 "14a11": "f796889b58ab1174091ad316bfddf2ce031eb33a29d7a58af7779d66a6ba92e0",
 "14a12": "6f685f0253b09d5d0077f7657c4a19ebb20beaeefc7e5fea42a650dd467d4c4b",
 "14a13": "573365e0a765107c084286e79e9058c7ec77004f47975deedac220ba96155885",
 "14a2": "64ac4bdbc71f88ffec050a55f3902ba2ba5dcdc0db41c7b4e88342a3c64af404",
 "14a3": "a685c4ceeb80a98543c19e01a11d09f4a5158834547ea01daf154d05b38e945c",
 "14a4": "981e913f8b73f7da4ebb2508a2f69cfcb1f871097e0f2a3063dd18a5afb8bfac",
 "14a5": "42ae50f06869c5fabdbc41e8a4e5016a9c9778f1dcc9cdbd61e68269c615a59c",
 "14a6": "b86570b8a913a72b090175b1d7046885cb4c5918cc624ba02c904385353b9c18",
 "14a7": "ed45602afa5cfc0c72a8eb7eac84bcf4e7f230728da4113346c55d4f6561b524",
 "14a8": "f6b0bd840396abb8d64694615abb71ee69b07f4a4533319824be10850fb8ce3b",
 "14a9": "765c6b35c6bb92011129ead820abd089f96b9a4c7c426b8f8e685abc3b5d04cb",
 "14c3": "ca5c63b0f1b3e97c4c848515e3e13ba76c6e77bab079e5b66fc9cbdd0519746b",
 "14d": "99e15f26d3109db8db84dbb72019c54f7aec49a4b1de9430ee0b3e7338057383",
 "15a": "8ad308556d60430b05043d9b9f71e8d74865e44fb5f12e5b5b63cb9c7bbf8454",
 "15a10": "9d315c3530e29b633e65ae474d503c36fcafb4d8af28295e1d98bb209abe69a5",
 "15a11": "0e536eefef75f4ae567814fc48e81f43d29ff6a69e15f99d624536b57956ddfb",
 "15a2": "934ca5451ac4be5dc3f96a46fc2d4bb77eec43073ce2c32c14e532fdd408a857",
 "15a3": "ab26f8351d0ffabc1dd26f6126335e835a8ded7ca39579616d8ea79f84b93bd7",
 "15a4": "a52f0ef8e1aebea1dcc57d47d09fadd2550a4292b8a21d5752aead851686a521",
 "15a5": "30c676374b431a3d99ea26c9fa12f4662712017f1ef96956e05954a41c731245",
 "15a6": "66249841dc50013997cea875e820bbe9475213607623394aaf5ca84765063b03",
 "15a7": "31929abe1dc32d6c30a0ddaf08145c1855ffa9ad5a019289dbca43d4f545e1aa",
 "15a8": "526650835e3117daa4bbd22dddc867766ace35c14fc3de8af582980a49062ab2",
 "15a9": "9a4aa5eed40b873397ac2aa8bf0bbe6724acceddd8fd6d9c7fc287e0801ee866",
 "15c2": "d3766924530f626788a2632c088d3bd9432f257298561574f96e699b81cd46d0",
 "15d": "8f564cba5a6ddd6a2a01fae3649107a63f82cdaf8f16fd2169d26c4a7f422d4a",
 "16a": "6ef6519a9dddc75fab92991240093d0c717d380efdcc4b41006cdea66d4a64c6",
 "16a2": "43a345cb1268d6c4b943a2212fdfa0f370742d03bd69e2b7d45e120c9bffe4f4",
 "16a3": "3c28296a86f8cb7448b1fe64aacffdc4e737dc48e98ad059d2e375a44dd7ef70",
 "16a4": "279511f574fac98ab5448013bcd5623a2306323fb7b57b22beb9954d3503e0d8",
 "16a5": "ae62eec4a8a5625a8083820aeda114afa3d7fe9720102a2b14b2a4d38c818445",
 "16c3": "1a4f9a1478d6753add49d87c33e54bcaa9f5252321d237683c8f4dcec910d329",
 "16d1": "6c3d46f4110d989324e63cbd85a7e29d9cdd9b4ed33bfb7d913f1dd234468d67",
 "16d2": "97c75fbc6ef240ded0e1c89b9e3ab2a04340d5890c9b2e42d321614e5e459acd"
}

REVIEWED_CG={
 "c1_contact_disagreement": {
  "image": "art/cg_v4/delivery/c1_contact_disagreement_builtin_r1.webp",
  "imageSha256": "7347621aa96b86ddac7ef446d2e440be0e96920fcfabb2308f3d74c1e47248ef",
  "metadata": "art/cg_v4/builtin/c1_contact_disagreement_builtin_r1.json"
 },
 "c1_next_morning": {
  "image": "art/cg_v4/delivery/c1_next_morning_builtin_r1.webp",
  "imageSha256": "150b67a1f48a8547665999aa5c3bc2aebf4dd945facfad22123a558e4a53a268",
  "metadata": "art/cg_v4/builtin/c1_next_morning_builtin_r1.json"
 },
 "c1_room_exchange": {
  "image": "art/cg_v4/delivery/c1_room_exchange_builtin_r2.webp",
  "imageSha256": "bf57bacd2c6eba3317c67883e804b60411bc628ba819883d4e8ee78233a30023",
  "metadata": "art/cg_v4/builtin/c1_room_exchange_builtin_r2.json"
 },
 "c1_tools_distance": {
  "image": "art/cg_v4/delivery/c1_tools_distance_builtin_r2.webp",
  "imageSha256": "3648e435dd581a2f017cbd357fa3507c4d92cf474b965a2dab8b6e5c0f1bafb7",
  "metadata": "art/cg_v4/builtin/c1_tools_distance_builtin_r2.json"
 },
 "c1_trial_pressure": {
  "image": "art/cg_v4/delivery/c1_trial_pressure_builtin_r1.webp",
  "imageSha256": "843a55f222107ebffa94d51d44e339dedc08083fa06da0e789bf842b3a146347",
  "metadata": "art/cg_v4/builtin/c1_trial_pressure_builtin_r1.json"
 },
 "c2_first_performance": {
  "image": "art/cg_v4/delivery/c2_first_performance_builtin_r1.webp",
  "imageSha256": "a59a806c46a6d3d389a1c85a4dac7c41381f9eee1edb5ee75ade9a546915e595",
  "metadata": "art/cg_v4/builtin/c2_first_performance_builtin_r1.json"
 },
 "c2_kitchen_boundary": {
  "image": "art/cg_v4/delivery/c2_kitchen_boundary_builtin_r1.webp",
  "imageSha256": "09c301fa5888cf305e5d9f1a7060a271db1ba3e5605c0185e2d6f530e8bfd7c9",
  "metadata": "art/cg_v4/builtin/c2_kitchen_boundary_builtin_r1.json"
 },
 "c2_props_normal": {
  "image": "art/cg_v4/delivery/c2_props_normal_builtin_r1.webp",
  "imageSha256": "6e537e84cbae9514cd873320357b58ba96ff515dec1f46aa442a2c329cc17866",
  "metadata": "art/cg_v4/builtin/c2_props_normal_builtin_r1.json"
 },
 "c2_trial_voice": {
  "image": "art/cg_v4/delivery/c2_trial_voice_builtin_r1.webp",
  "imageSha256": "d7fa6a5fa3a89af8e41a714d5ce50b1122f46dee7c5971c9f16629a958a7d75a",
  "metadata": "art/cg_v4/builtin/c2_trial_voice_builtin_r1.json"
 },
 "c2_unshared_table": {
  "image": "art/cg_v4/delivery/c2_unshared_table_builtin_r1.webp",
  "imageSha256": "4a338fa922a6f82b58aa380cd9ee1737ae4e20085faaa48c7f0044639a6a31f1",
  "metadata": "art/cg_v4/builtin/c2_unshared_table_builtin_r1.json"
 },
 "c3_after_two_absences": {
  "image": "art/cg_v4/delivery/c3_after_two_absences_builtin_r1.webp",
  "imageSha256": "763ee3ff6b9c4eeaae57d6549d9d1ae3841114107118aafdbdaf8913284e5a6c",
  "metadata": "art/cg_v4/builtin/c3_after_two_absences_builtin_r1.json"
 },
 "c3_blindfold_test": {
  "image": "art/cg_v4/delivery/c3_blindfold_test_builtin_r2.webp",
  "imageSha256": "6753dc4586dd499f2ee1936a90aea7b0bed4b4db9daa2970bf50428dec0d4233",
  "metadata": "art/cg_v4/builtin/c3_blindfold_test_builtin_r2.json"
 },
 "c3_information_custody": {
  "image": "art/cg_v4/delivery/c3_information_custody_builtin_r1.webp",
  "imageSha256": "19fdfed17e18144f5fe3d99cae92d4c0868f864ccd315b8769dc5f1fb19853a2",
  "metadata": "art/cg_v4/builtin/c3_information_custody_builtin_r1.json"
 },
 "c3_mirror_demonstration": {
  "image": "art/cg_v4/delivery/c3_mirror_demonstration_builtin_r1.webp",
  "imageSha256": "a78652d29e59778e9324ae968bfa98d620c3dd6c00f668bd6271c7632af47ea7",
  "metadata": "art/cg_v4/builtin/c3_mirror_demonstration_builtin_r1.json"
 },
 "c3_trial_contradiction": {
  "image": "art/cg_v4/delivery/c3_trial_contradiction_builtin_r1.webp",
  "imageSha256": "aba86a0c53f85f27166edb0612e6b6244e65ce9df00edea3bce8ce00b0f8385e",
  "metadata": "art/cg_v4/builtin/c3_trial_contradiction_builtin_r1.json"
 },
 "c4_historical_model": {
  "image": "art/cg_v4/delivery/c4_historical_model_builtin_r1.webp",
  "imageSha256": "cf03467e64bb224ec7e0a307ff8780c5f91230e3bb590d39234eaba9581b163f",
  "metadata": "art/cg_v4/builtin/c4_historical_model_builtin_r1.json"
 },
 "c4_own_senses": {
  "image": "art/cg_v4/delivery/c4_own_senses_builtin_r1.webp",
  "imageSha256": "51058f03253d2327935fc1492f0d2acd994fe76c87bfebe2c86dc358ec17ea54",
  "metadata": "art/cg_v4/builtin/c4_own_senses_builtin_r1.json"
 },
 "c4_questioning_origin": {
  "image": "art/cg_v4/delivery/c4_questioning_origin_builtin_r1.webp",
  "imageSha256": "4be7974a73dd971fc68b368701208c51d8f17eb41877604352b26c8624a7b5d8",
  "metadata": "art/cg_v4/builtin/c4_questioning_origin_builtin_r1.json"
 },
 "c4_remaining_photograph": {
  "image": "art/cg_v4/delivery/c4_remaining_photograph_builtin_r2.webp",
  "imageSha256": "c4a9524c51e4481dab0a40d9ecdc8b0ed393a385ab9e565ea84e3f590cccea78",
  "metadata": "art/cg_v4/builtin/c4_remaining_photograph_builtin_r2.json"
 },
 "c4_trial_late_alibi": {
  "image": "art/cg_v4/delivery/c4_trial_late_alibi_builtin_r1.webp",
  "imageSha256": "381d4562fc8255ef9bd803a97462ed9921b4486cf11a7fbd7bc3a8606fbad388",
  "metadata": "art/cg_v4/builtin/c4_trial_late_alibi_builtin_r1.json"
 },
 "c4_workshop_alignment": {
  "image": "art/cg_v4/delivery/c4_workshop_alignment_builtin_r3.webp",
  "imageSha256": "fcb7601ba22a834cb40df4c227aac53a5df0e88eb289cf02f130153869561c43",
  "metadata": "art/cg_v4/builtin/c4_workshop_alignment_builtin_r3.json"
 },
 "c5_five_in_lobby": {
  "image": "art/cg_v4/delivery/c5_five_in_lobby_builtin_r1.webp",
  "imageSha256": "bcebf082ad7582ead34dc83ae65bb25305118a7fdc81bf1931d20be312ebd6ea",
  "metadata": "art/cg_v4/builtin/c5_five_in_lobby_builtin_r1.json"
 },
 "c5_lines_not_answers": {
  "image": "art/cg_v4/delivery/c5_lines_not_answers_builtin_r1.webp",
  "imageSha256": "040c11c86043d1d52dfe675b2686ad52277a7d079b7b106d343be5c712f7f7de",
  "metadata": "art/cg_v4/builtin/c5_lines_not_answers_builtin_r1.json"
 },
 "c5_not_your_side": {
  "image": "art/cg_v4/delivery/c5_not_your_side_builtin_r1.webp",
  "imageSha256": "141b6548e89279332888591e910a5a18c9d06629d552cda8497279ceb3be11f7",
  "metadata": "art/cg_v4/builtin/c5_not_your_side_builtin_r1.json"
 },
 "c5_separate_promises": {
  "image": "art/cg_v4/delivery/c5_separate_promises_builtin_r1.webp",
  "imageSha256": "555419fc673c6ce247b953517c32a1ef24f3c2740b8b1120d1f4734bb3024b3f",
  "metadata": "art/cg_v4/builtin/c5_separate_promises_builtin_r1.json"
 },
 "c5_trial_inconvenient_truth": {
  "image": "art/cg_v4/delivery/c5_trial_inconvenient_truth_builtin_r1.webp",
  "imageSha256": "7d343c1f24c179c031021b554f50fd050881aceb7ba017c62c920a8492887ea1",
  "metadata": "art/cg_v4/builtin/c5_trial_inconvenient_truth_builtin_r1.json"
 },
 "c6_bench_remembered": {
  "image": "art/cg_v4/delivery/c6_bench_remembered_builtin_r1.webp",
  "imageSha256": "41bb9172d052606d882a3495389b0b2b5ccf28ee4e20807030948a322a00b4ac",
  "metadata": "art/cg_v4/builtin/c6_bench_remembered_builtin_r1.json"
 },
 "c6_current_and_old": {
  "image": "art/cg_v4/delivery/c6_current_and_old_builtin_r2.webp",
  "imageSha256": "3b031d5c1a6fdd439d90a8c614ee48588bf7a0033fe6e4998caf76246a06264e",
  "metadata": "art/cg_v4/builtin/c6_current_and_old_builtin_r2.json"
 },
 "c6_descending_order": {
  "image": "art/cg_v4/delivery/c6_descending_order_builtin_r1.webp",
  "imageSha256": "2bb91b25a08a2c2c1fbbae1068c78c3c63eb10314607269deef5e7414b116dfa",
  "metadata": "art/cg_v4/builtin/c6_descending_order_builtin_r1.json"
 },
 "c6_final_question": {
  "image": "art/cg_v4/delivery/c6_final_question_builtin_r1.webp",
  "imageSha256": "8625cdd116dce44edb318b705a822ada08cd824d1752d462df46ea4808a9441c",
  "metadata": "art/cg_v4/builtin/c6_final_question_builtin_r1.json"
 },
 "c6_outside_not_resolution": {
  "image": "art/cg_v4/delivery/c6_outside_not_resolution_builtin_r1.webp",
  "imageSha256": "2227bafe14a03ef306b5248921b47600311819ff85e291e0d773cdaad7da7951",
  "metadata": "art/cg_v4/builtin/c6_outside_not_resolution_builtin_r1.json"
 },
 "c6_support_keep": {
  "image": "art/cg_v4/delivery/c6_support_keep_builtin_r2.webp",
  "imageSha256": "e9a3f5a6f891e396b58baaa4d25bba6058d5228de94b0d4ee24918886eee58ab",
  "metadata": "art/cg_v4/builtin/c6_support_keep_builtin_r2.json"
 },
 "c6_support_stop": {
  "image": "art/cg_v4/delivery/c6_support_stop_builtin_r2.webp",
  "imageSha256": "23d694fc6ca7edbb764741db5e945bf22e8ff7c4e7d05be8acd64f6e58af3d42",
  "metadata": "art/cg_v4/builtin/c6_support_stop_builtin_r2.json"
 },
 "execution_c1_01": {
  "image": "art/cg_v4/delivery/execution_c1_01_builtin_r1.webp",
  "imageSha256": "a3732d02a3612587e96dcf9880cc3dc894a04136485143e8ab18ce06574892e3",
  "metadata": "art/cg_v4/builtin/execution_c1_01_builtin_r1.json"
 },
 "execution_c1_02": {
  "image": "art/cg_v4/delivery/execution_c1_02_builtin_r1.webp",
  "imageSha256": "afa0ba35b043c551335e17d2160fc0ab8a0f2b67cef3d4e258239139525263c5",
  "metadata": "art/cg_v4/builtin/execution_c1_02_builtin_r1.json"
 },
 "execution_c1_03": {
  "image": "art/cg_v4/delivery/execution_c1_03_builtin_r1.webp",
  "imageSha256": "1522e3445369ac4c154c7ffcdc525e8b012cb0f57e53da7536fcbeaf69cb2d82",
  "metadata": "art/cg_v4/builtin/execution_c1_03_builtin_r1.json"
 },
 "execution_c1_04": {
  "image": "art/cg_v4/delivery/execution_c1_04_builtin_r2.webp",
  "imageSha256": "d262d11949c08dfbe45f23b30b7327b09bb2a41754d26ab6df7f44b89aa36b60",
  "metadata": "art/cg_v4/builtin/execution_c1_04_builtin_r2.json"
 },
 "execution_c1_05": {
  "image": "art/cg_v4/delivery/execution_c1_05_builtin_r1.webp",
  "imageSha256": "199341ef0f537223d723cce5d3d451c3af06b3330c22772f1c4dfc252b9f11bc",
  "metadata": "art/cg_v4/builtin/execution_c1_05_builtin_r1.json"
 },
 "execution_c2_01": {
  "image": "art/cg_v4/delivery/execution_c2_01_builtin_r1.webp",
  "imageSha256": "66c62ed98aa2842111ca544ae532f873e59b0001daad205d88186deb3300af31",
  "metadata": "art/cg_v4/builtin/execution_c2_01_builtin_r1.json"
 },
 "execution_c2_02": {
  "image": "art/cg_v4/delivery/execution_c2_02_builtin_r1.webp",
  "imageSha256": "14ef028f36cf739d180cf1277b7c56a7e9fa1708a7ac8196d1b16c0f035ae0a4",
  "metadata": "art/cg_v4/builtin/execution_c2_02_builtin_r1.json"
 },
 "execution_c2_03": {
  "image": "art/cg_v4/delivery/execution_c2_03_builtin_r1.webp",
  "imageSha256": "cae1f9f9621d8ebb7f30a409b29e70375d31a0355f1305a2b07fa6044cb285a0",
  "metadata": "art/cg_v4/builtin/execution_c2_03_builtin_r1.json"
 },
 "execution_c2_04": {
  "image": "art/cg_v4/delivery/execution_c2_04_builtin_r1.webp",
  "imageSha256": "223a6701591592c4a53af56a88c964f565f9c6bfa540f8ad168488ca193f5ce6",
  "metadata": "art/cg_v4/builtin/execution_c2_04_builtin_r1.json"
 },
 "execution_c2_05": {
  "image": "art/cg_v4/delivery/execution_c2_05_builtin_r1.webp",
  "imageSha256": "a15cc25b8c6e7cfb66d50de38917f96e3b0f64712e0e8a6b81bd61fdc08ed06b",
  "metadata": "art/cg_v4/builtin/execution_c2_05_builtin_r1.json"
 },
 "execution_c3_01": {
  "image": "art/cg_v4/delivery/execution_c3_01_builtin_r2.webp",
  "imageSha256": "c31e3c19bdd46c53acc4c27095802b294bed552f68c7a8646ac2f489a24e961f",
  "metadata": "art/cg_v4/builtin/execution_c3_01_builtin_r2.json"
 },
 "execution_c3_02": {
  "image": "art/cg_v4/delivery/execution_c3_02_builtin_r2.webp",
  "imageSha256": "06fdc439583c96319baa26bec0b5c94eb258f20a6777b12791223af4bf45306f",
  "metadata": "art/cg_v4/builtin/execution_c3_02_builtin_r2.json"
 },
 "execution_c3_03": {
  "image": "art/cg_v4/delivery/execution_c3_03_builtin_r2.webp",
  "imageSha256": "51e9e4ce9f0b264ba3115442b94f36eed36ee81f32173cc0d05eaceb118a5dc2",
  "metadata": "art/cg_v4/builtin/execution_c3_03_builtin_r2.json"
 },
 "execution_c3_04": {
  "image": "art/cg_v4/delivery/execution_c3_04_builtin_r2.webp",
  "imageSha256": "23c8c62ed19953d3bd4c36008630e8457bf744a2e3c2831c87822cc7d3d43a13",
  "metadata": "art/cg_v4/builtin/execution_c3_04_builtin_r2.json"
 },
 "execution_c3_05": {
  "image": "art/cg_v4/delivery/execution_c3_05_builtin_r2.webp",
  "imageSha256": "e912f6d3001eb29c16fcb759ddf5c62899acc13223d54e9da8d29fd3129f4faf",
  "metadata": "art/cg_v4/builtin/execution_c3_05_builtin_r2.json"
 },
 "execution_c4_01": {
  "image": "art/cg_v4/delivery/execution_c4_01_builtin_r1.webp",
  "imageSha256": "dfc89bbf09d207fa21abb5757629660ce643766d2389a2204d6dcc0ebd01c68f",
  "metadata": "art/cg_v4/builtin/execution_c4_01_builtin_r1.json"
 },
 "execution_c4_02": {
  "image": "art/cg_v4/delivery/execution_c4_02_builtin_r2.webp",
  "imageSha256": "69c99af2de8cf3d0ba794aef2730bd40a3878b61a32a74695d9c2232025d4c7e",
  "metadata": "art/cg_v4/builtin/execution_c4_02_builtin_r2.json"
 },
 "execution_c4_03": {
  "image": "art/cg_v4/delivery/execution_c4_03_builtin_r1.webp",
  "imageSha256": "66a196fdb703740e30189fb1100f19a6872904c6d45f29f88b8eb746ac23c83b",
  "metadata": "art/cg_v4/builtin/execution_c4_03_builtin_r1.json"
 },
 "execution_c4_04": {
  "image": "art/cg_v4/delivery/execution_c4_04_builtin_r2.webp",
  "imageSha256": "689b1577bf155c152507ab20703f7e20878e3f34e9612ffac168a9231ad35799",
  "metadata": "art/cg_v4/builtin/execution_c4_04_builtin_r2.json"
 },
 "execution_c4_05": {
  "image": "art/cg_v4/delivery/execution_c4_05_builtin_r2.webp",
  "imageSha256": "398ae24dac8c2bc8dc88d7f2221d594a990fa6b37779eb40edb075c87560d9f4",
  "metadata": "art/cg_v4/builtin/execution_c4_05_builtin_r2.json"
 },
 "execution_c5_01": {
  "image": "art/cg_v4/delivery/execution_c5_01_builtin_r2.webp",
  "imageSha256": "b84b52eda17c981b28fe41b5889345eab48c6ac26b2a8677aa0a210c6e608836",
  "metadata": "art/cg_v4/builtin/execution_c5_01_builtin_r2.json"
 },
 "execution_c5_02": {
  "image": "art/cg_v4/delivery/execution_c5_02_builtin_r2.webp",
  "imageSha256": "1bd5305667d1c13cdeb4e6f8e66ac60de563b46d8e7c1d7f3a42dd1336d323c0",
  "metadata": "art/cg_v4/builtin/execution_c5_02_builtin_r2.json"
 },
 "execution_c5_03": {
  "image": "art/cg_v4/delivery/execution_c5_03_builtin_r2.webp",
  "imageSha256": "8be1da1403a23a8e63ee935309274bd0656dc511ab0a48e8a405db6300ddb14d",
  "metadata": "art/cg_v4/builtin/execution_c5_03_builtin_r2.json"
 },
 "execution_c5_04": {
  "image": "art/cg_v4/delivery/execution_c5_04_builtin_r2.webp",
  "imageSha256": "b9a2af600f36cc19d24b05a138de11336fa1189d7a8d957a3e7dfa5c8f80f331",
  "metadata": "art/cg_v4/builtin/execution_c5_04_builtin_r2.json"
 },
 "execution_c5_05": {
  "image": "art/cg_v4/delivery/execution_c5_05_builtin_r2.webp",
  "imageSha256": "f6b942f36581156af8777216f5232a1945a0d527badb5a8030321ba74ae21866",
  "metadata": "art/cg_v4/builtin/execution_c5_05_builtin_r2.json"
 },
 "incident_c1": {
  "image": "art\\cg_v4\\delivery\\incident_c1_forensic_r2.webp",
  "imageSha256": "21f698e0b9ff58826501367cb861edad39f462581ef3546f3fe4b2163de4d338",
  "metadata": "art/cg_v4/builtin/incident_c1_forensic_r2.json"
 },
 "incident_c2": {
  "image": "art\\cg_v4\\delivery\\incident_c2_forensic_r3.webp",
  "imageSha256": "35487aea60815af56576c4914f353786ab67f957857b53d67125494c0f50ae09",
  "metadata": "art/cg_v4/builtin/incident_c2_forensic_r3.json"
 },
 "incident_c3a": {
  "image": "art\\cg_v4\\delivery\\incident_c3a_forensic_r3.webp",
  "imageSha256": "6ea037df7a448a13399a725a90bd040a367434f5498163de84102680e6a1d786",
  "metadata": "art/cg_v4/builtin/incident_c3a_forensic_r3.json"
 },
 "incident_c3b": {
  "image": "art\\cg_v4\\delivery\\incident_c3b_forensic_r5.webp",
  "imageSha256": "d911664cd110d57fd377e2f7d1cc69a3c9cd68ce20cd6020f295d358d212442b",
  "metadata": "art/cg_v4/builtin/incident_c3b_forensic_r5.json"
 },
 "incident_c4": {
  "image": "art\\cg_v4\\delivery\\incident_c4_forensic_r3.webp",
  "imageSha256": "8d9824359f4730cf35006b7061173f43d2ed7b0927eb6fd6cd120dc9340e86dc",
  "metadata": "art/cg_v4/builtin/incident_c4_forensic_r3.json"
 },
 "incident_c5": {
  "image": "art\\cg_v4\\delivery\\incident_c5_forensic_r2.webp",
  "imageSha256": "e8768745434b79fec09b243f5dfe2ae2dfa79f401b23f4ceb9961cb791837397",
  "metadata": "art/cg_v4/builtin/incident_c5_forensic_r2.json"
 },
 "p01_notebook_boundary": {
  "image": "art/cg_v4/delivery/p01_notebook_boundary_builtin_r2.webp",
  "imageSha256": "d23743591a6b899c976b6b8eb64ccd04637fa612cf8d13ef03778e1027320ab6",
  "metadata": "art/cg_v4/builtin/p01_notebook_boundary_builtin_r2.json"
 },
 "p02_cup_refusal": {
  "image": "art/cg_v4/delivery/p02_cup_refusal_builtin_r1.webp",
  "imageSha256": "b0fc84d41e05b8c46d6f56409c7a86f415361b4d81532fbcca3f56bd8c1b016f",
  "metadata": "art/cg_v4/builtin/p02_cup_refusal_builtin_r1.json"
 },
 "p02_opened_seal": {
  "image": "art/cg_v4/delivery/p02_opened_seal_builtin_r1.webp",
  "imageSha256": "d60f69fc726e4d8b6f3a137c440b0170f6347557379f0a55b84d65cf34909f2f",
  "metadata": "art/cg_v4/builtin/p02_opened_seal_builtin_r1.json"
 },
 "p03_dust_boundary": {
  "image": "art/cg_v4/delivery/p03_dust_boundary_builtin_r1.webp",
  "imageSha256": "9244c5b5c18834f0ae013695e404ed689db2df83fd7aa05088b37c24b7d3d2c2",
  "metadata": "art/cg_v4/builtin/p03_dust_boundary_builtin_r1.json"
 },
 "p04_handle_observation": {
  "image": "art/cg_v4/delivery/p04_handle_observation_builtin_r1.webp",
  "imageSha256": "cfa9dbdc97c2442219e7459f6a08cd4d9e2bc9481db5fe8a7f87280afccdc4a1",
  "metadata": "art/cg_v4/builtin/p04_handle_observation_builtin_r1.json"
 },
 "p04_unanswered_phone": {
  "image": "art/cg_v4/delivery/p04_unanswered_phone_builtin_r1.webp",
  "imageSha256": "1181b95ed51d3376523b85374e5363b84a345fbb4a362600afcfbbdd25307225",
  "metadata": "art/cg_v4/builtin/p04_unanswered_phone_builtin_r1.json"
 },
 "p05_announcement": {
  "image": "art/cg_v4/delivery/p05_announcement_builtin_r2.webp",
  "imageSha256": "d56421cca7f71e90cf8b14c4b43961f7f763b0ea5e3cfdce7fcc68dd7c06a5b8",
  "metadata": "art/cg_v4/builtin/p05_announcement_builtin_r2.json"
 },
 "p08_pen_at_closed_door": {
  "image": "art/cg_v4/delivery/p08_pen_at_closed_door_builtin_r4.webp",
  "imageSha256": "7c33f0eb600a8ffea367ba9f007f400fc233ed3228653776b5b8aab2e1b9aed6",
  "metadata": "art/cg_v4/builtin/p08_pen_at_closed_door_builtin_r4.json"
 }
}

# Reviewed current personal-time source byte identities.
REVIEWED_FTE_HASHES={
 "20": "d3e9cd93db3bed04dd1468a510b69f6993574ad1d34f7d51bb8bd778b0f8172e",
 "21": "fa89b862743305b347524c590639e84b6f2115c79b79cffefa77dfe4c4fc2520",
 "22": "46a13d290296eed9340118dcec08f946d07c66a1bd7f1aa066bb4b4a3c2131e3",
 "23": "fc98b0b95f76e4e0d50f3ceae47cce95a15838631229cd454b63feb4d4cd3567",
 "24": "702147760f3aa070b24de3cd76b72368cc3f10298c1891eba8e5c40f8156a79a",
 "25": "518409a34d6808ca00083ce55ea3d5f4991854b9d222a3d21996459416ffeadc",
 "26": "8a990390790c81e6784b780224df54f8714926498108cc3988a54cecbda94a2c",
 "27": "04eedc56902b880dd07b6672988ad04431d79eb347039787349efc71a91efe55",
 "28": "89c1b37a3bab4aec7c24eb9589134b6868e325f05ff40f00c84865b001780c4e",
 "29": "a7f416fd8bdeb6c6e1a8dec3ff6571015d85e185cb3a1aec48957f3365b76dff",
 "30": "6753f518ec386374f30c706c6aa960650760add02fc1d68c8b6637e30a55b69c",
 "31": "22f150cfd14aa2b9a16b35361112c8d6fcd19f427c96d5ec8bb1086ad7219449",
 "32": "28d53ef7492be38a12577e61adea967b6360db139175031fd18fc9cf5e4d3845",
 "33": "5747a537cd64be29bf7a19b1ced0fcf36ab246dfe12c799f8b8e6243a75a9471",
 "34": "21cf898753978784ed8c5f4ce2a06131744bb5a717a761be1980707d997466c1",
 "35": "44db9fd52a95a299e81c02014d3674d8d3f14f5b62f14c01371b8c6ed3cedf88",
 "37": "e7be74a6de4bd1be8ab5d4a1c0dbd3fd038327b73f3c5c2f50183cc18434dc8f",
 "38": "0775ade00db44f25e099ace732f7fb759d79ffaf7fd421c31f4773cd29a6e64f",
 "36": "bfd60e4d46fc3d13cc38ca2b3374790098e78cfd20120d666103cf20e90c5fea",
 "39": "a6f1f5066085b03379514f902f2f299d494f64cfeab54ed110d1629798aa2a33",
 "40": "c7ae09b9922a2cca2e42ed19f2dc5d2a0d72180738545fefce16c85d6ecad424",
 "41": "866ef84d553df0de1701a950dc2f562ce4bb6665d5d6834f5ad157ba47e32deb",
 "42": "06e8807606eb7c05bb935357c25aec7a628ab9308ccf3ce4fbbde2382a8bd55d",
 "43": "f47828e4acc93bf6084a95641f6c74910d25254a312796e725c95de7d947ab4b",
 "44": "c9708a37da6edcf826e4b6857845411cd215938f4dbe5b20168df12a891b3a56",
 "45": "23f15ccccecd53867626941767668ef20326efe4081b27d91b4b58f79080f1c8",
 "46": "f0350e6d9fba1119d660f4c5e5630e79c0c2ec52bd2bb5b13655b10bcdc4225a",
 "47": "c0ed1c0bca684d7bb6fcf38fe7b74b13c23e479697153b4e354ceb81246f7b34",
 "48": "b1691be00edcb5400ec5917ae02f041bdc84dc499833fdf003187c625ea4cbe2",
 "49": "4c49a7b7b05f4e396d868e8360af5310edda516340a55f50ad436353c38b7503",
 "50": "309deb8efe6f5ffa32cc885749daf86b04f2fd8730b5791d53b22772cae18448",
 "51": "5ac6a0e3cb44d1f05fc77cd6849c7c300e4e0059e22a8a4ee4bc9a7378d5185c",
 "52": "abfd24bee3ebfd66a28658d698a0c72b4a93327afdab0c66d1e2b50b10d913bc",
 "53": "7c2dadbcceba142a0f9c1d082c4c26e2d968621785a6b44a5bb77fb4f9556ba3",
 "54": "8de7dc6ea0ae4dbc163e2fecd2a2f4cae88063108096a605cf957b508af190e3",
 "55": "a5e8cfa66241eab850693966244ecb4ef4bdd4451f47741de335fcc24cbc95fc",
 "56": "4e1127055a551df517ca76455cc4a47116629e8015528db272e0b9e9acd13ca0",
 "57": "95c4f036152fabb6cd186b807bcd10d137007f040ec8e6ad3549d6869a8fc0bd",
 "58": "1f9e0da316b6e8427a5f830bcbd5f4761b9e3c68b1c4e6f0aef1c644d4a6863a",
 "59": "ccfa86304bd020ee8e5dab936df0e09c5a2b05bfed110e94e0cfe7be33470331",
 "60": "e1764c8c4ca8437f64ad01de07a4535110b629594be9cdd461d66f695a80c591",
 "61": "0cc10b5a12a23801960ed582182ca640ed903a471431a75edc6881d098bdd4fd",
 "62": "55643c43fc6a542602af82846e6015908f855270fa6454b61cecc0578b54f8c1",
 "63": "a6e99629abdd73dbe27262e7a60c9cfba3f89e708d85f5c328d8404fa513619d",
 "64": "f7fab31714772acf10677e9719c16e12532d87b9c3631e0dca027362c949ae68",
 "87": "5d0732e18a1ad6b9948f74bec4d70a37009eb54d5a1fb94f79c42598a136dc4c",
 "88": "5a0be2c047f07953e7ef124a9edd26d70226f7f82ac8f89e49514a18bb18757c",
 "89": "f533426420bc480077be71d0925c053bfcfad932aa2cb4798de94818231794db",
 "90": "896a55642eb80a12c9587cf65175f908bdddd09a32ecf33b8e8e0d9af6e96206",
 "143": "90c3b98141376ece344c8c6719eb08d82dd8b1c6a302eada688dd2d4af5702b7",
 "144": "68bb731a446d77351c834ef55ec55a969086035e03019531be34c9dbd431acc2",
 "145": "1528665171ed516d9adc6b6a5be95330b5197647a669495bbc69d00ddc3da2d0",
 "146": "38bd1c033eab8850b229fbaa04d2c5cb6e54dbf69c6cad08c4c0603e6e164181",
 "147": "9b5839d04030c66e1507340b1bf94aef5226d43d4a7d9ce587ba4669a583d298",
 "148": "9dd5a0f79df1a9354fbcc9c3b142550ff1c492c8e19d74986529e4cd54b759b0",
 "149": "33adba675e641198eb237fd3a1ea4b721ee44a01d3827fc3718db56c40ebab78",
 "150": "1b2ac2e6275bbe0fad6c405fc98955b934033c9105c58f5ee4939c5b75abbac4",
 "151": "8d88be537bbaf2bfa05d203f3896be5f77b1a2c6e4c6c14ca75ab4add47870f5",
 "152": "784e834e084ebf0bfa655b9d059ea02d049c0a838f58a735e637b1b7cff89f82",
 "153": "660a7887f5cc86650a0d702504a1cf72a6ffb1eb0dce0e365e44654835b0af1a"
}
