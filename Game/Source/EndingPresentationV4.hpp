#include "EndingSourceFramesV4.hpp"
#include "ArmamentIntroSourceV4.hpp"
#include "PadWrapV4.hpp"

void Yumeno::endingSourceFrame(const std::string& name,int frame,int first,int count){
 if(frame<0){if(UI::Mounted("endingsourcev4"))for(int i=first;i<first+count;i++){UI::SetVisible(this,"endingsourcev4","EndingLeaf"+std::to_string(i),false);if(i<16){UI::SetVisible(this,"endingsourcev4","EndingWide"+std::to_string(i),false);UI::SetVisible(this,"endingsourcev4","EndingAgree"+std::to_string(i),false);}}return;}
 const auto& frames=endingsourcev4::frames.at(name);
 if(!UI::Mounted("endingsourcev4"))UI::Show(this,"Assets/UI/EndingSourceV4.hbwidget.json","endingsourcev4");
 const auto& rows=frames[std::clamp(frame,0,int(frames.size())-1)];
 if(int(rows.size())>count)throw std::runtime_error("Ending layer budget exceeded: "+name);
 for(int i=0;i<count;i++){
  const auto normal="EndingLeaf"+std::to_string(first+i),wideId="EndingWide"+std::to_string(first+i),agreeId="EndingAgree"+std::to_string(first+i);
  if(i>=int(rows.size())){UI::SetVisible(this,"endingsourcev4",normal,false);if(first+i<16){UI::SetVisible(this,"endingsourcev4",wideId,false);UI::SetVisible(this,"endingsourcev4",agreeId,false);}continue;}
  const auto& row=rows[i];const bool agree=name=="agreeCutin"&&first==0&&i<16,wide=agree&&row.w>1200;const auto id=agree?(wide?wideId:agreeId):normal;
  if(agree)UI::SetVisible(this,"endingsourcev4",normal,false);if(first+i<16){if(!wide)UI::SetVisible(this,"endingsourcev4",wideId,false);if(!agree||wide)UI::SetVisible(this,"endingsourcev4",agreeId,false);}
  int texture=row.texture;
  if(row.portrait>=0){
   std::string who;
   if(row.portrait==1&&debateResultSeat>=0)who=court::SEATS[debateResultSeat];
   else if(row.portrait>=2&&stage.contains("teams")){
    int index=0;for(const auto& actor:stage["teams"]["us"]){auto slug=actor.get<std::string>();if(slug=="mio")continue;if(index++==row.portrait-2){who=slug;break;}}
   }
   auto found=endingsourcev4::portraits.find(who);
   if(found==endingsourcev4::portraits.end()){UI::SetVisible(this,"endingsourcev4",id,false);continue;}
   texture=found->second.at(row.variant);
   if(name=="agreeCutin"&&row.portrait==1){auto custom=endingsourcev4::agreePortraits.find(who);if(custom==endingsourcev4::agreePortraits.end())throw std::runtime_error("Agreement portrait missing: "+who);texture=custom->second.at(endingsourcev4::agreeShadowTextures.count(row.texture)?1:0);}
  }
  UI::SetTexture(this,"endingsourcev4",id,endingsourcev4::textures.at(texture));
  UI::SetPosition(this,"endingsourcev4",id,{agree?(wide?row.x:row.x-640):row.x,agree?row.y-360:row.y});UI::SetSize(this,"endingsourcev4",id,{wide?1280-row.x-row.w:row.w,row.h});
  UI::SetRotation(this,"endingsourcev4",id,row.rotation);UI::SetOpacity(this,"endingsourcev4",id,row.alpha);
  UI::SetVisible(this,"endingsourcev4",id,row.alpha>0&&row.w>0&&row.h>0);
 }
}
void Yumeno::endingSourceBlack(float alpha){
 if(fractureSupportedV4&&fracturePhaseV4=="animate")alpha=0;
 if(alpha<=0&&!UI::Mounted("endingsourcev4"))return;
 if(!UI::Mounted("endingsourcev4"))UI::Show(this,"Assets/UI/EndingSourceV4.hbwidget.json","endingsourcev4");
 UI::SetOpacity(this,"endingsourcev4","EndingBlack",std::clamp(alpha,0.f,1.f));UI::SetVisible(this,"endingsourcev4","EndingBlack",alpha>0);
}
void Yumeno::endingSourceClear(){UI::Remove(this,"endingsourcev4");fractureControl("off");}

void Yumeno::fractureControl(const std::string& phase,float time,float duration){
 if(phase=="off"&&fracturePhaseV4.empty())return;
 const int frame=std::max(0,int(time*60));if(phase==fracturePhaseV4&&frame==fractureFrameV4)return;
 auto state=Json::parse(Game::GetStateText());
 fractureSupportedV4=state.value("renderCapabilities",Json::object()).value("screenFracture",false);
 if(phase=="off"){state.erase("screenFracture");fracturePhaseV4.clear();fractureFrameV4=-1;}
 else{
  if(phase=="animate"&&fracturePhaseV4!="animate"){
   UI::SetVisible(this,"trialvitalsv4","root",false);
   for(auto id:{"StatusPanel","StatusLabel"})UI::SetVisible(this,UI_ID,id,false);
   for(int i=0;i<10;i++)UI::SetVisible(this,UI_ID,"Star"+std::to_string(i),false);
  }
  if(fracturePhaseV4.empty())++fractureSerialV4;
  fracturePhaseV4=phase;fractureFrameV4=frame;
  state["screenFracture"]={{"id",fractureSerialV4},{"phase",phase},{"time",std::max(0.f,time)},{"duration",duration}};
 }
 Game::SetStateText(state.dump());
}

void Yumeno::beginModeEnding(const std::string& kind,const std::string& after,const std::string& next){
 sclear();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
 modeEndKindV4=kind;modeEndAfterV4=after;modeEndNextV4=next;modeEndTimeV4=0;
 if(kind=="scrum")UI::SetVisible(this,"scrumv4","root",false);
 if(kind=="climax"){
  v4ComicClear();auto target=endingsourcev4::climaxTargets.find(chapterAt);
  int seat=target==endingsourcev4::climaxTargets.end()?-1:court::seatOf(target->second);
  if(seat>=0)setCam(court::frame(court::seatAngle(seat),0,2.8f,1.75f,0,0));else courtWide();
 }
 if(kind=="reasoning"){
  svis("ReasoningBack",true);svis("ReasoningTitle",true);
  for(int i=0;i<3;i++){bool on=i<int(stage["questions"].size());auto suffix=std::to_string(i);svis("ReasoningPastBand"+suffix,on);svis("ReasoningPast"+suffix,on);if(on)stext("ReasoningPast"+suffix,padsystem::wrap(stage["questions"][i].value("answer",std::string()),320,"Assets/Fonts/pretendard/Pretendard-Medium.otf",18).first);}
 }
}
bool Yumeno::modeEndingInput(float delta){
 if(modeEndTimeV4<0)return false;
 const float before=modeEndTimeV4,t=modeEndTimeV4+=delta;float finish=0;
 if(modeEndKindV4=="scrum"){
  int size=int(stage["teams"]["us"].size()),variant=size>=7?1:size>=5?2:size==4?3:size==3?4:5;
  const std::string name="scrum"+std::to_string(variant);const float end=endingsourcev4::frames.at(name).size()/60.f;
  const float crack=end,split=crack+.4f; /* V3 HWGF48cBGF0 148.9~149.5 : 완전논파에서 바로 흰 번쩍(장면 복귀 없음) */
  fractureControl(t<end+.05f?"off":t<split?"capture":t<split+1.2f?"animate":"off",t-split);
  if(t<end)endingSourceFrame(name,int(t*60),0,48);
  else endingSourceFrame("crack",t>=crack&&t<split?int((t-crack)*60):-1);
  { /* V3 151.4 : 파편 뒤 「Break」(파랑 붓글씨) — 논파 끝과 같은 refuteBreak */ const float n=endingsourcev4::frames.at("refuteBreak").size()/60.f;endingSourceFrame("refuteBreak",t>=split&&t<split+n?int((t-split)*60):-1,24);}
  endingSourceBlack(t>=split?1.f:0.f);finish=split+endingsourcev4::frames.at("refuteBreak").size()/60.f+.3f;
  if(before<crack&&t>=crack)sfx("sfx_glass");if(before<split&&t>=split)sfx("sfx_break");
  if(t>=finish-.25f){scrumFormation(0);placeCamera(cameraAngle);} /* 검은 화면이 걷히기 전에 법정으로 되돌린다(걷힌 첫 장면에 스크럼 방이 비침) */
 }else if(modeEndKindV4=="climax"){
  const float hold=3.8f,complete=hold+.35f;
  fractureControl(t<hold-.15f?"off":t<complete?"capture":t<complete+1.2f?"animate":"off",t-complete);
  if(t<hold)endingSourceFrame("climax",std::min(77,int(t*60)));
  else endingSourceFrame("crack",t<complete?int((t-hold)*60):-1);
  endingSourceFrame("complete",t>=complete&&t<complete+64.f/60.f?int((t-complete)*60):-1,24);
  endingSourceBlack(t>=complete?1.f:0.f);finish=complete+2.f;
  if(before<hold&&t>=hold)sfx("sfx_glass");if(before<complete&&t>=complete)sfx("sfx_break");
 }else if(modeEndKindV4=="reasoning"){
  const float begin=2.8f,end=begin+armingfinish::frames.size()/60.f,crack=end+.25f,complete=crack+.35f;
  fractureControl(t<crack-.15f?"off":t<complete?"capture":t<complete+1.2f?"animate":"off",t-complete);
  if(t>=complete)UI::SetVisible(this,"stage","root",false);
  if(t>=begin&&t<end)solutionCutinFrame(int((t-begin)*60));
  else{solutionCutinFrame(-1);endingSourceFrame("crack",t>=crack&&t<complete?int((t-crack)*60):-1);}
  endingSourceFrame("complete",t>=complete&&t<complete+64.f/60.f?int((t-complete)*60):-1,24);
  endingSourceBlack(t>=complete?1.f:0.f);finish=complete+1.9f;
  if(before<begin&&t>=begin)sfx("v3se_327");if(before<crack&&t>=crack)sfx("sfx_glass");if(before<complete&&t>=complete)sfx("sfx_break");
 }
 if(t>=finish){
  const auto kind=modeEndKindV4,after=modeEndAfterV4,next=modeEndNextV4;modeEndTimeV4=-1;
  solutionCutinFrame(-1);endingSourceClear();if(kind=="scrum"){scrumFormation(0);placeCamera(cameraAngle);}
  if(after=="task-route")v4TaskRoute();else if(after=="story-node"){if(!storyv4::jump(v4,next))throw std::runtime_error(v4.blocked);v4Enter();}else beginScript();
 }
 return true;
}
