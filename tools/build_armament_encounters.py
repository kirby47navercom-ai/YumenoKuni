"""Compile the game's authored six encounters; never rewrite the V3 reference bank."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/armament_encounters.json'
WORK = ROOT / 'Game/Saved/armament-readable-20261107'
KEYS = 'wdsa'
KINDS = {'tap': 0, 'hold': 1, 'mash': 2}


def f(value):
    text = format(value, '.9g')
    return text + ('f' if '.' in text or 'e' in text else '.0f')


def overlap(a, b, shift=0):
    return max(a['spawn'], b['spawn'] + shift) < min(a['end'], b['end'] + shift) - 1e-6


def chart(encounter, phase, phase_index, patterns, spans):
    beat = 60 / phase['bpm']
    lead = phase['lead']
    cycle = sum(spans[name] for name in phase['bars']) * beat
    notes = []
    for bar, name in enumerate(phase['bars']):
        start = sum(spans[n] for n in phase['bars'][:bar])
        for event in patterns[name]:
            at, key = event[:2]
            kind = event[2] if len(event) > 2 else 'tap'
            strength = event[3] if len(event) > 3 else 0
            assert 0 <= at < spans[name] and key in KEYS and kind in KINDS
            target = lead + (start + at) * beat
            hold = round(strength * beat * 60) if kind == 'hold' else 0
            notes.append(dict(row=len(notes), key=KEYS.index(key), type=KINDS[kind], hold=hold,
                              power=int(strength) if kind == 'mash' else 0, beat=start + at,
                              pattern=name, spawn=target-lead, target=target,
                              end=target+hold/60+(.75 if kind == 'hold' else .4 if kind == 'mash' else 19/60)+.45))
    notes.sort(key=lambda n: n['spawn'])
    assert len({n['target'] for n in notes}) == len(notes), 'Do not hide chords in a single-key prompt'
    for row, note in enumerate(notes):
        note['row'] = row
        # No required press may reuse a still-held key, including across the loop.
        for other in notes:
            for turn in [-1, 0, 1]:
                at = other['target'] + cycle * turn
                if note['hold'] and other['key'] == note['key'] and note['target'] + .001 < at < note['target'] + note['hold']/60 - .001:
                    raise AssertionError(('Held-key collision', encounter['chapter'], phase_index, note, other))
                # Mash has its own protected input window; no competing tap/hold.
                if note['type'] == 2 and other is not note and abs(at-note['target']) < .45:
                    raise AssertionError(('Mash window collision', note, other))
    # One fixed input focus; runtime shows only a primary, held anchor and one preview.
    for note in notes:
        note['lane'] = 0
        note['x'], note['y'] = 1040, 660
    edges = []
    for turn in [-1, 0, 1, 2]:
        for n in notes:
            edges += [(n['spawn']+turn*cycle, 1), (n['end']+turn*cycle, -1)]
    count = peak = 0
    for time, delta in sorted(edges):
        count += delta
        if 0 <= time < 2*cycle:
            peak = max(peak, count)
    assert peak <= 12, (encounter['chapter'], phase_index, peak)
    assert all(n['target']-n['spawn'] >= 1.3 for n in notes)
    onsets = sorted(n['target'] for n in notes)
    gaps = [b-a for a,b in zip(onsets,onsets[1:])] + [onsets[0]+cycle-onsets[-1]]
    assert min(gaps)/1.12 >= .45, ('Insufficient human read/reaction interval', encounter['chapter'], phase_index)
    for n in notes:
        if not n['hold']: continue
        assert not any(other['hold'] and other is not n and any(n['target'] < other['target']+turn*cycle < n['target']+n['hold']/60-.001 for turn in [-1,0,1]) for other in notes), 'Do not require simultaneous holds'
    return dict(bpm=phase['bpm'], cycle=cycle, notes=notes, peak=peak, minimumPressGap=min(gaps),
                minimumReadSecondsHard=min(gaps)/1.12, moves=[(0,0)])



def main():
    raw = SOURCE.read_bytes()
    data = json.loads(raw)
    assert [e['chapter'] for e in data['encounters']] == list(range(1, 7))
    assert [len(e['phases']) for e in data['encounters']] == [3,3,3,3,3,4]
    output = ['#pragma once', '#include "ArmamentChartsV4.hpp"', '#include <string>',
              '// Own authored encounter arrangements; original V3 reference charts remain unchanged.',
              'namespace armencounters {', 'inline const std::array<std::vector<armcharts::Chart>,6> chapters=[] {', ' std::array<std::vector<armcharts::Chart>,6> out{{']
    receipt = dict(schema=data['schema'], source=str(SOURCE.relative_to(ROOT)),
                   sha256=hashlib.sha256(raw).hexdigest(), provenance=data['provenance'], encounters=[])
    fingerprints = set()
    for encounter in data['encounters']:
        phases = [chart(encounter, p, i, data['patterns'], data['pattern_beats']) for i, p in enumerate(encounter['phases'])]
        fingerprint = hashlib.sha256(json.dumps(phases, sort_keys=True).encode()).hexdigest()
        assert fingerprint not in fingerprints
        fingerprints.add(fingerprint)
        output.append(' {')
        for p in phases:
            output.append('  {'+f(p['cycle'])+', {')
            for n in p['notes']:
                values = [str(n[k]) for k in ['row','key','type','hold','power']]+['-1']
                values += [f(n[k]) for k in ['spawn','target','x','y']]
                values += ['.4f','1.0f',f(-8 if n['row']%2==0 else 8),'0.0f','.5f','1.0f']
                output.append('   {'+','.join(values)+'},')
            output.append('  }, {'+','.join('{'+f(t)+','+str(m)+'}' for t,m in p['moves'])+'}},')
        output.append(' },')
        receipt['encounters'].append(dict(chapter=encounter['chapter'], identity=encounter['identity'],
                                           mechanic=encounter['mechanic'], fingerprint=fingerprint, phases=phases))
    output += ['}};']
    output += '// UI-only ordinal mapping: authored phrases/counts/timing are retained; this is not an original chart reconstruction.\n for(std::size_t chapter=0;chapter<out.size();++chapter)for(std::size_t phase=0;phase<out[chapter].size();++phase){\n  const auto& source=armcharts::chapters.at(chapter).at(phase).notes;\n  for(auto& note:out[chapter][phase].notes){const auto& visual=source.at(std::size_t(note.row)%source.size());\n   note.x=visual.x;note.y=visual.y;note.startScale=visual.startScale;note.endScale=visual.endScale;\n   note.startRotation=visual.startRotation;note.endRotation=visual.endRotation;\n   note.startTextScale=visual.startTextScale;note.endTextScale=visual.endTextScale;\n  }\n }\n return out;\n}();'.splitlines()
    output += ['inline const std::array<std::vector<float>,6> bpm{{']
    output += [' {'+','.join(f(p['bpm']) for p in e['phases'])+'},' for e in data['encounters']]
    output += ['}};', '} // namespace armencounters', '']
    header=ROOT/'Game/Source/ArmamentEncountersV4.hpp'
    header.write_text('\n'.join(output), encoding='utf-8')
    receipt['headerSha256']=hashlib.sha256(header.read_bytes()).hexdigest()
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK/'generated-encounters.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(encounters=6,phases=19,notes=sum(len(p['notes']) for e in receipt['encounters'] for p in e['phases']),
                         maximumVisible=max(p['peak'] for e in receipt['encounters'] for p in e['phases']))))


if __name__ == '__main__':
    main()
