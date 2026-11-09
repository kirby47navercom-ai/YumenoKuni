"""Read original PNG alpha into gameplay masks; never edit bitmap pixels."""
import hashlib
import json
import shutil
import struct
import math
import argparse
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / 'art/v4_production/mine_objects_20261104'
GENERATED = Path('C:/Users/kirby/.codex/generated_images/01a19fd4-cd3f-7123-91ea-3a9194054780')
SPECS = [
    ('microphone_base', 'exec-54836ffb-d823-4c91-b97b-e0b56e453bbb.png', 'heavy-detached-base', [.06, .18, .46, .5575757576]),
    ('covering_cloth', 'exec-1a24cabd-3797-4f19-9acd-d3d7289c981a.png', 'covering-cloth', [.56, .30, .40, .3636363636]),
]


def rotated_footprints(rows, width, height, size):
    """Read-only alpha runs -> conservative rotated unit-cell intersections."""
    output = []
    for index in range(8):
        angle = (index-4)*math.pi/4
        co, si = math.cos(angle), math.sin(angle)
        cells = set()
        for y, row in enumerate(rows):
            for span in row.split(',') if row else []:
                a, b = map(int, span.split(':'))
                corners = []
                for px, py in [(a,y),(b,y),(b,y+1),(a,y+1)]:
                    x0 = (px-width/2)*size/max(width,height)
                    y0 = (py-height/2)*size/max(width,height)
                    corners.append((x0*co-y0*si+.5, x0*si+y0*co+.5))
                # Separating-axis test for an alpha-run quad and each unit cell.
                axes = [(1,0),(0,1),(co,si),(-si,co)]
                projected = [(min(x*ax+y*ay for x,y in corners), max(x*ax+y*ay for x,y in corners)) for ax,ay in axes]
                for gy in range(math.floor(min(y for x,y in corners)), math.floor(max(y for x,y in corners))+1):
                    for gx in range(math.floor(min(x for x,y in corners)), math.floor(max(x for x,y in corners))+1):
                        for (ax,ay),(low,high) in zip(axes,projected):
                            center = (gx+.5)*ax+(gy+.5)*ay
                            radius = (abs(ax)+abs(ay))*.5
                            if high < center-radius-1e-8 or low > center+radius+1e-8:
                                break
                        else:
                            cells.add((gx,gy))
        assert cells
        output.append({'index':index,'angle':(index-4)*45,'weight':1 if index%2==0 else 2,'cells':sorted(cells)})
    return output


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--task',default='T2-MM-A02')
    task=parser.parse_args().task
    approved={}
    specs,reference,mask_file,selection_file=SPECS,'art/inspection_v4/delivery/microphone_base_forensic_r2.webp','0.json','selection.json'
    if task!='T2-MM-A02':
        approved=json.loads((BANK/'reviewed-additions.json').read_text(encoding='utf-8'))[task]
        for ref in approved.get('review',{}).get('sourceStatements',[]):
            text=(ROOT/'docs/design/rewrite_v4'/ref['file']).read_text(encoding='utf-8-sig')
            assert hashlib.sha256(text.encode()).hexdigest()==ref['sha256']
            assert ref['quote'] in text.splitlines()[ref['line']-1]
        specs=[(x['id'],x['source'],x['regionId'],x['rect']) for x in approved['objects']]
        reference,mask_file,selection_file=approved['reference'],approved['maskFile'],approved['selectionFile']
    BANK.mkdir(parents=True, exist_ok=True)
    objects, masks = [], {}
    for name, filename, region, rect in specs:
        original = BANK / (name + '_original.png')
        if not original.exists():
            shutil.copyfile(GENERATED / filename, original)
        encoded = original.read_bytes()
        assert encoded[:8] == b'\x89PNG\r\n\x1a\n'
        chunks, offset = [encoded[:8]], 8
        while offset < len(encoded):
            size = struct.unpack_from('>I', encoded, offset)[0]
            end = offset + size + 12
            assert end <= len(encoded)
            if encoded[offset+4:offset+8] != b'caBX':
                chunks.append(encoded[offset:end])
            offset = end
        runtime = BANK / (name + '.png')
        runtime.write_bytes(b''.join(chunks))
        image = Image.open(original)
        assert image.mode == 'RGBA'
        width, height = image.size
        alpha = image.getchannel('A').tobytes()
        rows, footprints = [], {str(w): set() for w in (18, 20, 22)}
        rects = {str(w): [((rect[0]+rect[2]/2-.5)*20/w+.5)-rect[2]*20/w/2, rect[1], rect[2]*20/w, rect[3]] for w in (18,20,22)}
        for y in range(height):
            spans, start = [], -1
            for x in range(width + 1):
                opaque = x < width and alpha[y*width+x] > 127
                if opaque and start < 0:
                    start = x
                elif not opaque and start >= 0:
                    spans.append((start, x))
                    for columns, cells in footprints.items():
                        count = int(columns)
                        actual_rect = rects[columns]
                        row = int((actual_rect[1] + (y+.5)/height*actual_rect[3])*11)
                        left = int((actual_rect[0] + start/width*actual_rect[2])*count)
                        right = int((actual_rect[0] + (x-1)/width*actual_rect[2])*count)
                        assert 0 <= row < 11 and 0 <= left <= right < count
                        cells.update(row*count+c for c in range(left, right+1))
                    start = -1
            rows.append(','.join(f'{a}:{b}' for a, b in spans))
        assert any(rows) and any(not row for row in rows)
        size = max(rect[2]*20,rect[3]*11)
        masks[name] = {'width': width, 'height': height, 'rows': rows, 'alphaThreshold': 127,
                       'rotations':rotated_footprints(rows,width,height,size)}
        objects.append({'id': name, 'regionId': region, 'texture': f'Assets/Art/mine_objects/{name}.png', 'maskKey': name,
                        'maskAsset': 'Assets/Data/mine_objects/'+mask_file, 'rect': rect, 'rectByWidth': rects, 'rotation': 0,'sizeCells':size,
                        'cellsByWidth': {w: sorted(cells) for w, cells in footprints.items()},
                        'original': original.relative_to(ROOT).as_posix(), 'runtime': runtime.relative_to(ROOT).as_posix(),
                        'sourceSHA256': hashlib.sha256(encoded).hexdigest(),
                        'runtimeSHA256': hashlib.sha256(runtime.read_bytes()).hexdigest()})
    mask_bytes = json.dumps({'objects': masks}, separators=(',', ':')).encode()
    assert len(mask_bytes) < 262144 and sum(len(m['rows']) for m in masks.values()) < 9000
    (BANK / ('mask_'+mask_file)).write_bytes(mask_bytes)
    manifest = {'taskId': task, 'objects': objects, 'reference': reference,
                'method': 'Built-in imagegen redrew the reviewed existing physical objects (or reused an explicitly reviewed matching sprite); direct visual review. Original PNGs preserved, only caBX metadata omitted in runtime copies. Alpha is read into RLE geometry, no bitmap editing.',
                'visualReview': {'sameGeometryAndMaterials': True, 'noNewClue': True, 'independentObjects': True, 'runtime': False},
                'limits': ['Only the named task; inspect banks.json for total reviewed bindings.', 'Eight weighted angles use our conservative alpha-run cell intersection; original 20x20 image-mask quantization and random seeds are not pixel-identical.']}
    if approved.get('review',{}).get('scope'):
        manifest['reviewedScope']=approved['review']['scope']
        manifest['sourceStatements']=approved['review'].get('sourceStatements',[])
        manifest['visualReview']['sameGeometryAndMaterials']=False
        manifest['visualReview']['sourceMeaningAndMaterialsReviewed']=True
        if task=='T2-MM-01':
            manifest['method']='Built-in imagegen independent illustrative components of the source-confirmed connection diagram; not exact historical hardware geometry. Original PNGs and compressed pixel chunks preserved; caBX metadata omitted only.'
            manifest['visualReview']['sameGeometryAndMaterials']=False
            manifest['visualReview']['sourceTopologyPreserved']=True
            manifest['limits'].append('Hardware silhouette, connector standard and knob count are illustrative. No live power/card state, actor, time or new technical evidence follows from the drawing.')
    if approved.get('mergeCorrectRegions'):
        manifest['mergeCorrectRegions'] = approved['mergeCorrectRegions']
        manifest['comparisonLabel'] = approved['comparisonLabel']
        manifest['limits'].append('The source requires one comparison unit containing both joins. Its four old partial contours share the original canonical answer ID; partial joins are not independently sufficient answers.')
    (BANK / selection_file).write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'selectedObjects': len(objects), 'maskBytes': len(mask_bytes), 'rasterPixelsEdited': False}))


if __name__ == '__main__':
    main()
