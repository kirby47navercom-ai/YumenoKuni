"""Select inspected built-in edits; copy originals, never resample their pixels."""
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art/v4_production/death_posture_20261103'
GENERATED = Path('C:/Users/kirby/.codex/generated_images/01a19fd4-cd3f-7123-91ea-3a9194054780')
CHOICES = {
    'incident_c1': ('exec-6a38ea2d-e549-4790-8d7d-269d2739eb49.png', 3),
    'incident_c2': ('exec-36f0527f-2371-465a-bd56-303cc7334d47.png', 5),
    'incident_c3a': ('exec-9c7cbb7a-5211-412a-af48-a7174abda1a2.png', 3),
    'incident_c3b': ('exec-527383a7-dc56-4abb-be04-bfb435519896.png', 3),
    'incident_c4': ('exec-3ed5796e-6d6c-4721-9cc5-37f6e5763b78.png', 6),
    'incident_c5': ('exec-af0f3cc7-1e10-46db-8ee4-216de57507d6.png', 3),
}
REVIEWS = {
    'incident_c1': ['Head/shoulder bear weight on floor; one limp hand near collar, the other under crumpled damp paper as manuscript11a3:1154 requires.', 'Non-bleeding purple neck-pressure mark, printer/window/torn report retained; missing strip not supplied. Small partly melted frost/moisture retained on floor, no upper-wall invention.'],
    'incident_c2': ['Earlier open-palm/whole-loop versions rejected. Latest curls fingers around a small flat black fragment with a projecting fractured edge and short cord.', 'Connected stylized purple trace from existing temple/hair region to ear/neck/collar fabric, no new neck wound. Lid stays/open latches/weights/cloth preserved; apron decoration not reclassified as blood.'],
    'incident_c3a': ['Head fallen forward onto shoulder, asymmetric collapsed shoulders, dull gaze and slack gloved fingers.', 'Neck/collar trace and connected purple pool, fallen hat and work offcuts retained.'],
    'incident_c3b': ['First edit rejected for bright focused eyes; second has uneven narrow lids, inert gaze and hanging hand.', 'Post-death bench state retained, not earlier living rescue; brown crewneck, separate emergency cloth and purple bench-to-floor trace retained.'],
    'incident_c4': ['Earlier anatomy and waist/covering rejected by user. Latest retains coherent neck/shoulders/arms/hips, matches approved red plaid costume waistband instead of invented buckle belt, and lays one continuous thin gray sheet over hips/knees/shins with folds resting on floor; shoes remain visible.', 'Post-rescue OPEN hatch and RELEASED external hasp, gray covering/closed wet bag/clear water and localized forehead/one-hand/edge marks retained. Other hand uninjured; no new fatal bleeding.'],
    'incident_c5': ['First native framing rejected because dialogue covered face. Latest higher camera places face and elbow within upper65%, preserving skull-on-floor weight and inert hands.', 'Old minor elbow trace, plain unwashed glass/papers retained; poisoning is not replaced with new bleeding injury.'],
}
REVIEWS['incident_c1'].append('R3 connects waist/pelvis and both legs; skirt has a single continuous pleated hem and floor contact rather than a detached cloth mound.')
REVIEWS['incident_c2'].append('R5 replaces angular cloth planes with one continuous thin drape following hips/knees and compressed folds in the chest; four weights and held broken fragment retained.')
REVIEWS['incident_c3a'].append('R2 anatomy candidate erased the existing neck trace and was rejected. R3 restores it while retaining coherent shoulders/waist and relaxed five-finger gloved hands.')
REVIEWS['incident_c3b'].append('R3 rebuilds a single wearable belt and buckle, with tool clips hanging from it; tools no longer float in the abdomen, near arm remains hanging off bench.')
REVIEWS['incident_c5'].append('R3 connects shoulders/arms and waist/pelvis, with skirt following two bent legs; face and old elbow mark remain above dialogue area.')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def put(path, value):
    temp = path.with_suffix(path.suffix + '.posture.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    selection_path = ROOT / 'art/v4_production/forensic_repair/selected.json'
    catalog_path = ROOT / 'art/v4_production/completion/final_catalog.json'
    selection, catalog = read(selection_path), read(catalog_path)
    before = OUT / 'selected-before.json'
    if not before.exists():
        shutil.copyfile(selection_path, before)
    prior_review = read(OUT / 'review.json') if (OUT / 'review.json').exists() else {}
    prior_rows = {row['logical']: row for row in prior_review.get('rows', [])}
    rows = []
    for logical, (file, revision) in CHOICES.items():
        source = GENERATED / file
        with Image.open(source) as image:
            image.verify()
        with Image.open(source) as image:
            width, height = image.size
            assert abs(width / height - 16 / 9) < .005
            mode = image.mode
        original = OUT / f'{logical}_r{revision}.png'
        delivery = ROOT / f'art/cg_v4/delivery/{logical}_posture_20261103.png'
        for target in [original, delivery]:
            if not target.exists() or digest(target) != digest(source):
                shutil.copyfile(source, target)
        assert digest(source) == digest(original) == digest(delivery)
        old = read(before)['overrides'][logical]
        row = {**old, 'selected_id': f'{logical}_posture_20261103',
               'source': original.relative_to(ROOT).as_posix(),
               'delivery': delivery.relative_to(ROOT).as_posix(),
               'webp': delivery.relative_to(ROOT).as_posix(),
               'metadata': f'art/v4_production/death_posture_20261103/{logical}.json',
               'size': [width, height], 'format': 'PNG',
               'source_review': 'art/v4_production/death_posture_20261103/review.json',
               'completion_revision': 'User rejected lively/sleeping posture; rebuilt gravity, inert expression and gaze while preserving incident facts.',
               'runtime_integrated': False}
        row.pop('raw_4x', None)
        row['resolutionPolicy'] = 'Native built-in output retained byte-for-byte; no upscale or claim of former 6688x3762 detail.'
        row['forensicCropPolicy'] = 'Old normalized crop coordinates are not approved for this changed pose. Re-review before any new hotspot/detail binding.'
        put(ROOT / row['metadata'], {**row, 'sha256': digest(delivery), 'mode': mode, 'visualChecks': REVIEWS[logical]})
        selection['overrides'][logical] = row
        for item in catalog['story_cg']:
            if item.get('logical_id') == logical:
                item.update(row)
        review_row = {'logical': logical, 'selected': row['source'], 'delivery': row['delivery'],
                     'revision': revision, 'size': row['size'], 'sha256': digest(delivery),
                     'visualChecks': REVIEWS[logical], 'runtimeVerified': False}
        prior = prior_rows.get(logical, {})
        if prior.get('sha256') == review_row['sha256']:
            for key in ['runtimeVerified', 'runtimeProof', 'runtimeScope']:
                if key in prior:
                    review_row[key] = prior[key]
        rows.append(review_row)
    selection['posture_review'] = 'art/v4_production/death_posture_20261103/review.json'
    catalog['death_posture_review'] = selection['posture_review']
    catalog['deathPostureCropPolicy'] = 'Previous forensic_details retain their original pixels and refer to the old scene version; do not reuse those coordinates as hotspots on the new pose.'
    put(OUT / 'review.json', {'tool': 'built-in image_gen', 'status': 'selected-after-direct-pixel-review-runtime-pending',
                             'originalsPreserved': True, 'rows': rows,
                             'rejected': ['incident_c3b_r1: attentive bright eyes', 'incident_c4_r1: glossy responsive eyes', 'incident_c4_r2: sleep expression', 'incident_c3a_r2: neck trace erased; rejected before selection, restored in r3'],
                             'prompts': sorted(p.name for p in OUT.glob('prompts*.json')),
                             'limits': 'Illustrated death readability is an art judgement, not a medical finding. Original forensic crops/precise hotspots and full gameplay-size readability require separate verification.'})
    # Publish selection only after every inspected output exists and decodes.
    put(selection_path, selection)
    put(catalog_path, catalog)
    print(json.dumps({'selected': len(rows), 'imagesResampled': 0, 'oldOriginalsDeleted': 0}))


if __name__ == '__main__':
    main()
