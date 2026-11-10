"""Decode V3 WRD commands, preserving offsets, raw arguments and unknowns.

Opcode names/argument categories are format metadata researched against
CaptainSwag101/DRV3-Sharp commit 3155b11f225e2223dcdd4cc8555f0e051808e931,
WrdData.cs and WrdSerializer.cs. Categories are not proven runtime semantics.
0=parameter, 1=unsigned immediate, 2=dialogue ID, 3=label.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct

# Ordered opcode IDs. Punctuation is significant in the game's text commands.
_SPEC = '''FLG:00 IFF:000* WAK:000 IFW:001* SWI:0 CAS:1 MPF:000 SPW:
MOD:0000 HUM:0 CHK:0 KTD:00 CLR: RET: KNM:00000 CAP: FIL:00 END:
SUB:00 RTN: LAB:3 JMP:0 MOV:00 FLS:0000 FLM:000000 VOI:00 BGM:000
SE_:00 JIN:00 CHN:0 VIB:000 FDS:000 FLA: LIG:010 CHR:00000 BGD:0000
CUT:00 ADF:00000 PAL: MAP:000 OBJ:000 BUL:00000000 CRF:0000000
CAM:00000 KWM:0 ARE:000 KEY:00 WIN:0000 MSC: CSM: PST:00000
KNS:01111 FON:11 BGO:00000 LOG: SPT:0 CDV:0000000000 SZM:0000
PVI:0 EXP:0 MTA:0 MVP:000 POS:00000 ICO:0000 EAI:0000000000
COL:000 CFP:000000000 CLT=:0 R=: PAD=:0 LOC:2 BTN: ENT: CED: LBN:1 JMN:1'''
OPCODES = []
for _item in _SPEC.split():
    _name, _types = _item.split(':')
    OPCODES.append(dict(name=_name, types=[int(x) for x in _types.rstrip('*')], variable=_types.endswith('*')))

# Distinct shipped table: minigame/rsc/script/label.spc/command_label.dat,
# IDs0..103. Extended argument schemas remain unknown; raw values and bounded
# parameter candidates are retained without pretending the candidate is typed.
_RSC_NAMES = '''FLG IFF WAK IFW SWI CAS CLR RET FIL END SUB RTN LAB JMP MOV FLS
FLM VOI BGM SE_ JIN VIB FDS FLA ADF BUL CRF MSC FON CLT= R= PAD= ICON=
SUCCESS_MODE SELECT CHOICE WND_BG_SET WND_BG_FADE WND_BG_DELETE WND_BG_WAIT_LOADED
WND_CHAR_SET WND_CHAR_WAIT_LOADED WND_ITEM_SET WND_ITEM_WAIT_LOADED WND_OBJ_DELETE
WND_OBJ_DELETE_ALL WND_OBJ_SET_PRIOR WND_ACTION_MOVE WND_ACTION_ALPHA WND_ACTION_ROTATE
WND_ACTION_SCALE WND_ACTION_SE WND_ACTION_PATTERN WND_ACTION_PATTERN_FRAME WND_ACTION_WAIT
WND_ACTION_REPEAT WND_ACTION_SEQUENCE WND_ACTION_SPAWN WND_ACTION_START WND_ACTION_STOP
WND_ACTION_RESET WND_EMOTION_SET WND_EMOTION_CHANGE WND_EMOTION_RAND_PUSH
WND_EMOTION_RAND_START WND_EMOTION_RAND_STOP WND_EMOTION_DELETE WND_EMOTION_WAIT_LOADED
ADV_CHOICE_MODE ADV_BG_SET ADV_BG_FADE ADV_BG_DELETE ADV_CHAR_LOAD ADV_CHAR_UNLOAD
ADV_CHAR_WAIT_LOADED ADV_CHAR_SET ADV_CHAR_SHOW ADV_CHAR_MOVE ADV_CHAR_CHANGE
ADV_CHAR_XCHANGE ADV_CHAR_FADE ADV_CHAR_SET_PRIOR ADV_CHAR_DELETE ADV_CHAR_NAME
SUCCESS_PARAM_UP SUCCESS_OBTAIN_CARD SUCCESS_OBTAIN_FRAGMENT ADV_ACTOR_SET LOC BTN
ENT CED LBN JMN SUCCESS_OPEN_SKILL_WINDOW SUCCESS_BTL_SET_PARTY SUCCESS_BTL_SET_MONSTER
SUCCESS_PARAM_GET SUCCESS_COURSE_GET ADV_VIB ADV_ADF TROPHY_UNLOCK ADV_BG_SET_FIXED
UNLOCK_RPG_MODE'''.split()
_BY_NAME = {info['name']: info for info in OPCODES}
RSC_OPCODES = [dict(_BY_NAME[name]) if name in _BY_NAME else
               dict(name=name, types=[], variable=True, unknown_schema=True)
               for name in _RSC_NAMES]


def _read_strings(data, cursor, count, encoding='utf-8', terminator=b'\0'):
    values = []
    for _ in range(count):
        start = cursor
        length, shift = 0, 0
        while True:
            if cursor >= len(data) or shift > 28:
                raise ValueError('invalid WRD 7-bit string length')
            b = data[cursor]
            cursor += 1
            length |= (b & 127) << shift
            if b < 128:
                break
            shift += 7
        end = cursor + length
        if end + len(terminator) > len(data) or data[end:end + len(terminator)] != terminator:
            raise ValueError('invalid WRD length-prefixed string terminator')
        values.append(dict(offset=start, data_offset=cursor, text=data[cursor:end].decode(encoding)))
        cursor = end + len(terminator)
    return values


def parse(data, external_strings=None, dialect='main'):
    if dialect not in ('main', 'rsc'):
        raise ValueError('unknown WRD dialect')
    opcode_table = RSC_OPCODES if dialect == 'rsc' else OPCODES
    if len(data) < 32:
        raise ValueError('WRD header truncated')
    strings, labels, parameters, branches, unknown, bp, lp, ln, pp, sp = struct.unpack_from('<4H6I', data)
    if not 32 <= bp <= lp <= ln <= pp <= len(data):
        raise ValueError('WRD section pointers invalid')
    if bp + branches * 4 > lp or lp + labels * 2 > ln:
        raise ValueError('WRD offset tables truncated')
    label_values = _read_strings(data, ln, labels)
    parameter_values = _read_strings(data, pp, parameters)
    internal = _read_strings(data, sp, strings, 'utf-16le', b'\0\0') if sp else None
    commands, warnings = [], []
    cursor = 32
    while cursor + 1 < bp:
        start = cursor
        if data[cursor] != 0x70:
            raise ValueError(f'WRD opcode marker missing at {cursor:#x}')
        code = data[cursor + 1]
        cursor += 2
        args = []
        while cursor + 1 < bp and data[cursor] != 0x70:
            args.append(struct.unpack_from('>H', data, cursor)[0])
            cursor += 2
        info = opcode_table[code] if code < len(opcode_table) else None
        name = info['name'] if info else f'UNKNOWN_{code:02X}'
        if info is None:
            warnings.append(dict(offset=start, kind='unknown_opcode', opcode=code))
        elif len(args) < len(info['types']) or (len(args) != len(info['types']) and not info['variable']):
            warnings.append(dict(offset=start, kind='argument_count', opcode=name,
                                 expected=len(info['types']), actual=len(args)))
        refs = []
        for index, value in enumerate(args):
            # Variable commands repeat their complete argument-type group.
            kind = info['types'][index % len(info['types'])] if info and info['types'] else None
            if name == 'IFW':
                # Native0x140467450 consumes lhs/operator/s16 then an optional
                # connector before the next clause; it is not a 3-item cycle.
                kind = 1 if index % 4 == 2 else 0
            item = dict(value=value, kind=kind)
            if name == 'IFW' and kind == 1:
                item['signed_value'] = value if value < 32768 else value - 65536
            if info and info.get('unknown_schema'):
                item['schema'] = 'unverified RSC extension'
                if value < len(parameter_values):
                    item['parameter_candidate'] = parameter_values[value]['text']
                    item['parameter_offset'] = parameter_values[value]['offset']
            source = parameter_values if kind == 0 else label_values if kind == 3 else internal if kind == 2 else None
            if kind == 2 and source is None and external_strings is not None:
                source = external_strings
            if source is not None:
                if kind == 2 and external_strings is source:
                    candidates = [s for s in source if s['id'] == value]
                    if candidates:
                        item['resolved'] = candidates[0]['text']
                        item['resolution'] = 'STX string ID (runtime lookup unverified)'
                        item['string_offsets'] = [s['offset'] for s in candidates]
                        if len({s['text'] for s in candidates}) > 1:
                            item['ambiguous'] = True
                            warnings.append(dict(offset=start, kind='ambiguous_string_id', value=value))
                    else:
                        item['unresolved'] = True
                        warnings.append(dict(offset=start, kind='reference_bounds', argument=index, value=value, category=kind))
                elif value < len(source):
                    item['resolved'] = source[value]['text']
                else:
                    item['unresolved'] = True
                    warnings.append(dict(offset=start, kind='reference_bounds', argument=index, value=value, category=kind))
            refs.append(item)
        commands.append(dict(offset=start, relative_offset=start - 32, size=cursor - start,
                             opcode=code, name=name, args=args, arguments=refs))
    if cursor != bp:
        warnings.append(dict(offset=cursor, kind='trailing_command_byte', size=bp-cursor))
    return dict(format='WRD', dialect=dialect, header=dict(string_count=strings, label_count=labels,
                parameter_count=parameters, branch_count=branches, unknown=unknown,
                branch_offsets=bp, label_offsets=lp, label_names=ln, parameters=pp, strings=sp),
                parameters=parameter_values, labels=label_values, internal_strings=internal,
                branches=[dict(index=i, relative_offset=o, offset=32+o) for i,o in struct.iter_unpack('<HH', data[bp:bp+branches*4])],
                label_offsets=[dict(relative_offset=o[0], offset=32+o[0]) for o in struct.iter_unpack('<H', data[lp:lp+labels*2])],
                commands=commands, counts=dict(Counter(c['name'] for c in commands)), warnings=warnings)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--stx', type=Path, help='matching external dialogue table (optional)')
    parser.add_argument('--dialect', choices=('main', 'rsc'), default='main')
    args = parser.parse_args()
    external = None
    if args.stx:
        import stx
        external = stx.parse(args.stx.read_bytes())['tables'][0]['strings']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(parse(args.source.read_bytes(), external, args.dialect), ensure_ascii=False, indent=2), encoding='utf-8')
