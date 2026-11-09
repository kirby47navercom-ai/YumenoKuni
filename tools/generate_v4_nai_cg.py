"""Original v4 CG production. Credentials stay only in memory/environment, never artifacts."""
from pathlib import Path
import argparse, os, json, re, io, zipfile, base64, hashlib
import requests
from PIL import Image, ImageDraw
from generate_tpose_nai import build_payload

ROOT=Path(__file__).resolve().parents[1]

def token_from_current_user():
    raise SystemExit('NAI generation disabled by current user instruction; no request sent.')

STYLE='best quality, highres, professional anime visual novel CG, danganronpa (style), intricate clean variable-width ink linework, detailed character faces and carefully designed hair, angular expressive eyes, controlled hard cel shading with detailed fabric folds, strong intentional composition, rich subdued color design, psychological tension, cinematic anime illustration'
NEG='text, logo, watermark, signature, gore, dismemberment, organs, nudity, suggestive pose, sexualized, pinup, shiny skin, lens flare, sparkles, crude drawing, children illustration, western cartoon, overly simple drawing, flat featureless face, thick uniform outlines, blurry background, smile, duplicated limbs, malformed hands, extra fingers, missing fingers, floating body, impossible perspective, flowing fountain, waterfall'
JOBS={
 'p01_notebook_boundary':{
  'source':'docs/design/rewrite_v4/10_프롤로그_초고.md#P-01',
  'positive':'Close event CG, original two fully clothed teenage schoolgirls seen from shoulders to hands and bags. Black short bob protagonist wearing black blazer with red piping and white shirt/red ribbon, tense unsmiling face at left. Pink bob girl wearing cream blazer/pink ribbon at right, her hand has stopped just short of an old small notebook. Protagonist firmly pulls her OWN closed notebook back against her body; one schoolbag sits open on an amusement park bench, a small worn pink rabbit keychain with red-stitched ear hangs from bag loop. Clear visual distance between their hands, distrust rather than friendly posing, no physical injury. Empty dry fountain nozzle out of focus only in distant context, cool daytime light. Eye-level medium close shot, hands and notebook sharply drawn, anatomically plausible. Do not print any writing on notebook. Single continuous event scene, not collage.',
  'seed':1729001},
 'p02_cup_refusal':{
  'source':'docs/design/rewrite_v4/10_프롤로그_초고.md#P-01',
  'positive':'Event CG focused on ordinary hands and a paper cup at an abandoned theme park bench. Cream school blazer sleeve of a pink bob girl at right holding a half-filled white paper cup; fingertips slightly squeeze cup rim into an oval but no spilling. Black blazer with red piping sleeve of a second girl at left, her open empty hand makes a restrained stop gesture without grabbing. Grey uniform sleeve of a third person withdrawing in background beside small cart holding closed water jug and unused cups. Uneasy interpersonal distance; no smiling group pose, no weapons, no injury, no blood. Close crop excludes faces, natural plausible anatomy and spatial contact, cool morning light, flat hard cel shadows and strong ink outlines. No writing, labels, new props or magic effects.',
  'seed':1729002}
}

# The first two compositions failed identity/action QA; retain them as rejected studies.
for old,new in [('p01_notebook_boundary','p01_notebook_boundary_v2'),('p02_cup_refusal','p02_cup_refusal_v2')]:
    JOBS[new]=dict(JOBS[old]);JOBS[new]['seed']+=100
JOBS['p01_notebook_boundary_v2']['positive']='Two original teenage girls from this project, eye-level close event CG at a wooden amusement park bench. Left: short BLACK bob with blue inner streak and a single large curved ahoge, violet eyes, one red-thread tied side lock, black blazer with RED piping, white shirt and red ribbon; both her hands firmly protect her small CLOSED pink notebook against her OWN chest. Right: strawberry pink bob, cyan hairclip, lavender eyes, cream blazer and pink ribbon; her empty hand has withdrawn to her own chest, visibly separated from the left girl by open air. NO physical contact between the girls, no holding hands, no reaching into the notebook. Both look distrustful and unsmiling with clearly different expressive faces. Open dark schoolbag lies on bench, worn small pink rabbit keychain with red stitching on one ear hangs from bag loop. DRY fountain nozzle in distant background with no running water. Dark ink/cel illustration with fine hair detail and deliberate clothing folds. Notebook contains no writing or symbols. Composition shows both faces clearly and notebook/hand action clearly, no extra people, no new props.'
JOBS['p02_cup_refusal_v2']['positive']='Close event CG of two pairs of ordinary hands and a paper cup on a wooden amusement park bench. Right person wearing cream school blazer holds a white paper cup by its side; fingertips subtly pinch the rim into an oval. Left person wearing black school blazer with red piping holds her OPEN EMPTY palm near her own body to stop the gesture, no touching cup or other hand. The cup is clearly separate from both bodies. Hands are correct anatomy with five fingers. Faces OUTSIDE frame, no characters or bystanders in background, no grey suited people. Behind the bench a small cart with CLOSED plain water jug and unused cups, dry pavement and low theme park railing. Cool morning light, detailed anime linework and solid cel shadows. No blood, injury, weapons, extra objects or writing. The emotional focus is wary refusal rather than cooperation.'

# The prior study used obsolete eye colors. Never silently relabel that image.
JOBS['p01_notebook_boundary_v3'] = dict(JOBS['p01_notebook_boundary_v2'])
JOBS['p01_notebook_boundary_v3']['seed'] += 100
JOBS['p01_notebook_boundary_v3']['positive'] = (
    JOBS['p01_notebook_boundary_v2']['positive']
    .replace('violet eyes', 'warm amber eyes')
    .replace('lavender eyes', 'brown eyes')
)

# Prop-focused story CG: character acting remains referenced to the selected masters.
# Any readable contact/phone data is deliberately kept out of the raster art.
JOBS.update({
 'p02_opened_seal':{
  'source':'docs/design/rewrite_v4/10_프롤로그_초고.md#P-02', 'seed':1729203,
  'positive':'Single continuous event insert, close detail at a closed amusement park refreshment kiosk. A young medic in a plain grey school uniform sleeve holds an already torn blank tamper-evident strip beside the matching cap of an ordinary water jug. Focus on the clearly separated broken ends of the plastic seal, NOT blood or a wound. Grey sleeve and both ordinary hands, correct five finger anatomy. Jug on a worn wooden counter, clean unused paper cups stacked on one side, used cups kept distinctly on the other. No faces visible, no other hands, no labels, no text, no visible liquid spills. Uncomfortable cool morning light, deliberate angular ink drawing and hard cel shaded folds. This is an interpersonal trust scene, not laboratory evidence or a diagram.'},
 'p03_dust_boundary':{
  'source':'docs/design/rewrite_v4/10_프롤로그_초고.md#P-03', 'seed':1729204,
  'positive':'Single close event insert of an old amusement park direction-board frame seen by a suspicious visitor. Several faded opening-eve event poster sheets overlap underneath a glassless protective frame. All poster surfaces blank and abstract color blocks, no readable letters, faces, symbols, dates, or invented evidence. Close focus on a small rubbed clean area in ordinary accumulated grey dust along the lower wooden frame edge, surrounding dust undisturbed. No hand touching the clean patch, no fingerprint diagram, no magical glow. Weathered painted metal screws and wood, subdued daylight, clearly hand-drawn fine irregular anime ink lines and controlled dark cel shading. Cinematic wide 3:2 composition, no people.'},
 'p04_handle_observation':{
  'source':'docs/design/rewrite_v4/10_프롤로그_초고.md#P-04', 'seed':1729205,
  'positive':'Single continuous close event CG inside a theme park service office doorway. Slightly oblique eye-level view of an ordinary brass horizontal lever handle attached to a worn dark purple wooden door, real latch and rectangular backplate. Existing polished wear is concentrated on top of lever, dull grey dust on adjacent upper plate. A second faint newly disturbed area on underside remains visibly separate, subtle ordinary surface wear, not glowing fingerprint or forensic powder. At lower left frame a girl black blazer sleeve with red piping holds a small closed plain pink notebook against her body without touching handle. Face outside frame. Fine perspective-correct hand-drawn anime ink rendering, hard cel shaded brass, cool interior daylight, no writing, no diagrams, no extra evidence, no weapon, no injury.'},
 'p04_unanswered_phone':{
  'source':'docs/design/rewrite_v4/10_프롤로그_초고.md#P-04', 'seed':1729206,
  'positive':'Single continuous event insert in an old amusement park service office, abandoned wood desk with an ordinary corded beige pushbutton telephone. The receiver rests beside the cradle on desk, spiral cable connected, silent inactive phone with no light, no screen, no success indicator. A half-open shallow wooden drawer beneath desk contains a small stack of aged maintenance contact sheets. Sheets have only faint abstract straight ruling, absolutely no readable names or phone numbers. Four empty chairs partly visible in dim context. Through the open interior doorway a small switched-OFF printer stands in a neighboring lounge. No people, no blood or injury, no text, no electric sparks, no disconnected wires. Uneasy stillness, deliberately composed anime visual-novel ink and hard cel shading rather than photoreal 3D.'}
})

PROP_STYLE='best quality, highres, professional anime visual novel object closeup CG, deliberate angular variable-width ink linework, controlled hard cel shading, detailed worn materials, rich subdued color design, psychological tension, carefully constructed perspective, single cinematic illustration'
for identifier in ['p02_opened_seal','p03_dust_boundary','p04_handle_observation','p04_unanswered_phone']:
    redo=identifier+'_v2';JOBS[redo]=dict(JOBS[identifier]);JOBS[redo]['seed']+=100
    JOBS[redo]['style']=PROP_STYLE
    JOBS[redo]['negative']=NEG+', person, human, face, eyes, hair, character, portrait, reflection of person, extra prop, hand, fingers'
JOBS['p02_opened_seal_v2']['positive']='Object-only close insert CG, NO PEOPLE, NO HANDS. On a worn wooden refreshment counter stands an ordinary transparent blue plastic 5-litre water container with a wide SCREW CAP. 1.8::a visibly BROKEN thin plastic tamper-evident ring lies immediately beside its matching screw cap::, two ends visibly separated by a small gap. The ring is a narrow molded strip with serrated break tabs, not paper, not tissue, not a receipt. Container has a simple plain integrated plastic handle, no electric base, no kettle spout, no thermos. Two stacks of unused plain white PAPER CUPS behind it. No brand or text. Still, wary morning atmosphere, precise cel-shaded object rendering. This represents the already opened container being inspected, not the moment someone opens it.'
JOBS['p03_dust_boundary_v2']['positive']='Object-only close view of a weathered outdoor amusement-park poster board. NO PEOPLE OR FACES ANYWHERE, no figures printed on posters. Large frame of grey-brown wood, metal corner plates with screws. Several overlapping plain faded cream paper sheets with abstract muted color blocks, no writing and no symbols. Along the lower horizontal wooden ledge: 1.6::a short rubbed clean rectangular patch in a thin layer of ordinary accumulated grey dust::, dusty wood continues on both sides. Not a fingerprint, not a forensic outline. Dust lies ON the wood ledge, no grey sand piled in front of poster papers. No glass, no reflection, no hands. Fine angular ink lines, carefully controlled hard cel shadows, cool daylight, simple focused composition.'
JOBS['p04_handle_observation_v2']['positive']='Object-only close event CG of an ordinary brass horizontal door lever on a purple wooden door. NO PEOPLE, NO HANDS, NO HAIR. Perspective-correct brass lever and four-screw rectangular backplate, subtle top-surface polished wear and dull adjacent dust remain distinct from a small ordinary rubbed patch underneath. No forensic powder or glowing fingerprints. At far left lower frame the very edge of a CLOSED plain pink notebook sits on a side shelf, no one holds it. Notebook occupies less than ten percent of image. Focus is the door handle surface, muted cool light and finely shaded metal. No labels, no writing, no new clues.'
JOBS['p04_unanswered_phone_v2']['positive']='Object-only close event CG inside a small amusement park service office. 1.9::Beige pushbutton telephone BASE has an EMPTY CRADLE, receiver is OFF THE HOOK and lies separately flat on the wooden desk to its RIGHT, with CLEAR OPEN AIR GAP between base and receiver:: . Coiled cord connects base to separate receiver. Base is large in foreground, keypad contains blank buttons, no display, no lights. A shallow drawer beneath desk is half-open with aged maintenance sheets containing faint ruling only. No readable names or phone numbers. Dim open doorway behind reveals switched-OFF small printer in another room, four simple empty chairs in context. NO PEOPLE, no hands, no reflection. Quiet oppressive scene, anime fine ink and firm cel shading. Do not put receiver back on top of base.'
JOBS['p04_unanswered_phone_v3']=dict(JOBS['p04_unanswered_phone_v2'])
JOBS['p04_unanswered_phone_v3'].update(seed=1729406,
 positive='Close object insert on a worn wooden desk: one intact ordinary beige corded landline telephone. Pushbutton BASE on left, a SINGLE intact complete handset lying flat on desk to right, joined to base by one coiled telephone cord. The handset is one sturdy curved piece with two complete rounded earpieces connected by its bridge, no gaps or detached shell. Empty receiver cradle on top rear of base. Telephone keypad has twelve blank keys. 3/4 view from above, both objects completely visible. No other objects, no scene in background, no people. Muted cool grey wall and dark wood desk. Detailed inked anime object illustration with controlled hard cel shading. This phone is unanswered and off hook, not broken.',
 negative=JOBS['p04_unanswered_phone_v2']['negative']+', broken, shattered, cut receiver, disassembled, hollow earpiece, extra handset, disconnected cable, floating handset, dismantled telephone')
JOBS['p03_dust_boundary_v3']=dict(JOBS['p03_dust_boundary_v2'])
JOBS['p03_dust_boundary_v3'].update(seed=1729404,
 positive='Very close object insert: the lower horizontal wooden ledge of an old outdoor amusement park poster board fills the middle of frame. Entire ledge has a very THIN grey ordinary dust film except for a small irregular patch rubbed away to expose clean warm brown WOOD GRAIN. Rubbed patch is not rectangular paint, not a sticker, not a plaque, not metal; its edge is irregular and feathered. The exposed wood grain continues through the patch. A few darker dust specks cling beside it. Only lower edges of overlapping faded plain cream paper sheets are visible above the ledge. No pictures, no printed figures, no labels, no text, no diagram, no hand, no person. Fine expressive hand-inked anime linework, firm cel shadows, subdued daylight.',
 negative=JOBS['p03_dust_boundary_v2']['negative']+', nameplate, plaque, grey rectangle, paint stripe, fingerprint, sand pile')
JOBS['p04_unanswered_phone_v4']=dict(JOBS['p04_unanswered_phone_v3'])
JOBS['p04_unanswered_phone_v4'].update(seed=1729506,source_image='art/cg_v4/guides/phone_off_hook_guide.png',strength=.46,
 positive='One beige corded pushbutton telephone on a wooden service-office desk. Preserve the exact geometry of this guide: one phone BASE on left with twelve buttons and an EMPTY cradle, ONE single intact receiver on the right with complete connected bridge and two solid earpieces, one dark coiled cable between them. The base has NO additional receiver on it. Unanswered off-hook phone, ordinary undamaged objects, no writing, no faces, no people. Transform the surface rendering into detailed angular anime ink linework, strong contour variation and clean hard cel shadows, subdued cool lighting and dark worn wood. Keep both telephone parts and all spatial contact points in the same positions as guide. No photographic material, no plastic 3D toy look.',
 negative=JOBS['p04_unanswered_phone_v3']['negative']+', receiver on cradle, second handset, handset on base')
JOBS['p04_unanswered_phone_v5']=dict(JOBS['p04_unanswered_phone_v4'])
JOBS['p04_unanswered_phone_v5'].update(seed=1729606,strength=.72,
 style=PROP_STYLE+', 1.8::hand-drawn black ink contour outlines, angular anime cel shading, visible confident pen strokes, illustration, flat color shadow shapes::',
 negative=JOBS['p04_unanswered_phone_v4']['negative']+', 1.6::3d render, clay render, photorealism, plastic toy, smooth gradient shading, unoutlined objects::')
JOBS['p04_unanswered_phone_v6']=dict(JOBS['p04_unanswered_phone_v5'])
JOBS['p04_unanswered_phone_v6'].update(seed=1729706,source_image='art/cg_v4/p04_unanswered_phone_v5.webp',strength=1,
 unsupported_action='Observed HTTP400: nai-diffusion-5-full does not support infill; do not repeat or silently substitute another model.',
 inpaint_polygon=[[458,515],[432,450],[617,223],[748,225],[802,272],[644,520],[505,545]],
 positive='Replace the masked extra handset with the EMPTY recessed receiver cradle of an ordinary beige phone base. Beige plastic cradle surface and its small support tabs are clearly visible, no receiver or handle on top of this base. Match existing angular dark ink contour and flat hard cel shadows, same perspective and base material. The ONE real receiver remains separately on the desk to the right, outside this mask. No added objects, no new buttons or text.')


def export_hd(name, dest, metadata):
    """Keep the paid original; resume HD locally without another generation."""
    from upscale_v4_assets import run as upscale
    hd = metadata.get('hd_file', f'art/hd_v4/cg/{name}.png')
    upscale({'id': 'cg_v4_' + name, 'source': dest.relative_to(ROOT).as_posix(),
             'output': hd, 'family': 'original_cg'})
    metadata.update(hd_file=hd, upscale='4x Real-ESRGAN complete; individual HD review pending',
                    runtime_integrated=False)
    dest.with_suffix('.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n', encoding='utf8')


def main():
    raise SystemExit('NAI generation disabled by latest user instruction; no request sent')
    ap=argparse.ArgumentParser();ap.add_argument('jobs',nargs='+',choices=list(JOBS));ap.add_argument('--use-current-user-key',action='store_true');args=ap.parse_args()
    token=os.environ.get('NAI_TOKEN')
    if not token and args.use_current_user_key:token=token_from_current_user()
    if not token:raise SystemExit('NAI_TOKEN missing; no generation attempted')
    out=ROOT/'art/cg_v4';out.mkdir(parents=True,exist_ok=True)
    for name in args.jobs:
        spec=JOBS[name];dest=out/(name+'.png')
        if spec.get('unsupported_action'):
            print(name,spec['unsupported_action'],'No request sent.');continue
        if dest.exists():
            print(name,'already exists; local HD export only, no paid request')
            metadata=json.loads(dest.with_suffix('.json').read_text(encoding='utf8'))
            export_hd(name,dest,metadata)
            continue
        prompt=spec.get('style',STYLE)+', '+spec['positive'];negative=spec.get('negative',NEG);payload=build_payload(prompt,negative,spec['seed'])
        payload['parameters'].update(width=1536,height=1024)
        guide=None
        if spec.get('source_image'):
            guide=ROOT/spec['source_image']
            with Image.open(guide) as im:
                assert im.size==(1536,1024),'composition guide size mismatch'
                buf=io.BytesIO();im.convert('RGB').save(buf,format='PNG')
            payload['action']='img2img'
            payload['parameters'].update(image=base64.b64encode(buf.getvalue()).decode(),strength=spec.get('strength',.46),noise=.03,extra_noise_seed=spec['seed']+1)
            if spec.get('inpaint_polygon'):
                mask=Image.new('L',(1536,1024),0);ImageDraw.Draw(mask).polygon([tuple(v) for v in spec['inpaint_polygon']],fill=255)
                maskfile=out/(name+'_mask.png');mask.save(maskfile)
                buf=io.BytesIO();mask.save(buf,format='PNG')
                payload['action']='infill';payload['parameters'].update(mask=base64.b64encode(buf.getvalue()).decode(),add_original_image=False)
        try:res=requests.post('https://image.novelai.net/ai/generate-image',json=payload,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},timeout=180)
        except requests.RequestException:
            print(name,'network failure; no automatic paid retry');return
        if res.status_code!=200:
            try:message=json.dumps(json.JSONDecoder().raw_decode(res.text)[0],ensure_ascii=False)
            except (ValueError,TypeError):message='non-JSON error body omitted'
            message=re.sub(r'pst-[A-Za-z0-9_-]+','[REDACTED]',message).replace(token,'[REDACTED]')[:500]
            print(name,'HTTP',res.status_code,message);return
        with zipfile.ZipFile(io.BytesIO(res.content)) as z:
            members=[f for f in z.namelist() if f.lower().endswith('.png')]
            if len(members)!=1:raise RuntimeError('unexpected output count')
            dest.write_bytes(z.read(members[0]))
        with Image.open(dest) as im:
            im.save(dest.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=6)
            metadata={'id':name,'model':payload['model'],'prompt':prompt,'negative_prompt':negative,'seed':spec['seed'],'source':spec['source'],'size':list(im.size),'status':'generated; visual QA pending; not integrated'}
            if guide:metadata.update(generated_action=payload['action'],composition_guide=spec['source_image'],guide_sha256=hashlib.sha256(guide.read_bytes()).hexdigest(),strength=spec.get('strength',.46))
            if spec.get('inpaint_polygon'):metadata.update(mask_file=maskfile.relative_to(ROOT).as_posix(),mask_polygon=spec['inpaint_polygon'])
        dest.with_suffix('.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        export_hd(name,dest,metadata)
        print(name,'generated; visual QA pending')

if __name__=='__main__':main()
