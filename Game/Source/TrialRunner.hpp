#pragma once
#include "SpotLayoutV4.hpp"
#include "ArmamentIntroSourceV4.hpp"
// 학급 재판 단계 실행기 (docs/spec/15 §4, 대본 docs/design/1Nc). Yumeno.cpp 끝에서 한 번 포함한다.
// 단계 : 대사(개정·장면·인터럽트·휴정) / 논의(논스톱·패닉 → Debate.hpp) / 선택형(객관식·언령·지점·인물·투표)
//        / 클라이맥스 / 반론 쇼다운 / 논의 스크럼 / 이론 무장 / 섬광 애너그램 / 발굴 이매지네이션 / 브레인 드라이브
// 위젯 좌표는 tools/create-project.mjs 의 W_Stage 와 같다.

namespace trialui {
const char* ID="stage";
inline const char* armInkRole(const std::string& id){return id=="ArmQuestion"?"question":id=="ArmJoined"?"joined":id.size()==6&&id.rfind("Piece",0)==0&&id[5]>='0'&&id[5]<='3'?"piece":nullptr;}
inline const hb::Json& armInkBank(bool revised){
 if(revised){static const auto ink=hb::Data::Get("Assets/Data/armament_text_revision.json");return ink;}
 static const auto ink=hb::Data::Get("Assets/Data/armament_text_v4.json");return ink;
}
constexpr float OPT_X=290,OPT_W=700;
// t_riron_todome_* fl_wait plate bounds, design1920 ->1280. Top/right/bottom/left.
const float PIECE_LEFT[4]{485.6667f,852.9333f,485.6667f,111.6667f},PIECE_TOP[4]{116.6667f,335.f,552.6667f,334.6667f};
const float PIECE_X[4]{640,1007.267f,640,266},PIECE_Y[4]{144.6667f,363.f,580.6667f,362.6667f};
constexpr float CELL_X=270,CELL_Y=180,CELL_W=37,CELL_H=420.f/11;constexpr int COLS=20,ROWS=11;
constexpr float BLADE_Y=300;
const char* const DECOYS[]{"가","나","다","라","마","바","사","아","자","차","카","타","파","하","소","문","기","록"};
const char* const MINE_TILES[4]{"Assets/Art/ui/mine_w.svg","Assets/Art/ui/mine_p.svg","Assets/Art/ui/mine_y.svg","Assets/Art/ui/mine_b.svg"};
inline const char* widget(const std::string& id){return id.rfind("MineQuestion",0)==0||id.rfind("MineClock",0)==0||id.rfind("MineEntry",0)==0||id.rfind("MineBurst",0)==0||id=="MineMouseHint"||id=="MineOpeningTitle"||id=="MineCursor"||id=="MineToggle"?"minehudv4":id.rfind("PanicFig",0)==0||id.rfind("PanicFrame",0)==0||id.rfind("PanicName",0)==0?"panes":id.rfind("Cell",0)==0||id.rfind("MineHint",0)==0?"minev4":id.rfind("ScV",0)==0||id=="ScBand"?"scrumv4":id.rfind("Ana",0)==0||id.rfind("Orb",0)==0?"anagramv4":ID;}
inline float anaStep(int count){return std::min(50.f,850.f/std::max(1,count));}
inline char16_t unit(const std::string& s){if(s.empty())return 0;auto c=(unsigned char)s[0];if(c<128)return c;if(s.size()>=3&&c>=224)return char16_t(((c&15)<<12)|(((unsigned char)s[1]&63)<<6)|((unsigned char)s[2]&63));if(s.size()>=2)return char16_t(((c&31)<<6)|((unsigned char)s[1]&63));return 0;}
inline std::string glyph(char16_t c){std::string s;if(c<128)s+=char(c);else if(c<2048){s+=char(192|(c>>6));s+=char(128|(c&63));}else{s+=char(224|(c>>12));s+=char(128|((c>>6)&63));s+=char(128|(c&63));}return s;}
inline void armNote(trialv4::Arming& state,const hb::Json& stage,int index,int line=0){
 state.current=trialv4::Note{};state.current.button=index%4;state.holdSeconds=0;hb::Json notes=hb::Json::array();
 if(stage.contains("rhythm_waves")&&stage.contains("waveIndexByLine")&&line<int(stage["waveIndexByLine"].size())){
  int wave=stage["waveIndexByLine"][line];notes=stage["rhythm_waves"].at(wave).at("notes");
 }else if(stage.contains("rhythm_notes"))notes=stage["rhythm_notes"];
 if(!notes.empty()){
  auto& note=notes[index%notes.size()];state.current.button=std::clamp(note.value("button",0),0,3);auto type=note.value("type","tap");state.current.type=type=="hold"?trialv4::NoteType::Hold:type=="mash"?trialv4::NoteType::Mash:trialv4::NoteType::Tap;
  state.current.targetSeconds=std::clamp(note.value("targetSeconds",.9f),.5f,3.f);state.current.holdFrames=std::clamp(note.value("holdFrames",60),12,180);
 }else if(stage.value("v4",false))state.current.type=index%8==3?trialv4::NoteType::Hold:index%8==7?trialv4::NoteType::Mash:trialv4::NoteType::Tap;
}

}

#include "TrialAnswerChoiceV4.hpp"
#include "TrialPickerV4.hpp"
#include "PadWrapV4.hpp"
// ── 스킬 (00 §6, data/skills.json) : 인연 Lv 으로 익히고 SP(6 + 장마다 2, 최대 16) 안에서 표 순서대로 장착 ──
std::vector<hb::Json> Yumeno::equippedSkills()const{
 if(v4.active)return growthv4::Equipped(growthV4);
 std::vector<hb::Json> out;int sp=std::min(16,6+2*std::max(0,chapterAt-1)),used=0;
 if(skillData.contains("items"))for(auto& s:skillData["items"]){if(s.contains("sourceLabel")||level(s.value("who",""))<s.value("level",9))continue;int c=s.value("sp",2);if(used+c>sp)continue;used+=c;out.push_back(s);}
 return out;
}
bool Yumeno::skillOn(const std::string& effect)const{if(v4.active)return growthv4::Effect(growthV4,effect);for(auto& s:equippedSkills())if(s.value("effect","")==effect)return true;return false;}
void Yumeno::onCorrect(){
 ++correctCount;
 if((skillOn("heal_every_2")&&correctCount%2==0)||(skillOn("heal_every_3")&&correctCount%3==0)){
  if(v4TaskActive){if(v4TrialHp<maxHearts*2000){v4TrialHp=std::min(maxHearts*2000,v4TrialHp+2000);debate.hearts=(v4TrialHp+1999)/2000;message("회복!",.6f);}}
  else if(debate.hearts<maxHearts){debate.hearts++;message("회복!",.6f);}
 }
}
float Yumeno::maximumFocus()const{return v4.active?growthv4::MaximumMental(growthV4)/100.f:100.f;}
float Yumeno::trialTimeFactor()const{return (skillOn("ponder")?1.2f:1.f)*(skillOn("time_pct_5")?1.05f:1.f);}
bool Yumeno::skillFocusTick(bool held,float delta){
 skillMentalTicks+=std::max(0.f,delta)*60;int frames=int(skillMentalTicks);skillMentalTicks-=frames;int mental=int(std::round(debate.focus*100)),hp=v4TaskHp();
 if(!held)focusExhausted=false;bool request=held&&!focusExhausted;if(request&&mental<=0){focusExhausted=true;request=false;}bool depleted=false;bool focused=growthv4::MentalStep(growthV4,mental,hp,request,frames,&depleted);if(depleted)focusExhausted=true;debate.focus=mental/100.f;
 if(v4TaskActive&&hp!=v4TaskHp()){v4TrialHp=hp;if(stageKind=="showdown")showdownV4.hp=hp;else if(stageKind=="scrum")scrumHpV4=hp;else{v4TaskEntryHp=hp;debate.hearts=v4TaskEntryHearts=(hp+1999)/2000;}}
 return focused;
}
// ── 위젯 도우미 ──────────────────────────────────────────────
void Yumeno::stext(const std::string& id,const std::string& v){auto& c=stexts[id];if(c==v&&!c.empty())return;c=v;UI::SetText(this,trialui::widget(id),id,v);if(const auto* role=trialui::armInkRole(id);role&&v4TaskActive&&stageKind=="armament"){const auto& bank=trialui::armInkBank(stage.value("phaseTranscripts",false));if(!v.empty()){const auto texture=bank.at("final").at(role).at(v).at("texture").get<std::string>();UI::SetTexture(this,trialui::ID,id+"Ink",texture);}UI::SetVisible(this,trialui::ID,id,false);UI::SetVisible(this,trialui::ID,id+"Ink",!v.empty()&&svisible[id]);}}
void Yumeno::svis(const std::string& id,bool v){auto it=svisible.find(id);if(it!=svisible.end()&&it->second==v)return;svisible[id]=v;if(trialui::armInkRole(id)){bool ink=v4TaskActive&&stageKind=="armament";UI::SetVisible(this,trialui::ID,id+"Ink",v&&ink&&!stexts[id].empty());if(ink)v=false;}bool intro=id.rfind("Intro",0)==0;UI::SetVisible(intro?actor("IntroOwner"):this,intro?"intro":trialui::widget(id),id,v);}
void Yumeno::sclear(){
 solutionCutinFrame(-1);armamentVisualHide();endingSourceClear();
 trialAnswerOn=false;trialPickerClear();hideVote();trialinputmotion::clear(this);for(auto& [id,v]:svisible)if(v){svis(id,false);v=false;}
 if(stageShown){
  UI::SetPosition(this,trialui::ID,"QPlate",{140,24});UI::SetSize(this,trialui::ID,"QPlate",{760,80});
  UI::SetPosition(this,trialui::ID,"Question",{180,28});UI::SetSize(this,trialui::ID,"Question",{680,72});UI::SetFontSize(this,trialui::ID,"Question",28);
  UI::SetPosition(this,trialui::ID,"Hint",{900,560});UI::SetSize(this,trialui::ID,"Hint",{360,30});UI::SetFontSize(this,trialui::ID,"Hint",18);
 }
}
void Yumeno::smsg(const std::string& v,float seconds){stext("StageMsg",v);svis("StageMsg",true);stageMsgTimer=seconds;}
void Yumeno::armHudDraw(){
 static const char* names[]{"Hp","Mental","Boss"};
 std::array<float,3> values{{float(armingV4.hp)/std::max(1,armingV4.maxHp),debate.focus/maximumFocus(),float(armingV4.opponent)/std::max(1,armingV4.totalOpponent)}};
 for(int i=0;i<3;i++){auto id=std::string("ArmHud")+names[i];svis(id+"Track",true);svis(id,true);int percent=std::clamp(int(std::round(values[i]*100)),0,100);if(percent!=armHudShown[i]){armHudShown[i]=percent;UI::SetTexture(this,trialui::ID,id,std::string("Assets/Art/ui/arm_")+names[i]+"_"+std::to_string(percent)+".svg");}}
 int tension=std::clamp(armingV4.tension,0,20);if(tension!=armHudTension){armHudTension=tension;for(int i=0;i<20;i++){auto id="ArmHudTension"+std::to_string(i);if(v4TaskActive&&!armStreamBank.is_null()){auto key="tension_"+std::to_string(tension)+"_"+std::to_string(i);if(armStreamBank["textures"].contains(key))UI::SetTexture(this,trialui::ID,id,armStreamBank["textures"][key].get<std::string>());}svis(id,(i%2==1&&i<tension)||(tension%2==1&&i==tension-1));}}
}
void Yumeno::armNoteDraw(){
 if(v4TaskActive&&!armStreamBank.is_null()){armamentSites();return;}
 static const auto layout=Data::Get("Assets/Data/presentation/v3_armament_layout.json");const auto& points=layout.at("tracks").at(std::to_string(std::clamp(chapterAt,1,6)));const auto& point=points[armHits%points.size()];float x=point[0].get<float>()*(2.f/3),y=point[1].get<float>()*(2.f/3);
 UI::SetPosition(this,trialui::ID,"Ring",{x-29.8667f,y-29.8667f});UI::SetSize(this,trialui::ID,"Ring",{59.7333f,59.7333f});
 UI::SetPosition(this,trialui::ID,"RingCore",{x-29.8667f,y-29.8667f});UI::SetSize(this,trialui::ID,"RingCore",{59.7333f,59.7333f});
 UI::SetPosition(this,trialui::ID,"ArmNoteKey",{x-29.8667f,y-20.8f});svis("ArmNoteKey",true);static const char* keys[]{"W","D","S","A"};stext("ArmNoteKey",keys[armingV4.current.button]);
 UI::SetPosition(this,trialui::ID,"ArmNoteType",{x-60,y+34});stext("ArmNoteType",armingV4.current.type==trialv4::NoteType::Hold?"길게":armingV4.current.type==trialv4::NoteType::Mash?"연타":"");svis("ArmNoteType",armingV4.current.type!=trialv4::NoteType::Tap);
 // The complete own-language claim stays attached to this note; exact source font projection is separate.
 const auto& value=stage["lines"][armLine].get<std::string>();float left=std::clamp(x-320.f,12.f,628.f),top=std::max(8.f,y-140);
 if(v4TaskActive){const auto& bank=trialui::armInkBank(stage.value("phaseTranscripts",false));const auto& ink=bank.at("items").at(value);auto texture=ink.at("texture").get<std::string>();if(stexts["ArmLineInkTexture"]!=texture){UI::SetTexture(this,trialui::ID,"ArmLineInk",texture);stexts["ArmLineInkTexture"]=texture;}UI::SetPosition(this,trialui::ID,"ArmLineInk",{left,top});UI::SetSize(this,trialui::ID,"ArmLineInk",{640,112});svis("ArmLine",false);svis("ArmLineInk",true);}
 else{UI::SetPosition(this,trialui::ID,"ArmLine",{left,top});UI::SetSize(this,trialui::ID,"ArmLine",{640,112});stext("ArmLine",value);}svis("Hint",false);
}
std::string Yumeno::nameOf(const std::string& slug)const{for(auto& [k,v]:slugs)if(v==slug)return k;return slug;}

// 디버그 HUD : 논의 전용 요소만 끄고 발언력·집중은 계속 보인다
// 거짓 탄환을 누르고 있는 화면(V3 LP Ch1 「Nonstop Debate Lie」) : 인물은 흰 실루엣, 배경은 보랏빛으로 가라앉는다(tools/court_silhouettes.py)
void Yumeno::lieView(bool on){
 if(on==lieViewOn)return;lieViewOn=on;
 for(int i=0;i<16;i++){auto front=seatTexture[i];if(front.empty())continue;auto at=front.find("court_figures/");if(at==std::string::npos)continue;
  auto sil=front;sil.replace(at,14,"court_figures_sil/"); /* 같은 이름(.webp — optimize_assets 가 png 를 webp 로 바꾼다) */
  if(auto* a=actor("Seat"+std::to_string(i)))Components::SetString(a,"SpriteRenderer","texture",on?sil:front);
  if(auto* b=actor("SeatRear"+std::to_string(i)))Components::SetString(b,"SpriteRenderer","texture",on?sil:front.substr(0,front.size()-5)+"_back.webp");}
 lastDebateWashStep=16;UI::SetOpacity(this,UI_ID,"CourtDim",1.f);
 UI::SetTexture(this,UI_ID,"CourtDim",on?"Assets/Art/ui/lie_wash.svg":lastDebateWash.empty()?"Assets/Art/ui/gpu_trial/court_dim.svg":lastDebateWash);
}
void Yumeno::debateHud(bool on){
 const bool sourceHud=v4TaskActive&&(stageKind=="nonstop"||debate.panic());
 if(!on){
  if(UI::Mounted("panes"))svis("PanicFrame0",false);
  if(debate.panic())UI::SetTexture(this,UI_ID,"CourtDim","Assets/Art/ui/gpu_trial/court_dim.svg");
  lieView(false);
  if(!lastDebateWash.empty()){UI::SetTexture(this,UI_ID,"CourtDim","Assets/Art/ui/gpu_trial/court_dim.svg");UI::SetOpacity(this,UI_ID,"CourtDim",1.f);lastDebateWash.clear();lastDebateWashStep=16;}
 }
 if(v4TaskActive){bool noise=std::any_of(debate.lines.begin(),debate.lines.end(),[](const auto& l){return l.kind=="noise";});if(on){UI::SetPosition(this,trialui::ID,"Hint",{900,550});UI::SetSize(this,trialui::ID,"Hint",{360,90});UI::SetFontSize(this,trialui::ID,"Hint",16);stext("Hint",std::string("방향키 조준 · 클릭 탄환\nQ/E 증거 · Shift 집중")+(noise?(skillOn("grenade")?"\n우클릭 유지/놓기 소음":"\n우클릭 소음"):"")+(noise&&skillOn("zero_distance_shooting")?" · R 소음 제거":""));}svis("Hint",false);} // V3 논의 화면에는 조작 안내 글자가 없다(사양서 19 §12)
 for(int k=0;k<20;k++)UI::SetVisible(this,"trialvitalsv4","Heart"+std::to_string(k),on&&k<maxHearts*2);
 UI::SetVisible(this,UI_ID,"Aim",on);
 // V3 Dk_JjYZEzdg02:42: one active name at upper left, not a label per pane.
 for(auto id:{"NamePanel","TrialSpeaker"})UI::SetVisible(this,UI_ID,id,on&&!sourceHud&&stageKind!="nonstop");
 if(on&&!debate.panic()){ /* V3 [확인 A 16:43] 기울어진 검은 탭 + 넓은 자간 이름 + 증언 순서 점(사양서 19 §2, tools/hud_name_dots.py) */
  UI::SetPosition(this,UI_ID,"NamePanel",{14,10});UI::SetSize(this,UI_ID,"NamePanel",{360,84});
  UI::SetPosition(this,UI_ID,"TrialSpeaker",{44,18});UI::SetSize(this,UI_ID,"TrialSpeaker",{290,38});
  UI::SetFont(this,UI_ID,"TrialSpeaker","Assets/Fonts/pretendard/Pretendard-Medium.otf");UI::SetFontSize(this,UI_ID,"TrialSpeaker",24); /* V3 : 얇고 넓은 자간 */UI::SetColor(this,UI_ID,"TrialSpeaker",Color{1,1,1,1});}
 for(auto id:{"Cylinder","BulletPlate","Bullet","TimerPanel","Timer","VPoint"})UI::SetVisible(this,UI_ID,id,on&&((!sourceHud&&stageKind!="nonstop")||std::string(id)=="VPoint"));UI::SetVisible(this,UI_ID,"BulletLabel",false); /* 「언령」「Kotodama」 표기 둘 다 뺀다(주인님 지시 2026-11-05) */
 UI::SetVisible(this,UI_ID,"TrialBack",on);
 UI::SetVisible(this,UI_ID,"Lens",on&&!debate.panic()&&stageKind!="showdown"&&stageKind!="nonstop");
 if(!on){UI::SetVisible(this,UI_ID,"StartBand",false);UI::Remove(this,"panicphasestartv4");}
 if(!on){debateSwirl=0;if(debateSwirlOn)if(auto* sw=actor("DebateSwirl")){Components::Set(sw,"SpriteRenderer","visible",false);debateSwirlOn=false;}if(v4TaskActive)v4NoiseReset();UI::SetVisible(this,UI_ID,"VPoint1",false);UI::SetVisible(this,UI_ID,"VPoint2",false);drawGlyphs("M",48,{});drawGlyphs("N",26,{});drawPanicLanes(false);resetDebateFx();}
}
void Yumeno::drawHearts(){
 if(!UI::Mounted("trialvitalsv4"))return; /* 재판 화면을 내린 뒤(완전논파 후 대본)에는 그리지 않는다 */
 const bool visible=debateIntroTime<0&&fracturePhaseV4!="animate"&&mode==Mode::Trial&&!inScript&&!v4QueueActive&&!trialResultOn&&stageKind!="nonstop"&&!(v4TaskActive&&stageKind=="panic")&&stageKind!="anagram"&&stageKind!="armament"&&stageKind!="climax"&&stageKind!="mindmine"&&stageKind!="vote"&&!(stageKind=="scrum"&&(scrumT<1||scv3Op>=0||scv3Team>=0||scv3PushT>=0));
 const bool source=v4TaskActive&&trialinputmotion::usesSourceStatus(stageKind);
 const bool opening=(stageKind=="choice"&&stageTime<0)||(stageKind=="spot"&&stageTime<18.f/60);
 UI::SetVisible(this,"trialvitalsv4","root",visible&&(!source||!opening));
 trialinputmotion::sourceStatus(this,source,maxHearts,v4TaskHp(),debate.focus,maximumFocus());
 if(source)return;
 int parts=v4TaskActive?(v4TaskHp()+999)/1000:debate.hearts*2;if(!inScript&&!playingDebate){if(stageKind=="mindmine")parts=(mineV4.hp+999)/1000;else if(stageKind=="anagram")parts=(anagramV4.hp+999)/1000;else if(stageKind=="scrum")parts=(scrumHpV4+999)/1000;else if(stageKind=="armament")parts=(armingV4.hp+999)/1000;}
 if(shownHearts==parts&&shownHeartMax==maxHearts)return;shownHearts=parts;shownHeartMax=maxHearts;
 float step=maxHearts>6?252.f/(maxHearts*2):21.f;
 for(int k=0;k<20;k++){auto texture=k<parts?"Assets/Art/ui/hud_heartOn.svg":"Assets/Art/ui/hud_heartOff.svg";auto id="Heart"+std::to_string(k);UI::SetTexture(this,"trialvitalsv4",id,texture);UI::SetPosition(this,"trialvitalsv4",id,{990+k*step,56-k*step/15});UI::SetSize(this,"trialvitalsv4",id,{std::min(22.f,step+1),22});
  if(stageKind=="anagram"){auto a="AnaHeart"+std::to_string(k);UI::SetTexture(this,"anagramv4",a,texture);UI::SetPosition(this,"anagramv4",a,{990+k*step,46});UI::SetSize(this,"anagramv4",a,{std::min(22.f,step+1),22});}}
}
// 발언력 : 단계 실패 시 감소, 0이면 그 단계 처음부터(V3 : 같은 지점 재도전 + 점수 감점)
void Yumeno::hurt(){
 if(!v4TaskActive)sfx("v3se_316");
 if(stageKind=="showdown"&&skillOn("showdown_guard")&&!sdGuardUsed){sdGuardUsed=true;smsg("최후의 중재!",1.f);return;}
 if((v4TaskActive?v4Damage(2000):--debate.hearts)<=0&&skillOn("revive")&&!reviveUsed){reviveUsed=true;v4ResetHearts(2);smsg("다시 일어선다!",1.2f);return;}
 if(debate.hearts<=0){v4ResetHearts(maxHearts);retries++;smsg("발언력이 바닥났어요… 다시!",1.6f);restartStage=true;return;}
 if(!v4TaskActive)smsg("아야! 틀렸어요~!",1.f);
}
void Yumeno::heal(){sfx("v3se_310");if(!v4TaskActive){debate.hearts=std::min(maxHearts,debate.hearts+1);onCorrect();}}

// ── 카메라 : 화자 자리로 돌고, 도착하면 화자를 UI 층으로 옮긴다 ─────────────
void Yumeno::focusSpeaker(const std::string& slug,const std::string& texture){
 scrumPortraitSeatV4=-1;
 auto figureKey=texture.substr(texture.find_last_of('/')+1);auto figureDot=figureKey.find_last_of('.');if(figureDot!=std::string::npos)figureKey.resize(figureDot);
 auto resolved=courtFigures.contains(figureKey)?courtFigures[figureKey].value("texture",texture):texture;
 if(slug=="lappy"){ // 래피는 증언대가 아니라 왕좌 : 카메라를 왕좌 쪽으로 돌리고 3D 래피의 그림만 바꾼다
  if(auto* h=actor("Host"))if(!resolved.empty())Components::SetString(h,"SpriteRenderer","texture",resolved=="lappy"?std::string("Assets/Art/v4/lappy.webp"):resolved);
  UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
  if(speakerSeat!=-2){whipFrom=cam;pitchFrom=cameraPitch;speakerSeat=-2;cameraFrom=cameraAngle;cameraTo=180;cameraTime=0;}
  return;
 }
 if(!resolved.empty())UI::SetTexture(this,UI_ID,"Portrait",resolved);
 int seat=court::seatOf(slug);
 if(seat<0)return;
 if(!texture.empty())courtPose(seat,texture);
 courtIdle=false;
 // V3 : 같은 사람이 이어 말하면 각도만 끊어 바꾸고(컷), 다른 사람이면 원을 따라 휙 돈다(휩)
 static const int CUT[]{4,3,5,1,0,2},ARRIVE[]{0,1,2,0,3,1},DEBATE[]{8,6,9,10,11,7};
 bool talk=playingDebate;
 if(seat==speakerSeat&&!(talk&&v4TaskActive&&stageKind=="nonstop")){
  if(cameraTime>=1){shotKind=talk?DEBATE[shotCount++%6]:CUT[shotCount++%6];shotTime=0;}
  return;
 }
 whipFrom=cam;pitchFrom=cameraPitch;speakerSeat=seat;cameraFrom=cameraAngle;cameraTo=court::seatAngle(seat);cameraTime=0;
 shotKind=talk?DEBATE[shotCount++%6]:ARRIVE[shotCount++%6];shotTime=0;
 UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
}
// 화자 입상을 밝은 UI 층으로 겹치는 단계(대사·논의). 쇼다운·스크럼·이론 무장·미니게임은 자기 그림이 있다
bool Yumeno::overlayStage()const{static const std::set<std::string> no{"showdown","scrum","armament","climax","anagram","mindmine","taxi"};return !no.count(stageKind);}
// 고르기 화면(객관식·언령·인물·지점·투표) 뒤 : 재판장 가운데에서 천천히 돌며 모두를 비춘다
void Yumeno::courtWide(){courtIdle=true;speakerSeat=-3;cameraTime=1;UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);}
court::Cam Yumeno::shotCam(int seat,float u)const{
 const bool nonstop=playingDebate&&v4TaskActive&&stageKind=="nonstop";
 const auto& s=nonstop?court::NONSTOP_SHOTS[shotKind]:court::SHOTS[shotKind];float e=u*u*(3-2*u),sway=std::sin(shotTime*.7f); // 끝난 뒤에도 숨 쉬듯 조금씩 흔들린다
 return court::frame(court::seatAngle(seat),s.phi0+(s.phi1-s.phi0)*e+2.5f*sway,s.d0+(s.d1-s.d0)*e,s.h0+(s.h1-s.h0)*e+.03f*std::sin(shotTime*.9f),s.pitch,s.roll0+(s.roll1-s.roll0)*e+.6f*sway);
}
// 다중 카메라 : 엔진 focus 는 three.js setViewOffset(1,1,…) 로 화면비를 1 로 바꿔 인물이 옆으로 1.78배 늘어난다(engineCreate prototype/game-render-views.js).
// focus 를 쓰지 않고, 인물이 화면의 (fx,fy) 에 오도록 시선을 옆으로 비킨다(화면비 16:9, 세로 화각 fov)
static hb::Json aimView(hb::Vec3 eye,hb::Vec3 subject,float fov,float fx,float fy,std::vector<std::vector<float>> poly){
 float dx=subject.x-eye.x,dy=subject.y-eye.y,dz=subject.z-eye.z,len=std::max(.01f,std::sqrt(dx*dx+dy*dy+dz*dz));dx/=len;dy/=len;dz/=len;
 float rx=-dz,rz=dx,rl=std::max(.0001f,std::hypot(rx,rz));rx/=rl;rz/=rl; /* 오른쪽 = forward × up */
 float tv=std::tan(fov*.5f*court::PI/180),th=tv*16.f/9.f,ox=(.5f-fx)*2*th*len,oy=(fy-.5f)*2*tv*len;
 return {{"eye",{eye.x,eye.y,eye.z}},{"target",{subject.x+rx*ox,subject.y+oy,subject.z+rz*ox}},{"fov",fov},{"polygon",poly}};
}
void Yumeno::updateCamera(float delta){
 const bool panicLead=mode==Mode::Trial&&v4TaskActive&&v4QueueActive&&v4QueueAfter=="start"&&
  v4Task["stage"].value("kind",std::string())=="panic";
 std::vector<std::string> leadSpeakers;
 if(v4Court&&((mode==Mode::Story&&!panicLeadTask.empty())||panicLead))leadSpeakers=panicStorySpeakers;
 if(panicLead)for(int i=0;i<=v4QueueAt&&i<int(v4Queue.size())&&leadSpeakers.size()<3;++i){
  const auto& row=v4Queue[i];auto who=row.value("actor",std::string());
  if(!row.value("panicInterruption",false)||(who!="lappy"&&court::seatOf(who)<0))continue;
  if(std::find(leadSpeakers.begin(),leadSpeakers.end(),who)==leadSpeakers.end())leadSpeakers.push_back(who);
 }
 const bool viewsOn=mode==Mode::Trial&&stageKind=="panic"&&playingDebate&&debate.panic()&&!v4QueueActive&&!inScript&&debateResultTime<=0&&clearTimer<=0&&debateIntroTime<0;
 // V3 반론 쇼다운(LP 2장 Update 60) : 칸막이 왼쪽 = 증언대의 상대, 오른쪽 = 증언대의 주인공. 양쪽 다 실시간 3D 법정(뒤로 다른 인물들). 경계 = 형세 칸막이
 const bool sdViews=(mode==Mode::Trial||v4TaskActive)&&stageKind=="showdown"&&stage.contains("showdownV4")&&showdownV4.phase!=showdownv4::Phase::Complete&&showdownV4.phase!=showdownv4::Phase::Failed&&showdownV4.phase!=showdownv4::Phase::TimedOut&&(!inScript||v4QueueActive)&&debateResultTime<=0; /* 한국어판 3135.8·3136.4초 : 쇼다운 중 대사도 2분할 화면 위 대화창 */
 if(sdViews||sdTalkOn){
  float b=std::clamp(640+(50-showdownV4.gauge)*5,200.f,1080.f)/1280.f;int opp=court::seatOf(stage["showdownV4"].value("opponent",std::string()));
  hb::Json views=hb::Json::array();float sway=std::sin(idleYaw*.05f);
  auto view=[&](int seat,float phi,std::vector<std::vector<float>> poly,float fx){auto* a=seat==-2?actor("Host"):actor("Seat"+std::to_string(seat));if(!a)return; /* -2 = 왕좌의 래피(Host) */auto p=Scene::GetPosition(a); /* 실제 서 있는 자리(배치가 바뀌어도) */
   float len=std::max(.01f,std::hypot(p.x,p.z)),dx=-p.x/len,dz=-p.z/len,r=(phi+3*sway)*court::PI/180,ex=dx*std::cos(r)-dz*std::sin(r),ez=dx*std::sin(r)+dz*std::cos(r);
   float dist=sdTalkOn?1.9f:2.f; /* 주인님 지시 : 카메라는 늘 두 사람 정면 그대로(넓은 화면으로 바꾸지 않는다) */ /* 주인님 지시 : 정면에서, 머리까지 다 들어오게 */ /* 한국어판 3110~3112초 : 칸막이가 끝에 닿으면 주인공 쪽이 넓어져 옆 사람까지 */ /* 한국어판 3093.4초 : 양쪽 다 가슴 위를 크게 */ /* V3 175초 : 주인공 발언은 가슴 위를 크게 */views.push_back(aimView({p.x+ex*(seat==-2?2.4f:dist),seat==-2?p.y+.15f:1.86f,p.z+ez*(seat==-2?2.4f:dist)},{p.x,seat==-2?p.y:1.8f,p.z},40.f,fx,.5f,poly));}; /* 허리 위 + 옆 증언대가 보이는 거리(V3 LP 2장) */
  if(sdTalkOn)b=0; /* V3 175초 : 주인공 한 사람이 화면 가득 */
  if(opp<0&&stage["showdownV4"].value("opponent",std::string())=="lappy")opp=-2; /* 래피는 증언대가 아니라 왕좌 */
  {int me=court::seatOf("mio"),lo=opp,ro=me;auto has=[&](int s){return s>=0&&actor("Seat"+std::to_string(s));};
   if(opp>=0&&!v4QueueActive&&sdIntro>=2.6f&&sdIntro<3.1f){int k=1+int((3.1f-sdIntro)*10);if(has((opp+k)%16))lo=(opp+k)%16;if(me>=0&&has((me+16-k)%16))ro=(me+16-k)%16;} /* 3088.3~3088.8초 : 양쪽 카메라가 법정을 빠르게 훑고 멈춘다 */
   if((lo>=0||lo==-2)&&b>0)view(lo,0.f,{{0,0},{b,0},{b,1},{0,1}},b*.5f);
   if(ro>=0)view(ro,0.f,{{b,0},{1,0},{1,1},{b,1}},(1+b)*.5f);}
  auto state=hb::Json::parse(Game::GetStateText());state["renderViews"]=views;Game::SetStateText(state.dump());panicViewsPublished=true;
 }else if(leadSpeakers.size()>=2){
  const int count=int(leadSpeakers.size());
  if(count!=panicLeadCount){panicLeadCount=count;panicLeadSplit=0;}
  panicLeadSplit=std::min(1.f,panicLeadSplit+std::max(0.f,delta)/.28f);
  const float reveal=court::smooth5(panicLeadSplit);
  const bool three=count==3;
  std::vector<std::vector<std::vector<float>>> polygons=three
   ?std::vector<std::vector<std::vector<float>>>{{{0,0},{1,0},{0,.64f}},{{1,0},{1,1},{.46f,1}},{{0,.64f},{1,0},{.46f,1},{0,1}}}
   :std::vector<std::vector<std::vector<float>>>{{{0,0},{.59f,0},{.44f,1},{0,1}},{{.59f,0},{1,0},{1,1},{.44f,1}}};
  if(three){
   // Slide the new pane over the existing pair from their shared lower edge.
   for(auto& point:polygons[2])point[1]=1.f+(point[1]-1.f)*reveal;
   polygons[0]={{0,0},{.59f+.41f*reveal,0},{.44f*(1-reveal),1},{0,1}};
   polygons[1]={{.59f+.41f*reveal,0},{1,0},{1,1},{.44f+.02f*reveal,1}};
  }else{
   for(auto& point:polygons[0])if(point[0]>0)point[0]=1.f+(point[0]-1.f)*reveal;
   for(auto& point:polygons[1])if(point[0]<1)point[0]=1.f+(point[0]-1.f)*reveal;
  }
  const float focus[3][2]={{.26f,.38f},{.81f,.70f},{.48f,.72f}};
  auto views=hb::Json::array();
  for(int i=0;i<int(leadSpeakers.size());++i){
   if(leadSpeakers[i]=="lappy"){
    if(auto* host=actor("Host")){
     const auto p=Scene::GetPosition(host);const float length=std::max(.01f,std::hypot(p.x,p.z));
     views.push_back(aimView({p.x-p.x*2.6f/length,p.y+.15f,p.z-p.z*2.6f/length},p,41.f,focus[i][0],three?focus[i][1]:.44f,polygons[i]));
    }
    continue;
   }
   const int seat=court::seatOf(leadSpeakers[i]);const float angle=court::seatAngle(seat);
   const auto c=court::frame(angle,0,2.55f,1.81f,0,0);
   const float a=angle*court::PI/180;
   views.push_back(aimView({c.x,c.y,c.z},{court::RADIUS*std::sin(a),1.78f,court::RADIUS*std::cos(a)},41.f,focus[i][0],three?focus[i][1]:.44f,polygons[i]));
  }
  auto state=hb::Json::parse(Game::GetStateText());state["renderViews"]=views;Game::SetStateText(state.dump());panicViewsPublished=true;
 }else if(viewsOn){
  UI::SetTexture(this,UI_ID,"CourtDim","Assets/Art/ui/nonstop_source/panic_wash.svg");
  UI::SetOpacity(this,UI_ID,"CourtDim",1.f);
  const auto viewport=debate::panicViewport(gputrialhudv4::width,gputrialhudv4::height);
  UI::SetSize(this,"panes","PanicFrame0",{viewport[0],viewport[1]});
  hb::Json views=hb::Json::array();
  auto polygons=debate::PANIC_PANES;
  // The upper-right speaker's head must stay below the live status carrier.
  const float focus[3][2]={{.28f,.38f},{.83f,.55f},{.54f,.82f}};
  // Each YumenoKuni chapter uses the corresponding original wrapper's CDV
  // direction and local offsets, fitted to this courtroom's framing.
  struct Shot {float yaw,pitch;float offset[3][2];};
  static constexpr Shot profiles[]={
   {35,-35,{{0,0},{0,0},{0,0}}},
   {-70,25,{{0,100},{0,0},{0,0}}},
   {-28,62,{{50,0},{0,0},{0,0}}},
   {45,20,{{-200,-100},{0,0},{0,0}}},
   {0,0,{{0,0},{0,0},{0,0}}},
   {35,-30,{{-120,-20},{-120,-100},{40,-150}}}
  };
  const auto& shot=profiles[std::clamp(chapterAt,1,6)-1];
  for(int lane=0;lane<3&&lane<int(panicWho.size());lane++){
   const float fx=focus[lane][0]+shot.offset[lane][0]*.00022f;
   const float fy=focus[lane][1]+shot.offset[lane][1]*.00022f;
   if(panicWho[lane]=="lappy"){
    if(auto* host=actor("Host")){
     const auto p=Scene::GetPosition(host);const float length=std::max(.01f,std::hypot(p.x,p.z));
     views.push_back(aimView({p.x-p.x*2.6f/length,p.y+.15f,p.z-p.z*2.6f/length},p,43.f,fx,fy,polygons[lane]));
    }
    continue;
   }
   int seat=court::seatOf(panicWho[lane]);if(seat<0)continue;
   float phase=idleYaw*.055f+lane*2.1f;auto c=court::frame(court::seatAngle(seat),shot.yaw*.16f+4.f*std::sin(phase),(lane==2?2.95f:2.45f)+.08f*std::sin(phase*.8f),1.70f+shot.pitch*.004f,0,0);
   float angle=court::seatAngle(seat)*court::PI/180;
   views.push_back(aimView({c.x,c.y,c.z},{court::RADIUS*std::sin(angle),1.67f,court::RADIUS*std::cos(angle)},43.f,fx,fy,polygons[lane]));
  }
  svis("PanicFrame0",views.size()==3);
  auto state=hb::Json::parse(Game::GetStateText());state["renderViews"]=views;Game::SetStateText(state.dump());panicViewsPublished=true;
 }else if(panicViewsPublished){auto state=hb::Json::parse(Game::GetStateText());state.erase("renderViews");Game::SetStateText(state.dump());panicViewsPublished=false;}

 if(debateResultTime>0)return; // The success sequence owns the camera until it restores its entry pose.
 if(stageKind=="anagram"&&!v4QueueActive&&!inScript&&anagramIntroV4<=1.9f){
  UI::SetVisible(this,UI_ID,"Whip",false);
  return;
 }
 if(trialPickerOn&&!v4QueueActive&&!inScript&&stageKind!="bullet"){trialPickerCamera();return;}
 if(stageKind=="scrum"&&scrumT>=1&&(!v4QueueActive||speakerSeat>=0)&&scrumV4.state!=trialv4::Result::Complete){scrumFocus(); /* 완전논파 뒤 법정 대사는 스크럼 카메라로 돌아가지 않는다(Break 뒤 0.4초 스크럼 방이 비침) */UI::SetVisible(this,UI_ID,"Whip",false);return;}
 if(v4TaskActive&&!v4QueueActive&&stageKind=="showdown"&&stage.contains("showdownV4")){
  // The actual standing actor belongs to the left side of the observed V3
  // composition. A second front-of-desk portrait would duplicate that actor.
  int seat=court::seatOf(stage["showdownV4"].value("opponent",std::string()));
  if(seat>=0){auto c=court::frame(court::seatAngle(seat),0,2.8f,1.78f,0,0);c.yaw-=18.f;setCam(c);}
  UI::SetVisible(this,UI_ID,"Whip",false);return;
 }
 if(stageKind=="armament"&&v4TaskActive){
  // Own courtroom framing for V3's one-opponent rhythm view. Dialogue owns
  // its speaker camera only while queued; returning must face the actual target.
  float retreat=armFinish>0?court::smooth5((ARM_FINISH_SECONDS-armFinish-1.1f)/2.f):0;
  setCam({0,3.3f-.8f*retreat,10.f+2.f*retreat,0,0,0});armamentVisualUpdate(delta);
  UI::SetVisible(this,UI_ID,"Whip",false);return;
 }
 if(courtIdle||speakerSeat<0)UI::SetVisible(this,UI_ID,"Whip",false);
 // 패닉 : 세 영역 뒤 배경은 실제 재판장. 높이에서 위쪽 창·기둥을 비추며 천천히 돈다(입상은 영역마다 UI 로 크게)
 if(courtIdle&&stageKind=="panic"&&debate.panic()){idleYaw+=delta*4;float a=idleYaw*court::PI/180;setCam({.3f*std::sin(a),2.7f,.3f*std::cos(a),idleYaw,21,2*std::sin(idleYaw*.05f)});return;}
 if(courtIdle){idleYaw+=delta*7;float a=idleYaw*court::PI/180;setCam({.8f*std::sin(a),2.1f,.8f*std::cos(a),idleYaw,-5,0});return;}
 if(speakerSeat==-2&&playingDebate&&v4TaskActive&&stageKind=="nonstop"){
  // Start at the real preceding shot, rather than snapping onto the legacy orbit.
  if(cameraTime>=1)return;
  cameraTime=std::min(1.f,cameraTime+std::clamp(delta,0.f,1.f/40.f)/court::NONSTOP_WHIP_SECONDS);
  const float t=cameraTime*cameraTime*(3.f-2.f*cameraTime),bump=std::sin(cameraTime*court::PI);
  const auto host=court::shot(180);const court::Cam target{host.x*.2f,host.y+.48f,host.z*.2f,host.yaw,18,0};
  setCam(court::nonstopWhip(whipFrom,target,t));cameraPitch=cam.pitch;cameraAngle=court::turn(cameraFrom,cameraTo,t);
  UI::SetVisible(this,UI_ID,"Whip",cameraTime<1);if(cameraTime<1)UI::SetOpacity(this,UI_ID,"Whip",.28f*bump);
  return;
 }
 if(speakerSeat==-2||speakerSeat==-1){ // 래피(왕좌) · 시작 전 : 예전 정면 샷
  if(cameraTime>=1)return;
  cameraTime=std::min(1.f,cameraTime+delta/.45f);
  float t=cameraTime<.5f?4*cameraTime*cameraTime*cameraTime:1-std::pow(-2*cameraTime+2,3)/2;
  float pitchTo=speakerSeat==-2?24.f:0.f;cameraPitch=pitchFrom+(pitchTo-pitchFrom)*t;if(cameraTime>=1)pitchFrom=pitchTo;
  cameraAngle=court::turn(cameraFrom,cameraTo,t);placeCamera(cameraAngle);return;
 }
 if(speakerSeat<0)return;
 const bool nonstop=playingDebate&&v4TaskActive&&stageKind=="nonstop";
 if(!nonstop||cameraTime>=1)shotTime+=delta;
 float u=std::min(1.f,shotTime/(playingDebate?7.f:5.f));
 if(cameraTime<1){ // 휩 : 원을 따라 돌며 잠깐 멀어지고 기운다 + 속도선
  // Keep a late update from skipping the visible sweep across the courtroom.
  const float step=nonstop?std::clamp(delta,0.f,1.f/40.f):delta;
  cameraTime=std::min(1.f,cameraTime+step/(nonstop?court::NONSTOP_WHIP_SECONDS:.38f));
  float t=cameraTime<.5f?4*cameraTime*cameraTime*cameraTime:1-std::pow(-2*cameraTime+2,3)/2,bump=std::sin(cameraTime*court::PI);
  if(nonstop)t=cameraTime*cameraTime*(3.f-2.f*cameraTime);
  cameraAngle=court::turn(cameraFrom,cameraTo,t);
  auto to=shotCam(speakerSeat,0);auto mid=court::frame(cameraAngle,0,2.6f+1.3f*bump,1.6f,0,0);
  float dir=std::fmod(cameraTo-cameraFrom+540.f,360.f)-180.f>0?1.f:-1.f;
  auto lerp=[&](float a,float b){return a+(b-a)*t;};
  court::Cam c=mid;c.y=lerp(whipFrom.y,to.y);c.pitch=lerp(whipFrom.pitch,to.pitch);c.roll=lerp(whipFrom.roll,to.roll)+10*bump*dir;
  if(nonstop)c=court::nonstopWhip(whipFrom,to,t);
  if(cameraTime>=1)c=to;
  setCam(c);UI::SetVisible(this,UI_ID,"Whip",cameraTime<1);if(cameraTime<1)UI::SetOpacity(this,UI_ID,"Whip",(nonstop?.28f:.85f)*bump);
  if(cameraTime<1)return;shotTime=0;u=0;
 }
 setCam(shotCam(speakerSeat,u));
 // World-space 2D actors are depth-tested against actual 3D podiums, without flat UI furniture.
 UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
}
std::string Yumeno::poseTexture(const std::string& slug,const std::string& emo,const std::string& pose)const{
 if(slug.empty())return "";
 if(!pose.empty()){auto p=pose.substr(0,pose.find('_'));return "Assets/Art/sprites/"+p+"/"+pose+".webp";}
 std::string id="neutral";
 for(auto& [k,v]:emotions.items())if(!emo.empty()&&emo.find(k)!=std::string::npos){id=v.get<std::string>();break;}
 auto& table=slug=="lappy"?lappyPoses:poses;
 auto code=table.count(id)?table.at(id):(slug=="lappy"?"L01":"C01");
 return "Assets/Art/sprites/"+slug+"/"+slug+"_"+code+".webp";
}

// Move each 3D podium and its standing actor by the same radial offset. Room stays still.
void Yumeno::applyDebateSeats(float seconds){
 for(int i=0;i<16;i++){
  float offset=court::nonstopSeatOffset(i,seconds);
  if(std::abs(offset-debateSeatOffsets[i])<.00001f)continue;
  debateSeatOffsets[i]=offset;float a=court::seatAngle(i)*court::PI/180,si=std::sin(a),co=std::cos(a);
  if(auto* p=actor("Podium"+std::to_string(i)))Scene::SetPosition(p,{(court::RADIUS-court::PODIUM_INSET+offset)*si,.1f,(court::RADIUS-court::PODIUM_INSET+offset)*co});
  if(auto* p=actor("Seat"+std::to_string(i))){auto v=Scene::GetPosition(p);Scene::SetPosition(p,{(court::RADIUS+offset)*si,v.y,(court::RADIUS+offset)*co});}
 }
}
void Yumeno::cancelDebateIntro(){
 if(debateIntroTime>=0)applyDebateSeats(court::NONSTOP_SWEEP);
 debateIntroTime=-1;debateInputArmed=true;
 UI::Remove(this,"panicphasestartv4");
 for(auto id:{"IntroTop","IntroBottom","IntroFade","IntroStreaks","IntroStart","IntroStartEcho","IntroHoop","IntroHoop2","IntroAmmoList"})svis(id,false);
 for(int i=0;i<5;i++){svis("IntroGlyph"+std::to_string(i),false);svis("IntroGlow"+std::to_string(i),false);}
 for(auto id:{"IntroGun","IntroSelectedPlate","IntroSelectedText"})svis(id,false);
 for(int i=0;i<9;i++){svis("IntroAmmoRow"+std::to_string(i),false);svis("IntroAmmoPlate"+std::to_string(i),false);svis("IntroAmmoText"+std::to_string(i),false);}
 for(int i=0;i<5;i++)svis("IntroRound"+std::to_string(i),false);
 for(int i=0;i<32;i++)svis("IntroInBullet"+std::to_string(i),false);
 UI::Remove(actor("IntroOwner"),"intro");
 UI::SetVisible(this,UI_ID,"Whip",false);
 UI::SetVisible(this,UI_ID,"CourtDim",mode==Mode::Trial);
 UI::SetVisible(this,UI_ID,"Trial",mode==Mode::Trial);
}
void Yumeno::beginDebateIntro(){
 const bool sourceAmmo=stageKind=="nonstop"||debate.panic();
 if(!UI::Mounted("intro")){
  UI::Show(this,"Assets/UI/Intro.hbwidget.json","intro");
  for(auto it=svisible.begin();it!=svisible.end();)if(it->first.rfind("Intro",0)==0)it=svisible.erase(it);else ++it;
  pv4::Rehost(presentationV4);
 }
 debateIntroTime=debate.panic()?3.54f:0.f;debateIntroLoaded=0;debateInputArmed=false;courtIdle=false;
 auto first=debate.lines.empty()?std::string{}:!debate.lines.front().actor.empty()?debate.lines.front().actor:debate.lines.front().speaker;
 if(debate.panic()&&!panicWho.empty())first=panicWho.front();
 first=slugs.count(first)?slugs.at(first):first;
 debateIntroSeat=first=="lappy"?-2:court::seatOf(first);
 if(debateIntroSeat<0&&debateIntroSeat!=-2)debateIntroSeat=0;
 debateHud(false);drawNonstopSourceHud(0);UI::SetVisible(this,UI_ID,"Trial",false);
 for(auto id:{"Background","Portrait","SpeakerPodium","Cutin","TrialMsg"})UI::SetVisible(this,UI_ID,id,false);
 messageTimer=cutinTimer=0;
 for(auto id:{"IntroTop","IntroBottom","IntroFade"})svis(id,true);
 UI::SetVisible(this,UI_ID,"CourtDim",false);
 UI::SetOpacity(actor("IntroOwner"),"intro","IntroFade",0);
 UI::SetPosition(actor("IntroOwner"),"intro","IntroTop",{0,-24});UI::SetPosition(actor("IntroOwner"),"intro","IntroBottom",{0,702});
 for(int i=0;i<std::min(9,int(bullets.size()));i++){
  auto suffix=std::to_string(i);float width=sourceAmmo?std::clamp(50.f+17.5f*u8len(bullets[i].second),170.f,400.f):kotodamaPlateWidth(bullets[i].second);
  UI::SetText(actor("IntroOwner"),"intro","IntroAmmoText"+suffix,bullets[i].second);
  if(sourceAmmo){UI::SetFont(actor("IntroOwner"),"intro","IntroAmmoText"+suffix,"Assets/Fonts/pretendard/Pretendard-Medium.otf");UI::SetFontSize(actor("IntroOwner"),"intro","IntroAmmoText"+suffix,20);}
  UI::SetSize(actor("IntroOwner"),"intro","IntroAmmoPlate"+suffix,{width,sourceAmmo?38.f:50.f});
  UI::SetSize(actor("IntroOwner"),"intro","IntroAmmoText"+suffix,{width-(sourceAmmo?48:64),sourceAmmo?29.f:36.f});
 }
 UI::SetText(actor("IntroOwner"),"intro","IntroSelectedText",bullets.empty()?"":bullets[0].second);
 float selectedWidth=sourceAmmo?std::clamp(50.f+17.5f*u8len(bullets.empty()?"":bullets[0].second),170.f,400.f):kotodamaPlateWidth(bullets.empty()?"":bullets[0].second);
 UI::SetSize(actor("IntroOwner"),"intro","IntroSelectedPlate",{selectedWidth,sourceAmmo?38.f:50.f});
 UI::SetSize(actor("IntroOwner"),"intro","IntroSelectedText",{selectedWidth-(sourceAmmo?48:64),sourceAmmo?29.f:36.f});
 if(sourceAmmo){UI::SetFont(actor("IntroOwner"),"intro","IntroSelectedText","Assets/Fonts/pretendard/Pretendard-Medium.otf");UI::SetFontSize(actor("IntroOwner"),"intro","IntroSelectedText",20);UI::SetPosition(actor("IntroOwner"),"intro","IntroSelectedPlate",{125,600});UI::SetPosition(actor("IntroOwner"),"intro","IntroSelectedText",{149,604});}
 // All cartridges and labels share one transform origin and one row pitch.
 // This widget draws at most nine rows. Scaling by the entire acquired
 // inventory made 46 owned entries shrink those nine labels to 14.7%.
 const int visibleAmmo=std::min(9,int(bullets.size()));
 float listScale=std::min(1.f,420.f/(62*std::max(1,visibleAmmo))),a=10*court::PI/180,top=visibleAmmo>6?215.f:295.f;
 UI::SetRotation(actor("IntroOwner"),"intro","IntroAmmoList",-10);
 UI::SetScale(actor("IntroOwner"),"intro","IntroAmmoList",{listScale,listScale});
 UI::SetPosition(actor("IntroOwner"),"intro","IntroAmmoList",{185+listScale*(360*std::cos(a)+280*std::sin(a)),top+listScale*(-360*std::sin(a)+280*std::cos(a))});
 if(!debate.panic())setCam(court::nonstopIntro(debateIntroSeat,0,int(bullets.size())));
}
bool Yumeno::updateDebateIntro(float delta){
 if(debateIntroTime<0)return false;
 const bool panic=debate.panic(),sourceAmmo=stageKind=="nonstop"||panic;
 float previous=debateIntroTime;
 int count=int(bullets.size());float focusStart=court::nonstopFocusStart(count),duration=court::nonstopDuration(count);
 debateIntroTime=std::min(duration,debateIntroTime+std::max(0.f,delta));
 float t=debateIntroTime,load=t-court::NONSTOP_SWEEP;
 if(previous<2.05f&&t>=2.05f)sfx("sfx_band");
 applyDebateSeats(t);
 if(!panic||t>=court::NONSTOP_SWEEP){auto c=court::nonstopIntro(debateIntroSeat,t,count);setCam(c);cameraAngle=c.yaw-180;}
 float fade=t<court::NONSTOP_CUT?std::clamp(t/.8f,0.f,1.f):std::clamp(1-(t-court::NONSTOP_CUT)/.45f,0.f,1.f);
 svis("IntroFade",fade>0);if(fade>0)UI::SetOpacity(actor("IntroOwner"),"intro","IntroFade",fade);
 // Patch SFL confirms separate glyph/glow placements in reverse text order.
 // Distances and seconds below are authored for our own 1280x720 courtroom.
 const float glyphX[5]{130,350,500,685,855},glyphScale[5]{1.08f,.78f,.70f,.88f,1.08f},delay[5]{.42f,.37f,.32f,.13f,0};
 for(int i=0;i<5;i++){
  float age=t-2.05f-delay[i],out=court::smooth5((age-.92f)/.2f);
  bool on=!panic&&age>=0&&out<1&&t<3.55f;auto body="IntroGlyph"+std::to_string(i),glow="IntroGlow"+std::to_string(i);
  svis(body,on);svis(glow,on);
  if(on){float enter=court::smooth5(age/.14f),settle=court::smooth5((age-.07f)/.12f),x=-320+(glyphX[i]+320)*enter+1540*out+8*std::max(0.f,age-.14f),y=455-300*glyphScale[i]+42*(1-enter);
   for(auto& id:{glow,body}){UI::SetPosition(actor("IntroOwner"),"intro",id,{x,y});UI::SetScale(actor("IntroOwner"),"intro",id,{glyphScale[i],glyphScale[i]*(.5f+.5f*enter)});}
   UI::SetOpacity(actor("IntroOwner"),"intro",body,settle*(1-out));
   UI::SetOpacity(actor("IntroOwner"),"intro",glow,(1-.55f*settle)*(1-out));
  }
 }
 bool chargeStreak=load>=0&&load<.9f,streaks=(t>=1.9f&&t<3.55f)||chargeStreak;svis("IntroStreaks",streaks);
 if(streaks){UI::SetSize(actor("IntroOwner"),"intro","IntroStreaks",{1660,chargeStreak?530.f:210.f});UI::SetPosition(actor("IntroOwner"),"intro","IntroStreaks",{-190+120*std::sin(t*11),chargeStreak?60.f:260.f});UI::SetOpacity(actor("IntroOwner"),"intro","IntroStreaks",chargeStreak?std::clamp((.9f-load)/.18f,0.f,1.f):std::min(1.f,(t-1.9f)/.2f));}
 for(int i=0;i<32;i++){
  int lane=i%8,wave=i/8;float duration=.30f+.025f*(i%5),u=(load-wave*.12f-lane*.012f)/duration;
  auto id="IntroInBullet"+std::to_string(i);svis(id,u>=0&&u<1);
  if(u>=0&&u<1){UI::SetPosition(actor("IntroOwner"),"intro",id,{-1300+3000*u,75.f+lane*77+wave*9});UI::SetScale(actor("IntroOwner"),"intro",id,{1.05f+.22f*(i%4),.9f+.45f*(i%3)});}
 }
 bool start=t>=3.55f&&t<4.5f;svis("IntroStart",start&&!panic);svis("IntroStartEcho",start&&!panic);
 if(panic&&start&&!UI::Mounted("panicphasestartv4"))UI::Show(this,"Assets/UI/PanicPhaseStartV4.hbwidget.json","panicphasestartv4");
 if(panic&&!start&&UI::Mounted("panicphasestartv4"))UI::Remove(this,"panicphasestartv4");
 if(previous<3.55f&&t>=3.55f)sfx("sfx_band");
 if(start){float u=(t-3.55f)/.95f,exit=court::smooth5((u-.92f)/.08f),scale=u<.14f?.5f+.3f*u/.14f:.8f+.4f*(u-.14f)/.86f;
  auto* owner=actor("IntroOwner");
  UI::SetScale(owner,"intro","IntroStart",{scale,scale});UI::SetPosition(owner,"intro","IntroStart",{360,240});UI::SetOpacity(owner,"intro","IntroStart",1-exit);
  UI::SetScale(owner,"intro","IntroStartEcho",{scale,scale});UI::SetPosition(owner,"intro","IntroStartEcho",{360,240});UI::SetOpacity(owner,"intro","IntroStartEcho",.75f*(1-exit));
 }
 for(int i=0;i<2;i++){
  float u=(t-3.55f-i*.13f)/.72f;auto id=i==0?"IntroHoop":"IntroHoop2";bool on=u>=0&&u<1;svis(id,on);
  if(on){float scale=.2f+1.2f*court::smooth5(u);UI::SetScale(actor("IntroOwner"),"intro",id,{scale,scale});UI::SetRotation(actor("IntroOwner"),"intro",id,i==0?90.f:0.f);UI::SetOpacity(actor("IntroOwner"),"intro",id,1-court::smooth5((u-.45f)/.55f));}
 }
 float focus=court::smooth5((t-focusStart)/court::NONSTOP_FOCUS);
 bool loading=load>=.4f;
 svis("IntroGun",loading);
 svis("IntroAmmoList",load>=1.4f&&focus<.45f); /* 카메라가 첫 화자에 닿은 뒤(Courtroom nonstopIntro) */
 if(loading){
  auto* owner=actor("IntroOwner");float arrive=court::smooth5((load-.4f)/.25f);
  float size=sourceAmmo?600-290*focus:600-460*focus,gx=-180+(sourceAmmo?180:192)*focus-200*(1-arrive),gy=235+(sourceAmmo?215:319)*focus;
  UI::SetPosition(owner,"intro","IntroGun",{gx,gy});UI::SetSize(owner,"intro","IntroGun",{size,sourceAmmo?size*270/310:size});
  float turns=0;int loaded=0;
  for(int i=0;i<std::min(9,count);i++){
   float progress=(load-1.4f-i*.4f)/.22f,u=std::clamp(progress,0.f,1.f),e=court::smooth5(u);
   if(progress>=1)loaded++;
   turns+=e;bool listed=progress>=0&&focus<.45f;
   auto row="IntroAmmoRow"+std::to_string(i),plate="IntroAmmoPlate"+std::to_string(i),label="IntroAmmoText"+std::to_string(i);svis(row,listed);svis(plate,listed);svis(label,listed);
   if(listed){UI::SetPosition(owner,"intro",row,{50*(1-e),i*62.f});UI::SetOpacity(owner,"intro",row,e*(1-std::clamp(focus/.45f,0.f,1.f)));
   }
  }
  if(loaded>debateIntroLoaded){for(int i=debateIntroLoaded;i<loaded;i++)sfx("ui_select");debateIntroLoaded=loaded;}
  if(sourceAmmo){int frame=(int(std::round(-6*turns*(1-focus)))%36+36)%36;UI::SetTexture(owner,"intro","IntroGun","Assets/Art/ui/nonstop_source/cylinder"+std::to_string(frame)+".png");UI::SetRotation(owner,"intro","IntroGun",0);}else UI::SetRotation(owner,"intro","IntroGun",-72*turns);
  for(int i=0;i<5;i++){
   auto id="IntroRound"+std::to_string(i);bool on=!sourceAmmo&&i<loaded&&focus<1;svis(id,on);
   if(on){float a=(-90+72*i-72*turns)*court::PI/180,d=size*.278f,w=size*.1f;
    UI::SetPosition(owner,"intro",id,{gx+size*.5f+d*std::cos(a)-w*.5f,gy+size*.5f+d*std::sin(a)-w*.5f});UI::SetSize(owner,"intro",id,{w,w});UI::SetOpacity(owner,"intro",id,1-focus);}
  }
  if(v4TaskActive&&sourceAmmo)UI::SetOpacity(owner,"intro","IntroGun",1.f-focus);
  bool selected=!(v4TaskActive&&sourceAmmo)&&loading&&loaded>=std::min(9,count)&&focus>=.45f; /* 위 목록이 다 보이고 사라진 뒤에만(주인님 지시 2026-11-05 : 목록과 같이 있으면 안 됨) */ /* 장전이 다 끝난 뒤에만 고른 언령 이름표(주인님 지적 : 아무것도 안 했는데 미리 떠 있음) */
  svis("IntroSelectedPlate",selected);svis("IntroSelectedText",selected);
  if(selected)for(auto id:{"IntroSelectedPlate","IntroSelectedText"})UI::SetOpacity(owner,"intro",id,1.f);
 }
 drawNonstopSourceHud(delta);
 if(previous<focusStart&&t>=focusStart)sfx("ui_confirm");
 float open=std::clamp((t-duration+.15f)/.15f,0.f,1.f);
 UI::SetPosition(actor("IntroOwner"),"intro","IntroBottom",{0,702+18*open});
 if(t>=duration){
  cancelDebateIntro();debateInputArmed=false;debateHud(true);showBullet();
  if(panic){
   courtWide();updateCamera(0);drawNonstopSourceHud(0);return true;
  }
  if(!debate.lines.empty()){styleLine();shownLine=debate.index;}
  courtIdle=false;speakerSeat=debateIntroSeat;shotKind=8;shotTime=0;cameraTime=1;cameraPitch=pitchFrom=speakerSeat==-2?24.f:0.f;
  if(speakerSeat==-2){const auto host=court::shot(180);voteHostCamera={host.x*.2f,host.y+.48f,host.z*.2f,host.yaw,18,0};setCam(voteHostCamera);}
  else setCam(shotCam(speakerSeat,0));holdTime=-1;mouseWasDown=Input::IsKeyDown("mouse0");
 }
 return true; // Do not spend time or consume input on the handoff frame.
}

// ── 재판 진행 ────────────────────────────────────────────────
void Yumeno::startTrial(){
 if(!scenesv4::courtReady())return;
 stages=trials["stages"];
 trialVoted=false;
 bandTimer=flashTimer=0;evis("Band",false);evis("Flash",false); // 「수사 종료」 띠가 재판 내내 남아 있던 것(띠 시계는 탐색 화면에서만 돈다)
 debate=debate::State{};maxHearts=v4.active?growthv4::MaximumHp(growthV4)/2000:skillOn("max_heart")?6:5;debate.hearts=maxHearts;debate.focus=maximumFocus();shownHearts=-1;correctCount=0;reviveUsed=sdGuardUsed=missGuardUsed=false;retries=0;
 mode=Mode::Trial;dialogVisible(false);
 fvis("FHud",false);
 for(auto id:{"Title","Backdrop","Portrait","Background"})UI::SetVisible(this,UI_ID,id,false);
 UI::SetVisible(this,UI_ID,"Trial",true);UI::SetVisible(this,UI_ID,"CourtDim",true);
 mountTrialUi(stages.empty()?"scene":stages[0].value("kind",std::string("scene")));
 v4ComicClear();v4TaskRoot(true);setupCourt();
 enterStage(0);
}
void Yumeno::endTrial(){
 if(v4TaskActive){v4TaskEnd();return;}
 mode=Mode::Title;sclear();dialogVisible(false);UI::SetVisible(this,"trialvitalsv4","root",false);
 cancelDebateIntro();
 for(auto id:{"Trial","TrialBack","SpeakerPodium","Portrait","CourtDim"})UI::SetVisible(this,UI_ID,id,false);
 UI::SetVisible(this,UI_ID,"Backdrop",true);
 if(flowOn){trialDone();return;}
 UI::SetVisible(this,UI_ID,"Title",true);
}
void Yumeno::enterStage(int i){
 voteHostTime=0;voteMonitorTime=-1;
 modeEndTimeV4=-1;
 solutionPendingV4=0;solutionConsumedV4=false;
 skillMentalTicks=0;
 scrumPortraitSeatV4=-1;
 if(v4TaskActive)v4TrialInputArmed=false;
 if(stageKind=="scrum"){scrumFormation(0);for(auto id:{"scv3","scv3cut"})if(UI::Mounted(id))UI::Remove(this,id);scv3Op=scv3Team=scv3PushT=-1;}
 cancelDebateIntro();
 if(i<int(stages.size()))mountTrialUi(stages[i].value("kind",std::string("scene")));
 restartStage=false;inScript=false;sclear();dialogVisible(false);debateHud(false);playingDebate=false;
 armHudShown={-1,-1,-1};armHudTension=-1;
 for(auto id:{"StatusPanel","StatusLabel"})UI::SetVisible(this,UI_ID,id,true);for(int j=0;j<20;j++)UI::SetVisible(this,"trialvitalsv4","Heart"+std::to_string(j),j<maxHearts*2);for(int j=0;j<10;j++)UI::SetVisible(this,UI_ID,"Star"+std::to_string(j),true);
 UI::SetColor(this,trialui::ID,"StageTimer",Color{1,.698f,.122f,1});
 UI::SetPosition(this,trialui::ID,"StageTimer",{1040,656});UI::SetSize(this,trialui::ID,"StageTimer",{220,48}); // 객관식은 모래시계 아래로 옮긴다
 UI::SetPosition(this,trialui::ID,"SpkTag",{30,470});UI::SetPosition(this,trialui::ID,"SpkName",{52,478});UI::SetFontSize(this,trialui::ID,"SpkName",26.f);
 UI::SetPosition(this,trialui::ID,"BladeName",{880,640});UI::SetSize(this,trialui::ID,"BladeName",{380,50});UI::SetFontSize(this,trialui::ID,"BladeName",26.f);
 for(int k=0;k<4;k++){auto pid="Piece"+std::to_string(k);UI::SetPosition(this,trialui::ID,pid,{std::array<float,4>{482.6333f,843.4669f,482.6333f,115.3f}[k],std::array<float,4>{125.7667f,347.5667f,561.7667f,343.7667f}[k]});UI::SetColor(this,trialui::ID,pid,Color{1,1,1,1});UI::SetFontSize(this,trialui::ID,pid,30.f);}
 rhythmRecent=Json::array();rhythmPresses=0;rhythmJudge=0;rhythmInput=-1;
 stageAt=i;
 if(i>=int(stages.size())){endTrial();return;}
 stage=stages[i];stageKind=stage.value("kind","scene");stageTime=0;optStep=0;sdLine=0;scPair=0;mash=-1;armLine=0;armHits=0;armFinal=-1;taxiQ=0;taxiLane=1;taxiDist=0;anaFilled=0;
 auto& k=stageKind;
 if(v4TaskActive)v4TaskRoot(!v4QueueActive);
 if(i==0)trialVoted=false;
 if(k=="vote")trialVoted=true;
 if(k=="armament")sfx("sfx_heart_fast");
 const auto authoredMusic=stage.value("presentation",Json::object()).value("music",Json::object());
 const auto musicOperation=authoredMusic.value("operation",std::string());
 const bool ownsMusic=v4TaskActive&&(stage.contains("music")||musicOperation=="play"||musicOperation=="stop"||musicOperation=="keep");
 if(!ownsMusic){ // Legacy stages without an authored music policy.
  // 장마다 재판 곡·이론 무장 곡이 다르고, 논스톱은 재판 뒤쪽에서 고조되는 곡으로, 투표 슬롯 징글 뒤로는 진상 곡(V3)
  auto ch=trialKey.substr(1,1);bool late=i*2>=int(stages.size());
  static const std::map<std::string,std::string> cue{{"panic","bgm_trial_panic"},{"scrum","bgm_trial_scrum"},{"showdown","bgm_trial_showdown"},
   {"mindmine","bgm_trial_mindmine"},{"taxi","bgm_trial_taxi"},{"anagram","bgm_trial_anagram"},{"climax","bgm_trial_climax"}};
  auto it=cue.find(k);
  if(k=="vote")music("bgm_trial_main_1");
  else if(k=="nonstop")music(ch=="6"?"bgm_trial_nonstop_final":!late?"bgm_trial_nonstop":ch=="4"||ch=="5"?"bgm_trial_nonstop_lie":"bgm_trial_nonstop_b");
  else if(k=="armament")music("bgm_trial_armament_"+ch);
  else if(it!=cue.end())music(it->second);
  else if(!trialVoted)music("bgm_trial_main_"+ch);
 }
 if(v4TaskActive){
  const bool perjury=k=="nonstop"&&(chapterAt==4||chapterAt==5)&&
   v4Task.value("transformation",Json::object()).value("intentionalHold",false);
  if(perjury&&musicOperation=="play"&&authoredMusic.value("cue",std::string())=="bgm_trial_nonstop"){
   auto directedStage=stage;
   directedStage["presentation"]["music"]["cue"]="bgm_trial_nonstop_lie";
   pv4::Apply(presentationV4,directedStage,v4.generation);
  }else if(k=="climax"){
   auto directedStage=stage;
   directedStage["presentation"]["music"]={{"operation","stop"}};
   pv4::Apply(presentationV4,directedStage,v4.generation);
  }else pv4::Apply(presentationV4,stage,v4.generation);
 }
 if(k=="opening"||k=="scene"){beginScript();return;}
 if(k=="interrupt"){smsg("반론!",1.2f);beginScript();return;}
 if(k=="intermission"){smsg("휴정",1.4f);saveFlow();beginScript();return;}
 if(k=="nonstop"||k=="panic"){
  for(auto& d:trials["debates"])if(d.value("id","")==stage.value("id","")){startDebate(d);return;}
  if(v4TaskActive)throw std::runtime_error("Authored debate data missing");finishStage();return;
 }
 setupPlay();
}
void Yumeno::finishStage(){enterStage(stageAt+1);}

// 대사 재생 (단계 뒤 연출 / 대사만 있는 단계)
// 재판 CG (docs/spec/12 §5) : 이 단계 대사 동안 화면 가득. 둘이면 대사 절반에서 바뀐다
std::vector<std::string> Yumeno::trialCgs()const{
 static const std::map<std::string,std::map<std::string,std::vector<std::string>>> t{
  {"11c",{{"vote",{"event_1_breakdown"}}}},{"12c",{{"vote",{"event_2_salute"}}}},{"13c",{{"vote",{"event_3_identity"}}}},
  {"14c",{{"vote",{"event_4_fade","event_4_kneeling"}}}},{"15c",{{"vote",{"event_5_breakdown"}}}},
  {"16c",{{"0",{"event_6_lappy_identity"}},{"14",{"event_6_oath_lines"}},{"15",{"event_6_record_100"}},{"16",{"event_6_lappy_sacrifice"}}}}};
 auto a=t.find(trialKey);if(a==t.end())return {};
 auto b=a->second.find(stageKind);if(b==a->second.end())b=a->second.find(std::to_string(stageAt));
 std::vector<std::string> out;if(b!=a->second.end())for(auto& n:b->second)if(!artPath("cg",n,"cg",".webp").empty())out.push_back(n);
 return out;
}
void Yumeno::showTrialCg(int i){
 if(i>=int(scriptCgs.size()))return;
 UI::SetTexture(this,UI_ID,"Background","Assets/Art/cg/"+scriptCgs[i]+".webp");UI::SetPosition(this,UI_ID,"Background",{-40,-24});UI::SetScale(this,UI_ID,"Background",{1,1});
 UI::SetVisible(this,UI_ID,"Background",true);UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
}
void Yumeno::beginScript(){
 if(v4TaskActive&&!solutionConsumedV4&&stageKind=="reasoning"){solutionConsumedV4=true;beginModeEnding("reasoning","script");return;}
 if(v4TaskActive){trialScoreCapture();finishStage();return;}
 scriptLines.clear();for(auto& l:stage["script"])scriptLines.push_back(l);
 scriptAt=-1;inScript=true;sclear();debateHud(false);
 scriptCgs=trialCgs();showTrialCg(0);
 if(stageMsgTimer>0)svis("StageMsg",true);
 nextScriptLine();
}
void Yumeno::nextScriptLine(){
 if(++scriptAt>=int(scriptLines.size())){inScript=false;dialogVisible(false);if(!scriptCgs.empty()){scriptCgs.clear();UI::SetVisible(this,UI_ID,"Background",false);}finishStage();return;}
 if(scriptCgs.size()>1&&scriptAt==int(scriptLines.size())/2)showTrialCg(1);
 auto& l=scriptLines[scriptAt];
 auto who=l.value("speaker","");auto base=baseName(who);
 line=l.value("text","");
 bool monologue=who.find("독백")!=std::string::npos;
 bool narration=base.empty()||base=="UI";
 speaker=narration||monologue?"":base;
 if(narration&&line.rfind("[UI]",0)==0)line=line.substr(5);
 UI::SetColor(this,UI_ID,"Body",monologue?Color{.62f,.84f,1,1}:narration?(line.rfind("(",0)==0?Color{.8f,.75f,.85f,1}:Color{1,.86f,.45f,1}):Color{.96f,.94f,.97f,1});
 auto slug=slugs.count(base)?slugs.at(base):"";
 if(!slug.empty()&&!monologue&&scriptCgs.empty())focusSpeaker(slug,poseTexture(slug,l.value("emo",""),l.value("pose","")));
 dialogVisible(true);
 dialoguePrepare();
 auto readId="legacytrial:"+trialKey+":"+std::to_string(stageAt)+":"+std::to_string(scriptAt);optv4::BeginLine(optionsV4,readId,readLegacy.count(readId)>0);
}
void Yumeno::updateScript(float delta,bool next){
 if(int(shown)<lineLength){shown=std::min(float(lineLength),shown+delta*optv4::CharactersPerSecond(optionsV4));text("Body",u8prefix(dialogueText(),int(shown)));}
 bool fast=optv4::CanSkip(optionsV4,Input::IsKeyDown("Control"));if(fast){skipTimer+=delta;if(skipTimer>.05f){skipTimer=0;next=true;shown=float(lineLength);text("Body",dialogueText());}}else skipTimer=0;
 bool complete=int(shown)>=lineLength;if(optv4::ReportRead(optionsV4,complete&&dialogueFinal()))readLegacy.insert(optionsV4.line.id);
 if(optv4::AutoAdvance(optionsV4,delta,complete))next=true;
 if(!next)return;
 if(!dialogueAdvance())return;
 nextScriptLine();
}

// ── 놀이 단계 준비 ───────────────────────────────────────────
void Yumeno::showOptions(const std::string& question,const std::vector<std::string>& o){
 opts=o;optRects.assign(o.size(),{-10000,-10000,0,0});optHover=0;optPage=0;optionMouseX=aimX;optionMouseY=aimY;
 auto& k=stageKind;
 if(v4TaskActive&&k=="reasoning"){
  if(o.empty()||o.size()>3)throw std::runtime_error("Reasoning needs one to three authored candidates");
  for(auto id:{"Hourglass","AnswerLbl","StageTimer","Shade","QBand","QText","SpkTag","SpkName","Hint"})svis(id,false);
  svis("ReasoningBack",true);svis("ReasoningTitle",true);svis("Question",true);stext("Question",padsystem::wrap(question,480,"Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf",28).first);
  UI::SetPosition(this,trialui::ID,"Question",{64,218});UI::SetSize(this,trialui::ID,"Question",{490,220});UI::SetFontSize(this,trialui::ID,"Question",28);
  const auto& questions=stage["questions"];int first=std::max(0,v4TaskLinks-3);
  for(int i=0;i<3;i++){bool completed=first+i<v4TaskLinks;auto suffix=std::to_string(i);svis("ReasoningPastBand"+suffix,completed);svis("ReasoningPast"+suffix,completed);if(completed)stext("ReasoningPast"+suffix,padsystem::wrap(questions[first+i].value("answer",std::string()),314,"Assets/Fonts/pretendard/Pretendard-Medium.otf",18).first);svis("ReasoningBranch"+suffix,i<int(o.size()));}
  for(int i=0;i<8;i++){bool on=i<int(o.size());auto p="OptP"+std::to_string(i),t="OptT"+std::to_string(i);svis(p,on);svis(t,on);if(!on)continue;
   float y=180+i*110.f;optRects[i]={704,y,520,96};stext(t,padsystem::wrap(o[i],450,"Assets/Fonts/pretendard/Pretendard-Medium.otf",24).first);UI::SetPosition(this,trialui::ID,p,{704,y});UI::SetSize(this,trialui::ID,p,{520,96});UI::SetPosition(this,trialui::ID,t,{732,y+8});UI::SetSize(this,trialui::ID,t,{458,84});UI::SetFontSize(this,trialui::ID,t,24);
  }
  optionHighlight();return;
 }
 if(k=="choice"&&o.size()>=2&&o.size()<=4){trialAnswerStart(question);return;}
 if(v4TaskActive&&(k=="person"||k=="bullet")){trialPickerStart(question);return;}
 bool comic=k=="climax",chips=k=="scrum",bullet=k=="bullet",choice=k=="choice"||k=="reasoning",person=k=="person"||k=="vote",spot=k=="spot";
 // 공통 : 질문은 화면 아래 띠(V3 대사 자리), 화자 이름표, 조작 안내
 bool v3=choice||bullet||person||spot;
 if(v3){
  svis("Shade",true);svis("Emblem",!person&&!spot);svis("QBand",true);stext("QText",question);svis("QText",true);
  stext("Hint",person?"A/D 넘기기   Enter 지목":bullet?"W/S 고르기   Enter 제시":spot?"클릭 : 지목":"W/S 고르기   Enter 확인");svis("Hint",true);
  auto who=speaker.empty()?std::string("미오"):speaker;stext("SpkName",who);svis("SpkTag",choice);svis("SpkName",choice);
  svis("QPlate",false);svis("Question",false);
 }else{stext("Question",question);svis("QPlate",!question.empty());svis("Question",!question.empty());}
 if(choice){svis("AnswerLbl",true);svis("Hourglass",!v4TaskActive);UI::SetPosition(this,trialui::ID,"StageTimer",{100,480});}
 if(bullet){svis("BulCyl",true);svis("BulLine",true);for(auto id:{"CardFrame","CardImg","DescBox","CardTitle","CardText"})svis(id,true);}
 for(int i=0;i<8;i++){bool on=i<int(o.size())&&!person&&!spot;auto p="OptP"+std::to_string(i),t="OptT"+std::to_string(i);svis(p,on);svis(t,on);
  if(!on)continue;
  float x=300,y=250+i*46.f,w=980,h=42;
  if(bullet){x=96;y=150+i*44.f;w=420;h=40;}
  if(comic){x=290;y=404+i*52.f;w=700;h=46;}
  if(chips){w=std::min(236.f,(1232.f-12*(std::max(1,int(o.size()))-1))/std::max(1,int(o.size())));h=56;x=24+i*(w+12);y=640;} // 스크럼 : 우리 편 키워드를 아래에 가로로 (V3 십자키 선택)
  optRects[i]={x,y,w,h};
  stext(t,chips||bullet?o[i]:std::to_string(i+1)+" /  "+o[i]);
  UI::SetPosition(this,trialui::ID,p,{x,y});UI::SetSize(this,trialui::ID,p,{w,h});UI::SetTexture(this,trialui::ID,p,"Assets/Art/ui/band_off.svg");
  UI::SetPosition(this,trialui::ID,t,{x+(chips?12:bullet?22:30),y+(h-34)/2});UI::SetSize(this,trialui::ID,t,{w-(chips?24:60),34});UI::SetFontSize(this,trialui::ID,t,comic?19.f:chips?20.f:bullet?22.f:24.f);}
 if(k=="vote")voteShow();else if(person)personShow();
 if(spot)spotShow();
 optionHighlight();
}
// 고른 띠만 파랗게(V3). 언령 고르기는 오른쪽 카드·설명도 바꾼다
void Yumeno::bladeList(){
 if(v4TaskActive&&stageKind=="showdown"&&stage.contains("showdownV4")){
  for(int i=0;i<8;i++){svis("OptP"+std::to_string(i),false);svis("OptT"+std::to_string(i),false);}
  UI::SetTexture(this,"stage","SdBladeFrame","Assets/Art/ui/v3_hr/hud_katana_sheathed.webp");UI::SetPosition(this,"stage","SdBladeFrame",{6,590});UI::SetSize(this,"stage","SdBladeFrame",{640,109}); /* V3 조각을 원래 틀대로 조립한 칼(tools/v3_katana_compose.py) 비율 975:166 */ /* V3 원본 칼(kotodama_sword_saya·tuka) + 수국(t_hr_cylinder_mask) — 주인님 허락 V3 UI */
  UI::SetPosition(this,trialui::ID,"BladeName",{100,630});UI::SetSize(this,trialui::ID,"BladeName",{330,32});UI::SetFontSize(this,trialui::ID,"BladeName",22.f);UI::SetColor(this,trialui::ID,"BladeName",Color{1,1,1,1}); /* V3 LP 2장 : 수국 + 남색 칼집 위 흰 칼날 이름 + 붉은 매듭 + 검은 손잡이 */
  if(!bladeIds.empty())stext("BladeName",stage["options"][sdBullet].value("name",std::string()));svis("BladeName",true);return;
 }
 for(int i=0;i<8;i++){int item=(sdBullet/8)*8+i;bool on=item<int(bladeIds.size());auto p="OptP"+std::to_string(i),tt="OptT"+std::to_string(i);svis(p,on);svis(tt,on);if(!on)continue;
  float x=780+i*6.f,y=560-(std::min(8,int(bladeIds.size())-sdBullet/8*8)-1-i)*34.f;
  UI::SetPosition(this,trialui::ID,p,{x,y});UI::SetSize(this,trialui::ID,p,{480,32});UI::SetTexture(this,trialui::ID,p,item==sdBullet?"Assets/Art/ui/band_on.svg":"Assets/Art/ui/band_off.svg");
  UI::SetPosition(this,trialui::ID,tt,{x+24,y+2});UI::SetSize(this,trialui::ID,tt,{440,28});UI::SetFontSize(this,trialui::ID,tt,19.f);stext(tt,stage["options"][item].value("name",""));}
}
void Yumeno::optionHighlight(){
 auto& k=stageKind;
 if(trialPickerOn){trialPickerDraw();return;}
 if(trialAnswerOn&&k=="choice"){trialAnswerDraw(0);return;}
 if(k=="scrum"){scrumDraw();return;}
 if(v4TaskActive&&k=="reasoning")for(int i=0;i<int(opts.size());i++)UI::SetOpacity(this,trialui::ID,"ReasoningBranch"+std::to_string(i),i==optHover?1.f:.14f);
 if(k=="bullet"&&int(opts.size())>8){optPage=optHover/8;optRects.assign(opts.size(),{-10000,-10000,0,0});for(int row=0;row<8;row++){int index=optPage*8+row;bool on=index<int(opts.size());auto p="OptP"+std::to_string(row),t="OptT"+std::to_string(row);svis(p,on);svis(t,on);if(!on)continue;float y=150+row*44.f;optRects[index]={96,y,420,40};UI::SetPosition(this,trialui::ID,p,{96,y});UI::SetPosition(this,trialui::ID,t,{118,y+3});stext(t,opts[index]);UI::SetTexture(this,trialui::ID,p,index==optHover?"Assets/Art/ui/band_on.svg":"Assets/Art/ui/band_off.svg");}}
 if(k!="vote"&&!(k=="bullet"&&int(opts.size())>8))for(int i=0;i<std::min(8,int(optRects.size()));i++)UI::SetTexture(this,trialui::ID,"OptP"+std::to_string(i),i==optHover?"Assets/Art/ui/band_on.svg":"Assets/Art/ui/band_off.svg");
 if(k=="bullet"&&optHover<int(bladeIds.size())){
  auto id=bladeIds[optHover];bool icon=false;for(auto& c:art["kotodama"])if(c.get<std::string>()==id)icon=true;
  svis("CardImg",icon);if(v4TaskActive){svis("CardFrame",icon);UI::SetPosition(this,trialui::ID,"CardTitle",icon?Vec2{850,356}:Vec2{850,180});UI::SetPosition(this,trialui::ID,"CardText",icon?Vec2{846,400}:Vec2{846,240});UI::SetSize(this,trialui::ID,"CardText",icon?Vec2{400,190}:Vec2{400,310});}if(icon)UI::SetTexture(this,trialui::ID,"CardImg","Assets/Art/kotodama/"+id+".webp");
  stext("CardTitle",kotodamaName(id));auto t=kotodamaText(id);stext("CardText",t.empty()?std::string(" "):t);
 }
 if(k=="vote")voteShow();else if(k=="person")personShow();
}
// 인물 지목 : 가운데 한 명씩(전신), 번호·이름 장식, 발밑 고리
void Yumeno::personShow(){
 for(auto id:{"AccLbl","AccRing","AccFig","AccTag","AccNo","AccName","AccArrows","AccArrowR"})svis(id,true);
 if(optHover>=int(personIds.size()))return;
 auto& s=personIds[optHover];bool dead=std::find(trialDead.begin(),trialDead.end(),s)!=trialDead.end();
 UI::SetTexture(this,trialui::ID,"AccFig",dead?seatTexture[court::seatOf(s)]:v4TaskActive?courtFigures.at(s).at("texture").get<std::string>():"Assets/Art/sprites/"+s+"/"+s+"_C01.webp");
 stext("AccNo",std::to_string(court::seatOf(s)+1));stext("AccName",opts[optHover]);
 UI::SetPosition(this,trialui::ID,"AccFig",{210,40});UI::SetSize(this,trialui::ID,"AccFig",{500,v4TaskActive?540.f:600.f});UI::SetPosition(this,trialui::ID,"AccName",{790,282});UI::SetSize(this,trialui::ID,"AccName",{430,60});UI::SetFontSize(this,trialui::ID,"AccName",30);
 if(v4TaskActive&&stage.contains("candidateOverrides")&&stage["candidateOverrides"].contains(s)){
  auto row=stage["candidateOverrides"][s];auto image=row.value("image",std::string());if(!image.empty())UI::SetTexture(this,trialui::ID,"AccFig",image);
  auto caption=row.value("caption",std::string());stext("AccName",opts[optHover]+(caption.empty()?"":"\n"+caption));UI::SetSize(this,trialui::ID,"AccName",{430,150});UI::SetFontSize(this,trialui::ID,"AccName",24);
  if(row.value("layout",std::string())=="landscape-photo"){UI::SetPosition(this,trialui::ID,"AccFig",{135,130});UI::SetSize(this,trialui::ID,"AccFig",{590,370});}
 }
 UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
}
// 투표는 모든 참가자의 고정 4×4 자리다. 정답에 따라 후보를 추리지 않는다.
#include "VoteTVSourceV4.hpp"
void Yumeno::voteShow(){
 if(!voteGridVisible){votetvui::reset(this);voteIntroTicks=0;voteCommitTicks=-1;votePending=-1;}
 // The source motion belongs to the same TV plane; avoid a second fullscreen owner.
 if(UI::Mounted("trialinputmotion_vote"))UI::SetVisible(this,"trialinputmotion_vote","root",false);
 voteGridVisible=true;votetvui::monitorClear(this);UI::SetVisible(this,"vote","InputSourceFrame",true);UI::SetVisible(this,"vote","root",true);optRects.clear();
 UI::SetTexture(this,"vote","VoteBackdrop","Assets/Art/ui/vote_tv_source/black.svg");UI::SetPosition(this,"vote","VoteBackdrop",{0,0});UI::SetSize(this,"vote","VoteBackdrop",{1280,720});
 UI::SetTexture(this,"vote","VoteNamePlate",votetvui::assets().at("voteInputName").get<std::string>());votetvui::rect(this,"VoteNamePlate",0,0,1280,720);
 UI::SetVisible(this,"vote","VoteResultRows",false);votetvui::rect(this,"VotePortrait",votetvui::b().at("portrait"));UI::SetOpacity(this,"vote","VotePortrait",1);
 votetvui::rect(this,"VoteName",votetvui::b().at("name"));UI::SetFontSize(this,"vote","VoteName",36.f);UI::SetRotation(this,"vote","VoteName",votetvui::b().at("nameRotation"));
 for(auto id:{"VoteTitle","VoteTimer","VoteCommitText"})UI::SetVisible(this,"vote",id,false);
 for(int i=0;i<16;i++)for(auto prefix:{"VoteRF","VoteRN","VoteRB","VoteRC"})UI::SetVisible(this,"vote",std::string(prefix)+std::to_string(i),false);
 for(auto id:{"Shade","QBand","QText","Hint","StageTimer","AccFig","AccName"})svis(id,false);
 for(auto id:{"VoteBackdrop","VotePortrait","VoteNamePlate","VoteName","VoteTitleArt","VoteCommit"})UI::SetVisible(this,"vote",id,true);
 UI::SetVisible(this,"vote","VoteWait",false);
 for(int i=0;i<16;i++)UI::SetVisible(this,"vote","VoteShutter"+std::to_string(i),false);
 votetvui::rect(this,"VoteCommit",votetvui::b().at("commit"));votetvui::clock(this,std::max(0.f,stageLimit-stageTime),stageLimit);
 for(int i=0;i<16;i++){
  bool on=i<int(personIds.size());auto n=std::to_string(i);for(auto p:{"VoteP","VoteF"})UI::SetVisible(this,"vote",p+n,on);if(!on)continue;
  const auto& card=votetvui::assets().at("voteCards")[i];float x=card[0],y=card[1],w=card[2],h=card[3];const auto& screen=votetvui::b().at("screen");const auto& scale=votetvui::b().at("scale");optRects.push_back({screen[0].get<float>()+x*scale[0].get<float>(),screen[1].get<float>()+y*scale[1].get<float>(),w*scale[0].get<float>(),h*scale[1].get<float>()});
  for(auto p:{"VoteP","VoteF","VoteD"})votetvui::rect(this,std::string(p)+n,card);
  auto who=personIds[i];bool dead=std::find(trialDead.begin(),trialDead.end(),who)!=trialDead.end();votetvui::states[this].dead[i]=dead;UI::SetVisible(this,"vote","VoteD"+n,dead);
  UI::SetTexture(this,"vote","VoteP"+n,votetvui::assets().at("cardCursors")[i].get<std::string>());UI::SetOpacity(this,"vote","VoteP"+n,i==optHover?1.f:0.f);
  UI::SetTexture(this,"vote","VoteF"+n,votetvui::assets().at("cards").at(who)[i].get<std::string>());UI::SetOpacity(this,"vote","VoteF"+n,dead?.55f:1.f);
 }
 if(optHover<int(personIds.size())){
  const auto& who=personIds[optHover];auto image=courtFigures.at(who).at("texture").get<std::string>();auto label=nameOf(who);auto physical=who;bool explicitImage=false;
  if(v4TaskActive&&stage.contains("candidateOverrides")&&stage["candidateOverrides"].contains(who)){const auto& row=stage["candidateOverrides"][who];physical=row.value("physicalActor",who);if(courtFigures.contains(physical))image=courtFigures[physical].value("texture",image);explicitImage=row.contains("image");image=row.value("image",image);label=row.value("label",label);}
  if(!explicitImage)image=votetvui::portrait(physical,image);UI::SetTexture(this,"vote","VotePortrait",image);UI::SetText(this,"vote","VoteName",label);votetvui::states[this].resultName=label;
 }
 UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
}
void Yumeno::voteResultShow(){
 if(UI::Mounted("trialinputmotion_vote"))UI::Remove(this,"trialinputmotion_vote");voteShow();optRects.clear();voteResultTick=-1;votetvui::states[this].monitorSpace=true;votetvui::monitor(this,0,false,false);votetvui::pose(this,"intro",-1);
 sfx(!stage.value("finalVote",true)&&hasAudio("v3se_465")?"v3se_465":"v3se_369_d");UI::SetTexture(this,"vote","VoteBackdrop",votetvui::assets().at("voteResultBack").get<std::string>());votetvui::rect(this,"VoteBackdrop",0,0,1280,720);UI::SetTexture(this,"vote","VoteNamePlate",votetvui::assets().at("voteResultName").get<std::string>());
 UI::SetVisible(this,"vote","VoteResultRows",true);votetvui::rect(this,"VoteResultRows",0,0,1280,720);UI::SetVisible(this,"vote","VoteTitle",stage.value("selectionRole",std::string())=="historical-fact-intermediate-vote");
 for(auto id:{"VoteTitleArt","VoteTimeArt","VoteTimerObi","VoteTimer","VoteCommit","VoteCommitText","VoteGuide","VoteName","VoteNamePlate"})UI::SetVisible(this,"vote",id,false);
 for(int i=0;i<9;i++)UI::SetVisible(this,"vote","VoteDigit"+std::to_string(i),false);
 for(int i=0;i<16;i++)for(auto p:{"VoteP","VoteF","VoteD"})UI::SetVisible(this,"vote",std::string(p)+std::to_string(i),false);
 votetvui::rect(this,"VotePortrait",votetvui::b().at("portrait"));UI::SetOpacity(this,"vote","VotePortrait",0);votetvui::rect(this,"VoteNamePlate",0,0,1280,720);votetvui::rect(this,"VoteName",728.f,558.f,420.f,56.f);UI::SetRotation(this,"vote","VoteName",0);UI::SetFontSize(this,"vote","VoteName",29.f);
 UI::SetText(this,"vote","VoteTitle",stage.value("selectionRole",std::string())=="historical-fact-intermediate-vote"?"지목 확인":"투표 결과");
 for(int i=0;i<int(personIds.size())&&i<16;i++){
  auto n=std::to_string(i),who=personIds[i];const auto& f=votetvui::assets().at("voteResultFaces")[i];
  const auto& tally=votetvui::b().at("tally");
  const auto& label=tally.at("names")[i];
  const float x=label[0],y=label[1];
  votetvui::rect(this,"VoteRF"+n,f);votetvui::rect(this,"VoteRN"+n,x+10,y-1,156,24);
  UI::SetRotation(this,"vote","VoteRN"+n,label[2]);
  UI::SetFontSize(this,"vote","VoteRN"+n,14);
  votetvui::rect(this,"VoteRB"+n,tally.at("bounds")[i]);votetvui::rect(this,"VoteRC"+n,x,y+25,128,24);
  for(auto p:{"VoteRF","VoteRN"})UI::SetVisible(this,"vote",std::string(p)+n,true);UI::SetTexture(this,"vote","VoteRF"+n,"Assets/Art/ui/vote_verdict/dot_"+who+".png");UI::SetText(this,"vote","VoteRN"+n,nameOf(who));
 }
 voteResultUpdate(0);
}
void Yumeno::voteResultUpdate(float progress){
 int tick=std::clamp(int(progress*62),0,62);if(tick==voteResultTick)return;voteResultTick=tick;
 float intro=0;
 if(votetvui::b().contains("resultPortraitIn")){
  const auto& frames=votetvui::b().at("resultPortraitIn");
  intro=float(frames.size())/62.f;

 }
 const auto& tally=votetvui::b().at("tally");
 const int countFrame=tick-int(intro*62.f+.5f);
 const int countFrames=tally.at("countFrames");
 const bool announced=progress>=1.f||countFrame>=countFrames;
 UI::SetOpacity(this,"vote","VotePortrait",announced&&stage.value("finalVote",true)?1.f:0.f);
 Json counts=Json::object();if(stage.contains("voteCounts")&&stage["voteCounts"].is_object())counts=stage["voteCounts"];else if(stage.contains("authoredResult")&&stage["authoredResult"].is_object())for(const auto& who:personIds)if(stage["authoredResult"].contains(who))counts[who]=stage["authoredResult"][who];
 int total=0;for(auto& [who,count]:counts.items())if(count.is_number_integer())total+=std::max(0,count.get<int>());
 for(int i=0;i<int(personIds.size())&&i<16;i++){
  auto n=std::to_string(i),who=personIds[i];const bool known=total>0;
  const bool rowVisible=tick>=tally.at("rowIn")[i].get<int>();
  for(auto part:{"VoteRF","VoteRN"})UI::SetVisible(this,"vote",std::string(part)+n,rowVisible);
  int shown=0;
  const int count=known?std::clamp(counts.value(who,0),0,16):0;
  const auto& times=tally.at("timing")[i];
  while(shown<count&&countFrame>=times[shown].get<int>())++shown;
  UI::SetVisible(this,"vote","VoteRB"+n,shown>0);
  UI::SetVisible(this,"vote","VoteRC"+n,!known&&announced&&who==slotWho);
  if(shown>0)UI::SetTexture(this,"vote","VoteRB"+n,"Assets/Art/ui/vote_tv_source/tally_"+n+"_"+std::to_string(shown)+".png");
  else if(!known)UI::SetText(this,"vote","VoteRC"+n,announced&&who==slotWho?"다수표":"");
 }
 const bool finalVote=stage.value("finalVote",true);
 UI::SetVisible(this,"vote","VoteNamePlate",finalVote);
 UI::SetVisible(this,"vote","VoteName",finalVote);
 if(finalVote)UI::SetText(this,"vote","VoteName",announced?votetvui::states[this].resultName:"?????");
 if(!announced)votetvui::pose(this,"resultFx",-1);
}
void Yumeno::hideVote(){if(!voteGridVisible)return;votetvui::clearVerdict(this);votetvui::monitorClear(this);UI::SetVisible(this,"vote","root",false);voteGridVisible=false;}
// 지점 선택 : 현장 사진 액자 + 표식. 표식 자리는 보기 순서로 고르게 흩는다
void Yumeno::spotShow(){
 if(v4TaskActive){spotPending=-1;spotLockTicks=-1;spotQuestion=false;trialinputmotion::resetQuestion(this);svis("Question",false);svis("QPlate",false);trialinputmotion::show(this,"spot",trialInputClock);svis("QBand",false);svis("QText",false);svis("SpotModeFrame",true);svis("Hint",true);stext("Hint","클릭 지목 · F 질문 표시");}
 const auto r=v4TaskActive?spotlayoutv4::imageRect(v4Task.value("taskId",std::string())):std::array<float,4>{{190,90,900,520}};
 UI::SetPosition(this,trialui::ID,"SpotImg",{r[0],r[1]});UI::SetSize(this,trialui::ID,"SpotImg",{r[2],r[3]});UI::SetPosition(this,trialui::ID,"SpotFrame",{0,0});UI::SetSize(this,trialui::ID,"SpotFrame",{1280,720});
 UI::SetSize(this,trialui::ID,"CrossH",{r[2],1});UI::SetSize(this,trialui::ID,"CrossV",{1,r[3]});
 if(v4TaskActive){for(auto id:{"SpotTitle","SpotImg","SpotFrame","CrossH","CrossV"})svis(id,true);UI::SetTexture(this,trialui::ID,"SpotImg",stage.at("image").get<std::string>());for(int i=0;i<6;i++)svis("Mark"+std::to_string(i),false);UI::SetTexture(this,trialui::ID,"Mark0","Assets/Art/ui/spot_reticle.svg");UI::SetSize(this,trialui::ID,"Mark0",{44,44});svis("Mark0",true);svis("Hint",false);svis("MarkName",false);trialinputmotion::spotOpening(this,0);return;}
 for(auto id:{"SpotTitle","SpotImg","SpotFrame","CrossH","CrossV"})svis(id,true);
 UI::SetTexture(this,trialui::ID,"Mark0","Assets/Art/ui/spot_mark.svg");UI::SetSize(this,trialui::ID,"Mark0",{60,60});
 // 그 장 수사 현장 사진 : 수사 중 마지막 배경, 없으면 그 장 사망 CG
 std::string bg=sceneBackground;
 if(bg.empty()&&art.contains("cg"))for(auto& c:art["cg"]){auto n=c.get<std::string>();if(n.rfind("death_"+trialKey.substr(1,1),0)==0){bg="Assets/Art/cg/"+n+".webp";break;}}
 if(bg.empty())bg="Assets/Art/bg/trial_room.webp";
 UI::SetTexture(this,trialui::ID,"SpotImg",bg);
 const float MX[6]{.22f,.5f,.78f,.32f,.66f,.5f},MY[6]{.42f,.3f,.45f,.72f,.7f,.55f};
 for(int i=0;i<6;i++){bool on=i<int(opts.size());svis("Mark"+std::to_string(i),on);if(!on)continue;
  float x=190+900*MX[i],y=90+520*MY[i];UI::SetPosition(this,trialui::ID,"Mark"+std::to_string(i),{x,y});optRects.push_back({x-34,y-34,68,68});}
}
int Yumeno::optionAt(float x,float y)const{
 if(v4TaskActive&&stageKind=="spot"){
  const auto r=spotlayoutv4::imageRect(v4Task.value("taskId",std::string()));
  return taskv4::region(stage,(x-r[0])/r[2],(y-r[1])/r[3]);
 }
 for(size_t i=0;i<optRects.size();i++){auto& r=optRects[i];if(x>=r[0]&&x<=r[0]+r[2]&&y>=r[1]&&y<=r[1]+r[3])return int(i);}
 return -1;
}
std::vector<std::string> Yumeno::alive(bool withMio)const{
 std::vector<std::string> out;std::vector<std::string> dead;
 auto key=trialKey;
 dead=trialDead;(void)key;
 for(auto s:court::SEATS)if((withMio||std::string(s)!="mio")&&std::find(dead.begin(),dead.end(),s)==dead.end())out.push_back(s);
 return out;
}
void Yumeno::climaxOptions(){
 // 현재 빈칸 번호의 정답 조각("N번 정답") + 오답 조각, 이미 쓴 정답 조각은 뺀다
 std::vector<std::string> o;pieceIds.clear();
 auto& panels=stage["panels"];
 for(auto& p:stage["pieces"]){
  auto s=p.get<std::string>();
  if(std::find(usedPieces.begin(),usedPieces.end(),s)!=usedPieces.end())continue;
  std::string label=s;
  auto pos=s.find("번 정답");
  if(pos!=std::string::npos){int n=std::stoi(s.substr(0,pos));for(auto& q:panels)if(q.value("no",0)==n)label=q.value("caption","");}
  else if(s.rfind("오답(",0)==0)label=s.substr(7,s.size()-8);
  o.push_back(label);pieceIds.push_back(s);
 }
 int blank=-1;for(size_t i=0;i<panels.size();i++)if(panels[i].value("blank",false)&&!filledPanel[i]){blank=int(i);break;}
 climaxBlank=blank;
 optAnswer=-1;
 if(blank>=0){auto want=std::to_string(panels[blank].value("no",0))+"번 정답";for(size_t i=0;i<pieceIds.size();i++)if(pieceIds[i]==want)optAnswer=int(i);}
 showOptions(blank>=0?"빈칸 "+std::to_string(panels[blank].value("no",0))+"에 들어갈 그림은?":"",o);
 // 만화 칸 : 맞힌 칸은 설명, 빈칸은 「?」, 지금 채울 칸은 붉은 테두리
 for(size_t i=0;i<8;i++){bool on=i<panels.size();svis("PanP"+std::to_string(i),on);svis("PanT"+std::to_string(i),on);if(!on)continue;
  bool hole=panels[i].value("blank",false)&&!filledPanel[i];
  {auto img=artPath("cg","climax_"+trialKey.substr(1,1)+"_"+(panels[i].value("no",0)<10?"0":"")+std::to_string(panels[i].value("no",0)),"cg",".webp");bool pic=!hole&&!img.empty();
   svis("PanI"+std::to_string(i),pic);if(pic)UI::SetTexture(this,trialui::ID,"PanI"+std::to_string(i),img);
   stext("PanT"+std::to_string(i),pic?std::to_string(panels[i].value("no",0)):std::to_string(panels[i].value("no",0))+"  "+(hole?std::string("?"):panels[i].value("caption","")));}
  UI::SetColor(this,trialui::ID,"PanP"+std::to_string(i),int(i)==blank?Color{1,.82f,.86f,1}:hole?Color{.75f,.72f,.78f,1}:Color{.96f,.94f,.91f,1});}
}
void Yumeno::setupPlay(){
 auto& k=stageKind;std::vector<std::string> o;optAnswer=-1;
 UI::SetVisible(this,UI_ID,"Aim",k=="nonstop"||k=="panic");
 if(k=="mindmine"||k=="anagram"||k=="armament"){UI::SetPosition(this,trialui::ID,"Hint",{30,656});UI::SetSize(this,trialui::ID,"Hint",{960,32});UI::SetFontSize(this,trialui::ID,"Hint",16);}
 if(k=="choice"||k=="bullet"||k=="spot"||k=="person"||k=="vote"||k=="mindmine")courtWide(); // 고르는 동안 뒤에서 재판장이 천천히 돈다
 if(k=="choice"){for(auto& v:stage["options"])o.push_back(v.get<std::string>());optAnswer=stage.value("answer",0);showOptions(stage.value("question",""),o);}
 else if(k=="bullet"||k=="showdown"||k=="mindmine"){
  /* V3 : 언령은 장마다 그 사건에서 모은 것만 쓴다. 지난 장 언령까지 101개를 돌리면 칼을 고를 수 없다(T4-RS-A03 정답이 64번째). id 의 장 표시(v4:E<장>- / v4:<장>:)가 지금 장과 다른 것은 뺀다. 표시가 없는 공통 항목은 둔다. */
  {auto chapterOf=[](const std::string& id){if(id.rfind("v4:E",0)==0&&id.size()>5&&std::isdigit((unsigned char)id[4])&&id[5]=='-')return id[4]-'0';if(id.size()>4&&std::isdigit((unsigned char)id[3])&&id[4]==':')return id[3]-'0';return -1;};
   if(v4TaskActive&&chapterAt>0){Json kept=Json::array();for(auto& v:stage["options"]){int c=chapterOf(v.value("id",""));if(c<0||c==chapterAt)kept.push_back(v);}if(!kept.empty())stage["options"]=kept;}}
  bladeIds.clear();for(auto& v:stage["options"]){bladeIds.push_back(v.value("id",""));o.push_back(v.value("name",""));}
  if(k=="bullet"){for(size_t i=0;i<bladeIds.size();i++)if(bladeIds[i]==stage.value("answer",""))optAnswer=int(i);showOptions(stage.value("question",""),o);}
 }
 else if(k=="spot"){if(v4TaskActive){for(auto& r:stage["regions"]){if(r.value("id","")==stage.value("answerRegionId",""))optAnswer=int(o.size());o.push_back(r.value("label",std::string()));}}else{for(auto& v:stage["options"])o.push_back(v.get<std::string>());for(size_t i=0;i<o.size();i++)if(o[i]==stage.value("answer",""))optAnswer=int(i);}showOptions(stage.value("question",""),o);}
 else if(k=="person"||k=="vote"){
  personIds=v4TaskActive?stage.at("candidates").get<std::vector<std::string>>():k=="vote"?std::vector<std::string>(std::begin(court::SEATS),std::end(court::SEATS)):alive(true);
  {auto ans=stage.value("answer","");if(k=="vote"&&!ans.empty()&&std::find(personIds.begin(),personIds.end(),ans)==personIds.end())personIds.push_back(ans);} // 영정에게도 투표할 수 있다(3장)
  for(size_t i=0;i<personIds.size();i++){bool dead=std::find(trialDead.begin(),trialDead.end(),personIds[i])!=trialDead.end();auto label=nameOf(personIds[i]);if(v4TaskActive&&stage.contains("candidateOverrides")&&stage["candidateOverrides"].contains(personIds[i]))label=stage["candidateOverrides"][personIds[i]].value("label",label);o.push_back(label+(dead?" (영정)":""));if(personIds[i]==stage.value("answer",""))optAnswer=int(i);}
  const auto prompt=stage.value("question",std::string());
  showOptions(k=="vote"&&prompt.empty()?"범인이라고 생각하는 사람에게 투표하세요":prompt,o);
 }
 if(v4TaskActive&&k=="lie"){v4LieStart();return;}
 if(v4TaskActive&&k=="reasoning"){courtWide();v4Reasoning();}
 if(v4TaskActive&&k=="climax"){v4TaskRoot(true);v4ComicStart();v4ComicShow();return;}
 if(k=="climax"){usedPieces.clear();filledPanel.assign(stage["panels"].size(),false);climaxOptions();}
 if((k=="showdown"||k=="armament")&&stage.contains("opponent")){auto who=stage.value("opponent","");speakerSeat=-1;focusSpeaker(who,who=="lappy"?who:poseTexture(who,"",who+(k=="armament"?"_T04":"_C12")));}
 if(k=="showdown"){sdBullet=0;sdTime=0;stext("BladeName","언령의 칼 · "+(bladeIds.empty()?std::string():stage["options"][0].value("name","")));svis("BladeName",true);svis("Blade",true);
  auto who=stage.value("opponent","");svis("SdFace",true);UI::SetTexture(this,trialui::ID,"SdFace","Assets/Art/cutin/"+who+"_2.webp");
  UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
  stext("SpkName",v4TaskActive?stage.value("opponentDisplay",nameOf(who)):nameOf(who));svis("SpkTag",true);svis("SpkName",true);bladeList();if(v4TaskActive&&stage.contains("showdownV4")){v4ShowdownStart();return;}}
 if(k=="scrum")if(const auto* sx=trialdirection::find("scrum",stage.value("id",std::string()))){ // 늘린 대치(연출표 scrum, tools/trial_scrum.py) — 선택지는 라운드 수만큼 나온다
  for(const auto& p:*sx){bool have=false;for(const auto& q:stage["pairs"])have=have||q.value("id",std::string())==p.value("id",std::string());if(!have)stage["pairs"].push_back(p);}}
 if(k=="scrum"){scrumConfirmedV4.assign(stage["pairs"].size(),false);scrumChosenV4.assign(stage["pairs"].size(),-1);scrumHpV4=v4TaskActive?v4TaskEntryHp:debate.hearts*2000;scrumPairElapsedV4=0;scrumV4.reset(difficultyV4.action);scrumV4.duet=v4TaskActive&&skillOn("duet");minigameTicksV4=0;scrumT=0;scrumWait=0;svis("ScBand",false);for(auto id:{"scv3","scv3cut","scrumv4"})if(UI::Mounted(id))UI::Remove(this,id);UI::Show(this,"Assets/UI/ScrumV3Cut.hbwidget.json","scv3cut");UI::Show(this,"Assets/UI/ScrumV4.hbwidget.json","scrumv4");UI::Show(this,"Assets/UI/ScrumV3.hbwidget.json","scv3");stexts.clear();svisible.clear();pv4::Rehost(presentationV4); /* 그리는 순서 : 인물 판(scv3cut) → 양쪽 목록(scrumv4) → 시간판·문양·도입(scv3) */scv3HideAll();scv3Op=0;scv3Team=scv3PushT=-1;scv3Resp=-1;scv3Revealed.assign(stage["pairs"].size(),false);scv3Prev=0;scv3Focus.clear(); /* V3 : 「의견대립」부터(V4ScrumV3.hpp) */UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);scrumNext();}
 if(k=="armament"){armingV4=trialv4::Arming{};armingV4.maxHp=maxHearts*2000;armingV4.difficulty=difficultyV4.action;armingV4.viability=v4TaskActive&&skillOn("viability")?.8f:1.f;armingV4.highTension=v4TaskActive&&skillOn("high_tension");armingV4.beatHeaven=v4TaskActive&&skillOn("beat_heaven");armingV4.wildAwakening=v4TaskActive&&skillOn("wild_awakening");armingV4.hp=v4TaskActive?v4TaskEntryHp:debate.hearts*2000;armingV4.opponent=armingV4.totalOpponent=std::max(30,int(stage["lines"].size())*30);trialui::armNote(armingV4,stage,0,armLine);svis("ArmLine",true);svis("Ring",true);svis("RingCore",true);stext("ArmLine",stage["lines"][0].get<std::string>());armBeat=0;
  auto who=stage.value("opponent","");svis("AccFig",false); // The approved world opponent already occupies this view; no old duplicate portrait.
  if(v4TaskActive)armamentRhythmStart();
  armamentVisualStart();UI::SetVisible(this,UI_ID,"CourtDim",false);UI::SetPosition(this,trialui::ID,"ArmLine",{84,258});UI::SetSize(this,trialui::ID,"ArmLine",{720,120});svis("Hint",false);
  armNoteDraw();armHudDraw();
  for(auto id:{"StatusPanel","StatusLabel"})UI::SetVisible(this,UI_ID,id,false);for(int j=0;j<20;j++)UI::SetVisible(this,"trialvitalsv4","Heart"+std::to_string(j),false);for(int j=0;j<10;j++)UI::SetVisible(this,UI_ID,"Star"+std::to_string(j),false);
  UI::SetPosition(this,trialui::ID,"StageTimer",{72,656});UI::SetSize(this,trialui::ID,"StageTimer",{300,48});UI::SetColor(this,trialui::ID,"StageTimer",Color{.28f,.86f,1,1});
  svis("ArmFace",true);if(!v4TaskActive)UI::SetTexture(this,trialui::ID,"ArmFace","Assets/Art/armament_v4/player_mio.webp");
  UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
  stext("SpkName",v4TaskActive?stage.value("opponentDisplay",nameOf(who)):nameOf(who));svis("SpkTag",false);svis("SpkName",!v4TaskActive);UI::SetPosition(this,trialui::ID,"SpkName",{60,48});UI::SetFontSize(this,trialui::ID,"SpkName",22.f);}
 if(k=="anagram"){
  anaChars=debate::glyphs(stage.value("answer",""));orbs.clear();std::u16string required,choices;
  for(auto& g:anaChars)required+=trialui::unit(g);if(v4TaskActive&&stage.contains("distractors")){for(const auto& item:stage["distractors"])for(const auto& g:debate::glyphs(item.get<std::string>()))choices+=trialui::unit(g);}else for(auto d:trialui::DECOYS)choices+=trialui::unit(d);
  choices+=required;anagramV4.reset(required,choices,v4TaskActive&&skillOn("initial_a"));anagramV4.hp=v4TaskActive?v4TaskEntryHp:debate.hearts*2000;anagramV4.wrongDamage=difficultyv4::anagramDamage(difficultyV4.logic);if(v4TaskActive)anagramV4.wrongDamage=growthv4::Damage(growthV4,anagramV4.wrongDamage);anagramFeedbackV4=anagramV4.state==trialv4::Result::Complete?1.f:0.f;minigameTicksV4=0;anaFilled=int(anagramV4.at);
  anagramLitV4.fill(-1);anagramScaleV4.fill(-1);anagramQuestionV4=false;anagramFocusDrawnV4=-1;shownHearts=-1;anagramLightV4=trialv4::AnagramLight{};if(v4TaskActive)anagramLightV4.configure(skillOn("intuition_of_god"),skillOn("spark_it"));anagramLightV4.maxMental=int(maximumFocus()*100);anagramLightV4.reset(int(debate.focus*100));
  for(int i=0;i<trialv4::Anagram::COUNT;i++){auto& a=anagramV4.orbs[i];Orb b;b.ch=trialui::glyph(a.glyph);b.x=640+a.x*.5f;b.y=360+a.y*.48f;b.vx=(i%2?-1.f:1.f)*difficultyv4::anagramSpeed(difficultyV4.action)*.5f;b.vy=0;orbs.push_back(b);stext("Orb"+std::to_string(i),b.ch);svis("AnaBall"+std::to_string(i),true);anagramOrbDraw(i,b.x,b.y,1,false);}
  for(auto id:{"AnaBackground","AnaSilhouette","AnaLight","AnaAnswerLabel","AnaTimeLabel","AnaTime","AnaQuestionButton","AnaAim","AnaStatus"})svis(id,true);
  for(int i=0;i<20;i++)svis("AnaHeart"+std::to_string(i),i<maxHearts*2);for(int i=0;i<10;i++)svis("AnaStar"+std::to_string(i),true);
  auto question=stage.value("question",std::string());stext("AnaQuestion",question);UI::SetFontSize(this,"anagramv4","AnaQuestion",std::min(30.f,500.f/std::max(1,u8len(question))));svis("AnaQuestion",false);svis("AnaQuestionButton",!question.empty());lightX=-682.6667f;anaSlots();anagramPresentationStart();
 }
 if(k=="mindmine"){
  if(v4TaskActive){v4MineStart();return;}
  UI::Remove(this,"minev4");UI::Show(this,"Assets/UI/MineV4.hbwidget.json","minev4");for(int i=0;i<242;i++)svisible.erase("Cell"+std::to_string(i));
  int colorCount=stage.contains("mine")?stage["mine"].value("colors",3):(chapterAt>=4?4:3);
  cells=trialv4::mineBoard(trialui::COLS,trialui::ROWS,colorCount,stageAt+std::max(1,chapterAt));loneHits.assign(cells.size(),0);
  mineV4.reset(trialui::COLS,trialui::ROWS,colorCount,cells,int(18000*trialTimeFactor()));mineV4.hp=debate.hearts*2000;mineV4.wrongDamage=1000;mineV4.undoEnabled=skillOn("undo_enable")||(stage.contains("mine")&&stage["mine"].value("undo",false));mineV4.safetyFirst=skillOn("safety_first");minigameTicksV4=0;
  mineAnswer=0;for(size_t i=0;i<bladeIds.size();i++)if(bladeIds[i]==stage.value("card",""))mineAnswer=int(i);
  auto catalogue=Data::Get("Assets/Data/art.json");std::string bg="Assets/Art/bg/trial_room.webp";
  for(auto& name:catalogue["minigame"])if(name.get<std::string>()=="mindmine_"+trialKey.substr(1,1))bg="Assets/Art/ui/minigame/mindmine_"+trialKey.substr(1,1)+".webp";
  UI::SetTexture(this,trialui::ID,"MineBg",bg);UI::SetPosition(this,trialui::ID,"MineBg",{trialui::CELL_X,trialui::CELL_Y});UI::SetSize(this,trialui::ID,"MineBg",{740,420});svis("MineBg",true);
  std::vector<trialv4::MineImage> images;
  for(int i=0;i<3;i++){bool on=i<int(o.size());svis("MineItem"+std::to_string(i),on);svis("MineIcon"+std::to_string(i),false);if(!on)continue;
   float x=285+i*245.f;stext("MineItem"+std::to_string(i),o[i]);UI::SetPosition(this,trialui::ID,"MineItem"+std::to_string(i),{x,430});UI::SetSize(this,trialui::ID,"MineItem"+std::to_string(i),{220,38});
   bool icon=false;for(auto& c:catalogue["kotodama"])if(c.get<std::string>()==bladeIds[i])icon=true;
   if(icon){UI::SetTexture(this,trialui::ID,"MineIcon"+std::to_string(i),"Assets/Art/kotodama/"+bladeIds[i]+".webp");UI::SetPosition(this,trialui::ID,"MineIcon"+std::to_string(i),{x,290});UI::SetSize(this,trialui::ID,"MineIcon"+std::to_string(i),{220,140});svis("MineIcon"+std::to_string(i),true);}
   trialv4::MineImage image;image.id=i;image.correct=i==mineAnswer;
   // Legacy stages supply labelled cards, not pixel masks. Their authored footprint
   // includes the card plus its opaque nameplate; selection only uses that nameplate.
   for(int row=0;row<trialui::ROWS;row++)for(int col=0;col<trialui::COLS;col++){float cx=trialui::CELL_X+col*trialui::CELL_W,cy=trialui::CELL_Y+row*trialui::CELL_H;if(cx<x+220&&cx+trialui::CELL_W>x&&cy<468&&cy+trialui::CELL_H>290)image.cells.push_back(row*trialui::COLS+col);}images.push_back(image);
  }
  mineV4.setImages(images);
  for(size_t i=0;i<cells.size();i++){svis("Cell"+std::to_string(i),true);UI::SetTexture(this,"minev4","Cell"+std::to_string(i),trialui::MINE_TILES[cells[i]]);}
  stext("Question",stage.value("question",""));svis("QPlate",true);svis("Question",true);
  stext("Hint",mineV4.undoEnabled?"좌클릭 : 제거 · 우클릭 / Enter : 드러난 이름표 선택 · Backspace : 되돌리기":"좌클릭 : 제거 · 우클릭 / Enter : 드러난 이름표 선택");svis("Hint",true);stageLimit=999;
 }
 if(k=="taxi"){svis("Road",true);svis("Car",true);carX=640;taxiLane=1;roadT=0;taxiShow();}
 if(k=="showdown"||k=="armament"||k=="scrum"||k=="anagram"||k=="taxi")stageLimit=k=="taxi"?999:(k=="armament"?(chapterAt==6?600.f:420.f):k=="scrum"?scv3Task().value("limit",300.f):k=="anagram"?300.f:90.f)*trialTimeFactor(); // 브레인 드라이브는 시간 대신 집중력(다른 차와 부딪히면 감소)
 if(k!="mindmine"&&k!="showdown"&&k!="armament"&&k!="scrum"&&k!="anagram"&&k!="taxi")stageLimit=999;
 if(k=="vote")stageLimit=stage.value("duration",30.f)*trialTimeFactor();
 if(v4TaskActive)v4TaskRoot(true);
}

// ── 단계별 갱신 ─────────────────────────────────────────────
void Yumeno::optionPicked(int i){
 if(v4TaskActive&&stageKind=="climax"){v4ComicPick(i);return;}
 if(stageKind=="scrum"){scrumPick(i);return;}
 if(i<0){if(v4TaskActive&&stageKind=="spot"){hurt();v4TaskWrong();}return;}
 if(v4TaskActive&&stageKind=="reasoning"){
  const auto& q=stage["questions"].at(v4TaskLinks);if(i>=int(q["options"].size()))return;
  if(i!=optAnswer){hurt();pv4::Action(presentationV4,"trial_wrong");auto selected=q["optionIds"][i].get<std::string>();auto rows=Json::array();
   for(const auto& variant:q.value("wrongVariants",Json::array()))if(variant.value("optionId",std::string())==selected){rows=variant.value("script",Json::array());break;}
   if(!rows.empty()){++trialResults.current.gaffe;v4TaskQueue(rows,"resume");}else v4TaskWrong();return;
  }
  heal();auto rows=q.value("success",Json::array());++v4TaskLinks;sclear();v4TaskQueue(rows,"reasoning");return;
 }
 bool correct=i==optAnswer;if(v4TaskActive&&stageKind=="spot"&&i<int(stage["regions"].size()))correct=correct||stage["regions"][i].value("correct",false);
 if(!correct){hurt();int variant=-1;
  if(v4TaskActive&&(stageKind=="choice"||stageKind=="bullet"||stageKind=="person"||stageKind=="spot"||stageKind=="vote")){
   const auto variants=v4Task["queues"].value("wrongVariants",Json::array());
   const auto cause=stageKind=="spot"?stage["regions"][i].value("wrongVariant",std::string()):std::string();
   for(int v=0;v<int(variants.size());v++){
    const auto& authored=variants[v];
    if(stageKind!="spot"?authored.value("optionIndex",-1)==i:!cause.empty()&&authored.value("cause",std::string())==cause){variant=v;break;}
   }
  }
  v4TaskWrong(variant);return;}
 heal();
 if(stageKind=="climax"){
  usedPieces.push_back(pieceIds[i]);filledPanel[climaxBlank]=true;
  smsg("맞았어!",.6f);climaxOptions();
  if(climaxBlank<0){smsg("이게 사건의 전부야!",1.4f);beginScript();}
  return;
 }
 if(stageKind=="vote"){
  trialPickerClear();slotWho=personIds[i];hideVote();
  for(auto id:{"AccLbl","AccRing","AccFig","AccTag","AccNo","AccName","AccArrows","AccArrowR","QBand","QText","Hint","Shade"})svis(id,false);
  courtIdle=false;focusSpeaker("lappy","lappy");
  if(auto* h=actor("Host"))Scene::SetPosition(h,{0,3.87f,-(court::RADIUS+2.4f)});
  const auto host=court::shot(180);cameraTime=1;cameraPitch=pitchFrom=18.f;
  voteHostCamera={host.x*.2f,host.y+.48f,host.z*.2f,host.yaw,18,0};setCam(voteHostCamera);
  speaker=nameOf("lappy");line="투표가 끝났네. 그럼 결과를 발표할게!";
  dialogVisible(true);dialoguePrepare();shown=float(lineLength);text("Body",dialogueText());
  voteHostTime=4.f;sfx("ui_confirm");return;
 }
 if(!v4TaskActive&&stageKind!="choice")smsg("정답!",.8f);beginScript();
}
// 스크럼 배치 : 상대 편은 왼쪽 줄, 우리 편은 오른쪽 줄. 나머지 자리는 잠시 비운다.
void Yumeno::scrumFormation(float t,float rise){ // rise<0 : t 를 따른다(0 이면 내려옴)
 auto& pairs=stage["pairs"];
 std::vector<std::string> them,us;
 auto add=[&](std::vector<std::string>& v,const std::string& n){auto sl=slugs.count(n)?slugs.at(n):"";if(!sl.empty()&&std::find(v.begin(),v.end(),sl)==v.end())v.push_back(sl);};
 if(stage.contains("scrumSides")){
  const auto& sides=stage.at("scrumSides");
  them=sides.at("them").get<std::vector<std::string>>();
  us=sides.at("us").get<std::vector<std::string>>();
 }else{
  for(auto& p:pairs){add(them,p.value("them",""));add(us,p.value("us",""));}
  if(std::find(us.begin(),us.end(),"mio")==us.end())us.insert(us.begin(),"mio");
 }
 float e=t<.5f?2*t*t:1-std::pow(-2*t+2,2)/2;
 if(rise<0)rise=t>0?1.f:0.f;float r=rise<.5f?2*rise*rise:1-std::pow(-2*rise+2,2)/2;
 if(auto* bd=actor("ScrumBackdrop"))Components::Set(bd,"MeshRenderer","visible",t>0); // V3 : 변형된 재판장 벽(밝은 타일·남색 원)
 if(auto* th=actor("ScrumThrone")){Components::Set(th,"SpriteRenderer","visible",e>.5f);Scene::SetPosition(th,{0,1.45f,-3.7f}); /* 두 줄이 바닥에 서므로 왕좌도 바닥 높이 */}
 if(auto* host=actor("Host"))Scene::SetPosition(host,e>.5f?Vec3{0,1.9f,-3.62f}:Vec3{0,4.6f,-(court::RADIUS+2.4f)});
 for(int i=0;i<16;i++){
  std::string sl=court::SEATS[i];
  float a=court::seatAngle(i)*court::PI/180;
  float cx=court::RADIUS*std::sin(a),cz=court::RADIUS*std::cos(a);           // 원래 자리
  float tx=cx,tz=cz;bool shown=true;
  auto f=std::find(them.begin(),them.end(),sl);auto g=std::find(us.begin(),us.end(),sl);
  if(f!=them.end()){tx=-1.3f;tz=(float(them.size())-1)*.56f-1.12f*float(f-them.begin());}
  else if(g!=us.end()){tx=1.3f;tz=(float(us.size())-1)*.56f-1.12f*float(g-us.begin());}
  else shown=false;
  float x=cx+(tx-cx)*e,z=cz+(tz-cz)*e,lift=(f!=them.end()||g!=us.end())&&e>.5f?0.f:r*(2.2f+1.4f*float(i%4)+.5f*float(i%3)); /* 주인님 지시·영상 16~29초 : 증언대가 늘어나지 않고 통째로 하늘로 솟는다(자리마다 높이가 다름). 두 줄로 서면 바닥 */ // 솟을 때는 자리마다 다른 높이, 두 줄로 서면 같은 높이(V3 1:18:28)
  if(auto* s1=actor("Seat"+std::to_string(i))){bool gone=std::find(trialDead.begin(),trialDead.end(),sl)!=trialDead.end();Scene::SetPosition(s1,{x,lift+(gone?1.85f:courtFigures[sl].value("center",court::SPRITE_CENTER)),z});float original=court::seatAngle(i)+180,target=f!=them.end()?90.f:g!=us.end()?270.f:original;Scene::SetRotation(s1,{0,court::turn(original,target,e),0});seatVisible(i,shown||t<.05f);}
  { // V3 스크럼(영상 A 1:18:36~45) : 두 줄로 서면 빨강 팀은 화면 오른쪽, 파랑 팀은 왼쪽을 보는 옆모습. 그림(<slug>_SR/_SL)이 있을 때만(사양서 23)
   bool side=(f!=them.end()||g!=us.end())&&e>.5f;auto key=sl+(f!=them.end()?"_SR":"_SL");
   if(auto* plane=actor("Seat"+std::to_string(i)))Components::Set(plane,"SpriteRenderer","billboard",side);
   if(side&&!scrumSideSeats.count(i)&&courtFigures.contains(key)){courtPose(i,key);scrumSideSeats.insert(i);}
   else if(!side&&scrumSideSeats.count(i)){scrumSideSeats.erase(i);courtPose(i,sl);}}
  if(auto* p1=actor("Podium"+std::to_string(i))){Scene::SetScale(p1,{1,.82f,1}); /* 늘이지 않는다 */float k=1-court::PODIUM_INSET/court::RADIUS;Scene::SetPosition(p1,{x+(f!=them.end()?.35f:g!=us.end()?-.35f:0)*e+(cx*k-cx)*(1-e),.1f+lift,z+(cz*k-cz)*(1-e)});float original=court::seatAngle(i)+180,target=f!=them.end()?90.f:g!=us.end()?270.f:original;Scene::SetRotation(p1,{0,court::turn(original,target,e),0});Components::Set(p1,"MeshRenderer","visible",shown||t<.05f);}
 }
 // 카메라는 시작 연출(updateTrial 스크럼 들어가기)과 scrumFocus 가 정한다
}
void Yumeno::scrumFocus(){
 if(stageKind!="scrum"||!stage.contains("pairs")||stage["pairs"].empty())return;
 auto& p=stage["pairs"][std::min(scPair,int(stage["pairs"].size())-1)];
 auto slug=p.value("themActor",std::string());if(slug.empty()&&slugs.count(p.value("them",std::string())))slug=slugs.at(p.value("them",std::string()));
 if(UI::Mounted("scv3cut")&&mash<0&&scv3Op<0&&scv3Team<0&&scv3PushT<0&&!v4QueueActive&&scv3Resp>=0&&scv3RespT<.8f){scv3PlayCam();return;} /* 맞힌 순간 넓게 쓸고 지나감. 발언은 아래 증언대 화자 근접(주인님 지시 2026-11-07 : 큰 그림을 새로 띄우지 말고 의논석 기준으로, V3 46초 신구지는 자리에 선 채 카메라가 다가감) */
 int seat=!scv3Focus.empty()?court::seatOf(scv3Focus):mash>=0?court::seatOf(scv3PushSlug()):v4QueueActive?speakerSeat:court::seatOf(slug);if(seat<0)return;
 if(auto* a=actor("Seat"+std::to_string(seat))){
  auto pos=Scene::GetPosition(a);bool left=pos.x<0;
  // Shot adapted to our own two-row court, with the speaking actor in the
  // foreground. SFL pixel anchors do not imply V3 world/camera coordinates.
  auto texture=seatTexture[seat],key=texture.substr(texture.find_last_of('/')+1);auto dot=key.find_last_of('.');if(dot!=std::string::npos)key.resize(dot);
  float top=pos.y+(courtFigures.contains(key)?courtFigures[key].value("height",2.3f):2.3f)/2;
  // V3(영상 A 1:18:36~45) : 말하는 사람을 통로 안 왕좌 쪽에서 비스듬히 잡는다. 건너편을 향해 선 입상이 원근으로 비껴 보여 옆을 보는 구도가 된다
  { // V3(영상 A 1:18:40·1:18:50·1:19:00 프레임) : 말하는 사람을 가슴 위로 화면 절반 가득 잡는다. 빨강(건너편, 왼쪽 줄)은 화면 왼쪽에서 오른쪽을 보고
    // 발언은 오른쪽 빈 곳(ScVClaimInk 610,180), 파랑(우리 줄)은 화면 오른쪽에서 왼쪽을 본다. 입상은 billboard 라 정면 거리만 맞추면 된다.
   // FOCAL 900 기준 머리(약 0.35 m)가 화면 높이 45% 쯤 되는 거리 1.1 m, 가로 0.33 m 비켜 화자 중심이 x≈370 / 910
   float side=left?-1.f:1.f,d=1.1f,cx=pos.x-side*.33f,cy=top-.32f,cz=pos.z+d;
   setCam({cx,cy,cz,0,-2,0});}
  UI::SetVisible(this,UI_ID,"Portrait",false);scrumPortraitSeatV4=-1; // 정면 UI 초상을 덧그리면 원근(옆을 보는 각도)이 사라진다 : 3D 입상만
  if(false){float sx,sy,depth;if(courtFigures.contains(key)&&court::screen(cam,pos.x,pos.y,pos.z,sx,sy,depth)){
   const auto& f=courtFigures[key];float scale=court::FOCAL/depth,w=f.value("width",1.f)*scale,h=f.value("height",2.3f)*scale;
   // The bright speaker overlays the same world rectangle above CourtDim;
   // no second portrait at an unrelated screen anchor.
   std::array<float,4> rect{{sx-w/2,sy-h/2,w,h}};
   if(scrumPortraitSeatV4!=seat||scrumPortraitTextureV4!=texture||scrumPortraitRectV4!=rect){
    UI::SetTexture(this,UI_ID,"Portrait",texture);UI::SetPosition(this,UI_ID,"Portrait",{rect[0],rect[1]});UI::SetSize(this,UI_ID,"Portrait",{w,h});UI::SetVisible(this,UI_ID,"Portrait",true);scrumPortraitSeatV4=seat;scrumPortraitTextureV4=texture;scrumPortraitRectV4=rect;
   }
  }
 }
 }
 UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
}
void Yumeno::scrumDraw(){
 const auto& pairs=stage["pairs"];bool push=mash>=0;
 const auto decoys=stage.find("scrumDecoys");
 if(scv3Op>=0||scv3Team>=0||scv3PushT>=0||scrumT<1||(v4QueueActive&&mash<0)){scv3Speaker("",true); /* 반응 대사 중(영상 83초)에도 진행 HUD 없음 */ /* 의견대립·열쇠·증언대·주제 동안 진행 HUD 를 미리 그리지 않는다(주인님 지적 : 도입 전에 발언 글이 보였다) */
  for(int s2=0;s2<2;s2++)for(int r=0;r<10;r++)for(auto suf:{"P","F","T"})svis(std::string("ScV")+(s2?"R":"L")+suf+std::to_string(r),false);
  for(auto id:{"ScVStatementP","ScVStatement","ScVClaimInk","ScVPush","ScVKey","ScVPushText"})svis(id,false);scv3Speaker("",true);UI::SetVisible(this,"trialvitalsv4","root",false);return;}
 if(pairs.empty()||pairs.size()>10)throw std::runtime_error("Scrum supports one to ten authored pairs");
 svis("ScVStatementP",false);svis("ScVStatement",!push&&!v4TaskActive);svis("ScVClaimInk",false);if(!push&&scv3Resp<0&&scPair<int(pairs.size())){const auto& pp=pairs[scPair];auto sl=pp.value("themActor",std::string());if(sl.empty()&&slugs.count(pp.value("them",std::string())))sl=slugs.at(pp.value("them",std::string()));scv3Speaker(sl,true);}
 if(!push&&scv3Resp<0&&scPair<int(pairs.size()))scv3Claim(pairs[scPair].value("themText",std::string()),true,!(scPair<int(scv3Revealed.size())&&scv3Revealed[scPair])); /* 상대 낱말은 맞힌 적이 있어야 노랑(주인님 지시) */scv3Emblem(!push,stageTime);svis("StageMsg",false);
 svis("ScVPush",false);svis("ScVKey",false); /* V3 단추 그림(scv3PushButton) */svis("ScVPushText",false); if(push){UI::SetPosition(this,"scrumv4","ScVPush",{583,386});UI::SetSize(this,"scrumv4","ScVPush",{114,114});UI::SetPosition(this,"scrumv4","ScVKey",{595,410});} /* V3(1:19:20) : 둥근 단추는 아래 가운데, 두 팀 맨 앞 탭이 만나는 자리 */
 if(!push){const auto text=pairs[scPair].value("themText",std::string());if(!v4TaskActive)stext("ScVStatement",text); /* V4 발언 글은 V3 큰 글(scv3Claim) */}
 constexpr float offsets[10][2]={{0,0},{0,-66.6667f},{85.3333f,-133.3333f},{170.6667f,-200},{213.3333f,-266.6667f},{213.3333f,-333.3333f},{213.3333f,-400},{213.3333f,-466.6667f},{213.3333f,-533.3333f},{213.3333f,-600}};
 for(int side=0;side<2;side++)for(int rank=9;rank>=0;rank--){
  std::string base=std::string("ScV")+(side?"R":"L"),id=std::to_string(rank);
  bool on=rank<(push?1:side?int(scrumIds.size()):int(pairs.size()));
  for(auto suffix:{"P","F","T"})svis(base+suffix+id,on);if(!on)continue;
  int row=push?0:side?scrumIds[(optHover+rank)%scrumIds.size()]:(scPair+rank)%pairs.size();
  const auto& pair=row<int(pairs.size())?pairs.at(row):decoys->at(row-int(pairs.size()));
  float dx=side?offsets[rank][0]:-offsets[rank][0],dy=offsets[rank][1];bool large=rank==0;
  float x=(side?(large?714.6667f:943.3333f):(large?-118.f:-72.6667f))+dx,y=(large?538.6667f:572.f)+dy;
  float w=large?682.6667f:409.6f,h=large?170.6667f:102.4f;
  UI::SetPosition(this,"scrumv4",base+"P"+id,{x,y});UI::SetSize(this,"scrumv4",base+"P"+id,{w,h});
  float tx=(side?(large?809.3333f:999.3333f):(large?176.6667f:-12.6667f))+dx,ty=(large?607.3333f:613.3333f)+dy;
  auto keyword=push||side?pair.value("keyword",std::string()):trialv4::Scrum::keywordVisible(row,row<int(scv3Revealed.size())&&scv3Revealed[row],v4TaskActive&&skillOn("head_start_punch"))?pair.value("keyword",std::string()):std::string("？？？"); /* 주인님 지시 : 우리 쪽은 상대 말을 받아칠 같은 낱말을 그대로 들고 있다(V3 인터벌↔인터벌) */
  float textWidth=large?293.3333f:230.f,font=large?24.f:17.f;if(!large&&tx<12)tx=12;float textRight=side?1268.f:std::min(1268.f,x+w-34.f);textWidth=std::max(0.f,std::min(textWidth,textRight-tx));
  UI::SetFont(this,"scrumv4",base+"T"+id,keyword=="？？？"?"Assets/Fonts/pretendard/Pretendard-Medium.otf":"Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf");
  auto label=keyword;
  if(v4TaskActive&&keyword!="？？？"){static const auto bank=Data::Get("Assets/Data/scrum_text_v4.json");if(bank["keywordLabels"].contains(keyword))label=bank["keywordLabels"][keyword].get<std::string>(); /* 표시용 줄임말이 없으면 낱말 그대로 */}
  auto shownKeyword=textWidth<40.f?std::string():flowchoice::window(label,scrumPairElapsedV4,textWidth*26.66667f/font).first;
  UI::SetPosition(this,"scrumv4",base+"T"+id,{tx,ty});UI::SetSize(this,"scrumv4",base+"T"+id,{textWidth,40});UI::SetFontSize(this,"scrumv4",base+"T"+id,font);stext(base+"T"+id,shownKeyword);
  auto slug=pair.value(side?"usActor":"themActor",std::string());if(slug.empty()&&slugs.count(pair.value(side?"us":"them",std::string())))slug=slugs.at(pair.value(side?"us":"them",std::string()));
  // V3(1:18:36) : 얼굴은 탭 안, 배경 없이 머리만, 건너편을 보는 옆모습. 탭 높이(가는 막대 h*.28)보다 조금 크게
  float fw=w*(side?259.f:255.f)/1024.f,fh=h*140.f/256.f,fx=x+w*(side?520.f:245.f)/1024.f,fy=y+h*58.f/256.f;
  UI::SetPosition(this,"scrumv4",base+"F"+id,{fx,fy});UI::SetSize(this,"scrumv4",base+"F"+id,{fw,fh});if(!slug.empty()){static const auto courtData=Data::Get("Assets/Data/court.json");const auto key=slug+(side?"_SL":"_SR");auto texture="Assets/Art/scrum_faces/"+key+".webp";if(courtData.contains("scrumFaces")&&courtData["scrumFaces"].contains(key))texture=courtData["scrumFaces"][key].get<std::string>();UI::SetTexture(this,"scrumv4",base+"F"+id,texture);}else svis(base+"F"+id,false);
  if(side&&!push){int choice=(optHover+rank)%scrumIds.size();float hx=std::max(0.f,x),right=std::min(1280.f,x+w);optRects[choice]={hx,y+h*.25f,std::max(0.f,right-hx),h*.5f};}
 }
 UI::SetPosition(this,trialui::ID,"StageTimer",{490,18});UI::SetSize(this,trialui::ID,"StageTimer",{300,48});
 scrumFocus();
}
void Yumeno::scrumNext(){
 auto& pairs=stage["pairs"];
 if(scPair>=int(pairs.size())){auto wrong=std::find(scrumConfirmedV4.begin(),scrumConfirmedV4.end(),false);
  if(wrong!=scrumConfirmedV4.end()){ /* 영상 1번 81.9~94초 : 마지막 발언 뒤 넓은 화면 → 처음 틀린 합의 반응 대사 → 처음부터 다시(맞힌 합도 다시) */
   int w=int(wrong-scrumConfirmedV4.begin());auto& opponent=pairs[w];scrumHpV4=std::max(0,scrumHpV4-(v4TaskActive?growthv4::Damage(growthV4,opponent.value("damage",1000)):opponent.value("damage",1000)));sfx("v3se_362");debate.hearts=(scrumHpV4+1999)/2000;
   if(scrumHpV4<=0){debate.hearts=1;hurt();scrumHpV4=debate.hearts*2000;if(restartStage)return;}
   auto response=opponent.value("wrong",Json::array());
   const int chosen=scrumChosenV4[w];
   if(chosen>=int(pairs.size())&&stage.contains("scrumDecoys")){
    const auto& decoy=stage.at("scrumDecoys").at(chosen-int(pairs.size()));
    const auto specific=opponent.value("wrongByKeyword",Json::object());
    response=specific.value(decoy.at("keyword").get<std::string>(),response);
   }
   std::fill(scrumConfirmedV4.begin(),scrumConfirmedV4.end(),false);std::fill(scrumChosenV4.begin(),scrumChosenV4.end(),-1);scPair=0;opts.clear();optRects.clear();
   for(int s2=0;s2<2;s2++)for(int r=0;r<10;r++)for(auto suf:{"P","F","T"})svis(std::string("ScV")+(s2?"R":"L")+suf+std::to_string(r),false);scv3Speaker("",true);scv3Emblem(false,0);setCam({0,2.2f,4.4f,0,-5,0});
   auto rows=Json::array();{const auto& first=pairs[0];Json say={{"type","say"},{"speaker",first.value("them",std::string())},{"actor",first.value("themActor",std::string())},{"text",first.value("themText",std::string())},{"mono",false}};rows.push_back(say);} /* 영상 83~91초 : 한 바퀴 뒤 처음 말한 사람이 대화하듯 다시 말하고, 이어 반응 */
   for(const auto& r:response)rows.push_back(r);scrumWait=.6f;if(v4TaskActive&&!rows.empty())v4TaskQueue(rows,"resume");return;}
  else{scv3PushT=0;scv3Prev=0;sfx("v3se_366");opts.clear();optRects.clear();for(int s2=0;s2<2;s2++)for(int r=0;r<10;r++)for(auto suf:{"P","F","T"})svis(std::string("ScV")+(s2?"R":"L")+suf+std::to_string(r),false);scv3Speaker("",true);return;}} /* 137.9초 : 모두 맞으면 CROUCH·BIND·SET! */
 scrumPairElapsedV4=0;
 std::vector<std::string> o;scrumIds.clear();
 const auto decoys=stage.find("scrumDecoys");
 const size_t count=pairs.size()+(decoys==stage.end()?0:decoys->size());
 if(count>10)throw std::runtime_error("Scrum supports at most ten answer topics");
 for(size_t j=0;j<count;j++){
  const size_t q=(j+scPair+1)%count;
  const auto& topic=q<pairs.size()?pairs.at(q):decoys->at(q-pairs.size());
  o.push_back(topic.value("us","")+" · "+topic.value("keyword",""));scrumIds.push_back(int(q));
 }
 optAnswer=-1;for(size_t j=0;j<scrumIds.size();j++)if(scrumIds[j]==scPair)optAnswer=int(j);
 opts=std::move(o);optHover=0;optRects.assign(opts.size(),{-10000,-10000,0,0});optionMouseX=aimX;optionMouseY=aimY;
 for(int i=0;i<8;i++){svis("OptP"+std::to_string(i),false);svis("OptT"+std::to_string(i),false);}
 scrumDraw();
}
void Yumeno::scrumPick(int i){
 if(scPair<0||scPair>=int(stage["pairs"].size()))return;
 auto& opponent=stage["pairs"][scPair];int chosen=i>=0&&i<int(scrumIds.size())?scrumIds[i]:-1;bool correct=chosen==scPair;
 scrumChosenV4[scPair]=chosen;scrumConfirmedV4[scPair]=correct;
 /* V3(영상 1번 46~48초·98.5초) : 맞는 아군을 고르면 그 아군이 받아친다(큰 글). 틀리면 받아치지 않고 다음 상대 발언. 피해·반응은 한 바퀴가 끝난 뒤(scrumNext) */
 scv3Lines=Json::array();
 if(correct){if(v4TaskActive)pv4::Action(presentationV4,"scrum_link",640,300);else sfx("v3se_361");scv3Resp=scPair;if(scPair<int(scv3Revealed.size()))scv3Revealed[scPair]=true;scv3RespT=0;
  for(auto key:{"success","afterSuccess"})for(auto& row:opponent.value(key,Json::array()))if(row.value("type",std::string())=="say"&&!row.value("text",std::string()).empty())scv3Lines.push_back(row); /* 대화창 대신 같은 큰 글로 */
  scrumWait=4.f+2.8f*float(scv3Lines.size());}
 else{scv3Resp=-1;scrumWait=.35f;}
 ++scPair;
}
void Yumeno::anaSlots(){
 svis("Slots",false);
 if(anaChars.size()>20)throw std::runtime_error("anagram requires more than20 authored answer slots");
 float step=trialui::anaStep(int(anaChars.size()));for(int i=0;i<20;i++){auto id="AnaSlot"+std::to_string(i);bool on=i<int(anaChars.size());svis(id,on);svis("AnaSlotBack"+std::to_string(i),on);if(!on)continue;UI::SetPosition(this,"anagramv4","AnaSlotBack"+std::to_string(i),{52+i*step,24});UI::SetSize(this,"anagramv4","AnaSlotBack"+std::to_string(i),{step-2,56});stext(id,i<anaFilled?anaChars[i]:"?");UI::SetPosition(this,"anagramv4",id,{52+i*step,24});UI::SetSize(this,"anagramv4",id,{step,56});UI::SetFontSize(this,"anagramv4",id,std::min(42.f,step));UI::SetColor(this,"anagramv4",id,i==anaFilled?Color{1,.93f,.19f,1}:Color{.45f,.65f,.75f,1});}
}
void Yumeno::anagramOrbDraw(int i,float x,float y,float scale,bool lit){
 auto n=std::to_string(i);UI::SetPosition(this,"anagramv4","AnaBall"+n,{x,y});
 // Text has top-aligned 1.3 line height: centre its52px line in the84px orb.
 UI::SetPosition(this,"anagramv4","Orb"+n,{x,y+16*scale});
 if(anagramScaleV4[i]!=scale){anagramScaleV4[i]=scale;for(auto p:{"Orb","AnaBall"})UI::SetScale(this,"anagramv4",p+n,{scale,scale});}
 if(anagramLitV4[i]!=int(lit)){anagramLitV4[i]=int(lit);svis("Orb"+n,lit);UI::SetTexture(this,"anagramv4","AnaBall"+n,lit?"Assets/Art/ui/anagram_orb_"+std::to_string(i%4)+".svg":"Assets/Art/ui/anagram_orb_dark.svg");}
}
// 같은 색으로 이어진 블록 무리
std::vector<int> Yumeno::mineGroup(int start)const{return mineV4.group(start);}
bool Yumeno::itemOpen(int item)const{for(auto& image:mineV4.images)if(image.id==item){for(int cell:image.cells)if(mineV4.cells[cell]>=0)return false;return true;}return false;}
void Yumeno::mineClick(int cell){
 int oldTime=mineV4.time;auto result=mineV4.click(cell);if(result==trialv4::Result::Selected){sfx("ui_select");return;}
 if(mineV4.time<oldTime){sfx("v3se_395");if(!v4TaskActive)smsg("단독 제거 — 10초 소모",.6f);}else if(result==trialv4::Result::Removed)sfx("v3se_394");
 if(v4TaskActive&&result==trialv4::Result::Removed)mineBurstCellsV4.clear();
 for(size_t i=0;i<cells.size();i++)if(cells[i]!=mineV4.cells[i]){
  const int previous=cells[i];
  cells[i]=mineV4.cells[i];
  const auto id="Cell"+std::to_string(i);
  if(v4TaskActive){
   mineTileMotionV4[i]={previous,0};
   mineTileStyleV4[i]=-1;
   if(cells[i]<0){
    mineBurstCellsV4.push_back(int(i));
    std::string texture=trialui::MINE_TILES[previous];
    texture.insert(texture.size()-4,"_break");
    UI::SetTexture(this,"minev4",id,texture);
   }
  }else{
   svis(id,cells[i]>=0);
   if(cells[i]>=0)UI::SetTexture(this,"minev4",id,trialui::MINE_TILES[cells[i]]);
  }
 }
}
// 원근 : 깊이 d(0 먼 곳 ~ 1 가까운 곳), 차선 lane(0~2, 소수 = 차선 경계)
static void taxiProject(float lane,float d,float& x,float& y,float& scale){
 float e=d*d;float w=27+(413-27)*e;x=640+(lane-1)*w;y=250+470*e;scale=.25f+.95f*e;
}
void Yumeno::taxiShow(){
 auto& q=stage["questions"][taxiQ];
 taxiChars.clear();for(auto& g:debate::glyphs(q.value("q","")))if(g!=" "&&g!="?"&&g!="!"&&g!=",")taxiChars.push_back(g);
 taxiGot=0;taxiPhase=0;cubeD=-1;rivalD=-1;paxD=-1;taxiQText();
 for(int i=0;i<3;i++)svis("Lane"+std::to_string(i),false);
}
void Yumeno::taxiQText(){
 std::string t;int k=0;
 for(auto& g:debate::glyphs(stage["questions"][taxiQ].value("q",""))){bool keep=g!=" "&&g!="?"&&g!="!"&&g!=",";t+=!keep?g:(k<taxiGot?g:std::string("□"));if(keep)k++;}
 stext("TaxiQ",t);svis("TaxiQ",true);
}
void Yumeno::updateTaxi(float delta){
 float speed=(Input::IsKeyDown("Shift")&&debate.focus>0?.5f:1.f);
 if(Input::IsKeyDown("Shift"))debate.focus=std::max(0.f,debate.focus-20*delta);else debate.focus=std::min(maximumFocus(),debate.focus+6*delta);
 if(pressed("a"))taxiLane=std::max(0,taxiLane-1);if(pressed("d"))taxiLane=std::min(2,taxiLane+1);
 carX+=( (640+(taxiLane-1)*360.f) -carX)*std::min(1.f,delta*12); // 부드럽게 차선 이동
 UI::SetPosition(this,trialui::ID,"Car",{carX,640});
 roadT+=delta*speed*1.4f;
 for(int i=0;i<8;i++){float d=std::fmod(roadT+i*.125f,1.f);float x,y,sc;taxiProject(i<4?.5f:1.5f,d,x,y,sc);auto id="Dash"+std::to_string(i);svis(id,true);UI::SetPosition(this,trialui::ID,id,{x,y});UI::SetScale(this,trialui::ID,id,{sc,sc});}
 auto place=[&](const std::string& id,int lane,float d){float x,y,sc;taxiProject(float(lane),d,x,y,sc);UI::SetPosition(this,trialui::ID,id,{x,y});UI::SetScale(this,trialui::ID,id,{sc,sc});};
 const float HIT=.93f;
 // 다른 차 : 큐브와 다른 차선에서 다가온다. 부딪히면 집중력이 크게 준다(V3)
 if(rivalD<0&&std::fmod(roadT,2.6f)<delta*speed*1.4f){rivalLane=(cubeLane+1+int(roadT*7)%2)%3;rivalD=0;}
 if(rivalD>=0){rivalD+=delta*speed*.5f;place("Rival0",rivalLane,rivalD);svis("Rival0",true);
  if(rivalD>=HIT){if(rivalLane==taxiLane){debate.focus=std::max(0.f,debate.focus-30);smsg("쾅!",.5f);}rivalD=-1;svis("Rival0",false);}}
 if(taxiPhase==0){ // 글자 큐브 : 다음에 필요한 글자가 다가온다. 놓치면 다시 온다
  if(cubeD<0){cubeLane=int(debate::hash(taxiGot+taxiQ*31,9)*3)%3;cubeD=0;stext("Cube0",taxiChars[taxiGot]);}
  cubeD+=delta*speed*.55f;place("Cube0",cubeLane,cubeD);svis("Cube0",true);
  if(cubeD>=HIT){if(cubeLane==taxiLane){taxiGot++;taxiQText();if(taxiGot>=int(taxiChars.size())){taxiPhase=1;svis("Cube0",false);smsg("질문 완성!",.8f);}}cubeD=-1;}
  return;
 }
 // 손님 : 질문의 답을 든 세 사람. 정답 손님 차선으로 가서 태운다
 auto& q=stage["questions"][taxiQ];
 if(paxD<0){paxD=0;for(int i=0;i<3;i++){stext("Lane"+std::to_string(i),i<int(q["options"].size())?q["options"][i].get<std::string>():"");svis("Lane"+std::to_string(i),true);}}
 paxD+=delta*speed*.4f;for(int i=0;i<3;i++)place("Lane"+std::to_string(i),i,paxD);
 if(paxD>=HIT){
  auto ans=q.value("answer","");
  if(taxiLane<int(q["options"].size())&&q["options"][taxiLane].get<std::string>()==ans){heal();smsg("「"+ans+"」 태웠다!",1.f);taxiQ++;
   if(taxiQ>=int(stage["questions"].size())){beginScript();return;}taxiShow();}
  else{hurt();paxD=-1;}
 }
}
void Yumeno::updateTrial(float delta){
 if(v4TaskActive&&playingDebate&&cameraTime>=1)shotRecoveryV4.advance(delta,held.at("mouse0"));
 if(messageTimer>0&&(messageTimer-=delta)<=0)UI::SetVisible(this,UI_ID,"TrialMsg",false);
 if(v4TaskQueueUpdate(delta))return;
 if(v4TaskActive&&!v4TrialInputArmed){if(!Input::IsKeyDown("mouse0")&&!Input::IsKeyDown("mouse1")&&!Input::IsKeyDown("Enter")&&!Input::IsKeyDown("Space"))v4TrialInputArmed=true;return;}
 bool direct=v4TaskActive&&playingDebate,assisted=direct&&(skillOn("paranormal")||skillOn("robot_eye"));float gain=direct?aimskillsv4::directGain(skillOn("shift_down"),skillOn("shift_up")):1.f;
 aimskillsv4::Point axis{};if(direct&&debateInputArmed&&cameraTime>=1&&debateIntroTime<0){axis.x=float(Input::IsKeyDown("ArrowRight"))-float(Input::IsKeyDown("ArrowLeft"));axis.y=float(Input::IsKeyDown("ArrowDown"))-float(Input::IsKeyDown("ArrowUp"));}
 bool keyboard=axis.x!=0||axis.y!=0;auto before=aimSwayV4.desired;auto point=direct?before:aimskillsv4::Point{aimX,aimY};Vec2 m;aimPointerV4.moved=aimPointerV4.appliedPending=false;
 bool inputFrame=trialPickerOn||trialAnswerOn||(v4TaskActive&&(stageKind=="spot"||stageKind=="vote"));auto inputOffset=trialinputmotion::stageFrame(this,inputFrame);
 if(Input::GetMousePositionForCanvas({1280,720},m)){
  if(inputFrame){m.x-=inputOffset.x;m.y-=inputOffset.y;}
  bool ready=!keyboard&&debateInputArmed&&Input::IsKeyDown("Shift")&&!focusExhausted&&debate.focus>0&&cameraTime>=1&&shotRecoveryV4.ready()&&holdTime<0&&lieV4.phase==liev4::Phase::Idle;point=aimPointerV4.sample({m.x,m.y},point,assisted,aimAssistV4,ready,gain);
 }
 if(direct){if(keyboard){point=aimskillsv4::digitalAim(before,point,axis,delta,gain);aimPointerV4.digital=aimPointerV4.moved=true;aimAssistV4.active=false;}aimSwayV4.desired=point;if(aimPointerV4.appliedPending&&!keyboard)aimSwayV4.resetPhase();}else{aimX=point.x;aimY=point.y;}
 if(playingDebate&&!v4TaskActive&&debateResultTime<=0)UI::SetPosition(this,UI_ID,"Aim",{aimX-32,aimY-32});
 if(cutinTimer>0&&(cutinTimer-=delta)<=0)UI::SetVisible(this,UI_ID,"Cutin",false);
 if(stageMsgTimer>0&&(stageMsgTimer-=delta)<=0)svis("StageMsg",false);
 bool click=pressed("mouse0");bool released=!Input::IsKeyDown("mouse0")&&mouseWasDown;
 if(click){dragX=aimX;dragY=aimY;}mouseWasDown=Input::IsKeyDown("mouse0");
 enterPressed=pressed("Enter");spacePressed=pressed("Space");
 bool next=enterPressed||spacePressed||click;
 if(modeEndingInput(delta)||solutionCutinInput(delta))return;
 trialScoreTick(delta);
 drawHearts();if(stageKind=="armament"&&!inScript)armHudDraw();
 if(updateDebateIntro(delta))return;
 updateCamera(delta);
 if(restartStage){if(!v4ArmRetry()){if(v4TaskActive){v4TaskEntryHp=debate.hearts*2000;v4TaskEntryHearts=debate.hearts;}if(v4TaskActive&&(stageKind=="reasoning"||stageKind=="climax"))v4TaskLinks=0;enterStage(stageAt);trialScoreBegin();}return;}
 if(voteHostTime>0){
  if(next&&dialogueAdvance()){
   voteHostTime=0;dialogVisible(false);voteShow();optRects.clear();
   UI::SetVisible(this,"vote","InputSourceFrame",false);
   voteMonitorTime=0;sfx("sfx_tv");
  }
  return;
 }
 if(voteMonitorTime>=0){
  voteMonitorTime+=delta;
  const float move=court::smooth5(voteMonitorTime/1.45f);
  auto c=voteHostCamera;c.pitch+=27.f*move;c.y+=.36f*move;setCam(c);
  const float t=voteMonitorTime;
  const bool slate=t>=1.65f;
  const float alpha=std::clamp((t-1.65f)*6.f,0.f,1.f);
  votetvui::monitor(this,-700.f*(1.f-move),true,slate,alpha);
  if(t>=votetvui::monitorIntro){
   voteMonitorTime=-1;UI::SetVisible(this,"vote","InputSourceFrame",true);
   slotTimer=votetvui::tallySpan;voteResultShow();
  }
  return;
 }
 if(slotTimer>0||slotHold>0){
  const bool finalVote=stage.value("selectionRole",std::string())!="historical-fact-intermediate-vote";
  const float hostReturn=finalVote?.1f:0.f;
  const float fadeDuration=finalVote?.85f:0.f;
  const float fadeStart=votetvui::verdictHold+votetvui::monitorOutro+hostReturn;
  const float machineStart=fadeStart+fadeDuration;
  const float duration=machineStart+(finalVote?votetvui::verdictEnd-votetvui::verdictHold:0.f);
  if(slotTimer>0){
   slotTimer-=delta;voteResultUpdate(std::clamp(1.f-slotTimer/votetvui::tallySpan,0.f,1.f));
   if(slotTimer<=0){voteResultUpdate(1);slotHold=duration;}
  }else{
   const float raw=duration-slotHold;
   if(raw<votetvui::verdictHold){
    if(finalVote)votetvui::confetti(this,raw);
   }else if(raw<votetvui::verdictHold+votetvui::monitorOutro){
    const float turn=raw-votetvui::verdictHold;
    if(turn<delta){sfx("sfx_tv_off");votetvui::pose(this,"resultFx",-1);}
    UI::SetVisible(this,"vote","InputSourceFrame",false);
    const float move=court::smooth5((turn-.22f)/.78f);
    auto c=voteHostCamera;c.pitch+=27.f*(1-move);c.y+=.36f*(1-move);setCam(c);
    votetvui::monitor(this,-700.f*move,true,false);
   }else if(finalVote&&raw<fadeStart){
    auto& vote=votetvui::states[this];
    if(!vote.returnDialogueOpened){
     vote.returnDialogueOpened=true;
     if(chapterAt>=1&&chapterAt<=5)music("bgm_warm");
     UI::SetVisible(this,"vote","root",false);
     auto* presenter=actor("Host");
     const auto host=presenter?Scene::GetPosition(presenter):Vec3{0,3.87f,-(court::RADIUS+2.4f)};
     auto shot=voteHostCamera;
     shot.x=host.x+1.05f;shot.y=host.y+.27f;shot.z=host.z+3.05f;
     shot.yaw=14.f;shot.pitch=5.f;shot.roll=-4.f;
     setCam(shot);
     speaker=nameOf("lappy");
     line="과연 누가 검정으로 뽑혔을까? 그리고 그 선택은 맞았을까, 틀렸을까?";
     dialogVisible(true);dialoguePrepare();
     shown=float(lineLength);text("Body",dialogueText());
     return;
    }
    if(next&&dialogueAdvance()){
     dialogVisible(false);
     if(chapterAt>=1&&chapterAt<=5)music("@silence");
     slotHold=duration-fadeStart-.001f;
    }
    return;
   }else if(finalVote&&raw<machineStart){
    UI::SetVisible(this,"vote","root",true);
    UI::SetVisible(this,"vote","InputSourceFrame",false);
    UI::SetVisible(this,"vote","VoteFullMatte",true);
    UI::SetOpacity(this,"vote","VoteFullMatte",std::clamp((raw-fadeStart)/.55f,0.f,1.f));
   }else if(finalVote){
    UI::SetOpacity(this,"vote","VoteFullMatte",1.f);
    UI::SetVisible(this,"vote","root",true);
    votetvui::monitorClear(this);
    UI::SetVisible(this,"vote","InputSourceFrame",true);
    const float elapsed=raw-machineStart+votetvui::verdictHold;
    if(elapsed>=votetvui::verdictHold&&elapsed-delta<votetvui::verdictHold)sfx("sfx_machine");
    if(elapsed>=votetvui::coinStart&&elapsed-delta<votetvui::coinStart)sfx("sfx_coin");
    if(elapsed>=votetvui::closeStart&&elapsed-delta<votetvui::closeStart)sfx("sfx_bang_door");
    votetvui::verdict(this,elapsed,personIds,slotWho,nameOf(slotWho));
   }
   if((slotHold-=delta)<=0){
    UI::SetVisible(this,"vote","InputSourceFrame",true);hideVote();
    if(auto* h=actor("Host"))Scene::SetPosition(h,{0,4.6f,-(court::RADIUS+2.4f)});
    beginScript();
   }
  }
  return;
 }
 if(playingDebate){updateDebate(delta);return;}
 if(inScript){updateScript(delta,next);return;}
 auto& k=stageKind;
 if(k=="vote"){
  if(voteIntroTicks<98){voteIntroTicks+=delta*60;votetvui::pose(this,"intro",int(voteIntroTicks));return;}
  if(voteCommitTicks>=0){
   voteCommitTicks+=delta*60;
   const bool timeout=votePending==-2;const auto track=timeout?"timeout":"press";
   const int effect=trialinputmotion::bank().at("tracks").at(track).at("frames").get<int>();
   int end=effect;votetvui::pose(this,track,int(voteCommitTicks));
   if(!timeout&&votetvui::b().contains("shutters")){
    end+=votetvui::b().at("shutters").at("frames").get<int>();
    if(voteCommitTicks>=effect){
     UI::SetVisible(this,"vote","VoteCommit",false);
     votetvui::shutters(this,int(voteCommitTicks)-effect,int(personIds.size()),votePending);
    }
   }
   if(voteCommitTicks>=end){int selected=votePending;voteCommitTicks=-1;votePending=-1;if(timeout){hurt();restartStage=true;}else optionPicked(selected);}
   return;
  }
  votetvui::pose(this,"intro",-1);
 }
 if(k=="spot"&&v4TaskActive&&spotLockTicks>=0){
  trialinputmotion::questionPose(this,true,false,delta);spotLockTicks+=delta*60;
  if(spotLockTicks<18){trialinputmotion::spotPose(this,int(spotLockTicks),spotLockX,spotLockY);return;}
  UI::SetVisible(this,trialinputmotion::widget("spot"),"Lock",false);
  const auto image=spotlayoutv4::imageRect(v4Task.value("taskId",std::string()));
  if(trialinputmotion::bank().contains("spotExit")&&!trialinputmotion::spotExit(this,spotLockTicks-18,image))return;
  int selected=spotPending;spotLockTicks=-1;optionPicked(selected);return;
 }
 if(trialAnswerInput(delta,click))return;
 if(trialPickerInput(delta,click))return;
 if(v4MineUpdate(delta,click)||v4LieUpdate(delta,click)||v4ShowdownUpdate(delta,click,released)||v4ComicUpdate(delta,click))return;
 if(armamentPresentationInput(delta))return;
 if(k=="scrum"&&scrumT>=1&&scrumWait<=0){bool focus=skillFocusTick(Input::IsKeyDown("Shift"),delta);if(focus)delta*=.35f;}
 stageTime+=delta;
 if(v4TaskActive&&k=="spot"&&stageTime<1.2f&&trialinputmotion::spotOpening(this,stageTime))return;
 if(k=="vote")votetvui::clock(this,std::max(0.f,stageLimit-stageTime),stageLimit);
 if(stageLimit<900&&k!="vote"&&k!="anagram"&&k!="mindmine"&&!(k=="scrum"&&mash>=0)){float left=std::max(0.f,stageLimit-stageTime);int ms=int(left*1000);char t[16];std::snprintf(t,sizeof t,"%02d:%02d:%03d",ms/60000,ms/1000%60,ms%1000);stext("StageTimer",t);svis("StageTimer",k!="scrum");if(k=="scrum")scv3Clock(left); /* V3 시간판 */if(left<=0){hurt();restartStage=true;return;}}
 if(k=="scrum"){
  if(scv3Op>=0){scv3Op+=delta;if(scv3OpIntro(scv3Op)){stageTime=0;return;}scv3Op=-1;scv3HideAll();} /* 「의견대립」 → 증언대 */
  if(scrumT<1){ // V3 3fb720 : SE363→364→364→365 을 2초(120카운트) 간격, 이어 356·359. 앞 세 단계는 결정으로 건너뛴다
   // 화면(V3 영상 A 1:18:03~1:18:28) : 위에서 본 재판장 → 바닥 높이로 증언대를 따라가며 기둥이 솟음 → 바로 위에서 돎
   // → 높이 솟은 증언대를 아래에서 올려다보며 돎 → 암전 → 두 줄로 마주 선 통로 끝에서 왕좌 쪽
   const float total=6.6f;float prev=scrumT*total;scrumT=std::min(1.f,scrumT+delta/total);
   if(prev<5.4f&&prev>.2f&&(pressed("Enter")||click)){scrumT=std::max(scrumT,5.4f/total);prev=std::max(prev,5.39f);}
   float now=scrumT*total;static const float at[]{0,2,4,6,6,6.55f};static const char* se[]{"v3se_363","v3se_364","v3se_364","v3se_365","v3se_356","v3se_359"};
   for(int i=0;i<6;i++)if((prev<at[i]||(prev==0&&at[i]==0))&&now>=at[i])sfx(se[i]);
   auto ease=[](float u){u=std::clamp(u,0.f,1.f);return u*u*(3-2*u);};
   bool rows=now>=5.6f; // 암전 속에서 두 줄로
   scrumFormation(rows?1.f:0.f,ease((now-1.2f)/2.6f));
   float rad=court::PI/180;
   if(now<1.4f){float u=now/1.4f,y=20*u;setCam({std::sin(y*rad)*5.5f,9.f,std::cos(y*rad)*5.5f,y,-58,0});}                                   // 위에서 본 재판장
   else if(now<3.2f){float u=(now-1.4f)/1.8f,y=150+40*u;setCam({0,.55f,0,y,10+6*u,0});}                                                     // 바닥 높이에서 솟는 증언대를 따라감
   else if(now<4.4f){float u=(now-3.2f)/1.2f;setCam({0,11.f,.01f,90*u,-89,0});}                                                              // 바로 위에서 돎
   else if(now<5.6f){float u=(now-4.4f)/1.2f,y=200+50*u;setCam({0,.7f,0,y,38,6*std::sin(u*3)});}                                              // 아래에서 올려다봄
   else setCam({0,2.9f,3.9f,0,-8,0});                                                                                                          // 통로 끝 → 왕좌
   float dark=now<.35f?1-now/.35f:now<5.2f?0:now<5.4f?(now-5.2f)/.2f:now<5.8f?1:std::max(0.f,1-(now-5.8f)/.25f); /* 열쇠 장면에서 어둠으로 이어 받는다(영상 13.25초 겹쳐 바뀜) */ // 암전
   svis("ScVTunnel",dark>0);if(dark>0){UI::SetTexture(this,"scrumv4","ScVTunnel","Assets/Art/ui/result_black.svg");UI::SetSize(this,"scrumv4","ScVTunnel",{1280,720});UI::SetPosition(this,"scrumv4","ScVTunnel",{0,0});UI::SetRotation(this,"scrumv4","ScVTunnel",0);UI::SetOpacity(this,"scrumv4","ScVTunnel",dark);}
   { // 변형 중에는 스크럼 HUD 를 숨긴다(V3 : 변형이 끝난 뒤에 나온다)
    static const char* hud[]{"ScVStatementP","ScVStatement","ScVClaimInk","StageTimer"};for(auto id:hud)svis(id,false);
    for(int k=0;k<10;k++)for(auto side:{"L","R"})for(auto part:{"P","F","T"})svis(std::string("ScV")+side+part+std::to_string(k),false);
    UI::SetVisible(this,"trialvitalsv4","root",false);for(auto id:{"StatusPanel","StatusLabel"})UI::SetVisible(this,UI_ID,id,false);for(int i=0;i<10;i++)UI::SetVisible(this,UI_ID,"Star"+std::to_string(i),false);} /* V3 : 도입 동안 HUD 없음 */
   svis("ScBand",false);
   if(scrumT>=1){scv3Team=0;scv3Prev=0;}stageTime=0;return;}
  if(scv3Team>=0){scv3Team+=delta;if(scv3TeamIntro(scv3Team)){stageTime=0;return;}scv3Team=-1;scv3HideAll();scrumDraw();UI::SetVisible(this,"trialvitalsv4","root",true);} /* 주제·두 팀 → 「논의 스크럼 시작」 */
  if(scv3PushT>=0){scv3PushT+=delta;if(scv3PushCutin(scv3PushT))return;scv3PushT=-1;scv3HideAll();mash=0;scrumV4.reset(difficultyV4.action);minigameTicksV4=0;opts.clear();optRects.clear();scrumDraw();return;} /* CROUCH·BIND·SET! */
  if(scrumWait>0){scv3Respond(delta);if((scrumWait-=delta)<=0){scv3Resp=-1;scv3Focus.clear();scv3Speaker("",true);scrumNext();}return;}

 }
 // 키보드로도 고른다 : W/S 이동, Enter 확정
 if(!opts.empty()&&(k=="choice"||k=="reasoning"||k=="bullet"||k=="spot"||k=="person"||k=="vote"||k=="climax"||(k=="scrum"&&mash<0))){
  int before=optHover;bool person=k=="person"||k=="vote";
  if(pressed(person?"a":"w")||(k=="scrum"&&pressed("ArrowUp")))optHover=(optHover+int(opts.size())-1)%int(opts.size());
  if(pressed(person?"d":"s")||(k=="scrum"&&pressed("ArrowDown")))optHover=(optHover+1)%int(opts.size());
  if(k=="vote"){
   if(pressed("a")||pressed("ArrowLeft"))optHover=(before/4)*4+(before%4+3)%4;
   if(pressed("d")||pressed("ArrowRight"))optHover=(before/4)*4+(before%4+1)%4;
   if(pressed("w")||pressed("ArrowUp"))optHover=(optHover+int(opts.size())-4)%int(opts.size());
   if(pressed("s")||pressed("ArrowDown"))optHover=(optHover+4)%int(opts.size());
  }
  if(k=="spot"){ // 십자선이 마우스를 따라가고, 표식 위면 이름표
   const auto r=v4TaskActive?spotlayoutv4::imageRect(v4Task.value("taskId",std::string())):std::array<float,4>{{190,90,900,520}};
   if(v4TaskActive){
    const float dx=float(held.at("ArrowRight"))-float(held.at("ArrowLeft"));
    const float dy=float(held.at("ArrowDown"))-float(held.at("ArrowUp"));
    if(dx!=0||dy!=0){aimPointerV4.digital=true;aimX=std::clamp(aimX+dx*360*delta,r[0],r[0]+r[2]);aimY=std::clamp(aimY+dy*360*delta,r[1],r[1]+r[3]);}
   }
   float x=std::clamp(aimX,r[0],r[0]+r[2]),y=std::clamp(aimY,r[1],r[1]+r[3]);
   UI::SetPosition(this,trialui::ID,"CrossH",{r[0],y});UI::SetPosition(this,trialui::ID,"CrossV",{x,r[1]});
   if(v4TaskActive){UI::SetPosition(this,trialui::ID,"Mark0",{x,y});svis("MarkName",false);}else{int over=optionAt(aimX,aimY);svis("MarkName",over>=0);if(over>=0)stext("MarkName",opts[over]);}
  }
  int hit=click&&(!person||k=="vote")?(k=="vote"?trialinputmotion::voteAt(votetvui::x(aimX),votetvui::y(aimY)):optionAt(aimX,aimY)):-1;if(hit>=0)optHover=hit;bool voteCommit=k=="vote"&&click&&votetvui::commit(aimX,aimY);
  if(k=="person"&&click&&aimY>40&&aimY<640){if(aimX>150&&aimX<230)optHover=(optHover+int(opts.size())-1)%int(opts.size());else if(aimX>690&&aimX<770)optHover=(optHover+1)%int(opts.size());else if(aimX>230&&aimX<690)hit=optHover;} // 가운데 인물을 클릭하면 지목
  bool mouseMoved=aimX!=optionMouseX||aimY!=optionMouseY;optionMouseX=aimX;optionMouseY=aimY;
  if(!person&&k!="scrum"&&hit<0&&mouseMoved){int over=optionAt(aimX,aimY);if(over>=0&&k!="spot")optHover=over;}
  if(optHover!=before){if(v4TaskActive&&k=="climax"){for(int i=0;i<int(opts.size());i++)UI::SetColor(this,trialui::ID,"PanP"+std::to_string(i),i==optHover?Color{1,.2f,.45f,1}:Color{.4f,.4f,.45f,1});}else optionHighlight();}
  if(v4TaskActive&&k=="spot"){if(pressed("f"))spotQuestion=!spotQuestion;trialinputmotion::questionPose(this,true,spotQuestion,delta);if(click||enterPressed){spotQuestion=false;spotPending=optionAt(aimX,aimY);spotLockX=aimX;spotLockY=aimY;spotLockTicks=0;svis("Mark0",false);trialinputmotion::spotPose(this,0,aimX,aimY);sfx("v3se_305");}return;}
  if((hit>=0&&k!="vote")||enterPressed||voteCommit){if(k=="vote"){votePending=optHover;voteCommitTicks=0;sfx("v3se_368");}else optionPicked(hit>=0?hit:optHover);return;}
  if(k=="vote"&&stageLimit>0&&stageTime>=stageLimit){votePending=-2;voteCommitTicks=0;sfx("v3se_332");return;}
  if(k=="scrum"&&mash<0){scrumPairElapsedV4+=delta;if(scrumPairElapsedV4>stage["pairs"][scPair].value("duration",10.f)*(difficultyV4.logic==0?1.5f:difficultyV4.logic==1?1.2f:1.f))scrumPick(-1);}
  return;
 }
 if(k=="scrum"){
  int input=-1;if(pressed("w")||pressed("ArrowUp"))input=0;else if(pressed("d")||pressed("ArrowRight"))input=1;else if(pressed("s")||pressed("ArrowDown"))input=2;else if(pressed("a")||pressed("ArrowLeft"))input=3;
  minigameTicksV4+=delta*60;int frames=int(minigameTicksV4);minigameTicksV4-=frames;trialv4::Result outcome=trialv4::Result::None;
  if(input>=0&&frames==0){frames=1;minigameTicksV4=0;}
  int hitsBefore=scrumV4.success+scrumV4.phase*100;
  for(int n=0;n<frames;n++){auto result=scrumV4.tick(n==0?input:-1);if(result!=trialv4::Result::None)outcome=result;if(result==trialv4::Result::Complete||result==trialv4::Result::Failed)break;}
  if(scrumV4.success+scrumV4.phase*100>hitsBefore){if(auto* cam=actor("Camera"))Camera::Shake(cam,.012f,.1f);sfx("v3se_361");} /* 맞게 누를 때마다 화면이 튄다(V3 연타 단계는 전류·밀어붙임 연출, 1:19:20) */
  static const char* keys[]{"W","D","S","A"};stext("ScVKey",keys[scrumV4.direction()]);svis("ScVKey",false);scv3PushButton(scrumV4.direction(),stageTime,true);svis("StageMsg",false);
  svis("StageTimer",false); /* V3 밀기에는 초읽기 숫자가 없다(141.5~146.5초) */
  for(int s2=0;s2<2;s2++)for(int r=0;r<10;r++)for(auto suf:{"P","F","T"})svis(std::string("ScV")+(s2?"R":"L")+suf+std::to_string(r),false);
  if(UI::Mounted("scv3")){const float prog=std::clamp((scrumV4.phase+float(scrumV4.success)/trialv4::Scrum::required[scrumV4.difficulty][std::min(scrumV4.phase,4)])/5.f,0.f,1.f),dx=-540*prog*prog*(3-2*prog); /* V3 141.5→146.5초 : 밀수록 문양과 두 띠가 왼쪽으로 밀려 붉은 띠가 화면 밖으로 */for(auto s2:{"L","R"}){bool l=s2[0]=='L';scv3Box(std::string("ScArrow")+s2,(l?188.f:1092.f)+dx,624,680,105,1);scv3Box(std::string("ScArrowTail")+s2,(l?188.f:1092.f)+dx,624,680,105,1);scv3Box(std::string("ScArrowT")+s2,(l?258.f:1022.f)+dx,622,480,40,1);}UI::SetText(this,"scv3","ScArrowTL",scv3Task().value("them",std::string()));UI::SetText(this,"scv3","ScArrowTR",scv3Task().value("us",std::string()));scv3Emblem(true,stageTime,dx);} /* 141.5초 : 아래 두 팀 띠 + 가운데 문양 */
  if(outcome==trialv4::Result::Complete){scv3PushButton(0,0,false);for(auto id:{"scv3","scv3cut"})if(UI::Mounted(id))UI::Remove(this,id); /* 완전논파(엔딩 원본 타임라인)는 화면을 붙잡아 깨뜨린다 : 스크럼 V3 판은 먼저 내린다 */debate.hearts=std::max(1,(scrumHpV4+1999)/2000);sfx("v3se_347");beginModeEnding("scrum","script");return;}
  if(outcome==trialv4::Result::PhaseBack)sfx("v3se_362");
  if(outcome==trialv4::Result::PhaseAdvanced)sfx("v3se_364"); // V3 단계 통과
  if(outcome==trialv4::Result::Failed){scrumHpV4=std::max(0,scrumHpV4-(v4TaskActive?growthv4::Damage(growthV4,difficultyv4::wakDamage(5000,difficultyV4.logic)):difficultyv4::wakDamage(5000,difficultyV4.logic)));debate.hearts=(scrumHpV4+1999)/2000;sfx("v3se_316");if(scrumHpV4<=0){debate.hearts=1;hurt();scrumHpV4=debate.hearts*2000;if(restartStage)return;}scrumV4.reset(difficultyV4.action);scrumWait=1.2f;smsg("다시 맞춰 봐!",1.2f);}
  return;
 }
 if(k=="showdown"){
  auto& lines=stage["lines"];int n=int(lines.size());bool final=sdLine==n-1;
  if(final){if(pressed("e")){sdBullet=(sdBullet+1)%std::max<int>(1,int(bladeIds.size()));stext("BladeName","언령의 칼 · "+stage["options"][sdBullet].value("name",""));bladeList();}
            if(pressed("q")){sdBullet=(sdBullet+int(bladeIds.size())-1)%std::max<int>(1,int(bladeIds.size()));stext("BladeName","언령의 칼 · "+stage["options"][sdBullet].value("name",""));bladeList();}}
  sdTime+=delta;float dur=(final?6.f:3.6f)*(skillOn("showdown_time")?1.3f:1.f);
  float x=1280-(1280+700)*(sdTime/dur);
  stext("Blade",lines[sdLine].value("text",""));UI::SetPosition(this,trialui::ID,"Blade",{x,trialui::BLADE_Y});
  if(released&&std::abs(aimX-dragX)>150&&std::abs((aimY+dragY)/2-trialui::BLADE_Y)<70){
   // 베기 궤적이 발언을 지나갔는가 (발언 폭은 글자 수로 어림)
   float w=float(u8len(lines[sdLine].value("text","")))*52*.86f,a=std::min(aimX,dragX),b=std::max(aimX,dragX);
   if(b>x&&a<x+w){
    sfx("sfx_slash");
    if(!final){smsg(sdLine%2?"발전!":"베어 버린다!",.6f);sdLine++;sdTime=0;}
    else if(bladeIds[sdBullet]==stage["blade"].value("answer","")){heal();svis("Blade",false);svis("BladeName",false);smsg("베어 버린다!",1.2f);UI::SetVisible(this,UI_ID,"Cutin",true);cutinTimer=1.1f;beginScript();return;}
    else{hurt();sdTime=0;v4TaskWrong();}
   }
  }
  if(sdTime>dur){hurt();sdTime=0;v4TaskWrong();}
  return;
 }
 if(k=="armament"){
  if(v4TaskActive)svis("StageTimer",false);
  auto& lines=stage["lines"];static const char* buttons[]{"w","d","s","a"};
  auto damage=[&](){debate.hearts=std::max(1,int(std::ceil(double(armingV4.hp)*maxHearts/std::max(1,armingV4.maxHp))));if(armingV4.hp<=0){if(v4TaskActive){++retries;v4ResetHearts(maxHearts);armingV4.hp=armingV4.maxHp;restartStage=true;}else{debate.hearts=1;hurt();armingV4.hp=debate.hearts*2000;}}};
  if(armFinal>=0){
   trialv4::Result outcome=trialv4::Result::None;
   if(armPiecesV4.count==4){
    minigameTicksV4+=delta*60;int frames=int(minigameTicksV4);minigameTicksV4-=frames;
    for(int n=0;n<frames;n++){outcome=armPiecesV4.tick();if(outcome!=trialv4::Result::None)break;}
    float scale=1.3f-.8f*armPiecesV4.blend();UI::SetScale(this,trialui::ID,"ArmJoined",{scale,scale});UI::SetScale(this,trialui::ID,"ArmJoinedInk",{scale,scale});
   }else{
    for(int i=0;i<4;i++){bool hit=click&&aimX>=trialui::PIECE_LEFT[i]&&aimX<=trialui::PIECE_LEFT[i]+308.7f&&aimY>=trialui::PIECE_TOP[i]&&aimY<=trialui::PIECE_TOP[i]+56;if(!hit&&!pressed(std::to_string(i+1))&&!pressed(std::array<const char*,4>{"w","d","s","a"}[i]))continue;
     if(armPiecesV4.pick(armOrder[i])==trialv4::Result::None)break;armFinal=armPiecesV4.count;svis("Piece"+std::to_string(i),false);svis("ArmPieceBand"+std::to_string(i),false);UI::SetOpacity(this,trialui::ID,"ArmPieceKey"+std::to_string(i),.25f);sfx("v3se_021");
     const auto& answer=v4TaskActive&&chapterAt==6&&armQuestionPhase<3?taskv4::finalArmamentQuestion(stage,armQuestionPhase):stage;
     std::string joined=answer.value("finalSubject",std::string());for(int p=0;p<armPiecesV4.count;p++){if(!joined.empty())joined+=" ";joined+=answer["final"][armPiecesV4.order[p]].get<std::string>();}stext("ArmJoined",joined);UI::SetFontSize(this,trialui::ID,"ArmJoined",std::min(32.f,920.f/std::max(1,u8len(joined))));
     if(armPiecesV4.count==4)minigameTicksV4=0;break;
    }
   }
   // Wait for the complete selection's transition, then judge the permutation once.
   if(outcome==trialv4::Result::None)return;
   if(outcome==trialv4::Result::Complete&&v4TaskActive&&chapterAt==6&&armQuestionPhase<3){
    ++armQuestionPhase;armFinal=-1;armLastIntro=0;armingV4.combo=0;armingV4.tension=0;
    for(int j=0;j<4;j++)for(auto prefix:{"Piece","ArmPieceBand","ArmPieceKey"})svis(std::string(prefix)+std::to_string(j),false);
    for(auto id:{"ArmQuestion","ArmJoined","ArmQuestionInk","ArmJoinedInk"})svis(id,false);
    v4CancelInput();return;
   }
   if(outcome==trialv4::Result::Complete){debate.hearts=std::max(1,int(std::ceil(double(armingV4.hp)*maxHearts/std::max(1,armingV4.maxHp))));if(v4TaskActive)sfx("v3se_327");else{sfx("v3se_032");sfx("v3se_442");}if(v4TaskActive){armFinish=ARM_FINISH_SECONDS;gputrialhudv4::setVisible("ArmamentRoot",false);gputrialhudv4::setVisible("ArmIntroRoot",true);return;}smsg("이걸로 끝이야!",1.4f);for(auto id:{"Ring","RingCore","ArmLine","ArmQuestion","ArmJoined"})svis(id,false);for(int j=0;j<4;j++)svis("ArmPieceKey"+std::to_string(j),false);beginScript();return;}
   armingV4.finalWrong();if(v4TaskActive&&chapterAt==6){int future=0;const auto budgets=armrhythm::phaseBudgets(6);for(int q=armQuestionPhase+1;q<int(budgets.size());q++)future+=budgets[q];armingV4.opponent=future+145;}damage();sfx("v3se_404");if(restartStage)return;armFinal=-1;armLastIntro=0;armingV4.tension=10;armLine=std::max(0,int(lines.size())-1);armBeat=0;trialui::armNote(armingV4,stage,++armHits,armLine);for(int j=0;j<4;j++){svis("Piece"+std::to_string(j),false);svis("ArmPieceBand"+std::to_string(j),false);svis("ArmPieceKey"+std::to_string(j),false);}svis("ArmQuestion",false);svis("ArmJoined",false);svis("Ring",true);svis("RingCore",true);svis("ArmLine",true);stext("ArmLine",lines[armLine].get<std::string>());if(!v4TaskActive)smsg("아직 끝나지 않았어!",.9f);if(v4TaskActive){++trialResults.current.gaffe;armRhythmV4.phase=chapterAt==6?armQuestionPhase:armRhythmV4.phase;armRhythmV4.resetPhase();}
   return;
  }
  if(v4TaskActive){armamentRhythmTick(delta);return;}
  armBeat+=delta;float scale=std::max(.6f,2.2f-1.2f*(armBeat/armingV4.current.targetSeconds));UI::SetScale(this,trialui::ID,"Ring",{scale,scale});
  auto& note=armingV4.current;int oldHp=armingV4.hp;trialv4::Rating rating=trialv4::Rating::None;
  if(note.held>=0&&note.type==trialv4::NoteType::Hold){armingV4.holdSeconds+=delta;if(!Input::IsKeyDown(buttons[note.held])){int expected=note.holdFrames;rhythmJudge=int(armingV4.holdSeconds*60)-expected;rating=armingV4.release(note,note.held,rhythmJudge);}}
  else{int input=-1;for(int i=0;i<4;i++)if(pressed(buttons[i])){input=i;break;}if(spacePressed&&!v4TaskActive)input=note.button;
   if(input>=0&&!pressed("e")){int d=int(20+(note.targetSeconds-armBeat)*60);++rhythmPresses;rhythmInput=input;rhythmJudge=d;rating=armingV4.press(note,input,d);}}
  if(armBeat>note.targetSeconds+.35f&&!note.done&&note.held<0){armingV4.expire(note);rating=note.type==trialv4::NoteType::Mash?trialv4::Rating::MashFailure:trialv4::Rating::Miss;}
  armNoteDraw();
  if(armingV4.hp<oldHp){sfx("v3se_316");damage();if(restartStage)return;}
  if(note.done){
   if(rhythmRecent.size()>=8)rhythmRecent.erase(rhythmRecent.begin());
   rhythmRecent.push_back({{"note",armHits},{"type",int(note.type)},{"wanted",note.button},{"input",rhythmInput},{"presses",rhythmPresses},{"progress",note.progress},{"judge",rhythmJudge},{"rating",int(rating)},{"hp",armingV4.hp},{"opponent",armingV4.opponent}});rhythmPresses=0;rhythmJudge=0;rhythmInput=-1;
   bool hit=rating==trialv4::Rating::Critical||rating==trialv4::Rating::Hit||rating==trialv4::Rating::MashSuccess;if(hit)armVisualHit=.18f;sfx(hit?(rating==trialv4::Rating::Critical||rating==trialv4::Rating::MashSuccess?(chapterAt==6?"v3se_442":"v3se_402"):(chapterAt==6?"v3se_443":"v3se_403")):"v3se_404");if(v4TaskActive)armamentRating(rating);else smsg(rating==trialv4::Rating::Critical?"CRITICAL!":hit?"HIT!":"MISS",.35f);armBeat-=note.targetSeconds+(note.type==trialv4::NoteType::Hold?note.holdFrames/60.f:0.f);++armHits;
   int progressed=std::min(int(lines.size())-1,(armingV4.totalOpponent-armingV4.opponent)/30);if(progressed!=armLine){int previous=armLine;armLine=progressed;stext("ArmLine",lines[armLine].get<std::string>());if(v4TaskActive)v4ArmResponse(previous);}
   trialui::armNote(armingV4,stage,armHits,armLine);
  }
  if(armingV4.opponent<=0){if(v4TaskActive)v4ArmResponse(int(lines.size())-1);armFinal=0;v4ArmFinalShow();svis("Ring",false);svis("RingCore",false);if(!v4TaskActive)smsg("마지막 일격!",1.f);}
  return;
 }
 if(k=="anagram"){
  if(!stage.value("question",std::string()).empty()&&(pressed("q")||(click&&aimX>=996&&aimX<=1246&&aimY>=646&&aimY<=696))){anagramQuestionV4=!anagramQuestionV4;svis("AnaQuestion",anagramQuestionV4);stext("AnaQuestionButton",anagramQuestionV4?"Q 문제 닫기":"Q 문제 표시");click=false;}
  UI::SetPosition(this,"anagramv4","AnaAim",{aimX-18,aimY-18});
  if(anagramPresentationTick(delta))return;
  bool arrival=anagramV4.pending>=0;minigameTicksV4+=delta*60;int admitted=int(minigameTicksV4);minigameTicksV4-=admitted;float allowed=0;
  for(int i=0;i<admitted;i++){int wave=anagramLightV4.waveMode;allowed+=anagramLightV4.tick(Input::IsKeyDown("mouse1"),Input::IsKeyDown("Shift"),Input::IsKeyDown("Space"),arrival);if(v4TaskActive&&wave==1&&anagramLightV4.waveMode==2)sfx("sfx_flash");}
  debate.focus=anagramLightV4.mental/100.f;spot=anagramLightV4.radius*(2.f/3);lightX=640+anagramLightV4.waveOffset*(2.f/3)-341.3333f;
  UI::SetPosition(this,"anagramv4","AnaLight",{lightX,-2.6667f});svis("AnaSpot",spot>0);if(spot>0){UI::SetPosition(this,"anagramv4","AnaSpot",{640-spot,360-spot});UI::SetSize(this,"anagramv4","AnaSpot",{spot*2,spot*2});}
  int focusParts=int(std::ceil(debate.focus/maximumFocus()*10));if(focusParts!=anagramFocusDrawnV4){anagramFocusDrawnV4=focusParts;for(int i=0;i<10;i++)UI::SetTexture(this,"anagramv4","AnaStar"+std::to_string(i),i<focusParts?"Assets/Art/ui/hud_starOn.svg":"Assets/Art/ui/hud_starOff.svg");}
  stageTime+=arrival?-delta:allowed-delta;bool picked=false;
  for(int i=0;i<int(orbs.size());i++){
   auto& b=orbs[i];auto& orb=anagramV4.orbs[i];auto id="Orb"+std::to_string(i);
   if(!orb.flying){b.x+=b.vx*allowed;b.y+=b.vy*allowed;if(b.x<90||b.x>1190){b.x=b.x<90?1188.f:92.f;anagramV4.respawn(i);b.ch=trialui::glyph(orb.glyph);stext(id,b.ch);}if(b.y<135||b.y>560){b.y=std::clamp(b.y,135.f,560.f);b.vy=-b.vy;}
    bool lit=(b.x>lightX+682.6667f*.42f&&b.x<lightX+682.6667f*.96f)||std::hypot(b.x-640,b.y-360)<spot;anagramOrbDraw(i,b.x,b.y,1,lit);
    if(click&&!picked&&anagramV4.pending<0&&std::hypot(aimX-b.x,aimY-b.y)<42){orb.x=b.x;orb.y=b.y;orb.vx=b.vx;orb.vy=b.vy;float step=trialui::anaStep(int(anaChars.size())),tx=52+float(anagramV4.at)*step+step/2;
     if(anagramV4.pick(i,tx,52)==trialv4::Result::Selected){picked=true;sfx("v3se_384");}}
   }
  }
  // Own circular UI geometry matches the visible84px orb. Separate overlapping
  // normal orbs and reflect their normal velocity; selected flights are independent.
  for(int a=0;a<int(orbs.size());a++)for(int b=a+1;b<int(orbs.size());b++)if(!anagramV4.orbs[a].flying&&!anagramV4.orbs[b].flying){auto& x=orbs[a];auto& y=orbs[b];float dx=y.x-x.x,dy=y.y-x.y,d=std::hypot(dx,dy);if(d<84){if(d<.01f){dx=1;dy=0;d=1;}float nx=dx/d,ny=dy/d,push=(84-d)*.5f;x.x-=nx*push;x.y-=ny*push;y.x+=nx*push;y.y+=ny*push;float relative=(x.vx-y.vx)*nx+(x.vy-y.vy)*ny;if(relative>0){x.vx-=relative*nx;x.vy-=relative*ny;y.vx+=relative*nx;y.vy+=relative*ny;}}}
  int flying=anagramV4.pending;auto submittedGlyph=flying>=0?trialui::glyph(anagramV4.orbs[flying].glyph):std::string();auto result=anagramV4.advance(allowed);
  if(flying>=0){auto projected=anagramV4.position(flying);auto id="Orb"+std::to_string(flying);if(anagramV4.pending>=0)anagramOrbDraw(flying,projected[0],projected[1],projected[2],true);
   else if(result==trialv4::Result::Correct||result==trialv4::Result::Wrong){orbs[flying].ch=trialui::glyph(anagramV4.orbs[flying].glyph);stext(id,orbs[flying].ch);anagramOrbDraw(flying,orbs[flying].x,orbs[flying].y,1,false);}}
  if(result==trialv4::Result::Correct||result==trialv4::Result::Complete){anaFilled=int(anagramV4.at);anaSlots();sfx("v3se_002");anagramFeedbackStart(false,result==trialv4::Result::Complete);if(result==trialv4::Result::Complete){if(flying>=0){svis("Orb"+std::to_string(flying),false);svis("AnaBall"+std::to_string(flying),false);}return;}}
  if(result==trialv4::Result::Wrong){sfx("v3se_316");debate.hearts=(anagramV4.hp+1999)/2000;anagramFeedbackStart(true,false);if(anagramV4.hp<=0){debate.hearts=1;hurt();anagramV4.hp=debate.hearts*2000;if(restartStage)return;anagramV4.state=trialv4::Result::None;}
   if(v4TaskActive&&stage.contains("wrongText")){auto texts=stage["wrongText"];auto response=texts.value("other",std::string());if(flying>=0)for(auto& [word,text]:texts.items())if(word!="other"&&!submittedGlyph.empty()&&word.rfind(submittedGlyph,0)==0)response=text.get<std::string>();anagramWrongResponseV4=response;}
  }
  float left=std::max(0.f,stageLimit-stageTime);int ms=int(left*1000);char clock[16];std::snprintf(clock,sizeof clock,"%02d:%02d:%03d",ms/60000,ms/1000%60,ms%1000);stext("AnaTime",clock);svis("AnaTime",true);if(left<=0&&anagramV4.state!=trialv4::Result::Complete){sfx("v3se_332");++retries;restartStage=true;}
  return;
 }
 if(k=="mindmine"){
  // Undo restores only board/colors; the clock and player damage are never refunded.
  if(pressed("Backspace")&&mineV4.undo()==trialv4::Result::Rewound){sfx("v3se_004");for(size_t c=0;c<cells.size();c++)if(cells[c]!=mineV4.cells[c]){cells[c]=mineV4.cells[c];svis("Cell"+std::to_string(c),cells[c]>=0);if(cells[c]>=0)UI::SetTexture(this,"minev4","Cell"+std::to_string(c),trialui::MINE_TILES[cells[c]]);}}
  bool focus=Input::IsKeyDown("Shift")&&debate.focus>20;debate.focus=std::clamp(debate.focus+(focus?-30.f:8.f)*delta,0.f,maximumFocus());
  if(!focus){
   if(click){int col=int((aimX-trialui::CELL_X)/trialui::CELL_W),row=int((aimY-trialui::CELL_Y)/trialui::CELL_H);if(aimX>=trialui::CELL_X&&aimY>=trialui::CELL_Y&&col<trialui::COLS&&row<trialui::ROWS)mineClick(row*trialui::COLS+col);else mineV4.click(-1);}
   if(pressed("mouse1")||enterPressed){for(int i=0;i<int(mineV4.images.size());i++){float x=285+i*245.f;if(aimX<x||aimX>=x+220||aimY<430||aimY>=468)continue;
     int col=int((aimX-trialui::CELL_X)/trialui::CELL_W),row=int((aimY-trialui::CELL_Y)/trialui::CELL_H),hp=mineV4.hp;auto result=mineV4.submitAt(row*trialui::COLS+col,255); // Opaque authored nameplate only; no guessed image-alpha hit.
     if(result==trialv4::Result::Complete){debate.hearts=std::max(1,(mineV4.hp+1999)/2000);sfx("v3se_400");smsg("파냈다!",1.f);beginScript();return;}
     if(result==trialv4::Result::Wrong&&mineV4.hp<hp){sfx("v3se_316");debate.hearts=(mineV4.hp+1999)/2000;if(mineV4.hp<=0){debate.hearts=1;hurt();mineV4.hp=debate.hearts*2000;if(restartStage)return;mineV4.state=trialv4::Result::None;}}
    }}
  }
  for(size_t i=0;i<mineV4.images.size();i++)UI::SetColor(this,trialui::ID,"MineItem"+std::to_string(i),itemOpen(int(i))?Color{1,.91f,.66f,1}:Color{.4f,.35f,.3f,1});
  minigameTicksV4+=delta*60;int frames=int(minigameTicksV4);minigameTicksV4-=frames;mineV4.tick(frames);float left=mineV4.time/60.f;stext("StageTimer",std::to_string(left).substr(0,5));svis("StageTimer",true);
  if(mineV4.state==trialv4::Result::Failed){sfx("v3se_328");++retries;restartStage=true;}
  return;
 }
 if(k=="taxi"){updateTaxi(delta);return;}
 if(v4TaskActive)throw std::runtime_error("Unsupported native task update: "+k);
 beginScript(); // 모르는 단계는 대사만
}

// ── 자동 검증용 : 지금 정답이 되는 입력 ─────────────────────────
hb::Json Yumeno::autoAction(int mineTarget)const{
 using hb::Json;
 if(modeEndTimeV4>=0)return {{"kind","wait"}};
 if(trialResultOn)return {{"kind","key"},{"key",trialResultHistory?"Backspace":"Enter"}};
 if(mode!=Mode::Trial)return {{"kind","none"}};
 if(v4LogOpen)return {{"kind","key"},{"key","Backspace"}};
 if(v4QueueActive)return {{"kind","key"},{"key","Enter"}};
 if(v4TaskActive&&stageKind=="lie"){if(debateResultTime>0||optRects.empty())return {{"kind","wait"}};const auto& r=optRects[0];return {{"kind","hold-target"},{"key","Space"},{"x",std::clamp(r[0]+r[2]/2,20.f,1260.f)},{"y",std::clamp(r[1]+r[3]/2,30.f,690.f)},{"seconds",.55}};}
 if(debateIntroTime>=0)return {{"kind","wait"}};
 if(playingDebate)return {{"kind","debate"}};
 if(inScript)return {{"kind","key"},{"key","Enter"}};
 if(voteHostTime>0||voteMonitorTime>=0||slotTimer>0||slotHold>0)return {{"kind","wait"}};
 if(trialPickerOn){if(trialPickerPending>=0)return {{"kind","wait"}};return {{"kind","key"},{"key",optHover==optAnswer?"Enter":stageKind=="bullet"?"s":"d"}};}
 auto& k=stageKind;
 if(v4TaskActive&&k=="showdown"&&stage.contains("showdownV4"))return v4ShowdownAuto();
 if(v4TaskActive&&k=="climax")return v4ComicAuto();
 auto sourceOffset=trialAnswerOn||(v4TaskActive&&(k=="spot"||k=="vote"))?trialinputmotion::inset():Vec2{0,0};
 auto optClick=[&](int i){auto& r=optRects[i];return Json{{"kind","click"},{"x",r[0]+r[2]/2+sourceOffset.x},{"y",r[1]+r[3]/2+sourceOffset.y}};};
 if(v4TaskActive&&k=="spot"){const auto image=spotlayoutv4::imageRect(v4Task.value("taskId",std::string()));for(auto& r:stage["regions"])if(r.value("id","")==stage.value("answerRegionId","")){float x=0,y=0;for(auto& p:r["polygon"]){x+=p[0].get<float>();y+=p[1].get<float>();}return {{"kind","click"},{"x",image[0]+image[2]*x/r["polygon"].size()+sourceOffset.x},{"y",image[1]+image[3]*y/r["polygon"].size()+sourceOffset.y}};}}
 if(k=="bullet"&&optAnswer/8!=optHover/8)return {{"kind","key"},{"key","s"}};
 if(k=="person"&&optAnswer>=0)return optHover!=optAnswer?Json{{"kind","key"},{"key","d"}}:Json{{"kind","key"},{"key","Enter"}};
 if(k=="scrum"&&(scv3Op>=0||scv3Team>=0||scv3PushT>=0))return Json{{"kind","wait"}}; /* V3 연출 중 */
 if(k=="scrum"&&mash<0&&scrumT>=1&&scrumWait<=0&&optAnswer>=0)return Json{{"kind","key"},{"key",optHover==optAnswer?"Enter":"s"}};
 if(k=="vote"&&optAnswer>=0&&optAnswer<int(optRects.size())&&optHover==optAnswer)return {{"kind","key"},{"key","Enter"}};
 if((k=="choice"||k=="reasoning"||k=="bullet"||k=="spot"||k=="person"||k=="vote"||k=="climax")&&optAnswer>=0&&optAnswer<int(optRects.size()))return optClick(optAnswer);
 if(k=="scrum"){if(scrumT<1||scrumWait>0)return Json{{"kind","wait"}};static const char* keys[]{"w","d","s","a"};return Json{{"kind","key"},{"key",keys[scrumV4.direction()]}};}
 if(k=="showdown"){
  int n=int(stage["lines"].size());bool final=sdLine==n-1;
  if(final&&bladeIds[sdBullet]!=stage["blade"].value("answer",""))return {{"kind","key"},{"key","e"}};
  float dur=final?6.f:3.6f;float x=1280-(1280+700)*(sdTime/dur);
  if(x>1100||x<-200)return {{"kind","wait"}};
  float w=float(u8len(stage["lines"][sdLine].value("text","")))*52*.86f;
  float a=std::max(20.f,x-40),b=std::min(1260.f,x+w+40);
  return {{"kind","drag"},{"x0",a},{"x1",b},{"y",trialui::BLADE_Y}};
 }
 if(k=="armament"){
  if(armIntro>0||armLastIntro>0||armFinish>0)return {{"kind","wait"}};
  if(armFinal>=4)return {{"kind","wait"}};
  if(v4TaskActive&&armFinal<0)return armamentRhythmAuto();
  if(armFinal>=0){for(int i=0;i<4;i++)if(armOrder[i]==armFinal)return {{"kind","key"},{"key",std::array<const char*,4>{"w","d","s","a"}[i]}};}
  if(armingV4.current.type==trialv4::NoteType::Hold&&armingV4.current.held>=0)return {{"kind","release-after"},{"key",std::array<const char*,4>{"w","d","s","a"}[armingV4.current.held]},{"remaining",std::max(0.f,armingV4.current.holdFrames/60.f-armingV4.holdSeconds)}};
  float scale=2.2f-1.2f*(armBeat/armingV4.current.targetSeconds);
  static const char* keys[]{"w","d","s","a"};if(armingV4.current.type==trialv4::NoteType::Hold&&std::abs(scale-1)<.07f)return {{"kind","hold-key"},{"key",keys[armingV4.current.button]},{"seconds",armingV4.current.holdFrames/60.f}};
  return (armingV4.current.type==trialv4::NoteType::Mash&&armBeat>armingV4.current.targetSeconds-.35f&&armBeat<armingV4.current.targetSeconds+.3f)?Json{{"kind","rapid-key"},{"key",keys[armingV4.current.button]}}:std::abs(scale-1)<.07f?Json{{"kind","key"},{"key",keys[armingV4.current.button]}}:Json{{"kind","wait"},{"scale",scale}};
 }
 if(k=="anagram"){if(anagramIntroV4>0||anagramV4.pending>=0||anagramFeedbackV4>0)return {{"kind","wait"}};for(auto& b:orbs)if(!b.taken&&anaFilled<int(anaChars.size())&&b.ch==anaChars[anaFilled])return {{"kind","click"},{"x",b.x},{"y",b.y}};}
 if(k=="mindmine"){
  const minelayoutv4::Board mineLayout(mineV4.width,mineV4.height);
  const int target=mineTarget>=0?mineTarget:mineAnswer;
  if(v4TaskActive&&mineSuccessTimeV4>=0)return {{"kind","wait"}};
  if(v4TaskActive&&(minePaintAt<int(cells.size())||mineOpeningV4.active()))return {{"kind","wait"}};
  if(v4TaskActive&&itemOpen(target)){
   const auto& region=stage.at("regions").at(target);float u=0,v=0;
   if(stage.contains("mineObjects")){
    const auto& objects=stage.at("mineObjects");
    const auto object=std::find_if(objects.begin(),objects.end(),[&](const auto& row){return row.at("regionId")==region.at("id");});
    if(object==objects.end())return {{"kind","wait"}};
    const auto uv=taskv4::mineObjectAim(*object);u=uv.first;v=uv.second;
   }else{
    const auto& polygon=region.at("polygon");
    for(const auto& p:polygon){u+=p[0].get<float>();v+=p[1].get<float>();}
    u/=polygon.size();v/=polygon.size();
   }
   const float x=mineLayout.left+mineLayout.width*u,y=mineLayout.top+mineLayout.height*v;
   if(std::abs(aimX-x)<2&&std::abs(aimY-y)<2)return {{"kind","key"},{"key","Enter"}};
   return {{"kind","move"},{"x",x},{"y",y}};
  }
  if(!v4TaskActive&&itemOpen(mineAnswer)){float x=395+mineAnswer*245.f;if(std::abs(aimX-x)<90&&aimY>=430&&aimY<468)return {{"kind","key"},{"key","Enter"}};return {{"kind","click"},{"x",x},{"y",450}};}
  int best=-1;std::set<int> targets;for(auto& image:mineV4.images)if(image.id==target)for(int cell:image.cells)if(cells[cell]>=0){targets.insert(cell);if(best<0)best=cell;}
  // The QA input plan must play the actual colour puzzle. Repeatedly paying
  // the isolated-tile penalty can exhaust the unchanged timer at high capture
  // cost. Remove real connected groups near the target before isolated tiles.
  if(v4TaskActive){std::set<int> seen;int score=-1;for(int cell=0;cell<int(cells.size());cell++){if(cells[cell]<0||seen.count(cell))continue;auto group=mineGroup(cell);seen.insert(group.begin(),group.end());if(group.size()<2)continue;int covered=0,near=0;for(int member:group){covered+=targets.count(member);for(int n:mineV4.adjacent(member))near+=targets.count(n);}int value=covered*100+near*15+int(group.size());if((covered||near)&&value>score){score=value;best=group.front();}}}
  if(best>=0){auto group=mineGroup(best);if(group.size()>=2)best=group.front();int width=mineV4.width,height=mineV4.height;return {{"kind","click"},{"x",(v4TaskActive?mineLayout.left:trialui::CELL_X)+(best%width+.5f)*((v4TaskActive?mineLayout.width:740.f)/width)},{"y",(v4TaskActive?mineLayout.top:trialui::CELL_Y)+(best/width+.5f)*((v4TaskActive?mineLayout.height:420.f)/height)}};}
 }
 if(k=="taxi"){
  int want=taxiLane;
  if(taxiPhase==0&&cubeD>=0)want=cubeLane;
  if(taxiPhase==1){auto& q=stage["questions"][taxiQ];for(size_t i=0;i<q["options"].size();i++)if(q["options"][i].get<std::string>()==q.value("answer",""))want=int(i);}
  if(taxiLane<want)return {{"kind","key"},{"key","d"}};if(taxiLane>want)return {{"kind","key"},{"key","a"}};
  return {{"kind","wait"}};
 }
 return {{"kind","wait"}};
}

// Bounded read-only diagnostics. No story text and no gameplay writes.
std::string Yumeno::RhythmStats()const{
 Json down=Json::array(),edges=Json::array();for(auto k:{"w","d","s","a"}){down.push_back(held.count(k)&&held.at(k));edges.push_back(keyEdges.count(k)&&keyEdges.at(k));}
 const auto& n=armingV4.current;return Json{{"active",v4TaskActive&&stageKind=="armament"},{"update",rhythmUpdates},{"note",armHits},{"type",int(n.type)},{"button",n.button},{"beat",armBeat},{"target",n.targetSeconds},{"progress",n.progress},{"presses",rhythmPresses},{"held",n.held},{"holdSeconds",armingV4.holdSeconds},{"down",down},{"edges",edges},{"recent",rhythmRecent}}.dump();
}
