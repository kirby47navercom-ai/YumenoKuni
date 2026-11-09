"""Apply reviewed music and physical sound cues to the runtime story."""
from collections import Counter

# Manuscript section identity, with file family where names can repeat.
SCENE_BEDS = {
    ("10", "P-06"): "bgm_killing_game",
    ("10", "P-06a"): "bgm_killing_game",
    ("10", "P-07"): "bgm_warm",
    ("11a", "1-01"): "bgm_morning_calm",
    ("11a3", "1-23"): "bgm_tense",
    ("11a3", "1-24"): "bgm_rappy_theme",
    ("11a3", "1-24b"): "bgm_rappy_after",
    ("12a", "2-04"): "bgm_warm",
    ("12a", "2-11"): "bgm_night",
    ("12a", "2-12"): "bgm_night",
    ("13a", "3-03"): "bgm_morning_calm",
    ("15a", "5-01"): "bgm_motive",
    ("15a", "5-08"): "bgm_motive",
    ("16a", "6-04"): "bgm_investigation_final",
    ("16a", "6-05"): "bgm_investigation_final",
    ("16a", "6-07a"): "bgm_sad",
    ("16d2", "R6-40"): "bgm_night",
}
# Exact actions, kept out of dialogue mentions and attempted actions.
CONTACTS = {
    ("11a", "1-01"): ("타이가는 대답 대신 문을 더 세게 두드린다.", "knock"),
    ("11a3", "1-24"): ("모니터의 접속 시험 화면 뒤에 래피가 나타난다.", "broadcast_on"),
    ("12a5", "2-50"): ("하루카가 문을 닫는다.", "door_closed"),
    ("12a", "2-C02"): ("유우는 그렇게 말했지만 주방 앞에서 먼저 말을 고르는 사람은 미오였다. 미오는 한 발 뒤로 물러선다. 유우가 직접 노크한다.", "knock"),
    ("14a7", "4-98"): ("하루카가 마지막으로 식당 문을 닫는다.", "door_closed"),
    ("14a4", "4-56"): ("복도에서 발소리가 멈춘다. 문 밖의 하루카가 한 번 노크한다.", "knock"),
}

def freetime_sections(graphs):
    return {
        section
        for name, graph in graphs.items() if name.startswith("freetime/")
        for section, bed in graph.get("presentation", {}).get("sectionBeds", {}).items()
        if section != ":" and bed.get("music") == "bgm_freetime"
    }

def direct_beds(graph, free):
    counts = Counter()
    for section, bed in graph.get("presentation", {}).get("sectionBeds", {}).items():
        file, _, location = section.partition(":")
        family = file.split("_", 1)[0]
        cue = SCENE_BEDS.get((family, location))
        if not cue and section in free:
            cue = "bgm_freetime"
        if not cue and graph.get("chapter") == "5" and bed.get("music") == "bgm_investigation":
            cue = "bgm_investigation_final"
        if cue and bed.get("music") != cue:
            bed["music"] = cue
            counts[cue] += 1
    return counts

def direct_node(node):
    if node.get("type") != "stage":
        return False
    source = node.get("source", {})
    family = source.get("file", "").split("_", 1)[0]
    location = source.get("location", "")
    contact = CONTACTS.get((family, location))
    direction = node.get("direction", node.get("text", "")).strip().lstrip("(")
    if not contact or not direction.startswith(contact[0]):
        return False
    presentation = node.setdefault("presentation", {})
    actions = presentation.setdefault("actions", [])
    if contact[1] in actions:
        return False
    actions.append(contact[1])
    return True

def direct_task(bundle):
    stage = bundle.get("stage", {})
    task = bundle.get("taskId", "")
    # Authored added debate sequence. Use the rising cue for its later exchanges.
    if stage.get("kind") != "nonstop" or not task.startswith(("T1-NS-A", "T2-NS-A", "T3-NS-A", "T4-NS-A", "T5-NS-A")):
        return False
    sequence = task.rsplit("A", 1)[-1]
    if not sequence.isdigit() or int(sequence) < 7:
        return False
    policy = stage.get("presentation", {}).get("music", {})
    if policy.get("cue") != "bgm_trial_nonstop":
        return False
    policy["cue"] = "bgm_trial_nonstop_b"
    if stage.get("music") == "bgm_trial_nonstop":
        stage["music"] = "bgm_trial_nonstop_b"
    return True

def apply(graphs, tasks):
    free = freetime_sections(graphs)
    for name, graph in graphs.items():
        if name.startswith("chapters/"):
            direct_beds(graph, free)
        for node in graph.get("nodes", {}).values():
            direct_node(node)
    for task in tasks.values():
        direct_task(task)
