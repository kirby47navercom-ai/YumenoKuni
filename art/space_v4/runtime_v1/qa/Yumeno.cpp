#include "Yumeno.h"
#include "Courtroom.hpp"
#include <cstdio>
#include <array>
using namespace hb;

namespace {
const char* UI_ID="main";
const char* SAVE_SLOT="yumeno-progress-v1";
// 화자 이름(괄호 앞) → 스프라이트 폴더
const std::map<std::string,std::string> slugs{{"미오","mio"},{"레이","rei"},{"소라","sora"},{"켄","ken"},{"나나","nana"},{"리쿠","riku"},{"아카리","akari"},{"유우","yuu"},{"코토","koto"},{"사츠키","satsuki"},{"타이가","taiga"},{"린","rin"},{"쇼","sho"},{"아이","ai"},{"하루카","haruka"},{"카에데","kaede"},{"래피","lappy"}};
// emotion.json 의 표정 ID → 공통 포즈 (docs/spec/12 §1)
const std::map<std::string,std::string> poses{{"neutral","C01"},{"smile","C02"},{"surprise","C04"},{"anger","C05"},{"sad","C06"},{"worry","C09"},{"serious","C12"},{"closed","C14"},{"whisper","C10"}};
const std::map<std::string,std::string> lappyPoses{{"neutral","L01"},{"smile","L01"},{"anger","L02"},{"surprise","L03"},{"serious","L04"},{"sad","L05"},{"whisper","L06"},{"worry","L05"},{"closed","L06"}};

int u8len(const std::string& s){int n=0;for(unsigned char c:s)if((c&0xC0)!=0x80)++n;return n;}
std::string u8prefix(const std::string& s,int count){
 int n=0;size_t i=0;
 for(;i<s.size();++i)if((static_cast<unsigned char>(s[i])&0xC0)!=0x80){if(n==count)break;++n;}
 return s.substr(0,i);
}
std::string baseName(const std::string& speaker){auto p=speaker.find('(');return p==std::string::npos?speaker:speaker.substr(0,p);}
}

void Yumeno::sampleInput(){
 keyEdges.clear();
 for(auto key:{"mouse0","mouse1","Enter","Space","Tab","Backspace","Escape","Control","Shift","ArrowUp","ArrowDown","ArrowLeft","ArrowRight","a","d","w","s","q","e","g","m","c","t","y","l","1","2","3","4","5","6","7","8","9"}){
  bool now=Input::IsKeyDown(key);keyEdges[key]=now&&!held[key];held[key]=now;
 }
}
bool Yumeno::pressed(const std::string& key){auto it=keyEdges.find(key);return it!=keyEdges.end()&&it->second;}
void Yumeno::text(const std::string& id,const std::string& value){if(texts.count(id)&&texts[id]==value)return;texts[id]=value;UI::SetText(this,UI_ID,id,value);}

void Yumeno::dialogVisible(bool visible){
 for(auto id:{"DialogFrame","Nameplate","Name","NameHead","Body"})UI::SetVisible(this,UI_ID,id,visible);
 if(!visible)UI::SetVisible(this,UI_ID,"Next",false);
}

void Yumeno::message(const std::string& value,float seconds){text("TrialMsg",value);UI::SetVisible(this,UI_ID,"TrialMsg",true);messageTimer=seconds;}

static float kotodamaPlateWidth(const std::string& label){return std::max(118.f,68.f+25.f*u8len(label));}
void Yumeno::showBullet(){
 if(bullets.empty())return;
 auto label=(lie?"거짓 · ":"")+bullets[bullet].second;float width=kotodamaPlateWidth(label);
 text("Bullet",label);UI::SetSize(this,UI_ID,"BulletPlate",{width,50});UI::SetSize(this,UI_ID,"Bullet",{width-64,36});
 UI::SetTexture(this,UI_ID,"BulletPlate",lie?"Assets/Art/ui/kotodama_plate_lie.svg":"Assets/Art/ui/kotodama_plate.svg");
 UI::SetColor(this,UI_ID,"Bullet",lie?Color{.23f,.08f,.37f,1}:Color{.06f,.17f,.27f,1});
 UI::SetRotation(this,UI_ID,"Cylinder",bullet*72.f);
}


hb::Actor* Yumeno::actor(const std::string& id){auto& a=actors[id];if(!a)a=Scene::FindActorById(id);return a;}
void Yumeno::seatVisible(int seat,bool visible){for(auto prefix:{"Seat","SeatRear"})if(auto* a=actor(prefix+std::to_string(seat)))Components::Set(a,"SpriteRenderer","visible",visible);}
void Yumeno::placeCamera(float angle){
 auto s=court::shot(angle);
 setCam({s.x*(1-cameraPitch/30),s.y+cameraPitch*.02f,s.z*(1-cameraPitch/30),s.yaw,cameraPitch,0}); // 래피를 볼 때는 가운데로 물러나 올려다본다
}
void Yumeno::setCam(const court::Cam& c){
 cam=c;if(auto* a=actor("Camera")){auto r=court::engineRotation(c);Scene::SetPosition(a,{c.x,c.y,c.z});Scene::SetRotation(a,{r.x,r.y,r.z});}
 // Permanent front/rear planes: depth selects the side without re-uploading textures on turns.
 for(int i=0;i<16;i++)if(auto* a=actor("Seat"+std::to_string(i))){
  auto front=seatTexture[i],shown=front;
  if(front.find("court_figures/")!=std::string::npos||front.find("memorials/")!=std::string::npos){
   auto p=Scene::GetPosition(a);float angle=Scene::GetRotation(a).y*court::PI/180;
   if((c.x-p.x)*std::sin(angle)+(c.z-p.z)*std::cos(angle)<0)
    shown=front.substr(0,front.size()-5)+"_back.webp";
  }
  seatShownTexture[i]=shown;
  if(auto* back=actor("SeatRear"+std::to_string(i))){
   auto p=Scene::GetPosition(a),r=Scene::GetRotation(a);float angle=r.y*court::PI/180;
   Scene::SetPosition(back,{p.x-.004f*std::sin(angle),p.y,p.z-.004f*std::cos(angle)});Scene::SetRotation(back,r);
  }
 }
}
void Yumeno::courtPose(int seat,const std::string& texture){
 std::string slug=court::SEATS[seat];
 if(std::find(trialDead.begin(),trialDead.end(),slug)!=trialDead.end())return;
 auto key=texture.substr(texture.find_last_of('/')+1);auto dot=key.find_last_of('.');if(dot!=std::string::npos)key.resize(dot);
 if(!courtFigures.contains(key))key=slug;
 const auto& f=courtFigures[key];auto front=f.value("texture",std::string());
 if(seatTexture[seat]==front)return;
 seatTexture[seat]=front;seatShownTexture.erase(seat);
 for(auto prefix:{"Seat","SeatRear"})if(auto* a=actor(prefix+std::to_string(seat))){
  Components::SetString(a,"SpriteRenderer","texture",std::string(prefix)=="SeatRear"?f.value("back",front):front);
  Components::Set(a,"SpriteRenderer","width",f.value("width",1.f));Components::Set(a,"SpriteRenderer","height",f.value("height",2.3f));
  auto p=Scene::GetPosition(a);Scene::SetPosition(a,{p.x,f.value("center",1.25f),p.z});
 }
}
// 재판 시작 : 생존자는 입상, 사망자는 영정. 카메라는 첫 화자 자리에서 시작
void Yumeno::setupCourt(){
 auto court=Data::Get("Assets/Data/court.json");courtFigures=court["figures"];seatTexture.clear();seatShownTexture.clear();
 auto dead=trialDead;
 for(int i=0;i<16;i++){
  std::string slug=court::SEATS[i];bool gone=std::find(dead.begin(),dead.end(),slug)!=dead.end();
  const auto memorial=gone?court["memorials"][slug]:hb::Json::object();
  seatTexture[i]=gone?memorial.value("texture",std::string()):"Assets/Art/sprites/"+slug+"/"+slug+"_C01.webp";
  for(auto prefix:{"Seat","SeatRear"})if(auto* a=actor(prefix+std::to_string(i))){
   Components::SetString(a,"SpriteRenderer","texture",gone&&std::string(prefix)=="SeatRear"?memorial.value("back",seatTexture[i]):seatTexture[i]);
   Components::Set(a,"SpriteRenderer","height",gone?1.2f:court::SPRITE_SIZE);Components::Set(a,"SpriteRenderer","width",gone?1.2f:court::SPRITE_SIZE);
   Components::Set(a,"SpriteRenderer","visible",true);
   {auto p=Scene::GetPosition(a);Scene::SetPosition(a,{p.x,gone?1.85f:court::SPRITE_CENTER,p.z});}
   Scene::SetRotation(a,{0,court::seatAngle(i)+180,0});
  }
  if(!gone)courtPose(i,slug);
 }
 UI::SetTexture(this,UI_ID,"SpeakerPodium",court.value("podium",std::string()));
 speakerSeat=-1;cameraAngle=cameraFrom=cameraTo=0;cameraTime=1;placeCamera(0);
}

static std::pair<std::string,std::string> fontsOf(const std::string& slug);
void Yumeno::startDebate(const hb::Json& d){
 debateAt=stageAt;

 int hearts=debate.hearts,focus=debate.focus; // 발언력·집중은 재판 내내 이어짐
 debate=debate::State{};debate.focus=focus;
 int i=0;
 for(auto& l:d["lines"]){
  debate::Line x{l.value("speaker",""),l.value("text",""),l.value("kind","plain")};
  if(l.contains("weak")){x.word=l["weak"].value("word","");x.answer=l["weak"].value("answer","");x.start=l["weak"].value("start",0);x.lie=l["weak"].value("lie",false);}
  if(x.kind=="agree"&&l.contains("agree")){x.answer=l.value("agree","");x.word=x.text;x.start=0;}
  x.size=debate::sizeOf(x);
  x.motion=debate::motionOf(l.value("motion",""),x,i++,debate.lines.empty()?debate::Motion::Wave:debate.lines.back().motion);
  {auto sl=slugs.count(x.speaker)?slugs.at(x.speaker):"";auto fs=fontsOf(sl);x.spacing=debate::spacingOf(x.kind=="weak"?fs.second:x.kind=="noise"?"Gaegu":fs.first);}
  debate.lines.push_back(x);
 }
 debate.broken.assign(debate.lines.size(),false);debate.silenced.assign(debate.lines.size(),false);debate.hearts=hearts;
 bullets.clear();for(auto& b:d["bullets"])bullets.emplace_back(b.value("id",""),b.value("name",""));
 bullet=0;shownLine=-1;shownHearts=-1;shownNoise=-1;clearTimer=0;holdTime=-1;lie=lieCost=false;focusExhausted=false;shotsFired=0;resetDebateFx();
 playingDebate=true;dialogVisible(false);debateHud(true);sclear();
 debateTime=180*(skillOn("time_pct_5")?1.05f:1.f)+(skillOn("debate_time")?10.f:0.f);showBullet();
 bool panic=d.value("kind","")=="panic";
 if(panic){std::vector<std::string> who;for(auto& l:debate.lines){auto sl=slugs.count(l.speaker)?slugs.at(l.speaker):"";if(!sl.empty()&&std::find(who.begin(),who.end(),sl)==who.end()&&who.size()<3)who.push_back(sl);}
  for(int i=0;i<3;i++){bool on=i<int(who.size());for(auto id:{"PanicFig","PanicFrame","PanicName"})svis(id+std::to_string(i),on);if(!on)continue;
   UI::SetTexture(this,"stage","PanicFig"+std::to_string(i),"Assets/Art/cutin/"+who[i]+"_1.webp");stext("PanicName"+std::to_string(i),nameOf(who[i]));}
  panicWho=who;courtWide();UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"SpeakerPodium",false);}else panicWho.clear();UI::SetTexture(this,UI_ID,"StartBand",panic?"Assets/Art/ui/start_panic.svg":"Assets/Art/ui/start_nonstop.svg");UI::SetVisible(this,UI_ID,"StartBand",true);startBandTimer=1.6f;
 UI::SetVisible(this,UI_ID,"Lens",true);
 debateInputArmed=false; // Both modes require release of the click/key that entered the stage.
 if(!panic)beginDebateIntro();
}

// 인물별 논의 글꼴 (docs/spec/04 §4-3) : {평소, 감정 폭발}
static std::pair<std::string,std::string> fontsOf(const std::string& slug){
 static const std::map<std::string,std::pair<std::string,std::string>> f{
  {"mio",{"gothica1/GothicA1-Bold.ttf","blackhansans/BlackHanSans-Regular.ttf"}},{"rei",{"songmyung/SongMyung-Regular.ttf","notoserifkr/NotoSerifKR-VF.ttf"}},
  {"sora",{"jua/Jua-Regular.ttf","blackhansans/BlackHanSans-Regular.ttf"}},{"ken",{"notoserifkr/NotoSerifKR-VF.ttf","gugi/Gugi-Regular.ttf"}},
  {"nana",{"gowundodum/GowunDodum-Regular.ttf","nanumpenscript/NanumPenScript-Regular.ttf"}},{"riku",{"cutefont/CuteFont-Regular.ttf","kiranghaerang/KirangHaerang-Regular.ttf"}},
  {"akari",{"gothica1/GothicA1-Regular.ttf","gaegu/Gaegu-Regular.ttf"}},{"yuu",{"dohyeon/DoHyeon-Regular.ttf","eastseadokdo/EastSeaDokdo-Regular.ttf"}},
  {"koto",{"gowunbatang/GowunBatang-Regular.ttf","gugi/Gugi-Regular.ttf"}},{"satsuki",{"songmyung/SongMyung-Regular.ttf","dokdo/Dokdo-Regular.ttf"}},
  {"taiga",{"blackhansans/BlackHanSans-Regular.ttf","dokdo/Dokdo-Regular.ttf"}},{"rin",{"jua/Jua-Regular.ttf","cutefont/CuteFont-Regular.ttf"}},
  {"sho",{"gothica1/GothicA1-Light.ttf","nanumpenscript/NanumPenScript-Regular.ttf"}},{"ai",{"gowundodum/GowunDodum-Regular.ttf","dohyeon/DoHyeon-Regular.ttf"}},
  {"haruka",{"cutefont/CuteFont-Regular.ttf","gaegu/Gaegu-Regular.ttf"}},{"kaede",{"notoserifkr/NotoSerifKR-VF.ttf","songmyung/SongMyung-Regular.ttf"}},
  {"lappy",{"galmuri/Galmuri11.ttf","gugi/Gugi-Regular.ttf"}}};
 auto it=f.find(slug);
 auto v=it==f.end()?std::pair<std::string,std::string>{"pretendard/Pretendard-Medium.otf","blackhansans/BlackHanSans-Regular.ttf"}:it->second;
 return {"Assets/Fonts/"+v.first,"Assets/Fonts/"+v.second};
}

// 글자 한 층(앞/뒤 짝) 그리기. 바뀐 값만 엔진에 보낸다.
void Yumeno::drawGlyphs(const std::string& prefix,int capacity,const std::vector<debate::Glyph>& gs){
 for(int i=0;i<capacity;i++){
  auto front=prefix+"F"+std::to_string(i),back=prefix+"B"+std::to_string(i);
  auto& c=glyphCache[front];
  if(i>=int(gs.size())){if(c.visible!=0){UI::SetVisible(this,UI_ID,front,false);UI::SetVisible(this,UI_ID,back,false);c.visible=0;}
   if(prefix=="M"){auto& sc=glyphCache["MS"+std::to_string(i)];if(sc.visible){UI::SetVisible(this,UI_ID,"MS"+std::to_string(i),false);sc.visible=0;}}continue;}
  auto& g=gs[i];int vis=g.front?1:2;
  if(c.visible!=vis){UI::SetVisible(this,UI_ID,front,vis==1);UI::SetVisible(this,UI_ID,back,vis==2);c.visible=vis;}
  auto id=vis==1?front:back;
  if(c.text!=g.text){UI::SetText(this,UI_ID,front,g.text);UI::SetText(this,UI_ID,back,g.text);c.text=g.text;}
  // 위치·배율도 바뀐 만큼만 보낸다 : 엔진은 Update 한 번에 명령 1000개까지
  if(std::abs(c.x-g.x)>.6f||std::abs(c.y-g.y)>.6f||vis!=c.lastLayer){UI::SetPosition(this,UI_ID,id,{g.x,g.y});c.x=g.x;c.y=g.y;}
  if(std::abs(c.s-g.scale)>.006f||vis!=c.lastLayer){UI::SetScale(this,UI_ID,id,{g.scale,g.scale});c.s=g.scale;}
  c.lastLayer=vis;
  if(prefix=="M"){auto sh="MS"+std::to_string(i);auto& sc=glyphCache[sh];bool on=vis==1;
   if(sc.visible!=int(on)){UI::SetVisible(this,UI_ID,sh,on);sc.visible=on;}
   if(on){if(sc.text!=g.text){UI::SetText(this,UI_ID,sh,g.text);sc.text=g.text;}if(std::abs(sc.x-g.x)>.6f||std::abs(sc.y-g.y)>.6f){UI::SetPosition(this,UI_ID,sh,{g.x+3*g.scale,g.y+4*g.scale});sc.x=g.x;sc.y=g.y;}if(std::abs(sc.s-g.scale)>.006f){UI::SetScale(this,UI_ID,sh,{g.scale*1.04f,g.scale*1.04f});sc.s=g.scale;}
    if(std::abs(sc.rotation-g.rotation)>.2f){UI::SetRotation(this,UI_ID,sh,g.rotation);sc.rotation=g.rotation;}if(std::abs(sc.opacity-g.opacity*.8f)>.03f){UI::SetOpacity(this,UI_ID,sh,g.opacity*.8f);sc.opacity=g.opacity*.8f;}}}
  if(std::abs(c.rotation-g.rotation)>.2f){UI::SetRotation(this,UI_ID,front,g.rotation);UI::SetRotation(this,UI_ID,back,g.rotation);c.rotation=g.rotation;}
  if(std::abs(c.opacity-g.opacity)>.03f){UI::SetOpacity(this,UI_ID,front,g.opacity);UI::SetOpacity(this,UI_ID,back,g.opacity);c.opacity=g.opacity;}
 }
}

// 줄이 바뀔 때 : 글꼴·색·크기·화자 입상
void Yumeno::styleLine(){
 auto& l=debate.line();
 auto slug=slugs.count(l.speaker)?slugs.at(l.speaker):"";
 auto fonts=fontsOf(slug);bool weak=l.kind=="weak";
 // 글꼴·크기·색은 바뀐 글자에만 보낸다(엔진은 글꼴 지정마다 위젯 전체를 다시 그리고 글꼴 로딩을 기다린다)
 int n=std::min(48,debate::u8len(l.text));
 for(int i=0;i<n;i++){
  bool w=weak&&i>=l.start&&i<l.start+debate::u8len(l.word);
  Color c=w?Color{1,.6f,.15f,1}:l.kind=="agree"&&!l.answer.empty()?Color{.42f,.78f,1,1}:Color{1,1,1,1};
  auto font=weak?fonts.second:fonts.first;
  for(auto side:{"F","B"}){auto id=std::string("M")+side+std::to_string(i);auto& st=glyphStyle[id];
   if(st.font!=font){UI::SetFont(this,UI_ID,id,font);st.font=font;if(side==std::string("F")){UI::SetFont(this,UI_ID,"MS"+std::to_string(i),font);}}
   if(st.size!=debate.base()){UI::SetFontSize(this,UI_ID,id,debate.base());st.size=debate.base();if(side==std::string("F"))UI::SetFontSize(this,UI_ID,"MS"+std::to_string(i),debate.base());}
   if(st.r!=c.r||st.g!=c.g||st.b!=c.b){UI::SetColor(this,UI_ID,id,c);st.r=c.r;st.g=c.g;st.b=c.b;}}
 }
 text("TrialSpeaker",l.speaker);
 portrait=slug.empty()?"":"Assets/Art/sprites/"+slug+"/"+slug+"_"+(slug=="lappy"?"L04":weak?"T02":l.kind=="agree"?"T03":"C02")+".webp";
 speakerSeat=-1; // 같은 화자라도 줄마다 카메라가 다시 잡는다(V3)
 if(!panicWho.empty()){for(int i=0;i<int(panicWho.size());i++)UI::SetOpacity(this,"stage","PanicFig"+std::to_string(i),panicWho[i]==slug?1.f:.45f);return;}
 focusSpeaker(slug,portrait);
}

void Yumeno::updateDebate(float delta){
 if(startBandTimer>0&&(startBandTimer-=delta)<=0)UI::SetVisible(this,UI_ID,"StartBand",false);
 bool showingResult=debateResultTime>0;updateDebateFx(delta);
 if(showingResult){if(debateResultTime<=0){debate.next();shownLine=-1;debateInputArmed=false;}return;}
 if(clearTimer>0){if((clearTimer-=delta)<=0){playingDebate=false;debateHud(false);beginScript();}return;}
 // 집중 : Shift 를 누르는 동안 시간 0.35배, 게이지 소모. 놓으면 회복.
 if(!debateInputArmed&&!Input::IsKeyDown("mouse0")&&!Input::IsKeyDown("mouse1")&&!Input::IsKeyDown("Shift"))debateInputArmed=true;
 if(!Input::IsKeyDown("Shift"))focusExhausted=false;
 bool focusing=debateInputArmed&&Input::IsKeyDown("Shift")&&!focusExhausted&&debate.focus>0;
 debate.focus=std::clamp(debate.focus+(focusing?-28.f:9.f)*delta,0.f,100.f);
 if(focusing&&debate.focus<=0)focusExhausted=true;
 UI::SetVisible(this,"debatefx","FocusVeil",focusing);
 {int lit=int(std::ceil(debate.focus/10));if(lit!=shownStars){shownStars=lit;for(int k=0;k<10;k++)UI::SetTexture(this,UI_ID,"Star"+std::to_string(k),k<lit?"Assets/Art/ui/hud_starOn.svg":"Assets/Art/ui/hud_starOff.svg");}}
 bool turning=cameraTime<1;
 if(!turning)debateTime-=delta*(focusing?.35f:1);
 {int ms=std::max(0,int(debateTime*1000));char t[16];std::snprintf(t,sizeof t,"%02d:%02d:%03d",ms/60000,ms/1000%60,ms%1000);text("Timer",t);}
 if(debateTime<=0){sfx("sfx_timeup");message("시간 초과… 처음부터!",2.f);debateTime=180;debate.hearts=maxHearts;debate.broken.assign(debate.lines.size(),false);debate.index=0;debate.time=0;retries++;}
 bool changed=(!turning&&debate.tick(delta*(focusing?.35f:1)))||shownLine!=debate.index;
 if(changed){shownLine=debate.index;styleLine();} // 줄이 바뀐 프레임은 글꼴·색만, 글자는 다음 프레임(둘을 한 번에 보내면 1000개를 넘는다)
 else drawGlyphs("M",48,turning?std::vector<debate::Glyph>{}:debate.current());
 int ni=debate.noiseIndex();
 if(ni>=0&&!noiseStyled){noiseStyled=true;for(int k=0;k<26;k++)for(auto side:{"F","B"}){auto id=std::string("N")+side+std::to_string(k);UI::SetFont(this,UI_ID,id,"Assets/Fonts/gaegu/Gaegu-Regular.ttf");UI::SetColor(this,UI_ID,id,Color{.85f,.85f,.9f,1});}}
 drawGlyphs("N",26,debate.noise());
 float vx=0,vy=0;bool hasV=focusing&&debate.vpoint(vx,vy);
 UI::SetVisible(this,UI_ID,"VPoint",hasV);if(hasV)UI::SetPosition(this,UI_ID,"VPoint",{vx,vy});
 // 조준 : updateTrial 이 마우스 위치를 읽는다. ponytail: 창 크기 1280×720 고정 가정.
 if(bullets.empty()||!debateInputArmed)return;
 if(holdTime<0&&pressed("q")){bullet=(bullet+int(bullets.size())-1)%int(bullets.size());showBullet();}
 if(holdTime<0&&pressed("e")){bullet=(bullet+1)%int(bullets.size());showBullet();}
 // 사일런서 : 우클릭으로 소음 제거
 if(pressed("mouse1")&&debate.noiseHit(aimX,aimY)){if(ni>=0)debate.silenced[ni]=true;debate.focus=std::min(100.f,debate.focus+10);message("조용!",.6f);}
 // 발사 : 누를 때 장전, 떼면 발사. 0.45초 이상 누르면 거짓 탄환(발언력 1칸을 걸어 둔다)
 bool down=Input::IsKeyDown("mouse0");
 if(down){
  if(holdTime<0)holdTime=0;
  holdTime+=delta;
  if(!lie&&holdTime>.45f){lie=true;lieCost=debate.hearts>1;if(lieCost)--debate.hearts;showBullet();sfx("ui_confirm");} // 발언력 1칸이면 걸지 않고 장전
  return;
 }
 if(holdTime<0)return;
 holdTime=-1;bool lieShot=lie;lie=false;showBullet();
 shotLie=lieShot;shotTimeLeft=.22f;shotX=aimX;shotY=aimY;++shotsFired;sfx("sfx_gunshot");
 UI::SetTexture(this,"debatefx","ShotTrail",lieShot?"Assets/Art/ui/shot_lie.svg":"Assets/Art/ui/shot_normal.svg");
 if(debate.noiseHit(aimX,aimY)){message("소음에 막혔다!",.8f);return;}
 if(!debate.weakHit(aimX,aimY))return; // 빗나감 : 거짓 탄환이면 걸어 둔 발언력은 잃는다
 auto& l=debate.line();
 bool correct=bullets[bullet].first==l.answer&&lieShot==l.lie;
 if(correct){
  onCorrect();
  float px=0,py=0;bool v=debate.vpoint(px,py)&&std::hypot(aimX-px,aimY-py)<16;
  if(lieShot&&lieCost)++debate.hearts;
  bool agreeing=l.kind=="agree";
  debate.broken[debate.index]=true;vBreaks+=v&&!agreeing&&!lieShot;
  // A supported blue statement can resolve the same factual claim as its yellow counterpart.
  if(agreeing)for(size_t i=0;i<debate.lines.size();++i)if(debate.lines[i].kind=="weak"&&!debate.lines[i].lie&&debate.lines[i].answer==l.answer)debate.broken[i]=true;
  debateSuccess(agreeing?"agree":lieShot?"lie":"refute");
  if(debate.cleared())clearTimer=.15f; // Resume only after the complete cutin/crack/Break sequence.
 }else{
  sfx("sfx_wrong");
  if(skillOn("miss_guard")&&!missGuardUsed){missGuardUsed=true;message("마술사의 손! 빗나간 탄환을 되돌렸다",1.2f);return;}
  if(--debate.hearts<=0&&skillOn("revive")&&!reviveUsed){reviveUsed=true;debate.hearts=2;message("다시 일어선다!",1.4f);return;}
  if(debate.hearts<=0){message("발언력이 바닥났어요… 처음부터!",2.f);debate.hearts=maxHearts;debate.broken.assign(debate.lines.size(),false);debate.index=0;debate.time=0;debateTime=180;retries++;}
  else message("아야! 틀렸어요~!",1.2f);
 }
}

void Yumeno::Update(float delta){
 sampleInput();
 updateMusic(delta);
 if(!ready){
  ready=true;
  story=Data::Get("Assets/Data/story.json");
  emotions=Data::Get("Assets/Data/emotion.json");
  rules=Data::Get("Assets/Data/rules.json");
  art=Data::Get("Assets/Data/art.json");giftData=Data::Get("Assets/Data/gifts.json");kotodama=Data::Get("Assets/Data/kotodama.json");reactions=Data::Get("Assets/Data/reactions.json");hotspotData=Data::Get("Assets/Data/hotspots.json");skillData=Data::Get("Assets/Data/skills.json");
  UI::Show(this,"Assets/UI/Main.hbwidget.json",UI_ID);
  UI::Show(this,"Assets/UI/Explore.hbwidget.json","explore");
  UI::Show(this,"Assets/UI/Flow.hbwidget.json","flow");
  UI::Show(this,"Assets/UI/Pad.hbwidget.json","pad");
   UI::Show(this,"Assets/UI/V4Story.hbwidget.json","v4story");
   pv4::Init(presentationV4,this,Data::Get("Assets/Data/presentation/v4.json"),art,[this](const std::string& spec){playCue(spec);});
   optv4::Init(optionsV4,this,[this](const std::string& action){pv4::Action(presentationV4,action);},true);
   titleMenu(true);
  music("bgm_title");
  return;
 }
 optv4::Tick(optionsV4,delta);presentationV4.reducedMotion=optionsV4.values.reducedEffects;
  if(optionsV4.open){
   Vec2 m;Input::GetMousePosition(m);optv4::Edges e;
   e.up=pressed("w")||pressed("ArrowUp");e.down=pressed("s")||pressed("ArrowDown");e.left=pressed("a")||pressed("ArrowLeft");e.right=pressed("d")||pressed("ArrowRight");
   e.confirm=pressed("Enter");e.cancel=pressed("Escape")||pressed("Backspace")||pressed("mouse1");e.click=pressed("mouse0");
   e.mouseMoved=m.x!=optionsMouseX||m.y!=optionsMouseY;e.mouseX=m.x;e.mouseY=m.y;optionsMouseX=m.x;optionsMouseY=m.y;optv4::Handle(optionsV4,e);return;
  }
  pv4::Tick(presentationV4,mode==Mode::Pad?0.f:delta);
  if(mode==Mode::Trial){try{updateTrial(delta);}catch(const std::exception& e){lastError=std::string("stage ")+std::to_string(stageAt)+" "+stageKind+": "+e.what();}return;}
 bool click=pressed("mouse0");enterNow=pressed("Enter");bool next=enterNow|pressed("Space")|click; // 프레임 시작에 수집한 입력을 각 모드에서 공유한다.
 if(pressed("Tab")&&(flowOn||v4.active)&&(mode==Mode::Story||mode==Mode::Pad||mode==Mode::Menu||mode==Mode::Grid||mode==Mode::Explore||mode==Mode::Map)){
  padToggle();
  return;
 }
 if(mode==Mode::Pad){updatePad(delta,click);return;}
 if(mode==Mode::Title){
  
  if(pressed("t")||pressed("y")){titleMenu(false);trialKey=story["trials"][held["y"]?1:0].get<std::string>();trialDead.clear();for(auto& d:story["dead"][trialKey])trialDead.push_back(d.get<std::string>());trials=Data::Get("Assets/Data/trials/"+trialKey+".json");startTrial();return;}
  updateTitle(click);
  if(toastTimer>0&&(toastTimer-=delta)<=0)fvis("FToast",false);
  return;
 }
 if(v4.active){try{v4Update(delta,next,click);}catch(const std::exception& e){lastError="V4: "+std::string(e.what());}return;}
  if(mode==Mode::Explore||mode==Mode::Map||mode==Mode::Confirm||mode==Mode::Popup){try{updateExplore(delta,click);}catch(const std::exception& e){lastError=std::string("explore: ")+e.what();}return;}
 if(bandTimer>0&&(bandTimer-=delta)<=0)evis("Band",false);
 if(flashTimer>0&&(flashTimer-=delta)<=0)evis("Flash",false);
 try{updateFlow(delta,next,click);}catch(const std::exception& e){lastError=std::string("flow ")+std::to_string(chapterAt)+"/"+std::to_string(beat)+"/"+std::to_string(event)+": "+e.what();}
}

// Separate bounded diagnostic reply: Blueprint string outputs have a4096-character limit.
std::string Yumeno::CourtStats()const{
 auto cast=hb::Json::array(),desks=hb::Json::array();
 auto q=[](float v){return std::round(double(v)*10000)/10000;};
 for(int i=0;i<16;i++){
  if(auto* a=Scene::FindActorById("Seat"+std::to_string(i))){
   auto p=Scene::GetPosition(a),r=Scene::GetRotation(a);auto texture=Components::GetString(a,"SpriteRenderer","texture");
   hb::Json row{{"seat",i},{"position",{q(p.x),q(p.y),q(p.z)}},{"rotation",{q(r.x),q(r.y),q(r.z)}}};
   if(auto* back=Scene::FindActorById("SeatRear"+std::to_string(i))){
    auto rear=Scene::GetPosition(back);auto backTexture=Components::GetString(back,"SpriteRenderer","texture");
    row["rear"]={q(rear.x),q(rear.y),q(rear.z)};row["blackRear"]=backTexture.find("_back.webp")!=std::string::npos;
    float angle=r.y*court::PI/180;if((cam.x-p.x)*std::sin(angle)+(cam.z-p.z)*std::cos(angle)<0)texture=backTexture;
   }
   row["texture"]=texture.substr(texture.find_last_of('/')+1);cast.push_back(row);
  }
  if(auto* a=Scene::FindActorById("Podium"+std::to_string(i))){auto p=Scene::GetPosition(a),r=Scene::GetRotation(a);desks.push_back({{"seat",i},{"position",{q(p.x),q(p.y),q(p.z)}},{"rotation",{q(r.x),q(r.y),q(r.z)}}});}
 }
 return hb::Json{{"cast",cast},{"desks",desks}}.dump();
}
std::string Yumeno::Stats()const{
 const char* names[]{"title","story","pad","end","trial","menu","grid","card","credits","explore","map","confirm","popup"};
  Json s{{"mode",names[int(mode)]},{"chapter",chapterAt},{"beat",beat},{"event",event},{"pool",ctxPool},{"spot",ctxSpot},{"speaker",speaker},{"portrait",portrait},{"line",line},{"coins",coins},{"cards",int(cards.size())},{"gifts",int(gifts.size())},{"slots",slots},{"room",roomAt},{"mapSelection",mapHover},{"roomCount",rooms.size()},{"padPage",padPageAt},{"padRow",padRow},{"giftPage",giftPage},{"giftChoices",gridSlugs},{"notes",notes.size()}};
 if(v4.active){s["contentVersion"]="v4";s["node"]=v4.node;s["v4Kind"]=v4.current().value("type","");s["logCount"]=v4.log.size();s["routeBlocked"]=!v4.blocked.empty();s["auto"]=v4Auto();}
  if(flowOn&&mode!=Mode::Trial){s["beatKind"]=currentBeat().value("t","");s["auto"]=autoFlow();}
 s["world"]=exworld::stats(world);s["audioV4"]=pv4::Stats(presentationV4);s["options"]=optv4::Stats(optionsV4);
  if(!lastError.empty())s["error"]=lastError;
  if(mode==Mode::Pad&&padPageAt>=0){auto rows=padRows();s["padActions"]=Json::array();for(auto& row:rows)s["padActions"].push_back(row.first);s["padSelectedId"]=padRow>=0&&padRow<int(rows.size())?rows[padRow].first:"";}
 if(mode==Mode::Trial){s["stage"]={{"index",stageAt},{"count",int(stages.size())},{"kind",stageKind},{"script",inScript},{"hearts",debate.hearts},{"selection",optHover}};s["auto"]=autoAction();}
 if(mode==Mode::Trial)s["presentation"]={{"nonstopIntro",debateIntroTime>=0},{"elapsed",debateIntroTime},{"duration",court::nonstopDuration(int(bullets.size()))},{"loadStart",court::NONSTOP_SWEEP},{"focusStart",court::nonstopFocusStart(int(bullets.size()))},{"introPhase",debateIntroTime<0?"active":debateIntroTime<court::NONSTOP_SWEEP?"sweep":debateIntroTime<court::nonstopFocusStart(int(bullets.size()))?"load":"focus"},{"ammoCount",bullets.size()},{"loaded",debateIntroLoaded},{"timer",debateTime},{"statementTime",debate.time},{"inputArmed",debateInputArmed},{"camera",{cam.x,cam.y,cam.z,cam.yaw,cam.pitch,cam.roll}}};
 if(mode==Mode::Trial)if(auto* a=Scene::FindActorById("Camera")){auto r=Scene::GetRotation(a);s["presentation"]["sceneRotation"]={r.x,r.y,r.z};}
 if(mode==Mode::Trial&&playingDebate&&!debate.lines.empty()){
  auto& l=debate.line();int broken=0;for(bool b:debate.broken)broken+=b;
  Json weakPoint=nullptr;int front=0,back=0;
  for(auto& g:debate.current()){(g.front?front:back)++;if(weakPoint.is_null()&&g.weak&&g.front&&g.opacity>.5f&&g.x>80&&g.x<1200&&g.y>40&&g.y<620)weakPoint={g.x,g.y};}
  float vx=0,vy=0;bool v=debate.vpoint(vx,vy);
  s["trial"]={{"debate",debateAt},{"index",debate.index},{"kind",l.kind},{"motion",int(l.motion)},{"answer",l.answer},{"needLie",l.lie},{"hearts",debate.hearts},{"broken",broken},{"vBreaks",vBreaks},{"focus",debate.focus},{"bullet",bullets.empty()?"":bullets[bullet].first},{"lie",lie},{"aim",{aimX,aimY}},{"weakPoint",weakPoint},{"vpoint",v?Json{vx,vy}:Json(nullptr)},{"glyphsFront",front},{"glyphsBack",back},{"noise",debate.noiseIndex()},{"clearing",clearTimer>0||debateResultTime>0},{"camera",cameraAngle},{"speakerSeat",speakerSeat},{"turning",cameraTime<1},{"shots",shotsFired},{"result",debateResult},{"resultTime",debateResultTime},{"charge",holdTime},{"focusExhausted",focusExhausted}};
 }
 return s.dump();
}

#include "DebatePresentation.hpp"
#include "TrialRunner.hpp"
#include "Flow.hpp"
#include "Explore.hpp"
#include "Pad.hpp"
#include "V4Story.hpp"
#include "V4Explore.hpp"

void Yumeno::DebugJump(int index){if(mode==Mode::Trial)enterStage(index);}
void Yumeno::DebugCourtSeat(int index){
 if(mode!=Mode::Trial)return;
 cancelDebateIntro();playingDebate=false;inScript=false;opts.clear();stageKind="court-inspection";stageLimit=999;
 debateHud(false);courtIdle=false;speakerSeat=std::clamp(index,0,15);shotKind=0;shotTime=0;cameraTime=1;
 setCam(shotCam(speakerSeat,0));
}
void Yumeno::DebugChapter(int index){newGame();openChapter(index);enterBeat();}
void Yumeno::DebugDebateFixture(int outcome){
 // Isolated QA fixture only: no script/data/save edits, stage entry restores authored rules.
 if(!playingDebate)return;
 for(auto& l:debate.lines)if(l.kind=="weak"){l.lie=outcome==1;if(outcome==2)l.kind="agree";break;}
}
