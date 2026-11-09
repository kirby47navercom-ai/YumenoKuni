#pragma once
void Yumeno::armamentRhythmStart(){
 armRhythmV4.start(chapterAt);armingV4.maxHp=std::max(20000,maxHearts*2000);
 armRhythmV4.speed=armrhythm::speedForDifficulty(difficultyV4.action);
 armingV4.timingAssist=difficultyV4.action==1?4:0;
 // Keep the larger pool without halving the original percentage at risk.
 armingV4.viability*=armingV4.maxHp/10000.f;
 armingV4.hp=int(std::lround(double(v4TaskEntryHp)*armingV4.maxHp/std::max(1,maxHearts*2000)));
 armingV4.totalOpponent=0;for(int hp:armrhythm::phaseBudgets(chapterAt))armingV4.totalOpponent+=hp;
 armingV4.opponent=armingV4.totalOpponent;armQuestionPhase=0;armHits=armLine=0;armBeat=0;rhythmRecent.clear();
 dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
}
void Yumeno::armamentRhythmTick(float delta){
 static const char* keys[]{"w","d","s","a"};std::array<bool,4> edges{},down{};
 for(int i=0;i<4;i++){edges[i]=pressed(keys[i]);down[i]=held.at(keys[i]);}
 int previousHp=armingV4.hp,previousPhase=armRhythmV4.phase;auto events=armRhythmV4.tick(delta,armingV4,edges,down);
 for(const auto& e:events){
  if(e.rating!=trialv4::Rating::None){armHitPoint={e.x*2/3,e.y*2/3};armRatingTime=.45f;
   auto name=e.rating==trialv4::Rating::Critical?"CRITICAL":e.rating==trialv4::Rating::Hit||e.rating==trialv4::Rating::MashSuccess?"HIT":"MISS";
   armvisualv4::texture("ArRating",armStreamBank["labels"].at(name));sfx(e.rating==trialv4::Rating::Critical||e.rating==trialv4::Rating::MashSuccess?"v3se_402":e.rating==trialv4::Rating::Hit?"v3se_403":"v3se_404");
  }
  if(!e.judge)continue;
  if(e.rating==trialv4::Rating::Critical||e.rating==trialv4::Rating::Hit||e.rating==trialv4::Rating::MashSuccess)armVisualHit=.18f;
  if(rhythmRecent.size()>=8)rhythmRecent.erase(rhythmRecent.begin());rhythmRecent.push_back({{"note",armHits++},{"type",e.type},{"wanted",e.button},{"progress",e.progress},{"rating",int(e.rating)},{"hp",armingV4.hp},{"opponent",armingV4.opponent}});
 }
 if(armingV4.hp<previousHp){sfx("v3se_316");debate.hearts=std::max(1,int(std::ceil(double(armingV4.hp)*maxHearts/armingV4.maxHp)));if(armingV4.hp<=0){++retries;v4ResetHearts(maxHearts);armingV4.hp=armingV4.maxHp;restartStage=true;}}
 const auto& transcript=armStreamBank.at("transcripts").at(v4Task.at("taskId").get<std::string>());
 armLine=armvisualv4::phrase(transcript,armRhythmV4,armRhythmV4.deliveredPhrase-1).at("line").get<int>();
 if(previousPhase<armRhythmV4.phase&&stage.contains("phaseFeedback")){
  const auto& feedback=stage.at("phaseFeedback");
  if(previousPhase<int(feedback.size())){v4TaskQueue(feedback.at(previousPhase),"resume");return;}
 }
 if(const auto* n=armRhythmV4.front()){armingV4.current=n->note;armingV4.current.targetSeconds=std::max(.001f,n->target-n->spawn);armBeat=armRhythmV4.clock-n->spawn;armingV4.holdSeconds=n->heldSince>=0?armRhythmV4.clock-n->heldSince:0;}
 armRhythmV4.obscureTick(delta,armingV4);armamentSites();
 int boundary=0;const auto budgets=armrhythm::phaseBudgets(chapterAt);for(int i=0;i<=armQuestionPhase&&i<int(budgets.size());i++)boundary+=budgets[i];
 if(chapterAt==6&&armingV4.totalOpponent-armingV4.opponent>=boundary){armingV4.opponent=armingV4.totalOpponent-boundary;armFinal=0;v4ArmFinalShow();svis("Ring",false);svis("RingCore",false);return;}
 if(armingV4.opponent<=0){armFinal=0;v4ArmFinalShow();svis("Ring",false);svis("RingCore",false);}
}
hb::Json Yumeno::armamentRhythmAuto()const{
 static const char* keys[]{"w","d","s","a"};
 for(const auto& n:armRhythmV4.live)if(!n.done&&n.heldSince>=0){float left=n.note.holdFrames/60.f-(armRhythmV4.clock-n.heldSince);if(left<.04f)return {{"kind","release-after"},{"key",keys[n.note.held]},{"remaining",std::max(0.f,left)/armRhythmV4.speed}};}
 for(const auto& n:armRhythmV4.live)if(!n.done&&n.heldSince<0){float due=n.target-armRhythmV4.clock;
  if(n.note.type==trialv4::NoteType::Mash&&due<.40f&&due>-.25f){int key=n.note.progress%4;for(int i=0;i<4&&held.at(keys[key]);i++)key=(key+1)%4;return {{"kind","rapid-key"},{"key",keys[key]}};}
  if(std::abs(due)<.025f)return {{"kind",n.note.type==trialv4::NoteType::Hold?"hold-key":"key"},{"key",keys[n.note.button]},{"seconds",n.note.holdFrames/60.f/armRhythmV4.speed}};
 }
 return {{"kind","wait"}};
}
