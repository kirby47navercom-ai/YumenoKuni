#pragma once
// 학급 재판 단계 실행기 (docs/spec/15 §4, 대본 docs/design/1Nc). Yumeno.cpp 끝에서 한 번 포함한다.
// 단계 : 대사(개정·장면·인터럽트·휴정) / 논의(논스톱·패닉 → Debate.hpp) / 선택형(객관식·언령·지점·인물·투표)
//        / 클라이맥스 / 반론 쇼다운 / 논의 스크럼 / 이론 무장 / 섬광 애너그램 / 발굴 이매지네이션 / 브레인 드라이브
// 위젯 좌표는 tools/create-project.mjs 의 W_Stage 와 같다.

namespace trialui {
const char* ID="stage";
constexpr float OPT_X=290,OPT_W=700;
const float PIECE_X[4]{640,940,640,340},PIECE_Y[4]{472,362,592,362}; // 마지막 일격 조각 중심
constexpr float CELL_X=160,CELL_Y=130,CELL_W=80,CELL_H=70;constexpr int COLS=12,ROWS=6;
constexpr float BLADE_Y=300;
const char* const DECOYS[]{"가","나","다","라","마","바","사","아","자","차","카","타","파","하","소","문","기","록"};
const char* const MINE_TILES[3]{"Assets/Art/ui/mine_w.svg","Assets/Art/ui/mine_p.svg","Assets/Art/ui/mine_y.svg"};
}

// ── 위젯 도우미 ──────────────────────────────────────────────
void Yumeno::stext(const std::string& id,const std::string& v){auto& c=stexts[id];if(c==v&&!c.empty())return;c=v;UI::SetText(this,trialui::ID,id,v);}
void Yumeno::svis(const std::string& id,bool v){auto it=svisible.find(id);if(it!=svisible.end()&&it->second==v)return;svisible[id]=v;UI::SetVisible(this,trialui::ID,id,v);}
void Yumeno::sclear(){for(auto& [id,v]:svisible)if(v){UI::SetVisible(this,trialui::ID,id,false);v=false;}}
void Yumeno::smsg(const std::string& v,float seconds){stext("StageMsg",v);svis("StageMsg",true);stageMsgTimer=seconds;}
std::string Yumeno::nameOf(const std::string& slug)const{for(auto& [k,v]:slugs)if(v==slug)return k;return slug;}

// 디버그 HUD : 논의 전용 요소만 끄고 발언력·집중은 계속 보인다
void Yumeno::debateHud(bool on){
 for(auto id:{"NamePanel","TrialSpeaker","Cylinder","BulletPlate","Bullet","BulletLabel","TimerPanel","Timer","VPoint"})UI::SetVisible(this,UI_ID,id,on);
 UI::SetVisible(this,UI_ID,"TrialBack",on);
 UI::SetVisible(this,UI_ID,"Lens",on);if(!on)UI::SetVisible(this,UI_ID,"StartBand",false);
 if(!on){drawGlyphs("M",48,{});drawGlyphs("N",26,{});}
}
void Yumeno::drawHearts(){
 if(shownHearts==debate.hearts)return;shownHearts=debate.hearts;
 for(int k=0;k<10;k++)UI::SetTexture(this,UI_ID,"Heart"+std::to_string(k),k<debate.hearts*2?"Assets/Art/ui/hud_heartOn.svg":"Assets/Art/ui/hud_heartOff.svg");
}
// 발언력 : 단계 실패 시 감소, 0이면 그 단계 처음부터(V3 : 같은 지점 재도전 + 점수 감점)
void Yumeno::hurt(){
 sfx("sfx_wrong");
 if(--debate.hearts<=0){debate.hearts=5;retries++;smsg("발언력이 바닥났어요… 다시!",1.6f);restartStage=true;return;}
 smsg("아야! 틀렸어요~!",1.f);
}
void Yumeno::heal(){sfx("sfx_correct");debate.hearts=std::min(5,debate.hearts+1);}

// ── 카메라 : 화자 자리로 돌고, 도착하면 화자를 UI 층으로 옮긴다 ─────────────
void Yumeno::focusSpeaker(const std::string& slug,const std::string& texture){
 if(slug=="lappy"){ // 래피는 증언대가 아니라 왕좌 : 카메라를 왕좌 쪽으로 돌리고 3D 래피의 그림만 바꾼다
  if(auto* h=actor("Host"))if(!texture.empty())Components::SetString(h,"SpriteRenderer","texture",texture);
  UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
  if(speakerSeat!=-2){pitchFrom=cameraPitch;speakerSeat=-2;cameraFrom=cameraAngle;cameraTo=180;cameraTime=0;}
  return;
 }
 if(!texture.empty())UI::SetTexture(this,UI_ID,"Portrait",texture);
 int seat=court::seatOf(slug);
 if(seat<0)return;
 if(seat==speakerSeat&&cameraTime>=1)return;
 if(cameraTime<1&&seat==speakerSeat)return;
 if(auto* a=actor("Seat"+std::to_string(seat)))if(!texture.empty()&&seatTexture[seat]!=texture){Components::SetString(a,"SpriteRenderer","texture",texture);seatTexture[seat]=texture;}
 pitchFrom=cameraPitch;speakerSeat=seat;cameraFrom=cameraAngle;cameraTo=court::seatAngle(seat);cameraTime=0;
 UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
}
void Yumeno::updateCamera(float delta){
 if(cameraTime>=1)return;
 cameraTime=std::min(1.f,cameraTime+delta/.45f);
 float t=cameraTime<.5f?4*cameraTime*cameraTime*cameraTime:1-std::pow(-2*cameraTime+2,3)/2; // 가속·감속
 float pitchTo=speakerSeat==-2?24.f:0.f;cameraPitch=pitchFrom+(pitchTo-pitchFrom)*t;if(cameraTime>=1)pitchFrom=pitchTo;
 cameraAngle=court::turn(cameraFrom,cameraTo,t);placeCamera(cameraAngle);
 if(cameraTime>=1&&speakerSeat>=0){
  auto r=court::speakerRect(); // 3D 입상과 정확히 같은 자리·크기 → 겹쳐도 바뀌어 보이지 않는다
UI::SetPosition(this,UI_ID,"Portrait",{r.x,r.y});UI::SetSize(this,UI_ID,"Portrait",{r.w,r.h});UI::SetVisible(this,UI_ID,"Portrait",true);
  auto p=court::podiumRect();UI::SetPosition(this,UI_ID,"SpeakerPodium",{p.x,p.y});UI::SetSize(this,UI_ID,"SpeakerPodium",{p.w,p.h});UI::SetVisible(this,UI_ID,"SpeakerPodium",true);
 }
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

// ── 재판 진행 ────────────────────────────────────────────────
void Yumeno::startTrial(){
 stages=trials["stages"];
 debate=debate::State{};debate.hearts=5;shownHearts=-1;
 mode=Mode::Trial;dialogVisible(false);
 for(auto id:{"Title","Backdrop","Portrait"})UI::SetVisible(this,UI_ID,id,false);
 UI::SetVisible(this,UI_ID,"Trial",true);UI::SetVisible(this,UI_ID,"CourtDim",true);
 if(!stageShown){UI::Show(this,"Assets/UI/Stage.hbwidget.json",trialui::ID);stageShown=true;}
 setupCourt();
 enterStage(0);
}
void Yumeno::endTrial(){
 mode=Mode::Title;debate=debate::State{};sclear();dialogVisible(false);
 for(auto id:{"Trial","TrialBack","SpeakerPodium","Portrait","CourtDim"})UI::SetVisible(this,UI_ID,id,false);
 UI::SetVisible(this,UI_ID,"Backdrop",true);
 if(flowOn){trialDone();return;}
 UI::SetVisible(this,UI_ID,"Title",true);
}
void Yumeno::enterStage(int i){
 restartStage=false;sclear();dialogVisible(false);debateHud(false);playingDebate=false;
 UI::SetPosition(this,trialui::ID,"StageTimer",{1040,656}); // 객관식은 모래시계 아래로 옮긴다
 stageAt=i;
 if(i>=int(stages.size())){endTrial();return;}
 stage=stages[i];stageKind=stage.value("kind","scene");stageTime=0;optStep=0;sdLine=0;scPair=0;mash=-1;armLine=0;armHits=0;armFinal=-1;taxiQ=0;taxiLane=1;taxiDist=0;anaFilled=0;
 auto& k=stageKind;
 { // 단계별 BGM (docs/spec/16 §5, 15 §3)
  static const std::map<std::string,std::string> cue{{"nonstop","bgm_trial_nonstop"},{"panic","bgm_trial_panic"},{"scrum","bgm_trial_scrum"},{"showdown","bgm_trial_showdown"},{"armament","bgm_trial_armament"},
   {"mindmine","bgm_trial_mindmine"},{"taxi","bgm_trial_taxi"},{"anagram","bgm_trial_anagram"},{"climax","bgm_trial_climax"},{"vote","bgm_trial_vote"}};
  auto it=cue.find(k);music(it!=cue.end()?it->second:"bgm_trial_main");
 }
 if(k=="opening"||k=="scene"){beginScript();return;}
 if(k=="interrupt"){smsg("반론!",1.2f);beginScript();return;}
 if(k=="intermission"){smsg("휴정",1.4f);try{Save::Write(SAVE_SLOT,Json{{"trial",trialKey},{"stage",i}});}catch(const std::exception&){}beginScript();return;}
 if(k=="nonstop"||k=="panic"){
  for(auto& d:trials["debates"])if(d.value("id","")==stage.value("id","")){startDebate(d);return;}
  finishStage();return;
 }
 setupPlay();
}
void Yumeno::finishStage(){enterStage(stageAt+1);}

// 대사 재생 (단계 뒤 연출 / 대사만 있는 단계)
void Yumeno::beginScript(){
 scriptLines.clear();for(auto& l:stage["script"])scriptLines.push_back(l);
 scriptAt=-1;inScript=true;sclear();debateHud(false);
 if(stageMsgTimer>0)svis("StageMsg",true);
 nextScriptLine();
}
void Yumeno::nextScriptLine(){
 if(++scriptAt>=int(scriptLines.size())){inScript=false;dialogVisible(false);finishStage();return;}
 auto& l=scriptLines[scriptAt];
 auto who=l.value("speaker","");auto base=baseName(who);
 line=l.value("text","");
 bool monologue=who.find("독백")!=std::string::npos;
 bool narration=base.empty()||base=="UI";
 speaker=narration||monologue?"":base;
 if(narration&&line.rfind("[UI]",0)==0)line=line.substr(5);
 UI::SetColor(this,UI_ID,"Body",monologue?Color{.62f,.84f,1,1}:narration?(line.rfind("(",0)==0?Color{.8f,.75f,.85f,1}:Color{1,.86f,.45f,1}):Color{.96f,.94f,.97f,1});
 auto slug=slugs.count(base)?slugs.at(base):"";
 if(!slug.empty()&&!monologue)focusSpeaker(slug,poseTexture(slug,l.value("emo",""),l.value("pose","")));
 dialogVisible(true);
 bool named=!speaker.empty();UI::SetVisible(this,UI_ID,"Nameplate",named);UI::SetVisible(this,UI_ID,"Name",named);UI::SetVisible(this,UI_ID,"NameHead",named);
 text("Name",speaker);text("NameHead",u8prefix(speaker,1));UI::SetColor(this,UI_ID,"NameHead",nameColor(slug));text("Body","");lineLength=u8len(line);shown=0;
}
void Yumeno::updateScript(float delta,bool next){
 if(int(shown)<lineLength){shown=std::min(float(lineLength),shown+delta*45);text("Body",u8prefix(line,int(shown)));}
 bool fast=Input::IsKeyDown("Control");if(fast){skipTimer+=delta;if(skipTimer>.05f){skipTimer=0;next=true;shown=float(lineLength);}}
 if(!next)return;
 if(int(shown)<lineLength){shown=float(lineLength);text("Body",line);return;}
 nextScriptLine();
}

// ── 놀이 단계 준비 ───────────────────────────────────────────
void Yumeno::showOptions(const std::string& question,const std::vector<std::string>& o){
 opts=o;optRects.clear();optHover=0;
 auto& k=stageKind;
 bool comic=k=="climax",chips=k=="scrum",bullet=k=="bullet",choice=k=="choice",person=k=="person"||k=="vote",spot=k=="spot";
 // 공통 : 질문은 화면 아래 띠(V3 대사 자리), 화자 이름표, 조작 안내
 bool v3=choice||bullet||person||spot;
 if(v3){
  svis("Shade",true);svis("Emblem",!person&&!spot);svis("QBand",true);stext("QText",question);svis("QText",true);
  stext("Hint",person?"A/D 넘기기   Enter 지목":bullet?"W/S 고르기   Enter 제시":spot?"클릭 : 지목":"W/S 고르기   Enter 확인");svis("Hint",true);
  auto who=speaker.empty()?std::string("미오"):speaker;stext("SpkName",who);svis("SpkTag",choice);svis("SpkName",choice);
  svis("QPlate",false);svis("Question",false);
 }else{stext("Question",question);svis("QPlate",!question.empty());svis("Question",!question.empty());}
 if(choice){svis("AnswerLbl",true);svis("Hourglass",true);UI::SetPosition(this,trialui::ID,"StageTimer",{100,480});}
 if(bullet){svis("BulCyl",true);svis("BulLine",true);for(auto id:{"CardFrame","CardImg","DescBox","CardTitle","CardText"})svis(id,true);}
 for(int i=0;i<8;i++){bool on=i<int(o.size())&&!person&&!spot;auto p="OptP"+std::to_string(i),t="OptT"+std::to_string(i);svis(p,on);svis(t,on);
  if(!on)continue;
  float x=300,y=250+i*46.f,w=980,h=42;
  if(bullet){x=96;y=150+i*44.f;w=420;h=40;}
  if(comic){x=290;y=404+i*52.f;w=700;h=46;}
  if(chips){w=236;h=56;x=24+i*(w+12);y=640;} // 스크럼 : 우리 편 키워드를 아래에 가로로 (V3 십자키 선택)
  optRects.push_back({x,y,w,h});
  stext(t,chips||bullet?o[i]:std::to_string(i+1)+" /  "+o[i]);
  UI::SetPosition(this,trialui::ID,p,{x,y});UI::SetSize(this,trialui::ID,p,{w,h});UI::SetTexture(this,trialui::ID,p,"Assets/Art/ui/band_off.svg");
  UI::SetPosition(this,trialui::ID,t,{x+(chips?12:bullet?22:30),y+(h-34)/2});UI::SetSize(this,trialui::ID,t,{w-(chips?24:60),34});UI::SetFontSize(this,trialui::ID,t,comic?19.f:chips?20.f:bullet?22.f:24.f);}
 if(person)personShow();
 if(spot)spotShow();
 optionHighlight();
}
// 고른 띠만 파랗게(V3). 언령 고르기는 오른쪽 카드·설명도 바꾼다
void Yumeno::bladeList(){
 for(int i=0;i<8;i++){bool on=i<int(bladeIds.size());auto p="OptP"+std::to_string(i),tt="OptT"+std::to_string(i);svis(p,on);svis(tt,on);if(!on)continue;
  float x=780+i*6.f,y=560-(int(bladeIds.size())-1-i)*34.f;
  UI::SetPosition(this,trialui::ID,p,{x,y});UI::SetSize(this,trialui::ID,p,{480,32});UI::SetTexture(this,trialui::ID,p,i==sdBullet?"Assets/Art/ui/band_on.svg":"Assets/Art/ui/band_off.svg");
  UI::SetPosition(this,trialui::ID,tt,{x+24,y+2});UI::SetSize(this,trialui::ID,tt,{440,28});UI::SetFontSize(this,trialui::ID,tt,19.f);stext(tt,stage["options"][i].value("name",""));}
}
void Yumeno::optionHighlight(){
 auto& k=stageKind;
 for(int i=0;i<int(optRects.size());i++)UI::SetTexture(this,trialui::ID,"OptP"+std::to_string(i),i==optHover?"Assets/Art/ui/band_on.svg":"Assets/Art/ui/band_off.svg");
 if(k=="bullet"&&optHover<int(bladeIds.size())){
  auto id=bladeIds[optHover];bool icon=false;for(auto& c:art["kotodama"])if(c.get<std::string>()==id)icon=true;
  svis("CardImg",icon);if(icon)UI::SetTexture(this,trialui::ID,"CardImg","Assets/Art/kotodama/"+id+".png");
  stext("CardTitle",kotodamaName(id));auto t=kotodamaText(id);stext("CardText",t.empty()?std::string(" "):t);
 }
 if(k=="person"||k=="vote")personShow();
}
// 인물 지목 : 가운데 한 명씩(전신), 번호·이름 장식, 발밑 고리
void Yumeno::personShow(){
 for(auto id:{"AccLbl","AccRing","AccFig","AccTag","AccNo","AccName","AccArrows","AccArrowR"})svis(id,true);
 if(optHover>=int(personIds.size()))return;
 auto& s=personIds[optHover];bool dead=std::find(trialDead.begin(),trialDead.end(),s)!=trialDead.end();
 UI::SetTexture(this,trialui::ID,"AccFig",dead?seatTexture[court::seatOf(s)]:"Assets/Art/sprites/"+s+"/"+s+"_C01.webp");
 stext("AccNo",std::to_string(court::seatOf(s)+1));stext("AccName",opts[optHover]);
 UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
}
// 지점 선택 : 현장 사진 액자 + 표식. 표식 자리는 보기 순서로 고르게 흩는다
void Yumeno::spotShow(){
 for(auto id:{"SpotTitle","SpotImg","SpotFrame","CrossH","CrossV"})svis(id,true);
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
  stext("PanT"+std::to_string(i),std::to_string(panels[i].value("no",0))+"  "+(hole?std::string("?"):panels[i].value("caption","")));
  UI::SetColor(this,trialui::ID,"PanP"+std::to_string(i),int(i)==blank?Color{1,.82f,.86f,1}:hole?Color{.75f,.72f,.78f,1}:Color{.96f,.94f,.91f,1});}
}
void Yumeno::setupPlay(){
 auto& k=stageKind;std::vector<std::string> o;optAnswer=-1;
 if(k=="choice"){for(auto& v:stage["options"])o.push_back(v.get<std::string>());optAnswer=stage.value("answer",0);showOptions(stage.value("question",""),o);}
 else if(k=="bullet"||k=="showdown"||k=="mindmine"){
  bladeIds.clear();for(auto& v:stage["options"]){bladeIds.push_back(v.value("id",""));o.push_back(v.value("name",""));}
  if(k=="bullet"){for(size_t i=0;i<bladeIds.size();i++)if(bladeIds[i]==stage.value("answer",""))optAnswer=int(i);showOptions(stage.value("question",""),o);}
 }
 else if(k=="spot"){for(auto& v:stage["options"])o.push_back(v.get<std::string>());for(size_t i=0;i<o.size();i++)if(o[i]==stage.value("answer",""))optAnswer=int(i);showOptions(stage.value("question",""),o);}
 else if(k=="person"||k=="vote"){
  personIds=alive(k=="person");
  {auto ans=stage.value("answer","");if(k=="vote"&&!ans.empty()&&std::find(personIds.begin(),personIds.end(),ans)==personIds.end())personIds.push_back(ans);} // 영정에게도 투표할 수 있다(3장)
  for(size_t i=0;i<personIds.size();i++){bool dead=std::find(trialDead.begin(),trialDead.end(),personIds[i])!=trialDead.end();o.push_back(nameOf(personIds[i])+(dead?" (영정)":""));if(personIds[i]==stage.value("answer",""))optAnswer=int(i);}
  if(o.size()>8){ // 8칸 : 정답이 들어가게 앞에서 자른다
   int start=std::clamp(optAnswer-3,0,int(o.size())-8);o=std::vector<std::string>(o.begin()+start,o.begin()+start+8);personIds=std::vector<std::string>(personIds.begin()+start,personIds.begin()+start+8);optAnswer-=start;}
  showOptions(k=="vote"?"범인이라고 생각하는 사람에게 투표하세요":stage.value("question",""),o);
 }
 if(k=="climax"){usedPieces.clear();filledPanel.assign(stage["panels"].size(),false);climaxOptions();}
 if((k=="showdown"||k=="armament")&&stage.contains("opponent")){auto who=stage.value("opponent","");speakerSeat=-1;focusSpeaker(who,poseTexture(who,"",who+(k=="armament"?"_T04":"_C12")));}
 if(k=="showdown"){sdBullet=0;sdTime=0;stext("BladeName","언령의 칼 · "+(bladeIds.empty()?std::string():stage["options"][0].value("name","")));svis("BladeName",true);svis("Blade",true);
  auto who=stage.value("opponent","");svis("SdFace",true);UI::SetTexture(this,trialui::ID,"SdFace","Assets/Art/cutin/"+who+"_2.webp");
  UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
  stext("SpkName",nameOf(who));svis("SpkTag",true);svis("SpkName",true);bladeList();}
 if(k=="scrum"){scrumT=0;scrumWait=0;svis("ScBand",true);UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);scrumNext();}
 if(k=="armament"){svis("ArmLine",true);svis("Ring",true);svis("RingCore",true);stext("ArmLine",stage["lines"][0].get<std::string>());armBeat=0;
  auto who=stage.value("opponent","");svis("AccFig",true);UI::SetTexture(this,trialui::ID,"AccFig","Assets/Art/figure/"+who+".webp");
  svis("ArmFace",true);UI::SetTexture(this,trialui::ID,"ArmFace","Assets/Art/cutin/mio_3.webp");
  UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);
  stext("SpkName",nameOf(who));svis("SpkTag",true);svis("SpkName",true);UI::SetPosition(this,trialui::ID,"SpkTag",{30,26});UI::SetPosition(this,trialui::ID,"SpkName",{52,34});}
 if(k=="anagram"){
  anaChars=debate::glyphs(stage.value("answer",""));orbs.clear();
  std::vector<std::string> pool=anaChars;
  for(auto d:trialui::DECOYS){if(pool.size()>=std::max<size_t>(10,anaChars.size()+2))break;if(std::find(anaChars.begin(),anaChars.end(),d)==anaChars.end())pool.push_back(d);}
  for(size_t i=0;i<pool.size()&&i<14;i++){Orb b;b.ch=pool[i];b.x=150+debate::hash(int(i),1)*980;b.y=140+debate::hash(int(i),2)*400;b.vx=(debate::hash(int(i),3)-.5f)*160;b.vy=(debate::hash(int(i),4)-.5f)*120;orbs.push_back(b);stext("Orb"+std::to_string(i),b.ch);svis("Orb"+std::to_string(i),true);}
  stext("Question",stage.value("question",""));svis("QPlate",true);svis("Question",true);svis("Slots",true);svis("Light",true);lightX=-300;anaSlots();
 }
 if(k=="mindmine"){
  cells.assign(trialui::COLS*trialui::ROWS,0);loneHits.assign(cells.size(),0);
  for(size_t i=0;i<cells.size();i++)cells[i]=int(debate::hash(int(i),7)*3)%3;
  for(size_t i=0;i<cells.size();i++)svis("Cell"+std::to_string(i),true);
  mineAnswer=0;for(size_t i=0;i<bladeIds.size();i++)if(bladeIds[i]==stage.value("card",""))mineAnswer=int(i);
  { // 블록 아래 그림 : 장의 재판장 배경 + 보물 자리에 언령 카드 그림(없으면 이름표만)
   auto art=Data::Get("Assets/Data/art.json");std::string bg="Assets/Art/bg/trial_room.webp";
   for(auto& b:art["backgrounds"])if(stage.value("image","").find(b.get<std::string>())!=std::string::npos)bg="Assets/Art/bg/"+b.get<std::string>()+".webp";
   UI::SetTexture(this,trialui::ID,"MineBg",bg);svis("MineBg",true);
   for(int i=0;i<3;i++){bool on=i<int(o.size());svis("MineItem"+std::to_string(i),on);if(!on)continue;stext("MineItem"+std::to_string(i),o[i]);
    bool icon=false;for(auto& c:art["kotodama"])if(c.get<std::string>()==bladeIds[i])icon=true;
    if(icon){UI::SetTexture(this,trialui::ID,"MineIcon"+std::to_string(i),"Assets/Art/kotodama/"+bladeIds[i]+".png");svis("MineIcon"+std::to_string(i),true);}}
  }
  stext("Question",stage.value("question",""));svis("QPlate",true);svis("Question",true);
  for(size_t i=0;i<cells.size();i++)UI::SetTexture(this,trialui::ID,"Cell"+std::to_string(i),trialui::MINE_TILES[cells[i]]);
  stageLimit=120;
 }
 if(k=="taxi"){svis("Road",true);svis("Car",true);carX=640;taxiLane=1;roadT=0;taxiShow();}
 if(k=="showdown"||k=="armament"||k=="scrum"||k=="anagram"||k=="taxi")stageLimit=k=="armament"||k=="taxi"?999:90; // 브레인 드라이브는 시간 대신 집중력(다른 차와 부딪히면 감소)
 if(k!="mindmine"&&k!="showdown"&&k!="armament"&&k!="scrum"&&k!="anagram"&&k!="taxi")stageLimit=999;
}

// ── 단계별 갱신 ─────────────────────────────────────────────
void Yumeno::optionPicked(int i){
 if(i<0)return;
 if(i!=optAnswer){hurt();return;}
 heal();
 if(stageKind=="climax"){
  usedPieces.push_back(pieceIds[i]);filledPanel[climaxBlank]=true;
  smsg("맞았어!",.6f);climaxOptions();
  if(climaxBlank<0){smsg("이게 사건의 전부야!",1.4f);beginScript();}
  return;
 }
 if(stageKind=="scrum"){scrumPick(i);return;}
 smsg(stageKind=="vote"?"투표 완료":"정답!",.8f);beginScript();
}
// 스크럼 배치 : 상대 편은 왼쪽 줄, 우리 편은 오른쪽 줄. 나머지 자리는 잠시 비운다.
void Yumeno::scrumFormation(float t){
 auto& pairs=stage["pairs"];
 std::vector<std::string> them,us;
 auto add=[&](std::vector<std::string>& v,const std::string& n){auto sl=slugs.count(n)?slugs.at(n):"";if(!sl.empty()&&std::find(v.begin(),v.end(),sl)==v.end())v.push_back(sl);};
 for(auto& p:pairs){add(them,p.value("them",""));add(us,p.value("us",""));}
 if(std::find(us.begin(),us.end(),"mio")==us.end())us.insert(us.begin(),"mio");
 float e=t<.5f?2*t*t:1-std::pow(-2*t+2,2)/2;
 for(int i=0;i<16;i++){
  std::string sl=court::SEATS[i];
  float a=court::seatAngle(i)*court::PI/180;
  float cx=court::RADIUS*std::sin(a),cz=court::RADIUS*std::cos(a);           // 원래 자리
  float tx=cx,tz=cz;bool shown=true;
  auto f=std::find(them.begin(),them.end(),sl);auto g=std::find(us.begin(),us.end(),sl);
  if(f!=them.end()){tx=-1.8f;tz=-1.2f-1.7f*float(f-them.begin());}
  else if(g!=us.end()){tx=1.8f;tz=-1.2f-1.7f*float(g-us.begin());}
  else shown=false;
  float x=cx+(tx-cx)*e,z=cz+(tz-cz)*e;
  if(auto* s1=actor("Seat"+std::to_string(i))){Scene::SetPosition(s1,{x,court::SPRITE_CENTER,z});if(!shown)Components::Set(s1,"SpriteRenderer","visible",t<.05f);}
  if(auto* p1=actor("Podium"+std::to_string(i))){float k=1-court::PODIUM_INSET/court::RADIUS;Scene::SetPosition(p1,{x+(f!=them.end()?.35f:g!=us.end()?-.35f:0)*e+(cx*k-cx)*(1-e),court::PODIUM_H/2,z+(cz*k-cz)*(1-e)});if(!shown)Components::Set(p1,"SpriteRenderer","visible",t<.05f);}
 }
 // 카메라 : 원래 각도에서 통로 뒤(+Z)로 물러나 왕좌를 바라본다
 auto sh=court::shot(cameraAngle);
 if(auto* c=actor("Camera")){Scene::SetPosition(c,{sh.x+(0-sh.x)*e,sh.y+(2.1f-sh.y)*e,sh.z+(3.6f-sh.z)*e});Scene::SetRotation(c,{-6*e,sh.yaw+court::turn(0,360-sh.yaw,e)-0,0});}
}
void Yumeno::scrumNext(){
 auto& pairs=stage["pairs"];
 for(auto id:{"ScUsP","ScUsN","ScUsT"})svis(id,false);
 if(scPair>=int(pairs.size())){mash=0;stageTime=0;showOptions("",{});for(auto id:{"ScThemP","ScThemN","ScThemT"})svis(id,false);smsg("밀어붙여! Space 연타!",3.f);return;}
 auto& p=pairs[scPair];
 auto them=p.value("themText","");auto kw=p.value("keyword","");
 auto pos=them.find(kw);if(pos!=std::string::npos)them.replace(pos,kw.size(),"■■■");
 std::vector<std::string> o;scrumIds.clear();
 for(size_t j=0;j<pairs.size();j++){size_t q=(j*3+scPair)%pairs.size();o.push_back(pairs[q].value("us","")+" · "+pairs[q].value("keyword",""));scrumIds.push_back(int(q));}
 optAnswer=-1;for(size_t j=0;j<scrumIds.size();j++)if(scrumIds[j]==scPair)optAnswer=int(j);
 showOptions("",o);
 stext("ScThemN",p.value("them",""));stext("ScThemT",them);for(auto id:{"ScThemP","ScThemN","ScThemT"})svis(id,true);
 stageTime=0;
}
void Yumeno::scrumPick(int i){
 auto& p=stage["pairs"][scPair];
 stext("ScThemT",p.value("themText",""));
 stext("ScUsN",p.value("us",""));stext("ScUsT",p.value("usText",""));for(auto id:{"ScUsP","ScUsN","ScUsT"})svis(id,true);
 smsg("「"+p.value("keyword","")+"」!",.9f);
 scPair++;scrumWait=1.4f;(void)i;
}
void Yumeno::anaSlots(){
 std::string s;for(size_t i=0;i<anaChars.size();i++)s+=(int(i)<anaFilled?anaChars[i]:std::string("＿"))+" ";
 stext("Slots",s);
}
// 같은 색으로 이어진 블록 무리
std::vector<int> Yumeno::mineGroup(int start)const{
 std::vector<int> group,stack{start};std::vector<bool> seen(cells.size(),false);
 int color=cells[start];if(color<0)return group;
 while(!stack.empty()){int c=stack.back();stack.pop_back();if(seen[c]||cells[c]!=color)continue;seen[c]=true;group.push_back(c);
  int x=c%trialui::COLS,y=c/trialui::COLS;
  if(x>0)stack.push_back(c-1);if(x<trialui::COLS-1)stack.push_back(c+1);if(y>0)stack.push_back(c-trialui::COLS);if(y<trialui::ROWS-1)stack.push_back(c+trialui::COLS);}
 return group;
}
bool Yumeno::itemOpen(int item)const{ // 보물 item 은 2~3행, 4열 폭
 for(int y=2;y<=3;y++)for(int x=item*4;x<item*4+4;x++)if(cells[y*trialui::COLS+x]>=0)return false;
 return true;
}
void Yumeno::mineClick(int c){
 auto g=mineGroup(c);if(g.empty())return;
 if(g.size()<2){if(++loneHits[c]<3)return;stageTime+=5;g={c};smsg("시간 벌점!",.6f);} // 외톨이 블록은 여러 번 눌러 부순다
 std::vector<bool> gone(cells.size(),false);for(int i:g)gone[i]=true;
 for(int i:g){cells[i]=-1;svis("Cell"+std::to_string(i),false);}
 for(int i:g){int x=i%trialui::COLS,y=i/trialui::COLS;
  for(int n:{x>0?i-1:-1,x<trialui::COLS-1?i+1:-1,y>0?i-trialui::COLS:-1,y<trialui::ROWS-1?i+trialui::COLS:-1})
   if(n>=0&&!gone[n]&&cells[n]>=0){cells[n]=(cells[n]+1)%3;gone[n]=true;UI::SetTexture(this,trialui::ID,"Cell"+std::to_string(n),trialui::MINE_TILES[cells[n]]);}}
 // gone 표시는 한 번에 한 칸만 색을 바꾸려고 재사용했다
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
 if(Input::IsKeyDown("Shift"))debate.focus=std::max(0.f,debate.focus-20*delta);else debate.focus=std::min(100.f,debate.focus+6*delta);
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
 Vec2 m;if(Input::GetMousePosition(m)){aimX=m.x;aimY=m.y;}
 UI::SetPosition(this,UI_ID,"Aim",{aimX-32,aimY-32});
 if(messageTimer>0&&(messageTimer-=delta)<=0)UI::SetVisible(this,UI_ID,"TrialMsg",false);
 if(cutinTimer>0&&(cutinTimer-=delta)<=0)UI::SetVisible(this,UI_ID,"Cutin",false);
 if(stageMsgTimer>0&&(stageMsgTimer-=delta)<=0)svis("StageMsg",false);
 bool click=pressed("mouse0");bool released=!Input::IsKeyDown("mouse0")&&mouseWasDown;
 if(click){dragX=aimX;dragY=aimY;}mouseWasDown=Input::IsKeyDown("mouse0");
 enterPressed=pressed("Enter");spacePressed=pressed("Space");
 bool next=enterPressed||spacePressed||click;
 drawHearts();
 updateCamera(delta);
 if(restartStage){enterStage(stageAt);return;}
 if(playingDebate){updateDebate(delta);return;}
 if(inScript){updateScript(delta,next);return;}
 auto& k=stageKind;
 stageTime+=delta;
 if(stageLimit<900){float left=std::max(0.f,stageLimit-stageTime);int ms=int(left*1000);char t[16];std::snprintf(t,sizeof t,"%02d:%02d:%03d",ms/60000,ms/1000%60,ms%1000);stext("StageTimer",t);svis("StageTimer",true);if(left<=0){hurt();restartStage=true;return;}}
 if(k=="scrum"){
  if(scrumT<1){scrumT=std::min(1.f,scrumT+delta/1.1f);scrumFormation(scrumT);if(scrumT>=1)svis("ScBand",false);stageTime=0;return;}
  if(scrumWait>0){if((scrumWait-=delta)<=0)scrumNext();return;}
  if(mash<0&&pressed("a"))optHover=(optHover+int(opts.size())-1)%std::max<int>(1,int(opts.size()));
  if(mash<0&&pressed("d"))optHover=(optHover+1)%std::max<int>(1,int(opts.size()));
 }
 // 키보드로도 고른다 : W/S 이동, Enter 확정
 if(!opts.empty()&&(k=="choice"||k=="bullet"||k=="spot"||k=="person"||k=="vote"||k=="climax"||(k=="scrum"&&mash<0))){
  int before=optHover;bool person=k=="person"||k=="vote";
  if(pressed(person?"a":"w"))optHover=(optHover+int(opts.size())-1)%int(opts.size());
  if(pressed(person?"d":"s"))optHover=(optHover+1)%int(opts.size());
  if(k=="spot"){ // 십자선이 마우스를 따라가고, 표식 위면 이름표
   UI::SetPosition(this,trialui::ID,"CrossH",{190,std::clamp(aimY,90.f,610.f)});UI::SetPosition(this,trialui::ID,"CrossV",{std::clamp(aimX,190.f,1090.f),90});
   int over=optionAt(aimX,aimY);svis("MarkName",over>=0);if(over>=0)stext("MarkName",opts[over]);
  }
  int hit=click&&!person?optionAt(aimX,aimY):-1;if(hit>=0)optHover=hit;
  if(person&&click&&aimX>210&&aimX<710)hit=optHover; // 가운데 인물을 클릭하면 지목
  if(!person&&hit<0){int over=optionAt(aimX,aimY);if(over>=0&&k!="spot")optHover=over;}
  if(optHover!=before)optionHighlight();
  if(hit>=0||enterPressed)optionPicked(hit>=0?hit:optHover);
  if(k=="scrum"&&mash<0&&stageTime>10){hurt();scrumNext();}
  return;
 }
 if(k=="scrum"){ // 마지막 연타
  if(spacePressed)mash++;
  stext("StageMsg","밀어붙여! "+std::to_string(mash)+" / 12");svis("StageMsg",true);
  if(mash>=12){smsg("이게 우리의 답이야!",1.4f);scrumFormation(0);placeCamera(cameraAngle);beginScript();}
  else if(stageTime>4){mash=0;stageTime=0;}
  return;
 }
 if(k=="showdown"){
  auto& lines=stage["lines"];int n=int(lines.size());bool final=sdLine==n-1;
  if(final){if(pressed("e")){sdBullet=(sdBullet+1)%std::max<int>(1,int(bladeIds.size()));stext("BladeName","언령의 칼 · "+stage["options"][sdBullet].value("name",""));bladeList();}
            if(pressed("q")){sdBullet=(sdBullet+int(bladeIds.size())-1)%std::max<int>(1,int(bladeIds.size()));stext("BladeName","언령의 칼 · "+stage["options"][sdBullet].value("name",""));bladeList();}}
  sdTime+=delta;float dur=final?6.f:3.6f;
  float x=1280-(1280+700)*(sdTime/dur);
  stext("Blade",lines[sdLine].value("text",""));UI::SetPosition(this,trialui::ID,"Blade",{x,trialui::BLADE_Y});
  if(released&&std::abs(aimX-dragX)>150&&std::abs((aimY+dragY)/2-trialui::BLADE_Y)<70){
   // 베기 궤적이 발언을 지나갔는가 (발언 폭은 글자 수로 어림)
   float w=float(u8len(lines[sdLine].value("text","")))*52*.86f,a=std::min(aimX,dragX),b=std::max(aimX,dragX);
   if(b>x&&a<x+w){
    if(!final){smsg(sdLine%2?"발전!":"베어 버린다!",.6f);sdLine++;sdTime=0;}
    else if(bladeIds[sdBullet]==stage["blade"].value("answer","")){heal();svis("Blade",false);svis("BladeName",false);smsg("베어 버린다!",1.2f);UI::SetVisible(this,UI_ID,"Cutin",true);cutinTimer=1.1f;beginScript();return;}
    else{hurt();sdTime=0;}
   }
  }
  if(sdTime>dur){hurt();sdTime=0;}
  return;
 }
 if(k=="armament"){
  auto& lines=stage["lines"];
  if(armFinal>=0){ // 마지막 일격 : 조각을 순서대로 누른다
   for(int i=0;i<4;i++){
    bool hit=click&&std::abs(aimX-trialui::PIECE_X[i])<100&&std::abs(aimY-trialui::PIECE_Y[i])<32;
    if(!hit&&!pressed(std::to_string(i+1)))continue;
    if(armOrder[i]==armFinal){armFinal++;svis("Piece"+std::to_string(i),false);if(armFinal>=4){smsg("이걸로 끝이야!",1.4f);svis("Ring",false);svis("RingCore",false);svis("ArmLine",false);beginScript();return;}}
    else{hurt();armFinal=0;for(int j=0;j<4;j++)svis("Piece"+std::to_string(j),true);}
   }
   return;
  }
  armBeat+=delta;float t=armBeat/.9f;float scale=2.2f-1.2f*t; // 고리가 줄어 가운데 원(1.0)에 닿을 때 Space
  UI::SetScale(this,trialui::ID,"Ring",{scale,scale}); // 이미지 중심 기준 배율(위치 고정)
  if(spacePressed){
   if(std::abs(scale-1)<.16f){armHits++;armBeat=0;smsg("명중!",.3f);}
   else{hurt();armBeat=0;}
  }else if(scale<.75f){hurt();armBeat=0;}
  if(armHits>=3){armHits=0;armLine++;armBeat=0;
   if(armLine>=int(lines.size())){ // 갑옷이 부서졌다 → 마지막 일격
    armFinal=0;armOrder={0,1,2,3};std::rotate(armOrder.begin(),armOrder.begin()+(stageAt%3+1),armOrder.end());
    auto fin=stage["final"];for(int i=0;i<4;i++){stext("Piece"+std::to_string(i),std::to_string(i+1)+"  "+fin[armOrder[i]].get<std::string>());svis("Piece"+std::to_string(i),true);}
    svis("Ring",false);svis("RingCore",false);smsg("마지막 일격!",1.f);
   }else stext("ArmLine",lines[armLine].get<std::string>());
  }
  return;
 }
 if(k=="anagram"){
  lightX+=delta*300;if(lightX>1500)lightX=-300; // 빛의 물결이 약 6초마다 지나간다
  UI::SetPosition(this,trialui::ID,"Light",{lightX,0});
  bool focusing=Input::IsKeyDown("Shift")&&debate.focus>0;debate.focus=std::clamp(debate.focus+(focusing?-25.f:8.f)*delta,0.f,100.f);
  spot=focusing?std::min(300.f,spot+delta*260):std::max(0.f,spot-delta*400); // 집중 = 가운데서 넓어지는 섬광
  for(size_t i=0;i<orbs.size();i++){
   auto& b=orbs[i];if(b.taken)continue;
   b.x+=b.vx*delta;b.y+=b.vy*delta;if(b.x<120||b.x>1160)b.vx=-b.vx;if(b.y<130||b.y>560)b.vy=-b.vy;
   bool lit=(b.x>lightX&&b.x<lightX+260)||std::hypot(b.x-640,b.y-360)<spot;
   auto id="Orb"+std::to_string(i);UI::SetPosition(this,trialui::ID,id,{b.x,b.y});
   UI::SetColor(this,trialui::ID,id,lit?Color{1,1,1,1}:Color{.17f,.13f,.25f,1});
   if(click&&std::hypot(aimX-b.x,aimY-b.y)<42){
    if(anaFilled<int(anaChars.size())&&b.ch==anaChars[anaFilled]){b.taken=true;svis(id,false);anaFilled++;anaSlots();
     if(anaFilled>=int(anaChars.size())){smsg("「"+stage.value("answer","")+"」",1.4f);beginScript();return;}}
    else hurt();
   }
  }
  return;
 }
 if(k=="mindmine"){
  for(int i=0;i<3;i++){bool open=itemOpen(i);UI::SetColor(this,trialui::ID,"MineItem"+std::to_string(i),open?Color{1,.91f,.66f,1}:Color{.4f,.35f,.3f,1});
   if(open&&click&&aimX>180+i*320&&aimX<460+i*320&&aimY>272&&aimY<408){if(i==mineAnswer){heal();smsg("파냈다!",1.f);beginScript();return;}hurt();}}
  if(click){int cx=int((aimX-trialui::CELL_X)/trialui::CELL_W),cy=int((aimY-trialui::CELL_Y)/trialui::CELL_H);
   if(aimX>=trialui::CELL_X&&aimY>=trialui::CELL_Y&&cx<trialui::COLS&&cy<trialui::ROWS)mineClick(cy*trialui::COLS+cx);}
  return;
 }
 if(k=="taxi"){updateTaxi(delta);return;}
 beginScript(); // 모르는 단계는 대사만
}

// ── 자동 검증용 : 지금 정답이 되는 입력 ─────────────────────────
hb::Json Yumeno::autoAction()const{
 using hb::Json;
 if(mode!=Mode::Trial)return {{"kind","none"}};
 if(playingDebate)return {{"kind","debate"}};
 if(inScript)return {{"kind","key"},{"key","Enter"}};
 auto& k=stageKind;
 auto optClick=[&](int i){auto& r=optRects[i];return Json{{"kind","click"},{"x",r[0]+r[2]/2},{"y",r[1]+r[3]/2}};};
 if((k=="person"||k=="vote")&&optAnswer>=0)return optHover!=optAnswer?Json{{"kind","key"},{"key","d"}}:Json{{"kind","key"},{"key","Enter"}};
 if((k=="choice"||k=="bullet"||k=="spot"||k=="person"||k=="vote"||k=="climax"||(k=="scrum"&&mash<0&&scrumT>=1&&scrumWait<=0))&&optAnswer>=0&&optAnswer<int(optRects.size()))return optClick(optAnswer);
 if(k=="scrum")return scrumT<1||scrumWait>0?Json{{"kind","wait"}}:Json{{"kind","key"},{"key"," "}};
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
  if(armFinal>=0){for(int i=0;i<4;i++)if(armOrder[i]==armFinal)return {{"kind","key"},{"key",std::to_string(i+1)}};}
  float scale=2.2f-1.2f*(armBeat/.9f);
  return std::abs(scale-1)<.07f?Json{{"kind","key"},{"key"," "}}:Json{{"kind","wait"},{"scale",scale}};
 }
 if(k=="anagram"){for(auto& b:orbs)if(!b.taken&&anaFilled<int(anaChars.size())&&b.ch==anaChars[anaFilled])return {{"kind","click"},{"x",b.x},{"y",b.y}};}
 if(k=="mindmine"){
  if(itemOpen(mineAnswer))return {{"kind","click"},{"x",320+mineAnswer*320},{"y",340}};
  int best=-1;
  for(int y=2;y<=3&&best<0;y++)for(int x=mineAnswer*4;x<mineAnswer*4+4;x++){int c=y*trialui::COLS+x;if(cells[c]>=0){best=c;break;}}
  if(best>=0){for(size_t c=0;c<cells.size();c++)if(cells[c]>=0&&mineGroup(int(c)).size()>=2){auto g=mineGroup(int(c));if(std::find(g.begin(),g.end(),best)!=g.end()){best=int(c);break;}}
   return {{"kind","click"},{"x",trialui::CELL_X+(best%trialui::COLS)*trialui::CELL_W+40},{"y",trialui::CELL_Y+(best/trialui::COLS)*trialui::CELL_H+35}};}
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
