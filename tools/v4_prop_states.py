"""Source-addressed prop state metadata; no model/cook/Game writes or execution.

States describe only an actually executed paragraph after its text is revealed.
Unknown poses and absent assets are explicit. Node visibility is a separate,
small map for existing authored GLB nodes, never an inventory/knowledge action.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[1]


def _source(root,prefix):
    from v4_scene_bindings_more import REVIEWED_FTE_HASHES
    p=next((root/'docs/design/rewrite_v4').glob(prefix+'_자유시간*.md'))
    if hashlib.sha256(p.read_bytes()).hexdigest()!=REVIEWED_FTE_HASHES[prefix]:
        raise ValueError('Prop source changed; inspect exact states '+p.name)
    text=p.read_text(encoding='utf-8-sig')
    return p,text.splitlines(),hashlib.sha256(text.encode('utf-8')).hexdigest()


def build(root=None):
    root=Path(root) if root else ROOT
    from v4_dedicated_spaces import build as dedicated
    spaces=dedicated(root)['spaces'];catalog={};ranges=[];sources={}
    def node_group(space,*prefixes):
        return [n['id'] for n in spaces[space]['nodes'] if any(n['id']==p or n['id'].startswith(p+'.') for p in prefixes)]
    def prop(id,space,nodes=(),visible=False,identity='source-prop-not-yet-modelled'):
        catalog[id]={'space_id':space,'mesh':spaces[space]['mesh'],'meshNodes':list(nodes),
                     'defaultVisible':visible,'identityPolicy':identity,
                     'assetReady':bool(nodes),'runtimeVerified':False,
                     'ownershipOrKnowledgeWrites':False}
    can_nodes=node_group('can_toss_booth','can_0_0','can_0_1','can_0_2','can_1_0','can_1_1','can_2_0','can_metal_rim')
    prop('booth.cans','can_toss_booth',can_nodes,False,'current six-can set; unknown fallen identities/poses must not remain a six-upright stack')
    prop('booth.floorBallModels','can_toss_booth',node_group('can_toss_booth','soft_throw_ball'),False,'authored floor pool; not the source basket/counter/hand transforms')
    prop('shop.neutralFishStock','souvenir_shop',node_group('souvenir_shop','toy_goldfish_body','toy_goldfish_tail','toy_eye','toy_display_mount'),True,'neutral display stock, not a selected/held named fish')
    prop('shop.neutralCarStock','souvenir_shop',node_group('souvenir_shop','toy_car_body','toy_car_wheel'),True,'neutral shelf stock, not Sho\'s bent car or borrowed bus')
    prop('lounge.closedBoxes','hotel_rest_lounge',node_group('hotel_rest_lounge','plain_closed_game_box'),True,'neutral closed storage boxes; never an actual go/ring/puzzle board')
    prop('garden.blankMount','garden_rest_area',node_group('garden_rest_area','blank_drawing_mount'),True,'blank mounting surface, never Rei\'s actual drawing or title')
    prop('washroom.foldedTowelModel','hotel_washroom',node_group('hotel_washroom','folded_shared_towel'),True,'neutral folded towel at the worktable, not the unfolded haircut towel at the mirror')
    for id,space in {
      'booth.balls':'can_toss_booth','booth.canBox':'can_toss_booth',
      'rei.cloth':'hotel_indoor_garden','rei.bucket':'hotel_indoor_garden','rei.handkerchief':'hotel_indoor_garden',
      'rei.originalDrawing':'garden_rest_area','rei.draft':'garden_rest_area','mio.ownDrawing':'garden_rest_area',
      'rei.titleLabel':'garden_rest_area','haruka.haircutTowel':'hotel_washroom','haruka.handMirror':'hotel_washroom',
      'haruka.scissors':'hotel_washroom','haruka.comb':'hotel_washroom',
      'nana.goBoard':'hotel_rest_lounge','nana.goStones':'hotel_rest_lounge',
      'nana.ringBoard':'hotel_rest_lounge','nana.rings':'hotel_rest_lounge',
      'nana.hiddenPictureBook':'hotel_rest_lounge','ai.photoBook':'hotel_rest_lounge','ai.jigsaw':'hotel_rest_lounge',
      'rin.rabbitToy':'souvenir_shop','sho.bentCar':'souvenir_forecourt','sho.busToy':'souvenir_forecourt',
      'rin.oldPaperFoot':'hotel_rest_lounge','rin.clothPouch':'hotel_rest_lounge',
      'ken.heldFish':'souvenir_shop','riku.cards':'souvenir_forecourt',
    }.items():prop(id,space)

    def add(prefix,prop_id,start,end,state,when=(),visibility=None,proof_line=None,perspective='current-observation'):
        if prefix not in sources:sources[prefix]=_source(root,prefix)
        p,lines,digest=sources[prefix];end=end or len(lines)+1;line=proof_line or start
        if not 1<=start<end<=len(lines)+1 or not 1<=line<=len(lines):raise ValueError('Invalid prop source range '+prefix)
        row={'id':f'prop:{prefix}:{prop_id}:{start}:{len(ranges)}','prop':prop_id,
             'source':{'file':p.name,'line':line,'fileSha256':digest,'quote':lines[line-1]},
             'startLine':start,'endLineExclusive':end,'when':[{'flag':f,'equals':v} for f,v in when],
             'state':deepcopy(state),'space_id':catalog[prop_id]['space_id'],
             'mesh':catalog[prop_id]['mesh'],
             'meshNodes':catalog[prop_id]['meshNodes'],'nodeVisibility':{},
             'applyAt':'after-fully-shown','occurrenceScope':'only-if-this-source-node-actually-executes',
             'perspective':perspective,'knowledgeGrant':False,'inventoryGrant':False,
             'poseBound':False,'animationBound':False,'runtimeVerified':False}
        if visibility is not None:
            row['nodeVisibility']={n:visibility for n in row['meshNodes']}
        row['needsAsset']=not catalog[prop_id]['assetReady']
        ranges.append(row);return row

    # A visible generic folded block must not stand in for a cloth laid out by
    # the mirror. The source's actual towel/tools remain explicitly unbound.
    add('37','washroom.foldedTowelModel',7,None,{'depiction':'suppress unrelated folded worktable towel'},visibility=False)
    add('37','haruka.haircutTowel',7,285,{'visible':True,'form':'spread-out-by-mirror','custodian':'haruka','owner':None})
    for start,end in [(105,115),(155,157),(167,203),(207,285)]:
        add('37','haruka.haircutTowel',start,end,{'visible':True,'hair':'small cut strands on towel; no measured count'})
    add('37','haruka.haircutTowel',285,347,{'visible':True,'hair':'gathered and discarded by haruka'})
    add('37','haruka.haircutTowel',347,None,{'visible':None,'location':'unknown after work area is cleared','doNotInferCarryOrReturn':True})
    add('37','haruka.handMirror',23,47,{'visible':True,'custodian':'haruka','owner':'haruka','placement':'taken from own bag'})
    add('37','haruka.handMirror',51,115,{'visible':True,'custodian':'mio','owner':'haruka','placement':'held; exact angle unbound'})
    add('37','haruka.handMirror',131,157,{'visible':True,'custodian':'haruka','owner':'haruka','placement':'standing on sink'})
    add('37','haruka.handMirror',167,203,{'visible':True,'custodian':'haruka','owner':'haruka','placement':'standing on sink'})
    for value,who,place in [('A1','mio','held'),('A2','haruka','standing on sink'),('A3','haruka','standing on sink')]:
        add('37','haruka.handMirror',207,355,{'visible':True,'custodian':who,'owner':'haruka','placement':place},[('F-HA02-A',value)])
    add('37','haruka.handMirror',355,None,{'visible':False,'custodian':'haruka','owner':'haruka','placement':'taken away by owner; no photograph made'})
    for name in ['scissors','comb']:
        add('37','haruka.'+name,7,347,{'visible':True,'custodian':'haruka','owner':None,'reflectionOrHandMotion':'unbound'})
        add('37','haruka.'+name,347,None,{'visible':False,'custodian':'haruka','returnStatus':'intended-not-observed','sourceLimit':'Going to return it is not an observed completed return.'})

    # Papers are distinct authored works, not original/copy or a joint gift.
    add('45','rei.originalDrawing',7,17,{'visible':True,'owner':'rei','face':'down','placement':'table'})
    add('45','rei.originalDrawing',17,349,{'visible':True,'owner':'rei','face':'up','placement':'table','bench':'empty; not an erased Mio portrait'})
    add('45','rei.originalDrawing',177,349,{'pillarWidth':'corrected by rei'},[('F-RE02-A','A1')])
    add('45','rei.originalDrawing',309,349,{'footboard':'added by rei'},[('F-RE02-B','B1')])
    add('45','mio.ownDrawing',303,311,{'visible':True,'owner':'mio','subject':'own footboard drawing on separate paper'})
    add('45','mio.ownDrawing',311,333,{'visible':False,'owner':'mio','placement':'taken with mio'},[('F-RE02-B','B1')])
    add('45','rei.draft',355,369,{'visible':True,'owner':'rei','placement':'shown then kept behind original; not gifted'})
    add('45','rei.draft',369,None,{'visible':True,'owner':'rei','placement':'rei takes out and keeps draft after mio left','mioObserved':False},perspective='objective-unseen-by-mio')
    add('58','rei.originalDrawing',8,208,{'visible':True,'owner':'rei','placement':'table; original shown at line22'})
    add('58','rei.originalDrawing',8,None,{'pillarWidth':'previously corrected by rei'},[('F-RE02-A','A1')],proof_line=442)
    add('58','rei.originalDrawing',8,None,{'footboard':'previously added by rei'},[('F-RE02-B','B1')],proof_line=58)
    add('58','mio.ownDrawing',58,548,{'visible':True,'owner':'mio','placement':'own separate paper brought out'},[('F-RE02-B','B1')])
    add('58','rei.draft',8,76,{'visible':False,'owner':'rei','placement':'behind original; not yet brought out'})
    add('58','rei.draft',76,200,{'visible':True,'owner':'rei','placement':'shown on table today; previous unobserved exit scene grants no knowledge'})
    add('58','rei.originalDrawing',208,342,{'visible':True,'owner':'rei','placement':'existing notice board','title':'neutral title and own name; exact words unprovided'},visibility=None)
    add('58','garden.blankMount',208,342,{'depiction':'blank mount cannot represent posted actual artwork'},visibility=False)
    add('58','rei.titleLabel',218,342,{'visible':True,'owner':'rei','text':None,'textStatus':'author/title exist; exact literal title not supplied'})
    add('58','rei.originalDrawing',354,374,{'visible':True,'owner':'rei','placement':'being put in ordinary envelope; not lent to mio'})
    add('58','rei.originalDrawing',374,484,{'visible':False,'owner':'rei','placement':'flat inside ordinary envelope; bag from456','damage':'none newly wet/torn/cut'})
    add('58','rei.originalDrawing',494,548,{'visible':True,'owner':'rei','placement':'table; still there at last Mio observation'})
    add('58','rei.originalDrawing',548,550,{'visible':False,'owner':'rei','placement':'table last observed; later move unknown','mioObservedLater':False})
    for choice,place,visible in [('B1','notice board',True),('B2','rei bag in ordinary envelope',False)]:
        add('58','rei.originalDrawing',554,566,{'visible':visible,'owner':'rei','placement':place},[('F-RE03-B',choice)])
    add('58','garden.blankMount',554,566,{'depiction':'posted actual artwork must use its own asset'},[('F-RE03-B','B1')],visibility=False)
    add('58','rei.titleLabel',554,566,{'visible':True,'text':None,'textStatus':'neutral title and rei author label; literal title unknown'},[('F-RE03-B','B1')])
    add('58','rei.draft',554,566,{'visible':False,'owner':'rei','placement':'own bag; distinct from original'})
    add('58','mio.ownDrawing',554,566,{'visible':False,'owner':'mio','placement':'taken back by mio'},[('F-RE02-B','B1')])

    # Plant wiping changes actual participation, not every plant's biological
    # identity. No watering can or Rei's home table appears in this garden.
    add('27','rei.bucket',7,391,{'visible':True,'owner':None,'placement':'beside rei; rinse water','wateringCanPresent':False})
    add('27','rei.cloth',7,317,{'visible':True,'custodian':'rei','placement':'working cloth','pose':'unbound'})
    add('27','rei.cloth',63,83,{'mioHasSpareCloth':True,'plasticLeaf':'detached then reinserted at75'})
    add('27','rei.cloth',317,319,{'placement':'rei puts cloth in bucket'})
    add('27','rei.cloth',347,359,{'mioHasSpareCloth':True,'workedArea':'fronts of adjacent row only'})
    add('27','rei.cloth',359,375,{'mioCloth':'rinsed, wrung, beside bucket'},[('F-RE01-A','A1')])
    add('27','rei.cloth',359,375,{'mioCloth':'rinsed, wrung, beside bucket'},[('F-RE01-B','B2')])
    add('27','rei.handkerchief',375,391,{'visible':True,'owner':'rei','gift':False,'mioUse':'only actual acceptance/decline branch; never automatic ownership'})

    # Missing named objects remain separate from generic display geometry.
    for pre,prop_id,start,end,state in [
      ('20','rin.rabbitToy',186,220,{'owner':None,'condition':'one foot absent; paper first fails','location':'handled by rin'}),
      ('20','rin.rabbitToy',220,344,{'owner':None,'condition':'paper replacement foot; still turns; exact path not bound'}),
      ('20','rin.rabbitToy',344,418,{'owner':None,'location':'shelf','condition':'short distance can stand; not fully repaired'}),
      ('20','rin.rabbitToy',418,426,{'owner':None,'custodian':'mio','location':'briefly on palm; no gift'}),
      ('20','rin.rabbitToy',426,None,{'owner':None,'custodian':None,'location':'shelf','mioOwnership':False}),
      ('28','ken.heldFish',17,47,{'owner':None,'custodian':'mio','location':'held for role play; not gifted'}),
      ('28','ken.heldFish',339,409,{'owner':None,'custodian':'mio','location':'held in selected second role play'}),
      ('28','ken.heldFish',409,None,{'owner':None,'custodian':None,'location':'returned to shelf; ken adjusts direction455'}),
      ('41','sho.bentCar',7,507,{'owner':None,'custodian':'sho','location':'forecourt table/actual selected play','condition':'bent front axle unchanged; price tag retained'}),
      ('41','sho.busToy',523,525,{'owner':None,'custodian':'sho','location':'actually borrowed for himself; price tag retained'}),
      ('41','sho.bentCar',543,553,{'owner':None,'custodian':'sho','location':'outer bag compartment','condition':'still bent; cord retained only if prior B'}),
      ('30','riku.cards',37,215,{'owner':'riku','count':3,'faces':'one heart/two clubs, unequal numbers','noInventedMark':True}),
      ('30','riku.cards',273,415,{'owner':'riku','custodian':'mio','count':3,'noInventoryTransfer':True}),
      ('30','riku.cards',415,443,{'owner':'riku','custodian':'mio','location':'counted then placed; exact orientation unbound'}),
      ('30','riku.cards',443,None,{'owner':'riku','custodian':'riku','location':'riku remains at table; no unseen later shuffle'}),
    ]:add(pre,prop_id,start,end,dict(visible=True,**state))
    for choice,prop_id,visible in [('A','sho.busToy',True),('B','sho.busToy',False),('C','sho.bentCar',True)]:
        add('41',prop_id,553,None,{'visible':visible,'custodian':'sho' if visible else None,'owner':None},[('SHO-02B',choice)])

    # Game/books: source result fields are not fabricated board coordinates.
    for pre,prop_id,start,end,state in [
      ('29','nana.goBoard',9,455,{'visible':True,'placement':'table','rules':'normal then only selected current variant'}),
      ('29','nana.goStones',9,115,{'visible':True,'blackPlayer':'mio','whitePlayer':'nana','result':'mio first five at95; nana could have blocked'}),
      ('29','nana.goStones',147,179,{'visible':True,'result':'nana white five; prior black placement not undone'}),
      ('29','nana.goStones',185,215,{'visible':True,'blackFiveRetained':True,'whiteStones':'nana gathers into pot; not restored'}),
      ('29','nana.goStones',327,353,{'visible':True,'result':'nana white five loses under agreed reverse rule'}),
      ('29','nana.goStones',359,427,{'visible':True,'form':'temporary black face/white train drawing; not a real train'}),
      ('38','nana.ringBoard',9,453,{'visible':True,'form':'short posts, exact geometry not present'}),
      ('38','nana.rings',9,103,{'visible':True,'physicalTotal':5,'storedTogether':True,'earlierPractice':'not part of later score'}),
      ('38','nana.rings',103,207,{'visible':True,'physicalTotal':5,'result':'same-distance new game nana3/mio1; each5throws, reused rings'}),
      ('38','nana.rings',207,293,{'visible':True,'physicalTotal':5,'result':'different-distance new game nana2/mio2; not same-skill draw'}),
      ('38','nana.rings',293,349,{'visible':True,'physicalTotal':5,'result':'unscored play; one post remains empty'}),
      ('38','nana.rings',423,435,{'visible':False,'placement':'gathered; they drink water'}),
      ('38','nana.ringBoard',453,None,{'visible':True,'placement':'upright on shelf; no permanent equal-distance marker'}),
      ('43','ai.photoBook',9,255,{'visible':True,'owner':None,'custodian':'ai','content':'aquarium photos; shared seal photo only A2'}),
      ('43','ai.photoBook',255,333,{'visible':True,'open':False,'custodian':'ai'}),
      ('43','ai.jigsaw',101,139,{'visible':True,'form':'park panorama pieces on table'}),
      ('43','ai.jigsaw',139,229,{'visible':False,'form':'box closed at table end; no puzzle progress'}),
      ('43','ai.jigsaw',229,255,{'visible':True,'form':'mio silently tries border pieces; no forced completed puzzle'}),
      ('43','ai.photoBook',139,229,{'visible':True,'open':True,'placement':'between two readers; shared seal photos'}),
      ('43','ai.jigsaw',351,367,{'visible':True,'form':'actual puzzle progress; blue piece missing then found in sleeve'}),
      ('43','ai.photoBook',369,383,{'visible':True,'open':True,'page':'back viewing route; no actual aquarium visit'}),
      ('52','ai.photoBook',7,65,{'visible':True,'open':False,'placement':'ai lap'}),
      ('52','ai.photoBook',65,209,{'visible':True,'open':True,'placement':'turned on ai lap; not shared centrally'}),
      ('52','ai.photoBook',339,None,{'visible':False,'placement':'returned to lounge shelf on exit; not a gift'}),
      ('57','nana.hiddenPictureBook',8,96,{'visible':True,'owner':None,'custodian':'nana','open':True}),
      ('57','nana.hiddenPictureBook',96,326,{'visible':True,'page':'harbour; turtle not yet marked except actual A2 finding'}),
      ('57','nana.hiddenPictureBook',158,168,{'visible':True,'page':'harbour; rope turtle circled by nana; mio sees on return'}),
      ('57','nana.hiddenPictureBook',326,372,{'visible':True,'page':'park dining table; own selected umbrella/key search only'}),
      ('57','nana.hiddenPictureBook',380,382,{'visible':False,'lastObservedOpen':True,'location':'nana at lounge, last observed only','laterSolvingObserved':False}),
      ('57','nana.hiddenPictureBook',398,410,{'visible':True,'open':False,'answerPageOpened':False}),
      ('57','nana.hiddenPictureBook',410,418,{'visible':False,'custodian':'nana','placement':'own bag; no new solution'}),
    ]:add(pre,prop_id,start,end,state)
    for choice in ['B1','B2']:
        add('29','nana.goBoard',455,459,{'visible':False,'form':'pots closed and board folded in observed cleanup'},[('F-NA01-B',choice)])
    add('29','nana.goBoard',455,459,{'visible':None,'laterCleanupObserved':False},[('F-NA01-B','B3')])
    for choice in ['A1','A3']:
        add('43','ai.jigsaw',255,333,{'visible':True,'form':'actual unfinished pieces; no A2-only shared photo history'},[('F-AI02-A',choice)])
    add('43','ai.jigsaw',255,333,{'visible':False,'form':'box remains closed'},[('F-AI02-A','A2')])
    add('57','nana.hiddenPictureBook',188,326,{'turtleFound':True,'turtleMarkedBy':'nana'},[('F-NA03-A','A2')],proof_line=158)
    for choice in ['A1','A3']:
        add('57','nana.hiddenPictureBook',188,326,{'turtleFound':False,'noNewAnswerMark':True},[('F-NA03-A',choice)],proof_line=326)

    # Late introductions and follow-up possession do not replay the earlier
    # object transaction or turn a different rabbit into the repaired one.
    for pre,prop_id,start,end,state in [
      ('143','rin.rabbitToy',17,59,{'visible':False,'identity':'the dawn-corridor rabbit is NOT here; a different shelf individual is sought'}),
      ('143','rin.rabbitToy',91,107,{'visible':True,'identity':'the individual actually retrieved yesterday','condition':'paper foot; not the dawn rabbit'}),
      ('147','rei.cloth',7,105,{'visible':True,'custodian':'rei','mioHasSpareCloth':False}),
      ('147','rei.bucket',7,105,{'visible':True,'placement':'beside rei; mio steps around it'}),
      ('147','rei.originalDrawing',111,129,{'visible':True,'owner':'rei','face':'down','placement':'rest table'}),
      ('148','sho.bentCar',85,107,{'visible':True,'custodian':'sho','condition':'bent axle, unchanged','placement':'forecourt table'}),
      ('150','ken.heldFish',7,93,{'visible':True,'custodian':None,'placement':'shelf; ken does not hand it over at15'}),
      ('150','ken.heldFish',93,107,{'visible':True,'custodian':None,'placement':'brief Mio handoff then put on counter within same paragraph'}),
      ('88','nana.goBoard',9,143,{'visible':True,'placement':'today first personal game, not replay of an earlier game'}),
      ('88','nana.goStones',9,109,{'visible':True,'blackPlayer':'mio','whitePlayer':'nana','earlierGameGranted':False}),
      ('88','nana.goStones',109,139,{'visible':True,'form':'actual replacement figure; do not resurrect the deceased face from original29'}),
      ('88','nana.ringBoard',147,181,{'visible':True,'newGoBoardOpened':False}),
      ('88','nana.rings',147,181,{'visible':True,'physicalTotal':5,'placement':'current ring game; no new shared picture disclosure'}),
      ('90','riku.cards',9,79,{'visible':True,'owner':'riku','placement':'beside shop table; no first-attempt success granted'}),
      ('35','rin.rabbitToy',8,96,{'visible':True,'condition':'old paper foot is worn; toy stops after two steps; no new foot yet'}),
      ('35','rin.oldPaperFoot',96,234,{'visible':True,'custodian':'rin','owner':None,'placement':'beside toy; not automatically given to mio'}),
      ('35','rin.rabbitToy',120,234,{'visible':True,'condition':'work stopped after public disclosure; no completed replacement'}),
      ('35','rin.rabbitToy',312,328,{'visible':True,'condition':'new foot actually attached; walks straighter; mio held body only in this branch'}),
      ('35','rin.oldPaperFoot',328,350,{'visible':True,'custodian':'mio','owner':'mio','placement':'on palm; actually received only this branch'}),
      ('35','rin.oldPaperFoot',350,358,{'visible':False,'custodian':'mio','owner':'mio','placement':'small pocket'}),
      ('35','rin.rabbitToy',350,358,{'visible':True,'condition':'new foot attached by rin alone; mio only watched'}),
      ('35','rin.rabbitToy',366,398,{'visible':True,'condition':'new foot attached by rin alone using small support frame'}),
      ('35','rin.rabbitToy',410,None,{'visible':True,'placement':'returned to souvenir shelf; no ownership transferred to mio'}),
      ('54','rin.clothPouch',8,210,{'visible':True,'owner':'rin','condition':'personal cloth, not finished pouch or tool container'}),
      ('54','rin.clothPouch',210,522,{'visible':True,'owner':'rin','condition':'existing holes and blunt-ended cord; no needles, shoulder strap or new handle'}),
    ]:add(pre,prop_id,start,end,state)
    for value,prop_id in [('A','sho.busToy'),('C','sho.bentCar')]:
        add('56',prop_id,22 if value=='A' else 48,418,{'visible':True,'custodian':'sho','owner':None,'borrowedFrom41':True},[('SHO-02B',value)])
        add('56',prop_id,422,438,{'visible':False,'custodian':'sho','placement':'separate outer bag compartment'},[('SHO-02B',value)])
    for id in ['sho.busToy','sho.bentCar']:
        add('56',id,8,418,{'visible':False,'custodian':None,'borrowedFrom41':False},[('SHO-02B','B')])

    _cans(add,catalog)
    # Split portable-prop ranges at already reviewed exact scene transitions.
    # This changes no room geometry and prevents a mobile object from staying
    # tied to its asset-library home set after an observed room transition.
    from v4_scene_bindings_more import FTE_RUNS
    from v4_dedicated_spaces import _space
    split=[]
    for row in ranges:
        prefix=row['source']['file'].split('_')[0];runs=FTE_RUNS[prefix]
        cuts=sorted({row['startLine'],row['endLineExclusive']}|{n for n,_ in runs if row['startLine']<n<row['endLineExclusive']}|{n for n in {'55':[24],'147':[111]}.get(prefix,[]) if row['startLine']<n<row['endLineExclusive']})
        for start,end in zip(cuts,cuts[1:]):
            item=deepcopy(row);item.update(startLine=start,endLineExclusive=end)
            base=next(space for n,space in reversed(runs) if n<=start)
            item['space_id']=_space(prefix,start,base)
            item['id']=row['id']+':'+str(start)
            split.append(item)
    ranges=split
    # Conditional common merges refer only to flags already emitted by current
    # compiled graphs, never a guessed spelling or a flag set by this adapter.
    flags=set()
    for p in (root/'data/v4_story/freetime').glob('*.json'):
        g=json.loads(p.read_text(encoding='utf-8'))
        for n in g.get('nodes',{}).values():
            for option in n.get('options',[]):flags.update(option.get('set',{}))
            for case in n.get('cases',[]):
                if 'flag' in case:flags.add(case['flag'])
    for row in ranges:
        for condition in row['when']:
            if condition['flag'] not in flags:raise ValueError('No such actual graph flag '+condition['flag'])
    return {'schemaVersion':1,'catalog':catalog,'ranges':ranges,'spaceMeshes':{id:s['mesh'] for id,s in spaces.items()},
      'conditionalSceneRanges':conditional_scenes(root),
      'defaults':[{'prop':id,'space_id':p['space_id'],'mesh':p['mesh'],
                   'nodeVisibility':{n:p['defaultVisible'] for n in p['meshNodes']}} for id,p in catalog.items() if p['meshNodes']],
      'unbound':[{'prop':id,'reason':'Exact source prop has no approved matching runtime mesh; decorative stock is not an identity substitute.'} for id,p in catalog.items() if not p['assetReady']],
      'lifecycle':{'match':'actual source file + hash + one-based line interval, all when equalities, after fully shown',
                   'reset':'Restore mesh defaults when leaving the occurrence or changing scene/graph/load. Do not carry unknown later cleanup into prior source scenes.',
                   'merge':'Row order within matching ranges: patch logical state and nodeVisibility only. Do not persist to narrative flags/inventory.',
                   'knowledge':'Reported memory and objective-after-exit rows never grant Mio observation.',
                   'unknownPose':'Suppress an incompatible baked pose; expose unresolved state for a real renderer solution, not fake motion or arbitrary can identities.'},
      'scope':'Current six dedicated production sets and directly reviewed corresponding personal-time props; no claim of every object in the full manuscript.',
      'writesFiles':False,'runtimeVerified':False}


def _cans(add,catalog):
    full=catalog['booth.cans']['meshNodes']
    # Rims are separate mesh objects and must follow their actual can body.
    top={'can_2_0','can_metal_rim.010','can_metal_rim.011'}
    row=add('42','booth.cans',7,93,{'total':6,'upright':5,'setDown':1,'pose':'top can set down; where it is put is unbound'},visibility=True)
    row['nodeVisibility'].update({n:False for n in top})
    for pre,start,end,state in [
      ('42',93,99,{'upright':3,'fallen':3,'outside':2,'actor':'mio'}),
      ('42',99,113,{'upright':0,'fallen':6,'outside':5,'actor':'sora'}),
      ('42',115,121,{'upright':0,'fallen':6,'actor':'mio','line':'near'}),
      ('42',121,129,{'upright':1,'fallen':5,'actor':'sora','line':'back'}),
      ('42',129,135,{'upright':0,'fallen':6,'lastOne':'sora lowers by hand; not added to score'}),
      ('42',141,149,{'upright':5,'fallen':1,'actor':'mio','throw':1,'eachThrowResetsAllSix':True}),
      ('42',149,153,{'upright':3,'fallen':3,'actor':'sora','throw':1}),
      ('42',153,165,{'upright':4,'fallen':2,'actor':'mio','throw':2}),
      ('42',171,179,{'upright':6,'fallen':0,'actor':'sora','throw':2}),
      ('42',179,187,{'upright':5,'fallen':1,'actor':'mio','throw':3}),
      ('42',187,207,{'upright':2,'fallen':4,'actor':'sora','throw':3,'scores':{'mio':4,'sora':7}}),
      ('42',239,267,{'upright':0,'fallen':6,'freshGame':True,'scores':{'sora':4,'yuu':6},'oneThrowEach':True}),
      ('42',267,277,{'upright':0,'heldBy':'sora','heldColour':'blue','heldCount':1,'pose':'picked from floor; identity not specified'}),
      ('42',291,301,{'upright':None,'outside':4,'freshGame':True,'scores':{'mio':3,'sora':4},'oneThrowEach':True}),
      ('42',309,317,{'upright':1,'fallen':5,'layout':'low and wide','score':5}),
      ('42',317,335,{'upright':2,'fallen':4,'layout':'three pairs, final right pair remains','threeThrowsUsed':True}),
      ('42',335,337,{'uprightStack':0,'state':'last two standing cans lowered manually; not retroactive success'}),
      ('59',8,66,{'total':6,'pose':'taken out, top lowered at16; completed starting arrangement not shown'}),
      ('59',66,100,{'upright':2,'outside':4,'actor':'mio','throwsUsed':'1 then2; second misses'}),
      ('59',100,108,{'upright':1,'outside':5,'actor':'mio','throwsUsed':3}),
      ('59',108,126,{'upright':6,'outside':0,'state':'reset to first arrangement'}),
      ('59',126,138,{'upright':4,'outside':2,'actor':'sora','throwsUsed':1}),
      ('59',138,176,{'upright':2,'outside':4,'actor':'sora','throwsUsed':'2 then3; last misses'}),
      ('59',176,256,{'upright':6,'state':'stack restored; no new game yet','scores':{'mio':5,'sora':4}}),
      ('59',256,266,{'upright':None,'outside':3,'actor':'riku','throwsUsed':3,'firstGameUnchanged':True}),
      ('59',326,328,{'uprightStack':0,'location':'original box; actual joint cleanup'}),
      ('59',342,368,{'uprightStack':0,'state':'standing cans lowered, no new throws'}),
      ('59',376,382,{'upright':None,'outside':3,'actor':'riku','freshThreePersonGame':True,'scores':{'sora':5,'mio':4,'riku':3}}),
      ('59',382,384,{'uprightStack':0,'state':'three participants actually tidy their cans'}),
    ]:
        exact_full=pre=='59' and start in [108,176]
        when=[]
        if pre=='42':
            if 93<=start<113:when=[('SORA-02A','A')]
            elif 115<=start<135:when=[('SORA-02A','B')]
            elif 141<=start<207:when=[('SORA-02A','C')]
            elif start==291:when=[('SORA-02B','A')]
            elif 309<=start<337:when=[('SORA-02B','B')]
        elif pre=='59':
            if start==256:when=[('SORA-03A','A2')]
            elif start==326:when=[('SORA-03A','A1'),('SORA-03B-A','B2')]
            elif start==342:when=[('SORA-03A','A2')]
            elif start in [376,382]:when=[('SORA-03A','A2'),('SORA-03B-B','B2')]
        row=add(pre,'booth.cans',start,end,dict(total=6,**{k:v for k,v in state.items() if k!='total'}),when,visibility=exact_full)
        if exact_full:row['poseBound']=True
    for value,state in [('A',{'upright':0,'fallen':6,'outside':5}),('B',{'upright':0,'fallen':6,'lastOneLoweredByHand':True}),('C',{'upright':2,'fallen':4})]:
        add('42','booth.cans',207,239,state,[('SORA-02A',value)],visibility=False,proof_line={'A':99,'B':129,'C':187}[value])
    add('42','booth.cans',343,363,{'total':6,'upright':6,'state':'reset to first shape before leaving'},[('SORA-02B','C')],visibility=True)['poseBound']=True
    ranges_full=add('59','booth.cans',280,326,{'total':6,'upright':6,'state':'first restored stack; no extra game'},[('SORA-03A','A1')],visibility=True)
    ranges_full['poseBound']=True
    add('59','booth.cans',328,338,{'total':6,'upright':6,'state':'last observed stack before leaving; subsequent solo cleanup unknown'},[('SORA-03A','A1'),('SORA-03B-A','B3')],visibility=True)['poseBound']=True
    for pre,start,end in [('42',7,363),('59',8,278),('59',280,306),('59',318,338),('59',340,390)]:
        add(pre,'booth.floorBallModels',start,end,{'depiction':'Suppress floor trio: source uses counter/basket/hand, not this baked floor arrangement'},visibility=False)
        add(pre,'booth.balls',start,end,{'physicalTotal':3 if pre=='42' else None,
            'throwsPerPlayer':3 if pre=='59' else None,'meshTransform':'unbound','ownershipTransfer':False,
            'sourceLimit':'Three throws do not prove a basket contains exactly three physical balls.' if pre=='59' else 'Three soft balls explicitly placed on counter.'})
    add('59','booth.canBox',326,328,{'visible':True,'containsCans':6,'owner':None,'pose':'original box exact transform unbound'})
    # The after-exit variants do not assert Sora tidied unseen or a fourth throw.
    for start,end in [(278,280),(306,318),(338,340),(390,394)]:
        add('59','booth.cans',start,end,{'visible':False,'upright':None,'currentPoseKnown':False,'laterCleanupObserved':False,'laterGameObserved':False,'placement':'last observed only'},visibility=False)


def resolve(bundle,source,flags=None,space_id=None,fully_shown=True):
    """Reference consumer; does not mutate bundle/flags or invent saved state."""
    if not fully_shown:return {'deferred':True,'nodeVisibility':{},'states':{},'unresolved':[]}
    flags=flags or {};matches=[];file=source.get('file');line=source.get('line',0)
    known={r['source']['fileSha256'] for r in bundle['ranges'] if r['source']['file']==file}
    if known and source.get('fileSha256') not in known:raise ValueError('Prop runtime source hash differs '+str(file))
    for row in bundle['ranges']:
        if row['source']['file']!=file or not row['startLine']<=line<row['endLineExclusive']:continue
        if space_id and row['space_id']!=space_id:continue
        if all(flags.get(c['flag'])==c['equals'] for c in row['when']):matches.append(row)
    visible={};states={};unresolved=[]
    for default in bundle['defaults']:
        if not space_id or default['space_id']==space_id:visible.update(default['nodeVisibility'])
    for row in matches:
        if not space_id or row['mesh']==bundle['spaceMeshes'].get(space_id):visible.update(row['nodeVisibility'])
        states.setdefault(row['prop'],{}).update(deepcopy(row['state']))
        if row['needsAsset'] or not row['poseBound']:
            unresolved.append({'row':row['id'],'prop':row['prop'],'needsAsset':row['needsAsset'],'poseBound':row['poseBound'],'animationBound':False})
    return {'deferred':False,'nodeVisibility':visible,'states':states,'unresolved':unresolved,
            'matchedRows':[r['id'] for r in matches],'knowledgeGrant':False,'inventoryGrant':False}


def apply_scene_bindings(scene_data,root=None):
    bundle=build(root);scene_data['propStateRanges']=deepcopy(bundle['ranges'])
    scene_data['propCatalog']=deepcopy(bundle['catalog']);scene_data['propDefaults']=deepcopy(bundle['defaults'])
    scene_data['propStateLifecycle']=deepcopy(bundle['lifecycle'])
    # Static source-only matching cannot choose the physical place of this
    # shared closing dialogue. The runtime must select the actual current B.
    existing=scene_data.setdefault('conditionalSceneRanges',[])
    for row in bundle['conditionalSceneRanges']:
        if not any(x.get('id')==row['id'] for x in existing):existing.append(deepcopy(row))
    return {'stateRanges':len(bundle['ranges']),'logicalProps':len(bundle['catalog']),
            'unboundAssets':len(bundle['unbound']),'runtimeVerified':False}


def conditional_scenes(root=None):
    root=Path(root) if root else ROOT;p,lines,digest=_source(root,'43')
    return [{'id':'fte43-current-exit-place:'+choice,
             'source':{'file':p.name,'line':407,'fileSha256':digest,'quote':lines[406]},
             'startLine':407,'endLineExclusive':455,
             'when':[{'flag':'F-AI02-B','equals':choice}], 'space':space,
             'perspective':'current-observation','knowledgeGrant':False,
             'bindingStatus':'requires-runtime-flag-selection',
             'missingFlagPolicy':'unbound; do not fall back to hotel lounge',
             'geometryPolicy':'Existing production set for the source-described kitchen fork / lounge exit / pre-exit seat; no measured new topology.'}
            for choice,space in [('B1','kitchen'),('B2','hotel_corridor'),('B3','hotel_rest_lounge')]]


def resolve_scene(bundle,source,flags):
    rows=[r for r in bundle['conditionalSceneRanges'] if r['source']['file']==source.get('file') and r['source']['fileSha256']==source.get('fileSha256') and r['startLine']<=source.get('line',0)<r['endLineExclusive']]
    matched=[r for r in rows if all(flags.get(c['flag'])==c['equals'] for c in r['when'])]
    if len(matched)>1:raise ValueError('Conflicting current scene conditions')
    return {'handled':bool(rows),'space':matched[0]['space'] if matched else None,
            'status':'bound-current-choice' if matched else 'unbound-current-choice' if rows else 'outside-conditional-scope'}
