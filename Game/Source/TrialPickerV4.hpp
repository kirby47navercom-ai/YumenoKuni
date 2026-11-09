#include "PadWrapV4.hpp"
// Standalone nomination/evidence selectors; authored WRD-equivalent task callbacks own correctness.
void Yumeno::trialPickerClear(){if(trialPickerOn)if(auto* ring=actor("CulpritWorldOrbit"))Components::Set(ring,"SpriteRenderer","visible",false);trialPickerOn=false;trialPickerPending=-1;trialPickerStamp.clear();UI::Remove(this,"trialpickerv4");trialPickerShown=false;}
void Yumeno::trialPickerStart(const std::string& question){
 if(!UI::Mounted("trialpickerv4"))UI::Show(this,"Assets/UI/TrialPickerV4.hbwidget.json","trialpickerv4");trialPickerShown=true;
 trialinputmotion::resetQuestion(this);trialPickerOn=true;trialPickerQuestion=false;trialPickerFirst=trialPickerImage=trialPickerImages=0;trialPickerPending=-1;trialPickerTicks=trialPickerMarquee=0;trialPickerPrompt=question;trialPickerStamp.clear();optRects.assign(opts.size(),{-10000,-10000,0,0});
 pickerCameraFrom=cam;culpritDirection=0;
 trialInputClock.digits.clear();
 if(stageKind!="bullet"){
  const std::string base=stage.value("selectionRole",std::string())=="culprit"?"Assets/Art/ui/v3/trial_picker/culprit_":"Assets/Art/ui/v3/trial_picker/";
  for(const auto& [id,file]:std::array<std::pair<const char*,const char*>,5>{{{"PkShade","person_back.svg"},{"PkTitleArt","title.svg"},{"PkSeat","seat.svg"},{"PkLeft","arrow_left.svg"},{"PkRight","arrow_right.svg"}}})
   UI::SetTexture(this,"trialpickerv4",id,base+file);
 }
 for(auto id:{"PkEvidenceImage","PkEvidenceFrame"})UI::SetOpacity(this,"trialpickerv4",id,1);
 for(size_t i=1;i<trialPickerPrompt.size();++i){
  const auto next=static_cast<unsigned char>(trialPickerPrompt[i]);
  if(next>=0xea&&next<=0xed&&std::string_view(".?!").find(trialPickerPrompt[i-1])!=std::string_view::npos)
   trialPickerPrompt.insert(i++,1,' ');
 }
 float advance=0;
 for(const auto& glyph:debate::glyphs(trialPickerPrompt))advance+=glyphmetrics::advance(glyph,"pretendard/Pretendard-Medium.otf");
 UI::SetText(this,"trialpickerv4","PkQuestion",trialPickerPrompt);
 UI::SetFontSize(this,"trialpickerv4","PkQuestion",std::min(20.f,725/std::max(1.f,advance)));
 if(stageKind=="bullet")trialinputmotion::show(this,"bullet",trialInputClock);
 UI::SetVisible(this,"trialpickerv4","root",true);UI::SetVisible(this,UI_ID,"Aim",false);UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);trialPickerDraw();
}
void Yumeno::trialPickerCamera(){
 if(!trialPickerOn||stageKind=="bullet"||optHover>=int(personIds.size()))return;
 int seat=court::seatOf(personIds[optHover]);if(seat<0)return;
 const bool culprit=stage.value("selectionRole",std::string())=="culprit";
 const bool confirmed=trialPickerPending>=0;
 auto c=court::frame(court::seatAngle(seat),culprit?(confirmed?0.f:7.f):0.f,confirmed?(culprit?1.65f:1.95f):2.15f,1.86f,culprit&&confirmed?4.f:0.f,culprit?(confirmed?0.f:-7.f):0.f);
 c.yaw-=culprit&&confirmed?0.f:13.f;
 if(culprit){
  const float t=court::smooth5(confirmed?(trialPickerTicks-6.f)/24.f:trialPickerTicks/16.f);
  const auto& from=pickerCameraFrom;
  const auto blend=[t](float a,float b){return a+(b-a)*t;};
  const float a=std::atan2(from.x,from.z)*180.f/court::PI,b=std::atan2(c.x,c.z)*180.f/court::PI;
  const float angle=court::turn(a,b,t)*court::PI/180.f,r=blend(std::hypot(from.x,from.z),std::hypot(c.x,c.z));
  c={r*std::sin(angle),blend(from.y,c.y),r*std::cos(angle),court::turn(from.yaw,c.yaw,t),blend(from.pitch,c.pitch),blend(from.roll,c.roll)};
  if(!confirmed&&culpritDirection){
   const float bank=std::sin(court::PI*t)*culpritDirection;
   c.roll+=bank*4.f;c.yaw+=bank*5.f;
  }
 }
 setCam(c);
 UI::SetVisible(this,UI_ID,"Whip",false);UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
}
void Yumeno::trialPickerDraw(){
 if(!trialPickerOn||opts.empty())return;bool person=stageKind!="bullet";int selected=person?court::seatOf(personIds[optHover]):-1;
 auto label=flowchoice::window(opts[optHover],trialPickerMarquee,person?360.f:355.f);
 std::string stamp=std::to_string(optHover)+":"+std::to_string(trialPickerFirst)+":"+std::to_string(trialPickerPending)+":"+std::to_string(trialPickerImage)+":"+std::to_string(trialPickerQuestion)+":"+std::to_string(label.second);if(stamp==trialPickerStamp)return;trialPickerStamp=stamp;
 auto vis=[&](const std::string& id,bool on){UI::SetVisible(this,"trialpickerv4",id,on);};auto text=[&](const std::string& id,const std::string& value){UI::SetText(this,"trialpickerv4",id,value);};
 const bool culprit=person&&stage.value("selectionRole",std::string())=="culprit";
 vis("CulpritNumber",culprit&&optHover<16);
 if(culprit&&optHover<16){
  UI::SetTexture(this,"trialpickerv4","PkSeat","Assets/Art/ui/v3/trial_inputs_motion/culprit_seat_plate.png");
  UI::SetTexture(this,"trialpickerv4","CulpritNumber","Assets/Art/ui/v3/trial_inputs_motion/culprit_number_"+std::to_string(optHover)+".png");
  UI::SetFont(this,"trialpickerv4","PkName","Assets/Fonts/dokdo/Dokdo-Regular.ttf");
  UI::SetFontSize(this,"trialpickerv4","PkName",42.f);
 }
 vis("PkShade",person);vis("PkTitleArt",person);vis("PkTitle",person);if(person)UI::SetTexture(this,"trialpickerv4","PkTitle",Data::Get("Assets/Data/v4_story/trial_picker_layout.json").at("titles").at(culprit?"culprit":"person").get<std::string>());vis("PkSeat",person);vis("PkSelected",person&&selected>=0);if(person&&selected>=0)UI::SetTexture(this,"trialpickerv4","PkSelected",std::string("Assets/Art/ui/v3/trial_picker/")+(culprit?"culprit_":"")+"seat_"+std::to_string(selected)+".svg");
 for(int i=0;i<16;i++)vis("PkDead"+std::to_string(i),person&&std::find(trialDead.begin(),trialDead.end(),court::SEATS[i])!=trialDead.end());
 vis("PkLeft",person);vis("PkRight",person);vis("PkName",person);if(person)text("PkName",label.first);
 if(culprit){
  auto name=opts[optHover];const std::string memorial=" (영정)";
  if(name.size()>=memorial.size()&&name.compare(name.size()-memorial.size(),memorial.size(),memorial)==0)name.resize(name.size()-memorial.size());
  float advance=0;
  for(const auto& glyph:debate::glyphs(name))advance+=glyphmetrics::advance(glyph,"dokdo/Dokdo-Regular.ttf");
  UI::SetFontSize(this,"trialpickerv4","PkName",std::min(42.f,320.f/std::max(1.f,advance)));
  text("PkName",name);
 }
 bool photo=false;if(person&&stage.contains("candidateOverrides")&&stage["candidateOverrides"].contains(personIds[optHover])){auto row=stage["candidateOverrides"][personIds[optHover]];auto image=row.value("image",std::string());photo=!image.empty();if(photo)UI::SetTexture(this,"trialpickerv4","PkPhoto",image);auto caption=row.value("caption",std::string());if(!culprit&&!caption.empty())text("PkName",flowchoice::window(opts[optHover]+" · "+caption,trialPickerMarquee,360).first);}vis("PkPhoto",photo);
 vis("PkEvidenceBack",!person);vis("bullet_cylinder",!person);vis("bullet_scroll",!person);vis("PkCount",false);vis("PkEvidenceTitle",!person);vis("PkBodyScroll",!person);vis("PkEvidenceImage",false);vis("PkEvidenceFrame",false);vis("PkEvidencePage",false);
 optRects.assign(opts.size(),{-10000,-10000,0,0});
 for(int row=0;row<9;row++){
  int index=trialPickerFirst+row;bool on=!person&&index<int(opts.size());auto n=std::to_string(row);vis("PkRow"+n,on);vis("PkText"+n,on);if(!on)continue;
  bool chosen=index==optHover;UI::SetColor(this,"trialpickerv4","PkText"+n,chosen?Color{0,0,0,1}:Color{1,1,1,1});float x=62+(chosen?26.666667f:0),y=140+row*50.666667f;optRects[index]={x,y,446.666667f,40};
  UI::SetPosition(this,"trialpickerv4","PkRow"+n,{x,y});UI::SetPosition(this,"trialpickerv4","PkText"+n,{x+34,y+2});UI::SetTexture(this,"trialpickerv4","PkRow"+n,std::string("Assets/Art/ui/v3/trial_picker/bullet_")+(chosen?"on":"off")+".svg");text("PkText"+n,chosen?label.first:flowchoice::window(opts[index],0,355).first);
 }
 if(!person&&optHover<int(bladeIds.size())){
  auto id=bladeIds[optHover];text("PkCount",std::to_string(optHover+1)+" / "+std::to_string(opts.size()));text("PkEvidenceTitle",flowchoice::window(kotodamaName(id),trialPickerMarquee,570).first);auto description=padsystem::wrap(kotodamaText(id),580,"Assets/Fonts/pretendard/Pretendard-Regular.otf",22);text("PkEvidenceBody",description.first);
  UI::SetSize(this,"trialpickerv4","PkEvidenceBody",{600,std::max(200.f,description.second*29.f)});
  static const auto map=Data::Get("Assets/Data/v4_story/evidence_art.json");auto images=map.value("items",Json::object()).value(id,Json::array());trialPickerImages=int(images.size());if(trialPickerImages){trialPickerImage=(trialPickerImage+trialPickerImages)%trialPickerImages;vis("PkEvidenceImage",true);vis("PkEvidenceFrame",true);UI::SetTexture(this,"trialpickerv4","PkEvidenceImage",images[trialPickerImage].value("image",std::string()));vis("PkEvidencePage",trialPickerImages>1);text("PkEvidencePage",std::to_string(trialPickerImage+1)+" / "+std::to_string(trialPickerImages));}
 }
 vis("PkGuideBack",true);vis("PkGuide",false);vis("PkConfirm",false);
 for(int i=0;i<3;i++){
  const bool visible=trialPickerPending<0&&(i<2||!person);
  vis("PromptIcon"+std::to_string(i),visible);vis("PromptLabel"+std::to_string(i),visible);
 }
}
bool Yumeno::trialPickerInput(float delta,bool click){
 if(!trialPickerOn)return false;bool person=stageKind!="bullet";trialPickerTicks+=delta*60;trialPickerMarquee+=delta;
 trialinputmotion::questionPose(this,false,trialPickerQuestion&&trialPickerPending<0,delta);
 const bool culprit=person&&stage.value("selectionRole",std::string())=="culprit";
 if(person){
  if(auto* ring=actor("CulpritWorldOrbit")){
   const int target=optHover>=0&&optHover<int(personIds.size())?court::seatOf(personIds[optHover]):-1;
   auto* seatActor=target>=0?actor("Seat"+std::to_string(target)):nullptr;
   const bool exit=trialPickerPending>=0;
   const float frame=trialPickerTicks;
   const float opacity=exit?std::max(0.f,1.f-frame/16.f):std::min(1.f,frame/12.f);
   Components::Set(ring,"SpriteRenderer","visible",seatActor&&opacity>0);
   if(seatActor&&opacity>0){
    const auto p=Scene::GetPosition(seatActor);
    Scene::SetPosition(ring,{p.x,p.y*.32f+1.03f,p.z});
    Scene::SetRotation(ring,{-90.f,0.f,std::fmod(trialPickerMarquee*180.f,360.f)});
    Components::SetColor(ring,"SpriteRenderer","color",{1,1,1,opacity});
   }
  }
 }
 if(culprit&&trialinputmotion::bank().contains("culpritMotion")){
  const auto& motion=trialinputmotion::bank().at("culpritMotion");
  const bool exit=trialPickerPending>=0;
  const int frame=int(trialPickerTicks);
  const auto& arrows=motion.at(exit?"exit":culpritDirection<0?"left":culpritDirection>0?"right":"enter");
  const auto& seat=motion.at(exit?"seatOut":"seatIn");
  const float alpha=exit||culpritDirection==0?(frame<int(seat.size())?seat[frame].get<float>():exit?0.f:1.f):1.f;
  const auto& orbit=trialinputmotion::bank().at("culpritOrbit");
  UI::SetVisible(this,"trialpickerv4","CulpritOrbit",false);
  const auto& sweep=orbit.at("sweep");
  const bool sweeping=!exit&&culpritDirection!=0&&frame<int(sweep.size());
  UI::SetVisible(this,"trialpickerv4","CulpritSweep",sweeping);
  if(sweeping){
   auto texture=sweep[frame].get<std::string>();
   if(culpritDirection<0)texture.insert(texture.size()-4,"_left");
   UI::SetTexture(this,"trialpickerv4","CulpritSweep",texture);
  }
  for(auto id:{"PkShade","PkTitleArt","PkTitle","PkSeat","PkSelected","PkName","PkPhoto","CulpritNumber"})
   UI::SetOpacity(this,"trialpickerv4",id,alpha);
  for(int i=0;i<16;i++)UI::SetOpacity(this,"trialpickerv4","PkDead"+std::to_string(i),alpha);
  for(int i=0;i<2;i++){
   const auto id=i?"PkRight":"PkLeft";
   const bool moving=frame<int(arrows.size())&&i<int(arrows[frame].size());
   UI::SetOpacity(this,"trialpickerv4",id,moving?arrows[frame][i][2].get<float>():exit||frame<int(arrows.size())?0.f:1.f);
   UI::SetPosition(this,"trialpickerv4",id,moving?hb::Vec2{arrows[frame][i][0],arrows[frame][i][1]}:hb::Vec2{i?598.666667f:53.333333f,i?470.666667f:240.f});
  }
  for(int i=0;i<9;i++)UI::SetVisible(this,"trialpickerv4","CulpritClock"+std::to_string(i),!exit);
  if(!exit&&culpritDirection==0&&frame<int(arrows.size()))return true;
 }
 if(trialPickerPending>=0){
  int duration=person?120:12;
  if(culprit&&trialPickerTicks>=16.f)endingSourceFrame("nominate",int(trialPickerTicks)-16);
  else if(!culprit&&person&&trialinputmotion::bank().contains("personConfirm")){
   const auto& frames=trialinputmotion::bank().at("personConfirm");
   const int frame=int(trialPickerTicks);
   for(int i=0;i<4;i++){
    const auto id="PersonConfirm"+std::to_string(i);
    const bool visible=frame<int(frames.size())&&i<int(frames[frame].size());
    UI::SetVisible(this,"trialpickerv4",id,visible);if(!visible)continue;
    const auto& r=frames[frame][i];
    UI::SetTexture(this,"trialpickerv4",id,r[0].get<std::string>());
    UI::SetPosition(this,"trialpickerv4",id,{r[1],r[2]});UI::SetSize(this,"trialpickerv4",id,{r[3],r[4]});
    UI::SetRotation(this,"trialpickerv4",id,r[5]);UI::SetOpacity(this,"trialpickerv4",id,r[6]);
   }
  }
  else if(!person&&trialinputmotion::bank().contains("evidenceExit")){
   const auto& frames=trialinputmotion::bank().at("evidenceExit");
   duration=int(frames.size());
   const auto& frame=frames[std::min(int(trialPickerTicks),duration-1)];
   UI::SetOpacity(this,"trialpickerv4","PkEvidenceImage",frame[0]);
   UI::SetOpacity(this,"trialpickerv4","PkEvidenceFrame",frame[1]);
  }
  if(trialPickerTicks>=duration){
   endingSourceClear();int i=trialPickerPending;trialPickerPending=-1;trialPickerTicks=0;trialPickerStamp.clear();trialPickerDraw();optionPicked(i);
  }
  return true;
 }
 // Authored optional timeout and health take precedence over a simultaneous confirm.
 float duration=stage.value("duration",!person||culprit?60.f:0.f)*trialTimeFactor();
 if(duration>0){stageTime+=delta;if(stageTime>=duration){if(culprit)sfx("v3se_332");hurt();restartStage=true;return true;}}
 if(culprit){
  const auto digits=trialinputmotion::digits(std::max(0.f,duration-stageTime));
  const auto& textures=trialinputmotion::bank().at("clocks").at("bullet").at("digits");
  for(int i=0;i<9;i++)if(trialInputClock.digits.size()!=9||trialInputClock.digits[i]!=digits[i])
   UI::SetTexture(this,"trialpickerv4","CulpritClock"+std::to_string(i),textures.at(std::to_string(digits[i]-'0')).get<std::string>());
  trialInputClock.digits=digits;
 }
 if(!person)trialinputmotion::clock(this,"bullet",std::max(0.f,duration-stageTime),duration,trialInputClock);
 if(debate.hearts<=0){restartStage=true;return true;}
 int before=optHover,count=int(opts.size());if(count==0)return true;
 bool wheelSelect=!person&&aimX<550&&std::abs(mouseWheelV4)>.001f;
 if(wheelSelect){int steps=std::clamp(int(std::round(std::abs(mouseWheelV4))),1,9);optHover=(optHover+count+(mouseWheelV4>0?-steps:steps))%count;}
 if(pressed(person?"a":"w")||pressed(person?"ArrowLeft":"ArrowUp"))optHover=(optHover+count-1)%count;
 if(pressed(person?"d":"s")||pressed(person?"ArrowRight":"ArrowDown"))optHover=(optHover+1)%count;
 if(pressed("f")||pressed("q")){trialPickerQuestion=!trialPickerQuestion;trialPickerStamp.clear();sfx("ui_select");}
 bool submit=pressed("Enter");if(person&&click){if(aimX>=53&&aimX<=256&&aimY>=240&&aimY<=311)optHover=(optHover+count-1)%count;else if(aimX>=598&&aimX<=802&&aimY>=470&&aimY<=542)optHover=(optHover+1)%count;else if(aimX>=256&&aimX<598&&aimY>=90&&aimY<620)submit=true;}
 if(!person){int hit=optionAt(aimX,aimY);bool moved=std::abs(aimX-optionMouseX)>.5f||std::abs(aimY-optionMouseY)>.5f;if(!wheelSelect&&(moved||click)&&hit>=0)optHover=hit;if(click&&hit>=0)submit=true;if(trialPickerImages>1&&(pressed("a")||pressed("d"))){trialPickerImage=(trialPickerImage+trialPickerImages+(pressed("d")?1:-1))%trialPickerImages;trialPickerStamp.clear();}}
 optionMouseX=aimX;optionMouseY=aimY;
 if(culprit&&(before!=optHover||submit)){
  pickerCameraFrom=cam;trialPickerTicks=0;
  if(before!=optHover)culpritDirection=(optHover+count-before)%count==1?1:-1;
 }
 if(before!=optHover){trialPickerMarquee=0;trialPickerImage=0;if(optHover<trialPickerFirst)trialPickerFirst=optHover;if(optHover>=trialPickerFirst+9)trialPickerFirst=optHover-8;sfx(stageKind=="vote"?"v3se_367":"v3se_005");} // V3 투표 커서 SE367, 인물·언령 커서 SE005
 if(submit){trialPickerQuestion=false;trialPickerPending=optHover;trialPickerTicks=0;if(stageKind=="vote")sfx("v3se_368");else if(person)sfx("v3se_305");else pv4::Action(presentationV4,"ui_confirm");} /* V3 투표 결정 SE368, 인물 결정 SE305(3c44c0) */trialPickerDraw();return true;
}
std::string Yumeno::TrialPickerStats()const{
 Json visible=Json::array();if(stageKind=="bullet")for(int i=trialPickerFirst;i<std::min(int(bladeIds.size()),trialPickerFirst+9);i++)visible.push_back(bladeIds[i]);return Json{{"visible",trialPickerOn},{"kind",stageKind},{"count",opts.size()},{"hover",optHover},{"first",trialPickerFirst},{"pending",trialPickerPending},{"ticks",trialPickerTicks},{"question",trialPickerQuestion},{"image",trialPickerImage},{"images",trialPickerImages},{"logicalId",stageKind=="bullet"&&optHover<int(bladeIds.size())?bladeIds[optHover]:optHover<int(personIds.size())?personIds[optHover]:std::string()},{"visibleEvidence",visible}}.dump();
}
