"""Pure, fail-closed V4 task -> existing native trial-stage adapter.

No files, evidence ownership, answers or graph transitions are changed here.
The caller queues intro/wrong/success scripts and owns exact graph returns.
"""
from copy import deepcopy
import re


def _utf16_length(text):
    return len(text.encode('utf-16-le'))//2


def bounded_debate_lines(line,limit=48):
    """Split at actual sentence/word boundaries without cutting any target.

    Input starts are Python offsets from the adapter's freshly built utterance;
    output starts count UTF-16 units used by the Windows native text widget.
    Concatenating text fragments, including all spaces, restores the original.
    Unbreakable text/targets fail closed rather than becoming truncated output.
    """
    text=line['text'];protected=[]
    def span(weak):
        start=weak['start'];word=weak['word'];end=start+len(word)
        if text[start:end]!=word:raise ValueError(line['id']+': native target offset does not match utterance')
        if _utf16_length(word)>limit:raise ValueError(line['id']+': single target exceeds native48 UTF-16 units')
        protected.append((start,end));return start,end
    fields={key:span(line[key]) for key in ('weak','lieWeak') if line.get(key)}
    targets=[]
    for target in line.get('targets',[]):
        if 'weak' in target:interval=span(target['weak'])
        else:
            word=target['word'];start=target.get('start',text.index(word));interval=span({'start':start,'word':word})
        targets.append((target,interval))
    safe=lambda n:all(not a<n<b for a,b in protected)
    ranges=[];lo=0
    while _utf16_length(text[lo:])>limit:
        hi=lo;units=0
        while hi<len(text) and units+_utf16_length(text[hi])<=limit:
            units+=_utf16_length(text[hi]);hi+=1
        sentence=[lo+m.end() for m in re.finditer(r'[.!?。！？](?:[\"\u201d\u2019）)]*)(?:\s*)',text[lo:hi]) if safe(lo+m.end())]
        words=[lo+m.end() for m in re.finditer(r'\s+',text[lo:hi]) if safe(lo+m.end())]
        choices=sentence or words
        if not choices:raise ValueError(line['id']+': no source sentence/word boundary fits native48 without cutting a target')
        cut=max(choices)
        if cut<=lo:raise ValueError(line['id']+': empty native text fragment')
        ranges.append((lo,cut));lo=cut
    ranges.append((lo,len(text)));result=[]
    def adjusted(weak,start):
        return {**deepcopy(weak),'start':_utf16_length(text[start:weak['start']])}
    for part,(start,end) in enumerate(ranges):
        row={k:deepcopy(v) for k,v in line.items() if k not in ('weak','lieWeak','agree','targets')}
        row.update(text=text[start:end],kind='plain')
        if len(ranges)>1:
            row.update(id=line['id'] if part==0 else line['id']+':part:'+str(part+1),sourceLineId=line['id'],sourceTextSpan=[start,end],sourceTextSpanUnit='unicode-codepoints',splitPart=part+1,splitCount=len(ranges))
        for key,(a,b) in fields.items():
            if start<=a and b<=end:row[key]=adjusted(line[key],start)
        current=[]
        for target,(a,b) in targets:
            if not(start<=a and b<=end):continue
            copied=deepcopy(target)
            if 'weak' in copied:copied['weak']=adjusted(copied['weak'],start)
            else:copied['start']=_utf16_length(text[start:a])
            current.append(copied)
        if current:row['targets']=current
        if row.get('weak'):row['kind']='weak'
        elif line['kind']=='agree' and any(t['kind']=='agree' for t in current):row.update(kind='agree',agree=line['agree'])
        result.append(row)
    return result


def scripts(events):
    result=[]
    for e in events:
        if e.get('type') not in ('say','stage'):continue
        row={'type':e['type'],'source':deepcopy(e.get('source',{})),'presentation':deepcopy(e.get('presentation',{})),'eventId':e.get('id','')}
        if e['type']=='say':row.update(speaker=e.get('speaker',''),actor=e.get('actor',''),text=e['text'],mono=e.get('mono',False))
        else:row['direction']=e.get('direction','')
        result.append(row)
    return result


def convert_task(task, evidence_catalog=None):
    """Return {ready,stage,debate,queues,...}; never turn an unbound task ready."""
    evidence_catalog = evidence_catalog or {}
    result = {"taskId": task["id"], "ready": False, "bindings": deepcopy(task.get("bindings", [])), "source": deepcopy(task["source"])}
    if not task.get("runtimeReady"):
        result["reason"] = "Required source/asset/acquisition binding is unresolved. Do not substitute a menu or invent a correct location."
        return result
    kind = task["kind"]
    stage = {"id": task["id"], "kind": kind, "title": task.get("title", task.get("prompt", "")), "question": task.get("prompt", ""), "script": [], "presentation": deepcopy(task.get("presentation", {})), "v4": True}
    queues = {"intro": scripts(task.get("intro", [])), "wrong": scripts(task.get("wrong", [])), "success": scripts(task.get("success", [])), "wrongVariants": deepcopy(task.get("wrongVariants", []))}
    result.update(stage=stage, queues=queues, requiresEvidence=deepcopy(task.get("requiresEvidence", [])), scopeOnlyEvidence=task.get("scopeOnlyEvidence", False), outcomes=deepcopy(task.get("outcomes", {})), transformation=deepcopy(task.get("transformation", {})))

    def card(ident):
        local = next((e for e in task.get("evidenceOptions", []) if e["id"] == ident), None)
        c = local or evidence_catalog.get(ident, {})
        return {"id": ident, "name": c.get("name", c.get("label", ident)), "text": c.get("text", "")}

    def evidence_pool():
        pool = task.get("evidencePool", task.get("requiresEvidence", []))
        if pool == "actually-acquired-v4-cards-only":
            stage["filterOwnedEvidence"] = True
            return list(evidence_catalog) or list(task.get("requiresEvidence", []))
        return list(pool)

    if kind in ("person", "vote"):
        stage.update(answer=task["answer"], candidates=list(task["candidates"]), deadCandidatesSelectable=task.get("deadCandidatesSelectable", False), selectionRole=task.get("selectionRole", kind))
        if 'candidateOverrides' in task:stage['candidateOverrides']=deepcopy(task['candidateOverrides'])
        if kind == 'vote':
            for key in ('finalVote', 'authoredResult', 'voteCounts', 'voterCount', 'majorityRequired', 'otherIndividualBallotsPublic'):
                if key in task:stage[key]=deepcopy(task[key])
    elif kind == "lie":
        stage.update({k:deepcopy(task[k]) for k in ('fact','lie','holdToInvert','releaseRestoresFact','targetActor','factAttemptReturnsSameInput','cancelPausesScene','noHonestSuccessBypass','noOriginalTextDisplayed') if k in task})
        stage['answer']=task['answerEvidenceId']
        queues['trueCardAttempt']=scripts(task.get('trueCardAttempt',[]))
        stage['successInput']='held-transformed-card-fired-at-explicit-actor'
    elif kind == "choice":
        ids = [o["id"] for o in task["options"]]
        stage.update(options=[o["label"] for o in task["options"]], optionIds=ids, answer=ids.index(task["answer"]))
    elif kind == "reasoning":
        stage["questions"] = []
        for question in task["questions"]:
            q = deepcopy(question)
            q["optionIds"] = [o["id"] for o in q["options"]]
            q["options"] = [o["label"] for o in q["options"]]
            q["answer"] = q["options"][q["optionIds"].index(q["answer"])]
            stage["questions"].append(q)
        stage["retryPolicy"] = "currentLinkOnly"
    elif kind == "anagram":
        stage.update(answer=task["answer"], answerGlyphs=list(task["answerGlyphs"]), mechanic=deepcopy(task["mechanic"]), distractorDescription=task.get("distractorDescription", ""))
    elif kind == "bullet":
        stage.update(answer=task["answerEvidenceId"], options=[card(e) for e in evidence_pool()])
    elif kind in ("nonstop", "panic", "showdown"):
        answer = task["answerEvidenceId"]
        pool = [e["id"] for e in task.get("evidenceOptions", [])] or evidence_pool()
        if answer not in pool:
            raise ValueError(task["id"] + ": answer not offered; evidence cannot be silently granted")
        lines = []
        for event in task["lines"]:
            text = event["text"].replace("【", "").replace("】", "").replace("〔", "").replace("〕", "")
            line = {"id": event["id"], "speaker": event["speaker"], "actor": event["actor"], "text": text, "kind": "plain", "source": deepcopy(event["source"])}
            native_targets = []
            for target in task.get("targets", []):
                if target["lineId"] != event["id"]:
                    continue
                if target["word"] not in text:
                    raise ValueError(task["id"] + ": target is not in the actual utterance")
                if target["verdict"] == "lie":
                    transformed_answer=task.get("transformation",{}).get("sourceEvidenceId",answer)
                    weak={"start":text.index(target["word"]),"word":target["word"],"answer":transformed_answer,"lie":True,"lieText":task.get("transformation",{}).get("lieLabel","")}
                    for key in ('transformedJudgment','requireAgreement'):
                        if key in target or key in task.get('transformation',{}):
                            weak[key]=target.get(key,task.get('transformation',{}).get(key))
                    native_targets.append({"kind":"weak","weak":weak,"outcome":"B"})
                    line["lieWeak"] = weak
                elif target["verdict"] == "agree":
                    line.update(kind="agree", agree=answer)
                    native_targets.append({"kind":"agree","word":target["word"],"answer":answer})
                else:
                    line.update(kind="weak", weak={"start": text.index(target["word"]), "word": target["word"], "answer": answer, "lie": False})
                    native_targets.append({"kind":"weak","weak":deepcopy(line["weak"]),"outcome":"A"})
            if native_targets:line["targets"]=native_targets
            if line.get("weak") and task.get("transformation") and not line.get("lieWeak"):
                line["lieWeak"]={**line["weak"],"answer":task["transformation"]["sourceEvidenceId"],"lie":True,"lieText":task["transformation"]["lieLabel"]}
            lines.extend(bounded_debate_lines(line))
        stage["lines"] = lines
        stage["options"] = [card(e) for e in pool]
        if kind == "showdown":
            target = task["targets"][0]
            stage.update(opponent=target["actor"], blade={"word": target["word"], "answer": answer})
        else:
            result["debate"] = {"id": task["id"], "kind": kind, "title": stage["title"], "lines": lines, "bullets": stage["options"], "lanes": deepcopy(task.get("lanes", []))}
    elif kind == "scrum":
        stage.update(pairs=deepcopy(task["pairs"]), teams=deepcopy(task["teams"]))
        names={"mio":"미오","rei":"레이","sora":"소라","ken":"켄","nana":"나나","riku":"리쿠","akari":"아카리","yuu":"유우","koto":"코토","satsuki":"사츠키","taiga":"타이가","rin":"린","sho":"쇼","ai":"아이","haruka":"하루카","kaede":"카에데"}
        for pair in stage["pairs"]:
            if not pair.get("responseKeyword", "").strip():
                raise ValueError(f"{task['id']}: empty Scrum response keyword")
            pair["themActor"],pair["usActor"]=pair["them"],pair["us"]
            pair["them"],pair["us"]=names.get(pair["them"],pair["them"]),names.get(pair["us"],pair["us"])
    elif kind in ("spot", "mindmine", "climax", "armament"):
        # Bound picture/phrase contracts are preserved verbatim; native host
        # must support these exact fields instead of legacy generic options.
        stage.update({k: deepcopy(v) for k, v in task.items() if k not in ("intro", "wrong", "success", "return", "source", "id", "runtimeReady")})
        stage["script"] = []
        if kind == "armament":
            stage["lines"] = [e["text"] for e in task["lines"]]
            if task['id']=='T1-AA-01':
                stage['finalWrongVariantByOption']={'보고서만':'paper-or-missed-hand','놓친 손을':'paper-or-missed-hand','닿게 하지 않았다':'no-contact','입실 전부터':'wrong-order'}
                stage['finalWrongVariantSource']={'file':'163_1장_재판_형식별_연속대본.md','lines':[462,466,470],'policy':'Exact wrong-fragment headings, not an inferred character reaction.'}
            elif task['id']=='T2-AA-01':
                stage['finalWrongVariantByOption']={'함 안의 추가':'wrong-tool','내용을 알린 뒤':'carriers-knew'}
                stage['finalWrongVariantSource']={'file':'164_2장_재판_형식별_연속대본.md','lines':[495,497,498],'policy':'Only explicit wrong-tool/knowledge fragments mapped. Other fragments/order errors use the general wrong contract, not guessed character speech.'}
        if kind == "mindmine":
            stage["sourceMechanic"] = deepcopy(task.get("mechanic", {}))
            stage["mechanic"] = {"adjacency":4,"removeConnectedSameColorGroup":True,"recolorBoundaryOnce":True,"gravity":False,"thenSelectActuallyExposedRegion":True}
            stage["mechanicsResolvedBy"] = "REA: four-connected group removal and one boundary-color rotation; source prose gravity staging is preserved only as sourceMechanic, not executable physics."
    else:
        result["reason"] = "No explicit native adapter for task kind " + kind
        return result
    result["ready"] = True
    return result


def convert_tasks(tasks, evidence_catalog=None):
    return {"schemaVersion": 1, "contentVersion": "v4", "tasks": {ident: convert_task(task, evidence_catalog) for ident, task in tasks["tasks"].items()}, "policy": "Queues are conditional, not a serial story. Intro precedes input once; wrong pauses and returns to the same task state; success precedes the callsite graph success edge exactly once. Never auto-play wrongVariants or both outcomes."}
