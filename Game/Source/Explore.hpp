// 탐색 (docs/spec/16 §1-1·§2·§3) : 지도 → 방(1인칭 배경 + 서 있는 인물 + 조사 대상) → 조사/대화.
// 수사 : 방 = 수사 장면, 조사 대상 = 장면 안 break 구간. 자유행동 : 장소마다 인물이 서 있고, 말을 걸면 「함께 시간을 보낼까?」.
// Flow.hpp 다음에 include. 위젯 W_Explore 좌표는 tools/create-project.mjs 와 같다.
namespace exui {
const char* ID="explore";
constexpr float BG_W=1600,BG_H=900,PAN=160; // 배경은 화면보다 넓게 깔고 좌우로 돌아본다
constexpr float MAP_X=700,MAP_Y=96,MAP_W=520,MAP_H=56,MAP_STEP=62;
constexpr float CF_YES_X=380,CF_NO_X=660,CF_Y=360,CF_W=220,CF_H=50;
const char* const PLACES[]{"중앙 광장","호텔 로비","호텔 라운지","푸드코트","의무실","기념품샵","호텔 식당"}; // 이벤트가 없는 인물이 서 있을 곳
}

// 받침 있으면 b, 없으면 a (예 : 레이와 / 미오와 / 린과)
std::string josa(const std::string& word,const std::string& a,const std::string& b){
 if(word.size()<3)return a;auto s=word.substr(word.size()-3);unsigned c=((unsigned char)s[0]&0x0F)<<12|((unsigned char)s[1]&0x3F)<<6|((unsigned char)s[2]&0x3F);
 return c>=0xAC00&&c<=0xD7A3&&(c-0xAC00)%28?b:a;
}
void Yumeno::etext(const std::string& id,const std::string& v){if(etexts.count(id)&&etexts[id]==v)return;etexts[id]=v;UI::SetText(this,exui::ID,id,v);}
void Yumeno::evis(const std::string& id,bool v){if(evisible.count(id)&&evisible[id]==v)return;evisible[id]=v;UI::SetVisible(this,exui::ID,id,v);}
void Yumeno::hideExplore(){
 exworld::visible(world,false);
 for(auto id:{"ExBg","ArL","ArR","AreaBand","AreaIcon","AreaName","Mini","ExHint","LblBand","LblText","Cross","MapBack","MapImg","MapPlace","MapWho","MapHead","MapSub","MapHint","CfShade","CfBox","CfText","CfYesP","CfYes","CfNoP","CfNo"})evis(id,false);
 for(int i=0;i<6;i++)evis("Fig"+std::to_string(i),false);
 for(int i=0;i<10;i++){evis("MiniDot"+std::to_string(i),false);evis("Spark"+std::to_string(i),false);}
 for(int i=0;i<9;i++){evis("MapP"+std::to_string(i),false);evis("MapT"+std::to_string(i),false);for(int k=0;k<4;k++)evis("MapF"+std::to_string(i)+"_"+std::to_string(k),false);}
}

// ── 지도 : 수사 현장 / 자유행동 장소 목록 ─────────────────────────
void Yumeno::showMap(){
 hideFlow();hideExplore();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);mode=Mode::Map;
 exworld::load(world);
 auto& b=currentBeat();bool inv=b.value("t","")=="investigate";
 rooms.clear();
 if(inv){
  for(int i=0;i<int(b["spots"].size());i++){auto& s=b["spots"][i];Room r;r.spot=i;r.name=s.value("spot","");r.bg=s.value("bg","");
   for(auto& p:s["people"])if(inPark(p.get<std::string>()))r.people.push_back(p.get<std::string>());
   for(int k=0;k<int(s["objects"].size());k++){auto& o=s["objects"][k];r.objects.push_back({o.value("name",""),o.value("from",0),o.value("to",0),o.value("who",""),k});}
   r.done=roomDone(r);rooms.push_back(r);}
 }else{ // 자유행동 : 이벤트 장소마다 그 인물, 이벤트가 없는 인물은 기본 장소에
  std::map<std::string,int> at;
  auto roomFor=[&](const std::string& place,const std::string& bg)->Room&{if(!at.count(place)){at[place]=int(rooms.size());Room r;r.name=place;r.bg=bg;rooms.push_back(r);}return rooms[at[place]];};
  std::set<std::string> placed;
  for(auto& p:b["pool"]){auto who=p.value("who","");if(!inPark(who)||seen.count(p.value("id",""))||placed.count(who))continue;placed.insert(who);
   roomFor(p.value("place","중앙 광장"),p.value("bg","plaza_day")).people.push_back(who);}
  int k=0;for(auto s:{"rei","sora","ken","nana","riku","akari","yuu","koto","satsuki","taiga","rin","sho","ai","haruka","kaede"}){
   if(!inPark(s)||placed.count(s))continue;auto place=exui::PLACES[(k++*5+chapterAt)%7];
   roomFor(place,"").people.push_back(s);}
  for(auto& r:rooms)if(r.bg.empty()){for(auto& [w,prefixes]:std::vector<std::pair<std::string,std::string>>{{"광장","plaza_day"},{"로비","hotel_lobby"},{"라운지","hotel_lounge_day"},{"푸드코트","foodcourt"},{"의무실","infirmary"},{"기념품","souvenir_shop"},{"식당","hotel_dining"}})if(r.name.find(w)!=std::string::npos)r.bg=prefixes;if(r.bg.empty())r.bg="plaza_day";}

 }
 // The flow owns accessible destinations; the catalogue does not grant access.
 world.roomIds.clear();std::set<std::string> needed;
 for(auto& r:rooms){std::string explicitId;
  if(inv&&r.spot>=0)explicitId=b["spots"][r.spot].value("space_id","");
  else if(b.contains("pool"))for(auto& pool:b["pool"])if(pool.value("place","")==r.name){explicitId=pool.value("space_id","");break;}
  auto id=exworld::resolve(world,r.name,r.bg,explicitId);world.roomIds.push_back(id);if(!id.empty())needed.insert(id);}
 // Only intermediary rooms on paths between current destinations are walkable.
 // Their empty objects never create new clues or dialogue and cannot finish a beat.
 std::set<std::string> transit;
 if(!needed.empty())for(auto& id:needed)for(auto& step:exworld::route(world,*needed.begin(),id))if(!needed.count(step))transit.insert(step);
 for(auto& id:transit){if(id=="inspection_hall_changed"&&needed.count("inspection_hall_normal"))continue;
  if(id=="inspection_hall_normal"&&needed.count("inspection_hall_changed"))continue;
  Room r;r.name=world.data["instances"][id].value("label",id);r.spot=-1;r.done=true;rooms.push_back(r);world.roomIds.push_back(id);}
 mapHover=std::clamp(mapHover,0,std::max(0,int(rooms.size())-1));
 Vec2 mouse;Input::GetMousePositionForCanvas({1280,720},mouse);mapMouseX=mouse.x;mapMouseY=mouse.y;
 renderMap();
}
void Yumeno::renderMap(){
 bool inv=currentBeat().value("t","")=="investigate";int page=mapHover/9;
 evis("MapBack",true);evis("MapHead",true);evis("MapSub",true);evis("MapHint",true);mapPreview();
 etext("MapHead",inv?"수사 — 어디를 조사할까?":"자유행동 — 누구와 보낼까?");
 etext("MapSub",(inv?"현장 "+std::to_string(rooms.size())+"곳":"남은 시간 "+std::to_string(slots)+"번   ◎ "+std::to_string(coins))+"   "+std::to_string(page+1)+" / "+std::to_string(std::max(1,(int(rooms.size())+8)/9)));
 etext("MapHint",inv?"W/S 선택 · Enter 이동 · Esc 돌아가기":"W/S 선택 · Enter 이동 · G 캡슐 머신");
 for(int i=0;i<9;i++){int r=page*9+i;bool on=r<int(rooms.size());auto n=std::to_string(i);evis("MapP"+n,on);evis("MapT"+n,on);
  for(int k=0;k<4;k++){auto f="MapF"+n+"_"+std::to_string(k);bool face=on&&k<int(rooms[r].people.size());evis(f,face);
   if(face){auto s=rooms[r].people[k];auto img=artPath("pad","face_"+s,"pad",".webp");UI::SetTexture(this,exui::ID,f,img.empty()?"Assets/Art/sprites/"+s+"/"+s+"_C01.webp":img);}}
  if(!on)continue;
  etext("MapT"+n,(rooms[r].done?"✓ ":"")+rooms[r].name);
  UI::SetTexture(this,exui::ID,"MapP"+n,r==mapHover?"Assets/Art/ui/map_item_on.svg":"Assets/Art/ui/map_item.svg");}
 hud();fvis("FHud",true);
}

bool Yumeno::roomDone(const Room& r)const{
 if(r.spot<0)return true;
 auto& s=currentBeat()["spots"][r.spot];
 for(auto& o:r.objects)if(!seen.count(s.value("id","")+"#"+std::to_string(o.index)))return false;
 return true;
}
// 지도 왼쪽 : 가리킨 장소 미리보기 + 그곳에 있는 사람
void Yumeno::mapPreview(){
 if(mapHover<0||mapHover>=int(rooms.size()))return;auto& r=rooms[mapHover];
 auto img=r.bg.rfind("cg:",0)==0?artPath("cg",r.bg.substr(3),"cg",".webp"):artPath("backgrounds",r.bg,"bg",".webp");if(world.loaded&&mapHover<int(world.roomIds.size())&&!world.roomIds[mapHover].empty())img="Assets/Art/explore3d/atlas.svg";evis("MapImg",!img.empty());if(!img.empty())UI::SetTexture(this,exui::ID,"MapImg",img);
 std::string who;for(auto& p:r.people)who+=(who.empty()?"":" · ")+nameOf(p);
 etext("MapPlace",r.name);etext("MapWho",who.empty()?std::string(" "):who);evis("MapPlace",true);evis("MapWho",true);
}
int Yumeno::mapAt(float x,float y)const{
 if(x<exui::MAP_X||x>exui::MAP_X+exui::MAP_W||y<exui::MAP_Y)return -1;
 int i=int((y-exui::MAP_Y)/exui::MAP_STEP);
 return i<9&&mapHover/9*9+i<int(rooms.size())&&y-exui::MAP_Y-i*exui::MAP_STEP<=exui::MAP_H?mapHover/9*9+i:-1;
}

// ── 방 : 배경을 넓게 깔고, 인물은 바닥에 서 있고, 조사 대상은 화면 곳곳 ──────
void Yumeno::enterRoom(int i){
 roomAt=i;crossOver=-1;auto& r=rooms[i];panX=0;sfx("sfx_door");
 hideExplore();hideFlow();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);
 auto bg=r.bg.rfind("cg:",0)==0?artPath("cg",r.bg.substr(3),"cg",".webp"):artPath("backgrounds",r.bg,"bg",".webp"); // 범죄 현장은 사망 CG
 evis("ExBg",true);if(!bg.empty()){UI::SetTexture(this,exui::ID,"ExBg",bg);lastBackground=bg;if(currentBeat().value("t","")=="investigate")sceneBackground=bg;}
 for(auto id:{"ArL","ArR","AreaBand","AreaIcon","AreaName","Mini","Cross"})evis(id,true);
 etext("AreaName",r.name);
 evis("ExHint",false);
 // 조사 대상 자리 : 배경 가로를 고르게 나눠 바닥~벽 높이에 둔다(인물은 사이사이)
 hotspots.clear();
 int n=int(r.objects.size()),m=int(r.people.size());
 // 조사 지점 : data/hotspots.json(그림을 보고 정한 좌표)이 있으면 그 자리, 없으면 고르게
 const hb::Json* marks=nullptr;if(r.spot>=0){auto id=currentBeat()["spots"][r.spot].value("id","");if(hotspotData.contains(id))marks=&hotspotData[id];}
 // 말 걸 사람이 방에 없으면 그 대상은 그냥 조사 지점
 auto standing=[&](const std::string& who){for(int k=0;k<m&&k<16;k++)if(r.people[k]==who)return true;return false;};
 for(int k=0;k<n;k++){if(standing(r.objects[k].who))continue;float u=.14f+.72f*(k+.5f)/std::max(1,n);float v=k%2?.58f:.7f;
  size_t best=0;if(marks)for(auto& [key,uv]:marks->items())if(key.size()>best&&r.objects[k].name.rfind(key,0)==0){best=key.size();u=uv[0].get<float>();v=uv[1].get<float>();} // 가장 긴 이름 (「시체」 ≠ 「시체의 소지품」)
  hotspots.push_back({u,v,false,k,""});}
 for(int k=0;k<m&&k<16;k++){float u=m==1?.5f:.22f+.56f*k/std::max(1,m-1);hotspots.push_back({u,.98f,true,-1,r.people[k]});
  if(k<6){UI::SetTexture(this,exui::ID,"Fig"+std::to_string(k),"Assets/Art/figure/"+r.people[k]+".webp");evis("Fig"+std::to_string(k),true);}}
 if(i<int(world.roomIds.size()))exworld::begin(world,world.roomIds[i],true);else exworld::visible(world,false);
 if(world.active){
  evis("ExBg",false);evis("ArL",false);evis("ArR",false);UI::SetVisible(this,UI_ID,"Background",false);
  evis("ExHint",false);
  for(int k=0;k<6;k++)evis("Fig"+std::to_string(k),false);
  int person=0;
  for(int h=0;h<int(hotspots.size());h++){auto& hot=hotspots[h];
   if(hot.person){exworld::addPerson(world,h,hot.who,person++,int(r.people.size()));continue;}
   bool located=false;exworld::Point p;
   auto& obj=r.objects[hot.object];const hb::Json* raw=nullptr;
   if(r.spot>=0){auto& objects=currentBeat()["spots"][r.spot]["objects"];if(obj.index>=0&&obj.index<int(objects.size()))raw=&objects[obj.index];}
   if(raw&&raw->contains("world_pos")&&(*raw)["world_pos"].is_array()&&(*raw)["world_pos"].size()==3){auto& v=(*raw)["world_pos"];p={v[0].get<float>(),v[2].get<float>(),-v[1].get<float>()};located=true;}
   else if(raw&&raw->contains("target_id")){auto target=raw->value("target_id","");for(auto& node:world.spec()["targets"])if(node.value("id","")==target){p=exworld::point(node["p"]);located=true;break;}for(auto& node:world.spec()["nodes"])if(!located&&node.value("id","")==target){p=exworld::point(node["p"]);located=true;break;}}
   if(!located)p=exworld::locate(world,obj.name,hot.object,int(r.objects.size()),located);
   world.targets.push_back({p,h,-1,false,located,obj.name,""});
  }
  exworld::addDoors(world);exploreReactionPlace(true);UI::SetTexture(this,exui::ID,"Mini",world.spec().value("map",""));exworld::camera(world);
 }
 placeRoom();mode=Mode::Explore;
 // 들어가자마자 나오는 대사(첫 조사 대상 앞) : 한 번만
 if(currentBeat().value("t","")=="investigate"&&r.spot>=0){auto& s=currentBeat()["spots"][r.spot];auto key=s.value("id","")+"#in";
  if(!seen.count(key)&&s.value("intro",0)>0){seen.insert(key);playSegment(r.spot,0,s.value("intro",0));}}
}
void Yumeno::placeRoom(){
 if(world.active){
  exploreReactionPlace(false);
  // Actual world XZ floor plan; same collision geometry and same camera pose as rendering.
  auto& b=world.spec()["bounds"];float bx=b[0].get<float>(),bz=b[1].get<float>(),bw=b[2].get<float>()-bx,bh=b[3].get<float>()-bz;
  int spark=0,dot=0,person=0;
  for(auto& target:world.targets){float x=0,y=0,d=0;bool screen=exworld::project(world,target.p,x,y,d);
   if(target.person){if(person<16)if(auto* a=actor("ExplorePerson"+std::to_string(person)))Components::Set(a,"SpriteRenderer","visible",world.visible);person++;}
   if(!target.person&&spark<10){auto id="Spark"+std::to_string(spark++);bool near=!world.free||std::hypot(target.p.x-world.pose.x,target.p.z-world.pose.z)<=4.8f;bool on=screen&&near&&(!target.located||!exworld::occluded(world,target.p));evis(id,on);if(on)UI::SetPosition(this,exui::ID,id,{x,y});}
   if(dot<9){auto id="MiniDot"+std::to_string(dot++);evis(id,true);UI::SetPosition(this,exui::ID,id,{1086+(target.p.x-bx)/bw*168,506+(target.p.z-bz)/bh*168});
    bool done=false;if(target.hot>=0&&!target.person&&rooms[roomAt].spot>=0){auto& r=rooms[roomAt];done=seen.count(currentBeat()["spots"][r.spot].value("id","")+"#"+std::to_string(r.objects[hotspots[target.hot].object].index));}
    UI::SetColor(this,exui::ID,id,done?Color{.4f,.43f,.46f,1}:target.room>=0?Color{.3f,.9f,1,1}:target.person?Color{1,.6f,.85f,1}:Color{1,.82f,.12f,1});}
  }
  for(;spark<10;spark++)evis("Spark"+std::to_string(spark),false);for(;dot<9;dot++)evis("MiniDot"+std::to_string(dot),false);
  evis("MiniDot9",true);UI::SetPosition(this,exui::ID,"MiniDot9",{1086+(world.pose.x-bx)/bw*168,506+(world.pose.z-bz)/bh*168});UI::SetColor(this,exui::ID,"MiniDot9",Color{1,1,1,1});
  return;
 }
 float ox=-exui::PAN+panX,oy=-90; // 배경 왼쪽 위
 UI::SetPosition(this,exui::ID,"ExBg",{ox,oy});
 int fig=0,dot=0;
 for(auto& h:hotspots){float x=ox+h.u*exui::BG_W,y=oy+h.v*exui::BG_H;
  if(h.person){if(fig<6)UI::SetPosition(this,exui::ID,"Fig"+std::to_string(fig),{x,std::min(y,740.f)});fig++;}
  else if(dot<10){auto id="Spark"+std::to_string(dot);UI::SetPosition(this,exui::ID,id,{x,y});dot++;}}
 // 미니맵 : 조사 대상 점(끝난 것은 회색)
 auto& r=rooms[roomAt];
 for(int k=0;k<10;k++){bool on=k<int(r.objects.size());auto id="MiniDot"+std::to_string(k);evis(id,on);if(!on)continue;
  float a=k*6.2832f/std::max<size_t>(1,r.objects.size());UI::SetPosition(this,exui::ID,id,{1170+44*std::cos(a),590+44*std::sin(a)});
  bool done=currentBeat().value("t","")=="investigate"&&seen.count(currentBeat()["spots"][r.spot].value("id","")+"#"+std::to_string(r.objects[k].index));
  UI::SetColor(this,exui::ID,id,done?Color{.45f,.45f,.5f,1}:Color{1,.82f,.12f,1});}
}
int Yumeno::hotspotAt(float x,float y)const{
 if(world.active){int k=exworld::at(world,x,y);return k>=0?world.targets[k].hot:-1;}
 float ox=-exui::PAN+panX,oy=-90;int best=-1;float bd=1e9f;
 for(int i=0;i<int(hotspots.size());i++){auto& h=hotspots[i];float hx=ox+h.u*exui::BG_W,hy=oy+h.v*exui::BG_H;
  float d=h.person?(std::abs(x-hx)<90&&y>hy-480&&y<hy?std::abs(x-hx):1e9f):std::hypot(x-hx,y-hy);
  if(d<(h.person?90.f:70.f)&&d<bd){bd=d;best=i;}}
 return best;
}
std::string Yumeno::hotspotLabel(int i)const{
 auto& h=hotspots[i];auto& r=rooms[roomAt];
 if(h.person)return nameOf(h.who);
 return r.objects[h.object].name;
}
// 장면 구간 재생 : 끝나면 탐색으로 돌아온다
void Yumeno::playSegment(int spot,int from,int to){
 ctxSpot=spot;event=from;eventEnd=to;showStory();flowPresent();
}
void Yumeno::interact(int i){
 auto h=hotspots[i];auto& r=rooms[roomAt];bool inv=currentBeat().value("t","")=="investigate";
 playerXp(h.person?"TalkCharacter":"CheckObject");
 sfx(h.person?"sfx_talk_in":"sfx_inspect");
 if(inv){
  int obj=h.object;
  if(h.person){auto& s=currentBeat()["spots"][r.spot];for(int k=0;k<int(r.objects.size());k++)if(r.objects[k].who==h.who){obj=k;if(!seen.count(s.value("id","")+"#"+std::to_string(r.objects[k].index)))break;}}
  if(obj<0){sayOnce(h.who,reaction(h.who,"chat"),"C01",After::Explore);return;}
  auto& o=r.objects[obj];segmentKey=currentBeat()["spots"][r.spot].value("id","")+"#"+std::to_string(o.index);
  playSegment(r.spot,o.from,o.to);return;
 }
 // 자유행동 : 확인 → 이벤트
 if(!h.person)return;
 confirmWho=h.who;showConfirm(nameOf(h.who)+josa(nameOf(h.who),"와","과")+" 함께 시간을 보낼까?");
}
void Yumeno::showConfirm(const std::string& q){
 mode=Mode::Confirm;confirmYes=true;sfx("ui_select");
 for(auto id:{"CfShade","CfBox","CfText","CfYesP","CfYes","CfNoP","CfNo"})evis(id,true);etext("CfText",q);
 UI::SetTexture(this,exui::ID,"CfYesP","Assets/Art/ui/map_item_on.svg");UI::SetTexture(this,exui::ID,"CfNoP","Assets/Art/ui/map_item.svg");
}
void Yumeno::confirmPicked(bool yes){
 for(auto id:{"CfShade","CfBox","CfText","CfYesP","CfYes","CfNoP","CfNo"})evis(id,false);
 if(!yes){mode=Mode::Explore;return;}
 int p=poolOf(confirmWho);
 if(p>=0){band("free");ctxPool=p;event=0;eventEnd=-1;showStory();flowPresent();return;}
 addBond(confirmWho,1);coins+=1;giftTarget=confirmWho;sayOnce(confirmWho,reaction(confirmWho,"chat"),"C02",After::Gift);
}
// 수사 : 방의 조사 대상 하나가 끝났다
void Yumeno::segmentDone(){
 if(!segmentKey.empty()){seen.insert(segmentKey);segmentKey.clear();coins+=1;sfx("sfx_coin");}
 ctxSpot=-1;eventEnd=-1;
 bool all=true;for(auto& r:rooms)if(!roomDone(r))all=false;
 if(all){ // V3 : 필요한 조사를 다 하면 수사 종료 방송 → 재판으로
  auto ch=chapter.value("chapter","1");int added=0;
  for(auto& [id,v]:kotodama.items())if(id.size()>2&&id[1]==ch[0]&&cards.insert(id).second)++added;
  band("invend");sfx("sfx_ding");hideExplore();nextBeat();return;
 }
 rooms[roomAt].done=roomDone(rooms[roomAt]);
 enterRoomBack();
}
void Yumeno::enterRoomBack(){ // 대화가 끝난 뒤 같은 방 그대로
 if(world.active){hideFlow();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"Background",false);
  for(auto id:{"AreaBand","AreaIcon","AreaName","Mini","Cross"})evis(id,true);
  evis("ExBg",false);evis("ArL",false);evis("ArR",false);exworld::visible(world,true);exworld::camera(world);placeRoom();mode=Mode::Explore;hud();fvis("FHud",true);return;}
 hideFlow();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);
 for(auto id:{"ExBg","ArL","ArR","AreaBand","AreaIcon","AreaName","Mini","Cross"})evis(id,true);
 for(int k=0;k<int(rooms[roomAt].people.size())&&k<6;k++)evis("Fig"+std::to_string(k),true);
 placeRoom();mode=Mode::Explore;hud();fvis("FHud",true);
}

// 띠 연출 : 자유행동·수사 개시·수사 종료·시체 발견 (1.4초, 입력을 막지 않음)
void Yumeno::band(const std::string& kind){
 UI::SetTexture(this,exui::ID,"Band","Assets/Art/ui/band_"+kind+".svg");evis("Band",true);bandTimer=1.4f;
 if(kind=="body"){evis("Flash",true);flashTimer=.25f;} // 소리(충격 + 시체 발견 징글)는 사망 CG 이벤트에 붙어 있다(tools/sound_design.py)
 else if(kind!="invend")sfx("sfx_band");
}
// 코토다마 획득 : 빛 + 카드 + 「코토다마 ○○를 손에 넣었다」. 클릭할 때까지
void Yumeno::kotodamaGet(const std::string& id){
 for(auto x:{"KShade","KGlow","KFrame","KCard","KBand","KTitle","KMsg"})evis(x,true);
 bool icon=false;for(auto& c:art["kotodama"])if(c.get<std::string>()==id)icon=true;
 evis("KCard",icon);if(icon)UI::SetTexture(this,exui::ID,"KCard","Assets/Art/kotodama/"+id+".webp");
 std::string frame=id[0]=='T'?"frame_testimony":id[0]=='M'||id[0]=='R'?"frame_rule_magic":id[0]=='N'?"frame_memo":"frame_evidence";
 UI::SetTexture(this,exui::ID,"KFrame","Assets/Art/ui/kotodama/"+frame+".webp");
 etext("KTitle","코토다마 「"+kotodamaName(id)+"」");etext("KMsg",josa(kotodamaName(id),"를","을")+" 손에 넣었다!");
 popupFrom=mode;mode=Mode::Popup;kspin=0;sfx("sfx_card");
}
void Yumeno::updateExplore(float delta,bool click){
 if(bandTimer>0&&(bandTimer-=delta)<=0)evis("Band",false);
 if(flashTimer>0&&(flashTimer-=delta)<=0)evis("Flash",false);
 Vec2 m{640,360};Input::GetMousePositionForCanvas({1280,720},m);
 if(mode==Mode::Popup){
  kspin+=delta;UI::SetRotation(this,exui::ID,"KGlow",kspin*20);UI::SetScale(this,exui::ID,"KFrame",{std::min(1.f,kspin*4),std::min(1.f,kspin*4)});
  if(click||enterNow){playerClaim("GetKotodama","legacy-evidence-out:"+std::to_string(chapterAt)+":"+std::to_string(beat)+":"+std::to_string(ctxPool)+":"+std::to_string(ctxSpot)+":"+std::to_string(event));for(auto x:{"KShade","KGlow","KFrame","KCard","KBand","KTitle","KMsg"})evis(x,false);mode=popupFrom;++event;flowPresent();}
  return;
 }
 if(mode==Mode::Map){
  if(pressed("g")&&currentBeat().value("t","")=="freetime"){pullCapsule();renderMap();}
  int old=mapHover;bool moved=m.x!=mapMouseX||m.y!=mapMouseY;mapMouseX=m.x;mapMouseY=m.y;
  int over=mapAt(m.x,m.y);if(moved&&over>=0)mapHover=over;
  if(!rooms.empty()){
   if(pressed("w")||pressed("ArrowUp"))mapHover=(mapHover+int(rooms.size())-1)%int(rooms.size());
   if(pressed("s")||pressed("ArrowDown"))mapHover=(mapHover+1)%int(rooms.size());
  }
  if(old!=mapHover){sfx("ui_select");renderMap();}
  if((click&&over>=0)||enterNow){if(!rooms.empty())enterRoom(click&&over>=0?over:mapHover);return;}
  if((pressed("Backspace")||pressed("Escape")||pressed("mouse1")||pressed("m"))&&mapReturnRoom>=0&&mapReturnRoom<int(rooms.size()))enterRoom(mapReturnRoom);
  return;
 }
 if(mode==Mode::Confirm){
  bool overYes=m.y>exui::CF_Y&&m.y<exui::CF_Y+exui::CF_H&&m.x>exui::CF_YES_X&&m.x<exui::CF_YES_X+exui::CF_W;
  bool overNo=m.y>exui::CF_Y&&m.y<exui::CF_Y+exui::CF_H&&m.x>exui::CF_NO_X&&m.x<exui::CF_NO_X+exui::CF_W;
  if(overYes&&click)confirmYes=true;if(overNo&&click)confirmYes=false;
  if(pressed("a")||pressed("ArrowLeft"))confirmYes=true;if(pressed("d")||pressed("ArrowRight"))confirmYes=false;
  if(pressed("Backspace")||pressed("Escape")||pressed("mouse1")){confirmPicked(false);return;}
  UI::SetTexture(this,exui::ID,"CfYesP",confirmYes?"Assets/Art/ui/map_item_on.svg":"Assets/Art/ui/map_item.svg");UI::SetTexture(this,exui::ID,"CfNoP",confirmYes?"Assets/Art/ui/map_item.svg":"Assets/Art/ui/map_item_on.svg");
  if((click&&(overYes||overNo))||enterNow)confirmPicked(click?overYes:confirmYes);
  return;
 }
 if(world.active){
  exploreConcentration();
  float turn=(Input::IsKeyDown("ArrowRight")?1.f:0.f)-(Input::IsKeyDown("ArrowLeft")?1.f:0.f);
  evis("ExHint",false);
  float pitch=(Input::IsKeyDown("ArrowUp")?1.f:0.f)-(Input::IsKeyDown("ArrowDown")?1.f:0.f);
  float yaw=turn*delta*105,dy=pitch*delta*55;
  if(Input::IsKeyDown("mouse1")&&world.mouseX>=0){yaw+=(m.x-world.mouseX)*.16f;dy-=(m.y-world.mouseY)*.12f;}
  if(optionsV4.values.controls==0)yaw+=((Input::IsKeyDown("d")?1.f:0.f)-(Input::IsKeyDown("a")?1.f:0.f))*delta*105;
  exworld::reticle(world,m,Input::IsKeyDown("mouse1"),optv4::ReticleScale(optionsV4.values));world.mouseX=m.x;world.mouseY=m.y;
  if(yaw||dy)exworld::look(world,yaw*(optionsV4.values.invertX?-1.f:1.f),dy*(optionsV4.values.invertY?-1.f:1.f));float oldX=world.pose.x,oldZ=world.pose.z;
  bool moved=exworld::move(world,delta,(Input::IsKeyDown("w")?1.f:0.f)-(Input::IsKeyDown("s")?1.f:0.f),optionsV4.values.controls==1?(Input::IsKeyDown("d")?1.f:0.f)-(Input::IsKeyDown("a")?1.f:0.f):0,Input::IsKeyDown("Shift"));
  if(moved){world.footTime+=delta;if(world.footTime>(Input::IsKeyDown("Shift")?.26f:.42f)){world.footTime=0;auto cue="v4_footstep_"+world.spec().value("footstep_surface","tile")+"_"+std::to_string((world.footstep++%2)+1);sfx(hasAudio(cue)?cue:"sfx_footstep");}}
  float distance=std::hypot(world.pose.x-oldX,world.pose.z-oldZ);playerWalk(distance);bool bobChanged=exworld::bob(world,distance,optionsV4.values.movementBob);if(moved||yaw||dy||bobChanged){exworld::camera(world);placeRoom();}
  UI::SetPosition(this,exui::ID,"Cross",{world.cursorX,world.cursorY});
  int target=exworld::at(world,world.cursorX,world.cursorY),hot=target>=0?world.targets[target].hot:-1;
  int token=target>=0?target:-1;if(token!=crossOver){crossOver=token;UI::SetTexture(this,exui::ID,"Cross",token>=0?"Assets/Art/ui/ex_cross_on.svg":"Assets/Art/ui/ex_cross.svg");
   evis("LblBand",token>=0);evis("LblText",token>=0);if(token>=0){auto& t=world.targets[target];etext("LblText",t.room>=0?t.label:hotspotLabel(hot));sfx(t.person?"sfx_hover_person":"sfx_hotspot");}}
  if(exploreReactionUpdate(delta,target))return;
  if(pressed("Backspace")){world.remember();mapReturnRoom=roomAt;mapHover=roomAt;showMap();return;}
  if(pressed("m")){world.remember();mapReturnRoom=roomAt;mapHover=roomAt;sfx("ui_page_b");showMap();return;}
  if(pressed("e")||enterNow){target=exworld::at(world,640,360);if(target<0)target=exworld::at(world,world.cursorX,world.cursorY);}
  if((click||pressed("e")||enterNow)&&target>=0){auto selected=world.targets[target];evis("LblBand",false);evis("LblText",false);crossOver=-1;
   if(selected.room>=0){world.remember();enterRoom(selected.room);return;}if(selected.hot>=0){interact(selected.hot);return;}}
  return;
 }
 // 방 : 아직 공간 식별자가 없는 구버전 저장의 이미지 조사 호환 경로
 float dir=(m.x<70||Input::IsKeyDown("a")?1.f:0.f)-(m.x>1210||Input::IsKeyDown("d")?1.f:0.f);
 if(dir!=0){panX=std::clamp(panX+dir*delta*420,-exui::PAN,exui::PAN);placeRoom();}
 UI::SetPosition(this,exui::ID,"Cross",{m.x,m.y});
 int over=hotspotAt(m.x,m.y);
 if(over!=crossOver){crossOver=over;UI::SetTexture(this,exui::ID,"Cross",over>=0?"Assets/Art/ui/ex_cross_on.svg":"Assets/Art/ui/ex_cross.svg");if(over>=0)sfx(hotspots[over].person?"sfx_hover_person":"sfx_hotspot");
  evis("LblBand",over>=0);evis("LblText",over>=0);if(over>=0)etext("LblText",hotspotLabel(over));}
 if(pressed("m")){mapReturnRoom=roomAt;mapHover=roomAt;sfx("ui_page_b");showMap();return;}
 if(click&&over>=0){evis("LblBand",false);evis("LblText",false);crossOver=-1;interact(over);}
}
// 자동 진행 검증 : 지도에서 아직 안 끝난 곳 → 방에서 안 본 대상(또는 이벤트가 남은 인물)
Json Yumeno::autoExplore()const{
 using hb::Json;
 if(mode==Mode::Popup)return Json{{"kind","key"},{"key","Enter"}};
 if(mode==Mode::Confirm)return Json{{"kind","key"},{"key","Enter"}};
 bool inv=currentBeat().value("t","")=="investigate";
 if(mode==Mode::Map){
  int want=0;
  for(int i=0;i<int(rooms.size());i++){if(inv?!rooms[i].done:std::any_of(rooms[i].people.begin(),rooms[i].people.end(),[&](const std::string& s){return poolOf(s)>=0;})){want=i;break;}}
  if(!inv&&coins>=3&&gifts.empty())return Json{{"kind","key"},{"key","g"}};
  if(want/9!=mapHover/9)return Json{{"kind","key"},{"key","s"}};
  return Json{{"kind","click"},{"x",exui::MAP_X+60},{"y",exui::MAP_Y+(want%9)*exui::MAP_STEP+exui::MAP_H/2}};
 }
 if(mode==Mode::Explore){
  if(world.active){
   auto& r=rooms[roomAt];
   for(int k=0;k<int(world.targets.size());k++){auto& target=world.targets[k];if(target.hot<0)continue;auto& h=hotspots[target.hot];bool todo=false;
    if(inv&&r.spot>=0){int obj=h.object;auto sid=currentBeat()["spots"][r.spot].value("id","");if(h.person){obj=-1;for(int n=0;n<int(r.objects.size());n++)if(r.objects[n].who==h.who&&!seen.count(sid+"#"+std::to_string(r.objects[n].index))){obj=n;break;}}todo=obj>=0&&!seen.count(sid+"#"+std::to_string(r.objects[obj].index));}
    else todo=!inv&&h.person&&poolOf(h.who)>=0;
    if(todo)return exworld::autoTarget(world,k);
   }
   // Empty connective spaces are entered through doors, not supplied fake events.
   int destination=-1;for(int n=0;n<int(rooms.size());n++)if(inv?!rooms[n].done:std::any_of(rooms[n].people.begin(),rooms[n].people.end(),[&](const std::string& s){return poolOf(s)>=0;})){destination=n;break;}
   if(destination>=0&&destination<int(world.roomIds.size())){auto path=exworld::route(world,world.id,world.roomIds[destination]);if(path.size()>1)for(int k=0;k<int(world.targets.size());k++){auto& target=world.targets[k];if(target.room>=0&&world.roomIds[target.room]==path[1])return exworld::autoTarget(world,k);}}
   return Json{{"kind","key"},{"key","m"}};
  }
  auto& r=rooms[roomAt];float ox=-exui::PAN+panX,oy=-90;
  for(auto& h:hotspots){
   bool todo;
   if(inv){int obj=h.object;auto sid=currentBeat()["spots"][r.spot].value("id","");
    if(h.person){obj=-1;for(int k=0;k<int(r.objects.size());k++)if(r.objects[k].who==h.who&&!seen.count(sid+"#"+std::to_string(r.objects[k].index)))obj=k;}
    todo=obj>=0&&!seen.count(sid+"#"+std::to_string(r.objects[obj].index));}
   else todo=h.person&&poolOf(h.who)>=0;
   if(todo){float x=ox+h.u*exui::BG_W,y=oy+h.v*exui::BG_H;if(h.person)y=std::min(y,740.f)-200;
    if(x<80)return Json{{"kind","key"},{"key","a"}};if(x>1200)return Json{{"kind","key"},{"key","d"}};
    return Json{{"kind","click"},{"x",x},{"y",y}};}
  }
  if(!inv&&!hotspots.empty()){for(auto& h:hotspots)if(h.person){float x=ox+h.u*exui::BG_W;return Json{{"kind","click"},{"x",std::clamp(x,100.f,1180.f)},{"y",500}};}}
  return Json{{"kind","key"},{"key","m"}};
 }
 return Json{{"kind","key"},{"key","Enter"}};
}
