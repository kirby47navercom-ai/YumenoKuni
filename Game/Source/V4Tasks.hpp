// Authored native tasks: input resolves a task; dialogue never supplies a free pass.
void Yumeno::v4NoiseReset(){
 if(!noiseSeV4.empty()){Audio::Stop(noiseSeV4);noiseSeV4.clear();}noiseSeTimeV4=0;silencerV4.reset(true);noiseGainTimeV4=0;for(int i=0;i<3;i++)UI::SetVisible(this,UI_ID,"SilenceShot"+std::to_string(i),false);UI::SetVisible(this,UI_ID,"NoiseGain",false);
}
bool Yumeno::v4NoiseBreak(int at,int power){
 if(at<0||at>=int(debate.lines.size()))return false;auto before=debate.noiseGlyphs(at);
 auto result=silencerv4::clear(debate,at,debateTime,trialScoreInitial/60,power);if(!result.changed&&!result.damaged)return false;
 debate.shatterNoiseTransition(at,before);sfx("v3se_307");
 if(result.reward>0){noiseGainTimeV4=.8f;UI::SetText(this,UI_ID,"NoiseGain","+"+std::to_string(result.reward));UI::SetPosition(this,UI_ID,"NoiseGain",{aimX-60,aimY-55});UI::SetVisible(this,UI_ID,"NoiseGain",true);}
 return true;
}

bool Yumeno::v4NoiseInput(float delta){
 debate.tickNoiseDebris(delta);noiseSeTimeV4=std::max(0.f,noiseSeTimeV4-delta);
 bool held=this->held.at("mouse1"),remote=pressed("r")&&skillOn("zero_distance_shooting"),machine=skillOn("machine_gun"),shotgun=skillOn("shotgun"),grenade=skillOn("grenade");if(remote)silencerV4.remotePending=true;
 silencerV4.fraction+=std::max(0.f,delta)*60;int frames=int(silencerV4.fraction+1e-5f);silencerV4.fraction=std::max(0.f,silencerV4.fraction-frames);bool fired=false;
 for(int i=0;i<frames;i++){
  auto mode=silencerV4.tick(held,machine,shotgun,grenade,silencerV4.remotePending,holdTime<0&&shotRecoveryV4.ready()&&!this->held.at("mouse0"));if(mode==silencerv4::Mode::None)continue;
  if(mode==silencerv4::Mode::Remote)silencerV4.remotePending=false;auto hit=silencerv4::targets(debate,mode,aimX,aimY);auto& pulse=silencerV4.pulses[silencerV4.lastSlot];if(mode==silencerv4::Mode::Remote&&hit.empty()){pulse.life=0;silencerV4.cooldown=0;continue;}fired=true;if(noiseSeTimeV4<=0&&hasAudio("v3se_351")){noiseSeV4=Audio::Play(art["audio"]["v3se_351"].get<std::string>(),1.f,1.f,"sfx");noiseSeTimeV4=std::max(.1f,audioLen("v3se_351"));}pulse.x=aimX;pulse.y=aimY;
  if(mode==silencerv4::Mode::Remote&&!hit.empty()){auto glyphs=debate.noiseGlyphs(hit[0]);if(!glyphs.empty()){pulse.x=glyphs[glyphs.size()/2].x;pulse.y=glyphs[glyphs.size()/2].y;}}
  for(int at:hit)v4NoiseBreak(at,mode==silencerv4::Mode::Blast?2:mode==silencerv4::Mode::Remote?debate.lines[at].noiseDurability:1);
 }
 if(!held&&!noiseSeV4.empty()){Audio::Stop(noiseSeV4);noiseSeV4.clear();noiseSeTimeV4=0;}
 for(int i=0;i<3;i++){const auto& p=silencerV4.pulses[i];auto id="SilenceShot"+std::to_string(i);UI::SetVisible(this,UI_ID,id,p.life>0);if(p.life>0){UI::SetPosition(this,UI_ID,id,{p.x,p.y});float scale=1+(10-p.life)*.16f;UI::SetScale(this,UI_ID,id,{scale,scale});UI::SetOpacity(this,UI_ID,id,p.life/10.f);}}
 if(noiseGainTimeV4>0&&(noiseGainTimeV4-=delta)<=0)UI::SetVisible(this,UI_ID,"NoiseGain",false);
 if(held&&silencerV4.charge>0){float p=silencerV4.charge/60.f;UI::SetVisible(this,"debatefx","ChargeRing",true);UI::SetVisible(this,"debatefx","ChargeState",true);UI::SetPosition(this,"debatefx","ChargeRing",{aimX,aimY});UI::SetScale(this,"debatefx","ChargeRing",{1.25f-.4f*p,1.25f-.4f*p});UI::SetText(this,"debatefx","ChargeState",p>=1?"소음 탄환 충전 · 놓으면 발사":"소음 탄환 충전 "+std::to_string(int(p*100))+"%");}
 return (held&&holdTime<0)||silencerV4.charge>0||fired||remote;
}
void Yumeno::v4AimAssist(bool focused){
 aimAssistV4.active=false;bool paranormal=skillOn("paranormal"),robot=skillOn("robot_eye");
 if(!focused||aimPointerV4.moved||cameraTime<1||!shotRecoveryV4.ready()||holdTime>=0||lieV4.phase!=liev4::Phase::Idle||(!paranormal&&!robot))return;
 std::vector<aimskillsv4::Point> weak,points;
 auto collect=[&](int at,const std::vector<debate::Glyph>& glyphs){if(at<0||at>=int(debate.lines.size())||debate.broken[at])return;const auto& line=debate.lines[at];if(line.kind!="weak"&&line.kind!="agree")return;if(auto p=aimskillsv4::paranormalTarget(glyphs))weak.push_back(*p);if(auto p=aimskillsv4::robotTarget(line,glyphs))points.push_back(*p);};
 if(debate.panic())for(int lane=0;lane<3;lane++)collect(debate.laneLine(lane),debate.panicGlyphs(lane));else collect(debate.index,debate.current());
 aimAssistV4=aimskillsv4::step({aimX,aimY},focused,aimPointerV4.moved,debate.panic(),paranormal,robot,weak,points);
}
void Yumeno::v4TaskRoot(bool visible){
 bool standard=visible&&stageKind!="nonstop"&&stageKind!="panic"&&stageKind!="anagram"&&stageKind!="armament"&&stageKind!="climax"&&stageKind!="mindmine"&&stageKind!="vote";
 UI::SetVisible(this,"trialvitalsv4","root",standard);
 if(stageKind=="nonstop"||stageKind=="panic")drawNonstopSourceHud(0);
 const bool selector=trialinputmotion::usesSourceStatus(stageKind);
 for(auto id:{"StatusPanel","StatusLabel"})UI::SetVisible(this,UI_ID,id,standard&&!selector);for(int i=0;i<10;i++)UI::SetVisible(this,UI_ID,"Star"+std::to_string(i),standard&&!selector);
 if(visible)for(int k=0;k<20;k++)UI::SetVisible(this,"trialvitalsv4","Heart"+std::to_string(k),!selector&&k<maxHearts*2);
 for(auto id:{"stage","minev4","minehudv4","vote","debatefx","panicv4","comicv4","scrumv4","anagramv4"}){
  const std::string widget=id;
  bool active=!v4TaskActive||widget=="stage"||widget=="debatefx"||((widget=="minev4"||widget=="minehudv4")&&stageKind=="mindmine")||(widget=="vote"&&stageKind=="vote"&&voteGridVisible)||(widget=="panicv4"&&(stageKind=="panic"||stageKind=="showdown"))||(widget=="comicv4"&&stageKind=="climax")||(widget=="scrumv4"&&stageKind=="scrum")||(widget=="anagramv4"&&stageKind=="anagram");
  UI::SetVisible(this,id,"root",visible&&active);
 }
 UI::SetVisible(this,"trialpickerv4","root",visible&&trialPickerOn);
 trialinputmotion::visibility(this,visible);
 if(trialResultOn)UI::SetVisible(this,"trialresultv4","root",visible);
 if(!visible){debateHud(false);UI::SetVisible(this,UI_ID,"TrialMsg",false);}
 if(!visible&&mode==Mode::Trial&&v4TaskActive&&stageKind=="climax"&&v4QueueActive&&v4QueueAfter=="comic"&&v4ComicReplay)v4ComicReplayDrawV3(true);
}
int Yumeno::v4TaskHp()const{
 if(!v4TaskActive)return v4TrialHp;if(v4QueueActive&&v4QueueAfter=="start")return v4TaskEntryHp;if(v4QueueActive&&v4QueueAfter=="success")return v4TrialHp;
 if(stageKind=="mindmine")return mineV4.hp;if(stageKind=="anagram")return anagramV4.hp;if(stageKind=="scrum")return scrumHpV4;if(stageKind=="armament")return int(std::lround(double(armingV4.hp)*maxHearts*2000/std::max(1,armingV4.maxHp)));
 if(stageKind=="showdown"&&stage.contains("showdownV4"))return showdownV4.hp;
 return std::clamp(v4TaskEntryHp+(debate.hearts-v4TaskEntryHearts)*2000,0,maxHearts*2000);
}
void Yumeno::v4ResetHearts(int hearts){
 debate.hearts=std::clamp(hearts,1,maxHearts);if(v4TaskActive){v4TaskEntryHp=v4TrialHp=debate.hearts*2000;v4TaskEntryHearts=debate.hearts;}shownHearts=-1;
}
void Yumeno::mountTrialUi(const std::string& kind){
 const std::vector<std::pair<std::string,std::string>> assets{{"stage","Stage"},{"trialvitalsv4","TrialVitalsV4"},{"minev4","MineV4"},{"minehudv4","MineHUDV4"},{"vote","Vote"},{"intro","Intro"},{"debatefx","DebateFX"},{"panes","PanicPanes"},{"panicv4","PanicV4"},{"comicv4","ComicV4"},{"scrumv4","ScrumV4"},{"anagramv4","AnagramV4"}};
 std::set<std::string> needed{"trialvitalsv4"};
 if(kind!="nonstop")needed.insert("stage");
 if(kind=="nonstop"||kind=="panic"||kind=="showdown"||kind=="lie")needed.insert("debatefx");
 if(kind=="panic"){needed.insert("panicv4");needed.insert("panes");}if(kind=="showdown")needed.insert("panicv4");
 if(kind=="mindmine"){needed.insert("minev4");needed.insert("minehudv4");}if(kind=="vote")needed.insert("vote");if(kind=="climax")needed.insert("comicv4");if(kind=="scrum")needed.insert("scrumv4");if(kind=="anagram")needed.insert("anagramv4");
 bool mounted=false;
 for(const auto& [id,asset]:assets){if(!needed.count(id)){UI::Remove(this,id);continue;}if(!UI::Mounted(id)){UI::Show(this,"Assets/UI/"+asset+".hbwidget.json",id);mounted=true;if(id=="panicv4"){panicGlyphDisplay={};for(auto it=glyphCache.begin();it!=glyphCache.end();)if(it->first[0]=='P')it=glyphCache.erase(it);else ++it;for(auto it=glyphStyle.begin();it!=glyphStyle.end();)if(it->first[0]=='P')it=glyphStyle.erase(it);else ++it;}}}
 if(mounted){stexts.clear();svisible.clear();pv4::Rehost(presentationV4);}stageShown=true;comicShown=UI::Mounted("comicv4");
}
void Yumeno::releaseTrialUi(){
 trialinputmotion::clear(this);
 modeEndTimeV4=-1;endingSourceClear();
 for(auto id:{"stage","trialvitalsv4","minev4","minehudv4","vote","intro","debatefx","panes","panicv4","comicv4","scrumv4","anagramv4","trialpickerv4"})UI::Remove(this,id);
 stageShown=comicShown=trialPickerShown=trialPickerOn=false;stexts.clear();svisible.clear();
}
void Yumeno::v4TaskStart(){
 const auto& node=v4.current();auto id=node.value("taskId",std::string());
 const auto& page=storyv4::bucketData(v4.graph.value("taskBucketPrefix",std::string("Assets/Data/v4_story/native_tasks/")),storyv4::bucket(id,64));
 if(!page["tasks"].contains(id))throw std::runtime_error("Missing native task bundle: "+id);
 auto bundle=page["tasks"][id];auto native=taskv4::prepare(bundle,v4.evidence);auto kind=native.value("kind",std::string());
 if(kind=="nonstop"){
  const auto* ammo=native.contains("authoredAmmo")?&native.at("authoredAmmo"):trialdirection::find("nonstopAmmo",id);
  if(!ammo)throw std::runtime_error("Missing authored Nonstop ammunition: "+id);
  Json selected=Json::array();
  const auto& owned=native.at("options");
  for(const auto& evidence:*ammo){
   auto option=std::find_if(owned.begin(),owned.end(),[&](const Json& card){return card.at("id")==evidence;});
   if(option!=owned.end())selected.push_back(*option);
   else{
    const auto id=evidence.get<std::string>();
    if(v4.evidence.contains(id))selected.push_back({{"id",id},{"name",kotodamaName(id)},{"text",kotodamaText(id)}});
   }
  }
  if(selected.empty())throw std::runtime_error("No acquired Nonstop ammunition: "+id);
  native["options"]=std::move(selected);
 }
 static const std::set<std::string> supported{"nonstop","panic","choice","bullet","person","vote","showdown","scrum","anagram","reasoning","spot","mindmine","climax","armament","lie"};
 if(!supported.count(kind))throw std::runtime_error("Native task schema requires implementation: "+kind);
 if(kind=="spot"&&(!native.contains("image")||!native.contains("regions")))throw std::runtime_error("Point selection needs its actual image and regions");
 if(kind=="reasoning"&&native.value("questions",Json::array()).empty())throw std::runtime_error("Reasoning chain has no authored links");
 scenesv4::courtMode=scenesv4::trialMode(kind);if(!scenesv4::courtReady())return;
 if(kind=="anagram"&&!gputrialhudv4::warmAnagram())return;
 if(kind=="showdown"&&!gputrialhudv4::warmShowdown())return;
 v4Task=std::move(bundle);v4Task["stage"]=std::move(native);v4TaskActive=true;v4Judgment="refute";v4TaskLinks=0;v4LieHeld=0;v4ComicReview=false;v4ComicPage.clear();
 trialKey="1"+v4.graph.value("chapter",std::string("1"))+"c";
 auto dead=node.value("trialDead",Json::array()).get<std::vector<std::string>>();
 bool initial=!v4Court||trialDead!=dead;trialDead=std::move(dead);
 if(!v4Court)v4BeginCourt();
 v4TaskEntryHp=v4TrialHp;v4TaskEntryHearts=(v4TrialHp+1999)/2000;debate.hearts=v4TaskEntryHearts;
 v4Court=true;world.active=false;exworld::visible(world,false);hideExplore();hideMenu();mode=Mode::Trial;dialogVisible(false);fvis("FHud",false);
 for(auto name:{"Title","Backdrop","Portrait","Background"})UI::SetVisible(this,UI_ID,name,false);
 mountTrialUi(kind);trialPickerClear();
 v4ComicClear();v4TaskRoot(true);if(initial)setupCourt();UI::SetVisible(this,UI_ID,"Trial",true);UI::SetVisible(this,UI_ID,"CourtDim",true);
 stages=Json::array({v4Task["stage"]});trials={{"stages",stages},{"debates",Json::array()}};
 if(v4Task.contains("debate")){auto d=v4Task["debate"];d["bullets"]=v4Task["stage"].value("options",Json::array());trials["debates"].push_back(std::move(d));}
 if(!v4PendingTaskResume.empty()){
  stage=v4Task["stage"];stageKind=stage.value("kind",std::string());stageAt=0;if(stageKind=="climax"&&stage.contains("comicPresentation"))v4ComicPage=stage["comicPresentation"]["board"].value("image",std::string());
  v4Judgment=v4PendingTaskResume.at("judgment").get<std::string>();v4PendingTaskResume=Json::object();
  {auto rows=v4Task.value("queues",Json::object()).value("success",Json::array());if(!sdDeferred.empty()){Json all=sdDeferred;for(auto& r:rows)all.push_back(r);rows=all;sdDeferred=Json::array();}v4TaskQueue(rows,"success");} /* 쇼다운 중 미룬 다른 사람 대사 먼저 */
 }else{
  auto intro=v4Task.value("queues",Json::object()).value("intro",Json::array());
  if(kind=="panic"){
   panicStorySpeakers.clear();panicLeadTask.clear();panicLeadCount=0;panicLeadSplit=0;
   const bool authored=std::any_of(intro.begin(),intro.end(),[](const Json& row){return row.value("panicInterruption",false);});
   const auto& d=v4Task.at("debate");
   const auto& lines=d.at("lines");
   if(!authored)for(const auto& lane:d.at("lanes")){
    const Json* claim=nullptr;
    for(const auto& id:lane.at("lines")){
     const auto row=std::find_if(lines.begin(),lines.end(),[&](const Json& line){return line.at("id")==id;});
     if(row==lines.end()||row->value("kind",std::string())=="noise")continue;
     if(!claim)claim=&*row;
     if(row->value("kind",std::string())=="plain"){claim=&*row;break;}
    }
    if(!claim)continue;
    const auto actor=claim->value("actor",std::string());
    intro.push_back({{"type","say"},{"id",claim->at("id").get<std::string>()+":panic-lead"},
     {"actor",actor},{"speaker",claim->value("speaker",nameOf(actor))},{"text",claim->at("text")},
     {"panicInterruption",true}});
   }
  }
  v4TaskQueue(intro,"start");
 }
}
void Yumeno::v4TaskPlay(){enterStage(0);trialScoreBegin();}
void Yumeno::v4DebateMode(bool transformed){
 if(!v4Task.contains("debate")||v4AppliedDebateMode==int(transformed))return;v4AppliedDebateMode=int(transformed);
 auto transformation=v4Task.value("transformation",Json::object());
 const auto& lines=v4Task["debate"]["lines"];
 for(int i=0;i<int(debate.lines.size());i++){ // 늘린 발언·잡음이 끼어 있어 번호가 아니라 id 로 원래 줄을 찾는다(사양서 25)
  const Json* found=nullptr;for(const auto& L:lines)if(L.value("id",std::string())==debate.lines[i].id){found=&L;break;}if(!found)continue;
  const auto& source=*found;auto weak=source.value("weak",Json::object());
  if(transformed&&source.contains("lieWeak"))weak=source["lieWeak"];
  else if(transformed&&!transformation.empty()&&transformation.value("intentionalHold",false)&&weak.value("answer",std::string())==transformation.value("sourceEvidenceId",std::string()))weak["lie"]=true;
  if(weak.empty())continue;auto& line=debate.lines[i];auto word=weak.value("word",std::string());
  auto kind=transformed&&weak.value("requireAgreement",false)?std::string("agree"):source.value("kind",std::string("plain"));bool changed=line.word!=word||line.kind!=kind;line.kind=kind;
  line.word=word;line.start=weak.value("start",0);line.answer=weak.value("answer",std::string());line.lie=weak.value("lie",false);
  if(changed)shownLine=-1;
 }
}
void Yumeno::v4TaskQueue(const hb::Json& rows,const std::string& after){
 if(stageKind=="nonstop"&&(after=="nonstop-loop"||after=="nonstop-wrong")){
  // Also clear GPU leaf visibility: retained shadow/solid faces can outlive a
  // widget/cache visibility change when the debate freezes into a dialogue.
  for(int i=0;i<48;++i)for(auto face:{"MF","MB","MS"}){auto id=std::string(face)+std::to_string(i);glyphDisplay.visible(id,false);gputrialhudv4::setVisible(id,false);}
  drawGlyphs("M",48,{});drawGlyphs("N",26,{});
 }
 v4NoiseReset(); if(after=="start"||after=="success"){shotRecoveryV4.reset();UI::SetOpacity(this,UI_ID,"Aim",1);}aimAssistV4.active=false;aimPointerV4={};
 if(stageKind=="showdown"&&after.rfind("showdown",0)==0)for(auto id:{"SdV3Arc","SdV3Pointer","SdV3Flower","SdV3Band","SdV3SlashN","SdV3SlashT","SdV3Bonus0","SdV3Bonus1","SdV3Bonus2","SdV3Bonus3","SdV3TimeBase","SdV3X0","SdV3X1","SdV3Streak"})UI::SetVisible(this,"sdv3",id,false);sdCutFx=0;for(int i=0;i<9;i++)UI::SetVisible(this,"sdv3","SdV3TimeD"+std::to_string(i),false); /* V3 : 대사 중엔 HUD 없음 */if(after!="showdown-advance"){for(auto id:{"SdV3HitRing","SdV3BrkHit"})UI::SetVisible(this,"sdv3",id,false);sdHit[2]=-1;sdShards.clear();sdShardCh.clear();for(int i=0;i<48;i++)UI::SetVisible(this,"panicv4","P0G"+std::to_string(i),false);glyphCache.clear();}for(auto& b:sdBonus)b[2]=0;sdSlashT=0; /* V3 : 대사 중에는 칼 커서·형세 띠·SLASH 가 없다(그리기에서 다시 켠다) */
 v4Queue=rows;v4QueueAt=-1;v4QueueAfter=after;v4QueueActive=true;++v4QueueGeneration;v4TaskRoot(false);v4TaskQueueNext();
 if(v4TaskActive&&after=="success"&&stageKind=="climax"&&!v4ComicPage.empty())v4ComicComplete(true);
 if(v4TaskActive&&v4QueueActive&&after=="comic"&&stageKind=="climax"&&v4ComicReplay)v4ComicReplayDrawV3(true);
}
void Yumeno::v4TaskQueueNext(){
 if(stageKind=="showdown")for(int i=0;i<16;i++){UI::SetVisible(this,"sdv3","SdV3TW"+std::to_string(i),false);UI::SetVisible(this,"sdv3","SdV3TP"+std::to_string(i),false);} /* 앞 줄 주인공 글자 지우기 */
 while(++v4QueueAt<int(v4Queue.size())){
  const auto& row=v4Queue[v4QueueAt];auto cue=row;if(!cue.contains("id")&&cue.contains("eventId"))cue["id"]=cue["eventId"];pv4::Apply(presentationV4,cue,(std::uint64_t(1)<<63)+(v4QueueGeneration<<16)+v4QueueAt);
  if(!row.contains("text")||row.value("type",std::string("say"))=="stage")continue;
  line=row.value("text",std::string());speaker=row.value("mono",false)?"":row.value("speaker",std::string());portrait.clear();
  auto who=row.value("actor",std::string());const auto* dir=trialdirection::find("queue",row.value("eventId",stageKind=="nonstop"?row.value("id",std::string()):std::string())); /* 대화 줄마다 표정·흔들림·소리(사양서 25) */
  bool sdLine=stageKind=="showdown"&&v4QueueAfter.rfind("showdown",0)==0; /* 쇼다운 대사 중엔 2분할 카메라 그대로(화자 따라 카메라가 넘어가지 않는다) */
  if(!who.empty()&&!row.value("mono",false)&&!sdLine){auto pose=dir?trialdirection::pose(who,dir->value("pose",std::string())):std::string();focusSpeaker(who,!pose.empty()?pose:row.value("pose",row.value("appearanceActor",who)));}
  if(dir){auto fx=dir->value("fx",std::string());if(trialdirection::has(fx,"shake"))if(auto* cam=actor("Camera"))Camera::Shake(cam,.02f,.25f);if(dir->contains("se"))sfx((*dir)["se"].get<std::string>());}
  UI::SetColor(this,UI_ID,"Body",row.value("mono",false)?Color{.62f,.84f,1,1}:Color{.96f,.94f,.97f,1});sdTalkOn=stageKind=="showdown"&&v4QueueAfter.rfind("showdown",0)==0&&v4QueueAfter!="showdown-pre"&&who=="mio"&&!row.value("mono",false); /* V3 영상 Hs3Y7uyOAQk 174~178초 : 쇼다운 중 주인공 발언 = 주인공 화면 가득 + 하늘색 큰 글, 대화창 없음 */dialogVisible(!sdTalkOn);if(stageKind=="showdown")for(auto id:{"SdLeft","SdDivider"})svis(id,!sdTalkOn);showLine();if(sdTalkOn){dialogVisible(false);UI::SetVisible(this,UI_ID,"Next",false);sdTalkT=0;sdTalkWords.clear();for(int k=0;k<16;k++)for(auto pre:{"SdV3TW","SdV3TP"})UI::SetFont(this,"sdv3",pre+std::to_string(k),"Assets/Fonts/gothica1/GothicA1-Bold.ttf"); /* 한국어판 3114~3118초 : 대화창·NEXT 없이 낱말이 흐르고 저절로 넘어간다 */
   std::vector<std::string> w;auto flush=[&]{if(w.empty())return;int t=sdTail(w);std::string a,b;for(size_t k=0;k<w.size();k++)(int(k)>=int(w.size())-t?b:a)+=w[k];if(a.empty()){a=b;b.clear();}sdTalkWords.push_back({a,b});w.clear();};
   for(auto& g:debate::glyphs(line)){if(g==" "){flush();continue;}w.push_back(g);if(g=="."||g==","||g=="?"||g=="!")flush();}flush();}
  if(!sdTalkOn)dialogueCue(row.value("delivery",std::string()),false);
  if(speakerSeat>=0&&row.contains("dialogueShot")){shotKind=row.at("dialogueShot").get<int>();shotTime=0;}
  if(stageKind=="climax"&&v4QueueAfter=="comic"&&v4ComicReplay)v4ComicReplayDrawV3(true);
  if(stageKind=="climax"&&v4QueueAfter=="success"&&!v4ComicPage.empty())v4ComicComplete(true);
  auto readId="task:"+v4Task.value("taskId",std::string())+":"+v4QueueAfter+":"+row.value("id",readSignature(line));
  optv4::BeginLine(optionsV4,readId,v4.read.count(readId)>0);
  v4.log.push_back({{"id",readId},{"speaker",speaker},{"actor",who},{"text",line},{"mono",row.value("mono",false)}});if(v4.log.size()>2000)v4.log.erase(v4.log.begin());return;
 }
 v4QueueActive=false;dialogVisible(false);if(sdTalkOn){sdTalkOn=false;for(int i=0;i<16;i++){UI::SetVisible(this,"sdv3","SdV3TW"+std::to_string(i),false);UI::SetVisible(this,"sdv3","SdV3TP"+std::to_string(i),false);}for(auto id:{"SdLeft","SdDivider"})svis(id,true);}auto after=v4QueueAfter;v4QueueAfter.clear();v4TaskRoot(true);
 if(after=="start")v4TaskPlay();else if(after=="success")v4TaskRoute();else if(after=="nonstop-wrong"||after=="nonstop-loop"||after=="panic-restart")v4NonstopRestart();else if(after=="reasoning")v4Reasoning();else if(after=="comic")v4ComicShow();else if(after=="showdown-dialogue"){showdownV4.resumeDialogue();showdownShown=-1;}else if(after=="showdown-advance"){showdownV4.acknowledge();showdownShown=-1;}else if(after=="showdown-pre"){for(auto k:{"SdLeft","SdRight","SdDivider"})svis(k,true);} /* 2분할 대사가 끝나면 칸막이가 서며 제목 */else if(playingDebate){if(stageKind=="nonstop")shownLine=-1;debateHud(true);}
}
bool Yumeno::v4TaskQueueUpdate(float delta){
 if(!v4QueueActive)return false;
 if(stageKind=="showdown"&&sdAdvT>0){updateCamera(delta);const float previousAdvance=sdAdvT;sdAdvT-=delta;
  if(sdAdvT>1.4f){v4ShowdownDraw();for(auto id:{"SdV3Arc","SdV3Pointer","SdV3Flower","SdV3Band","SdV3SlashN","SdV3SlashT","SdV3TimeBase"})UI::SetVisible(this,"sdv3",id,false);for(int i=0;i<9;i++)UI::SetVisible(this,"sdv3","SdV3TimeD"+std::to_string(i),false);} /* 마지막 충격파·파편이 끝까지 */
  {float r=std::clamp((2.f-sdAdvT)/.2f,0.f,1.f)*std::clamp((sdAdvT-1.4f)/.2f,0.f,1.f);UI::SetColor(this,"stage","SdLeft",Color{1,.25f+.75f*(1-r),.2f+.8f*(1-r),1});UI::SetOpacity(this,"stage","SdLeft",.2f+.6f*r);} /* 3112.0 왼쪽 붉은 번쩍 */
  if(sdAdvT<=1.4f){UI::SetVisible(this,"sdv3","SdV3HitRing",false);UI::SetVisible(this,"sdv3","SdV3BrkHit",false);sdHit[2]=-1;if(!sdShards.empty()){for(int i=0;i<48;i++)UI::SetVisible(this,"panicv4","P0G"+std::to_string(i),false);glyphCache.clear();}sdShards.clear();sdShardCh.clear();} /* 충격파는 발전 전에 끝 */
  bool adv=sdAdvT<1.4f&&sdAdvT>0;UI::SetVisible(this,"sdv3","SdV3Adv",adv);UI::SetVisible(this,"sdv3","SdV3AdvLine",adv);if(adv&&previousAdvance>=1.4f)sfx("v3se_374");dialogVisible(sdAdvT<=0&&!sdTalkOn); /* 발전 동안 대화창 없음 */return true;} /* V3 172.5초 : 「Advance!」가 걷힌 뒤 발언 */
 updateCamera(delta);shown=std::min(float(lineLength),shown+delta*optv4::CharactersPerSecond(optionsV4));text("Body",u8prefix(dialogueText(),int(shown)));if(sdTalkOn){sdTalkT+=delta;float x=130,y=300;int n=int(sdTalkWords.size()); /* 3115~3118초 : 가운데 왼쪽, 보통 크기 */ /* 낱말마다 0.22초 간격으로 왼쪽에서 밀려 들어온다 */
  // 3114.2~3119.1초 : 문장 하나씩(앞 문장은 지우고), 낱말이 0.3초마다 왼쪽에서 붙는다. 화면 가운데 높이
  std::vector<int> sent(n,0);{int s=0,count=0;for(int k=0;k<n;k++){sent[k]=s;auto& wd=sdTalkWords[k][1].empty()?sdTalkWords[k][0]:sdTalkWords[k][1];if(++count==16||(!wd.empty()&&std::string(".?!").find(wd.back())!=std::string::npos)){++s;count=0;}}}
  std::vector<float> start(n,0);{float t0=0;int prev=-1,idx=0;for(int k=0;k<n;k++){if(sent[k]!=prev){if(prev>=0)t0+=idx*.3f+1.2f;prev=sent[k];idx=0;}start[k]=t0+idx*.3f;++idx;}}
  float total=n?start[n-1]+1.5f:0;int cur=-1;for(int k=0;k<n;k++)if(sdTalkT>=start[k])cur=sent[k];
  int first=cur<0?n:int(std::find(sent.begin(),sent.end(),cur)-sent.begin());
  x=320;y=330;for(int slot=0;slot<16;slot++){int k=first+slot;auto a="SdV3TW"+std::to_string(slot),b="SdV3TP"+std::to_string(slot);bool on=k<n&&sent[k]==cur&&sdTalkT>=start[k];UI::SetVisible(this,"sdv3",a,on);UI::SetVisible(this,"sdv3",b,on&&!sdTalkWords[k][1].empty());if(k>=n||sent[k]!=cur)continue;
   float wa=52.f*u8len(sdTalkWords[k][0]),wb=26.f*u8len(sdTalkWords[k][1]);if(x+wa+wb>1150){x=360;y+=78;}float u=std::clamp((sdTalkT-start[k])/.15f,0.f,1.f),dx=-40*(1-u);
   if(on){UI::SetText(this,"sdv3",a,sdTalkWords[k][0]);UI::SetPosition(this,"sdv3",a,{x+dx,y});UI::SetOpacity(this,"sdv3",a,u);UI::SetText(this,"sdv3",b,sdTalkWords[k][1]);UI::SetPosition(this,"sdv3",b,{x+wa+dx,y+24});UI::SetOpacity(this,"sdv3",b,u);}x+=wa+wb+18;}
  UI::SetVisible(this,UI_ID,"Next",false);if(sdTalkT>total)v4TaskQueueNext();return true;}
 dialogueCueTick(delta);
 bool done=int(shown)>=lineLength;if(optv4::ReportRead(optionsV4,done&&dialogueFinal()))v4.read.insert(optionsV4.line.id);UI::SetVisible(this,UI_ID,"Next",done);
 bool next=pressed("Enter")||pressed("Space")||pressed("mouse0");
 if(optv4::CanSkip(optionsV4,Input::IsKeyDown("Control"))){skipTimer+=delta;if(skipTimer>.05f){skipTimer=0;next=true;}}
 if(optv4::AutoAdvance(optionsV4,delta,done))next=true;
 if(next&&dialogueAdvance())v4TaskQueueNext();return true;
}
void Yumeno::v4TaskWrong(int variant){
 if(!v4TaskActive||v4QueueActive)return;
 auto queues=v4Task.value("queues",Json::object());auto rows=queues.value("wrong",Json::array());
 auto variants=queues.value("wrongVariants",Json::array());if(variant>=0&&variants.is_array()&&variant<int(variants.size()))rows=variants[variant].value("script",variants[variant].value("events",Json::array()));
 if(rows.empty()&&stageKind=="nonstop")if(const auto* fallback=trialdirection::find("nonstopFeedback","unmatched"))rows=*fallback;
 ++trialResults.current.gaffe; // Own authored wrong-queue event; HP damage alone is not a gaffe.
 sfx("v3se_316");
 if(stageKind=="panic"){
  if(rows.empty()&&!variants.empty())rows=variants.front().value("script",variants.front().value("events",Json::array()));
  if(rows.empty())v4NonstopRestart();else v4TaskQueue(rows,"panic-restart");
 }else if(!rows.empty())v4TaskQueue(rows,stageKind=="nonstop"?"nonstop-wrong":"resume");
}
void Yumeno::v4NonstopRestart(){
 // Internal retry preserves remaining time, HP, focus and selected evidence.
 debate.restartRows();v4NoiseReset();shotRecoveryV4.reset();lieV4.cancel();lieV4Ticks=0;holdTime=-1;lie=false;lieView(false);
 flyingEvidence.clear();flyingImpact=false;shotTimeLeft=0;aimSwayV4.reset();aimPointerV4={};aimAssistV4.active=false;
 shownLine=-1;debateInputArmed=false;playingDebate=true;showBullet();debateHud(true);
}
void Yumeno::v4TaskEnd(){
 trialScoreCapture();trialResults.current.retry=std::max(trialResults.current.retry,retries);
 v4TrialHp=std::clamp(v4TaskHp(),1,maxHearts*2000);
 onCorrect();
 sclear();cancelDebateIntro();playingDebate=false;inScript=false;debateHud(false);dialogVisible(false);
 // Own response lines belong after the completed rhythm round, never in its input clock.
 auto successRows=v4Task.value("queues",Json::object()).value("success",Json::array());
 if(stageKind=="armament"){Json all=Json::array();for(const auto& wave:stage.value("waves",Json::array()))for(const auto& pair:wave.value("pairs",Json::array())){auto response=pair.value("response",Json());if(response.is_object()&&response.contains("text"))all.push_back(response);else if(response.is_array())for(const auto& line:response)all.push_back(line);}for(const auto& line:successRows)all.push_back(line);successRows=all;}
 v4TaskQueue(successRows,"success");
}
void Yumeno::v4TaskRoute(){
 if(stageKind=="climax"&&!climaxEndDoneV4&&stage.at("comicPresentation").at("completion").value("owner",std::string())=="task-success-queue"){climaxEndDoneV4=true;beginModeEnding("climax","task-route");return;}
 auto route=taskv4::success(v4.current(),v4Task,v4Judgment);if(route.target.empty())throw std::runtime_error("Native task has no authored success route");

 const auto completedId=v4Task.value("taskId",std::string());bool showResult=completedId==v4.graph.value("resultTaskId",std::string());resultv4::commit(trialResults,completedId,v4Judgment=="lie");
 v4LastOutcome={{"taskId",v4Task.value("taskId",std::string())},{"judgment",v4Judgment},{"target",route.target},{"sets",route.sets}};storyv4::setFlags(v4,route.sets);v4TaskActive=false;v4QueueActive=false;v4Task=Json::object();mode=Mode::Story;scenesv4::courtMode="Court";
 for(auto id:{"Trial","CourtDim","TrialBack"})UI::SetVisible(this,UI_ID,id,false);
 if(!storyv4::jump(v4,route.target))throw std::runtime_error(v4.blocked);
 if(showResult)trialResultStart();else{
  if(v4.current().value("type",std::string())=="say"&&stageKind!="vote"&&!musicCue.empty())
   music("bgm_trial_main_"+v4.graph.value("chapter",std::string("1")));
  v4Enter();
 }
}
void Yumeno::v4Reasoning(){
 const auto& questions=stage["questions"];if(v4TaskLinks>=int(questions.size())){beginScript();return;}
 const auto& q=questions[v4TaskLinks];std::vector<std::string> options=q["options"].get<std::vector<std::string>>();optAnswer=-1;
 for(int i=0;i<int(options.size());i++)if(options[i]==q.value("answer",std::string()))optAnswer=i;
 if(optAnswer<0)throw std::runtime_error("Reasoning answer is absent from actual candidates");showOptions(q.value("q",std::string()),options);
 stext("Hint",std::to_string(v4TaskLinks+1)+" / "+std::to_string(questions.size())+"   W/S · Enter");UI::SetPosition(this,trialui::ID,"Hint",{930,660});UI::SetSize(this,trialui::ID,"Hint",{300,30});svis("Hint",true);
}
void Yumeno::v4MineHints(){
 for(int i=0;i<10;i++){bool on=skillOn("mieru_goggles")&&i<int(stage["regions"].size())&&stage["regions"][i].contains("hintOutline")&&mineV4.partialImage(i);svis("MineHint"+std::to_string(i),on);}
}
void Yumeno::v4MineStart(){
 mineSuccessTimeV4=-1;mineSuccessPhaseV4=-1;mineQuestionVisibleV4=false;mineFocusActiveV4=false;mineIntroV4=2.8f;mineBurstTimeV4=0;mineBurstCellsV4.clear();mineClockV4.clear();minePenaltyV4=mineTimeoutV4=0;mineCursorStateV4=-1;svis("MinePenalty",false);svis("MineTimeout",false);
 if(!stage.contains("image")||!stage.contains("regions"))throw std::runtime_error("Mine needs an authored image and exact regions");
 stageLimit=999;minigameTicksV4=0;int colors=difficultyv4::mineColors(chapterAt,difficultyV4.logic),width=difficultyv4::mineWidth(difficultyV4.action);
 cells=trialv4::mineBoard(width,11,colors,int(storyv4::bucket(stage.value("id",std::string()),97)));mineV4.reset(width,11,colors,cells,int(18000*trialTimeFactor()));mineV4.hp=v4TaskEntryHp;mineV4.wrongDamage=growthv4::Damage(growthV4,difficultyv4::anagramDamage(difficultyV4.logic));mineV4.undoEnabled=skillOn("undo_enable");mineV4.safetyFirst=skillOn("safety_first");
 const minelayoutv4::Board layout(width);
 if(stage.contains("mineObjects"))taskv4::minePlaceObjects(stage,width,std::uint32_t(std::chrono::steady_clock::now().time_since_epoch().count()));
 UI::Remove(this,"minehudv4");UI::Remove(this,"minev4");UI::Show(this,"Assets/UI/MineV4.hbwidget.json","minev4");UI::Show(this,"Assets/UI/MineHUDV4.hbwidget.json","minehudv4");for(auto id:{"MineQuestionPlate","MineQuestionText","MineToggle","MineCursor","MineEntryDim","MineEntryBlur","MineEntryTitle","MineEntryEcho","MineEntryRays","MineEntrySubtitle","MineEntrySpark"})svisible.erase(id);for(int i=0;i<10;i++)svisible.erase("MineBurst"+std::to_string(i));for(int i=0;i<9;i++)svisible.erase("MineClock"+std::to_string(i));minePaintAt=0;mineTileAlphaV4.assign(cells.size(),1.f);mineTileStyleV4.assign(cells.size(),-1);mineTileMotionV4.assign(cells.size(),{});mineFocusPulseV4=0;for(int i=0;i<242;i++)svisible.erase("Cell"+std::to_string(i));
 for(int i=0;i<10;i++){auto id="MineHint"+std::to_string(i);svisible.erase(id);UI::SetRotation(this,"minev4",id,0);if(i<int(stage["regions"].size())&&stage["regions"][i].contains("hintOutline")){UI::SetTexture(this,"minev4",id,stage["regions"][i]["hintOutline"].get<std::string>());UI::SetPosition(this,"minev4",id,{layout.left,layout.top});UI::SetSize(this,"minev4",id,{layout.width,layout.height});}}
 UI::SetTexture(this,trialui::ID,"MineBg",stage["image"].get<std::string>());UI::SetPosition(this,trialui::ID,"MineBg",{layout.left,layout.top});UI::SetSize(this,trialui::ID,"MineBg",{layout.width,layout.height});svis("MineBg",false);

 for(int i=0;i<10;i++){auto id="MineObject"+std::to_string(i);svis(id,false);if(stage.contains("mineObjects")&&i<int(stage["mineObjects"].size())){auto& object=stage["mineObjects"][i];auto& r=object["rect"];UI::SetTexture(this,"stage",id,object["texture"].get<std::string>());UI::SetPosition(this,"stage",id,{layout.left+layout.width*r[0].get<float>(),layout.top+layout.height*r[1].get<float>()});UI::SetSize(this,"stage",id,{layout.width*r[2].get<float>(),layout.height*r[3].get<float>()});UI::SetRotation(this,"stage",id,object.value("rotation",0.f));for(int region=0;region<int(stage["regions"].size());region++)if(stage["regions"][region]["id"]==object["regionId"]){auto hint="MineHint"+std::to_string(region);UI::SetTexture(this,"minev4",hint,object.at("hintLocal").get<std::string>());UI::SetPosition(this,"minev4",hint,{layout.left+layout.width*r[0].get<float>(),layout.top+layout.height*r[1].get<float>()});UI::SetSize(this,"minev4",hint,{layout.width*r[2].get<float>(),layout.height*r[3].get<float>()});UI::SetRotation(this,"minev4",hint,object.value("rotation",0.f));}}}
 std::vector<trialv4::MineImage> images;mineAnswer=-1;
 for(int i=0;i<int(stage["regions"].size());i++){
  auto& region=stage["regions"][i];trialv4::MineImage image;image.id=i;image.correct=region.value("correct",false)||region.value("id",std::string())==stage.value("answerRegionId",std::string());if(image.correct)mineAnswer=i;
  if(stage.contains("mineObjects")){for(const auto& object:stage["mineObjects"])if(object["regionId"]==region["id"])image.cells=object.at("placedCells").get<std::vector<int>>();}
  else image.cells=taskv4::mineFootprint(region["polygon"],mineV4.width,mineV4.height);
  if(image.cells.empty())throw std::runtime_error("Mine region has no native footprint");images.push_back(std::move(image));
 }
 if(mineAnswer<0)throw std::runtime_error("Mine answer region absent");mineV4.setImages(images,!stage.contains("mineObjects"));
 mineOpeningV4.reset();if(skillOn("roller_strategy"))mineOpeningV4.start(width,11,10,storyv4::bucket(stage.value("id",std::string()),65521));

 svis("MineBackdrop",false);svis("MineTimer",false);svis("StageTimer",false);svis("MineHealth",false);svis("MineFocus",false);for(auto id:{"MineBoardFrame","MineBottomFrame","MineMeterBack"})svis(id,false);UI::SetPosition(this,"stage","MineBoardFrame",{layout.left-4,layout.top-4});UI::SetSize(this,"stage","MineBoardFrame",{layout.width+8,layout.height+8});svis("QPlate",false);svis("Question",false);svis("MineQuestionPlate",false);svis("MineQuestionText",false);svis("MineToggle",false);stext("MineQuestionText",padsystem::wrap(stage.value("question",std::string()),648,"Assets/Fonts/pretendard/Pretendard-Medium.otf",18).first);stext("MineToggle","Space  질문 표시");
 UI::SetPosition(this,"stage","Question",{36,606});UI::SetSize(this,"stage","Question",{1208,38});UI::SetFontSize(this,"stage","Question",std::min(26.f,1208.f/std::max(1,u8len(stage.value("question",std::string())))));
 stext("Question",stage.value("question",std::string()));
 UI::SetPosition(this,"stage","Hint",{28,666});UI::SetSize(this,"stage","Hint",{380,44});UI::SetFontSize(this,"stage","Hint",14);
 UI::SetPosition(this,"stage","StageTimer",{440,654});UI::SetSize(this,"stage","StageTimer",{300,50});
 stext("Hint",mineOpeningV4.active()?"초기 자동 발굴 중… 보드가 열리면 조작할 수 있어요":mineV4.undoEnabled?"좌클릭 제거 · 우클릭 지목\nBackspace 되돌리기":"좌클릭 제거 · 우클릭 지목");svis("Hint",false);
}
bool Yumeno::v4MineUpdate(float delta,bool click){
 if(!v4TaskActive||stageKind!="mindmine")return false;
 const minelayoutv4::Board layout(mineV4.width,mineV4.height);
 if(mineTimeoutV4>0){mineTimeoutV4+=delta;if(mineTimeoutV4>=1.2f){svis("MineTimeout",false);++retries;restartStage=true;}return true;}
 auto drawClock=[&]{char clock[16];std::snprintf(clock,sizeof(clock),"%02d:%02d:%03d",mineV4.time/3600,(mineV4.time/60)%60,(mineV4.time%60)*1000/60);std::string key=std::string(mineV4.time<=3600?"r":"g")+clock;for(int i=0;i<9;i++){auto id="MineClock"+std::to_string(i);svis(id,true);if(mineClockV4.empty()||key[0]!=mineClockV4[0]||key[i+1]!=mineClockV4[i+1])UI::SetTexture(this,"minehudv4",id,"Assets/Art/ui/mine_digit_"+key.substr(0,1)+(clock[i]==':'?"colon":std::string(1,clock[i]))+".svg");}mineClockV4=key;};
 if(mineSuccessTimeV4>=0){
  mineSuccessTimeV4+=delta;float t=mineSuccessTimeV4;
  if(t<5.72f)drawClock();else for(int i=0;i<9;i++)svis("MineClock"+std::to_string(i),false);
  svis("MineCursor",false);svis("MinePenalty",false);for(int i=0;i<10;i++)svis("MineBurst"+std::to_string(i),false);
  fractureControl(t<5.2f?"off":t<5.72f?"capture":t<6.92f?"animate":"off",t-5.72f);
  if(t>=5.72f){UI::SetVisible(this,"stage","root",false);UI::SetVisible(this,"minev4","root",false);UI::SetVisible(this,"minehudv4","root",false);}
  svis("MineEntryClear",t>=.35f&&t<1.75f);
  if(t>=.35f&&t<1.75f)UI::SetOpacity(this,"minehudv4","MineEntryClear",court::smooth5((t-.35f)/.12f)*(1-court::smooth5((t-1.4f)/.35f)));
  svis("MineEntryComplete",false);
  endingSourceFrame("complete",t>=5.72f&&t<6.79f?int((t-5.72f)*60):-1,24);
  int phase=t<1.f?0:t<5.35f?1:t<5.95f?2:t<6.75f?3:4;
  if(phase!=mineSuccessPhaseV4){mineSuccessPhaseV4=phase;if(phase==2)sfx("v3se_327");}
  for(auto id:{"Question","Hint","MineTimer","MineHealth","MineFocus","StageMsg","MineQuestionPlate","MineQuestionText","MineToggle"})svis(id,false);
  svis("MineHintHit",false);for(int i=0;i<10;i++)svis("MineHint"+std::to_string(i),false);for(auto id:{"MineBoardFrame","MineBottomFrame","MineMeterBack"})svis(id,t<5.72f);for(int i=0;i<10;i++){svis("MineHealthSegment"+std::to_string(i),t<5.72f&&float(mineV4.hp)/std::max(1,maxHearts*2000)*10>i);svis("MineFocusSegment"+std::to_string(i),t<5.72f&&debate.focus/maximumFocus()*10>i);}
  if(t-delta<.32f)for(int i=0;i<int(cells.size());i++){auto id="Cell"+std::to_string(i);UI::SetOpacity(this,"minev4",id,mineTileAlphaV4[i]*std::max(0.f,1-t/.32f));if(t>=.32f)svis(id,false);}
  if(stage.contains("mineObjects"))for(int i=0;i<int(stage["mineObjects"].size());i++)svis("MineObject"+std::to_string(i),t<5.72f);
  svis("MineResultBand",false);
  const float solutionBegin=2.5f,solutionEnd=solutionBegin+armingfinish::frames.size()/60.f;
  solutionCutinFrame(t>=solutionBegin&&t<solutionEnd?int((t-solutionBegin)*60):-1);
  svis("MineResultCrack",false);endingSourceFrame("crack",t>=5.35f&&t<5.75f?int((t-5.35f)*60):-1);
  for(int i=0;i<12;i++){auto id="MineResultShard"+std::to_string(i);bool on=t>=5.72f&&t<6.75f&&!fractureSupportedV4;svis(id,on);if(on){float p=(t-5.72f)/1.03f,a=i*court::PI/6;UI::SetPosition(this,"stage",id,{560+std::cos(a)*(80+850*p),280+std::sin(a)*(50+530*p)+160*p*p});UI::SetRotation(this,"stage",id,i*31+190*p);UI::SetOpacity(this,"stage",id,1-p);}}
  svis("MineResultBlack",false);endingSourceBlack(t>=5.72f?1.f:0.f);
  if(t>=7.1f){solutionCutinFrame(-1);endingSourceClear();mineSuccessTimeV4=-1;beginScript();}return true;
 }
 for(int i=0;i<10;i++)for(bool mental:{false,true}){auto id=std::string(mental?"MineFocusSegment":"MineHealthSegment")+std::to_string(i);float amount=std::clamp((mental?debate.focus/maximumFocus():float(mineV4.hp)/std::max(1,maxHearts*2000))*10-i,0.f,1.f);svis(id,amount>0&&mineIntroV4<=1.9f);if(amount>0&&mineIntroV4<=1.9f)UI::SetSize(this,"stage",id,{28*amount,11});}
 if(minePaintAt<int(cells.size())){int end=std::min(int(cells.size()),minePaintAt+48);float cw=layout.cell,ch=layout.cell;for(;minePaintAt<end;minePaintAt++){auto id="Cell"+std::to_string(minePaintAt);UI::SetPosition(this,"minev4",id,{layout.left+(minePaintAt%mineV4.width)*cw,layout.top+(minePaintAt/mineV4.width)*ch});UI::SetSize(this,"minev4",id,{cw,ch});UI::SetTexture(this,"minev4",id,trialui::MINE_TILES[cells[minePaintAt]]);UI::SetOpacity(this,"minev4",id,1);}return true;}

 if(mineIntroV4>0){
  const float prev=2.8f-mineIntroV4;
  mineIntroV4=std::max(0.f,mineIntroV4-delta);
  const float t=2.8f-mineIntroV4;
  // Reference frames: lettering over the courtroom, same lettering over the
  // completed board, then the clock and the movable pointer.
  if(prev<.9f&&t>=.9f){
   for(auto id:{"MineBackdrop","MineBoardFrame","MineBottomFrame","MineMeterBack","MineToggle"})svis(id,true);
   for(int i=0;i<int(cells.size());i++)svis("Cell"+std::to_string(i),true);
   svis("MineBg",!stage.contains("mineObjects"));
   if(stage.contains("mineObjects"))for(int i=0;i<int(stage["mineObjects"].size());i++)svis("MineObject"+std::to_string(i),true);
  }
  const float in=court::smooth5(t/.4f),out=court::smooth5((t-1.15f)/.68f),alpha=in*(1-out);
  auto layer=[&](const char* id,float opacity){svis(id,opacity>.005f);if(opacity>.005f)UI::SetOpacity(this,"minehudv4",id,opacity);};
  const float lit=court::smooth5((t-.83f)/.14f);
  layer("MineEntryDim",.62f*alpha);
  layer("MineEntryBlur",alpha);
  layer("MineEntryTitle",alpha*(1-lit));
  layer("MineEntrySubtitle",alpha);
  layer("MineEntryEcho",lit*(1-out));
  if(lit>0&&out<1){
   // The afterimage expands beyond the board as the solid strokes dissolve.
   const float scale=1+.22f*out;
   UI::SetPosition(this,"minehudv4","MineEntryEcho",{640-652*scale,368-404*scale});
   UI::SetSize(this,"minehudv4","MineEntryEcho",{1304*scale,808*scale});
  }
  layer("MineEntryRays",std::max(0.f,1-std::abs(t-1.16f)/.42f));
  layer("MineEntrySpark",std::max(0.f,1-std::abs(t-1.22f)/.31f));
  if(t>=2.42f)drawClock();
  return true;
 }
 if(mineOpeningV4.active()){minigameTicksV4+=delta*60;int frames=int(minigameTicksV4);minigameTicksV4-=frames;for(int i=0;i<frames&&mineOpeningV4.active();i++){int cell=mineOpeningV4.tick(mineV4);if(cell>=0){cells[cell]=-1;svis("Cell"+std::to_string(cell),false);}}if(!mineOpeningV4.active())stext("Hint",mineV4.undoEnabled?"좌클릭 제거 · 우클릭 지목\nBackspace 되돌리기":"좌클릭 제거 · 우클릭 지목");return true;}
 if(pressed("Backspace")){if(mineV4.undo()==trialv4::Result::Rewound){sfx("v3se_004");for(int i=0;i<int(cells.size());i++){if(cells[i]==mineV4.cells[i])continue;bool restored=cells[i]<0;mineTileMotionV4[i]={cells[i],0};cells[i]=mineV4.cells[i];mineTileStyleV4[i]=-1;if(restored){svis("Cell"+std::to_string(i),true);mineTileAlphaV4[i]=0;UI::SetOpacity(this,"minev4","Cell"+std::to_string(i),0);}}}else sfx("v3se_000");}
 if(pressed("Space")){mineQuestionVisibleV4=!mineQuestionVisibleV4;svis("MineQuestionPlate",mineQuestionVisibleV4);svis("MineQuestionText",mineQuestionVisibleV4);stext("MineToggle",mineQuestionVisibleV4?"Space  질문 숨기기":"Space  질문 표시");}
 float u=(aimX-layout.left)/layout.width,v=(aimY-layout.top)/layout.height;
 int col=int(u*mineV4.width),row=int(v*mineV4.height);bool in=u>=0&&u<1&&v>=0&&v<1;
 svis("MineCursor",in);if(in){UI::SetPosition(this,"minehudv4","MineCursor",{aimX-40,aimY-40});UI::SetOpacity(this,"minehudv4","MineCursor",.8f+.2f*std::abs(std::sin(mineFocusPulseV4*4)));}
 const bool held=Input::IsKeyDown("Shift");if(!held||debate.focus<=0)mineFocusActiveV4=false;else if(pressed("Shift")&&debate.focus>20)mineFocusActiveV4=true;const bool focus=mineFocusActiveV4;debate.focus=std::clamp(debate.focus+(focus?-30.f:8.f)*delta,0.f,maximumFocus());
 const int cell=in?row*mineV4.width+col:-1;
 const int region=in?(stage.contains("mineObjects")?taskv4::mineObjectRegion(stage,u,v):taskv4::region(stage,u,v)):-1;
 if(!focus&&click){const int before=mineV4.time,prior=cell>=0?cells[cell]:-1;mineClick(cell);if(prior>=0&&cells[cell]<0){mineBurstTimeV4=.48f;mineBurstColorV4=prior;}if(mineV4.time<before){minePenaltyV4=.7f;UI::SetPosition(this,"stage","MinePenalty",{std::clamp(aimX-24,0.f,1110.f),std::clamp(aimY-58,0.f,590.f)});}}
 if(mineBurstTimeV4>0){
  mineBurstTimeV4=std::max(0.f,mineBurstTimeV4-delta);
  const float age=.48f-mineBurstTimeV4;
  const float flight=std::clamp((age-.075f)/.405f,0.f,1.f);
  for(int i=0;i<10;i++){
   const auto id="MineBurst"+std::to_string(i);
   const bool visible=age>.075f&&mineBurstTimeV4>0;
   svis(id,visible);
   if(!visible)continue;
   const int origin=mineBurstCellsV4[i*mineBurstCellsV4.size()/10];
   const float x=layout.left+(origin%mineV4.width+.5f)*layout.cell;
   const float y=layout.top+(origin/mineV4.width+.5f)*layout.cell;
   const float angle=i*court::PI/5, radius=(.10f+(.9f+.3f*(i%3))*flight)*layout.cell;
   UI::SetTexture(this,"minehudv4",id,"Assets/Art/ui/mine_chip_"+std::to_string(mineBurstColorV4)+".svg");
   UI::SetPosition(this,"minehudv4",id,{x-8+radius*std::cos(angle),y-8+radius*std::sin(angle)+layout.cell*flight*flight});
   UI::SetRotation(this,"minehudv4",id,i*31+240*flight);
   UI::SetOpacity(this,"minehudv4",id,1-court::smooth5((flight-.35f)/.65f));
  }
 }
 minePenaltyV4=std::max(0.f,minePenaltyV4-delta);svis("MinePenalty",minePenaltyV4>0);if(minePenaltyV4>0)UI::SetOpacity(this,"stage","MinePenalty",std::min(1.f,minePenaltyV4*5));
 // Exposed edges identify the connected group under the pointer. No extra
 // tile actors or permanent per-frame full-widget rebuilds are required.
 auto highlighted=mineV4.group(cell);
 const int cursor=highlighted.size()>1?2:highlighted.size()==1?1:region<0?0:mineV4.imageExposed(region)?4:3;
 if(in&&cursor!=mineCursorStateV4){mineCursorStateV4=cursor;UI::SetTexture(this,"minehudv4","MineCursor","Assets/Art/ui/mine_cursor_"+std::to_string(cursor)+".svg");}
 std::set<int> members(highlighted.begin(),highlighted.end());mineFocusPulseV4+=delta;
 for(int k=0;k<int(cells.size());k++){
  auto id="Cell"+std::to_string(k);int mask=0;
  const int w=mineV4.width;auto joins=[&](int n){return cells[k]>=0&&cells[n]==cells[k];};
  const bool up=k>=w&&joins(k-w),right=k%w+1<w&&joins(k+1),down=k+w<int(cells.size())&&joins(k+w),left=k%w!=0&&joins(k-1);
  const bool groupFocus=focus&&(up||right||down||left);if(groupFocus||(!focus&&members.count(k))){if(!up)mask|=1;if(!right)mask|=2;if(!down)mask|=4;if(!left)mask|=8;}
  auto& motion=mineTileMotionV4[k];
  int shownColor=cells[k];
  if(motion.oldColor>=0){
   const bool firstFrame=motion.elapsed==0;
   motion.elapsed+=delta;
   if(shownColor<0){
    if(firstFrame){
     UI::SetPosition(this,"minev4",id,{layout.left+(k%w)*layout.cell,layout.top+(k/w)*layout.cell});
     UI::SetSize(this,"minev4",id,{layout.cell,layout.cell});
    }
    mineTileAlphaV4[k]=1-court::smooth5((motion.elapsed-.075f)/.22f);
    if(motion.elapsed>=.295f){svis(id,false);motion={};}
   }else{
    const float phase=std::min(1.f,motion.elapsed/.32f);
    const float width=layout.cell*std::max(.045f,std::abs(std::cos(court::PI*phase)));
    UI::SetPosition(this,"minev4",id,{layout.left+(k%w)*layout.cell+(layout.cell-width)*.5f,layout.top+(k/w)*layout.cell});
    UI::SetSize(this,"minev4",id,{width,layout.cell});
    if(phase<.5f)shownColor=motion.oldColor;
    if(phase<1)mask=0;
    else motion={};
   }
  }
  if(shownColor>=0){
   mineTileAlphaV4[k]=std::min(1.f,mineTileAlphaV4[k]+delta*3.f);
   const int style=shownColor*16+mask;
   if(mineTileStyleV4[k]!=style){
    mineTileStyleV4[k]=style;
    std::string texture=trialui::MINE_TILES[shownColor];
    if(mask)texture.insert(texture.size()-4,"_edge"+std::to_string(mask));
    UI::SetTexture(this,"minev4",id,texture);
   }
  }
  float alpha=mineTileAlphaV4[k];if(groupFocus)alpha*=.55f+.45f*std::abs(std::sin(mineFocusPulseV4*4));UI::SetOpacity(this,"minev4",id,alpha);
 }

 bool hitVisible=mineV4.last>=0&&mineV4.clicks>0;svis("MineHintHit",hitVisible);if(hitVisible){float cw=layout.cell,ch=layout.cell;UI::SetTexture(this,"minev4","MineHintHit","Assets/Art/ui/mine_hit_"+std::to_string(std::min(2,mineV4.clicks))+".svg");UI::SetPosition(this,"minev4","MineHintHit",{layout.left+(mineV4.last%mineV4.width)*cw,layout.top+(mineV4.last/mineV4.width)*ch});UI::SetSize(this,"minev4","MineHintHit",{cw,ch});}
 if(!focus&&in&&(pressed("mouse1")||enterPressed)){

  if(region>=0&&mineV4.cells[cell]<0){int hp=mineV4.hp;auto result=mineV4.submitImage(region,255); // Sprite mode checked actual alpha>127; legacy photo mode checked the authored UV polygon first.
   if(result==trialv4::Result::Complete){debate.hearts=std::max(1,(mineV4.hp+1999)/2000);sfx("v3se_400");mineSuccessTimeV4=0;mineSuccessPhaseV4=-1;return true;}
   if(result==trialv4::Result::Wrong&&mineV4.hp<hp){debate.hearts=(mineV4.hp+1999)/2000;sfx("v3se_316");if(mineV4.hp<=0){debate.hearts=1;hurt();}int variant=-1;auto cause=stage["regions"][region].value("wrongVariant",std::string());auto variants=v4Task["queues"].value("wrongVariants",Json::array());for(int i=0;i<int(variants.size());i++)if(!cause.empty()&&variants[i].value("cause",std::string())==cause)variant=i;v4TaskWrong(variant);}
  }
 }
 v4MineHints();minigameTicksV4+=delta*60;int frames=int(minigameTicksV4);minigameTicksV4-=frames;mineV4.tick(frames);drawClock();
 if(mineV4.state==trialv4::Result::Failed){if(mineV4.time==0){mineTimeoutV4=.001f;sfx("v3se_328");svis("MineCursor",false);for(int i=0;i<10;i++)svis("MineBurst"+std::to_string(i),false);svis("MinePenalty",false);svis("MineQuestionPlate",false);svis("MineQuestionText",false);svis("MineToggle",false);svis("MineTimeout",true);}else{++retries;restartStage=true;}}return true;
}
void Yumeno::v4LieStart(){
 v4LieHeld=0;holdTime=-1;lie=false;opts.clear();optRects.clear();personIds={stage.at("targetActor").get<std::string>()};optHover=0;
 trialPickerClear();focusSpeaker(personIds[0],personIds[0]);debateHud(true);text("TrialSpeaker",nameOf(personIds[0]));
 bullets={{stage.value("answer",std::string()),stage.value("fact",std::string())}};bullet=0;showBullet();
 for(auto id:{"Question","QPlate","CardTitle","CardFrame","CardText","DescBox","Hint","AccFig","AccLbl","AccTag","AccName"})svis(id,false);
 for(auto id:{"Portrait","SpeakerPodium","TimerPanel","Timer","TrialBack"})UI::SetVisible(this,UI_ID,id,false);
}
bool Yumeno::v4LieUpdate(float delta,bool click){
 if(!v4TaskActive||stageKind!="lie")return false;
 if(debateResultTime>0){updateDebateFx(delta);if(debateResultTime<=0){v4Judgment="lie";beginScript();}return true;}
 if(pressed("Backspace")){v4LieHeld=0;optv4::Open(optionsV4);return true;}
 if(Input::IsKeyDown("Space"))v4LieHeld+=delta;else v4LieHeld=0;
 bool inverted=v4LieHeld>=.45f;holdTime=v4LieHeld>0?v4LieHeld:-1;if(lie!=inverted){lie=inverted;showBullet();}text("Bullet",stage.value(inverted?"lie":"fact",std::string()));updateDebateFx(delta);UI::SetVisible(this,"debatefx","ChargeState",false);
 const int seat=court::seatOf(stage.at("targetActor").get<std::string>());auto* target=actor("Seat"+std::to_string(seat));float x=0,y=0,depth=0;bool targetHit=false;
 if(target){auto p=Scene::GetPosition(target);if(court::screen(cam,p.x,p.y,p.z,x,y,depth)&&depth>.05f){float h=Components::GetFloat(target,"SpriteRenderer","height")*court::FOCAL/depth,w=Components::GetFloat(target,"SpriteRenderer","width")*court::FOCAL/depth;optRects={{x-w/2,y-h/2,w,h}};targetHit=aimX>=x-w/2&&aimX<=x+w/2&&aimY>=y-h/2&&aimY<=y+h/2;}}
 if(click&&targetHit){
  if(inverted){sfx("sfx_gunshot");holdTime=-1;debateSuccess("lie");}
  else{auto rows=v4Task["queues"].value("trueCardAttempt",Json::array());v4LieHeld=0;v4TaskQueue(rows,"resume");}
 }return true;
}
// Explicit QA fixture: exercises authored input without claiming the preceding investigation ran.
void Yumeno::DebugV4Task(const std::string& taskId){
 int chapter=taskId.size()>1&&taskId[1]>='1'&&taskId[1]<='6'?taskId[1]-'0':1;v4Start(std::to_string(chapter));
 if(!v4.graph["taskNodes"].contains(taskId)){lastError="No authored task QA fixture: "+taskId;return;}
 auto& tasks=storyv4::bucketData("Assets/Data/v4_story/native_tasks/",storyv4::bucket(taskId,64))["tasks"];const auto& bundle=tasks.at(taskId);
 for(auto& id:bundle.value("requiresEvidence",Json::array())){auto key=id.get<std::string>();v4.evidence[key]={{"name",key},{"text","QA fixture required evidence"}};cards.insert(key);}
 // Give the current chapter's existing cards only, to exercise actual inventory pagination.
 auto catalogue=v4.graph.value("evidenceCatalog",Json::object());for(auto& [id,e]:catalogue.items()){v4.evidence[id]={{"name",e.value("name",id)},{"text",e.value("text",std::string())}};cards.insert(id);}
 storyv4::jump(v4,v4.graph["taskNodes"][taskId].get<std::string>());v4Enter();
}

void Yumeno::v4ArmResponse(int index){
 int at=0;for(auto& wave:stage.value("waves",Json::array()))for(auto& pair:wave.value("pairs",Json::array())){
  if(at++!=index)continue;auto response=pair.value("response",Json::object());if(response.is_object()&&response.contains("text"))v4TaskQueue(Json::array({response}),"resume");else if(response.is_array())v4TaskQueue(response,"resume");return;
 }
}
bool Yumeno::v4ArmRetry(){
 if(v4TaskActive&&stageKind=="armament"&&stage.contains("waveIndexByLine")){
  restartStage=false;v4ResetHearts(maxHearts);armingV4.hp=armingV4.maxHp;armingV4.tension=10;armingV4.combo=0;
  int damage=0;for(int i=0;i<armRhythmV4.phase;i++)damage+=armrhythm::phaseBudgets(chapterAt)[i];armingV4.opponent=armingV4.totalOpponent-damage;
  armRhythmV4.resetPhase();armFinal=-1;armLastIntro=0;stageTime=0;v4CancelInput();return true;
 }

 if(!v4TaskActive||stageKind!="armament"||!stage.contains("waveIndexByLine")||!stage.contains("waves"))return false;
 auto indices=stage["waveIndexByLine"].get<std::vector<int>>();if(indices.empty())return false;
 int current=std::clamp(armLine,0,int(indices.size())-1),wave=indices[current];
 if(wave<0||wave>=int(stage["waves"].size())||stage["waves"][wave].value("retryPolicy",std::string())!="sameWave")return false;
 int first=current;while(first>0&&indices[first-1]==wave)--first;
 restartStage=false;armingV4.hp=debate.hearts*2000;v4TaskEntryHp=armingV4.hp;v4TaskEntryHearts=debate.hearts;
 armingV4.opponent=std::max(30,armingV4.totalOpponent-first*30);armingV4.tension=10;armingV4.combo=0;armLine=first;armFinal=-1;armLastIntro=0;armBeat=0;stageTime=0;
 for(int i=0;i<4;i++)for(auto prefix:{"Piece","ArmPieceBand","ArmPieceKey"})svis(std::string(prefix)+std::to_string(i),false);svis("ArmQuestion",false);svis("ArmJoined",false);svis("Ring",true);svis("RingCore",true);svis("ArmLine",true);stext("ArmLine",stage["lines"][armLine].get<std::string>());
 trialui::armNote(armingV4,stage,++armHits,armLine);v4CancelInput();return true;
}
void Yumeno::v4ArmFinalShow(){
 if(armFinal<0)return;
 if(v4TaskActive&&armLastIntro==0){armLastIntro=118/60.f;sfx("v3se_032");return;}
 stageMsgTimer=0;svis("StageMsg",false); // A previous HIT/MISS label cannot cover the final phrase.
 const auto& answer=chapterAt==6&&armQuestionPhase<3?taskv4::finalArmamentQuestion(stage,armQuestionPhase):stage;
 auto final=answer.at("final").get<std::vector<std::string>>();if(final.size()!=4)throw std::runtime_error("Last phrase must contain four authored fragments");
 armPiecesV4=trialv4::FourPieces{};armFinal=0;armOrder={0,1,2,3};v4ArmChoices.clear();UI::SetScale(this,trialui::ID,"ArmJoined",{1,1});UI::SetScale(this,trialui::ID,"ArmJoinedInk",{1,1});
 int shift=v4TaskActive?1+int(storyv4::bucket(stage.value("id",std::string()),3)):stageAt%3+1;std::rotate(armOrder.begin(),armOrder.begin()+shift,armOrder.end());
 for(int i=0;i<4;i++){
  const auto& value=final[armOrder[i]];v4ArmChoices.push_back(value);auto id="Piece"+std::to_string(i);stext(id,value);UI::SetFontSize(this,trialui::ID,id,std::min(30.f,296.f/std::max(1,u8len(value))));svis(id,true);svis("ArmPieceBand"+std::to_string(i),true);svis("ArmPieceKey"+std::to_string(i),true);UI::SetOpacity(this,trialui::ID,"ArmPieceKey"+std::to_string(i),1.f);
 }
 svis("ArmLine",false);svis("ArmLineInk",false);svis("ArmNoteKey",false);svis("ArmNoteType",false);svis("Hint",false);svis("QBand",false);svis("QText",false);stext("ArmQuestion",answer.value("question",std::string()));svis("ArmQuestion",true);stext("ArmJoined",answer.value("finalSubject",std::string()));svis("ArmJoined",true);
}

bool Yumeno::v4LieCommit(bool correct){
 int cost=lieV4.pending,hp=lieV4.settleHp(v4TaskHp(),correct);lieV4Ticks=0;holdTime=-1;lie=lieCost=false;if(!correct&&cost>0)sfx("v3se_316");
 v4TrialHp=v4TaskEntryHp=hp;debate.hearts=v4TaskEntryHearts=(hp+1999)/2000;shownHearts=-1;
 if(hp>0)return true;
 // Raw pending cost has already been applied; don't run another hurt/debit.
 shotRecoveryV4.reset();v4NoiseReset();message("발언력이 바닥났어요… 처음부터!",2.f);v4ResetHearts(maxHearts);if(v4TaskActive){debate.restartRows();aimSwayV4.reset();aimPointerV4={};aimAssistV4.active=false;}else{debate.broken.assign(debate.lines.size(),false);debate.index=0;debate.time=0;}debateTime=(v4TaskActive&&stageKind=="panic"?300.f:180.f)*trialTimeFactor()+(skillOn("debate_time")?10.f:0.f);++retries;debateInputArmed=false;shownLine=-1;showBullet();return false;
}
void Yumeno::v4CancelInput(){
 for(int layer=0;layer<4;layer++)pv4::HideSequence(presentationV4,layer);
 v4NoiseReset(); aimAssistV4.active=false;aimPointerV4={};
 if(!v4TaskActive&&holdTime>=0&&lie&&lieCost)debate.hearts=std::min(maxHearts,debate.hearts+1);
 lieV4.cancel();lieV4Ticks=0;holdTime=-1;lie=lieCost=false;v4LieHeld=0;v4TrialInputArmed=false;debateInputArmed=false;mouseWasDown=false;dragX=aimX;dragY=aimY;
 if(playingDebate)showBullet();
}

void Yumeno::v4LeaveTrial(){
 for(int layer=0;layer<4;layer++)pv4::HideSequence(presentationV4,layer);
 v4NoiseReset(); if(trialResultOn)trialResultClear();
 if(stageShown){sclear();cancelDebateIntro();resetDebateFx();v4TaskRoot(false);}
 v4TaskActive=v4QueueActive=v4Court=false;v4Task=Json::object();v4Queue=Json::array();playingDebate=inScript=false;debateIntroTime=-1;debateResultTime=clearTimer=slotTimer=slotHold=voteHostTime=0;stageKind.clear();holdTime=-1;lie=lieCost=false;lieV4.cancel();lieV4Ticks=0;reviveUsed=sdGuardUsed=missGuardUsed=false;
 for(auto id:{"Trial","TrialBack","CourtDim","SpeakerPodium","Portrait"})UI::SetVisible(this,UI_ID,id,false);
 releaseTrialUi();scenesv4::release(scenesv4::court);
}
void Yumeno::v4BeginCourt(){
 pv4::StopAmbient(presentationV4);pv4::SceneReady(presentationV4,"court",true);
 resultv4::begin(trialResults,v4.graph.value("chapter",std::string()));
 debate=debate::State{};maxHearts=growthv4::MaximumHp(growthV4)/2000;debate.hearts=maxHearts;debate.focus=maximumFocus();v4TrialHp=maxHearts*2000;shownHearts=-1;correctCount=retries=0;reviveUsed=sdGuardUsed=missGuardUsed=false;v4Court=true;
}
void Yumeno::DebugV4CompletionFixture(){
 DebugV4Task("T1-ANSWER-A01");bonds["sho"]=4;growthV4.owned.insert("sho1");DebugPlayerProgressFixture(500);growthv4::Toggle(growthV4,"sho1",playerprogress::level(playerProgress),true);correctCount=1;v4TrialHp=v4TaskEntryHp=4000;debate.hearts=v4TaskEntryHearts=2;
}
