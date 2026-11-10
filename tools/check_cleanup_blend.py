"""Blender background: repair only image file links after the cleanup move."""
from pathlib import Path
import json, bpy

R = Path(__file__).resolve().parents[1]
Q = R / '_삭제대기_2026-10-29'
plan = json.loads((Q / 'move-plan.json').read_text(encoding='utf8'))
moves = {a['source']: a['destination'] for a in plan['files']}
mapping = dict(moves)
for a in plan['files']:
    if a['category'] == 'A_pixel_identical_png':
        webp = str(Path(a['source']).with_suffix('.webp')).replace('\\', '/')
        mapping[a['source']] = moves.get(webp, webp)
report = []
for p in sorted((R / 'art/space_v4').rglob('*.blend')):
    bpy.ops.wm.open_mainfile(filepath=str(p))
    changes, missing = [], []
    for im in bpy.data.images:
        if not im.filepath or im.source != 'FILE':
            continue
        src = Path(bpy.path.abspath(im.filepath)).resolve()
        if src.is_relative_to(R):
            rel = src.relative_to(R).as_posix()
            if rel in mapping:
                target = R / mapping[rel]
                assert target.is_file(), target
                im.filepath = bpy.path.relpath(str(target), start=str(p.parent))
                changes.append([rel, mapping[rel]])
        if not Path(bpy.path.abspath(im.filepath)).is_file() and not im.packed_file:
            missing.append(im.filepath)
    if changes:
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(p))
    report.append({'file': p.relative_to(R).as_posix(), 'changed_image_links': changes, 'missing_unpacked': missing})
(Q / 'blend-references.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
assert not any(x['missing_unpacked'] for x in report), 'Missing Blender image file links; see report'
print('BLEND REFERENCES PASS', len(report), 'files;', sum(len(x['changed_image_links']) for x in report), 'links repaired')
