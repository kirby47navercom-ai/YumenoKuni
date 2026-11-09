"""V4's authored sound and presentation contract.

No target execution, downloads, or audio extraction.  A stable manuscript block
selects the scene bed; actual state changes select feedback.  A character name,
emotion, or punctuation mark is never a sound trigger here.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import wave
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/presentation/v4.json"
ORIGINAL = ROOT / "audio/v4_original/manifest.json"
CATALOG = ROOT / "art/v4_production/completion/final_catalog.json"
DAILY = {"P": "bgm_daily_pro", "1": "bgm_daily_pastel", "2": "bgm_daily_summer",
         "3": "bgm_daily_night", "4": "bgm_daily_grey", "5": "bgm_daily_mono", "6": "bgm_core"}

# These are project editing choices, not seconds recovered from native ticks.
TRIAL_MUSIC = {"panic": "bgm_trial_panic", "scrum": "bgm_trial_scrum",
               "showdown": "bgm_trial_showdown", "mindmine": "bgm_trial_mindmine",
               "anagram": "bgm_trial_anagram", "reasoning": "bgm_trial_taxi",
               "reasoning_link": "bgm_trial_taxi", "taxi": "bgm_trial_taxi",
               "climax": "bgm_trial_climax"}
MOTION_FOR_ACTION = {
    "evidence_acquired": "fx_evidence_reveal_r1", "evidence_revised": "fx_evidence_reveal_r1",
    "body_reveal": "fx_discovery_border_r1", "refute": "fx_statement_fracture_r1",
    "agree": "fx_argument_impact_r1", "lie": "fx_argument_impact_r1",
    "shot_miss": "fx_miss_deflection_r1", "slash_hit": "fx_slash_trail_r1",
    "scrum_link": "fx_scrum_link_sparks_r1", "camera_whip": "fx_camera_whip_streak_r1",
    "rewind_confirmed": "fx_rewind_scan_r1", "scene_cover": "scene_ink_cover",
    "scene_uncover": "scene_ink_uncover", "concentration_on": "concentration_border_native_r2",
}
# (file prefix, manuscript section, actual direction prefix, action, music).
# Distinct first/second discovery in C3 and C4's living rescue are essential.
# Matching is bounded to a block in that source, not a free-text mention scan.
SCRIPT_ACTIONS = [
    ("10", "P-05", "분수 소리가 끊긴다. 녹음이 멎자", "broadcast_on", None),
    ("11a3", "1-33", "미오는 말을 끝내지 못한다. 목 부위에 남은 손상과", "body_reveal", "jingle_body_1>bgm_tense"),
    ("11a3", "1-33", "공원의 음악이 멎는다. 발표음이 울린다.", "body_announcement", None),
    ("12a7", "2-69", "아이는 무대에서 보던 밝은 색 천 위에", "body_reveal", "jingle_body_2>bgm_tense"),
    ("12a7", "2-71", "래피의 방송이 시작된다.", "body_announcement", None),
    ("13a12", "3-132", "발견 방송이 울린다. 리쿠의 몸 위에서", "body_reveal", "jingle_body_3>bgm_tense"),
    ("13b2", "I3-24", "나나가 고개를 숙인다. 쇼도 소라의 이름을 다시 부르지 않는다. 두 번째 몸의 사망이 확인된다. 그 뒤에 두 번째 발견 방송이", "body_reveal", "jingle_body_3>bgm_tense"),
    ("14a13", "4-195", "사망 확인. 발견 방송이 울린다.", "body_reveal", "jingle_body_4>bgm_tense"),
    ("15a11", "5-199", "코토의 눈과 입은 조금 열린 채 움직이지 않는다.", "body_reveal", "jingle_body_5>bgm_tense"),
    ("15a11", "5-199", "그 뒤에야 발견 방송이 울린다.", "body_announcement", None),
    ("16d2", "R6-29A", "지원 상태가 중단으로 바뀐다.래피의 입이", "support_stopped", "@silence"),
    ("11a", "1-01", "호텔 복도. 아침 방송은 음악만 나오고 말은 없다.", "knock", None),
    ("11a2", "1-09", "타이가가 문을 닫는다.", "door_closed", None),
    ("11a2", "1-15", "소라가 안에 남고 타이가가 문을 닫는다.", "door_closed", None),
    ("11a3", "1-24", "모니터가 꺼진다.", "broadcast_off", None),
    ("12a3", "2-26B-b", "미오는 자기 방 쪽으로 가려다가 하루카 문 앞에서 멈춘다. 노크한다.", "knock", None),
    ("12a3", "2-26B-b", "하루카가 잠깐 미오를 보고 방문을 닫는다.", "door_closed", None),
    ("14a13", "4-181", "안에서 낮은 물건 소리가 난다. 미오가 노크한다.", "knock", None),
]


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def original_cues():
    """Namespace the already-authored sounds, preserving both source and loop."""
    result = {}
    for a in json.loads(ORIGINAL.read_text(encoding="utf-8"))["assets"]:
        key = "v4_" + a["id"]
        result[key] = {"file": str(Path(a["ogg"]).relative_to("audio")).replace("\\", "/"),
                       "src": a["source"], "use": a["usage"], "len": a["duration_seconds"],
                       "original_manifest_id": a["id"], "loop_samples": a["loop"],
                       "sample_rate": a["sample_rate"], "wav_sha256": a["sha256"]}
    return result


def register_original_cues(path=None):
    """Idempotent merger. Existing supplied/imported mappings remain untouched."""
    path = Path(path) if path else ROOT / "audio/cues.json"
    cues = json.loads(path.read_text(encoding="utf-8"))
    cues.setdefault("sfx", {}).update(original_cues())
    # Prevent caller order from changing a source hash on every regeneration.
    path.write_text(json.dumps(cues, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return cues


def _sound(cue, gain=1.0):
    return {"cue": cue, "gain": gain, "bus": "ui" if cue.startswith(("ui_", "v4_ui_")) else "sfx"}


def action_contract():
    # 'when' is a state-transition condition: presentation must not decide hits,
    # acquisition, reveal timing, or script progression by itself.
    specs = {
        # v3se_* : V3 원작 효과음(tools/import_v3_se.py, 번호별 근거는 그 USE 표)
        "ui_focus": ("focus key changed", "v3se_005", .6),
        "ui_confirm": ("valid choice accepted", "v3se_001", .7),
        "ui_cancel": ("back action accepted", "v3se_004", .7),
        "ui_reject": ("invalid request rejected without advancement", "v3se_000", .7),
        "pad_open": ("pad changed from closed to open", "ui_pad", .65),
        "pad_close": ("pad changed from open to closed", "ui_pad_close", .65),
        "page_turn": ("page index changed", "v4_paper_turn", .6),
        "room_enter": ("room transition committed, not every loading tick", "sfx_room_move", .6),
        "door_locked": ("locked door activation rejected", "sfx_locked", .7),
        "knock": ("actual authored knock occurred, not a failed intention or recollection", "sfx_knock", .6),
        "door_open": ("door hinge animation actually began", "v4_door_hinge", .7),
        "door_closed": ("door leaf reached closed contact", "v4_door_wood_close", .75),
        "latch_open": ("latch release contact occurred", "v4_metal_latch_release", .8),
        "latch_closed": ("latch seats at closed pose", "v4_metal_latch_close", .8),
        "talk_start": ("talk target accepted", "sfx_talk_in", .65),
        "talk_end": ("conversation returned to exploration", "sfx_talk_out", .65),
        "inspect": ("inspect target accepted", "sfx_inspect", .65),
        "evidence_acquired": ("new evidence id committed", "v4_evidence_acquired", .8),
        "evidence_revised": ("existing evidence version changed", "v4_evidence_revised", .7),
        "body_reveal": ("authored dead-body reveal reached; never unresponsive alone", "sfx_shock", .8),
        "body_announcement": ("authored announcement reached after required confirmations", "sfx_body_chime", .8),
        "refute": ("validated refutation accepted", "v3se_309", .9),
        "agree": ("validated agreement accepted", "v3se_310", .85),
        "lie": ("validated perjury accepted after its cost, not charge alone", "v3se_308", .85),
        "shot_fire": ("projectile created after input permitted", "sfx_gunshot", .55),
        "shot_miss": ("projectile expires or validated wrong target", "v3se_307", .75),
        "trial_wrong": ("logical wrong-answer outcome committed", "v3se_316", .85),
        "selection_correct": ("correct person/evidence/answer/region judgment committed", "v3se_310", .8),
        "slash_hit": ("showdown slice intersects a valid cuttable segment", "v3se_375", .85),
        "scrum_link": ("correct opposing claim/evidence link committed", "v3se_361", .85),
        "climax_insert": ("panel placement passed actual slot validation", "v3se_310", .8),
        "climax_page": ("comic page changed", "v3se_007", .7),
        "camera_whip": ("directed camera transition began", "sfx_flash", .3),
        "rewind_confirmed": ("script confirms actual ability use, not allegation or discussion", "v4_memory_scan", .7),
        "camera_capture": ("story permits and actually takes a new photograph", "v4_camera_shutter", .75),
        "note_written": ("new note line committed", "sfx_note", .65),
        "coin_award": ("positive coin delta committed", "sfx_coin", .65),
        "bond_up": ("bond level actually crossed threshold", "sfx_bond_up", .65),
        "broadcast_on": ("actual monitor broadcast starts", "sfx_tv", .6),
        "broadcast_off": ("actual monitor switches off", "sfx_tv_off", .6),
        "elevator_start": ("elevator starts moving", "sfx_elevator", .7),
        "elevator_stop": ("elevator has stopped", "sfx_elevator_stop", .75),
        "scene_cover": ("transition owns input before scene replacement", "sfx_room_move", .45),
        "scene_uncover": ("new scene ready; uncover does not advance story", None, 0),
        "concentration_on": ("focus active; keep or use reduced-motion static border", None, 0),
        "concentration_off": ("focus released; remove border without success feedback", None, 0),
        "ending_choice": ("moral/support choice accepted; no right/wrong reward", "v4_ui_confirm", .45),
        "support_stopped": ("actual support state switched off; no execution/reward cue", None, 0),
    }
    out = {}
    for key, (when, cue, gain) in specs.items():
        out[key] = {"when": when, "sfx": [_sound(cue, gain)] if cue else [],
                    "music": {"operation": "keep"}, "coalesce_ms": 70 if key == "ui_focus" else 0,
                    "repeat": "state-edge", "cancel_on_mode_exit": True}
        if key in MOTION_FOR_ACTION:
            out[key]["sequence"] = MOTION_FOR_ACTION[key]
    out["body_reveal"]["music"] = {"operation": "stop", "fade_seconds": .12}
    out["support_stopped"]["music"] = {"operation": "stop", "fade_seconds": .4}
    out["ending_choice"]["no_success_reward"] = True
    return out


def build_contract():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    sequences = {}
    for x in catalog["effects"]:
        frames = [f.get("webp", f.get("file", "")) for f in x["frames"]]
        sequences[x["id"]] = {"frames": frames, "fps": x["fps"], "loop": bool(x["loop"]),
                               "seconds": len(frames) / x["fps"],
                               "reduced_motion": "static-opacity-.12" if x["id"].startswith("concentration") else "crossfade-.07-no-shake",
                               "input_owner": False, "stop_on_mode_exit": True,
                               "completion": "hide-and-return-to-caller"}
    return {
        "version": 1, "contentVersion": "v4", "actions": action_contract(), "sequences": sequences,
        "original_cues": original_cues(), "trial_music": TRIAL_MUSIC,
        "music_policy": {"same_cue": "keep-current-position", "silence": "stop-and-clear-pending-chain",
                         "intro_end": "switch-to-authored-loop-file-once", "modal_pad": "keep-playing",
                         "pause": "pause-is-distinct-from-stop; native support required",
                         "unavailable_cue": "report-missing; never silently mark as playing",
                         "restore": "restore-scene-bed-without-replaying-one-shot-reveal-or-jingle",
                         "loop_boundary": "supplied cue introLen/loop seconds retained; no claim of ACB sample identity"},
        "footsteps": {"trigger": "movement-phase contact; no sounds for look-only or idle",
                      "surface_source": "explicit space material only, not room-name guess",
                      "fallback_surface": "tile", "variants": {
                          # V3 40b000 : 수동 보행은 index0 = V3_SE_064(변형 3개). 다른 index 의 표면 구분은 근거가 없다
                          s: ["v3se_064", "v3se_064_1", "v3se_064_2"]
                          for s in ("tile", "wood", "metal", "cloth")},
                      "selection": "alternate per contact, no random reseed", "gain": .55, "running_gain": .7},
        "ambience": {"dry_fountain": [], "unknown_space": [],
                     "interior_air": {"cue": "v4_amb_room_air", "gain": .2},
                     "outside": {"cue": "v4_amb_outside_wind", "gain": .2},
                     "powered_machine": {"cue": "v4_amb_machine_hum", "gain": .24, "requires": "power_on"},
                     "flowing_water": {"cue": "v4_amb_water_flow", "gain": .25, "requires": "water_actually_flowing"}},
        "evidence": {"source": "docs/spec/18_V3_분석/07_소리.md",
                     "native_sound_same_cue": "ev_1c9a6b51e448d6bb21d39d15f33f2d8d1ac79b778c5ee3b5803fbc94b5d55d51",
                     "scope": "REA static control semantics plus original-project editing, not original runtime measurements"},
        "script_actions": [{"file_prefix": f, "section": sec, "direction_prefix": p, "action": a, "music": m}
                           for f, sec, p, a, m in SCRIPT_ACTIONS],
        "verification": {"runtime_integrated": False, "audition_approved": False}}


def _source_prefix(b):
    src = b.get("source", {})
    file = src.get("file", "") if isinstance(src, dict) else str(src)
    stem = Path(file).name.split("_", 1)[0]
    if not stem and str(b.get("id", "")).startswith("v4:"):
        stem = b["id"].split(":")[1]
    return stem


def _block_location(b):
    # Prefix matches only an actual manuscript block location, never prose.
    if isinstance(b.get("source"), dict) and b["source"].get("location"):
        return b["source"]["location"]
    ident = str(b.get("id", "")).split(":")[-1]
    return ident or str(b.get("title", "")).split(" ", 1)[0]


def scene_music(ch, b):
    """Choose a bed from authored chapter/section, not an actor emotion."""
    ch = str(ch)
    kind = b.get("t", b.get("kind", "scene"))
    stem, loc = _source_prefix(b), _block_location(b)
    if kind == "freetime":
        return "bgm_freetime"
    if kind == "investigate" or re.match(r"1[1-6]b", stem):
        return "bgm_investigation_final" if ch in {"5", "6"} else "bgm_investigation"
    if kind == "execution" or "처형 —" in b.get("title", ""):
        return "bgm_punishment_time"
    if ch == "P":
        return {"P-01": "bgm_pro_arrival", "P-02": "bgm_pro_intro", "P-03": "bgm_pro_intro",
                "P-04": "bgm_pro_intro", "P-05": "bgm_killing_game", "P-08": "bgm_night"}.get(loc, "bgm_daily_pro")
    if stem.startswith("16d"):
        # Successful contact is not an ecstatic ending; neither support choice
        # carries a correct-answer fanfare.  The original ending remains open.
        return "bgm_night" if stem == "16d1" else "bgm_sad"
    if re.match(r"1[1-5]d", stem):
        return "bgm_sad"
    # Supplemental manuscripts retain explicit T/Tn section IDs while their
    # numbered filenames differ from the parent chapter's 1nc files.
    if re.match(r"1[1-6]c", stem) or re.match(r"T(?:[1-6])?[-:]", loc) or kind == "trial":
        return "bgm_trial_main_" + ch
    # Same daily bed is intentionally kept before the first revealed corpse;
    # there is no automatic death omen based on a filename containing 발견.
    return DAILY.get(ch, "bgm_night")


def _set_action(e, action, *, spec=None, once=None):
    p = e.setdefault("presentation", {})
    actions = p.setdefault("actions", [])
    if action not in actions:
        actions.append(action)
    p["source"] = "v4-authored-state-edge"
    if once:
        p["once"] = once
    # Legacy eventSound can render the supplied first-class sounds today. Rich
    # contract consumers should ignore legacy sfx when presentation is consumed.
    if spec:
        e["music"] = spec
    if action in action_contract():
        values = action_contract()[action]["sfx"]
        if values:
            old = e.get("sfx", [])
            old = [old] if isinstance(old, str) else list(old)
            e["sfx"] = list(dict.fromkeys(old + [v["cue"] for v in values]))


def score_v4(flow):
    """Mutate a compiler's flow-compatible blocks without altering story text.

    Unresolved gates are kept unresolved. A mention of an old death, hypothetical
    rewind, disabled photo, or dialogue emotion creates no action.
    """
    ch = str(flow["chapter"])
    summary = {"blocks": 0, "authored_actions": 0, "gate_events_untouched": 0}
    for b in flow.get("beats", []):
        if b.get("t", b.get("kind", "scene")) in {"gate", "call"}:
            continue
        b.setdefault("bgm", scene_music(ch, b))
        b.setdefault("presentation", {"music": {"operation": "play", "cue": b["bgm"],
                                               "same_cue": "keep", "fade_seconds": .5},
                                      "source": "authored-manuscript-section"})
        summary["blocks"] += 1
        stem, loc = _source_prefix(b), _block_location(b)
        announcement_scheduled = False
        last_speaker = None
        for e in b.get("events", []):
            typ, text = e.get("type"), e.get("text", e.get("direction", ""))
            if typ in {"gate", "call", "task"}:
                summary["gate_events_untouched"] += 1
                continue
            before = copy.deepcopy(e.get("presentation"))
            if typ in {"card", "evidence"}:
                _set_action(e, "evidence_revised" if e.get("revision") else "evidence_acquired", once=e.get("id"))
            if typ == "stage":
                plain = text.strip().lstrip("(")
                event_stem = _source_prefix(e) or stem
                event_loc = e.get("source", {}).get("location", loc)
                for file_prefix, section, start, action, music in SCRIPT_ACTIONS:
                    if event_stem == file_prefix and event_loc == section and plain.startswith(start):
                        token = f"v4:{event_stem}:{event_loc}:{action}"
                        _set_action(e, action, spec=music, once=token)
                        if action == "body_announcement":
                            announcement_scheduled = True
                        if action == "body_reveal" and "방송" in start:
                            # A direction containing both actions has only one
                            # one-shot dispatch, rather than its following say
                            # firing another announcement from the same block.
                            announcement_scheduled = True
                        if music == "@silence":
                            e["presentation"]["music"] = {"operation": "stop", "fade_seconds": .4}
                        elif music:
                            e["presentation"]["music"] = {"operation": "play", "cue": music, "same_cue": "keep"}
                if stem == "16d1" and loc == "R6-14" and plain.startswith("사츠키가 문턱을 넘는다."):
                    # Successful passage is not graduation or a victory fanfare.
                    e.setdefault("presentation", {})["music"] = {"operation": "keep"}
            if typ == "say":
                speaker = e.get("speaker", "")
                if "방송" in speaker and text.startswith("시체가 발견되었습니다") and not announcement_scheduled:
                    _set_action(e, "body_announcement", once=f"v4:{stem}:{loc}:body_announcement")
                    announcement_scheduled = True
                p = e.setdefault("presentation", {})
                # A directed focus request is silent. No sound per new speaker
                # and no random pose changes; actual authored pose is retained.
                if not e.get("mono") and speaker and speaker != last_speaker:
                    p.setdefault("camera", {"operation": "focus-speaker", "speaker": speaker,
                                             "transition": "cut" if last_speaker is None else "directed-move",
                                             "sound": False})
                if e.get("pose"):
                    p.setdefault("actor", {"speaker": speaker, "pose": e["pose"], "repeat_same_pose": False})
                if not e.get("mono"):
                    last_speaker = speaker
            if e.get("presentation") != before:
                summary["authored_actions"] += 1
        # Reading/returning to a scene never replays its one-shot action.
        b["presentation"]["restore"] = "bed-only-no-one-shot"
    return summary


def score_trials_v4(trials, chapter):
    """Attach per-mode entry beds, preserving every actual puzzle outcome."""
    ch = str(chapter)
    stages = trials.get("stages", trials.get("steps", []))
    voted = False
    for s in stages:
        kind = s.get("kind", s.get("type", "talk"))
        if kind == "vote":
            cue, voted = "bgm_trial_main_1", True
        elif kind == "nonstop":
            cue = "bgm_trial_nonstop_final" if ch == "6" else (
                "bgm_trial_nonstop_lie" if s.get("requiredLie") else "bgm_trial_nonstop_b" if s.get("escalation") == "high" else "bgm_trial_nonstop")
        elif kind == "armament":
            cue = "bgm_trial_armament_" + ch
        else:
            cue = TRIAL_MUSIC.get(kind, "bgm_trial_truth" if voted else "bgm_trial_main_" + ch)
        s.setdefault("music", cue)
        s.setdefault("presentation", {"music": {"operation": "play", "cue": cue, "same_cue": "keep"},
                                       "restore": "bed-only-no-entry-jingle", "cancel_pending_on_exit": True})
    return len(stages)


def score_graph_v4(graph):
    """Compile node presentation without attaching a fresh BGM to every line.

    The index may contain nested duplicate blocks. A graph entry is an event,
    so each event is scored once, and its music operation is only the explicit
    authored operation. Scene-bed metadata is returned separately for the
    caller to use when it genuinely enters another section, not on every say.
    """
    ch = str(graph["chapter"])
    beds, actions = {}, 0
    for e in graph.get("nodes", {}).values():
        if e.get("type") not in {"say", "stage", "card", "evidence", "menu"}:
            continue
        src = e.get("source", {})
        section = f"{src.get('file', '')}:{src.get('location', '')}"
        b = {"id": e["id"], "source": src, "events": [e], "title": src.get("heading", ""),
             "kind": graph.get("kind", "scene")}
        score_v4({"chapter": ch, "beats": [b]})
        beds.setdefault(section, {"music": b["bgm"], "restore": "bed-only-no-one-shot"})
        actions += len(e.get("presentation", {}).get("actions", []))
        if e.get("presentation", {}).get("camera"):
            e["presentation"]["camera"]["transition"] = "keep-if-same-otherwise-directed-move"
    graph["presentation"] = {"entryMusic": "bgm_freetime" if graph.get("kind") == "freetime" else DAILY.get(ch, "bgm_night"), "sectionBeds": beds,
                              "policy": "section bed is a scene-enter request, never replay per dialogue node",
                              "save": "persist actual current music and silence; do not infer from next speaker"}
    return {"nodes": len(graph.get("nodes", {})), "sections": len(beds), "actions": actions}


def score_tasks_v4(task_index):
    """Input/result edges own feedback even when their spoken arrays are empty."""
    tasks = task_index.get("tasks", task_index)
    for task in tasks.values():
        ch = str(task["chapter"])
        score_trials_v4({"stages": [task]}, ch)
        for slot in ("intro", "wrong", "success", "lines"):
            if isinstance(task.get(slot), list):
                score_v4({"chapter": ch, "beats": [{"id": task["id"], "source": task.get("source", {}),
                                                    "kind": "trial", "events": task[slot]}]})
        correct = task.get("judgment", "selection_correct")
        if correct not in {"refute", "agree", "lie"}:
            correct = "selection_correct"
        task["presentation"]["outcomes"] = {
            "wrong": {"action": "trial_wrong", "music": "keep", "next": "existing-retry-route"},
            "success": {"action": correct, "music": "keep", "next": "existing-success-route"},
            "return": {"music": "restore-callsite-bed", "one_shot_entry": False,
                       "stop_effects": True, "route": "existing-exact-return"}}
    return len(tasks)


@dataclass
class PresentationState:
    """Renderer-independent reference for native scheduling acceptance tests.

    This intentionally does not play audio or claim to reproduce engine mixing.
    The real native consumer must pass the same interrupted-chain/save cases.
    """
    cue: str = ""
    pending: str = ""
    remaining: float = 0.0
    one_shots: set = field(default_factory=set)
    event_ids: set = field(default_factory=set)
    sequence: str = ""
    output: list = field(default_factory=list)

    def music(self, spec, lengths=None):
        lengths = lengths or {}
        if spec == "@silence":
            self.cue, self.pending, self.remaining = "", "", 0
            self.output.append(("stop",))
            return
        if not spec or spec == self.cue:
            return
        self.pending, self.remaining = "", 0
        first, sep, after = spec.partition(">")
        self.cue = first
        if sep:
            self.pending, self.remaining = after, lengths.get(first, 1.0)
        self.output.append(("music", first))

    def tick(self, delta):
        if self.remaining <= 0:
            return
        self.remaining = max(0, self.remaining - delta)
        if self.remaining == 0 and self.pending:
            next_cue = self.pending
            self.pending = ""
            self.music(next_cue)

    def event(self, e, contract):
        p = e.get("presentation", {})
        ident = e.get("id", "")
        token = p.get("once", "")
        if ident in self.event_ids or token and token in self.one_shots:
            return
        if ident:
            self.event_ids.add(ident)
        if token:
            self.one_shots.add(token)
        spec = e.get("music", "")
        if spec:
            self.music(spec)
        # Contract actions own sound. Do not also play e.sfx compatibility data.
        for name in p.get("actions", []):
            a = contract["actions"][name]
            for s in a["sfx"]:
                self.output.append(("sfx", s["cue"]))
            if a.get("sequence"):
                self.sequence = a["sequence"]
                self.output.append(("sequence", self.sequence))
        if p.get("music", {}).get("operation") == "stop" and not spec:
            self.music("@silence")

    def mode_exit(self):
        self.sequence = ""
        self.event_ids.clear()  # new events can play; persistent reveals cannot

    def save(self):
        return {"cue": self.cue, "pending": self.pending, "remaining": self.remaining,
                "one_shots": sorted(self.one_shots)}

    def restore(self, data):
        # Seek is not available in the current native music wrapper. Restore
        # the intended bed after a one-shot, rather than replaying that one-shot
        # with an old remaining timer and cutting it off at a false boundary.
        self.cue = data["pending"] or ("" if data["cue"].startswith("jingle_") else data["cue"])
        self.pending, self.remaining = "", 0
        self.one_shots = set(data["one_shots"])
        self.event_ids.clear()
        self.sequence = ""  # completed or suspended effects are never replayed
        self.output.clear()


def validate_contract(contract, cues):
    errors, observations = [], {"cue_files": 0, "sequence_frames": 0, "wav_samples": 0}
    all_cues = {k: v for g in ("bgm", "jingle", "sfx") for k, v in cues.get(g, {}).items()}
    for k, c in all_cues.items():
        if not c.get("file"):
            errors.append("cue has no file: " + k)
            continue
        p = ROOT / "audio" / c["file"]
        if not p.is_file():
            errors.append("missing cue: " + k)
        else:
            observations["cue_files"] += 1
        if c.get("intro"):
            if not (ROOT / "audio" / c["intro"]).is_file() or c.get("introLen", 0) <= 0:
                errors.append("invalid intro: " + k)
        if c.get("loop"):
            if c["loop"][0] < 0 or c["loop"][1] <= c["loop"][0]:
                errors.append("invalid supplied loop bounds: " + k)
    requested = set(TRIAL_MUSIC.values()) | set(DAILY.values())
    for a in contract["actions"].values():
        requested.update(x["cue"] for x in a["sfx"])
        if a.get("sequence") not in {None, *contract["sequences"]}:
            errors.append("unknown action sequence")
    for c in requested:
        if c not in all_cues:
            errors.append("unknown requested cue: " + c)
    for ident, seq in contract["sequences"].items():
        if seq["fps"] <= 0 or not seq["frames"]:
            errors.append("invalid frame timing: " + ident)
        if seq["completion"] != "hide-and-return-to-caller" or not seq["stop_on_mode_exit"]:
            errors.append("missing cleanup: " + ident)
        for f in seq["frames"]:
            if not (ROOT / f).is_file():
                errors.append("missing sequence frame: " + f)
            observations["sequence_frames"] += 1
    for a in json.loads(ORIGINAL.read_text(encoding="utf-8"))["assets"]:
        p = ROOT / a["file"]
        with wave.open(str(p), "rb") as w:
            if w.getnframes() != a["samples"] or w.getframerate() != a["sample_rate"]:
                errors.append("WAV source sample contract differs: " + a["id"])
            observations["wav_samples"] += w.getnframes()
        if hashlib.sha256(p.read_bytes()).hexdigest() != a["sha256"]:
            errors.append("WAV source hash differs: " + a["id"])
        if (ROOT / a["ogg"]).read_bytes()[:4] != b"OggS":
            errors.append("OGG carrier signature differs: " + a["id"])
    return {"status": "pass" if not errors else "fail", "errors": errors, "observations": observations,
            "runtime_played": False, "audition_approved": False,
            "limits": ["File/sample/route checks do not prove audible mix or visual quality.",
                       "Native consumer hooks are required; contract generation is not runtime completion."]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--register-cues", action="store_true")
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    cues = register_original_cues() if args.register_cues else json.loads((ROOT / "audio/cues.json").read_text(encoding="utf-8"))
    contract = build_contract()
    report = validate_contract(contract, cues)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["contract_sha256"] = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_name("v4_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
