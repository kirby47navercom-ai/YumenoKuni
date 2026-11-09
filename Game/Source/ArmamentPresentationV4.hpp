#include "ArmamentIntroSourceV4.hpp"
// Symbolic armor presentation follows actual opponent HP. Rules/answers stay
// in Arming and the authored queues; this layer never changes a judgment.
namespace armvisualv4 {
inline std::map<std::string,std::string> blends;
inline const hb::Json& phrase(const hb::Json& rows,const armrhythm::State& rhythm,int index){
 if(rows.front().is_array()){
  const auto& wave=rows.at(rhythm.phase);
  return wave.at(std::max(0,index-rhythm.phasePhraseBase)%wave.size());
 }
 return rows.at(std::max(0,index)%rows.size());
}
inline void show(const std::string& id,bool on){gputrialhudv4::setVisible(id,on);}
inline void rect(const std::string& id,float x,float y,float w,float h){gputrialhudv4::setPosition(id,{x,y});gputrialhudv4::setSize(id,{w,h});}
inline void texture(const std::string& id,const std::string& value){gputrialhudv4::setTexture(id,value);}
// The source SFL owns the band bounds; no fullscreen duplicate underneath.
inline void finishBackdrop(const std::string& id,int){show(id,false);}

template<class Frames>inline void frame(const Frames& frames,const std::vector<std::string>& textures,int at,const std::string& prefix="ArIntro"){const auto& rows=frames[std::clamp(at,0,int(frames.size())-1)];for(int i=0;i<20;i++){auto id=prefix+std::to_string(i);show(id,i<int(rows.size()));if(i>=int(rows.size()))continue;const auto& r=rows[i];texture(id,textures[r.texture]);auto blend=textures[r.texture].find("DXT1")!=std::string::npos?"additive":"translucent";if(blends[id]!=blend){Components::SetString(gputrialhudv4::nodes.at(id).actor,"SpriteRenderer","blendMode",blend);blends[id]=blend;}rect(id,r.x,r.y,r.w,r.h);gputrialhudv4::setRotation(id,r.rotation);gputrialhudv4::setOpacity(id,r.alpha);}}

}
#include "ArmamentSiteRenderV4.hpp"
void Yumeno::armamentVisualHide(){gputrialhudv4::setVisible("ArmSceneRoot",false);for(auto id:{"ArmamentBoss","ArmamentBossPrevious"})if(auto* a=actor(id))Components::Set(a,"SpriteRenderer","visible",false);}
void Yumeno::armamentVisualStart(){
 if(!v4TaskActive)return;
 const auto bank=Data::Get("Assets/Data/armament_figures_v4.json");auto who=stage.value("opponent",std::string());
 if(!bank["figures"].contains(who))throw std::runtime_error("Missing armament figure: "+who);
 armFigureStates=bank["figures"][who]["states"];if(armFigureStates.size()!=3)throw std::runtime_error("Armament requires three reviewed armor states");
 armDefeatFigure=bank["figures"][who].at("defeat");
 armStreamBank=bank.at("presentation");if(armStreamBank.contains("transcriptsPath"))armStreamBank["transcripts"]=Data::Get(armStreamBank.at("transcriptsPath").get<std::string>());armvisualv4::blends.clear();
 if(chapterAt==6){const auto mask=Data::Get("Assets/Data/armament_final_ui.json");armStreamBank["obscurer"]=mask;for(const auto& n:mask.at("nodes"))armStreamBank["nodes"].push_back(n);}
 if(!gputrialhudv4::ready)throw std::runtime_error("Armament GPU scene is not ready");
 for(auto root:{"ArmSceneRoot","ArmamentRoot","ArmIntroRoot"}){gputrialhudv4::parents[root]=std::string(root)=="ArmSceneRoot"?"":"ArmSceneRoot";gputrialhudv4::visible[root]=std::string(root)!="ArmIntroRoot";gputrialhudv4::opacity[root]=1;}
 for(const auto& row:armStreamBank["nodes"]){const auto id=row["id"].get<std::string>();gputrialhudv4::Node n;n.id=id;n.parent=row.value("parent",std::string("ArmamentRoot"));n.image=true;n.ax=n.ay=0;n.x=row["rect"][0];n.y=row["rect"][1];n.w=row["rect"][2];n.h=row["rect"][3];n.texture=row.value("texture",std::string());n.visible=row.value("initiallyVisible",false);n.rotation=row.value("rotation",0.f);n.actor=actor("TrialGpu_"+id);if(!n.actor)throw std::runtime_error("Missing armament sprite "+id);gputrialhudv4::nodes[id]=n;if(row.value("native",false))hb::UI::SetVisible(UI::Owner(this,"stage"),"stage",id,false);}
 for(auto it=armStreamBank["aliases"].begin();it!=armStreamBank["aliases"].end();++it)gputrialhudv4::textureAliases[it.key()]=it.value().get<std::string>();
 // The frame and shoulder portrait share the native game's existing GPU path.
 armvisualv4::show("ArName",true);auto name=stage.value("opponentDisplay",stage.value("opponent",std::string()));armvisualv4::texture("ArName",armStreamBank["labels"].at(name));
 armvisualv4::texture("ArmFace",armStreamBank["textures"]["hero"]);armvisualv4::rect("ArmFace",987,475,182,149);
 armIntro=(armingintro::frames.size()+24)/60.f;armLastIntro=0;armFinish=armRatingTime=armFeverTicks=0;armArmorPhase=-1;armVisualTime=armArmorTransition=armVisualHit=0;armamentVisualUpdate(0);
}
void Yumeno::armamentVisualUpdate(float delta){
 if(!v4TaskActive||stageKind!="armament"||armFigureStates.size()!=3)return;
 auto* current=actor("ArmamentBoss");auto* previous=actor("ArmamentBossPrevious");if(!current||!previous)return;
 armVisualTime+=delta;armVisualHit=std::max(0.f,armVisualHit-delta);
 if(armFinish>0&&ARM_FINISH_SECONDS-armFinish>=1.f){
  const float collapse=court::smooth5((ARM_FINISH_SECONDS-armFinish-1.f)/.38f),height=3.9f;
  Components::SetString(current,"SpriteRenderer","texture",armDefeatFigure.at("texture").get<std::string>());
  Components::Set(current,"SpriteRenderer","height",height);Components::Set(current,"SpriteRenderer","width",height*armDefeatFigure.at("aspect").get<float>());
  Components::Set(current,"SpriteRenderer","visible",true);Components::Set(previous,"SpriteRenderer","visible",false);
  Sprites::SetColor(current,{1,1,1,1});Scene::SetPosition(current,{-.6f,1.85f+.18f*(1-collapse),0});Scene::SetRotation(current,{0,0,0});return;
 }
 float remaining=float(armingV4.opponent)/std::max(1,armingV4.totalOpponent);int phase=std::min(2,armRhythmV4.phase);
 // Leave the durability carrier above the head and the time display below feet.
 constexpr float figureHeight=6.6f;
 auto apply=[&](hb::Actor* a,int state){const auto& row=armFigureStates[state];Components::SetString(a,"SpriteRenderer","texture",row.at("texture").get<std::string>());Components::Set(a,"SpriteRenderer","height",figureHeight);Components::Set(a,"SpriteRenderer","width",figureHeight*row.at("aspect").get<float>());};
 if(phase!=armArmorPhase){
  if(armArmorPhase>=0){apply(previous,armArmorPhase);Components::Set(previous,"SpriteRenderer","visible",true);armArmorTransition=.65f;if(auto* c=actor("Camera"))Camera::Shake(c,.035f,.20f);Camera::Flash({.92f,.82f,1,.18f},.18f);sfx("v3se_418");music(std::string("bgm_trial_armament_")+std::to_string(phase==0?2:phase==1?3:5));}
  apply(current,phase);armArmorPhase=phase;
 }
 Components::Set(current,"SpriteRenderer","visible",true);
 armArmorTransition=std::max(0.f,armArmorTransition-delta);float blend=1-armArmorTransition/.65f;
 Sprites::SetColor(current,{1,1,1,blend});Sprites::SetColor(previous,{1,1,1,1-blend});if(armArmorTransition<=0)Components::Set(previous,"SpriteRenderer","visible",false);
 float impact=armVisualHit/.18f;Vec3 position{-.6f+armRhythmV4.moveX*(2.f/3)*cam.z/court::FOCAL+std::sin(armVisualTime*51)*.07f*impact,3.2f-armRhythmV4.moveY*(2.f/3)*cam.z/court::FOCAL,0};Scene::SetPosition(current,position);Components::Set(current,"SpriteRenderer","height",figureHeight*armRhythmV4.scaleY);Components::Set(current,"SpriteRenderer","width",figureHeight*armFigureStates[phase].at("aspect").get<float>()*armRhythmV4.scaleX);
 Scene::SetPosition(previous,{position.x-std::pow(1-blend,2)*.8f,position.y-(1-blend)*.2f,0});Scene::SetRotation(previous,{0,0,(1-blend)*-8});
 armRatingTime=std::max(0.f,armRatingTime-delta);armvisualv4::show("ArRating",armRatingTime>0);armvisualv4::show("ArSpark",armRatingTime>0);if(armRatingTime>0){float t=1-armRatingTime/.45f;armvisualv4::rect("ArRating",armHitPoint.x-110,armHitPoint.y-85-t*25,220,65);gputrialhudv4::setOpacity("ArRating",std::min(1.f,armRatingTime*6));float size=60+t*100;armvisualv4::rect("ArSpark",armHitPoint.x-size/2,armHitPoint.y-size/2,size,size);gputrialhudv4::setOpacity("ArSpark",1-t);}
 if(armFinal>=0){if(chapterAt==6)for(int slot=-1;slot<12;slot++)for(int pass=0;pass<2;pass++)armvisualv4::show("ArObscure"+(slot<0?std::string("Moving"):std::to_string(slot))+"_"+std::to_string(pass),false);armsitevisual::hideAll();for(int i=0;i<armsitevisual::POOL;i++)armvisualv4::show("ArSiteWord"+std::to_string(i),false);}
 if(armIntro<=0&&armLastIntro<=0&&armFinish<=0){
  armvisualv4::show("ArHeroName",true);int ms=int(std::max(0.f,stageLimit-stageTime)*1000);char time[20];std::snprintf(time,sizeof time,"%02d:%02d:%03d",ms/60000,ms/1000%60,ms%1000);
  for(int i=0;i<9;i++){auto id="ArClock"+std::to_string(i);armvisualv4::show(id,true);int digit=time[i]==':'?10:time[i]-'0';armvisualv4::texture(id,armStreamBank["textures"]["clock_"+std::to_string(digit)]);}
  int combo=std::min(999,armingV4.combo);armvisualv4::show("ArComboLabel",combo>0);for(int i=0;i<3;i++){auto id="ArComboDigit"+std::to_string(i);armvisualv4::show(id,combo>0&&(i==0||combo>=(i==1?10:100)));int value=i==0?combo%10:i==1?combo/10%10:combo/100;armvisualv4::texture(id,armStreamBank["textures"]["combo_"+std::to_string(value)]);}
 }

}

void Yumeno::armamentSites(){
 if(armStreamBank.is_null())return;
 const auto& transcript=armStreamBank.at("transcripts").at(v4Task.at("taskId").get<std::string>());
 const bool active=armFinal<0&&armIntro<=0&&armLastIntro<=0&&armFinish<=0;
 for(int slot=0;slot<armsitevisual::POOL;slot++){
  const armrhythm::Live* live=nullptr;for(const auto& n:armRhythmV4.live)if(n.slot==slot){live=&n;break;}
  const auto word="ArSiteWord"+std::to_string(slot);armvisualv4::show(word,active&&live&&!live->done);
  if(!active||!live){armsitevisual::hide(slot);continue;}
  const auto& n=*live;const bool held=n.heldSince>=0;
  const float x=n.source->x*2/3,y=n.source->y*2/3;const auto pose=armRhythmV4.pose(n);
  const float lead=std::max(.001f,n.target-n.spawn);
  const bool success=n.rating==trialv4::Rating::Critical||n.rating==trialv4::Rating::Hit||n.rating==trialv4::Rating::MashSuccess;
  const float progress=held?std::clamp((armRhythmV4.clock-n.heldSince)*60/std::max(1,n.note.holdFrames),0.f,1.f):0;
  armsitevisual::render(slot,int(n.note.type),armRhythmV4.clock-n.spawn,lead,n.done,success,n.done?armRhythmV4.clock-n.finished:0,held,progress,n.note.progress,n.note.button,armingV4.fever,x,y,pose[0],pose[1],1);
  if(n.done)continue;
  const auto& phrase=armvisualv4::phrase(transcript,armRhythmV4,n.phrase);armvisualv4::texture(word,phrase.at("texture").get<std::string>());
  const float scale=armRhythmV4.textScale(n),w=384*scale,h=72*scale;armvisualv4::rect(word,x-w/2,y-h/2,w,h);gputrialhudv4::setOpacity(word,1);gputrialhudv4::setRotation(word,pose[1]);
 }
 if(chapterAt==6&&armStreamBank.contains("obscurer")){
  const auto& tracks=armStreamBank.at("obscurer").at("tracks");
  for(int slot=-1;slot<armsitevisual::POOL;slot++){
   const armrhythm::Live* n=nullptr;for(const auto& q:armRhythmV4.live)if(q.slot==slot){n=&q;break;}
   bool on=active&&armRhythmV4.obscureActive&&!armingV4.fever&&(slot<0?armRhythmV4.obscureIndex==0:armRhythmV4.obscureIndex==1&&n&&!n->done&&(n->id&1));
   const auto prefix="ArObscure"+(slot<0?std::string("Moving"):std::to_string(slot))+"_";
   for(int pass=0;pass<2;pass++){const auto id=prefix+std::to_string(pass);armvisualv4::show(id,on);if(!on)continue;const auto& frames=tracks.at(slot<0?"moving":"odd").at("wait");int age=slot<0?int(armRhythmV4.obscureAge):int((armRhythmV4.clock-n->spawn)*60);const auto& meta=tracks.at(slot<0?"moving":"odd");int lead=meta.at("waitLead"),period=meta.at("waitPeriod");int frame=age<lead?age:lead+(age-lead)%period;const auto texture=frames.at(frame).at(pass).get<std::string>();armvisualv4::texture(id,texture);const auto& rect=armStreamBank.at("obscurer").at("rects").at(texture);float x=slot<0?armRhythmV4.obscureX*2/3:n->source->x*2/3,y=slot<0?armRhythmV4.obscureY*2/3:n->source->y*2/3;armvisualv4::rect(id,x+rect[0].get<float>(),y+rect[1].get<float>(),rect[2].get<float>(),rect[3].get<float>());}
  }
 }
 for(auto id:{"ArmLineInk","ArmLine","ArmNoteKey","ArmNoteType","Ring","RingCore"})svis(id,false);
}

void Yumeno::armamentRating(trialv4::Rating rating){
 const auto& layout=Data::Get("Assets/Data/presentation/v3_armament_layout.json");const auto& a=layout["tracks"][std::to_string(std::clamp(chapterAt,1,6))];const auto& p=a[armHits%a.size()];armHitPoint={p[0].get<float>()*2/3,p[1].get<float>()*2/3};armRatingTime=.45f;
 std::string label=rating==trialv4::Rating::Critical?"CRITICAL":rating==trialv4::Rating::Hit||rating==trialv4::Rating::MashSuccess?"HIT":"MISS";armvisualv4::texture("ArRating",armStreamBank["labels"].at(label));
}
bool Yumeno::armamentPresentationInput(float delta){
 if(!v4TaskActive||stageKind!="armament")return false;
 auto hide=[&](){gputrialhudv4::setVisible("ArmamentRoot",false);gputrialhudv4::setVisible("ArmIntroRoot",true);};
 auto restore=[&](){gputrialhudv4::setVisible("ArmamentRoot",true);gputrialhudv4::setVisible("ArmIntroRoot",false);};
 if(armIntro>0){hide();armIntro=std::max(0.f,armIntro-delta);int elapsed=int(((armingintro::frames.size()+24)/60.f-armIntro)*60);int at=elapsed<57?elapsed:elapsed<81?57:elapsed-24;armvisualv4::frame(armingintro::frames,armingintro::textures,at);if(armIntro<=0)restore();return true;}
 if(armLastIntro>0){hide();armLastIntro=std::max(0.f,armLastIntro-delta);int at=int((118/60.f-armLastIntro)*60);armvisualv4::frame(arminglast::frames,arminglast::textures,at);if(armLastIntro<=0){armLastIntro=-1;restore();v4ArmFinalShow();}return true;}
 if(armFinish>0){
  hide();const float before=ARM_FINISH_SECONDS-armFinish;armFinish=std::max(0.f,armFinish-delta);const float t=ARM_FINISH_SECONDS-armFinish;
  fractureControl(t<3.1f?"off":t<3.55f?"capture":t<4.75f?"animate":"off",t-3.55f);
  armvisualv4::finishBackdrop("ArFinishBackdrop",int(t*60));
  if(t<armingfinish::frames.size()/60.f)armvisualv4::frame(armingfinish::frames,armingfinish::textures,int(t*60));
  else for(int i=0;i<20;i++)armvisualv4::show("ArIntro"+std::to_string(i),false);
  endingSourceFrame("crack",t>=3.25f&&t<3.65f?int((t-3.25f)*60):-1);
  endingSourceFrame("refuteBreak",t>=3.55f&&t<4.62f?int((t-3.55f)*60):-1,24);
  endingSourceBlack(t>=3.65f?1.f:0.f);
  if(before<3.25f&&t>=3.25f)sfx("sfx_glass");if(before<3.55f&&t>=3.55f)sfx("sfx_break");
  if(armFinish<=0){endingSourceClear();armamentVisualHide();beginScript();}return true;
 }
 if(armingV4.fever){debate.focus=std::max(0.f,debate.focus-delta*(100.f/(difficultyV4.action==0?24.f:difficultyV4.action==1?12.f:6.f)));armingV4.tension=20;if(debate.focus<=0)armingV4.fever=false;}
 else if(pressed("e")||spacePressed){if(debate.focus>=maximumFocus()){armingV4.fever=true;armFeverTicks=0;sfx("v3se_446");}}
 if(!armingV4.fever)debate.focus=std::min(maximumFocus(),debate.focus+delta*(difficultyV4.action==0?12.f:6.f));
 armvisualv4::show("ArFever",armingV4.fever);return false;
}

// Shared authored solution timeline: empty strip -> ink arcs -> word and face.
// Do not flatten it into a single completed illustration.
void Yumeno::solutionCutinFrame(int frame){
 solutionFrameV4=frame;if(frame<0){gputrialhudv4::setVisible("SolutionRoot",false);if(UI::Mounted("minehudv4"))for(int i=-1;i<20;i++)UI::SetVisible(this,"minehudv4","SolutionNative"+(i<0?std::string("Back"):std::to_string(i)),false);return;}
 if(stageKind=="reasoning"){
  gputrialhudv4::setVisible("SolutionRoot",false);
  if(!UI::Mounted("endingsourcev4"))UI::Show(this,"Assets/UI/EndingSourceV4.hbwidget.json","endingsourcev4");
  const auto& rows=armingfinish::frames[std::clamp(frame,0,int(armingfinish::frames.size())-1)];
  for(int i=0;i<24;i++){auto id="EndingLeaf"+std::to_string(i);if(i>=int(rows.size())){UI::SetVisible(this,"endingsourcev4",id,false);continue;}const auto& r=rows[i];UI::SetTexture(this,"endingsourcev4",id,armingfinish::textures[r.texture]);UI::SetPosition(this,"endingsourcev4",id,{r.x,r.y});UI::SetSize(this,"endingsourcev4",id,{r.w,r.h});UI::SetRotation(this,"endingsourcev4",id,r.rotation);UI::SetOpacity(this,"endingsourcev4",id,r.alpha);UI::SetVisible(this,"endingsourcev4",id,r.w>0&&r.h>0&&r.alpha>0);}return;
 }
 if(stageKind=="mindmine"){
  gputrialhudv4::setVisible("SolutionRoot",false);
  const auto& rows=armingfinish::frames[std::clamp(frame,0,int(armingfinish::frames.size())-1)];
  const auto paint=[&](const std::string& id,const std::string& texture,float x,float y,float w,float h,float rotation,float alpha){UI::SetTexture(this,"minehudv4",id,texture);UI::SetPosition(this,"minehudv4",id,{x,y});UI::SetSize(this,"minehudv4",id,{w,h});UI::SetRotation(this,"minehudv4",id,rotation);UI::SetOpacity(this,"minehudv4",id,alpha);UI::SetVisible(this,"minehudv4",id,w>0&&h>0&&alpha>0);};
  UI::SetVisible(this,"minehudv4","SolutionNativeBack",false);
  for(int i=0;i<20;i++){auto id="SolutionNative"+std::to_string(i);if(i>=int(rows.size())){UI::SetVisible(this,"minehudv4",id,false);continue;}const auto& r=rows[i];paint(id,armingfinish::textures[r.texture],r.x,r.y,r.w,r.h,r.rotation,r.alpha);}return;
 }
 auto* first=actor("SolutionGpu0");if(!first)throw std::runtime_error("Solution sprites missing from active scene");
 if(!gputrialhudv4::ready)throw std::runtime_error("Solution GPU renderer is not ready");
 if(!gputrialhudv4::nodes.count("Solution0")||gputrialhudv4::nodes.at("Solution0").actor!=first){
  gputrialhudv4::parents["SolutionSceneRoot"]=stageKind=="anagram"?"AnagramRoot":"";gputrialhudv4::visible["SolutionSceneRoot"]=true;gputrialhudv4::opacity["SolutionSceneRoot"]=1;
  gputrialhudv4::parents["SolutionRoot"]="SolutionSceneRoot";gputrialhudv4::visible["SolutionRoot"]=false;gputrialhudv4::opacity["SolutionRoot"]=1;
  for(int i=-1;i<20;i++){auto id=i<0?std::string("SolutionBackdrop"):"Solution"+std::to_string(i);gputrialhudv4::Node n;n.id=id;n.parent="SolutionRoot";n.image=true;n.ax=n.ay=0;n.x=n.y=0;n.w=1280;n.h=720;n.visible=false;n.actor=actor("SolutionGpu"+(i<0?std::string("Back"):std::to_string(i)));if(!n.actor)throw std::runtime_error("Missing solution layer "+id);gputrialhudv4::nodes[id]=n;armvisualv4::blends.erase(id);}
 }
 armvisualv4::finishBackdrop("SolutionBackdrop",frame);
 gputrialhudv4::setVisible("SolutionRoot",true);armvisualv4::frame(armingfinish::frames,armingfinish::textures,frame,"Solution");
}
bool Yumeno::solutionCutinInput(float delta){
 if(solutionPendingV4<=0)return false;
 const float duration=armingfinish::frames.size()/60.f;solutionPendingV4=std::max(0.f,solutionPendingV4-delta);
 solutionCutinFrame(int((duration-solutionPendingV4)*60));
 if(solutionPendingV4<=0){solutionCutinFrame(-1);beginScript();}return true;
}
