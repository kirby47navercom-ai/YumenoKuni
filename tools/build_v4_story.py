#!/usr/bin/env python3
"""Compile V4 manuscripts without silently joining mutually exclusive branches.

This is a separate, source-addressed content pipeline. It never imports the old
case data. Source paragraphs and editorial instructions are indexed separately;
only explicitly routed nodes are executable. ``--strict`` rejects an incomplete
campaign rather than publishing a shortened/flattened version as the full game.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from v4_editorial_ids import fingerprint as editorial_fingerprint
from v4_editorial_ids import original_voice_line

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs/design/rewrite_v4"
OUT = ROOT / "data/v4_story"
SPEAKERS = {"미오": "mio", "레이": "rei", "소라": "sora", "켄": "ken", "나나": "nana", "리쿠": "riku", "아카리": "akari", "유우": "yuu", "코토": "koto", "사츠키": "satsuki", "타이가": "taiga", "린": "rin", "쇼": "sho", "아이": "ai", "하루카": "haruka", "카에데": "kaede", "래피": "lappy"}
KIND = {"NS": "nonstop", "PN": "panic", "RS": "showdown", "PERSON": "person", "CULPRIT": "person", "EVIDENCE": "bullet", "ANSWER": "choice", "SPOT": "spot", "MM": "mindmine", "FA": "anagram", "RL": "reasoning"}
SAY = re.compile(r"^\[([^\]]+)\]\s*(.+)$")
HEADING = re.compile(r"^(#{1,6})\s+(.+)$")
LINK = re.compile(r"\[([^\]]*)\]\(([^)]+\.md)(?:#([^)]+))?\)")
LOCATION = re.compile(r"^(?:선택\s+)?((?:[PTIRF]\d*[-:]|\d[-:])[A-Za-z0-9가-힣_-]+)")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean(text: str) -> str:
    """Remove inline emphasis, never remove semantic target delimiters."""
    return text.replace("**", "").strip().strip('"“”')


def speaker_line(text: str) -> dict[str, Any] | None:
    m = SAY.fullmatch(text.strip())
    if not m:
        return None
    raw = m[1]
    # Square-bracket author tags and UI instructions are not actors.
    name = re.split(r"[·(（/]", raw, maxsplit=1)[0].strip()
    if name not in SPEAKERS:
        return None
    return {"type": "say", "speaker": name, "actor": SPEAKERS[name], "text": clean(m[2]), "mono": "속말" in raw or "독백" in raw, "delivery": raw}


class Source:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.prefix = path.name.split("_", 1)[0]
        self.text = path.read_text(encoding="utf-8-sig")
        self.lines = self.text.splitlines()
        self.hash = sha(self.text)
        self.headings: list[dict[str, Any]] = []
        for i, line in enumerate(self.lines, 1):
            m = HEADING.match(line)
            if m:
                token = LOCATION.match(m[2])
                self.headings.append({"line": i, "depth": len(m[1]), "title": m[2], "location": token[1] if token else "h-" + sha(m[2])[:10]})

    def ref(self, line: int) -> dict[str, Any]:
        head = next((h for h in reversed(self.headings) if h["line"] <= line), None)
        return {"file": self.name, "line": line, "fileSha256": self.hash, "heading": head["title"] if head else "", "location": head["location"] if head else "root"}

    def at(self, anchor: str) -> int:
        hits = [i for i, line in enumerate(self.lines, 1) if line == anchor]
        if not hits:
            hits = [i for i,line in enumerate(self.lines,1) if original_voice_line(self.name,i,line)==anchor]
        if len(hits) != 1:
            raise ValueError(f"{self.name}: anchor must be unique ({len(hits)}): {anchor}")
        return hits[0]

    def section(self, token: str) -> tuple[int, int]:
        hits = [h for h in self.headings if h["location"] == token]
        if len(hits) != 1:
            raise ValueError(f"{self.name}: section {token} is not unique")
        h = hits[0]
        end = next((q["line"] - 1 for q in self.headings if q["line"] > h["line"] and q["depth"] <= h["depth"]), len(self.lines))
        return h["line"], end

    def paragraphs(self, start: int = 1, end: int | None = None) -> list[dict[str, Any]]:
        """Keep prose as metadata. Only exact recognized actors become say nodes."""
        events = []
        duplicate = Counter()
        # Count duplicate occurrences in the complete source, even when callers
        # compile only a subrange. Splitting a range must not rename its events.
        for n in range(1, len(self.lines) + 1):
            line = self.lines[n - 1].strip()
            if not line or HEADING.match(line):
                continue
            event = speaker_line(line)
            if event is None:
                if line.startswith(("(", "（")) and line.endswith((")", "）")):
                    event = {"type": "stage", "direction": line[1:-1]}
                else:
                    event = {"type": "editorial", "direction": line}
            ref = self.ref(n)
            fingerprint = editorial_fingerprint(self.prefix, ref['location'], line, source_file=self.name, source_line=n)
            duplicate[(ref["location"], fingerprint)] += 1
            event.update(id=f"v4:{self.prefix}:{ref['location']}:e:{fingerprint}:{duplicate[(ref['location'], fingerprint)]}", source=ref)
            if start <= n <= (end if end is not None else len(self.lines)):
                events.append(event)
        return events


class Graph:
    """Explicit control flow; no implicit fallthrough between branches."""
    def __init__(self, chapter: str):
        self.chapter = chapter
        self.nodes: dict[str, dict[str, Any]] = {}
        self.taskDefinitions: dict[str, dict[str, Any]] = {}

    def add(self, node_id: str, node: dict[str, Any]) -> str:
        if node_id in self.nodes:
            raise ValueError(f"duplicate graph ID {node_id}")
        # These source headings expose an editorial choice ID. Keep that
        # anchor stable for saves, but give the player the actual question.
        if node.get('type') == 'menu':
            authored_questions = {
                '### 선택 W1-C02': '전화 연습에 답할까',
                '### 선택 W2-C03': '아프지 않다는 말 앞에서',
                '### 선택 F-AK02-A': '어떤 맛으로 만들까',
                '### 선택 F-NA02-A': '고리를 던질 자리',
                '### 선택 F-NA02-B': '마지막 고리와 남은 시간',
                '### 선택 F-HA02-A': '거울을 드는 방식',
                '### 선택 F-HA02-B': '오늘의 모습을 남길까',
                '선택 T5-C02': '지금 고를 표와 책임',
                '선택 T5-C03 — 지금 끊어야 할 연결': '지금 끊어야 할 연결',
                '선택 T5-C01': '엇갈린 두 기록을 묻는 순서',
                '선택 5-C05': '없었으면 하는 사람',
                '선택 5-C04': '자료 앞에서 먼저 할 일',
                '선택 5-C06 — 아직 잡지 않은 손': '아직 잡지 않은 손',
                '선택 5-C07 — 목록 앞에서 먼저 할 대답': '목록 앞에서 먼저 할 대답',
                '선택 5-C03': '기다릴 자료와 남을 사람',
                '선택 5-C02': '남은 잔과 앉을 자리',
                '선택 5-C01': '의심을 들은 사람에게',
                '선택 T6-C01': '밖으로 남길 자료',
                '선택 I6-C01': '먼저 맞출 연결',
                '선택 6-C02': '지금 부를 이름',
                '선택 6-C01': '이 방에서 먼저 확인할 것',
            }
            if node.get('q') in authored_questions:
                node = {**node, 'q': authored_questions[node['q']]}
        self.nodes[node_id] = {"id": node_id, **node}
        return node_id

    def sequence(self, source: Source, start: int, end: int, next_id: str) -> str:
        events = source.paragraphs(start, end)
        # Author notes remain source metadata, not player-visible events.
        executable = []
        for event in events:
            if event["type"] in ("say", "stage"):
                executable.append(event)
            elif event["type"] == "editorial":
                marker = re.match(r"^>\s*\*\*필수 입력 (T\d+-[A-Z]+-A\d+):", event["direction"])
                if marker:
                    if marker[1] not in self.taskDefinitions:
                        raise ValueError(f"Missing explicit task definition {marker[1]}")
                    executable.append({"id": "v4:input:" + marker[1], "type": "task", "taskId": marker[1], "source": event["source"], "runtimeReady": self.taskDefinitions[marker[1]]["runtimeReady"]})
        target = next_id
        for event in reversed(executable):
            node = {**event, "next": target}
            if event["type"] == "task":
                node["success"] = target
            target = self.add(event["id"], node)
        return target

    def export(self, entry: str, **extra: Any) -> dict[str, Any]:
        return {"schemaVersion": 1, "contentVersion": "v4", "chapter": self.chapter, "entry": entry, "nodes": self.nodes, **extra}


def compile_choice_scene(source: Source) -> dict[str, Any]:
    """Compile a reviewed, simple first-meeting manuscript with real choices.

    Intentionally called only for an explicit allowlist below. Later meetings
    contain earlier-choice callbacks, exit routes and physical-item variants;
    those are not equivalent to these simple converging menus.
    """
    g = Graph("freetime")
    end = g.add(f"v4:{source.prefix}:return", {"type": "return"})
    footer = next((h["line"] - 1 for h in source.headings if any(w in h["title"] for w in ("후속 연결", "후속 상태", "후속 상태", "다음 만남에 남는 상태"))), len(source.lines))

    def route(start: int, stop: int, next_id: str) -> str:
        choices = [h for h in source.headings if start <= h["line"] <= stop and h["title"].startswith("선택 ")]
        if not choices:
            return g.sequence(source, start, stop, next_id)
        first = choices[0]
        # A same/shallower heading ends this choice section. An explicit bold
        # merge can end it earlier (common in third-level F-XX menus).
        menu_end = next((h["line"] - 1 for h in source.headings if first["line"] < h["line"] <= stop and h["depth"] <= first["depth"]), stop)
        merge = next((i for i in range(first["line"] + 1, menu_end + 1) if source.lines[i - 1].startswith("**합류")), None)
        if merge:
            menu_end = merge - 1
        after = route(menu_end + 1, stop, next_id) if menu_end < stop else next_id
        option_rows = []
        for i in range(first["line"] + 1, menu_end + 1):
            raw = source.lines[i - 1]
            match = re.match(r"^(?:\*\*|#{3,6}\s+)([ABC][123]?)\.\s*(.+?)(?:\*\*)?$", raw)
            if match:
                option_rows.append((i, match[1], clean(match[2])))
        if len(option_rows) != 3:
            raise ValueError(f"{source.name}: only explicitly three-way simple menu supported at {first['title']}, found {len(option_rows)}")
        label = first["title"].removeprefix("선택 ")
        q_id = re.split(r"\s", label, maxsplit=1)[0]
        q = label.split("—", 1)[-1].strip() if "—" in label else q_id
        menu_id = f"v4:{source.prefix}:{q_id}:menu"
        options = []
        for index, (line, letter, title) in enumerate(option_rows):
            last = option_rows[index + 1][0] - 1 if index + 1 < len(option_rows) else menu_end
            options.append({"id": letter, "label": title, "to": route(line + 1, last, after), "set": {q_id: letter}})
        g.add(menu_id, {"type": "menu", "q": q, "options": options, "source": source.ref(first["line"])})
        return g.sequence(source, start, first["line"] - 1, menu_id)

    entry = route(1, footer, end)
    if source.prefix == "29":
        # This is an actual line embedded in an authored conditional stage,
        # not dialogue shared by all three first-game choices. The delayed88
        # clone retains this branch without restoring its replaced Ken face.
        conditional=next(n for n in g.nodes.values() if n.get('source',{}).get('line')==293)
        after=conditional['next']
        actual_line="규칙을 바꾸면 한 판은 더 해 보고 싶어"
        if actual_line not in source.lines[292] or 'A3에서 그만두겠다고 했다면' not in source.lines[292]:
            raise ValueError('Re-read Nana01 conditional restart before compiling changed source.')
        permission=g.add('v4:29:actual-restart-permission',{'type':'stage','direction':'나나가 돌을 다시 꺼내도 되는지 확인한 뒤 시작한다.','source':source.ref(293),'next':after})
        restart=g.add('v4:29:actual-A3-restart-line',{'type':'say','speaker':'미오','actor':'mio','text':actual_line,'mono':False,'source':source.ref(293),'next':permission})
        missing=g.add('v4:29:missing-actual-first-game-ending',{'type':'gate','reason':'Actual earlier F-NA01-A choice absent; do not invent a prior refusal.'})
        g.nodes[conditional['id']]={'id':conditional['id'],'type':'branch','cases':[{'flag':'F-NA01-A','equals':value,'to':restart if value=='A3' else after} for value in ('A1','A2','A3')],'default':missing,'source':source.ref(293)}
    return g.export(entry, kind="freetime", routingStatus="authored_simple_convergence", sourceFile=source.name, completionFlag=f"fte:{source.prefix}:complete", eligibility="Caller must enforce the exact manuscript day/time and prior-meeting requirements. No caller may auto-play every library file.")


def compile_chapter_one_first_day(sources: dict[str, Source], freetime_graphs: dict[str, Any], tasks: dict[str, Any]) -> dict[str, Any]:
    """Case-one authored route, including exact inserts and delayed callbacks.

    The historical function name is retained for importer compatibility.
    Mandatory source flow reaches chapter end; unfinished pictures/optional
    meetings remain explicit input gates, so campaignReady remains false.
    """
    g = Graph("1")
    docs = {s.prefix: s for s in sources.values()}
    main = docs["11a"]

    def line(prefix: str, anchor: str) -> int:
        return docs[prefix].at(anchor)

    def span(prefix: str, first: str | int, last: str | int | None, target: str) -> str:
        source = docs[prefix]
        start = source.at(first) if isinstance(first, str) else first
        stop = source.at(last) - 1 if isinstance(last, str) else last if last is not None else len(source.lines)
        return g.sequence(source, start, stop, target)

    def select(prefix: str, heading: str, option_anchors: list[str], end: str | int, target: str, flag: str) -> str:
        source = docs[prefix]
        option_lines = [source.at(a) for a in option_anchors]
        finish = source.at(end) if isinstance(end, str) else end
        options = []
        for i, (anchor, start) in enumerate(zip(option_anchors, option_lines)):
            raw = clean(re.sub(r"^#+\s*", "", anchor))
            label = re.sub(r"^[ABC][123]?[.\s—-]+", "", raw).strip()
            options.append({"id": "ABC"[i], "label": label, "to": span(prefix, start + 1, option_lines[i + 1] - 1 if i + 1 < len(option_lines) else finish - 1, target), "set": {flag: "ABC"[i]}})
        return g.add(f"v4:{prefix}:{flag}:menu", {"type": "menu", "q": heading.split("—")[-1].strip(), "source": source.ref(source.at(heading)), "options": options})

    def first_window(target: str) -> str:
        # Keep the complete authored candidate list. Uncompiled meetings stop
        # explicitly; they are not swapped for another actor or counted done.
        eligible = [("20", "린"), ("24", "소라"), ("25", "아이"), ("26", "유우"), ("27", "레이"), ("28", "켄"), ("29", "나나"), ("30", "리쿠"), ("31", "아카리"), ("32", "사츠키"), ("33", "타이가"), ("34", "하루카")]
        options = []
        for prefix, actor in eligible:
            if prefix in freetime_graphs:
                fte = freetime_graphs[prefix]
                for ident, node in fte["nodes"].items():
                    if ident not in g.nodes:
                        g.add(ident, node)
                entry = g.add(f"v4:1:F1-A:call:{prefix}", {"type": "call", "target": fte["entry"], "returnTo": target, "onReturnSet": {fte["completionFlag"]: True, "window:F1-A:completed": True}, "source": main.ref(line("11a", "## 1-05 오후의 팀") - 2)})
            else:
                entry = g.add(f"v4:1:F1-A:unrouted:{prefix}", {"type": "gate", "reason": f"{actor} first meeting has additional nested/conditional routing not encoded yet. Never auto-complete or substitute another meeting.", "sourceFile": next(s.name for s in sources.values() if s.prefix == prefix)})
            options.append({"id": prefix, "label": actor, "to": entry})
        options.append({"id": "REST", "label": "혼자 쉰다", "to": target, "set": {"window:F1-A:completed": True}})
        return g.add("v4:1:F1-A", {"type": "menu", "q": "개인시간 — 누구와 시간을 보낼까?", "selectionRole": "freetime", "maxSelections": 1, "options": options})

    next_day = g.add("v4:1:11a2:pending", {"type": "gate", "reason": "The first day and its actual insertions are routed. Day two, later investigation/trial, and remaining meetings still require authored routes.", "nextSource": docs["11a2"].name})
    night = span("86", "## 1-08a 잠든 척하면", None, next_day)
    evening_end = span("11a", "### 1-07k 부탁한 잠", None, night)
    later_120 = span("120", "## 1-07j 잘 자라는 말 앞에서", None, evening_end)
    menu_120 = select("120", "## 선택 1-C08 — 끝을 누가 정할까", ["### A. 유우가 끝났다고 할 때까지 들어 주겠다고 한다", "### B. 듣되 중간에 그만하겠다고 말할 수도 있다고 한다", "### C. 함께 앉아 있는 것을 앞으로의 약속으로 만들지 않겠다고 한다"], "**합류.모든 경로 현재 잠깐 더 앉되,A만 미오의 명시적인 무기한 청취 약속/B는 중단 가능 의사/C는 장래 약속 없음이다.하루카의 부른 이유는 현재 사실로 정정됐고,유우가 미오를 직접 지명했다는 거짓 사실은 남기지 않는다.**", later_120, "1-C08")
    entry_120 = span("120", "## 1-07g 다시 내려가자는 사람", "## 선택 1-C08 — 끝을 누가 정할까", menu_120)
    after_dinner_choice = span("65", "## 1-07f 흩어진 뒤에 정리되는 말", "## 유지할 상태", entry_120)
    dinner_choice = select("65", "## 선택 1-C05 — 더 있고 싶은 자리", ["### A. 코토의 정리를 돕는다", "### B. 목록을 보는 카에데에게 간다", "### C. 조용해진 유우에게 간다"], "## 1-07f 흩어진 뒤에 정리되는 말", after_dinner_choice, "1-C05")
    dinner_common = span("65", "## 1-07b 식탁으로 부른 이유", "## 선택 1-C05 — 더 있고 싶은 자리", dinner_choice)
    # Only a real earlier AI01 selection creates this callback. Missing flag
    # skips it; it does not select A1 and grant an event the player never saw.
    ai_a = line("65", "**25-A1 — 당근을 빼 달라고 했다.**")
    ai_b = line("65", "**25-A2 — 섞기 전의 몫을 부탁했다.**")
    ai_c = line("65", "**25-A3 — 작은 조각은 먹겠다고 했다.**")
    ai_merge = span("65", "**합류.**", "## 1-07b 식탁으로 부른 이유", dinner_common)
    ai_branch = g.add("v4:65:AI01:callback", {"type": "branch", "cases": [
        {"flag": "F-AI01-A", "equals": "A1", "to": span("65", ai_a + 1, ai_b - 1, ai_merge)},
        {"flag": "F-AI01-A", "equals": "A2", "to": span("65", ai_b + 1, ai_c - 1, ai_merge)},
        {"flag": "F-AI01-A", "equals": "A3", "to": span("65", ai_c + 1, line("65", "**합류.**") - 1, ai_merge)},
    ], "default": dinner_common})
    dinner_entry = span("65", "## 1-07a 자리가 열여섯 개", "### 1-07a-AI01 첫 부탁 뒤의 저녁", ai_branch)
    late_options = []
    for prefix, actor, condition in (("21", "코토", {}), ("46", "타이가", {"fte:33:complete": True}), ("152", "타이가 — 늦은 첫 만남", {"fte:33:complete": False})):
        if prefix in freetime_graphs:
            fte=freetime_graphs[prefix]
            for node_id,node in fte['nodes'].items():
                if node_id not in g.nodes:g.add(node_id,node)
            jump=g.add(f'v4:1:F1-B:call:{prefix}',{'type':'call','target':fte['entry'],'returnTo':dinner_entry,'onReturnSet':{fte['completionFlag']:True,'window:F1-B:completed':True,**fte.get('completionSet',{})}})
        else:
            jump=g.add(f"v4:1:F1-B:unrouted:{prefix}", {"type": "gate", "reason": "This meeting's exact late-entry/prior-choice routing is not compiled. Preserve the manuscript's actual day and physical state."})
        late_options.append({"id": prefix, "label": actor, "to": jump, "requires": condition})
    late_options.append({"id": "REST", "label": "혼자 쉰다", "to": dinner_entry, "set": {"window:F1-B:completed": True}})
    late_window = g.add("v4:1:F1-B", {"type": "menu", "q": "늦은 개인시간", "selectionRole": "freetime", "maxSelections": 1, "poolComplete": False, "options": late_options})
    before_late = span("11a", "### 1-07F 저녁에 다시 볼 자리", "### 1-07k 부탁한 잠", late_window)
    bench = span("101", "## 1-07-101 돌아오겠다고 한 벤치", "## 1-17a 고치다 접어 둔 길", before_late)
    after_punishment = span("11a", 953, "### 1-07F 저녁에 다시 볼 자리", bench)
    punishment = span("135", "## 1-07P1 장난이 끝나고 남는 사람", None, after_punishment)
    main_after_tour = span("11a", "## 1-06 사라진 것은 공구가 아니다", 951, punishment)
    map_after = span("101", "## 1-05f 남이 먼저 고른 편", "## 1-07-101 돌아오겠다고 한 벤치", main_after_tour)
    map_merge = line("101", "**합류.미오의 낱장은 A/B에서 굽이를 실제 수정/C에서 미수정,모든 경로 미오 가방 바깥 칸이다.공구 점검표/카에데 사본/오늘 보호 페이지와 별개다.이 낱장으로 사건 현장 구조나 타인의 연속 알리바이를 증명하지 않는다.**")
    map_ab = span("101", "### A/B", "### C", map_after)
    map_c = span("101", line("101", "### C") + 1, map_merge - 1, map_after)
    map_callback = g.add("v4:101:1-C06:callback-map", {"type": "branch", "cases": [{"flag": "1-C06", "equals": "A", "to": map_ab}, {"flag": "1-C06", "equals": "B", "to": map_ab}, {"flag": "1-C06", "equals": "C", "to": map_c}], "default": "v4:101:1-C06:missing"})
    g.add("v4:101:1-C06:missing", {"type": "gate", "reason": "Required 1-C06 choice is missing; do not invent a map correction."})
    map_callback_intro = span("101", "## 1-05e 더 잘 보이는 그림", "### A/B", map_callback)
    map_choice = select("101", "## 선택 1-C06 — 다음에 앞설 사람", ["### A. 미오가 그린 다른 구간을 직접 앞서 걷는다", "### B. 소라에게 그림을 보고 앞서 가 달라고 한다", "### C. 지금은 그만하고 하루카와 벤치에 앉는다"], "## 1-05e 더 잘 보이는 그림", map_callback_intro, "1-C06")
    map_tour = span("101", "## 1-05a 아직 모르는 광장", "## 선택 1-C06 — 다음에 앞설 사람", map_choice)
    afternoon = span("11a", "## 1-05 오후의 팀", 811, map_tour)
    first_free = first_window(afternoon)
    tools_and_lunch = span("11a", "## 1-02b 빌린 카메라", "## 1-05 오후의 팀", first_free)
    office_join = span("91", "**합류.**", None, tools_and_lunch)
    office_a = line("91", "### P-C02 A — 전날 합석을 제안했고,뒤에 함께 가기로 했다")
    office_b = line("91", "### P-C02 B — 전날 카에데 자리에서 먹었고,다음 날 동행 약속은 없었다")
    office_branch = g.add("v4:91:P-C02:callback", {"type": "branch", "cases": [{"flag": "P-C02", "equals": "A", "to": span("91", office_a + 1, office_b - 1, office_join)}, {"flag": "P-C02", "equals": "B", "to": span("91", office_b + 1, line("91", "**합류.**") - 1, office_join)}], "default": "v4:91:P-C02:missing"})
    g.add("v4:91:P-C02:missing", {"type": "gate", "reason": "Prologue dinner choice missing; no prior promise is invented."})
    office_intro = span("91", "## 1-02a1 밥 먹은 다음", office_a - 1, office_branch)
    protected_page = span("11a", "### 1-02N 오늘의 한 면", "## 1-02b 빌린 카메라", office_intro)
    breakfast_choice = select("11a", "### 선택 1-C01 — 명단 앞에서", ["**A. 이름 대신 수량만 적자고 제안한다.**", "**B. 누가 먹었는지 남기는 데 동의한다.**", "**C. 음식은 받되 작성에는 참여하지 않는다.**"], "### 1-02N 오늘의 한 면", protected_page, "1-C01")
    entry = span("11a", "## 1-01 아침에 나오지 않은 사람", "### 선택 1-C01 — 명단 앞에서", breakfast_choice)

    def branches(ident: str, flag: str, ranges: list[tuple[str, str, str | int, str | int | None]], default: str, target: str) -> str:
        cases = [{"flag": flag, "equals": value, "to": span(prefix, first, last, target)} for value, prefix, first, last in ranges]
        return g.add(ident, {"type": "branch", "cases": cases, "default": default})

    def unresolved_window(ident: str, title: str, candidates: list[tuple[str, str, dict[str, Any]]], target: str) -> str:
        options = []
        for prefix, actor, requires in candidates:
            if prefix in freetime_graphs:
                fte = freetime_graphs[prefix]
                for node_id, node in fte["nodes"].items():
                    if node_id not in g.nodes:
                        g.add(node_id, node)
                extraSet={'TA02Late3AM':True} if ident=='F1-early' and prefix=='46' else {}
                if ident=='F1-E' and prefix=='40':extraSet={'KAEDE02Late3E':True}
                jump = g.add(f"v4:1:{ident}:call:{prefix}", {"type": "call", "target": fte["entry"], "returnTo": target, "onReturnSet": {fte["completionFlag"]: True, f"window:{ident}:completed": True, **fte.get('completionSet',{}),**extraSet}})
            else:
                jump = g.add(f"v4:1:{ident}:unrouted:{prefix}", {"type": "gate", "reason": "This meeting needs its exact prior-choice and late-entry contracts. Do not grant completion, items, or relationship progress."})
            options.append({"id": prefix, "label": actor, "to": jump, "requires": requires})
        options.append({"id": "REST", "label": "혼자 쉰다", "to": target, "set": {f"window:{ident}:completed": True}})
        return g.add(f"v4:1:{ident}", {"type": "menu", "q": title, "selectionRole": "freetime", "maxSelections": 1, "poolComplete": False, "options": options})

    day3_gate = g.add("v4:1:11a3:pending", {"type": "gate", "reason": "The two actual living days and exact insertions are routed. Discovery day/investigation/trial still need explicit routes.", "nextSource": next(s.name for s in sources.values() if s.prefix == "11a3")})
    # The night manuscript also contains next-morning consequences. Those are
    # deliberately excluded here and will be called only from 11a3.
    night2 = span("170", "## 1-18a 누구 방 앞에 서 있는가", "## 1-19-F-170 얇은 종이를 나눠 주는 아침", day3_gate)
    before_night2 = span("11a2", "## 1-18 피곤한 사람의 순서", None, night2)
    sa1 = line("11a2", "**49B1:아카리를 함께 기다리고 세 사람이 돌았다.**")
    sa2 = line("11a2", "**49B2:미오가 다녀오는 동안 사츠키가 약속한 자리를 떠났다.**")
    sa3 = line("11a2", "**49B3:미오가 서운함을 말하고 떠났다.**")
    sa_end = line("11a2", "**합류.미오는밤의의무실앞장면을멀리서보는원래동선으로간다.**")
    sa_callback = branches("v4:11a2:SA02:callback", "F-SA02-B", [("B1", "11a2", sa1 + 1, sa2 - 1), ("B2", "11a2", sa2 + 1, sa3 - 1), ("B3", "11a2", sa3 + 1, sa_end - 1)], before_night2, before_night2)
    evening2_tail = span("11a2", 1062, "### 1-17-F-SA02 — 기다리는 쪽이 바뀐 복도", sa_callback)
    ea = line("11a2", "### 1-C07-A — 실제로 타이가의 자세를 흉내 냈다")
    eb = line("11a2", "### 1-C07-B — 웃었지만 직접 흉내 내지는 않았다")
    ec = line("11a2", "### 1-C07-C — 없는 자리의 조롱을 그만하라고 했다")
    evening2_choice_echo = branches("v4:11a2:1-C07:evening", "1-C07", [("A", "11a2", ea + 1, eb - 1), ("B", "11a2", eb + 1, ec - 1), ("C", "11a2", ec + 1, 1060)], "v4:108:1-C07:missing", evening2_tail)
    evening2 = span("11a2", "## 1-17g 빈 의자가 먼저 고른 자리", ea - 1, evening2_choice_echo)
    # 108 has two different immediate callbacks followed by another-day echo.
    tail108 = span("108", 284, "## 1-24a 웃던 얼굴이 다시 모인 곳", evening2)
    echo2 = branches("v4:108:1-C07:echo2", "1-C07", [("A", "108", 272, 274), ("B", "108", 276, 278), ("C", "108", 280, 282)], "v4:108:1-C07:missing", tail108)
    between108 = span("108", "## 1-17e 네가 웃으면 끝나는 것", 270, echo2)
    echo1 = branches("v4:108:1-C07:echo1", "1-C07", [("A", "108", 160, 178), ("B", "108", 180, 196), ("C", "108", 198, 210)], "v4:108:1-C07:missing", between108)
    intro_echo1 = span("108", "## 1-17d 방금 웃은 사람", 158, echo1)
    g.add("v4:108:1-C07:missing", {"type": "gate", "reason": "The actual earlier 1-C07 choice is missing. Do not play every reaction."})
    menu108 = select("108", "## 선택 1-C07 — 빈 자리 쪽을 보고", ["### A. 타이가가 후보로 나서던 자세를 흉내 낸다", "### B. 같이 웃지만 직접 흉내 내지는 않는다", "### C. 타이가가 없는 자리에서 그만하라고 한다"], "**합류.미오의 직접 흉내는A만,켄 연기에 웃으며 남은 것은B,C는 거부하고 본인도 조롱당했다.A/B에서 미오가 공개적으로 그만두라 했다고 합치지 않는다.**", intro_echo1, "1-C07")
    entry108 = span("108", "## 1-17b 후보가 나간 의자", "## 선택 1-C07 — 빈 자리 쪽을 보고", menu108)
    after176 = span("176", "## W1-176-04 실제로 끊는 사람", "## R1-176 대답하지 않는 상대", entry108)
    menu176 = select("176", "### 선택 W1-C02", ["**A. 연습을 거절하고 켄의 손을 내려놓게 한다.**", "**B. 자기 첫마디를 말해 본다.**", "**C. 받는 사람을 맡겠다고 한다.**"], "## W1-176-04 실제로 끊는 사람", after176, "W1-C02")
    entry176 = span("176", "## W1-176-01 수화기 없이 거는 사람", "### 선택 W1-C02", menu176)
    representatives = span("11a2", "## 1-17 서로 다른 대표", 976, entry176)
    map_next_day_tail = span("101", "**합류.지금은 연락 대표와 후보 이야기로 넘어간다.어제의 팀을 투표 연대나 순찰 의무로 자동 승계하지 않는다.**", None, representatives)
    map_next_day = branches("v4:101:1-C06:nextday", "1-C06", [("A", "101", 426, 434), ("B", "101", 436, 444), ("C", "101", 446, 456)], "v4:101:1-C06:missing", map_next_day_tail)
    window_e = unresolved_window("F1-E", "개인시간 — 연락 안내 뒤", [("23", "쇼", {}), ("40", "카에데 — 늦은 두 번째", {"KAEDE01Late3D": True, "fte:40:complete": False})], span("101", "## 1-17a 고치다 접어 둔 길", 424, map_next_day))
    before_e = span("11a2", "### 1-16F 대표 모임까지", 907, window_e)
    entry78 = span("78", "## 1-16a 우리 중에 한 사람", None, before_e)
    announcement2 = span("11a2", "## 1-16 외부 연락 신청", 891, entry78)
    window_d = unresolved_window("F1-D", "개인시간 — 공동 점검 뒤", [("40", "카에데 — 두 번째", {"fte:22:complete": True, "fte:40:complete": False}), ("153", "카에데 — 늦은 첫 만남", {"fte:22:complete": False})], announcement2)
    common_check = span("11a2", "## 1-14 소리가 닿는 곳", "## 1-16 외부 연락 신청", window_d)
    window_c = unresolved_window("F1-C", "개인시간 — 점심 뒤", [("22", "카에데", {"fte:22:complete": False}), ("43", "아이 — 두 번째", {"fte:25:complete": True}), ("51", "타이가 — 세 번째", {"fte:46:complete": True}), ("49", "사츠키 — 두 번째", {"fte:32:complete": True})], common_check)
    lunch_after = span("92", "## 1-13a 밥 먹기 전이라고 했잖아", None, span("11a2", "### 1-13F 식사 뒤의 한 사람", "## 1-14 소리가 닿는 곳", window_c))
    after_game = span("11a2", 605, 607, lunch_after)
    end123 = span("123", "## 1-13P3 끝낸 사람", "## T-01P 빈 소리는 누가 낼까", after_game)
    game123 = select("123", "### 선택 1-C09 — 손을 올리는 이유", ["### A — 틀리는 쪽이 편해서", "### B — 두 번째도 같은 데서", "### C — 구경하는 자리"], "**합류.미오의A는고의변형/B는두번실패뒤느린순서성공/C는청취다.다른두경로의성공·실패·대변을뒤회상에합치지않는다.**", end123, "1-C09")
    entry123 = span("123", "## 1-13P1 이번에는 네가 틀렸어", "### 선택 1-C09 — 손을 올리는 이유", game123)
    lunch_common = span("11a2", 591, 603, entry123)
    eat = span("11a2", 584, 585, lunch_common)
    leave = span("11a2", 588, 589, lunch_common)
    eat_choice = g.add("v4:11a2:AI01:current-lunch", {"type": "menu", "q": "접시의 작은 조각", "options": [{"id": "EAT", "label": "작은 조각을 먹는다", "to": eat, "set": {"F-AI01-A3-LUNCH": "EAT"}}, {"id": "LEAVE", "label": "이번에도 남긴다", "to": leave, "set": {"F-AI01-A3-LUNCH": "LEAVE"}}]})
    ai_lunch_intro = span("11a2", 579, 581, eat_choice)
    ai_lunch = g.add("v4:11a2:AI01:lunch-callback", {"type": "branch", "cases": [{"flag": "F-AI01-A", "equals": "A1", "to": span("11a2", 571, 573, lunch_common)}, {"flag": "F-AI01-A", "equals": "A2", "to": span("11a2", 575, 577, lunch_common)}, {"flag": "F-AI01-A", "equals": "A3", "to": ai_lunch_intro}], "default": lunch_common})
    lunch_start = span("11a2", "## 1-13 점심, 반쯤 남은 의자", "### 1-13-F-AI01 — 앞서 부탁한 접시", ai_lunch)
    entry92 = span("92", "## 1-12a 모인 사람부터", "## 1-13a 밥 먹기 전이라고 했잖아", lunch_start)
    moving_after = span("11a2", 435, 531, entry92)
    moving_branch = branches("v4:11a2:1-C02:moving", "1-C02", [("A", "11a2", 403, 417), ("B", "11a2", 419, 433)], "v4:11a2:1-C02:missing", moving_after)
    room_join = span("11a2", 291, "### 1-C02 A — 미오와 카에데가 바꾼다", moving_branch)
    room_choice = select("11a2", "### 선택 1-C02 — 방 교환", ["**A. 바꾼다.**", "**B. 거절하고 다른 희망자를 같이 찾는다.**"], 290, room_join, "1-C02")
    g.add("v4:11a2:1-C02:missing", {"type": "gate", "reason": "Required room-exchange choice is missing; do not assign the same key/room in both branches."})
    room_start = span("11a2", "## 1-10 방을 바꾸자는 사람들", "### 선택 1-C02 — 방 교환", room_choice)
    early_window = unresolved_window("F1-early", "개인시간 — 아침", [("46", "타이가 — 늦은 두 번째", {"TA01Late2B": True, "fte:46:complete": False})], room_start)
    c14_end = span("154", "**합류.**", "## 1-19-C14 다음날 아침의 반환", early_window)
    c14_ab = span("154", "**A/B 공통.**", "**C만.**", c14_end)
    c14_c = span("154", "**C만.**", "**합류.**", c14_end)
    c14_callback = g.add("v4:154:1-C14:after", {"type": "branch", "cases": [{"flag": "1-C14", "equals": "A", "to": c14_ab}, {"flag": "1-C14", "equals": "B", "to": c14_ab}, {"flag": "1-C14", "equals": "C", "to": c14_c}], "default": "v4:154:1-C14:missing"})
    g.add("v4:154:1-C14:missing", {"type": "gate", "reason": "Required physical-cushion choice missing; no duplicate possession is invented."})
    c14_choice = select("154", "## 선택 1-C14 — 먼저 찾으면", ["### A. 미오가 오늘 밤 쓰겠다고 마음먹는다", "### B. 카에데를 불러 지금 건넨다", "### C. 로비에 두자고 말하고 의자에 놓는다"], "## 1-09a-03 식사 전의 다른 길", c14_callback, "1-C14")
    c14_entry = span("154", "## 1-09a-01 아침에 다시 나온 사람", "## 선택 1-C14 — 먼저 찾으면", c14_choice)
    dawn_common = span("11a2", 43, "## 1-09a 먼저 찾은 아침", c14_entry)
    dawn_callback = g.add("v4:11a2:RIN01:dawn", {"type": "branch", "cases": [{"flag": "fte:20:complete", "equals": True, "to": span("11a2", "**린 자유시간01을 본 경로.**", "**보지 않은 경로.**", dawn_common)}], "default": span("11a2", "**보지 않은 경로.**", 41, dawn_common)})
    day2_entry = span("11a2", "## 1-09 누구 방에서 나는 소리", "**린 자유시간01을 본 경로.**", dawn_callback)
    g.nodes[next_day] = {"id": next_day, "type": "stage", "direction": "첫 생활일 밤 뒤 다음 생활일 새벽으로 이어진다.", "next": day2_entry}
    investigation_gate = g.add("v4:1:11b:pending", {"type": "gate", "reason": "The three daily-life days through discovery are explicitly routed. Investigation/trial and uncompiled optional meetings remain.", "nextSource": next(s.name for s in sources.values() if s.prefix == "11b")})
    discovery_tail = span("11a3", 1095, None, investigation_gate)
    departure_callback = branches("v4:11a3:1-C04:departure", "1-C04", [("A", "11a3", 1045, 1061), ("B", "11a3", 1063, 1077), ("C", "11a3", 1079, 1093)], "v4:11a3:1-C04:missing", discovery_tail)
    after_copy = span("11a3", 957, 1043, departure_callback)
    copy_choice = select("11a3", "### 선택 1-C04 — 지금 할 말", ["**A. 개인정보 부록을 다시 묻는다.**", "**B. 사본 보관 범위를 정한다.**", "**C. 그냥 받는다.**"], 956, after_copy, "1-C04")
    g.add("v4:11a3:1-C04:missing", {"type": "gate", "reason": "Required actual copy/question choice missing; no later promise or kept copy is invented."})
    late_day = span("11a3", "## 1-28 약속한 시각", "### 선택 1-C04 — 지금 할 말", copy_choice)
    entry82 = span("82", "## 1-27a 알아야 하는 사람", None, late_day)
    public_objection = span("11a3", "**공통 장면 복귀.**", "## 1-28 약속한 시각", entry82)
    kaede03_common = span("11a3", 823, 833, public_objection)
    kaede03_callback = branches("v4:11a3:KAEDE03:callback", "KAEDE-03B", [("A", "11a3", 809, 813), ("B", "11a3", 815, 817), ("C", "11a3", 819, 821)], public_objection, kaede03_common)
    afternoon3 = span("11a3", "## 1-25 고칠 것과 말할 것", "### 1-27-F-KAEDE03 — 조금 전에 알던 사람", kaede03_callback)
    window_f = unresolved_window("F1-F", "개인시간 — 모니터가 꺼진 뒤", [("50", "카에데 — 세 번째", {"fte:40:complete": True})], afternoon3)
    candy_tail = span("139", "**합류.**", None, window_f)
    candy_seen = span("139", "### 22를 실제로 본 경로", "### 22를 보지 않은 경로", candy_tail)
    candy_not_seen = span("139", "### 22를 보지 않은 경로", "**합류.**", candy_tail)
    candy_callback = g.add("v4:139:KAEDE01:callback", {"type": "branch", "cases": [{"flag": "fte:22:complete", "equals": True, "to": candy_seen}], "default": candy_not_seen})
    candy_start = span("139", "## 1-24c 아직 말을 걸어도 되는 사람", "### 22를 실제로 본 경로", candy_callback)
    after_monitor = span("11a3", "### 1-24b 모니터가 꺼진 뒤", "## 1-25 고칠 것과 말할 것", candy_start)
    late108_common = span("108", 332, None, after_monitor)
    late108 = branches("v4:108:1-C07:discoveryday", "1-C07", [("A", "108", 310, 316), ("B", "108", 318, 322), ("C", "108", 324, 330)], "v4:108:1-C07:missing", late108_common)
    late108_intro = span("108", "## 1-24a 웃던 얼굴이 다시 모인 곳", 308, late108)
    after_representative = span("11a3", 65, 435, late108_intro)
    vote_options = []
    for name, first, last in (("카에데", 49, 51), ("타이가", 53, 55), ("켄", 57, 59), ("기권", 61, 63)):
        vote_options.append({"id": SPEAKERS.get(name, "abstain"), "label": name, "to": span("11a3", first, last, after_representative), "set": {"1-C03": name}})
    representative_menu = g.add("v4:11a3:1-C03:representative", {"type": "menu", "q": "외부 연락 대표 후보", "selectionRole": "representative-vote", "finalVote": False, "fixedResult": "kaede", "options": vote_options, "source": docs["11a3"].ref(44)})
    before_representative = span("11a3", 13, "### 선택 1-C03 — 대표 후보", representative_menu)
    morning170 = span("170", "## 1-19-F-170 얇은 종이를 나눠 주는 아침", None, before_representative)
    vote_papers = span("11a3", "## 1-19 종이에는 누구 이름을 적을까", 11, morning170)
    cushion_common = span("154", 402, None, vote_papers)
    cushion_return = branches("v4:154:1-C14:return", "1-C14", [("A", "154", 302, 338), ("B", "154", 340, 372), ("C", "154", 374, 400)], "v4:154:1-C14:missing", cushion_common)
    cushion_intro = span("154", "## 1-19-C14 다음날 아침의 반환", 300, cushion_return)
    g.nodes[day3_gate] = {"id": day3_gate, "type": "stage", "direction": "둘째 생활일 밤 뒤 다음 날 아침으로 이어진다.", "next": cushion_intro}
    # Only the actual discovery changes the publicly known roster. Earlier
    # foreshadowing, discussions of death and optional scenes never do so.
    for node in g.nodes.values():
        if node.get("source", {}).get("file") == docs["11a3"].name and node.get("source", {}).get("line") == 1154:
            node["set"] = {"public:kaede:body-discovered": True}
    from v4_story_case1 import compile_investigation, insert_prior_observations
    trial_gate = g.add("v4:1:11c1:pending", {"type": "gate", "reason": "Three living days, discovery and source-scoped investigation are routed. The actual complete trial is still being encoded; no legacy trial is substituted."})
    investigation_entry, catalogue = compile_investigation(g, sources, trial_gate)
    g.nodes[investigation_gate] = {"id": investigation_gate, "type": "stage", "direction": "발견 직후의 실제 수사로 이어진다.", "next": investigation_entry}
    insert_prior_observations(g, sources)
    from v4_story_trial1 import compile_first_half
    from v4_story_trial1_late import compile_second_half
    from v4_story_result1 import compile_result
    chapter_end = g.add("v4:1:end", {"type": "end", "chapterComplete": True, "nextChapter": "2", "note": "Actual end after the case-one result route. Runtime, visual and duration acceptance remain separate."})
    result_entry = compile_result(g, sources, chapter_end)
    result_gate = g.add("v4:1:11d:pending", {"type": "gate", "reason": "Case-one aftermath routing is being authored. Correct-vote state does not auto-complete aftermath."})
    g.nodes[result_gate] = {"id": result_gate, "type": "stage", "direction": "실제 정답 투표 후의 결과와 다음 날로 이어진다.", "next": result_entry}
    late_trial = compile_second_half(g, sources, tasks, result_gate)
    second_half_gate = g.add("v4:1:11c2:pending", {"type": "gate", "reason": "Trial second-half routing is being authored; no old case or automatic answers are substituted."})
    g.nodes[second_half_gate] = {"id": second_half_gate, "type": "stage", "direction": "앞서 확인한 범위를 지닌 채 재판 후반으로 이어진다.", "next": late_trial}
    trial_entry = compile_first_half(g, sources, tasks, second_half_gate)
    g.nodes[trial_gate] = {"id": trial_gate, "type": "stage", "direction": "수집한 증거를 지닌 채 첫 학급재판으로 이어진다.", "next": trial_entry}
    from v4_case1_picture_bindings import bind_pictures
    bind_pictures(g, sources, tasks)
    seats = [actor for actor in SPEAKERS.values() if actor != "lappy"]
    for node in g.nodes.values():
        if node.get("type") == "task":
            node["trialDead"] = ["kaede"]
            node["seats"] = seats
            node["rosterSource"] = docs["11a3"].ref(1154)
    return g.export(entry, routingStatus="mandatory-source-routes-through-case-one-end", evidenceCatalog=catalogue, contentScope="Three living days, every authored first-case personal-time candidate, discovery, source-scoped interactive investigation, both trial halves, exclusive lie route, six-slot reconstruction, real vote and conditional aftermath through the next-area opening. Runtime, staging and play-time acceptance are separate.", campaignReady=False)


def compile_prologue(source: Source) -> dict[str, Any]:
    """The two choices and all three delayed C01 callbacks are authored routes.

    Ranges are located by exact original text, not mutable line-number offsets.
    Actual readable rule/private ability pages are document nodes, while other
    blockquotes remain editorial metadata and are never displayed.
    """
    g = Graph("P")
    at = source.at
    end = g.add("v4:P:end", {"type": "end", "chapterComplete": True, "nextChapter": "1"})
    tail = g.sequence(source, at("## P-08 방 앞에서"), len(source.lines), end)
    join2 = g.sequence(source, at("(카운터에서 아이가 남은 양을 재고 있다. 쇼가 옆에서 식기 하나를 내려놓는다.)"), at("## P-08 방 앞에서") - 1, tail)
    a2 = at("**A. 하루카와 앉되 카에데에게 합석을 제안한다.**")
    b2 = at("**B. 하루카에게 잠시 기다려 달라고 하고 카에데의 테이블로 간다.**")
    c2 = g.add("v4:10:P-C02", {"type": "menu", "q": "빈 의자", "source": source.ref(at("### 선택 P-C02 — 빈 의자")), "options": []})
    g.nodes[c2]["options"] = [
        {"id": "A", "label": clean(source.lines[a2 - 1])[3:], "to": g.sequence(source, a2 + 1, b2 - 1, join2), "set": {"P-C02": "A"}},
        {"id": "B", "label": clean(source.lines[b2 - 1])[3:], "to": g.sequence(source, b2 + 1, at("(카운터에서 아이가 남은 양을 재고 있다. 쇼가 옆에서 식기 하나를 내려놓는다.)") - 1, join2), "set": {"P-C02": "B"}},
    ]
    before_choice2 = g.sequence(source, at("## P-07 저녁을 먹는 자리"), at("### 선택 P-C02 — 빈 의자") - 1, c2)

    # First-meeting revisions may grow the opening. Locate the two readable
    # pages by their authored boundaries instead of obsolete line numbers.
    ability_title = at("> 아오이 미오 — 기록")
    ability_end = at("(미오는 마지막 두 줄을 먼저 두 번 읽는다. 어떤 문장으로 무엇을 끝낼 수 있는지, 끝난 일이 되돌아오는지까지 이 짧은 설명에는 없다.)")
    ability = g.sequence(source, ability_end, at("## P-07 저녁을 먹는 자리") - 1, before_choice2)
    ability_rows = [line[2:] for line in source.lines[ability_title:ability_end-1] if line.startswith('> ')]
    assert len(ability_rows) == 3
    ability_doc = g.add("v4:10:P-06a:document", {"type": "document", "title": "아오이 미오 — 기록", "rows": ability_rows, "private": True, "source": source.ref(ability_title), "next": ability})
    ability_intro = g.sequence(source, at("## P-06a 자기 이름 아래의 글"), ability_title-1, ability_doc)
    rules_begin = at("> 공통 규칙: 다른 참가자를 살해한 검정이 누구인지 학급 재판에서 가린다.")
    rules_end = at("(미오는 둘째 줄을 읽다가 셋째 줄로 내려간다. 한 번 위로 돌아가 다시 읽는다. 자기 이름표를 붙여 놓은 기기인데, 글 안에는 자기 이름이 없다.)")
    rules_after = g.sequence(source, rules_end, at("## P-06a 자기 이름 아래의 글") - 1, ability_intro)
    rules_rows = [line[2:] for line in source.lines[rules_begin-1:rules_end-1] if line.startswith('> ')]
    assert len(rules_rows) == 3
    rules_doc = g.add("v4:10:P-06-READ:document", {"type": "document", "title": "공통 규칙", "rows": rules_rows, "private": False, "source": source.ref(rules_begin), "next": rules_after})
    announcement = g.sequence(source, at("## P-05 안내 방송"), rules_begin-1, rules_doc)

    common_return = g.sequence(source, at("**A/B 공통 귀환.**"), at("## P-05 안내 방송") - 1, announcement)
    late_b_start = at("### P-C01 B — 돌아온 뒤 처음 묻는다")
    late_b = g.sequence(source, late_b_start, at("**A/B 공통 귀환.**") - 1, common_return)
    late_branch = g.add("v4:10:P-C01:callback-return", {"type": "branch", "cases": [{"flag": "P-C01", "equals": "B", "to": late_b}], "default": common_return})
    common_middle = g.sequence(source, at("(미오는 일반 메모의「전화 불통」을「이 전화에서 발신음 없음/목록 첫 한 곳 연결 못 함」으로 고친다.프린터 출력이나 새 능력의 판정이 아니다.)"), late_b_start - 1, late_branch)
    ca = at("### P-C01 A — 하루카가 관리실에 동행했다")
    cb = at("### P-C01 B — 하루카가 광장에 남았다")
    present_a = g.sequence(source, ca + 1, cb - 1, common_middle)
    present_b = g.sequence(source, cb + 1, at("(미오는 일반 메모의「전화 불통」을「이 전화에서 발신음 없음/목록 첫 한 곳 연결 못 함」으로 고친다.프린터 출력이나 새 능력의 판정이 아니다.)") - 1, common_middle)
    followup = g.add("v4:10:P-C01:callback-office", {"type": "branch", "cases": [{"flag": "P-C01", "equals": "A", "to": present_a}, {"flag": "P-C01", "equals": "B", "to": present_b}], "default": "v4:10:P-C01:missing-flag"})
    g.add("v4:10:P-C01:missing-flag", {"type": "gate", "reason": "P-C01 selection is missing or invalid; no default companion is invented."})
    common1 = g.sequence(source, at("[리쿠] 끝났어? 가방 하나에 표정이 몇 개나 걸리네."), ca - 1, followup)
    a1 = at("**A. 하루카에게 같이 가자고 한다.**")
    b1 = at("**B. 하루카에게 남아 달라고 한다.**")
    menu1 = g.add("v4:10:P-C01", {"type": "menu", "q": "함께 갈 사람", "source": source.ref(at("### 선택 P-C01 — 함께 갈 사람")), "options": [
        {"id": "A", "label": "하루카에게 같이 가자고 한다", "to": g.sequence(source, a1 + 1, b1 - 1, common1), "set": {"P-C01": "A"}},
        {"id": "B", "label": "하루카에게 남아 달라고 한다", "to": g.sequence(source, b1 + 1, at("[리쿠] 끝났어? 가방 하나에 표정이 몇 개나 걸리네.") - 1, common1), "set": {"P-C01": "B"}},
    ]})
    entry = g.sequence(source, 6, at("### 선택 P-C01 — 함께 갈 사람") - 1, menu1)
    introductions = {
        'haruka': '하루카. 아사노 하루카.', 'sho': '쇼입니다.',
        'nana': '나나예요.', 'ai': '아이예요.', 'taiga': '나 타이가!',
        'rin': '린.', 'ken': '켄.', 'sora': '소라야.', 'kaede': '카에데.',
        'koto': '코토예요.', 'rei': '레이입니다.', 'riku': '리쿠.',
        'yuu': '유우.', 'akari': '아카리예요.', 'satsuki': '사츠키.',
    }
    known = {'mio'}
    cursor = entry
    while g.nodes[cursor]['type'] != 'menu':
        node = g.nodes[cursor]
        if node['type'] == 'say':
            actor = node['actor']
            # A rewritten introduction still occurs at the original authored
            # line. Do not tie the name reveal to a particular spoken ending.
            line_no = node['source']['line']
            original = speaker_line(original_voice_line(source.name, line_no, source.lines[line_no - 1]))
            intro_text = original['text'] if original else node['text']
            if actor in introductions and intro_text.startswith(introductions[actor]):
                known.add(actor)
                node['introducesActor'] = actor
            if actor not in known and not node.get('mono'):
                node['speaker'] = '???'
        cursor = node['next']
    assert len(known) == 16, known
    return g.export(entry, routingStatus="authored", routePolicy="Both menus and delayed callbacks are mutually exclusive; stage directions are not dialogue.")


def field(text: str, name: str) -> str:
    match = re.search(r"^- " + re.escape(name) + r"[：:]\s*(.+)$", text, re.M)
    return clean(match[1]) if match else ""


def source_says(source: Source, start: int, end: int) -> list[dict[str, Any]]:
    return [e for e in source.paragraphs(start, end) if e["type"] == "say"]


def compile_tasks(sources: dict[str, Source], ledger: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for item in ledger["entries"]:
        source = sources[item["file"]]
        start, end = source.section(item["id"])
        lines = source.lines
        text = "\n".join(lines[start - 1:end])
        h = [(i, HEADING.match(lines[i - 1])) for i in range(start + 1, end + 1) if HEADING.match(lines[i - 1])]
        wrong = next((i for i, m in h if "오답" in m[2]), None)
        correct = next((i for i, m in h if "정답" in m[2] and "오답" not in m[2]), None)
        config_start = next((i for i, m in h if "입력과 판정" in m[2]), None)
        body_end = min(x for x in (wrong, correct, config_start, end + 1) if x is not None) - 1
        before = source_says(source, start + 1, body_end)
        task: dict[str, Any] = {"id": item["id"], "chapter": str(item["chapter"]), "kind": KIND[item["kind"]], "sourceKind": item["kind"], "title": lines[start - 1].split(" ", 2)[-1], "source": source.ref(start), "prompt": field(text, "질문") or field(text, "지목 질문"), "intro": before, "wrong": source_says(source, wrong + 1, correct - 1) if wrong and correct else [], "success": source_says(source, correct + 1, end) if correct else [], "answerScope": item["answer"], "retry": {"sameTask": True, "preserveEvidence": True, "preservePublicFacts": True, "cancellationIsSuccess": False}, "bindings": []}
        if item.get("success_next"):
            task["return"] = {"taskId": item["success_next"]}
        else:
            parent = sources[item["parent"]]
            line = item["success_parent_line"]
            if not parent.lines[line - 1].startswith(item["return_first"]) and not original_voice_line(parent.name,line,parent.lines[line-1]).startswith(item["return_first"]):
                raise ValueError(f"{item['id']}: ledger return anchor has moved; update editorial ledger first")
            task["return"] = {"source": parent.ref(line), "exactLine": parent.lines[line - 1], "ledgerPrefix": item["return_first"]}
        if item["kind"] in ("NS", "PN", "RS"):
            # Debate utterances are the live loop; do not also run them as a
            # linear intro and then play the same utterances a second time.
            task["intro"] = [e for e in before if e["mono"]]
            task["lines"] = [e for e in before if not e["mono"]]
            targets = []
            for event in before:
                for mark, close, verdict in (("【", "】", "refute"), ("〔", "〕", "agree")):
                    for match in re.finditer(re.escape(mark) + "(.+?)" + re.escape(close), event["text"]):
                        targets.append({"lineId": event["id"], "word": match[1], "verdict": verdict, "actor": event["actor"]})
            task["targets"] = targets
            task["judgment"] = item.get("judgment", "refute")
            task["selectedEvidenceLabel"] = item.get("selected_evidence", "")
            task["vpoint"] = {"optional": True, "character": item.get("vpoint_character", "")} if item["kind"] == "NS" else {"optional": True}
            # The manuscript identifies one projectile but some labels refer to
            # bundles not yet mapped to acquired E-n cards. Do not auto-grant it.
            task["bindings"].append({"kind": "evidenceAcquisition", "required": True, "description": task["selectedEvidenceLabel"] or field(text, "정답")})
            if item["kind"] == "PN":
                lane_names = dict(re.findall(r"(왼쪽|가운데|오른쪽)\s+(?:열\s+)?(" + "|".join(SPEAKERS) + r")", text))
                task["lanes"] = [{"id": slot, "speaker": name, "actor": SPEAKERS[name], "lines": [e["id"] for e in task["lines"] if e["speaker"] == name]} for slot, name in lane_names.items()]
                if len(task["lanes"]) != 3 or {e["id"] for e in task["lines"]} != {ident for lane in task["lanes"] for ident in lane["lines"]}:
                    task["bindings"].append({"kind": "panicLanes", "required": True, "description": "Use the explicit left/centre/right source staging, not arbitrary speaker order."})
        elif item["kind"] in ("PERSON", "CULPRIT"):
            answer = str(item["answer"])
            # The past-day Haruka identity is intentionally separate from the
            # later created-body identity, despite the same portrait.
            names = [n for n in SPEAKERS if n in answer]
            exact = next((n for n in names if answer.startswith(n)), None)
            if not exact and item["id"] == "T6-PERSON-A02":
                exact = "하루카"
            if not exact:
                raise ValueError(f"{item['id']}: unknown person answer")
            task.update(answer=SPEAKERS[exact], candidates=[s for s in SPEAKERS.values() if s != "lappy"], selectionRole="culprit" if item["kind"] == "CULPRIT" else "person", finalVote=False, deadCandidatesSelectable=True)
        elif item["kind"] == "ANSWER":
            raw = field(text, "후보/표시 그림")
            options = re.split(r"/+(?=[A-C])", raw)
            task["options"] = [{"id": s[0], "label": s[1:].strip()} for s in options if re.match(r"^[A-C]", s)]
            match = re.match(r"([A-C])", str(item["answer"]))
            if not match or len(task["options"]) != 3:
                raise ValueError(f"{item['id']}: explicit three-option answer contract missing")
            task["answer"] = match[1]
        elif item["kind"] == "EVIDENCE":
            task["candidatesDescription"] = field(text, "후보/표시 그림")
            task["selectedEvidenceLabel"] = item["answer"]
            task["bindings"].append({"kind": "evidenceAcquisition", "required": True, "description": item["answer"]})
        elif item["kind"] in ("SPOT", "MM"):
            task.update(imageDescription=field(text, "가린 그림") or field(text, "후보/표시 그림"), regionDescription=item["answer"], regionsDescription=field(text, "노출되는 영역"))
            task["bindings"].append({"kind": "forensicImageRegions", "required": True, "description": "Bind this exact inspected image and actual visible clue polygons. Never use option-index coordinates."})
            if item["kind"] == "MM":
                task["mechanic"] = {"colors":["white","pink","yellow","blue"],"colorCountByDifficulty":True,"removeAdjacentSameColor":True,"adjacency":"orthogonal-four","gravity":False,"boundaryColorCycleOnce":True,"isolatedHits":3,"isolatedPenaltyTicks":600,"thenSelectRegion":True}
        elif item["kind"] == "FA":
            letters = [s.strip() for s in field(text, "제작용 답안 순서").split("/")]
            task.update(answer="".join(letters), answerGlyphs=letters, distractorDescription=field(text, "혼동 구슬"), retryPolicy="wrongSlotOnly", mechanic={"selectGlyphCount": 1, "arrivalJudgment": True, "poolSlots": 20, "specialCollectibleSeparate": True}, editorialMechanicCorrection="Native REA e9550/e96c0 selects one glyph and judges on arrival. The manuscript's same-glyph pair staging is not adopted as an executable rule.")
            if task["answer"] != item["answer"]:
                raise ValueError(f"{item['id']}: anagram order differs from approved ledger")
        elif item["kind"] == "RL":
            task["questions"] = []
            for n, (i, head) in enumerate(h):
                if not head[2].startswith("연결 "):
                    continue
                last = next((j - 1 for j, _ in h if j > i), end)
                block = "\n".join(lines[i:last])
                raw = field(block, "보기")
                options = re.split(r"/+(?=[A-C])", raw)
                answer = field(block, "정답")
                task["questions"].append({"id": f"{item['id']}:link:{len(task['questions']) + 1}", "q": field(block, "질문"), "options": [{"id": s[0], "label": s[1:]} for s in options], "answer": answer[0], "retryPolicy": "currentLinkOnly"})
            if [q["answer"] + next(o["label"] for o in q["options"] if o["id"] == q["answer"]) for q in task["questions"]] != item["answer"]:
                raise ValueError(f"{item['id']}: connection answers differ from ledger")
        task["runtimeReady"] = not any(b["required"] for b in task["bindings"])
        result[item["id"]] = task
    return {"schemaVersion": 1, "contentVersion": "v4", "tasks": result, "retired": ledger["purpose_revision"]["retired"] if isinstance(ledger.get("purpose_revision", {}).get("retired"), list) else [], "policy": "No correct-path simulation is run automatically; bindings never grant unacquired evidence."}


def index_sources(sources: dict[str, Source]) -> dict[str, Any]:
    blocks = {}
    for source in sources.values():
        events = source.paragraphs()
        for h in source.headings:
            if h["depth"] > 2:
                continue
            end = next((q["line"] - 1 for q in source.headings if q["line"] > h["line"] and q["depth"] <= h["depth"]), len(source.lines))
            key = f"v4:{source.prefix}:{h['location']}"
            if key in blocks:
                key += ":" + sha(h["title"])[:8]
            blocks[key] = {"id": key, "title": h["title"], "source": source.ref(h["line"]), "endLine": end, "events": [e for e in events if h["line"] <= e["source"]["line"] <= end], "executable": False, "note": "Indexed source block. Branches/conditional callbacks/editorial links require an explicit route; never play this list linearly."}
    return {"schemaVersion": 1, "contentVersion": "v4", "blocks": blocks}


def chapter_sources() -> dict[str, list[str]]:
    """The main reading order is already explicitly authored in the guide."""
    guide = (SRC / "전편_대본_읽기안내.md").read_text(encoding="utf-8-sig")
    result = {}
    for ch in ["P", "1", "2", "3", "4", "5", "6"]:
        header = "## 프롤로그" if ch == "P" else f"## {ch}장"
        start = guide.index(header) + len(header)
        end = guide.find("\n## ", start)
        part = guide[start:end if end != -1 else None]
        result[ch] = list(dict.fromkeys(m[2] for m in LINK.finditer(part)))
    return result


def score_index(index: dict[str, Any]) -> None:
    """Add cue metadata once per source event, despite nested index blocks."""
    from v4_presentation import score_graph_v4
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    for block in index["blocks"].values():
        for event in block["events"]:
            name = event["source"]["file"]
            match = re.search(r"([1-6])장", name)
            chapter = match[1] if match else "P" if name.startswith("10_") else "1"
            kind = "freetime" if "_자유시간_" in name else "scene"
            group = groups.setdefault((chapter, kind), {"chapter": chapter, "kind": kind, "nodes": {}})
            group["nodes"][event["id"]] = event
    for group in groups.values():
        score_graph_v4(group)
    index["presentationPolicy"] = "Metadata only. Nested blocks share event IDs; source index is not a playable sequence. Dispatch once on actual route entry."


def guard_unique_freetime_calls(graph):
    """Only a real normal return earns completion; completed calls hide.

    Existing per-day/prerequisite predicates stay in place. This adds only
    the current meeting's own uncompleted predicate, never new story facts.
    """
    for menu in graph['nodes'].values():
        if menu.get('selectionRole')!='freetime':continue
        for option in menu['options']:
            target=graph['nodes'][option['to']]
            if target['type']!='call':continue
            earned=[key for key,value in target.get('onReturnSet',{}).items() if key.startswith('fte:') and key.endswith(':complete') and value is True]
            requires=option.setdefault('requires',{})
            for key in earned:
                if requires.get(key) is True:raise ValueError('Repeated meeting contradicts authored prerequisite: '+menu['id']+' '+key)
                requires[key]=False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--strict", action="store_true", help="fail unless every required campaign route/binding is ready")
    args = parser.parse_args(argv)
    from v4_presentation import score_graph_v4, score_tasks_v4
    from v4_climax_picture_bindings import bind_climax_candidates
    from v4_remaining_picture_bindings import bind_remaining_pictures
    sources = {p.name: Source(p) for p in sorted(SRC.glob("*.md"))}
    routed_revisions = load(ROOT / "tools/v4_story_route_sources.json")["sources"]
    for name, expected in routed_revisions.items():
        if sources[name].hash != expected:
            raise ValueError(f"{name}: authored source ranges changed. Re-read the changed branch/call scopes and revise the routing contract before regenerating.")
    ledger = load(SRC / "qa_2026-10-29/trial_input_reedit.json")
    tasks = compile_tasks(sources, ledger)
    from v4_story_case1 import bind_tasks
    bind_tasks(tasks)
    score_tasks_v4(tasks)
    index = index_sources(sources)
    score_index(index)
    dump(args.out / "blocks.json", index)
    orders = chapter_sources()
    prologue = compile_prologue(sources[orders["P"][0]])
    score_graph_v4(prologue)
    dump(args.out / "chapters/P.json", prologue)
    from v4_story_freetime_third import compile_third,THIRD_PREFIXES
    simple_meetings = ("20", "22", "24", "25", "29", "30", "32", "33", "26", "27", "28", "31", "34", "21", "46", "152", "51", "43", "49", "23", "40", "50", "153", "35", "41", "44", "45", "48", "39", "42", "47", "52", "54", "63", "36", "53",*THIRD_PREFIXES)
    freetime = {}
    freetime_graphs = {}
    for prefix in simple_meetings:
        source = next(s for s in sources.values() if s.prefix == prefix)
        if prefix in ("26", "27", "28", "31", "34"):
            from v4_story_freetime import compile_nested_first_meeting
            graph = compile_nested_first_meeting(source)
        elif prefix in THIRD_PREFIXES:
            graph=compile_third(prefix,sources)
        elif prefix in ('21','46','152','51','43','49','23','40','50','153','35','41','44','45','48','39','42','47','52','54','63','36','53'):
            from v4_story_freetime_followups import compile_followup
            graph=compile_followup(prefix,sources)
        else:
            graph = compile_choice_scene(source)
        score_graph_v4(graph)
        freetime_graphs[prefix] = graph
        freetime[prefix] = {"sourceFile": source.name, "entry": graph["entry"], "path": f"freetime/{prefix}.json", "completionFlag": graph["completionFlag"]}
        dump(args.out / f"freetime/{prefix}.json", graph)
    from v4_story_freetime_late import compile_late,LATE_KEYS
    for key in LATE_KEYS:
        graph=compile_late(key,sources,freetime_graphs)
        score_graph_v4(graph)
        freetime_graphs[key]=graph
        freetime[key]={"sourceFile":graph['sourceFile'],"entry":graph['entry'],"path":f"freetime/{key}.json","completionFlag":graph['completionFlag']}
        dump(args.out / f"freetime/{key}.json",graph)
    canonical_meetings={str(n) for n in range(20,65)}
    dump(args.out / "freetime/index.json", {"schemaVersion": 1, "contentVersion": "v4", "meetings": freetime, "completePool": canonical_meetings.issubset(freetime), "canonicalCount":len(canonical_meetings.intersection(freetime)), "calendarVariantCount":len(set(freetime)-canonical_meetings), "coverageMeaning":"All 45 authored canonical meeting routes and source-authored calendar variants compiled; this is not runtime, visual, duration or campaign acceptance.", "unsupportedPolicy": "Never substitute another character, auto-complete a missing meeting, or combine all first-meeting variants."})
    route_issues = []
    for chapter in map(str, range(1, 7)):
        if chapter == "1":
            graph = compile_chapter_one_first_day(sources, freetime_graphs, tasks)
            bind_remaining_pictures(graph,sources,tasks)
            score_graph_v4(graph)
            dump(args.out / "chapters/1.json", graph)
            route_issues.append({"chapter": chapter, "kind": "partialCampaignRoutes", "completedScope": graph["contentScope"], "sourceOrder": orders[chapter]})
            continue
        if chapter == "2":
            from v4_story_case2 import compile_chapter_two
            graph = compile_chapter_two(sources, freetime_graphs, tasks)
            from v4_case2_6_picture_bindings import bind_pictures
            bind_pictures(graph,sources,tasks)
            score_graph_v4(graph)
            dump(args.out / "chapters/2.json", graph)
            route_issues.append({"chapter": chapter, "kind": "partialCampaignRoutes", "completedScope": graph["contentScope"], "sourceOrder": orders[chapter]})
            continue
        if chapter == "3":
            from v4_story_case3 import compile_chapter_three
            graph = compile_chapter_three(sources, freetime_graphs, tasks)
            from v4_identity_candidate_bindings import bind_candidate_identity
            bind_candidate_identity(graph,sources,tasks)
            bind_remaining_pictures(graph,sources,tasks)
            bind_climax_candidates(graph, sources, tasks)
            score_graph_v4(graph)
            dump(args.out / "chapters/3.json", graph)
            route_issues.append({"chapter": chapter, "kind": "partialCampaignRoutes", "completedScope": graph.get("contentScope", graph.get("routingStatus", "Explicit source routes with unresolved input gates")), "sourceOrder": orders[chapter]})
            continue
        if chapter == "4":
            from v4_story_case4 import compile_chapter_four
            graph = compile_chapter_four(sources, freetime_graphs, tasks)
            bind_remaining_pictures(graph,sources,tasks)
            bind_climax_candidates(graph, sources, tasks)
            score_graph_v4(graph)
            dump(args.out / "chapters/4.json", graph)
            route_issues.append({"chapter": chapter, "kind": "partialCampaignRoutes", "completedScope": graph.get("contentScope", graph.get("routingStatus", "Explicit source routes with unresolved input gates")), "sourceOrder": orders[chapter]})
            continue
        if chapter == "5":
            from v4_story_case5 import compile_chapter_five
            graph = compile_chapter_five(sources, freetime_graphs, tasks)
            bind_remaining_pictures(graph,sources,tasks)
            bind_climax_candidates(graph, sources, tasks)
            score_graph_v4(graph)
            dump(args.out / "chapters/5.json", graph)
            route_issues.append({"chapter": chapter, "kind": "partialCampaignRoutes", "completedScope": graph["contentScope"], "sourceOrder": orders[chapter]})
            continue
        if chapter == "6":
            from v4_story_case6 import compile_chapter_six
            graph = compile_chapter_six(sources, freetime_graphs, tasks)
            from v4_case2_6_picture_bindings import bind_pictures
            bind_pictures(graph,sources,tasks)
            score_graph_v4(graph)
            dump(args.out / "chapters/6.json", graph)
            route_issues.append({"chapter": chapter, "kind": "partialCampaignRoutes", "completedScope": graph.get("contentScope", graph.get("routingStatus", "Explicit source routes with unresolved input gates")), "sourceOrder": orders[chapter]})
            continue
        # Do not put old events after a V4 opening to disguise missing coverage.
        g = Graph(chapter)
        entry = f"v4:{chapter}:routing-required"
        g.add(entry, {"type": "gate", "reason": "Main source order exists, but required call ranges, state-dependent callbacks, original 66 tasks, investigation/freetime contracts are not yet all encoded.", "sourceOrder": orders[chapter]})
        dump(args.out / f"chapters/{chapter}.json", g.export(entry, routingStatus="blocked", mainSourceOrder=orders[chapter]))
        route_issues.append({"chapter": chapter, "kind": "campaignRoutes", "sourceOrder": orders[chapter]})
    manifest = {"schemaVersion": 1, "contentVersion": "v4", "campaignReady": False, "playableNarrativeChapters": ["P"], "authoredFreetimeMeetings": list(freetime), "runtimeIntegrationTested": False, "originalGameExecuted": False, "mainSourceOrder": orders, "sourceFiles": [{"file": s.name, "sha256": s.hash} for s in sources.values()], "tasks": {"total": len(tasks["tasks"]), "typedReady": sum(t["runtimeReady"] for t in tasks["tasks"].values()), "requiredBindings": sum(len(t["bindings"]) for t in tasks["tasks"].values()), "kinds": dict(Counter(t["kind"] for t in tasks["tasks"].values()))}, "sourceBlockCount": len(index["blocks"]), "remaining": route_issues, "readinessPolicy": "Do not mount this as the complete campaign until campaignReady is true. Indexed blocks are not executable streams. No legacy story fallback."}
    from v4_rhythm_bindings import bind_rhythm_tasks
    tasks['tasks']=bind_rhythm_tasks(tasks['tasks'])
    manifest['tasks']['typedReady']=sum(t['runtimeReady'] for t in tasks['tasks'].values())
    manifest['tasks']['requiredBindings']=sum(len(t['bindings']) for t in tasks['tasks'].values())
    # Rhythm charts are authored only after every chapter has contributed its
    # source waves. Refresh the stored input boundary readiness, not its route.
    from v4_investigation_placements import apply_placements
    chapters={chapter:load(args.out/f'chapters/{chapter}.json') for chapter in map(str,range(1,7))}
    placement_result=apply_placements(chapters)
    dump(args.out/'investigation_placements.json',placement_result)
    for chapter,graph in chapters.items():
        path=args.out/f'chapters/{chapter}.json'
        guard_unique_freetime_calls(graph)
        for node in graph['nodes'].values():
            if node.get('taskId') in tasks['tasks']:node['runtimeReady']=tasks['tasks'][node['taskId']]['runtimeReady']
        dump(path,graph)
    score_tasks_v4(tasks)
    dump(args.out / "tasks.json", tasks)
    manifest["tasks"]["compiledBaseline"] = [t["id"] for t in tasks["tasks"].values() if t.get("sourceKind") == "BASELINE"]
    from v4_native_tasks import convert_tasks
    catalogue = {}
    for chapter in map(str, range(1, 7)):
        catalogue.update(load(args.out / f"chapters/{chapter}.json").get("evidenceCatalog", {}))
    dump(args.out / "native_tasks.json", convert_tasks(tasks, catalogue))
    dump(args.out / "manifest.json", manifest)
    print(json.dumps({k: manifest[k] for k in ("contentVersion", "campaignReady", "playableNarrativeChapters", "tasks", "sourceBlockCount")}, ensure_ascii=False))
    return 2 if args.strict and not manifest["campaignReady"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
