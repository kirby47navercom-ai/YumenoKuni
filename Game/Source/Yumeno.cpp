#include "Yumeno.h"
#include "Courtroom.hpp"
#include "ComicLayoutV4.hpp"
#include "TrialDirectionV4.hpp"
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
std::string readSignature(const std::string& s){std::uint64_t h=14695981039346656037ull;for(unsigned char c:s){h^=c;h*=1099511628211ull;}return std::to_string(h);}
std::string u8prefix(const std::string& s,int count){
 int n=0;size_t i=0;
 for(;i<s.size();++i)if((static_cast<unsigned char>(s[i])&0xC0)!=0x80){if(n==count)break;++n;}
 return s.substr(0,i);
}
std::string baseName(const std::string& speaker){auto p=speaker.find('(');return p==std::string::npos?speaker:speaker.substr(0,p);}
}

void Yumeno::sampleInput(){
 keyEdges.clear();mouseWheelV4=Input::GetAxis("MouseWheelAxis");
 for(auto key:{"mouse0","mouse1","mouse2","F1","F3","z","x","r","Enter","Space","Tab","Backspace","Escape","Control","Shift","ArrowUp","ArrowDown","ArrowLeft","ArrowRight","a","d","w","s","q","f","e","g","m","c","t","y","l","o","1","2","3","4","5","6","7","8","9"}){
  bool now=Input::IsKeyDown(key);keyEdges[key]=now&&!held[key];held[key]=now;
 }
}
bool Yumeno::pressed(const std::string& key){auto it=keyEdges.find(key);return it!=keyEdges.end()&&it->second;}
void Yumeno::text(const std::string& id,const std::string& value){if(texts.count(id)&&texts[id]==value)return;texts[id]=value;UI::SetText(this,UI_ID,id,value);}

void Yumeno::dialogVisible(bool visible){
 for(auto id:{"DialogFrame","Body"})UI::SetVisible(this,UI_ID,id,visible);
 if(visible)dialogueName();else for(auto id:{"Nameplate","Name","DialogueOrnament","DialogFrameMiddle","DialogFrameRight","DialogueOrnamentMiddle","DialogueOrnamentRight"})UI::SetVisible(this,UI_ID,id,false);UI::SetVisible(this,UI_ID,"NameHead",false);
 if(!visible)UI::SetVisible(this,UI_ID,"Next",false);
}

void Yumeno::message(const std::string& value,float seconds){const bool nonstop=v4TaskActive&&stageKind=="nonstop";UI::SetFontSize(this,UI_ID,"TrialMsg",nonstop?30.f:60.f);UI::SetPosition(this,UI_ID,"TrialMsg",{0,nonstop?540.f:300.f});UI::SetColor(this,UI_ID,"TrialMsg",Color{1,.56f,.78f,1});text("TrialMsg",value);UI::SetVisible(this,UI_ID,"TrialMsg",true);messageTimer=seconds;}

static float kotodamaPlateWidth(const std::string& label){return std::max(118.f,68.f+25.f*u8len(label));}
void Yumeno::showBullet(){
 if(bullets.empty())return;
 auto label=(lie?"거짓 · ":"")+bullets[bullet].second;
 if(v4TaskActive&&v4Task.contains("transformation")){auto t=v4Task["transformation"];if(t.value("sourceEvidenceId",std::string())==bullets[bullet].first)label=lie?t.value("lieLabel",label):t.value("normalLabel",label);}float width=kotodamaPlateWidth(label);
 text("Bullet",label);UI::SetSize(this,UI_ID,"BulletPlate",{width,50});UI::SetSize(this,UI_ID,"Bullet",{width-64,40});
 UI::SetTexture(this,UI_ID,"BulletPlate",lie?"Assets/Art/ui/kotodama_plate_lie.svg":"Assets/Art/ui/kotodama_plate.svg");
 UI::SetColor(this,UI_ID,"Bullet",lie?Color{.23f,.08f,.37f,1}:Color{.06f,.17f,.27f,1});
 UI::SetRotation(this,UI_ID,"Cylinder",bullet*72.f);
}


hb::Actor* Yumeno::actor(const std::string& id){return scenesv4::find(id);}
void Yumeno::seatVisible(int seat,bool visible){for(auto prefix:{"Seat","SeatRear"})if(auto* a=actor(prefix+std::to_string(seat)))Components::Set(a,"SpriteRenderer","visible",visible);}
void Yumeno::placeCamera(float angle){
 auto s=court::shot(angle);
 setCam({s.x*(1-cameraPitch/30),s.y+cameraPitch*.02f,s.z*(1-cameraPitch/30),s.yaw,cameraPitch,0}); // 래피를 볼 때는 가운데로 물러나 올려다본다
}
void Yumeno::setCam(const court::Cam& c){
 cam=c;if(auto* a=actor("Camera")){auto r=court::engineRotation(c);Scene::SetPosition(a,{c.x,c.y,c.z});Scene::SetRotation(a,{r.x,r.y,r.z});}
 // Retain both textures, but submit only the plane facing the camera.
 for(int i=0;i<16;i++)if(auto* a=actor("Seat"+std::to_string(i))){
  auto front=seatTexture[i],shown=front;
  if(front.find("court_figures/")!=std::string::npos||front.find("memorials/")!=std::string::npos){
   auto p=Scene::GetPosition(a);float angle=Scene::GetRotation(a).y*court::PI/180;
   if((c.x-p.x)*std::sin(angle)+(c.z-p.z)*std::cos(angle)<0)
    shown=front.substr(0,front.size()-5)+"_back.webp";
  }
  auto previous=seatShownTexture.find(i);
  if(previous==seatShownTexture.end()||previous->second!=shown){
   bool rear=shown!=front;Components::SetBool(a,"SpriteRenderer","enabled",!rear);
   if(auto* back=actor("SeatRear"+std::to_string(i)))Components::SetBool(back,"SpriteRenderer","enabled",rear);
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
 if(stageKind=="scrum"&&scrumSideSeats.count(seat))if(auto* a=actor("Seat"+std::to_string(seat))){auto side=slug+(Scene::GetPosition(a).x<0?"_SR":"_SL");if(courtFigures.contains(side))key=side;}
 if(!courtFigures.contains(key))key=slug;
 const auto& f=courtFigures[key];auto front=f.value("texture",std::string());
 if(seatTexture[seat]==front)return;
 auto previous=seatTexture[seat];auto oldKey=previous.substr(previous.find_last_of('/')+1);auto oldDot=oldKey.find_last_of('.');if(oldDot!=std::string::npos)oldKey.resize(oldDot);float oldCenter=courtFigures.contains(oldKey)?courtFigures[oldKey].value("center",1.25f):f.value("center",1.25f);
 seatTexture[seat]=front;seatShownTexture.erase(seat);
 for(auto prefix:{"Seat","SeatRear"})if(auto* a=actor(prefix+std::to_string(seat))){
  Components::SetString(a,"SpriteRenderer","texture",std::string(prefix)=="SeatRear"?f.value("back",front):front);
  Components::Set(a,"SpriteRenderer","width",f.value("width",1.f));Components::Set(a,"SpriteRenderer","height",f.value("height",2.3f));
  auto p=Scene::GetPosition(a);Scene::SetPosition(a,{p.x,p.y-oldCenter+f.value("center",1.25f),p.z});
 }
}
// 재판 시작 : 생존자는 입상, 사망자는 영정. 카메라는 첫 화자 자리에서 시작
void Yumeno::setupCourt(){
 if(!scenesv4::courtReady())return;
 auto court=Data::Get("Assets/Data/court.json");courtFigures=court["figures"];seatTexture.clear();seatShownTexture.clear();
 // Keep Rin's stance grounded while matching the neighboring witness scale.
 for(auto& [key,figure]:courtFigures.items())if(key=="rin"||key.rfind("rin_",0)==0){
  constexpr float scale=.85f;
  const float height=figure.value("height",2.3f);
  figure["center"]=figure.value("center",1.25f)-height*(1.f-scale)*.5f;
  figure["height"]=height*scale;
  figure["width"]=figure.value("width",1.f)*scale;
 }
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
 v4AppliedDebateMode=-1;
 if(stageShown){bool p=d.value("kind",std::string())=="panic";for(int lane=0;lane<(p?3:1);lane++)for(int i=0;i<48;i++)UI::SetScale(this,"panicv4","P"+std::to_string(lane)+"G"+std::to_string(i),{p?1.3f:1.f,p?1.3f:1.f});} // 패닉은 크게(V3), 쇼다운이 키운 배율은 되돌린다
 debateAt=stageAt;

 int hearts=debate.hearts;float focus=debate.focus; // 발언력·집중은 재판 내내 이어짐
 noiseBlockedShotsV4=0;debate=debate::State{};debate.focus=focus;debate.noisePool=v4TaskActive;debate.noiseAction=difficultyV4.action;
 int i=0;
 // 늘린 발언(연출표 extra, 사양서 25) : 원래 줄 사이에 끼운다. V3 논스톱은 발언 묶음이 평균 12개(nonstop_*.dat u16[1])
 hb::Json source=d["lines"];
 if(d.value("kind",std::string())!="panic")if(const auto* ex=trialdirection::find("extra",d.value("id",std::string()))){
  hb::Json merged=hb::Json::array();auto put=[&](int after){for(const auto& e:*ex)if(e.value("after",-2)==after)merged.push_back({{"id",e.value("id",std::string())},{"actor",e.value("actor",std::string())},{"speaker",e.value("speaker",std::string())},{"text",e.value("text",std::string())},{"kind","plain"}});};
  put(-1);for(int k=0;k<int(source.size());k++){merged.push_back(source[k]);put(k);}source=merged;}
 for(auto& l:source){
  // Accept old saves/packages without reviving the retired inline noise layer.
  if(v4TaskActive&&d.value("kind",std::string())=="nonstop"&&l.value("kind",std::string())=="noise")continue;
  debate::Line x{l.value("speaker",""),l.value("text",""),l.value("kind","plain")};
  x.actor=l.value("actor",std::string());x.noiseGroup=l.value("noiseGroup",l.value("sourceLineId",l.value("id",std::string())));x.noiseRewardSeconds=std::clamp(l.value("noiseRewardSeconds",0),0,60);
  x.noiseLoud=v4TaskActive&&d.value("kind",std::string())=="panic"&&l.value("noiseRole",std::string())=="loud";x.pose=l.value("pose",std::string());
  if(x.noiseLoud)x.noiseDurability=std::max(1,l.value("noiseDurability",2));
  if(l.contains("vpoint"))x.vpointIndex=l["vpoint"].value("glyphIndex",-1);
  if(l.contains("weak")){x.word=l["weak"].value("word","");x.answer=l["weak"].value("answer","");x.start=l["weak"].value("start",0);x.lie=l["weak"].value("lie",false);}
  // 함정 약점·동의점(연출표 decoy, 사양서 25) : V3 는 한 논의에 노란 약점이 여럿이고 대부분 함정이다. 정답이 없어 어느 언령으로 쏴도 틀린다
  if(d.value("kind",std::string())!="panic"&&x.kind=="plain")if(const auto* dd=trialdirection::find("debate",l.value("id",std::string()));dd&&dd->contains("decoy")){const auto& dc=(*dd)["decoy"];auto word=dc.value("word",std::string());auto at=x.text.find(word);
   if(!word.empty()&&at!=std::string::npos){x.kind=dc.value("kind",std::string("weak"))=="agree"?"agree":"weak";x.word=word;x.start=debate::u8len(x.text.substr(0,at));x.answer="decoy:none";x.decoy=true;}} /* 맞으면 틀린 것(V3) — 어떤 언령 id 와도 같지 않다 */
  if(x.kind=="agree"&&l.contains("agree")){x.answer=l.value("agree","");x.word=x.text;x.start=0;if(l.contains("agreeTarget")){x.word=l["agreeTarget"].value("word",x.text);x.start=l["agreeTarget"].value("glyphStart",0);}}
  x.readable=v4TaskActive&&stageKind=="nonstop"&&x.kind!="noise";
  if(x.readable&&d.value("id",std::string()).rfind("T1-",0)==0&&x.kind=="agree"){
   x.kind="weak";
   if(!x.decoy){
    const auto* authored=trialdirection::find("debate",l.value("id",std::string()));
    if(!authored||!authored->contains("openingRefutation"))throw std::runtime_error("Chapter one agreement needs an authored refutation");
    const auto& replacement=authored->at("openingRefutation");x.text=replacement.at("text").get<std::string>();x.word=replacement.at("word").get<std::string>();
    const auto at=x.text.find(x.word);if(at==std::string::npos||x.word.empty())throw std::runtime_error("Invalid opening refutation target");
    x.start=debate::u8len(x.text.substr(0,at));x.vpointIndex=-1;
   }
  }
  x.size=debate::sizeOf(x);
  x.id=l.value("id",std::string());const auto* dir=trialdirection::find("debate",x.id); // 줄마다 연출표(사양서 25)
  x.motion=debate::motionOf(dir?dir->value("motion",std::string()):l.value("motion",""),x,i++,debate.lines.empty()?debate::Motion::Wave:debate.lines.back().motion);
  {auto sl=!x.actor.empty()?x.actor:slugs.count(x.speaker)?slugs.at(x.speaker):"";auto fs=fontsOf(sl);x.font=x.readable?fs.first:x.kind=="weak"?fs.second:x.kind=="noise"?std::string(stageKind=="nonstop"?"Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf":"Assets/Fonts/jua/Jua-Regular.ttf"):fs.first;x.spacing=1; /* 폭은 글꼴 실측(GlyphMetricsV4) */
   if(dir){x.directed=true;x.yaw=dir->value("yaw",0.f);x.size*=dir->value("size",1.f);x.shot=dir->value("shot",-1);x.fx=dir->value("fx",std::string());if(dir->contains("font"))x.font="Assets/Fonts/"+(*dir)["font"].get<std::string>();auto p=trialdirection::pose(sl,dir->value("pose",std::string()));if(!p.empty())x.pose=p;x.followPose=trialdirection::pose(sl,dir->value("followPose",std::string()));if(dir->contains("acting")){std::string cue=(*dir)["acting"].get<std::string>();std::vector<std::string> fields;size_t at=0,end;while((end=cue.find('|',at))!=std::string::npos){fields.push_back(cue.substr(at,end-at));at=end+1;}fields.push_back(cue.substr(at));if(fields.size()>=6){if(fields.size()>6&&!fields[6].empty())x.font="Assets/Fonts/"+fields[6];x.shot=std::stoi(fields[4]);x.yaw=std::stof(fields[5]);x.performance=fields[0];x.composition=fields[1];x.followPose=trialdirection::pose(sl,fields[2]);try{x.followAt=std::clamp(std::stof(fields[3]),.2f,.75f);}catch(...){x.followAt=.4f;}}}}}
  if(x.readable)x.size=std::clamp(x.size,.96f,1.12f);
  debate.lines.push_back(x);
 }

 // 잡음(분홍, 연출표 noise, 사양서 25) : V3 논스톱 58개 중 48개에 잡음 행(nonstop_*.dat u16[6]==1)이 평균 9.5줄. 문구별 발언 연결과 표시 시각은 자체 연출표에서 지정한다
 if(d.value("kind",std::string())!="panic"&&debate::noiseEnabled(d.value("id",std::string())))if(const auto* nz=trialdirection::find("noise",d.value("id",std::string())))for(const auto& n:*nz){
  debate::Line x{n.value("speaker",""),n.value("text",""),"noise"};x.actor=n.value("actor",std::string());x.id=n.value("id",std::string());x.noiseGroup=x.id;x.noiseRewardSeconds=2; /* V3 : 잡음을 쏘면 제한 시간이 는다(Fandom Class Trials). Codex 잡음과 같은 2초 */
  x.size=debate::sizeOf(x);x.motion=debate::Motion::Wave;x.font="Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf";x.spacing=1;debate.lines.push_back(x);}
 if(v4TaskActive&&stageKind=="nonstop"){
  const auto task=d.value("id",std::string());
  if(debate::noiseEnabled(task))for(const auto& row:debate::NOISE_BINDINGS)if(task==row.task&&row.text[0]){
   debate::Line n{"",row.text,"noise"};n.id=row.id;n.actor=row.actor;n.noiseGroup=n.id;n.noiseRewardSeconds=2;n.font="Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf";n.spacing=1;debate.lines.push_back(n);
  }
  // Context is authored per interruption, never a repeated row-count pattern.
  for(auto& n:debate.lines)if(n.kind=="noise"){
   const auto cue=debate::noiseCue(n.id,n.text);n.noiseDurability=cue.hits;n.noiseFor=-1;
   for(int k=0;k<int(debate.lines.size());++k)if(debate.lines[k].kind!="noise"&&debate.lines[k].id==cue.host&&debate.lines[k].actor!=n.actor){n.noiseFor=k;break;}
   if(n.noiseFor<0)throw std::runtime_error("Unbound Nonstop interruption: "+n.id);
  }
 }else{
 if(d.value("kind",std::string())!="panic"){ // 잡음을 발언에 묶는다 — V3 nonstop_02_2xx : 발언마다 0·1·2·3·4줄(예 202 = 2,0,2,0,4,3,0,0,0,3,0), 절반쯤은 0. 마지막 발언엔 안 붙인다
  std::vector<int> st,nz;for(int k=0;k<int(debate.lines.size());k++){if(debate.lines[k].kind!="noise")st.push_back(k);else nz.push_back(k);}
  {std::vector<int> rest;for(int k:nz){int own=-1;for(int t:st)if(!debate.lines[k].noiseGroup.empty()&&debate.lines[t].id==debate.lines[k].noiseGroup)own=t;if(own>=0)debate.lines[k].noiseFor=own;else rest.push_back(k);}nz=rest;} /* Codex 잡음은 반응한 원래 발언에 */
  static const int pattern[]{2,0,2,1,0,3,0,2,1,0};int at=0;
  for(int k=0;k<int(st.size())-1&&at<int(nz.size());k++)for(int m=0;m<pattern[k%10]&&at<int(nz.size());m++)debate.lines[nz[at++]].noiseFor=st[k];
  for(int k=0;at<int(nz.size());k=(k+1)%std::max(1,int(st.size())-1))debate.lines[nz[at++]].noiseFor=st[k];}
 }
 debate.broken.assign(debate.lines.size(),false);debate.silenced.assign(debate.lines.size(),false);debate.noiseDamage.assign(debate.lines.size(),0);debate.bindNoiseAnchors();debate.hearts=hearts;
 if(v4.active&&d.value("kind",std::string())=="panic"){
  if(!d.contains("lanes")||d["lanes"].size()!=3)throw std::runtime_error("Panic requires its three authored lanes");
  debate.authoredPanicBeats=d.value("synchronizedBeats",false);
  for(int at=0;at<int(source.size());++at){
   const auto host=source[at].value("hostStatement",std::string());if(host.empty())continue;
   const auto found=std::find_if(debate.lines.begin(),debate.lines.end(),[&](const auto& row){return row.id==host&&row.kind!="noise";});
   if(found==debate.lines.end()||!debate.lines[at].noiseLoud)throw std::runtime_error("Unbound Panic interruption: "+host);
   debate.lines[at].noiseFor=int(found-debate.lines.begin());
  }
  for(const auto& lane:d["lanes"]){std::vector<int> indices;for(const auto& id:lane["lines"])for(int j=0;j<int(d["lines"].size());j++)if(d["lines"][j].value("id",std::string())==id.get<std::string>())indices.push_back(j);if(indices.empty())throw std::runtime_error("Panic lane has no source lines");debate.lanes.push_back(indices);}
  if(debate.authoredPanicBeats&&std::any_of(debate.lanes.begin(),debate.lanes.end(),[&](const auto& lane){return lane.size()!=debate.lanes[0].size();}))throw std::runtime_error("Synchronized Panic requires equal beat counts");
  debate.laneAt.assign(3,0);debate.laneTime.assign(3,0);debate.selectPanic();
 }
 if(gputrialhudv4::ready){std::vector<std::pair<std::string,int>> required;if(d.value("kind",std::string())!="panic")for(const auto& l:debate.lines){if(l.kind=="noise"||(l.motion!=debate::Motion::Slam&&l.motion!=debate::Motion::Assemble&&l.motion!=debate::Motion::Zoom&&l.motion!=debate::Motion::Type&&l.motion!=debate::Motion::Spiral))continue;auto slug=!l.actor.empty()?l.actor:slugs.count(l.speaker)?slugs.at(l.speaker):"";auto f=fontsOf(slug);required.push_back({gputrialhudv4::hash((l.kind=="weak"?f.second:f.first)+"|"+std::to_string(l.kind=="weak"?62:54)+"|"+l.text),l.kind=="weak"?1:l.kind=="agree"?2:0});}bool warming=gputrialhudv4::warmup("T"+std::to_string(chapterAt),required);if(gpupanichudv4::ready){std::vector<std::pair<int,std::string>> rows;if(debate.panic())for(int lane=0;lane<3;lane++)for(int at:debate.lanes[lane]){const auto& l=debate.lines[at];auto slug=!l.actor.empty()?l.actor:slugs.count(l.speaker)?slugs.at(l.speaker):"";auto f=fontsOf(slug);rows.push_back({lane,gpupanichudv4::key(l.kind=="weak"?f.second:f.first,l.text,l.kind,l.start,l.word)});}warming=gpupanichudv4::warmup(rows)||warming;}if(gpunoisehudv4::ready){std::vector<std::string> keys;for(const auto& l:debate.lines)if(l.kind=="noise"&&!l.noiseLoud)keys.push_back(gputrialhudv4::hash(std::string("Assets/Fonts/gaegu/Gaegu-Regular.ttf|40|")+l.text));warming=gpunoisehudv4::warmup(keys)||warming;}if(warming){UI::Show(this,"Assets/UI/LoadingV4.hbwidget.json","loadingv4");gputrialhudv4::warmupOverlay=true;}}
 bullets.clear();for(auto& b:d["bullets"])bullets.emplace_back(b.value("id",""),b.value("name",""));
 bullet=0;shownLine=-1;shownHearts=-1;shownNoise=-1;clearTimer=0;holdTime=-1;lie=lieCost=false;lieV4.cancel();lieV4Ticks=0;shotRecoveryV4.reset();v4NoiseReset();aimAssistV4.active=false;aimPointerV4={};aimSwayV4.reset();focusExhausted=false;shotsFired=0;resetDebateFx();
 playingDebate=true;dialogVisible(false);debateHud(true);sclear();
 debateTime=(v4TaskActive&&stageKind=="panic"?300.f:180.f)*trialTimeFactor()+(skillOn("debate_time")?10.f:0.f);showBullet();
 bool panic=d.value("kind","")=="panic";
 if(panic){std::vector<std::string> who;for(auto& l:debate.lines){auto sl=!l.actor.empty()?l.actor:slugs.count(l.speaker)?slugs.at(l.speaker):"";if(!sl.empty()&&std::find(who.begin(),who.end(),sl)==who.end()&&who.size()<3)who.push_back(sl);}
  if(debate.panic()){who.clear();for(const auto& lane:d["lanes"])who.push_back(lane.value("actor",std::string()));}
  panicWho=std::move(who);panicStorySpeakers.clear();panicLeadTask.clear();panicLeadCount=0;panicLeadSplit=0;
 }else panicWho.clear();
 beginDebateIntro();
}

void Yumeno::drawPanicLanes(bool visible){
 if(!visible&&panicViewsPublished){auto state=hb::Json::parse(Game::GetStateText());state.erase("renderViews");Game::SetStateText(state.dump());panicViewsPublished=false;}
 if(!stageShown)return;
 int styledLane=-1; // Font initialization redraws a widget; bound it to one voice per tick.
 for(int lane=0;lane<3;lane++){
  auto gs=visible&&debate.panic()?debate.panicGlyphs(lane):std::vector<debate::Glyph>{};
  int index=visible&&debate.panic()?debate.laneLine(lane):-1;std::string font;
  if(index>=0){const auto& l=debate.lines[index];auto fs=fontsOf(l.actor);font=l.kind=="weak"?fs.second:fs.first;
   if(lane==debate.panicDisplayLane)text("TrialSpeaker",l.speaker.empty()?nameOf(l.actor):l.speaker);
   auto pose=l.pose.empty()?l.actor:l.pose;auto cache="PanicPose"+std::to_string(lane);if(stexts[cache]!=pose){int seat=court::seatOf(l.actor);if(seat>=0)courtPose(seat,pose);stexts[cache]=pose;}
  }
  if(gpupanichudv4::ready&&!gpupanichudv4::fallback&&gpupanichudv4::error.empty()){std::string key;if(index>=0){const auto& l=debate.lines[index];key=gpupanichudv4::key(font,l.text,l.kind,l.start,l.word);}gpupanichudv4::set(lane,key,index>=0?debate.laneTime[lane]:0,gs.empty()?0:gs[0].opacity,visible&&!gs.empty());continue;}
  bool needsFont=false;for(int i=0;i<int(gs.size());i++)if(glyphStyle["P"+std::to_string(lane)+"G"+std::to_string(i)].font!=font)needsFont=true;
  if(needsFont&&styledLane>=0)gs.clear();else if(needsFont)styledLane=lane;
  for(int i=0;i<48;i++){
   auto id="P"+std::to_string(lane)+"G"+std::to_string(i);auto& c=glyphCache[id];
   if(i>=int(gs.size())){if(c.visible){panicGlyphDisplay.visible(id,false);c.visible=0;}continue;}
   const auto& g=gs[i];auto& st=glyphStyle[id];Color color=g.weak?(debate.lines[index].kind=="agree"?Color{.35f,.78f,1,1}:Color{1,.78f,.12f,1}):debate.lines[index].kind=="noise"?Color{1,.3f,.72f,1}:Color{1,1,1,1}; /* V3 : 약점 노랑, 동의 파랑, 큰소리·소음 분홍(영상 A 1:31) */
   if(st.font!=font){UI::SetFont(this,"panicv4",id,font);st.font=font;}if(st.r!=color.r||st.g!=color.g||st.b!=color.b){UI::SetColor(this,"panicv4",id,color);st.r=color.r;st.g=color.g;st.b=color.b;}
   if(!c.visible){panicGlyphDisplay.visible(id,true);c.visible=1;}if(c.text!=g.text){panicGlyphDisplay.text(id,g.text);c.text=g.text;}
   if(std::abs(c.x-g.x)>.6f||std::abs(c.y-g.y)>.6f){panicGlyphDisplay.position(id,{g.x,g.y});c.x=g.x;c.y=g.y;}
   panicGlyphDisplay.scale(id,{debate::PANIC_TYPE[lane].scale,debate::PANIC_TYPE[lane].scale});
   if(std::abs(c.rotation-g.rotation)>.2f){panicGlyphDisplay.rotation(id,g.rotation);c.rotation=g.rotation;}
   if(std::abs(c.opacity-g.opacity)>.03f){panicGlyphDisplay.opacity(id,g.opacity);c.opacity=g.opacity;}
  }
 }
 panicGlyphDisplay.flush([this](const std::string& id,const glyphdisplayv4::Values& value,unsigned fields){
  using namespace glyphdisplayv4;
  if(fields&Text)UI::SetText(this,"panicv4",id,value.text);
  if(fields&Position)UI::SetPosition(this,"panicv4",id,{value.position.x,value.position.y});
  if(fields&Scale)UI::SetScale(this,"panicv4",id,{value.scale.x,value.scale.y});
  if(fields&Rotation)UI::SetRotation(this,"panicv4",id,value.rotation);
  if(fields&Opacity)UI::SetOpacity(this,"panicv4",id,value.opacity);
  if(fields&Visible)UI::SetVisible(this,"panicv4",id,value.visible);
 });
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
 if(prefix=="M"&&gputrialhudv4::speakerRoot){
  if(auto* target=actor(speakerSeat>=0?"Seat"+std::to_string(speakerSeat):speakerSeat==-2?"Host":"")){auto p=Scene::GetPosition(target);float yaw=cam.yaw*court::PI/180,pitch=cam.pitch*court::PI/180;gputrialhudv4::setSpeakerDepth(.45f*((p.x-cam.x)*-std::sin(yaw)*std::cos(pitch)+(p.y-cam.y)*std::sin(pitch)+(p.z-cam.z)*-std::cos(yaw)*std::cos(pitch)));} /* 글자 층을 화자보다 카메라 쪽(.45)으로 — 화면 위 자리·크기는 같고 앞 단상에 가리지 않는다(V3 : 발언은 늘 맨 앞) */
 }
 if(prefix=="M"&&gputrialhudv4::ready){if(debate.lines.empty())gputrialhudv4::motion(-1,0);else gputrialhudv4::motion(int(debate.line().motion),debate.t());}
 for(int i=0;i<capacity;i++){
  auto front=prefix+"F"+std::to_string(i),back=prefix+"B"+std::to_string(i);
  auto& c=glyphCache[front];
  if(i>=int(gs.size())){if(c.visible!=0){glyphDisplay.visible(front,false);glyphDisplay.visible(back,false);c.visible=0;}
   if(prefix=="M"){auto& sc=glyphCache["MS"+std::to_string(i)];if(sc.visible){glyphDisplay.visible("MS"+std::to_string(i),false);sc.visible=0;}}continue;}
  auto& g=gs[i];int vis=g.front?1:2;
  if(c.visible!=vis){glyphDisplay.visible(front,vis==1);glyphDisplay.visible(back,vis==2);c.visible=vis;}
  auto id=vis==1?front:back;
  if(c.text!=g.text){glyphDisplay.text(front,g.text);glyphDisplay.text(back,g.text);c.text=g.text;}
  // 위치·배율도 바뀐 만큼만 보낸다 : 엔진은 Update 한 번에 명령 1000개까지
  if(std::abs(c.x-g.x)>.6f||std::abs(c.y-g.y)>.6f||vis!=c.lastLayer){glyphDisplay.position(id,{g.x,g.y});c.x=g.x;c.y=g.y;}
  if(std::abs(c.s-g.scale)>.006f||vis!=c.lastLayer){glyphDisplay.scale(id,{g.scale,g.scale});c.s=g.scale;}
  c.lastLayer=vis;
  if(prefix=="M"){auto sh="MS"+std::to_string(i);auto& sc=glyphCache[sh];bool on=vis==1;
   if(sc.visible!=int(on)){glyphDisplay.visible(sh,on);sc.visible=on;}
   if(on){if(sc.text!=g.text){glyphDisplay.text(sh,g.text);sc.text=g.text;}if(std::abs(sc.x-g.x)>.6f||std::abs(sc.y-g.y)>.6f){glyphDisplay.position(sh,{g.x+3*g.scale,g.y+4*g.scale});sc.x=g.x;sc.y=g.y;}if(std::abs(sc.s-g.scale)>.006f){glyphDisplay.scale(sh,{g.scale*1.04f,g.scale*1.04f});sc.s=g.scale;}
    if(std::abs(sc.rotation-g.rotation)>.2f){glyphDisplay.rotation(sh,g.rotation);sc.rotation=g.rotation;}if(std::abs(sc.opacity-g.opacity*.8f)>.03f){glyphDisplay.opacity(sh,g.opacity*.8f);sc.opacity=g.opacity*.8f;}}}
  if(std::abs(c.rotation-g.rotation)>.2f){glyphDisplay.rotation(front,g.rotation);glyphDisplay.rotation(back,g.rotation);c.rotation=g.rotation;}
  if(std::abs(c.opacity-g.opacity)>.03f){glyphDisplay.opacity(front,g.opacity);glyphDisplay.opacity(back,g.opacity);c.opacity=g.opacity;}
 }
 glyphDisplay.flush([this](const std::string& id,const glyphdisplayv4::Values& value,unsigned fields){
  using namespace glyphdisplayv4;
  if(fields&Text)UI::SetText(this,UI_ID,id,value.text);
  if(fields&Position)UI::SetPosition(this,UI_ID,id,{value.position.x,value.position.y});
  if(fields&Scale)UI::SetScale(this,UI_ID,id,{value.scale.x,value.scale.y});
  if(fields&Rotation)UI::SetRotation(this,UI_ID,id,value.rotation);
  if(fields&Opacity)UI::SetOpacity(this,UI_ID,id,value.opacity);
  if(fields&Visible)UI::SetVisible(this,UI_ID,id,value.visible);
 });
 if((prefix=="M"||prefix=="N")&&gputrialhudv4::ready)for(int i=0;i<std::min(capacity,int(gs.size()));i++){const auto& g=gs[i];for(auto side:{"F","B"})gputrialhudv4::raw(prefix+side+std::to_string(i),g.x,g.y,g.scale,g.rotation,g.opacity,g.depth,g.front,g.solid,g.yaw,g.pitch);if(prefix=="M")gputrialhudv4::raw("MS"+std::to_string(i),g.x+3*g.scale,g.y+4*g.scale,g.scale*1.04f,g.rotation,g.solid?0.f:g.opacity*.8f,g.depth,true,false,g.yaw,g.pitch);}

}

// 줄이 바뀔 때 : 글꼴·색·크기·화자 입상
void Yumeno::styleLine(){
 // The next font must not be resolved against the previous utterance's text
 // during the one-frame style handoff, including its retained shadow layer.
 if(v4TaskActive&&stageKind=="nonstop"){
  for(int i=0;i<48;++i)for(auto face:{"MF","MB","MS"})UI::SetText(this,UI_ID,std::string(face)+std::to_string(i),"");
  for(auto it=glyphCache.begin();it!=glyphCache.end();)if(it->first.rfind("M",0)==0)it=glyphCache.erase(it);else ++it;
  glyphDisplay.invalidatePrefix("M"); // Keep noise visibility so shorter responses hide their old tail.
 }
 debateFollowPosePlayed=false;
 auto& l=debate.line();
 auto slug=!l.actor.empty()?l.actor:slugs.count(l.speaker)?slugs.at(l.speaker):"";
 auto fonts=fontsOf(slug);bool weak=l.kind=="weak";
 gputrialhudv4::line(l.font.empty()?(weak?fonts.second:fonts.first):l.font,debate.base(),l.text);
 // 글꼴·크기·색은 바뀐 글자에만 보낸다(엔진은 글꼴 지정마다 위젯 전체를 다시 그리고 글꼴 로딩을 기다린다)
 int n=std::min(48,debate::u8len(l.text));
 for(int i=0;i<n;i++){
  bool w=(weak||l.kind=="agree")&&i>=l.start&&i<l.start+debate::u8len(l.word);
  Color c=w?(weak?Color{1,.82f,.16f,1}:Color{.35f,.82f,1,1}):Color{1,1,1,1}; // V3 : 약점 노랑(Gematsu 2016 · 영상 A 1:31), 동의 파랑
  auto font=l.font.empty()?(weak?fonts.second:fonts.first):l.font; /* 연출표 글꼴 */
  for(auto side:{"F","B"}){auto id=std::string("M")+side+std::to_string(i);auto& st=glyphStyle[id];
   if(st.font!=font){UI::SetFont(this,UI_ID,id,font);st.font=font;if(side==std::string("F")){UI::SetFont(this,UI_ID,"MS"+std::to_string(i),font);}}
   if(st.size!=debate.base()){UI::SetFontSize(this,UI_ID,id,debate.base());st.size=debate.base();if(side==std::string("F"))UI::SetFontSize(this,UI_ID,"MS"+std::to_string(i),debate.base());}
   if(st.r!=c.r||st.g!=c.g||st.b!=c.b){UI::SetColor(this,UI_ID,id,c);st.r=c.r;st.g=c.g;st.b=c.b;}}
 }
 {std::string spaced;for(size_t k=0;k<l.speaker.size();){size_t n=(unsigned char)l.speaker[k]<0x80?1:(unsigned char)l.speaker[k]<0xE0?2:(unsigned char)l.speaker[k]<0xF0?3:4;if(!spaced.empty())spaced+=" ";spaced+=l.speaker.substr(k,n);k+=n;}text("TrialSpeaker",spaced); /* V3 넓은 자간 */
  if(!debate.panic()){int n=0,at=0;for(int k=0;k<int(debate.lines.size());k++)if(debate.lines[k].kind!="noise"){if(k==debate.index)at=n;n++;}
   n=std::clamp(n,1,14);at=std::clamp(at,0,n-1);UI::SetTexture(this,UI_ID,"NamePanel","Assets/Art/ui/hud_name_dots/n"+std::to_string(n)+"_"+std::to_string(at)+".svg");}}
 portrait=slug.empty()?"":"Assets/Art/sprites/"+slug+"/"+slug+"_"+(slug=="lappy"?"L04":weak?"T02":l.kind=="agree"?"T03":"C02")+".webp";
 if(v4.active)portrait=l.pose.empty()?slug:l.pose;
 if(l.readable&&!lieViewOn){
  const auto wash=debate::courtWash(l);
  if(lastDebateWash!=wash){UI::SetTexture(this,UI_ID,"CourtDim",wash);lastDebateWash=wash;}
 }
 if(!l.readable)speakerSeat=-1; // 같은 화자라도 줄마다 카메라가 다시 잡는다(V3)
 if(!panicWho.empty()){for(int i=0;i<int(panicWho.size());i++)UI::SetOpacity(this,"panes","PanicFig"+std::to_string(i),panicWho[i]==slug?1.f:.8f);return;}
 focusSpeaker(slug,portrait);
 if(l.readable){
  const auto tone=debate::delivery(l);
  const bool focus=tone==debate::Delivery::Assertive||tone==debate::Delivery::Suspect||tone==debate::Delivery::Regret||tone==debate::Delivery::Uneasy;
  if(focus||debateCastTinted){
   for(int seat=0;seat<16;++seat)for(auto prefix:{"Seat","SeatRear"})if(auto* figure=actor(prefix+std::to_string(seat))){
    Color tint{1,1,1,1};
    if(focus){const bool speaker=seat==speakerSeat;float other=tone==debate::Delivery::Assertive?.48f:tone==debate::Delivery::Suspect?.56f:.76f;tint=speaker?(tone==debate::Delivery::Regret?Color{.76f,.82f,.94f,1}:tone==debate::Delivery::Assertive?Color{1,.98f,.90f,1}:Color{.94f,.97f,1,1}):Color{other,other,other,1};}
    Sprites::SetColor(figure,tint);
   }
   debateCastTinted=focus;
  }
 }
 { // V3 다이내믹 논스톱(영상 A 16:36~17:16) : 발언마다 구도·화자 뒤 효과·화자 움직임이 함께 바뀐다
  const auto& t=l.text;auto has=[&](const char* x){return t.find(x)!=std::string::npos;};
  if(l.directed){ // 연출표가 있는 줄은 그대로 따른다(문장부호로 추측하지 않는다)
   if(l.shot>=0)shotKind=l.shot;
   if(trialdirection::has(l.fx,"swirl"))debateSwirl=std::max(debateSwirl,3.2f);
   if(trialdirection::has(l.fx,"punch")){debatePunchSeat=court::seatOf(slug);debatePunch=0;}
   if(trialdirection::has(l.fx,"shake"))if(auto* cam=actor("Camera"))Camera::Shake(cam,.022f,.22f);
   if(const auto* dir=trialdirection::find("debate",l.id);dir&&dir->contains("se"))sfx((*dir)["se"].get<std::string>());
   return;
  }
  bool shout=has("!")||has("！"),ask=has("?")||has("？"),hesitate=has("…")||has("..."),pointed=l.kind=="weak"||(l.kind=="agree"&&!l.answer.empty());
  if(shout){shotKind=11;debateSwirl=std::max(debateSwirl,3.2f);debatePunchSeat=court::seatOf(slug);debatePunch=0;if(auto* cam=actor("Camera"))Camera::Shake(cam,.022f,.22f);sfx("emo_shout");} // 기운 클로즈업 + 소용돌이 + 튀어나옴 + 흔들림
  else if(ask)shotKind=shownLine%2?6:7;      // 화자 둘레를 돈다
  else if(hesitate)shotKind=4;                // 얼굴 가까이 천천히
  else if(pointed)shotKind=shownLine%2?8:10;  // 약점 줄 : 낮게 깔아 여러 명과 함께
 }
}

void Yumeno::updateDebate(float delta){
 const auto* shotKey=v4TaskActive?"mouse0":"mouse1";
 if(v4TaskActive&&flyingEvidence.empty())v4DebateMode(lie);
 // 외침 뒤 소용돌이(카메라에 붙은 판, 천천히 돈다)와 화자 튀어나옴(짧게 커졌다가 돌아온다)
 if(auto* sw=actor("DebateSwirl")){const bool owned=v4TaskActive&&stageKind=="nonstop"&&!debate.lines.empty();bool on=owned?playingDebate&&clearTimer<=0&&debateResultTime<=0&&trialdirection::has(debate.line().fx,"swirl"):debateSwirl>0&&!debate.panic();if(on){if(!owned)debateSwirl-=delta;Scene::SetRotation(sw,{0,0,owned?debate.time*23.f:debateSwirl*-38.f});}if(on!=debateSwirlOn){debateSwirlOn=on;Components::Set(sw,"SpriteRenderer","visible",on);}}
 if(debatePunchSeat>=0){debatePunch+=delta;float k=debatePunch<.1f?1+.12f*debatePunch/.1f:1+.12f*std::exp(-(debatePunch-.1f)*7);if(auto* a=actor("Seat"+std::to_string(debatePunchSeat)))Scene::SetScale(a,{k,k,1});if(debatePunch>.9f){if(auto* a=actor("Seat"+std::to_string(debatePunchSeat)))Scene::SetScale(a,{1,1,1});debatePunchSeat=-1;}}
 bool showingResult=debateResultTime>0;updateDebateFx(delta);
 if(!flyingEvidence.empty()){
  if(shotTimeLeft<=0){
   std::string evidence=std::move(flyingEvidence);
   flyingEvidence.clear();flyingMeshes.clear();UI::SetOpacity(this,UI_ID,"Bullet",1);
   resolveDebateShot(shotX,shotY,evidence,shotLie);
  }
  return;
 }
 if(showingResult){if(debateResultTime<=0&&clearTimer<=0){debate.next();shownLine=-1;debateInputArmed=false;}return;}
 if(clearTimer>0){if((clearTimer-=delta)<=0){playingDebate=false;debateHud(false);beginScript();}return;}
 // 집중 : Shift 를 누르는 동안 시간 0.35배, 게이지 소모. 놓으면 회복.
 if(!debateInputArmed&&!held.at("mouse0")&&!held.at(shotKey))debateInputArmed=true;
 if(!held.at("Shift"))focusExhausted=false;
 bool focusing=debateInputArmed&&held.at("Shift")&&!focusExhausted&&debate.focus>0;
 if(v4.active)focusing=skillFocusTick(debateInputArmed&&held.at("Shift"),delta);else debate.focus=std::clamp(debate.focus+(focusing?-28.f:9.f)*delta,0.f,100.f);
 if(focusing&&debate.focus<=0)focusExhausted=true;
 UI::SetVisible(this,"debatefx","FocusVeil",focusing);
 {int lit=int(std::ceil(debate.focus/maximumFocus()*10));if(stageKind!="nonstop"&&lit!=shownStars){shownStars=lit;for(int k=0;k<10;k++)UI::SetTexture(this,UI_ID,"Star"+std::to_string(k),k<lit?"Assets/Art/ui/hud_starOn.svg":"Assets/Art/ui/hud_starOff.svg");}}
 bool turning=cameraTime<1;
 if(!turning)debateTime-=delta*(focusing?.35f:1);
 {int ms=std::max(0,int(debateTime*1000));char t[16];std::snprintf(t,sizeof t,"%02d:%02d:%03d",ms/60000,ms/1000%60,ms%1000);text("Timer",t);}
 if(debateTime<=0){if(v4TaskActive){lieV4.cancel();lieV4Ticks=0;shotRecoveryV4.reset();v4NoiseReset();holdTime=-1;lie=false;showBullet();}sfx("v3se_332");message("시간 초과… 처음부터!",2.f);debateTime=(v4TaskActive&&stageKind=="panic"?300.f:180.f)*trialTimeFactor()+(skillOn("debate_time")?10.f:0.f);v4ResetHearts(maxHearts);if(v4TaskActive){debate.restartRows();aimSwayV4.reset();aimPointerV4={};aimAssistV4.active=false;}else{debate.broken.assign(debate.lines.size(),false);debate.index=0;debate.time=0;}retries++;if(v4TaskActive){debateInputArmed=false;shownLine=-1;return;}}
 int priorIndex=debate.index;bool rowAdvanced=!turning&&debate.tick(delta*(focusing?.35f:1));
 if(!turning&&debate.panic())debate.advancePanicLock(delta*(focusing?.35f:1));
 if(v4TaskActive&&debate.panicRoundDone()){
  const auto task=v4Task.value("taskId",std::string());
  v4TaskQueue(Json::array({{{"type","say"},{"id",task+":panic-loop"},{"actor","mio"},{"mono",true},
   {"text","다들 서로 다른 얘길 하고 있어. 일단 한 사람 말부터 끝까지 들어 보자."}}}),"panic-restart");
  return;
 }
 if(v4TaskActive&&stageKind=="nonstop"&&!debate.panic()&&rowAdvanced&&debate.index<=priorIndex){
  if(lieV4.transformed&&!v4LieCommit(false))return;
  const auto task=v4Task.value("taskId",std::string());
  Json thoughts=Json::array();int part=0;for(const auto& thought:nonstopv4::thoughts(task))thoughts.push_back({{"type","say"},{"id",task+":loop-hint:"+std::to_string(part++)},{"actor","mio"},{"mono",true},{"text",thought}});
  v4TaskQueue(thoughts,"nonstop-loop");return;
 }
 bool changed=rowAdvanced||shownLine!=debate.index;
 if(v4TaskActive&&!turning&&debateInputArmed)for(int at:silencerv4::advanceLoud(debate,delta*(focusing?.35f:1),skillOn("silent_voice")))v4NoiseBreak(at,debate.lines[at].noiseDurability);
 if(debate.panic()){drawPanicLanes(!turning);shownLine=debate.index;}
 else if(changed){shownLine=debate.index;styleLine();} // 줄이 바뀐 프레임은 글꼴·색만, 글자는 다음 프레임(둘을 한 번에 보내면 1000개를 넘는다)
 else drawGlyphs("M",48,turning?std::vector<debate::Glyph>{}:debate.current());
 const auto& deliveryLine=debate.line();
 if(deliveryLine.readable&&!turning&&!changed&&!debateFollowPosePlayed&&!deliveryLine.followPose.empty()&&debate.t()>=deliveryLine.followAt){
  debateFollowPosePlayed=true;
  if(speakerSeat>=0&&courtFigures.contains(deliveryLine.followPose))courtPose(speakerSeat,deliveryLine.followPose);

 }
 if(deliveryLine.readable&&!lieViewOn){
  // A delivery owns the whole statement, including camera arrival. Its look
  // is established by styleLine; no independent short timer or late fade.
  if(lastDebateWashStep!=16){lastDebateWashStep=16;UI::SetOpacity(this,UI_ID,"CourtDim",1.f);}
 }
 int ni=debate.noiseIndex();
 if(ni>=0&&!noiseStyled){noiseStyled=true;for(int k=0;k<26;k++)for(auto side:{"F","B"}){auto id=std::string("N")+side+std::to_string(k);UI::SetFont(this,UI_ID,id,v4TaskActive&&!debate.panic()?"Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf":"Assets/Fonts/jua/Jua-Regular.ttf");UI::SetFontSize(this,UI_ID,id,v4TaskActive&&!debate.panic()?54:40);UI::SetColor(this,UI_ID,id,Color{1,.3f,.72f,1}); /* V3 화이트 노이즈는 분홍(영상 A 1:31 「Y-Yeah, I...?」) */}}
 auto noiseGlyphs=v4TaskActive&&turning?std::vector<debate::Glyph>{}:debate.noise();
 drawGlyphs("N",26,noiseGlyphs);
 /* 잡음 통째 그림(gpunoisehudv4 rig)은 끈다 — 글자마다 길(NF/NB)로 그린다. rig 는 예전 크기(.9·Z1250)로 구워져 지금 Debate.hpp 와 어긋난다(Claude 2026-11-04) */
 if(v4TaskActive){auto points=focusing||skillOn("ones_minds_eye")?aimskillsv4::visiblePoints(debate):std::vector<aimskillsv4::Point>{};for(int i=0;i<3;i++){auto id=i?"VPoint"+std::to_string(i):std::string("VPoint");UI::SetVisible(this,UI_ID,id,i<int(points.size()));if(i<int(points.size()))UI::SetPosition(this,UI_ID,id,{points[i].x,points[i].y});}}else{float vx=0,vy=0;bool hasV=focusing&&debate.vpoint(vx,vy);UI::SetVisible(this,UI_ID,"VPoint",hasV);if(hasV)UI::SetPosition(this,UI_ID,"VPoint",{vx,vy});}
 if(v4TaskActive){
  bool admitted=!turning&&debateInputArmed&&shotRecoveryV4.ready()&&holdTime<0&&lieV4.phase==liev4::Phase::Idle&&!held.at(shotKey);
  auto actual=aimSwayV4.step(delta,admitted,aimskillsv4::swayAmplitude(skillOn("calm_down_lv1"),skillOn("calm_down_lv2")));aimX=actual.x;aimY=actual.y;
  if(debate.panic()){
   const auto viewport=debate::panicViewport(gputrialhudv4::width,gputrialhudv4::height);
   debate.trackPanicCursor(aimX,aimY,delta,viewport[0],viewport[1]);
  }
  UI::SetPosition(this,UI_ID,"Aim",{aimX-32,aimY-32});v4AimAssist(focusing);
 }
 // updateTrial shares the size-independent canvas pointer snapshot.
 if(bullets.empty()||!debateInputArmed||(v4TaskActive&&cameraTime<1))return;
 if(v4TaskActive&&v4NoiseInput(delta)&&!held.at(shotKey)&&lieV4.phase==liev4::Phase::Idle)return;
 if(v4TaskActive){UI::SetOpacity(this,UI_ID,"Aim",shotRecoveryV4.ready()?1.f:.4f);if(!shotRecoveryV4.ready())return;}
 if(holdTime<0&&pressed("q")){bullet=(bullet+int(bullets.size())-1)%int(bullets.size());showBullet();sfx("v3se_302");} // V3 언령 바꾸기 SE302
 if(holdTime<0&&pressed("e")){bullet=(bullet+1)%int(bullets.size());showBullet();sfx("v3se_302");}
 // 사일런서 : 우클릭으로 소음 제거
 if(!v4TaskActive&&pressed("mouse0")&&debate.noiseHit(aimX,aimY)){if(ni>=0)debate.silenced[ni]=true;debate.focus=std::min(maximumFocus(),debate.focus+10);message("조용!",.6f);}
 // V4 uses the recovered charge/conversion/deferred-cost states. Legacy
 // keeps its old stake/refund behavior for compatibility.
 bool down=held.at(shotKey),lieShot=false; // V3 PC : 우클릭 = 언령 발사, 누르고 있으면 거짓 탄환 / 좌클릭 = 사일런서(StrategyWiki V3 Controls, Steam 토론)
 if(v4TaskActive){
  bool permitted=!debate.panic()&&v4Task.value("transformation",Json::object()).value("intentionalHold",false);if(!permitted&&!debate.panic()&&v4Task.contains("debate"))for(const auto& row:v4Task["debate"]["lines"])if(row.contains("lieWeak")||row.value("weak",Json::object()).value("lie",false)){permitted=true;break;}
  auto event=lieV4.advance(delta,down,skillOn("white_lie"),permitted,lieV4Ticks);
  if(event==liev4::Event::Transformed){lie=true;v4DebateMode(true);showBullet();sfx("ui_confirm");}
  if(lieV4.phase!=liev4::Phase::Idle)holdTime=holdTime<0?0:holdTime+delta;
  lieView(lieV4.phase!=liev4::Phase::Idle&&lie); /* 거짓으로 바뀐 동안(V3 : 누르고 있으면 거짓 탄환 화면) */
  if(!liev4::isShot(event))return;lieShot=event==liev4::Event::LieShot;
 }else{
  if(down){if(holdTime<0)holdTime=0;holdTime+=delta;if(!lie&&holdTime>.45f){lie=true;lieCost=debate.hearts>1;if(lieCost)--debate.hearts;showBullet();sfx("ui_confirm");}return;}
  if(holdTime<0)return;lieShot=lie;
 }
 flyingLabel=texts.count("Bullet")?texts.at("Bullet"):bullets[bullet].second;
 holdTime=-1;lie=false;showBullet();
 if(v4TaskActive){shotRecoveryV4.fire(skillOn("laser_beam"),skillOn("triger_happy"));shotDuration=shotRecoveryV4.duration();}else shotDuration=.22f;
 shotLie=lieShot;shotTimeLeft=shotDuration;shotX=aimX;shotY=aimY;++shotsFired;sfx("v3se_305"); // V3 발사(3f0500 case10)
 UI::SetTexture(this,"debatefx","ShotTrail",lieShot?"Assets/Art/ui/nonstop_refute/shot_lie.png":"Assets/Art/ui/nonstop_refute/shot_normal.png");
 if(v4TaskActive&&(stageKind=="nonstop"||debate.panic())){
  flyingEvidence=bullets[bullet].first;
  flyingMeshes.begin(flyingLabel);
  const int selected=debate.index;
  flyingImpact=debate.noiseHit(shotX,shotY)||(debate.panic()?debate.panicHit(shotX,shotY):debate.weakHit(shotX,shotY));
  debate.index=selected;
  flyingWord=shotv4::WordFlight::make(shotX,shotY,shotRecoveryV4.laser,unsigned(shotsFired*137));
  shotDuration=shotTimeLeft=flyingWord.prepare+flyingWord.duration+NONSTOP_IMPACT;
  updateDebateFx(0);
  return;
 }
 resolveDebateShot(aimX,aimY,bullets[bullet].first,lieShot);
}

void Yumeno::resolveDebateShot(float x,float y,const std::string& evidence,bool lieShot){
 if(debate.noiseHit(x,y)){if(v4TaskActive&&skillOn("murder_smash")){auto hits=silencerv4::targets(debate,silencerv4::Mode::Normal,x,y);for(int at:hits)v4NoiseBreak(at,debate.lines[at].noiseDurability);}else{if(v4TaskActive)++noiseBlockedShotsV4;sfx("v3se_339");if(v4TaskActive&&!v4LieCommit(false))return;if(stageKind!="nonstop")message("방해 발언에 막혔어 · 사일런서로 걷어 내자",1.25f);return;}}
 if(!(debate.panic()?debate.panicHit(x,y):debate.weakHit(x,y))){if(v4TaskActive){pv4::Action(presentationV4,"shot_miss",x,y);v4LieCommit(false);}return;}
 auto& l=debate.line();
 bool correct=evidence==l.answer&&lieShot==l.lie;
 if(correct){
  if(v4TaskActive)v4Judgment=lieShot?"lie":l.kind=="agree"?"agree":"refute";
  if(!v4TaskActive)onCorrect();
  float px=0,py=0;auto designated=aimskillsv4::robotTarget(l,debate.current());bool v=v4TaskActive?designated&&std::hypot(x-designated->x,y-designated->y)<16:debate.vpoint(px,py)&&std::hypot(x-px,y-py)<16;
  if(v4TaskActive)v4LieCommit(true);else if(lieShot&&lieCost)++debate.hearts;
  bool agreeing=l.kind=="agree";
  debate.broken[debate.index]=true;vBreaks+=v&&!agreeing&&!lieShot;
  // A supported blue statement can resolve the same factual claim as its yellow counterpart.
  if(agreeing)for(size_t i=0;i<debate.lines.size();++i)if(debate.lines[i].kind=="weak"&&!debate.lines[i].lie&&debate.lines[i].answer==l.answer)debate.broken[i]=true;
  if(v4TaskActive&&debate.cleared())trialScoreCapture();
  debateSuccess(agreeing?"agree":lieShot?"lie":"refute");
  if(debate.cleared())clearTimer=.15f; // Resume only after the complete cutin/crack/Break sequence.
 }else{
  if(v4TaskActive)shotRecoveryV4.wrong();
  if(v4TaskActive&&!v4LieCommit(false))return;
  sfx("v3se_311"); // V3 틀린 명중(피해 SE316 은 trial_wrong 에서)
  if(skillOn("miss_guard")&&!missGuardUsed){missGuardUsed=true;message("마술사의 손! 빗나간 탄환을 되돌렸다",1.2f);return;}
  if((v4TaskActive?v4Damage(2000):--debate.hearts)<=0&&skillOn("revive")&&!reviveUsed){reviveUsed=true;v4ResetHearts(2);message("다시 일어선다!",1.4f);return;}
  if(debate.hearts<=0){shotRecoveryV4.reset();v4NoiseReset();message("발언력이 바닥났어요… 처음부터!",2.f);v4ResetHearts(maxHearts);if(v4TaskActive){debate.restartRows();aimSwayV4.reset();aimPointerV4={};aimAssistV4.active=false;}else{debate.broken.assign(debate.lines.size(),false);debate.index=0;debate.time=0;}debateTime=(v4TaskActive&&stageKind=="panic"?300.f:180.f)*trialTimeFactor()+(skillOn("debate_time")?10.f:0.f);retries++;}
  else if(stageKind!="nonstop")message("아야! 틀렸어요~!",1.2f);
  int wrongVariant=-1;
  const Json* wrongCards=nullptr;
  if(v4TaskActive&&stage.contains("wrongCards"))wrongCards=&stage.at("wrongCards");
  else if(v4TaskActive&&stageKind=="nonstop")wrongCards=trialdirection::find("nonstopWrongCards",v4Task.value("taskId",std::string()));
  if(wrongCards&&wrongCards->contains(evidence)){
   auto variants=v4Task["queues"].value("wrongVariants",Json::array());
   const auto& cause=wrongCards->at(evidence);
   for(int n=0;n<int(variants.size());++n)if(variants[n].value("cause",std::string())==cause){wrongVariant=n;break;}
  }
  v4TaskWrong(wrongVariant);
 }
}

void Yumeno::Update(float delta){
 Input::centeredCanvas=!optionsV4.open&&(mode==Mode::Pad||mode==Mode::Gallery||mode==Mode::Title||mode==Mode::Menu);
 trialImpactCooldown=std::max(0.f,trialImpactCooldown-std::max(0.f,delta));
 gpunoisehudv4::Frame noiseFrame;gpupanichudv4::Frame panicFrame;gputrialhudv4::Frame gpuFrame;
 struct LoadingCover {Yumeno* owner;~LoadingCover(){if(scenesv4::waiting()&&!scenesv4::loadingShown)try{UI::Show(owner,"Assets/UI/LoadingV4.hbwidget.json","loadingv4");scenesv4::loadingShown=true;}catch(const std::exception& e){owner->lastError=std::string("Loading cover: ")+e.what();}}} loadingCover{this};
 sampleInput();++rhythmUpdates;
 if(scenesv4::waiting()){
  if(!scenesv4::loadingShown){UI::Show(this,"Assets/UI/LoadingV4.hbwidget.json","loadingv4");scenesv4::loadingShown=true;return;}
  if(!scenesv4::desired->requested){releaseGameplay();for(auto it=UI::owners.begin();it!=UI::owners.end();){auto id=(it++)->first;if(id!="loadingv4")UI::Remove(this,id);}}
  if(!scenesv4::poll())return;
  scenesv4::loadingShown=false;scenesv4::cover=true;UI::owners.erase("loadingv4");UI::applied.erase("loadingv4");
  // The native scene boundary retains loop music but releases one-shot voices.
  if(jingleIntro&&!jingleNext.empty())updateMusic(jingleTimer);
  if(mode==Mode::Title){titleMenu(true);UI::Show(this,"Assets/UI/LoadingV4.hbwidget.json","loadingv4");return;}
  prepareGameplay();
  if(scenesv4::court.loaded)setupCourt();else if(scenesv4::explore.loaded){auto& target=galleryReplay?galleryReplayWorld:world;target.visible=false;target.mesh.clear();target.environmentStamp.clear();exworld::begin(target,target.id,true,!galleryReplay&&v4FreeWorld()&&v4.graph.contains("campaignRevision"));exworld::camera(target);}
  if(mode==Mode::Gallery){UI::Show(this,"Assets/UI/GalleryV4.hbwidget.json","galleryv4");galleryDraw();if(galleryReplay)galleryReplayShow();}
  else if(mode==Mode::Credits)v4Credits();
  else if(v4.active&&!v4LoadPhase)v4Enter();
  else if(!v4.active&&scenesv4::court.loaded)startTrial();
  UI::Show(this,"Assets/UI/LoadingV4.hbwidget.json","loadingv4");return;
 }

 updateMusic(delta);
 if(gputrialhudv4::anagramWarming){
  if(!gputrialhudv4::warmupOverlay){UI::Remove(this,"loadingv4");UI::Show(this,"Assets/UI/LoadingV4.hbwidget.json","loadingv4");gputrialhudv4::warmupOverlay=true;return;}
  if(!gputrialhudv4::pollAnagram())return;
  v4TaskStart();if(v4LoadPhase==1&&v4TaskActive)v4LoadPhase=2;UI::Remove(this,"loadingv4");UI::Show(this,"Assets/UI/LoadingV4.hbwidget.json","loadingv4");return;
 }
 if(gputrialhudv4::warmupFrames>0||gpupanichudv4::warmFrames>0||gpunoisehudv4::warmFrames>0)return;
 // Validated restore has its own updates: do not stack cold court/UI setup
 // and task entry, or admit gameplay/modal input until presentation is ready.
 if(v4LoadPhase){try{v4LoadTick();if(scenesv4::cover){UI::Remove(this,"loadingv4");UI::Show(this,"Assets/UI/LoadingV4.hbwidget.json","loadingv4");}}catch(const std::exception& e){v4LoadPhase=0;lastError="V4 restore: "+std::string(e.what());}return;}
 if(gputrialhudv4::warmupOverlay||scenesv4::cover){UI::Remove(this,"loadingv4");gputrialhudv4::warmupOverlay=false;scenesv4::cover=false;}
 if(!ready){
  ready=true;
  art=Data::Get("Assets/Data/art.json");
  optv4::Init(optionsV4,this,[this](const std::string& action){
   if(presentationV4.initialized)pv4::Action(presentationV4,action);
   else if(action=="ui_focus")sfx("ui_select");
   else if(action=="ui_reject")sfx("v3se_000");
   else sfx(action);
  },true);
  chapterArchiveInit();galleryInit();
   titleMenu(true);
  music("bgm_title");
  return;
 }
 chapterArchiveTick();
 if(v4EndingSavePending){v4EndingTick();return;}
 if(toastTimer>0&&(toastTimer-=delta)<=0)fvis("FToast",false);
 optv4::Tick(optionsV4,delta);presentationV4.reducedMotion=optionsV4.values.reducedEffects;
 playerTick(delta);
 pv4::Tick(presentationV4,delta,mode!=Mode::Pad&&!optionsV4.open&&!v4LogOpen);
  if(optionsV4.open){
   Vec2 m,physicalMouse;Input::GetMousePositionForCanvas({1280,720},m);Input::GetMousePosition(physicalMouse);exworld::refreshViewport();m.x-=(exworld::viewport.width/exworld::viewport.fit-1280.f)*.5f;m.y-=(exworld::viewport.height/exworld::viewport.fit-720.f)*.5f;optv4::Edges e;e.wheel=mouseWheelV4;
   e.up=pressed("w")||pressed("ArrowUp");e.down=pressed("s")||pressed("ArrowDown");e.left=pressed("a")||pressed("ArrowLeft");e.right=pressed("d")||pressed("ArrowRight");
   e.confirm=pressed("Enter");e.cancel=pressed("Escape")||pressed("Backspace")||pressed("mouse1");e.click=pressed("mouse0");
   // Canvas coordinates change after a resize even when the pointer stays still.
   e.mouseMoved=physicalMouse.x!=optionsMouseX||physicalMouse.y!=optionsMouseY;e.mouseX=m.x;e.mouseY=m.y;optionsMouseX=physicalMouse.x;optionsMouseY=physicalMouse.y;optv4::Handle(optionsV4,e);
   if(!optionsV4.open&&mode==Mode::Pad&&padPageAt==5)padSystemDraw();
   if(!optionsV4.open&&mode==Mode::Title)titleMenu(true);
   if(!optionsV4.open&&mode==Mode::Trial){if(v4.active){v4CancelInput();if(v4TaskActive){v4TaskRoot(!v4QueueActive);if(playingDebate&&!v4QueueActive)debateHud(true);if(v4QueueAfter=="success"&&!v4ComicPage.empty())v4ComicComplete(true);}else if(v4.current().contains("comicPage"))v4ComicComplete(true);}else{v4TaskRoot(true);if(playingDebate)debateHud(true);}}
   return;
  }
  if(v4LogOpen){v4LogUpdate(pressed("mouse0"));return;}
  if(mode==Mode::Machine){machineUpdate(delta);return;}
  if(mode==Mode::Gallery){galleryUpdate(delta);return;}
  if(mode==Mode::Trial&&trialResultOn){if(pressed("Tab")&&!trialResultHistory){padToggle();return;}trialResultUpdate(delta);return;}
  if(mode==Mode::Trial&&v4.active&&pressed("l")){v4CancelInput();v4TaskRoot(false);v4Log(true);return;}
  if(mode==Mode::Trial&&pressed("o")){if(v4.active)v4CancelInput();v4TaskRoot(false);optv4::Open(optionsV4);return;}
  if(mode==Mode::Trial&&pressed("Tab")){padToggle();return;}
  if(mode==Mode::Trial){
   int beforeHp=v4TaskActive?v4TaskHp():debate.hearts*2000,beforeRetries=retries;
   try{updateTrial(delta);}catch(const std::exception& e){lastError=std::string("stage ")+std::to_string(stageAt)+" "+stageKind+": "+e.what();}
   if(mode==Mode::Trial&&trialImpactCooldown<=0&&((v4TaskActive?v4TaskHp():debate.hearts*2000)<beforeHp||retries>beforeRetries))sfx("v3se_316");
   return;
  }
 bool click=pressed("mouse0");enterNow=pressed("Enter");bool next=enterNow|pressed("Space")|click; // 프레임 시작에 수집한 입력을 각 모드에서 공유한다.
 if(mode==Mode::Menu&&menuVisualUpdate(delta))return;
 if((pressed("Tab")||(pressed("Escape")&&mode==Mode::Explore))&&v4GiftMode==0&&(mode==Mode::Pad||flowOn||v4.active)&&(trialEntryTime<0||mode==Mode::Pad)&&(mode==Mode::Story||mode==Mode::Pad||mode==Mode::Menu||mode==Mode::Grid||mode==Mode::Explore||mode==Mode::Map)){
  padToggle();
  return;
 }
 if(mode==Mode::Pad){updatePad(delta,click);return;}
 if(mode==Mode::Title&&difficultyOn){difficultyUpdate();return;}
 if(mode==Mode::Title&&chapterSelectOn){chapterSelectUpdate(delta);return;}
 if(mode==Mode::Title){

  updateTitle(click);
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
  if(auto* a=scenesv4::find("Seat"+std::to_string(i))){
   auto p=Scene::GetPosition(a),r=Scene::GetRotation(a);auto texture=Components::GetString(a,"SpriteRenderer","texture");
   hb::Json row{{"seat",i},{"position",{q(p.x),q(p.y),q(p.z)}},{"rotation",{q(r.x),q(r.y),q(r.z)}}};
   if(auto* back=scenesv4::find("SeatRear"+std::to_string(i))){
    auto rear=Scene::GetPosition(back);auto backTexture=Components::GetString(back,"SpriteRenderer","texture");
    row["rear"]={q(rear.x),q(rear.y),q(rear.z)};row["blackRear"]=backTexture.find("_back.webp")!=std::string::npos;
    float angle=r.y*court::PI/180;if((cam.x-p.x)*std::sin(angle)+(cam.z-p.z)*std::cos(angle)<0)texture=backTexture;
   }
   row["texture"]=texture.substr(texture.find_last_of('/')+1);cast.push_back(row);
  }
  if(auto* a=scenesv4::find("Podium"+std::to_string(i))){auto p=Scene::GetPosition(a),r=Scene::GetRotation(a);desks.push_back({{"seat",i},{"position",{q(p.x),q(p.y),q(p.z)}},{"rotation",{q(r.x),q(r.y),q(r.z)}}});}
 }
 return hb::Json{{"cast",cast},{"desks",desks}}.dump();
}
std::string Yumeno::AimStats()const{
 return Json{{"active",v4TaskActive&&playingDebate},{"desired",{aimSwayV4.desired.x,aimSwayV4.desired.y}},{"actual",{aimX,aimY}},{"physical",{aimPointerV4.physical.x,aimPointerV4.physical.y}},{"initialized",aimPointerV4.initialized},{"gain",aimskillsv4::directGain(skillOn("shift_down"),skillOn("shift_up"))},{"phase",aimSwayV4.phase},{"quadrant",aimSwayV4.quadrant},{"amplitude",aimskillsv4::swayAmplitude(skillOn("calm_down_lv1"),skillOn("calm_down_lv2"))},{"projectile",{{"label",flyingLabel},{"phase",flyingEvidence.empty()?"idle":shotDuration-shotTimeLeft<flyingWord.prepare?"prepare":shotTimeLeft>NONSTOP_IMPACT?"word":"impact"},{"aim",{shotX,shotY}},{"age",shotDuration-shotTimeLeft}}}}.dump();
}
std::string Yumeno::Stats()const{
 const char* names[]{"title","story","pad","end","trial","menu","grid","card","credits","explore","map","confirm","popup","machine","gallery"};
  Json s{{"mode",names[int(mode)]},{"chapter",chapterAt},{"beat",beat},{"event",event},{"pool",ctxPool},{"spot",ctxSpot},{"speaker",speaker},{"portrait",portrait},{"line",line},{"coins",coins},{"cards",int(cards.size())},{"gifts",int(gifts.size())},{"slots",slots},{"room",roomAt},{"mapSelection",mapHover},{"roomCount",rooms.size()},{"padPage",padPageAt},{"padRow",padRow},{"giftPage",giftPage},{"giftChoices",gridSlugs},{"notes",notes.size()}};
 if(v4.active){s["contentVersion"]="v4";s["node"]=v4.node;s["v4Kind"]=v4.current().value("type","");s["logCount"]=v4.log.size();if(!v4LastOutcome.empty())s["lastTaskOutcome"]=v4LastOutcome;s["routeBlocked"]=!v4.blocked.empty();s["auto"]=v4Auto();if(v4TaskActive){s["taskId"]=v4Task.value("taskId",std::string());s["taskQueue"]=v4QueueActive;s["taskLink"]=v4TaskLinks;s["trialHp"]=v4TaskHp();s["queueAfter"]=v4QueueAfter;}}
  if(mode==Mode::Gallery||mode==Mode::Machine)s["auto"]=v4Auto();
 if(mode==Mode::Gallery)s["gallery"]={{"reading",galleryReading},{"replay",galleryReplay},{"at",galleryReplayAt},{"count",galleryReplayNodes.size()},{"node",galleryReplay&&galleryReplayAt<int(galleryReplayNodes.size())?galleryReplayNodes[galleryReplayAt]:std::string()},{"worldActive",galleryReplayWorld.active},{"worldVisible",galleryReplayWorld.visible},{"space",galleryReplayWorld.id},{"phase",galleryReplayWorld.environmentPhase},{"music",musicCue}};
 if(flowOn&&mode!=Mode::Trial&&mode!=Mode::Gallery&&mode!=Mode::Machine){s["beatKind"]=currentBeat().value("t","");s["auto"]=autoFlow();}
 if(v4.active)s["giftV4"]={{"mode",v4GiftMode},{"actor",v4GiftActor},{"item",v4GiftItem},{"choices",v4GiftChoices},{"claims",growthV4.giftClaims.size()},{"present",v4FreeActors()},{"role",v4.current().value("selectionRole",std::string())},{"court",v4Court}};
 s["scenes"]={{"court",scenesv4::court.loaded},{"explore",scenesv4::explore.loaded},{"loading",scenesv4::waiting()||scenesv4::cover},{"widgets",UI::owners.size()}};s["world"]=exworld::stats(world);s["audioV4"]=pv4::Stats(presentationV4);s["options"]=optv4::Stats(optionsV4);
 if(mode==Mode::Menu)s["choice"]={{"count",menuCount},{"hover",menuHover},{"first",menuFirst},{"pending",menuPending},{"commits",menuCommits}};
 if(mode==Mode::Pad&&padPageAt==5)s["padSystem"]={{"view",padSystemView},{"column",padSystemColumn},{"slot",padStorageRow},{"themeRow",padThemeRow},{"themeFirst",padThemeFirst},{"themeSaveNo",padThemeSaveNo},{"confirm",padConfirmChoice},{"busy",padStorageBusy},{"savePhase",padSavePhase},{"savePart",padSaveWriter.at},{"saveParts",padSaveWriter.package.parts.size()},{"saveClean",padSaveWriter.clean},{"saveObsolete",padSaveWriter.obsolete.size()},{"log",v4LogOpen},{"logFirst",v4LogRow},{"logCursor",v4LogCursor}};
 s["difficulty"]={{"logic",difficultyV4.logic},{"action",difficultyV4.action},{"open",difficultyOn},{"row",difficultyRow}};if(difficultyOn)s["auto"]=v4Auto();
  if(!lastError.empty())s["error"]=lastError;
  if(mode==Mode::Pad&&padPageAt>=0){auto rows=padRows();s["padActions"]=Json::array();for(auto& row:rows)s["padActions"].push_back(row.first);s["padSelectedId"]=padRow>=0&&padRow<int(rows.size())?rows[padRow].first:"";s["padFirst"]=padListFirst;if(padPageAt==3){s["padReportPage"]=padReportPage;s["padReportPages"]=padPageAt==3?padReportPages():0;s["padReportActor"]=padPageAt==3?padReportActor():"";s["padReportVisible"]=padReportVisible;s["padSkillVisible"]=padSkillVisible;s["padSkillRow"]=padSkillRow;}if(padPageAt==4){s["padRulesVisible"]=padRulesVisible;s["padRulesTransition"]=padRuleTimer>0;s["padRulesTarget"]=padRuleTarget;s["padRulesCount"]=padRuleIds().size();}s["padGiftVisible"]=padGiftVisible;s["padEvidenceVisible"]=padEvidenceVisible;s["padEvidenceImage"]=padEvidenceImage;s["padEvidenceImages"]=padEvidenceImages;s["padPrimaryHintVisible"]=padHintRow>=0;}
 if(mode==Mode::Trial){s["stage"]={{"index",stageAt},{"count",int(stages.size())},{"kind",stageKind},{"script",inScript},{"hearts",debate.hearts},{"selection",optHover}};s["auto"]=autoAction();}
 if(mode==Mode::Trial)s["presentation"]={{"nonstopIntro",debateIntroTime>=0},{"elapsed",debateIntroTime},{"duration",court::nonstopDuration(int(bullets.size()))},{"loadStart",court::NONSTOP_SWEEP},{"focusStart",court::nonstopFocusStart(int(bullets.size()))},{"introPhase",debateIntroTime<0?"active":debateIntroTime<court::NONSTOP_SWEEP?"sweep":debateIntroTime<court::nonstopFocusStart(int(bullets.size()))?"load":"focus"},{"ammoCount",bullets.size()},{"loaded",debateIntroLoaded},{"timer",debateTime},{"statementTime",debate.time},{"inputArmed",debateInputArmed},{"camera",{cam.x,cam.y,cam.z,cam.yaw,cam.pitch,cam.roll}}};
 if(mode==Mode::Trial)if(auto* a=scenesv4::find("Camera")){auto r=Scene::GetRotation(a);s["presentation"]["sceneRotation"]={r.x,r.y,r.z};}
 if(v4TaskActive&&stageKind=="lie")s["lieV4"]={{"held",v4LieHeld},{"transformed",lie},{"resultTime",debateResultTime},{"result",debateResult},{"targets",optRects}};
 if(v4TaskActive&&stageKind=="mindmine"){int covered=0;for(const auto& image:mineV4.images)if(image.id==mineAnswer)for(int cell:image.cells)covered+=mineV4.cells[cell]>=0;s["mineV4"]={{"last",mineV4.last},{"clicks",mineV4.clicks},{"feedback",mineV4.feedback},{"state",int(mineV4.state)},{"successTime",mineSuccessTimeV4},{"successPhase",mineSuccessPhaseV4},{"time",mineV4.time},{"covered",covered},{"aim",{aimX,aimY}},{"paint",minePaintAt},{"width",mineV4.width},{"height",mineV4.height},{"boardRect",{minelayoutv4::Board(mineV4.width).left,minelayoutv4::Board(mineV4.width).top,minelayoutv4::Board(mineV4.width).width,minelayoutv4::Board(mineV4.width).height}},{"questionVisible",mineQuestionVisibleV4}};}
 if(v4TaskActive&&stageKind=="mindmine"&&v4.graph.contains("campaignRevision")){
  auto choices=Json::object();for(const auto& image:mineV4.images)if(!image.correct)choices[stage.at("regions").at(image.id).at("id").get<std::string>()]=autoAction(image.id);
  s["mineV4"]["wrongInputs"]=std::move(choices);
 }
 if(mode==Mode::Trial)if(auto* a=scenesv4::find("LieWorldGrade"))s["presentation"]["worldNegative"]=Components::GetFloat(a,"PostProcessVolume","weight");
 if(mode==Mode::Trial&&playingDebate&&!debate.lines.empty()){
  auto& l=debate.line();int broken=0;for(bool b:debate.broken)broken+=b;
  Json weakPoint=nullptr;int front=0,back=0;
  for(auto& g:debate.current()){(g.front?front:back)++;if(weakPoint.is_null()&&g.weak&&g.front&&g.opacity>.5f&&g.x>80&&g.x<1200&&g.y>40&&g.y<620)weakPoint={g.x,g.y};}
  float vx=0,vy=0;bool v=false;if(v4TaskActive){if(auto point=aimskillsv4::robotTarget(l,debate.current())){v=true;vx=point->x;vy=point->y;}}else v=debate.vpoint(vx,vy);
  s["trial"]={{"sampledRightHeld",held.at("mouse1")},{"debate",debateAt},{"index",debate.index},{"kind",l.kind},{"motion",int(l.motion)},{"answer",l.answer},{"needLie",l.lie},{"hearts",debate.hearts},{"broken",broken},{"vBreaks",vBreaks},{"focus",debate.focus},{"bullet",bullets.empty()?"":bullets[bullet].first},{"lie",lie},{"aim",{aimX,aimY}},{"weakPoint",weakPoint},{"vpoint",v?Json{vx,vy}:Json(nullptr)},{"glyphsFront",front},{"glyphsBack",back},{"noise",debate.noiseIndex()},{"noiseSilenced",std::count(debate.silenced.begin(),debate.silenced.end(),true)},{"noiseDebris",debate.noiseDebris.size()},{"noiseDamage",debate.noiseDamage},{"clearing",clearTimer>0||debateResultTime>0},{"camera",cameraAngle},{"speakerSeat",speakerSeat},{"turning",cameraTime<1},{"shots",shotsFired},{"shotInFlight",!flyingEvidence.empty()},{"shotButton",v4TaskActive?"left":"right"},{"noiseButton",v4TaskActive?"right":"left"},{"shotRecovery",{{"phase",int(shotRecoveryV4.phase)},{"frames",shotRecoveryV4.frames},{"ready",shotRecoveryV4.ready()},{"laser",shotRecoveryV4.laser}}},{"result",debateResult},{"resultTime",debateResultTime},{"charge",holdTime},{"chargeRequired",v4TaskActive?62.f/60:.45f},{"liePending",v4TaskActive?lieV4.pending:0},{"liePhase",int(lieV4.phase)},{"hp",v4TaskActive?v4TaskHp():debate.hearts*2000},{"focusExhausted",focusExhausted}};
 }
 if(mode==Mode::Trial&&playingDebate&&!debate.panic()){
  s["trial"]["noiseBlockedShots"]=noiseBlockedShotsV4;s["trial"]["noiseBlockPoint"]=Json(nullptr);s["trial"]["noiseRows"]=Json::array();
  for(const auto& g:debate.current())if(g.weak&&g.front&&g.opacity>.99f&&g.text!=" "&&debate.noiseHit(g.x,g.y)){s["trial"]["noiseBlockPoint"]={g.x,g.y};break;}
  for(int at:debate.noiseIndices())s["trial"]["noiseRows"].push_back({{"index",at},{"id",debate.lines[at].id},{"durability",debate.lines[at].noiseDurability},{"damage",at<int(debate.noiseDamage.size())?debate.noiseDamage[at]:0},{"host",debate.lines[at].noiseFor}});
  s["trial"]["noiseGlyphInk"]=Json::array();{auto glyphs=debate.noise();for(int i=0;i<int(glyphs.size())&&i<26;i++){const auto& g=glyphs[i];if(g.opacity>.01f&&glyphdisplayv4::hasInk(g.text))s["trial"]["noiseGlyphInk"].push_back(std::string(g.front?"NF":"NB")+std::to_string(i));}}
 }
 if(mode==Mode::Trial&&playingDebate&&debate.panic()){s["trial"]["lanes"]=Json::array();for(int n=0;n<3;n++)s["trial"]["lanes"].push_back({{"line",debate.laneLine(n)},{"time",std::round(debate.laneTime[n]*100)/100},{"glyphs",debate.panicGlyphs(n).size()}});}
 if(v4TaskActive)s["taskInputArmed"]=v4TrialInputArmed;
 if(v4TaskActive&&stageKind=="scrum")s["scrumV4"]={{"pair",scPair},{"mash",mash},{"entry",scrumT},{"feedback",scrumWait},{"phase",scrumV4.phase},{"success",scrumV4.success},{"elapsed",scrumV4.elapsed},{"hp",scrumHpV4}};
 if(v4TaskActive&&stageKind=="climax")s["comicV4"]={{"placed",v4TaskLinks},{"filledSlots",comicProgressV4.placed},{"autoFilled",comicProgressV4.automatic},{"autoResponses",comicProgressV4.responded.size()},{"review",v4ComicReview},{"replay",v4ComicReplay},{"replayAct",v4ComicReplayAt},{"spread",v4ComicSpread},{"cursor",v4ComicCursor},{"stock",optHover},{"stockPage",v4ComicStockPage},{"stockCount",v4ComicStock.size()},{"zoom",v4ComicZoom},{"placing",v4ComicPlacing>=0},{"placeTicks",v4ComicPlaceTicks}};
 if(v4TaskActive&&stageKind=="climax"){s["comicV4"]["pageCount"]=comicv4ui::count(stage);s["comicV4"]["pageSlots"]=comicv4ui::slots(stage,v4ComicSpread);s["comicV4"]["slotRects"]=Json::array();s["comicV4"]["slotPages"]=Json::array();for(int i=0;i<int(stage["slots"].size());i++){s["comicV4"]["slotRects"].push_back(comicv4ui::rect(stage,i));s["comicV4"]["slotPages"].push_back(comicv4ui::page(stage,i));}}
 if(v4TaskActive&&stageKind=="climax"){
  auto& c=s["comicV4"];c["expanded"]=v4ComicExpanded;c["pageTurning"]=v4ComicPageTurnV4<1;c["stockAnimating"]=v4ComicStockAnimationTimeV4>=0;c["time"]=stageTime;c["respondedCount"]=comicProgressV4.responded.size();c["feedback"]=v4ComicFeedbackV3>=0;c["unlockIndex"]=comicProgressV4.stockUnlockIndex;
  if(stage.at("comicPresentation").contains("storyStock")){
   auto remaining=Json::array();int ready=0;
   for(int i=0;i<int(v4ComicStock.size());i++){
    remaining.push_back(comicProgressV4.stockRemaining(i));
    if(comicProgressV4.stockOrigins[i]>=0&&comicProgressV4.stockReady(i))++ready;
   }
   c["readyAnswers"]=ready;c["remaining"]=std::move(remaining);
   c["selectedOrigin"]=comicProgressV4.stockValid(optHover)?comicProgressV4.stockOrigins[optHover]:-1;
  }else{
   c["stockState"]=Json::array();
   for(int i=0;i<int(v4ComicStock.size());i++)c["stockState"].push_back({{"originSlot",v4ComicStock[i]["originSlot"]},{"remaining",comicProgressV4.stockRemaining(i)},{"available",comicProgressV4.stockReady(i)},{"unlocking",comicProgressV4.stockUnlockIndex==i},{"used",comicProgressV4.stockUsed(i)}});
  }
 }

 if(trialPickerOn)s["trialPicker"]=Json::parse(TrialPickerStats());
 s["endingV4"]={{"kind",modeEndKindV4},{"time",modeEndTimeV4},{"after",modeEndAfterV4},{"climaxConsumed",climaxEndDoneV4}};
 s["fractureV4"]={{"id",fractureSerialV4},{"phase",fracturePhaseV4},{"supported",fractureSupportedV4}};
 s["solutionV4"]={{"frame",solutionFrameV4},{"pending",solutionPendingV4},{"consumed",solutionConsumedV4}};
 if(v4TaskActive&&stageKind=="anagram")s["anagramV4"]={{"filled",anaFilled},{"pending",anagramV4.pending},{"hp",anagramV4.hp},{"time",stageTime},{"question",anagramQuestionV4},{"light",lightX},{"focus",debate.focus},{"lightMode",anagramLightV4.mode},{"spotRadius",spot},{"orb0",orbs.empty()?Json::array():Json::array({orbs[0].x,orbs[0].y})}};
 if(stageKind=="armament")s["armamentV4"]={{"intro",armIntro},{"lastIntro",armLastIntro},{"finish",armFinish},{"fever",armingV4.fever},{"mental",debate.focus},{"combo",armingV4.combo},{"type",int(armingV4.current.type)},{"beat",armBeat},{"hud",armHudShown},{"tension",armingV4.tension},{"retries",retries},{"selected",armPiecesV4.count},{"order",armPiecesV4.order},{"layout",armOrder},{"final",armFinal},{"transition",armPiecesV4.transition},{"settled",armPiecesV4.settled},{"hp",armingV4.hp},{"opponent",armingV4.opponent},{"choices",v4ArmChoices},{"noteIndex",armHits},{"button",armingV4.current.button}};
 if(stageKind=="armament"){auto& a=s["armamentV4"];a["maxHp"]=armingV4.maxHp;a["obscurerActive"]=armRhythmV4.obscureActive;a["obscurerIndex"]=armRhythmV4.obscureIndex;a["obscurerPosition"]={armRhythmV4.obscureX,armRhythmV4.obscureY};a["questionRound"]=armQuestionPhase;a["timeLimit"]=stageLimit;a["rhythmSpeed"]=armRhythmV4.speed;a["hitHalfWindow"]=armingV4.hitHalfWindow();a["damageScale"]=armingV4.viability;a["phase"]=armRhythmV4.phase;a["totalOpponent"]=armingV4.totalOpponent;a["clock"]=std::round(double(armRhythmV4.clock)*1000)/1000;a["judged"]=armRhythmV4.judged;Json notes=Json::array();for(const auto& n:armRhythmV4.live)if(!n.done&&notes.size()<8)notes.push_back({{"id",n.id},{"slot",n.slot},{"phrase",n.phrase},{"row",n.source->row},{"type",int(n.note.type)},{"key",n.note.button},{"due",std::round(double(n.target-armRhythmV4.clock)*1000)/1000},{"held",n.note.held},{"release",n.heldSince>=0?std::round(double(n.note.holdFrames/60.f-(armRhythmV4.clock-n.heldSince))*1000)/1000:-1.},{"power",n.note.mashPower},{"progress",n.note.progress},{"x",n.source->x},{"y",n.source->y}});a["notes"]=notes;}

 if(v4TaskActive&&stageKind=="showdown"&&stage.contains("showdownV4")&&!showdownV4.groups.empty()){auto* current=showdownV4.current();s["showdownV4"]={{"phase",int(showdownV4.phase)},{"group",showdownV4.group},{"entry",showdownV4.entry},{"statement",current?current->id:""},{"blade",current&&current->blade},{"decoy",current&&current->decoy},{"blades",int(bladeIds.size())},{"hitsLeft",showdownV4.remainingHits()},{"gauge",showdownV4.gauge},{"angle",showdownV4.angle},{"hp",showdownV4.hp},{"intro",sdIntro},{"remaining",showdownV4.remaining},{"retries",retries},{"inScript",inScript},{"playing",playingDebate},{"result",debateResultTime},{"brk",sdBreak},{"talk",sdTalkOn},{"adv",sdAdvT},{"restart",restartStage},{"draw",sdDraw}};}
 if(gputrialhudv4::showdown&&stageKind=="showdown"){auto points=Json::array();for(const auto& g:v4ShowdownGlyphs())if(g.visible&&points.size()<3)points.push_back({g.index,g.center.x,g.center.y});s["showdownV4"]["points"]=points;}
 s["gpuPanicHud"]={{"slots",gpupanichudv4::slots()},{"ready",gpupanichudv4::ready},{"warming",gpupanichudv4::warmFrames>0},{"error",gpupanichudv4::error}};if(!gpupanichudv4::error.empty())s["error"]=gpupanichudv4::error;if(mode==Mode::Trial&&playingDebate&&debate.panic()){auto points=Json::array();for(int lane=0;lane<3;lane++){auto gs=debate.panicGlyphs(lane);for(int i:{0,int(gs.size()/2),int(gs.size())-1})if(i>=0&&i<int(gs.size())&&gs[i].text!=" ")points.push_back({lane,i,gs[i].x,gs[i].y});}s["gpuPanicHud"]["modelPoints"]=points;}
 s["gpuNoiseHud"]={{"ready",gpunoisehudv4::ready},{"warming",gpunoisehudv4::warmFrames>0},{"error",gpunoisehudv4::error}};if(!gpunoisehudv4::error.empty())s["error"]=gpunoisehudv4::error;
 if(mode==Mode::Trial&&playingDebate&&debate.panic()){auto gs=debate.noise();auto points=Json::array();for(int i:{0,std::min(25,int(gs.size()/2)),std::min(25,int(gs.size())-1)})if(i>=0&&i<int(gs.size())&&gs[i].text!=" ")points.push_back({i,gs[i].x,gs[i].y,gs[i].scale,gs[i].opacity,gs[i].front});s["gpuNoiseHud"]["panicPoints"]=points;}
 if(gpunoisehudv4::ready||(mode==Mode::Trial&&playingDebate&&!debate.panic())){auto rows=Json::array(),points=Json::array();auto rounded=[](float v){return std::round(double(v)*1000)/1000;};for(int i=0;i<3;i++){const auto& r=gpunoisehudv4::rows[i];if(r.visible)rows.push_back({i,r.key,rounded(r.time),r.start,r.count,r.shown});}if(mode==Mode::Trial&&playingDebate&&!debate.panic()){auto pool=debate.noiseIndices();for(int slot=0;slot<int(pool.size());slot++){auto gs=debate.noiseGlyphs(pool[slot],slot);for(int i:{0,int(gs.size()/2),int(gs.size())-1})if(i>=0&&i<int(gs.size())&&gs[i].text!=" ")points.push_back({slot,i,rounded(gs[i].x),rounded(gs[i].y),rounded(gs[i].opacity),pool[slot]});}}s["gpuNoiseHud"]["rows"]=rows;s["gpuNoiseHud"]["modelPoints"]=points;}
 s["gpuTrialHud"]={{"batched",gputrialhudv4::useBatches},{"scope",gputrialhudv4::renderScope},{"ready",gputrialhudv4::ready},{"warming",gputrialhudv4::warmupFrames>0||gputrialhudv4::warmupOverlay},{"timer",gputrialhudv4::timer},{"error",gputrialhudv4::error}};if(!gputrialhudv4::error.empty())s["error"]=gputrialhudv4::error;if(gputrialhudv4::renderScope=="debate"&&!debate.lines.empty()&&!debate.panic()){auto gs=debate.current();auto rounded=[](float v){return std::round(double(v)*1000)/1000;};auto points=Json::array();for(int i:{0,int(gs.size()/2),int(gs.size())-1})if(i>=0&&i<int(gs.size())&&gs[i].text!=" ")points.push_back({i,rounded(gs[i].x),rounded(gs[i].y),gs[i].front});s["gpuTrialHud"]["modelPoints"]=points;}
 // Diagnostic coordinates need three decimals, not seventeen-digit wire strings.
 // Preserve the native4096-character port and every diagnostic field.
 if(v4TaskActive&&(stageKind=="nonstop"||stageKind=="climax"||stageKind=="mindmine")){
  auto compact=[](auto&& self,Json& value)->void{if(value.is_number_float())value=std::round(value.get<double>()*1000.)/1000.;else if(value.is_array()||value.is_object())for(auto& child:value)self(self,child);};compact(compact,s);
 }
 return s.dump();
}

#include "EndingPresentationV4.hpp"
#include "NonstopSourceHudV4.hpp"
#include "DebatePresentation.hpp"
#include "TrialRunner.hpp"
#include "ArmamentPresentationV4.hpp"
#include "ArmamentGameplayV4.hpp"
#include "AnagramPresentationV4.hpp"
#include "Flow.hpp"
#include "Explore.hpp"
#include "Pad.hpp"
#include "V4Story.hpp"
#include "ChapterSelectV4.hpp"
#include "DifficultyPresentationV4.hpp"
#include "V4Explore.hpp"
#include "ExploreReactionPresentationV4.hpp"

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
 if(!playingDebate)return;v4AppliedDebateMode=-1;
 for(auto& l:debate.lines)if(l.kind=="weak"){l.lie=outcome==1;if(outcome==2)l.kind="agree";break;}
}

#include "V4Tasks.hpp"
#include "TrialResultPresentationV4.hpp"
#include "V4Gifts.hpp"
#include "MachinePresentationV4.hpp"
#include "GalleryPresentationV4.hpp"
#include "V4Showdown.hpp"
#include "V4ScrumV3.hpp"
#include "V4Comic.hpp"

#include "RuntimeLifecycleV4.hpp"
