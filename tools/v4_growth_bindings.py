"""Authored FTE completion identity and explicit project growth policy.
No choice scoring, story rewrites, gift reactions or central output writes.
"""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ROUNDS={
 'rin':('20','35','54'),'koto':('21','36','55'),'kaede':('22','40','50'),
 'sho':('23','41','56'),'sora':('24','42','59'),'ai':('25','43','52'),
 'yuu':('26','44','53'),'rei':('27','45','58'),'ken':('28','47','60'),
 'nana':('29','38','57'),'riku':('30','48','61'),'akari':('31','39','62'),
 'satsuki':('32','49','63'),'taiga':('33','46','51'),'haruka':('34','37','64'),
}
ALIASES={'87':'34','88':'29','89':'24','90':'30','143':'20','144':'21','145':'25','146':'26','147':'27','148':'23','149':'32','150':'28','151':'31','152':'33','153':'22'}
SUPPORTED_EFFECTS={'time_pct_5','max_heart','heal_every_3','heal_every_2','revive','showdown_time','showdown_guard','miss_guard','debate_time','voice_lv1','voice_lv2','concentration_lv1','concentration_lv2','right_brain','bed_making','delusion','financing','ponder','undo_enable','safety_first','showdown_tug_half','viability','duet','initial_a','doutanuki','high_tension','beat_heaven','white_lie','two_dimensional_love','paranormal','robot_eye','laser_beam','triger_happy','intuition_of_god','wild_awakening','spark_it','roller_strategy','murder_smash','machine_gun','shotgun','grenade','zero_distance_shooting','ones_minds_eye','shift_down','shift_up','head_start_punch','swap_limit','silent_voice','mieru_goggles','abracadabra','calm_down_lv1','calm_down_lv2'}


def build_growth_contract(sources=None):
    from build_v4_story import Source
    sources=sources or {p.name:Source(p) for p in (ROOT/'docs/design/rewrite_v4').glob('*.md')}
    docs={s.prefix:s for s in sources.values()}
    entries={};flag_index={}
    for actor,rounds in ROUNDS.items():
        for index,prefix in enumerate(rounds,1):
            s=docs[prefix];key=f'{actor}:{index}'
            aliases=[a for a,b in ALIASES.items() if b==prefix]
            flags=['fte:'+p+':complete' for p in [prefix,*aliases]]
            entries[key]={'actor':actor,'episode':index,'sourcePrefix':prefix,'completionFlags':flags,'source':s.ref(1),'title':s.lines[0].lstrip('# ').strip(),'trustChange':False,'unlocksStoryEvidence':False,'xpReward':'GetKakera','xpRewardPolicy':'Own canonical completed encounter awards one relationship-record fragment; no gift/line/choice reward.'}
            for flag in flags:flag_index[flag]=key
    system=ROOT/'docs/design/00_시스템_기획서.md'
    return {
      'schemaVersion':1,'contentVersion':'v4','entries':entries,'flagIndex':flag_index,
      'policy':{'name':'explicit-existing-project-event-reward','eventBond':2,'eventCoins':2,'eventFP':1,'bondThresholds':[0,4,10,18,28],'initialCapacity':6,'capacityPerChapter':2,'maximumCapacity':16,'numericSource':{'file':system.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(system.read_bytes()).hexdigest(),'lines':[199,200,201,202,203,205,216,218,221]},'isOriginalV3NumericClaim':False,'choiceBonus':0,'automaticEquip':False,'capacityPolicy':'actual-player-level-1-to-99; old chapter policy fields retained only for save migration','skillGroupPolicy':'Each nonnegative source numeric group excludes another equipped member of that same group; minus1 has no mutual exclusion. Legacy equivalent-effect groups remain for old saves.','storyEligibilityUsesBondLevel':False},
      'supportedEffects':sorted(SUPPORTED_EFFECTS),
      'effectGroups':{e:('periodic-heal' if e.startswith('heal_every_') else e) for e in sorted(SUPPORTED_EFFECTS)},
      'giftOffers':{},
      'limits':['Only an actual successful FTE completion flag can claim an encounter. A stage/say/choice alone cannot.','Completion is a record of time spent, never agreement, forgiveness, trust or ability disclosure.','All choice consequences and possessions remain in original story flags; no canonical gift is invented from story props.','The base growth builder leaves giftOffers empty. The production publisher explicitly merges the separately authored v4_gift_contract: 15 actor offers, 110 real inventory items and optional reactions. Actual eligible present actors, confirmation, stock and once-per-window receipts gate consumption; story props never become gifts implicitly.','Three authored encounters yield six event bond points under this existing policy. Level-four skills do not silently unlock; no fabricated extra meetings or automatic gifts fill the gap.','FP +1 per newly completed canonical own encounter is own adaptation, not a reproduction of original hidden invitation counters. Existing completed saves receive no retroactive FP.','Twenty-seven masteryActor assignments are own narrative rewards; original character-to-skill assignments and CP shop are not imported. Price0 never means a free FP purchase.']}


if __name__=='__main__':
    destination=ROOT/'tools/v4_growth_contract.json'
    destination.write_text(json.dumps(build_growth_contract(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'entries':45,'completionFlags':60,'output':str(destination),'centralOutputsWritten':False},ensure_ascii=False))
