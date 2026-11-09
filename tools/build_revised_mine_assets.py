"""Build the chapter-one comparison boards from existing art and diagrams."""

import json
from pathlib import Path

from prepare_mine_object_bank import rotated_footprints


ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / 'art/v4_production/mine_objects_20261104'
ART = 'Assets/Art/revision_mine/'
MASK = 'Assets/Data/v4_story/revision/mine/door-comparison.json'
PAPER_MASK = 'Assets/Data/v4_story/revision/mine/paper-comparison.json'
RING_MASK = 'Assets/Data/v4_story/revision/mine/theatre-ring.json'


def authored_object(task, region, label):
    selection = json.loads((BANK / f'selection_{task}.json').read_text(encoding='utf8'))
    source = next(row for row in selection['objects'] if row['regionId'] == region)
    return {
        'id': source['id'], 'regionId': label, 'texture': source['texture'].replace('.png', '.webp'),
        'maskKey': source['maskKey'], 'maskAsset': source['maskAsset'], 'sizeCells': source['sizeCells'],
        'hintLocal': 'Assets/Art/ui/mine-objects/' + source['id'] + '_local_hint.svg',
    }


def diagram(name, width, height, spans, shapes, size, mask_asset=MASK):
    rows = [','.join(f'{start}:{end}' for start, end in spans(y)) for y in range(height)]
    mask = {'width': width, 'height': height, 'rows': rows,
            'rotations': rotated_footprints(rows, width, height, size)}
    wrapper = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" preserveAspectRatio="none">'
    hint = ''.join(f'<rect x="{start}" y="{y}" width="{end-start}" height="1"/>'
                   for y in range(height) for start, end in spans(y))
    texture = ART + name + '.svg'
    outline = ART + name + '-hint.svg'
    files = {texture: wrapper + shapes + '</svg>',
             outline: wrapper + '<g fill="#fff4bd" opacity=".42">' + hint + '</g></svg>'}
    return {'id': name, 'regionId': name, 'texture': texture, 'maskKey': name, 'maskAsset': mask_asset,
            'sizeCells': size, 'hintLocal': outline}, mask, files


def inspection_latch_section():
    """Authored explanatory section: generated walls do not touch the old latch."""
    return {ART+'inspection-latch-section.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 896 506">
<defs><pattern id="wall" width="14" height="14" patternUnits="userSpaceOnUse"><path d="M0 14L14 0" stroke="#a18a73" stroke-width="2"/></pattern><linearGradient id="metal" x2="0" y2="1"><stop stop-color="#d2d5d7"/><stop offset="1" stop-color="#626b78"/></linearGradient></defs>
<path fill="#211e2c" d="M0 0h896v506H0z"/><path fill="#695365" d="M30 26h836v447H30z"/>
<path fill="#dbc5a1" d="M40 34h225v145H40z"/><path fill="url(#wall)" d="M40 34h225v145H40z"/>
<path fill="#bca786" d="M278 34h220v145H278z"/><path fill="#44384c" d="M298 50h175v124H298z"/>
<path fill="#73516c" stroke="#c99d6c" stroke-width="6" d="M302 54L432 70v90l-130 11z"/><circle cx="412" cy="118" r="6" fill="#dbc48a"/>
<path fill="#d3c4af" d="M36 204h824v23H36z"/><path fill="#151926" d="M104 296h394v162H104z"/>
<path fill="#29485f" d="M111 391h383v58H111z"/><path stroke="#527b8c" stroke-width="3" d="M112 404h381m-381 14h381m-381 15h381"/>
<path fill="url(#metal)" stroke="#27303e" stroke-width="4" d="M99 278h395v24H99zM485 278h34v110h-34z"/>
<path fill="#393947" stroke="#b1b9c3" stroke-width="3" d="M541 234h208v121H541z"/>
<path fill="#8994a1" d="M566 246h24v86h-24zM590 276h112v22H590z"/><path fill="#d8dece" d="M670 252h36v70h-36z"/>
<circle cx="686" cy="287" r="13" fill="#444d5c"/><path d="M574 246v-20m-9 9 9-10 9 10M604 287h47m-10-9 11 9-11 9" fill="none" stroke="#f4d25c" stroke-width="4"/>
<path fill="#bc9d83" stroke="#352d39" stroke-width="3" d="M180 370c-7-18-12-36-7-43l8 4 10 25-3-43c2-8 10-5 11 2l5 36 3-42c2-6 10-5 10 2l2 40 6-34c3-5 10-4 9 4l-4 43 14-18c4-4 10 1 7 6l-16 31-12 9-1 47h-33l3-46z"/>
<path stroke="#b78eac" stroke-width="8" d="M196 380h30"/><path fill="#e9bd4c" d="M514 363l12-16 12 16z"/>
<g fill="#f5eedf" font-family="Malgun Gothic,sans-serif" font-size="19"><text x="67" y="79">새 벽 모서리</text><text x="319" y="99">수납실 문</text><text x="548" y="390">외부 고정</text><text x="142" y="467">안쪽 손의 가장자리</text></g>
<path d="M515 90h111v100" stroke="#c7bcac" stroke-width="2" stroke-dasharray="8 7" fill="none"/>
<text x="529" y="129" font-family="Malgun Gothic,sans-serif" font-size="17" fill="#e2c1d5">접촉하지 않는 경계</text>
<text x="37" y="493" font-family="Malgun Gothic,sans-serif" font-size="16" fill="#d5d0d0">수사 기록을 나눈 도식 · 실제 장면의 축척과 시각을 나타내지 않음</text></svg>'''}


def inspection_mines():
    """Two source-owned spatial comparisons; no new eyewitness or photographed face."""
    mask_path='Assets/Data/v4_story/revision/mine/inspection-mines.json'
    assets={};masks={}
    def obj(name,width,height,spans,shapes,size):
        item,mask,files=diagram(name,width,height,spans,shapes,size,mask_path)
        masks[name]=mask;assets.update(files);return item
    visibility=[obj('inspection-control-and-gap',116,88,
        lambda y: ([(6,49)] if 8<=y<70 else [])+([(63,110)] if 38<=y<82 else []),
        '<path fill="#697482" stroke="#283040" stroke-width="3" d="M6 58h43v12H6zM18 10h14v48H18z"/>'
        '<circle cx="25" cy="46" r="6" fill="#d7d4bc"/><path fill="#aeb7bf" d="M12 8h25v8H12z"/>'
        '<path fill="#252b38" d="M63 38h47v44H63z"/><path fill="#9ca8b4" d="M63 38h47v12H63zM63 72h47v10H63z"/>'
        '<path fill="#b39d8b" stroke="#493e44" stroke-width="2" d="M75 72V59l-5-7 4-3 5 5V44l4-2 2 14 3-15 4 1v15l5-10 4 2-3 18-6 5z"/>'
        '<path stroke="#e5c955" stroke-width="2" stroke-dasharray="4 3" d="M42 22L76 55"/>',6.5),
        obj('inspection-lid-side',104,32,lambda y:[(5,99)] if 7<=y<26 else [],
        '<path fill="#8993a3" stroke="#303647" stroke-width="3" d="M5 7h94v19H5z"/><path stroke="#c5cbd0" d="M12 12h80M12 17h80"/>',5.1),
        obj('inspection-storage-wall',62,86,lambda y:[(6,56)] if 5<=y<81 else [],
        '<path fill="#b7a38b" stroke="#54465b" stroke-width="4" d="M6 5h50v76H6z"/><path fill="#6d5266" d="M15 15h31v54H15z"/><circle cx="39" cy="45" r="3" fill="#d5b77d"/>',5.1),
        obj('inspection-lamp-outline',68,66,lambda y:[(12,56)] if 6<=y<22 else [(30,38)] if 22<=y<60 else [],
        '<path fill="#bca467" d="M12 6h44v16H12z"/><path fill="#42424d" d="M30 22h8v38h-8z"/><path fill="#eee0a3" d="M18 12h32v7H18z"/>',4.6)]
    ends=[obj('inspection-sealed-end',104,78,lambda y:[(8,97)] if 6<=y<72 else [],
        '<path fill="#392f42" d="M8 6h89v66H8z"/><path fill="#b3a28b" d="M12 10h81v42H12z"/>'
        '<path fill="#756c69" d="M12 52h81v16H12z"/><path d="M12 52h81M39 52L28 68M67 52l10 16" stroke="#d6c3a1" fill="none"/>'
        '<path fill="#444951" stroke="#c5b89e" stroke-width="2" d="M39 21h30v20H39z"/>'
        '<path stroke="#a0a6ac" stroke-width="2" d="M41 26h26M41 32h26M47 23v16M60 23v16"/>',6.0),
        obj('inspection-hypothesis-arrow',102,40,lambda y:[(5,72)] if 15<=y<25 else [(60,95)] if 5<=y<35 else [],
        '<path fill="#e4cb65" d="M5 15h55V5l35 15-35 15V25H5z"/>',4.8),
        obj('inspection-rescue-floor',98,54,lambda y:[(6,92)] if 6<=y<48 else [],
        '<path fill="#aaa191" d="M6 6h86v42H6z"/><path stroke="#6a6265" stroke-width="2" d="M6 27h86M35 6v42M63 6v42"/>'
        '<path fill="#547180" d="M10 12h18v12H10z"/>',5.0),
        obj('inspection-stair-meeting',92,78,lambda y:[(6,86)] if 8<=y<70 else [],
        '<path fill="#5c5364" d="M6 70V56h20V40h20V24h20V8h20v62z"/><path stroke="#c0b095" stroke-width="4" d="M8 45L78 9M15 40v25M40 28v24M65 15v24"/>',5.1)]
    assets[mask_path]={'masks':masks}
    return visibility,ends,assets


def door_comparison():
    assets = {}
    masks = {}
    objects = [authored_object('T1-MM-01', 'reinforcing-plate', 'fixing'),
               authored_object('T1-MM-A02', 'floor-ice', 'frost')]
    for obj, mask, files in (
        diagram('latch', 96, 58, lambda y: [(57, 91)] if 5 <= y < 53 and not 25 <= y < 36 else
                [(5, 91)] if 25 <= y < 36 else [],
                '<path fill="#a5afbf" d="M57 5H91V53H57V36H5V25H57Z"/>'
                '<path fill="#3c495d" d="M57 5h34v6H57zm-52 25h52v6H5zm52 17h34v6H57z"/>'
                '<path fill="#e5e9ed" d="M7 25h51v3H7z"/><circle cx="74" cy="31" r="8" fill="#566477"/>'
                '<circle cx="74" cy="15" r="3" fill="#283342"/><circle cx="74" cy="45" r="3" fill="#283342"/>', 5.2),
        diagram('front-plate', 96, 42, lambda y: [(5, 91)] if 5 <= y < 37 else [],
                '<path fill="#96754c" d="M5 5H91V37H5z"/><path fill="#e9c58c" d="M7 5H89V9H7z"/>'
                '<path fill="#66462c" d="M5 33H91V37H5z"/><path fill="#b48e59" d="M12 13H84V29H12z"/>'
                '<g fill="#312c2b"><circle cx="11" cy="11" r="2.5"/><circle cx="85" cy="11" r="2.5"/>'
                '<circle cx="11" cy="31" r="2.5"/><circle cx="85" cy="31" r="2.5"/></g>', 5.0),
    ):
        objects.append(obj)
        masks[obj['maskKey']] = mask
        assets.update(files)
    assets[MASK] = {'masks': masks}
    assets[ART + 'witness-view.svg'] = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 896 506">
<defs><linearGradient id="wall" x2="0" y2="1" gradientUnits="objectBoundingBox"><stop stop-color="#887767"/><stop offset="1" stop-color="#bbaa95"/></linearGradient></defs>
<path fill="#292939" d="M0 0h896v506H0z"/><path fill="url(#wall)" d="M0 0h896v338H0z"/>
<path fill="#4c3b54" d="M0 244h896v99H0z"/><path fill="#806449" d="M0 243h896v9H0z"/>
<path fill="#6a5562" d="M0 344h896v162H0z"/><path d="M0 386h896M0 451h896M223 344L93 506m403-162 10 162m202-162 150 162" stroke="#87737d" fill="none"/>
<path fill="#251f28" d="M142 55h214v312H142z"/><path fill="#796345" d="M147 61h201v298H147z"/>
<path fill="#171822" d="M160 72h175v276H160z"/><path fill="#633d66" stroke="#272132" stroke-width="4" d="M160 75L284 101V328l-124 21z"/>
<path fill="#855c54" d="M175 126l94 16v61l-94-6zm0 99 94-3v65l-94 14z"/><path fill="#d5bd92" d="M248 207h24v6h-24z"/>
<path fill="#655967" d="M353 136c17 0 29 14 29 31v23c-3 16-14 23-26 23h-17v-67z"/><path fill="#474457" d="M340 209c-24 9-37 34-38 76l7 59h71l8-61c-1-46-15-70-40-74z"/>
<path fill="#867369" d="M359 37h70v341h-70z"/><path fill="#392d3b" d="M354 37h15v342h-15z"/><path fill="#aa9482" d="M373 37h9v342h-9z"/>
<path fill="#a79180" d="M653 106h148v253H653z"/><path fill="#27252d" d="M660 113h134v239H660z"/>
<path fill="#65646a" d="M669 122h116v221H669z"/><path stroke="#292a34" stroke-width="16" d="M673 173h108m-108 107h108"/><path fill="#a7a2a1" d="M673 170h108v4H673zm0 107h108v4H673z"/>
<path fill="#242231" d="M0 394h172l44 112H0z"/><path fill="#80634f" d="M0 387h170l9 17H0z"/>
</svg>'''
    return objects, assets


def paper_comparison():
    objects, masks, assets = [], {}, {}
    # The torn edge follows the existing report diagram, so its silhouette and the
    # later comparison describe the same object.
    end_by_y = (91, 87, 83, 91, 97, 92, 86, 92, 98, 93, 88)
    outlines = (
        ('torn-number', 104, 38, lambda y: [(4, end_by_y[(y - 3) // 3])] if 3 <= y < 36 else [],
         '<path d="M4 3H91V6H87V9H83V12H91V15H97V18H92V21H86V24H92V27H98V30H93V33H88V36H4Z" fill="#eee1bd"/>'
         '<path d="M12 14h6l-3 8m7-8h8l-4 8m18-6h36m-36 5h29m-62 7h59" stroke="#544b4e" stroke-width="2" fill="none"/>', 5.2),
        ('stored-number', 82, 54, lambda y: [(6, 75)] if 4 <= y < 50 else [],
         '<path d="M6 4h69v46H6z" fill="#b9ad99"/><path d="M11 9h59v36H11z" fill="#d4cbb7"/>'
         '<path d="M18 17h4v13m9-13h-4v13h6v-6h-6m15-6h21m-21 6h21m-21 6h14m-28 8h41" stroke="#70635e" stroke-width="2" fill="none"/>', 4.4),
        ('medical-strip', 92, 36, lambda y: [(6, 85)] if 6 <= y < 30 else [],
         '<path d="M6 6h79v24H6z" fill="#dddce0"/><path d="M6 7h79v5H6zm0 19h79v4H6z" fill="#a6adbb"/>'
         '<path d="M27 7v22m3-21v21m29-22v22m3-21v21" stroke="#8b93a1" fill="none"/>', 5.1),
        ('check-cover', 72, 90, lambda y: [(9, 68)] if 6 <= y < 84 else [],
         '<path d="M9 6h59v78H9z" fill="#5e7678"/><path d="M12 9h53v72H12z" fill="#879897"/>'
         '<path d="M22 20h32v20H22zM22 52h33v3H22zm0 8h23v3H22z" fill="#d3d0b2"/>'
         '<path d="M20 79V10m1 15h43" stroke="#42595f" fill="none"/>', 4.9),
    )
    for name, width, height, spans, shapes, size in outlines:
        obj, mask, files = diagram(name, width, height, spans, shapes, size, PAPER_MASK)
        objects.append(obj)
        masks[obj['maskKey']] = mask
        assets.update(files)
    assets[PAPER_MASK] = {'masks': masks}
    return objects, assets


def theatre_ring():
    """The torn attachment, open end and two strands determine this round."""
    pieces = (
        ('theatre-open-ring', lambda y: [(14, 73)] if 10 <= y < 20 or 51 <= y < 60 else
         [(10, 22), (61, 72)] if 20 <= y < 36 else [(10, 22), (65, 82)] if 36 <= y < 51 else [],
         '<path d="M65 24Q54 8 31 13Q12 16 13 34Q11 54 37 56Q59 57 67 47" fill="none" stroke="#b78c56" stroke-width="10"/>'
         '<path d="M67 45q11-6 13 4m-13-1q9-2 13 7" fill="none" stroke="#efccad" stroke-width="2"/>'),
        ('theatre-apron-buckle', lambda y: [(9, 82)] if 12 <= y < 22 or 49 <= y < 58 else
         [(9, 19), (42, 48), (72, 82)] if 22 <= y < 49 else [],
         '<rect x="14" y="17" width="63" height="36" rx="4" fill="none" stroke="#a8a5ac" stroke-width="9"/>'
         '<path d="M45 19v32" stroke="#dedce0" stroke-width="6"/>'),
        ('theatre-washer', lambda y: [(21, 71)] if 13 <= y < 24 or 48 <= y < 59 else
         [(17, 30), (59, 75)] if 24 <= y < 48 else [],
         '<circle cx="46" cy="36" r="24" fill="none" stroke="#8b969a" stroke-width="10"/>'
         '<circle cx="46" cy="36" r="28" fill="none" stroke="#cfd8d9" stroke-width="2"/>'),
        ('theatre-tag-clip', lambda y: [(8, 83)] if 41 <= y < 58 else
         [(32, 66)] if 16 <= y < 41 else [],
         '<rect x="8" y="41" width="75" height="17" rx="3" fill="#acd6e2" fill-opacity=".65" stroke="#deffff"/>'
         '<path d="M34 41V21L61 16L67 43H57L55 26L42 28V42Z" fill="#a8acb7"/>'),
    )
    objects, masks, assets = [], {}, {}
    for key, spans, shapes in pieces:
        obj, mask, files = diagram(key, 92, 68, spans, shapes, 4.8, RING_MASK)
        objects.append(obj)
        masks[key] = mask
        assets.update(files)
    assets[RING_MASK] = {'masks': masks}
    assets[ART+'theatre-ring-board.svg'] = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 896 506">'
        '<defs><pattern id="grain" width="86" height="27" patternUnits="userSpaceOnUse">'
        '<path fill="#4a3748" d="M0 0h86v27H0z"/><path d="M0 3h86M0 23h86" stroke="#544051"/></pattern></defs>'
        '<path fill="url(#grain)" d="M0 0h896v506H0z"/><path fill="#bba69f" d="M182 77l527 20-23 333-527-22z"/>'
        '<path d="M182 99l525 20M166 389l520 20" stroke="#e1c4b4" stroke-width="4"/>'
        '<path d="M44 88h98v314H44zm712 44h90v272h-90z" fill="#211c29" stroke="#6d5867" stroke-width="8"/>'
        '</svg>')
    return objects, assets


def mirror_comparison():
    pieces = (
        ('mirror-corner', lambda y: [(8, 81)] if 9 <= y < 23 else [(66, 81)] if 23 <= y < 55 else [],
         '<path d="M8 9h73v46H66V23H8z" fill="#bfb29e"/><path d="M9 24h55v22H9z" fill="#687fb6"/>'
         '<path d="M61 24h18v21H61" fill="#e7c881"/><path d="M17 14h49" stroke="#eee6cf" stroke-width="3"/>'),
        ('mirror-bench', lambda y: [(12, 78)] if 15 <= y < 50 else [],
         '<path d="M12 15h66v34H12z" fill="#694a69"/><path d="M15 18h60v6H15m0 14h60v6H15" fill="#c3a3b7"/>'),
        ('mirror-wall', lambda y: [(15, 71)] if 9 <= y < 56 else [],
         '<path d="M15 9h56v47H15z" fill="#8b819e"/><path d="M15 47h56v9H15zm1-35h54v6H16z" fill="#534d67"/>'),
        ('mirror-gate', lambda y: [(14, 77)] if 12 <= y < 23 else [(14, 25), (65, 77)] if 23 <= y < 54 else [],
         '<path d="M14 13h63v41H65V23H25v31H14z" fill="#aa746f"/><path d="M29 17h33" stroke="#e1a998" stroke-width="3"/>'),
    )
    path = 'Assets/Data/v4_story/revision/mine/mirror-comparison.json'
    objects, masks, assets = [], {}, {}
    for key, spans, shapes in pieces:
        obj, mask, files = diagram(key, 92, 64, spans, shapes, 4.8, path)
        objects.append(obj)
        masks[key] = mask
        assets.update(files)
    assets[path] = {'masks': masks}
    assets[ART+'mirror-plan.svg'] = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 896 506">
<rect width="896" height="506" fill="#221e32"/>
<path d="M40 103h242v257H40zM311 103h249v257H311zM590 103h263v257H590z" fill="#4a405d" stroke="#7e718e" stroke-width="4"/>
<path d="M65 131h191v203H65zM334 130h202v204H334zM613 130h218v204H613z" fill="#353049"/>
<path d="M89 171h145v113H89z" fill="#6f86a6" stroke="#abc1d8" stroke-width="5"/>
<path d="M105 273l111-96m-95 101l107-93" stroke="#a9c4d0" opacity=".6" stroke-width="2"/>
<path d="M115 268q45-25 92-65" fill="none" stroke="#eebdaf" stroke-width="11" opacity=".6"/>
<path d="M356 289v-84h60v-51h91m-91 51h90" fill="none" stroke="#9e88a5" stroke-width="19"/>
<path d="M443 274q-14-53 46-51" fill="none" stroke="#f8c97e" stroke-width="14"/>
<path d="M437 276l6 6 7-6" fill="none" stroke="#f8c97e" stroke-width="5"/>
<path d="M644 201h157v56H644z" fill="#896975" stroke="#cba2ae" stroke-width="4"/>
<path d="M651 214h143m-143 24h143" stroke="#442b50" stroke-width="4"/>
<path d="M77 410h743" stroke="#7a667f" stroke-width="4"/>
<path d="M160 392v37m274-37v37m288-37v37" stroke="#e0cb9d" stroke-width="3"/>
</svg>'''
    return objects, assets


def theatre_pedestal():
    path = 'Assets/Data/v4_story/revision/mine/theatre-pedestal.json'
    def rim_span(y):
        offset = (y + .5 - 31) / 20
        if abs(offset) >= 1:
            return []
        half_width = round(40 * (1 - offset * offset) ** .5)
        return [(46 - half_width, 46 + half_width)]

    pieces = (
        ('pedestal-rim', rim_span,
         '<ellipse cx="46" cy="31" rx="37" ry="17" fill="#695d68" stroke="#d4c5ad" stroke-width="6"/>'
         '<path d="M69 17l9 6-11 5" fill="none" stroke="#cf8fae" stroke-width="3"/>'),
        ('shelf-fixed-face', lambda y: [(8,84)] if 10 <= y < 26 else
         [(11,24),(68,81)] if 26 <= y < 52 else [],
         '<path d="M8 10h76v16H80v26H68V26H24v26H12V26H8z" fill="#988397"/>'
         '<path d="M10 15h72" stroke="#ddc6ba" stroke-width="3"/>'),
        ('platter-underside', lambda y: [(18,75)] if 12 <= y < 19 or 47 <= y < 54 else
         [(8,84)] if 19 <= y < 47 else [],
         '<ellipse cx="46" cy="33" rx="38" ry="21" fill="#cfc4b9" stroke="#91868b" stroke-width="4"/>'
         '<path d="M27 42q7 3 12-2m3-2 6-3" fill="none" stroke="#a2769e" stroke-width="3"/>'),
        ('pouch-stitch', lambda y: [(22,71)] if 10 <= y < 26 else
         [(12,80)] if 26 <= y < 53 else [],
         '<path d="M22 10h49l9 16v27H12V26z" fill="#775147"/>'
         '<path d="M25 26l7 4 7-4 7 4 7-4 4 3m8-3 8 5" fill="none" stroke="#ead2ac" stroke-width="2"/>'),
    )
    objects, masks, assets = [], {}, {}
    for key, spans, shapes in pieces:
        obj, mask, files = diagram(key, 92, 64, spans, shapes, 4.8, path)
        objects.append(obj)
        masks[key] = mask
        assets.update(files)
    assets[path] = {'masks': masks}
    assets[ART+'pedestal-board.svg'] = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 896 506">'
        '<path fill="#302838" d="M0 0h896v506H0z"/><path fill="#736474" d="M87 70h722v366H87z"/>'
        '<path d="M100 164h697M100 257h697M100 350h697M260 73v360M450 73v360M644 73v360" stroke="#544857" stroke-width="4"/>'
        '<path d="M100 77h157v349H100zM648 75h147v350H648z" fill="#6b5869" fill-opacity=".7"/>'
        '<path d="M126 125h108m435 243h110" stroke="#b4a39c" stroke-width="6"/>'
        '</svg>')
    return objects, assets


def mirror_knife_sequence():
    mask_path = 'Assets/Data/v4_story/revision/mine/mirror-knife.json'
    views = (
        ('knife-at-threshold',
         '<path d="M12 20h17v41H12zm59-3h8v45h-8z" fill="#806b8e"/>'
         '<path d="M29 52h38l-13 7H29z" fill="#d6d9e0"/><path d="M19 50h13v9H19z" fill="#544050"/>'),
        ('knife-from-bench',
         '<path d="M9 45h34v15H9z" fill="#816981"/><path d="M40 20l15 9-7 20H35l4-11-10-5z" fill="#b89baa"/>'
         '<path d="M48 30l25 3-9 6-18-2z" fill="#dfe4e9"/><path d="M72 10h8v51h-8z" fill="#6b5a7b"/>'
         '<path d="M58 51h11l-7 5h-7z" fill="#b9b5d0"/>'),
        ('knife-carried-in',
         '<path d="M10 12h17v49H10zM66 47h15v14H66z" fill="#756581"/>'
         '<path d="M23 20l29 15-6 10-25-16z" fill="#c4a9b5"/>'
         '<path d="M45 34l26 1-13 7H46z" fill="#dfe4e9"/>'),
    )
    objects, masks, assets = [], {}, {}
    for key, details in views:
        shapes = '<rect x="4" y="4" width="84" height="60" rx="3" fill="#312b40" stroke="#c5b4bd" stroke-width="3"/>' + details
        obj, mask, files = diagram(key,92,68,lambda y:[(3,89)] if 3 <= y < 65 else [],
                                   shapes,5.1,mask_path)
        objects.append(obj)
        masks[key] = mask
        assets.update(files)
    assets[mask_path] = {'masks':masks}
    assets[ART+'mirror-knife-board.svg'] = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 896 506">'
        '<path fill="#2e273e" d="M0 0h896v506H0z"/><path fill="#50435d" d="M50 44h796v417H50z"/>'
        '<path d="M291 45v415m310-415v415" stroke="#a58eaa" stroke-width="4"/>'
        '<path d="M74 422h749" stroke="#74667d" stroke-width="6"/></svg>')
    return objects, assets


def archive_slot():
    pieces = (
        ('archive-d', (10, 12, 82, 58), '<path d="M10 12h72v46H10z" fill="#9459a6"/><path d="M29 22h18q15 0 15 13T47 48H29z" fill="none" stroke="#fff1bb" stroke-width="6"/>'),
        ('archive-tape', (6, 23, 86, 47), '<path d="M6 23h80v24H6z" fill="#d9b477"/><path d="M20 24l8 22m8-22 8 22m8-22 8 22m8-22 8 22" stroke="#a65b6a" stroke-width="3"/>'),
        ('archive-e', (18, 10, 75, 61), '<path d="M18 10h57v51H18z" fill="#566f8f"/><path d="M57 22H34v28h23m-23-14h19" fill="none" stroke="#c0e9ec" stroke-width="5"/>'),
        ('archive-return', (8, 10, 85, 58), '<path d="M8 10h77v48H8z" fill="#ded2b6"/><path d="M20 22h46m-46 10h52m-52 10h52" stroke="#564254" stroke-width="2"/>'),
    )
    path = 'Assets/Data/v4_story/revision/mine/archive-slot.json'
    objects, masks, assets = [], {}, {}
    for key, (x0,y0,x1,y1), shapes in pieces:
        obj, mask, files = diagram(key, 92, 68, lambda y: [(x0,x1)] if y0<=y<y1 else [], shapes, 4.8, path)
        objects.append(obj)
        masks[key] = mask
        assets.update(files)
    assets[path] = {'masks': masks}
    assets[ART+'archive-slot-board.svg'] = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 896 506">'
        '<rect width="896" height="506" fill="#2b273a"/><path d="M85 92h726v314H85z" fill="#54475e" stroke="#948297" stroke-width="7"/>'
        '<path d="M136 150h624v192H136z" fill="#252130" stroke="#a0919e" stroke-width="7"/>'
        '<path d="M240 153v186m104-186v186m104-186v186m104-186v186m104-186v186" stroke="#78647d" stroke-width="5"/>'
        '<path d="M142 334h611" stroke="#c7b5ad" stroke-width="8"/></svg>')
    return objects, assets


def archive_package_comparison():
    path = 'Assets/Data/v4_story/revision/mine/archive-package.json'
    assets, objects, masks = {}, [], {}
    edge = (91,87,95,86,92,96,89,94)
    pieces = [
        ('archive-fitting-edge', lambda y: [(5,edge[(y-8)//6]),(edge[(y-8)//6]+4,113)] if 8<=y<56 else [],
         '<path fill="#d7a66f" d="M5 8h86v6h-4v6h8v6h-9v6h6v6h4v6h-7v6h5v6H5z"/>'
         '<path fill="#e8c189" d="M95 8h18v48H98v-6h-5v-6h7v-6h-4v-6h-6v-6h9v-6h-8v-6h4z"/>'
         '<path fill="#79526f" d="M5 29h81v7H5zm94 0h14v7H99z"/>'),
        ('archive-printed-foil', lambda y: [(8,105)] if 10<=y<54 else [],
         '<path fill="#b88e70" d="M8 10h97v44H8z"/><path d="M43 19h13q14 0 14 13T56 45H43z" fill="none" stroke="#e7c294" stroke-width="5"/>'),
        ('archive-d-base', lambda y: [(19,103)] if 16<=y<52 else [],
         '<path fill="#685371" d="M19 16h84v36H19z"/><path d="M50 22h12q13 0 13 12T62 46H50z" stroke="#efe2d3" fill="none" stroke-width="4"/>'),
        ('archive-pot-lid', lambda y: [(12,107)] if 34<=y<48 else [(48,72)] if 21<=y<34 else [],
         '<path fill="#797d89" d="M12 34h95v14H12zM48 21h24v13H48z"/><path d="M13 43h93" stroke="#c3b6ab" stroke-width="2"/>'),
    ]
    for key,spans,shapes in pieces:
        obj,mask,files=diagram(key,120,64,spans,shapes,5.4,path)
        objects.append(obj);masks[key]=mask;assets.update(files)
    assets[path]={'masks':masks}
    assets[ART+'archive-preparation-view.svg']='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 896 506">
<rect width="896" height="506" fill="#282534"/><path fill="#666073" d="M47 36h802v427H47z"/>
<path fill="#35374c" d="M60 45h253v175H60z"/><path d="M180 47v172M60 138h253" stroke="#918395" stroke-width="8"/>
<path fill="#504150" d="M287 268l402-101 152 135-447 134z"/><path fill="#98716d" d="M292 255l399-94 150 129-447 134z"/>
<path fill="#494353" d="M394 424l447-134v67L395 464z"/><path fill="#d2ad88" d="M396 354l131-41 94 75-137 36z"/>
<path fill="#534a54" d="M583 200q-16-21-36-21l-57 16 8 29 48-10 39 21 28-10z"/>
<path fill="#dbc5a1" d="M511 189l-36-9-34 19 7 22 36 4 34-12z"/><path fill="#dac393" d="M453 200l38-8 12 12-38 11z"/>
<path fill="#f0e6d6" d="M182 276h83l-13 75h-57z"/><path stroke="#d5b98f" stroke-width="9" d="M262 281q35-2 27 28l-31 15" fill="none"/>
<ellipse cx="223" cy="275" rx="42" ry="10" fill="#9f8b86"/><path fill="#6d697d" d="M701 236h71l-7 37h-60z"/>
<path stroke="#c3a4b6" stroke-width="2" stroke-dasharray="7 5" d="M416 231l159 25m98-72 123 97"/>
<g font-family="Malgun Gothic,sans-serif" fill="#faf1e0" font-size="19"><text x="56" y="482">창가 시점 대조 · 상판에 가려진 내용물은 그리지 않음</text></g></svg>'''
    return objects,assets


def corridor_sightlines():
    """Comparison shapes for the old door and the witness's continuous view."""
    mask_path = 'Assets/Data/v4_story/revision/mine/corridor-sightlines.json'
    parts = [
        ('corridor-old-sill', lambda y: [(6,114)] if 39<=y<54 else [(6,27),(92,114)] if 18<=y<39 else [],
         '<path d="M6 18h21v21h65V18h22v36H6z" fill="#8f7467"/><path d="M27 39h65" stroke="#ffe0a1" stroke-width="5"/>'),
        ('corridor-new-step', lambda y: [(13,105)] if 31<=y<52 else [(31,91)] if 20<=y<31 else [],
         '<path d="M13 31h18V20h60v11h14v21H13z" fill="#778491"/><path d="M31 20h60M13 32h92" stroke="#c5d4db" stroke-width="3"/>'),
        ('corridor-reception', lambda y: [(10,110)] if 17<=y<52 else [],
         '<rect x="10" y="17" width="100" height="35" rx="2" fill="#654f69"/><path d="M12 23h96m-70 8h45v12H38z" stroke="#cfbbc1" fill="none" stroke-width="2"/>'),
        ('corridor-sign', lambda y: [(14,106)] if 13<=y<43 else [(54,66)] if 43<=y<59 else [],
         '<path d="M14 13h92v30H66v16H54V43H14z" fill="#8a7850"/><path d="M30 27h49l-9-8m9 8-9 8" stroke="#fff0c3" fill="none" stroke-width="3"/>'),
        ('corridor-frame-end', lambda y: [(12,108)] if 13<=y<54 else [],
         '<rect x="12" y="13" width="96" height="41" rx="4" fill="#484c65"/><path d="M18 34h49m9-12v24m10-24v24" stroke="#e1ced1" stroke-width="4"/>'),
        ('corridor-face-occluded', lambda y: [(10,109)] if 14<=y<53 else [],
         '<rect x="10" y="14" width="99" height="39" fill="#51455b"/><circle cx="43" cy="33" r="14" fill="#b78f78"/><path d="M45 14h64v39H45z" fill="#897381"/>'),
        ('corridor-continuous-body', lambda y: [(15,105)] if 29<=y<56 else [(43,78)] if 11<=y<29 else [],
         '<path d="M43 11h35v18h27v27H15V29h28z" fill="#4c7773"/><path d="M22 45h71m-10-8 10 8-10 8" fill="none" stroke="#e7e1bb" stroke-width="4"/>'),
        ('corridor-pressure', lambda y: [(9,111)] if 19<=y<52 else [],
         '<rect x="9" y="19" width="102" height="33" fill="#7d5d70"/><path d="M25 36h59m-15-10 15 10-15 10" fill="none" stroke="#f4c7c2" stroke-width="5"/>'),
    ]
    objects, masks, assets = [], {}, {}
    for key,spans,shapes in parts:
        obj,mask,files = diagram(key,120,64,spans,shapes,4.9,mask_path)
        objects.append(obj)
        masks[key] = mask
        assets.update(files)
    assets[mask_path] = {'masks':masks}
    assets[ART+'corridor-sightline-board.svg'] = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 896 506">'
        '<rect width="896" height="506" fill="#262434"/><path d="M58 69h368v330H58zM470 69h368v330H470z" fill="#53495d" stroke="#ac94a3" stroke-width="4"/>'
        '<path d="M89 345l292-129V95m110 250 307-129V95" fill="none" stroke="#918284" stroke-width="5"/>'
        '<path d="M164 310h182m209-32h181m-181-23h181m-181-23h181" stroke="#d4a983" stroke-width="8"/>'
        '<path d="M110 179l218 69m169-69 213 52" stroke="#b7d2cb" stroke-width="3" stroke-dasharray="9 7"/>'
        '<g font-family="Malgun Gothic,sans-serif" fill="#fff4e7" font-size="20"><text x="80" y="112">그날 · 옆문과 낮은 모서리</text>'
        '<text x="491" y="112">현재 · 새 발판과 난간</text><text x="80" y="455">시야가 확인된 범위만 표시</text></g></svg>')
    assets[ART+'inspection-result-columns.svg'] = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 896 506">'
        '<rect width="896" height="506" fill="#2e2834"/><rect x="77" y="57" width="742" height="392" rx="9" fill="#e4d1b0"/>'
        '<path d="M120 140h653v143H120zM120 313h653v82H120z" fill="#dbc09d" stroke="#836767" stroke-width="4"/>'
        '<path d="M309 140v143m289-143v143M120 204h653" stroke="#836767" stroke-width="4"/>'
        '<g font-family="Malgun Gothic,sans-serif" fill="#46333e" font-size="24" text-anchor="middle">'
        '<text x="448" y="112">당시 최종 점검본</text><text x="210" y="184">항목 번호</text><text x="453" y="184">점검 결과</text>'
        '<text x="678" y="184">발행 날짜</text><text x="210" y="250">동일 항목</text><text x="453" y="250">정상</text>'
        '<text x="679" y="250">인계 당시</text><text x="448" y="365">별지 · 사후 재확인 서명</text></g></svg>')
    return objects[:4], objects[4:], assets


def theatre_section():
    return {ART + 'theatre-section.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 896 506">
<path fill="#25253a" d="M0 0h896v506H0z"/><path fill="#514056" d="M65 94h761v322H65z"/>
<path fill="#816a68" d="M84 114h302v210H84z"/><path fill="#736477" d="M407 114h397v210H407z"/>
<path fill="#30263d" d="M84 326h720v66H84z"/><path fill="#a59481" d="M84 326h720v12H84z"/>
<path fill="#4a3448" stroke="#211e2c" stroke-width="8" d="M123 164h92v162h-92z"/>
<path fill="#cfb38f" d="M188 239h21v6h-21z"/>
<path fill="#242230" stroke="#ad9d89" stroke-width="8" d="M365 167h65v96h-65z"/>
<path d="M379 171v87m12-87v87m12-87v87m12-87v87m-49-61h64m-64 31h64" stroke="#8c8492" stroke-width="4"/>
<path fill="#534760" stroke="#252635" stroke-width="8" d="M589 165h109v87H589z"/>
<path fill="#d8ae5f" d="M671 158l10 4-38 100-10-4z"/>
<path fill="#9c7967" stroke="#3c3443" stroke-width="5" d="M712 281h77v29h-77z"/>
<path d="M729 306v27m42-27v27" stroke="#9c7967" stroke-width="6"/>
<path d="M61 93h766v326H61zM395 95v67m0 104v62" fill="none" stroke="#c1b2a8" stroke-width="8"/>
</svg>'''}
