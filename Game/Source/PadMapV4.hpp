// Source six-place/4x4 character-find layout. Own atlas uses actual authored
// room polygons; travel follows the active hub, never map browsing or spoilers.
namespace padmap {
inline const hb::Json& space(const exworld::State& world,const std::string& instance){
 const auto& entry=world.data["spaces"][world.data["instances"][instance]["space"].get<std::string>()];
 if(!entry.contains("bucket"))return entry;
 static std::map<std::string,hb::Json> pages;auto file=entry["bucket"].get<std::string>();
 if(!pages.count(file))pages[file]=hb::Data::Get(file);
 return pages[file]["spaces"][world.data["instances"][instance]["space"].get<std::string>()];
}
inline float angle(const hb::Json& layout,const exworld::State& world,bool rotate,int group){
 if(!rotate||!layout["instances"].contains(world.id)||layout["instances"][world.id]["group"]!=group)return 0;
 return world.pose.yaw-layout["instances"][world.id].value("rotation",0.f);
}
inline std::array<float,2> project(const hb::Json& layout,const std::string& id,float x,float z){
 const auto& i=layout["instances"][id];const auto& group=layout["regions"][i["group"].get<int>()];float a=i.value("rotation",0.f)*exworld::PI/180,scale=group["scale"].get<float>();
 return {(i["origin"][0].get<float>()+x*std::cos(a)-z*std::sin(a)-group["worldCenter"][0].get<float>())*scale,(i["origin"][2].get<float>()+x*std::sin(a)+z*std::cos(a)-group["worldCenter"][1].get<float>())*scale};
}
}
void Yumeno::padMapClear(){
 if(padMapVisible){UI::Remove(this,"padmap");UI::Remove(this,"padmapatlas");}
 padMapVisible=false;padMapDragging=false;
}
bool Yumeno::padMapCanTravel(const std::string& id)const{
 if(machineActive&&machineFromGallery)return false;
 if(!world.loaded||!world.data["instances"].contains(id)||!world.active||!exworld::accessible(world,id))return false;
 if(v4.active){if(v4Court||(!v4FreeWorld()&&v4.current().value("type",std::string())!="investigate")||(beforePad!=Mode::Explore&&beforePad!=Mode::Menu))return false;}
 else if(beforePad!=Mode::Explore&&beforePad!=Mode::Map)return false;
 std::set<std::string> allowed(world.roomIds.begin(),world.roomIds.end());allowed.insert(world.id);
 if(!allowed.count(id))return false;
 // Restrict every intermediate room, not only the destination of a global BFS.
 std::set<std::string> reached{world.id};std::queue<std::string> q;q.push(world.id);
 while(!q.empty()){auto at=q.front();q.pop();if(at==id)return true;for(const auto& edge:world.data["connections"]){if(edge.value("minimumChapter",0)>world.accessChapter)continue;std::string next;if(edge["a"]==at)next=edge["b"].get<std::string>();else if(edge["b"]==at)next=edge["a"].get<std::string>();if(allowed.count(next)&&exworld::accessible(world,next)&&reached.insert(next).second)q.push(next);}}
 return false;
}
std::vector<std::string> Yumeno::padMapCandidates()const{
 static const auto layout=Data::Get("Assets/Data/v4_story/map_layout.json");std::set<std::string> known;
 if(layout["instances"].contains(world.id))known.insert(world.id);
 for(const auto& [id,pose]:world.history)if(layout["instances"].contains(id)&&exworld::accessible(world,id))known.insert(id);
 for(const auto& id:world.roomIds)if(layout["instances"].contains(id)&&padMapCanTravel(id))known.insert(id);
 std::map<int,std::string> aliases;
 auto priority=[&](const std::string& id){return id==world.id?3:padMapCanTravel(id)?2:1;};
 for(const auto& id:known){int geometry=layout["instances"][id]["geometry"].get<int>();if(!aliases.count(geometry)||priority(id)>priority(aliases[geometry]))aliases[geometry]=id;}
 std::vector<std::string> out;for(const auto& [geometry,id]:aliases)out.push_back(id);return out;
}
hb::Json Yumeno::padMapPeople()const{
 Json people=Json::object();if(!world.active)return people;
 people["mio"]={{"instance",world.id},{"x",world.pose.x},{"z",world.pose.z}};
 if(v4.active&&(v4FreeWorld()||v4.current().value("type",std::string())=="investigate")&&!v4Court){
  const auto& spots=v4FreeWorld()?v4FreeSpots:v4.current().at("spots");
  for(const auto& spot:spots){if(!v4SpotEligible(spot))continue;auto id=spot.value("space_id",std::string());if(!world.data["instances"].contains(id))continue;bool located=false;float x=0,z=0;
   auto target=spot.value("target_id",std::string());if(!target.empty())for(const auto& item:padmap::space(world,id)["targets"])if(item.value("id",std::string())==target){x=item["p"][0].get<float>();z=item["p"][2].get<float>();located=true;break;}
   if(spot.contains("world_pos")&&spot["world_pos"].is_array()&&spot["world_pos"].size()==3){x=spot["world_pos"][0].get<float>();z=spot["world_pos"][2].get<float>();located=true;}
   if(located)for(const auto& who:spot.value("interviewActors",std::vector<std::string>{}))if(who!="mio"&&!people.contains(who))people[who]={{"instance",id},{"x",x},{"z",z}};
  }
 }else if(!v4.active){
  for(int i=0;i<int(rooms.size())&&i<int(world.roomIds.size());i++){auto id=world.roomIds[i];if(!world.data["instances"].contains(id))continue;const auto& spawn=padmap::space(world,id)["spawn"];for(const auto& who:rooms[i].people)if(who!="mio"&&!people.contains(who))people[who]={{"instance",id},{"x",spawn[0]},{"z",spawn[2]}};}
 }
 return people;
}
void Yumeno::padMapFocus(const std::string& id){
 static const auto layout=Data::Get("Assets/Data/v4_story/map_layout.json");padMapSelected=id;padMapFirst=0;
 if(layout["instances"].contains(id)){const auto& i=layout["instances"][id];padMapGroup=i["group"].get<int>();padMapPanX=i["anchor"][0].get<float>();padMapPanY=i["anchor"][1].get<float>();}
}
void Yumeno::padMapPaintAtlas(){
 static const auto layout=Data::Get("Assets/Data/v4_story/map_layout.json");auto known=padMapCandidates();std::set<int> geometry;
 for(const auto& id:known)if(layout["instances"][id]["group"]==padMapGroup)geometry.insert(layout["instances"][id]["geometry"].get<int>());
 float angle=padmap::angle(layout,world,optionsV4.values.mapRotate,padMapGroup),radians=angle*exworld::PI/180;
 auto point=[&](float x,float y){x-=padMapPanX;y-=padMapPanY;return Vec2{layout["center"][0].get<float>()+x*std::cos(radians)-y*std::sin(radians),layout["center"][1].get<float>()+x*std::sin(radians)+y*std::cos(radians)};};
 auto rect=[&](const std::string& id,const Json& r){float w=r[2].get<float>(),h=r[3].get<float>();auto p=point(r[0].get<float>()+w/2,r[1].get<float>()+h/2);UI::SetPosition(this,"padmapatlas",id,{p.x-w/2,p.y-h/2});UI::SetSize(this,"padmapatlas",id,{w,h});UI::SetRotation(this,"padmapatlas",id,angle);};
 for(int i=0;i<int(layout["geometry"].size());i++){auto n="MaRoom"+std::to_string(i);bool on=geometry.count(i);UI::SetVisible(this,"padmapatlas",n,on);if(on)rect(n,layout["geometry"][i]["rect"]);}
 for(int i=0;i<int(layout["edges"].size());i++){const auto& edge=layout["edges"][i];bool on=edge["group"]==padMapGroup&&geometry.count(layout["instances"][edge["a"].get<std::string>()]["geometry"].get<int>())&&geometry.count(layout["instances"][edge["b"].get<std::string>()]["geometry"].get<int>());auto n="MaLink"+std::to_string(i);UI::SetVisible(this,"padmapatlas",n,on);if(on)rect(n,edge["rect"]);}
 bool current=layout["instances"].contains(world.id)&&layout["instances"][world.id]["group"]==padMapGroup;
 UI::SetVisible(this,"padmapatlas","MaPlayer",current);if(current){auto p=padmap::project(layout,world.id,world.pose.x,world.pose.z);auto screen=point(p[0],p[1]);UI::SetPosition(this,"padmapatlas","MaPlayer",{screen.x-11,screen.y-11});UI::SetRotation(this,"padmapatlas","MaPlayer",-world.pose.yaw+layout["instances"][world.id].value("rotation",0.f)+angle);}
 auto people=padMapPeople();bool selected=layout["instances"].contains(padMapSelected)&&layout["instances"][padMapSelected]["group"]==padMapGroup;
 UI::SetVisible(this,"padmapatlas","MaSelected",selected);UI::SetVisible(this,"padmapatlas","MaName",selected);UI::SetVisible(this,"padmapatlas","MaNameShadow",selected);
 if(selected){const auto& i=layout["instances"][padMapSelected];float x=i["anchor"][0].get<float>(),y=i["anchor"][1].get<float>();std::string label=i.value("label",padMapSelected);
  auto who=std::string(padui::REPORTERS[padMapCharacter]);if(padMapMode==1&&people.contains(who)&&people[who]["instance"]==padMapSelected){auto p=padmap::project(layout,padMapSelected,people[who]["x"].get<float>(),people[who]["z"].get<float>());x=p[0];y=p[1];label=nameOf(who)+" · "+label;}
  auto screen=point(x,y);UI::SetPosition(this,"padmapatlas","MaSelected",{screen.x-18,screen.y-18});for(const auto& id:std::vector<std::string>{"MaNameShadow","MaName"}){float shadow=id=="MaNameShadow"?1.5f:0;UI::SetPosition(this,"padmapatlas",id,{screen.x-175+shadow,screen.y+22+shadow});UI::SetText(this,"padmapatlas",id,label);}
 }
 for(int i=0;i<16;i++){auto who=std::string(padui::REPORTERS[i]),n="MaPerson"+std::to_string(i);bool on=i>0&&padReportAllowed(i)&&people.contains(who)&&layout["instances"].contains(people[who]["instance"].get<std::string>())&&layout["instances"][people[who]["instance"].get<std::string>()]["group"]==padMapGroup;
  UI::SetVisible(this,"padmapatlas",n,on);if(on){auto p=padmap::project(layout,people[who]["instance"].get<std::string>(),people[who]["x"].get<float>(),people[who]["z"].get<float>());auto screen=point(p[0],p[1]);UI::SetPosition(this,"padmapatlas",n,{screen.x-14,screen.y-14});UI::SetTexture(this,"padmapatlas",n,"Assets/Art/student_ids/thumb/"+who+".webp");}
 }
}
void Yumeno::padMapDraw(){
 if(!padMapVisible){padMapMode=0;padMapCharacter=0;padMapFocus(world.id);UI::Show(this,"Assets/UI/PadMapAtlasV4.hbwidget.json","padmapatlas");UI::Show(this,"Assets/UI/PadMapV4.hbwidget.json","padmap");padMapVisible=true;}
 for(auto id:{"PdTitle","PdTint","PdSide","PdCoins","PdName","PdSchool","PdHint"})pvis(id,false);
 static const auto layout=Data::Get("Assets/Data/v4_story/map_layout.json"),pages=Data::Get("Assets/Data/v4_story/system_pages_layout.json");
 for(const auto& theme:pages["theme"]["entries"])if(theme.value("saveNo",-1)==padThemeSaveNo){auto image=theme.value("image",std::string());auto at=image.rfind("type_");if(at!=std::string::npos)UI::SetTexture(this,"padmap","MpOutsideMask","Assets/Art/ui/v3/map_mask/"+image.substr(at,8)+".svg");break;}
 auto rows=padRows();int index=0;for(int i=0;i<int(rows.size());i++)if(rows[i].first==padMapSelected)index=i;padRow=index;
 if(index<padMapFirst)padMapFirst=index;if(index>=padMapFirst+6)padMapFirst=index-5;padMapFirst=std::clamp(padMapFirst,0,std::max(0,int(rows.size())-6));
 bool list=padMapMode==0;UI::SetVisible(this,"padmap","MpListActive",list&&!rows.empty());UI::SetVisible(this,"padmap","MpListShade",list);
 for(int i=0;i<6;i++){auto n="MpPlace"+std::to_string(i);bool on=list&&padMapFirst+i<int(rows.size());UI::SetVisible(this,"padmap",n,on);if(on){auto id=rows[padMapFirst+i].first;UI::SetText(this,"padmap",n,rows[padMapFirst+i].second);UI::SetColor(this,"padmap",n,id==padMapSelected?Color{0,0,0,1}:Color{1,1,1,1});UI::SetOpacity(this,"padmap",n,id==padMapSelected?1.f:padMapCanTravel(id)?.8f:.5f);}}
 if(list&&!rows.empty())padsystem::rect(this,"padmap","MpListActive",layout["selected"][index-padMapFirst]);
 for(auto id:{"MpScrollBase","MpScrollTrack","MpScroll"})UI::SetVisible(this,"padmap",id,list&&rows.size()>6);
 if(list&&rows.size()>6){const auto& r=layout["scroll"];float height=r[3].get<float>()*6/rows.size(),dy=(r[3].get<float>()-height)*padMapFirst/std::max(1,int(rows.size())-6);UI::SetPosition(this,"padmap","MpScroll",{r[0].get<float>(),r[1].get<float>()+dy});UI::SetSize(this,"padmap","MpScroll",{r[2].get<float>(),height});}
 auto people=padMapPeople();for(int i=0;i<16;i++){auto n=std::to_string(i),who=std::string(padui::REPORTERS[i]);bool known=padReportAllowed(i),located=known&&people.contains(who),dead=v4Court&&std::find(trialDead.begin(),trialDead.end(),who)!=trialDead.end();
  UI::SetVisible(this,"padmap","MpCharBase"+n,!list);UI::SetVisible(this,"padmap","MpChar"+n,!list&&known);UI::SetVisible(this,"padmap","MpCharDim"+n,!list&&!located);UI::SetVisible(this,"padmap","MpCharUnavailable"+n,!list&&known&&dead);UI::SetVisible(this,"padmap","MpCharSelected"+n,!list&&padMapCharacter==i);if(!list&&known)UI::SetTexture(this,"padmap","MpChar"+n,"Assets/Art/student_ids/thumb/"+who+".webp");}
 UI::SetOpacity(this,"padmap","MpPlaceTab",list?1.f:.5f);UI::SetOpacity(this,"padmap","MpStudentTab",list?.5f:1.f);
 UI::SetText(this,"padmap","MpArea",layout["regions"][padMapGroup].value("name",std::string()));UI::SetText(this,"padmap","MpFloor",layout["regions"][padMapGroup].value("floor",std::string()));
 std::string hint=list?"W/S 장소":"W/S/A/D 학생";hint+=" · Q/E 지역 · Space 장소/학생 · 드래그 지도 · ";hint+=padMapCanTravel(padMapSelected)?"Enter 이동 · ":"";hint+="Esc 돌아가기";for(auto id:{"MpHintShadow","MpHint"})UI::SetText(this,"padmap",id,hint);
 padMapPaintAtlas();
}
void Yumeno::padMapTravel(){
 if(padMapSelected.empty()||!padMapCanTravel(padMapSelected)){sfx("ui_cancel");return;}
 auto dest=padMapSelected;int room=-1;if(!v4.active){auto it=std::find(world.roomIds.begin(),world.roomIds.end(),dest);if(it==world.roomIds.end()||int(it-world.roomIds.begin())>=int(rooms.size())){sfx("ui_cancel");return;}room=int(it-world.roomIds.begin());}
 sfx("ui_confirm");
 padToggle(false);hideMenu();world.mouseX=world.mouseY=-1;
 if(v4.active){mode=Mode::Explore;if(world.id!=dest)exworld::begin(world,dest,true,v4FreeWorld()&&v4.graph.contains("campaignRevision"));v4WorldPlace();pv4::Action(presentationV4,"room_enter");}
 else if(room>=0){mode=Mode::Explore;enterRoom(room);}
}
void Yumeno::padMapUpdate(float delta,bool click){
 (void)delta;Vec2 m;Input::GetCenteredMousePositionForCanvas({1280,720},m);static const auto layout=Data::Get("Assets/Data/v4_story/map_layout.json");
 if(pressed("Backspace")||pressed("mouse1")||pressed("Escape")||pressed("x")||pressed("r")){padPageAt=-1;padHidePage();padMenu();sfx("ui_cancel");return;}
 bool redraw=false;
 int nextMode=padMapMode;if(pressed("Space"))nextMode=1-padMapMode;
 // Source tab text carriers overlap. These own PC hit areas divide their
 // visible captions at the midpoint; they do not claim recovered hit testing.
 if(click&&m.x>=68&&m.x<324&&m.y>=135&&m.y<175)nextMode=m.x<195.5f?0:1;
 if(nextMode!=padMapMode){padMapMode=nextMode;padMapSelected.clear();if(padMapMode==0)padMapFocus(world.id);redraw=true;}
 if(pressed("q")||pressed("e")||(click&&(padsystem::hit(m,layout["MpPrev"])||padsystem::hit(m,layout["MpNext"])) )){
  std::set<int> groups;for(const auto& id:padMapCandidates())groups.insert(layout["instances"][id]["group"].get<int>());std::vector<int> order(groups.begin(),groups.end());if(!order.empty()){auto it=std::find(order.begin(),order.end(),padMapGroup);int index=it==order.end()?0:int(it-order.begin());int step=pressed("q")||(click&&padsystem::hit(m,layout["MpPrev"]))?-1:1;padMapGroup=order[(index+int(order.size())+step)%order.size()];padMapFirst=0;padMapPanX=padMapPanY=0;padMapSelected.clear();auto rows=padRows();if(!rows.empty())padMapFocus(rows[0].first);redraw=true;}
 }
 if(padMapMode==0){auto rows=padRows();if(!rows.empty()){int index=0;for(int i=0;i<int(rows.size());i++)if(rows[i].first==padMapSelected)index=i;int next=index;
   if(pressed("w"))next=(index+int(rows.size())-1)%rows.size();if(pressed("s"))next=(index+1)%rows.size();if(click)for(int i=0;i<6;i++)if(padMapFirst+i<int(rows.size())&&padsystem::hit(m,layout["place"][i]))next=padMapFirst+i;
   if(next!=index||padMapSelected.empty()){int first=padMapFirst;padMapFocus(rows[next].first);padMapFirst=first;redraw=true;}
  }
 }else{int before=padMapCharacter,row=before/4,column=before%4;if(pressed("w"))row=(row+3)%4;if(pressed("s"))row=(row+1)%4;if(pressed("a"))column=(column+3)%4;if(pressed("d"))column=(column+1)%4;padMapCharacter=row*4+column;
  if(click)for(int i=0;i<16;i++)if(padsystem::hit(m,layout["cells"][i]["base"]))padMapCharacter=i;
  if(before!=padMapCharacter||redraw){auto people=padMapPeople();auto who=std::string(padui::REPORTERS[padMapCharacter]);padMapSelected.clear();if(padReportAllowed(padMapCharacter)&&people.contains(who))padMapFocus(people[who]["instance"].get<std::string>());redraw=true;}
 }
 bool held=Input::IsKeyDown("mouse0");if(click&&padsystem::hit(m,layout["viewport"])){padMapDragging=true;padMapDragX=m.x;padMapDragY=m.y;}
 if(!held)padMapDragging=false;
 if(padMapDragging&&(m.x!=padMapDragX||m.y!=padMapDragY)){float angle=-padmap::angle(layout,world,optionsV4.values.mapRotate,padMapGroup)*exworld::PI/180,x=padMapDragX-m.x,y=padMapDragY-m.y;padMapPanX=std::clamp(padMapPanX+x*std::cos(angle)-y*std::sin(angle),-560.f,560.f);padMapPanY=std::clamp(padMapPanY+x*std::sin(angle)+y*std::cos(angle),-360.f,360.f);padMapDragX=m.x;padMapDragY=m.y;padMapPaintAtlas();}
 if(redraw){padMapDraw();sfx("ui_select");}if(enterNow)padMapTravel();
}
std::string Yumeno::MapStats()const{
 auto candidates=padMapCandidates();Json allowed=Json::array();for(const auto& id:candidates)if(padMapCanTravel(id))allowed.push_back(id);
 return Json{{"visible",padMapVisible},{"mode",padMapMode},{"group",padMapGroup},{"first",padMapFirst},{"character",padMapCharacter},{"selected",padMapSelected},{"canTravel",padMapCanTravel(padMapSelected)},{"pan",{padMapPanX,padMapPanY}},{"dragging",padMapDragging},{"known",candidates},{"allowed",allowed},{"people",padMapPeople()},{"flags",v4.flags.size()},{"visited",world.history.size()}}.dump();
}
void Yumeno::DebugV4MapFixture(){
 // Explicit UI fixture: real authored investigation/interview, plus seeded
 // discovered poses to exercise all five own map groups. No played-path claim.
 v4Start("1");if(!storyv4::jump(v4,"v4:1:investigate:I-12d")){lastError="Missing authored map QA hub";return;}v4Enter();
 for(const auto& [id,entry]:world.data["instances"].items()){const auto& p=padmap::space(world,id)["spawn"];world.history[id]={p[0].get<float>(),p[1].get<float>(),p[2].get<float>(),0,0};}
 exworld::begin(world,"plaza",true);mode=Mode::Explore;v4WorldPlace();
}
void Yumeno::DebugV4OutdoorFixture(int index,int phase){
 // Focused environment fixture; this does not unlock a normal-route destination.
 DebugV4MapFixture();static const char* ids[]{"plaza","park_garden","park_main_gate","ticket_booth","pool_edge","ferris_platform","ferris_cabin","coaster_platform","loading_gate","outside_threshold","hotel_corridor"};
 playerProgress.skyPhase=std::clamp(phase,0,2);playerProgress.phase=phase==1?1:0;exworld::begin(world,ids[std::clamp(index,0,10)]);exworld::environment(world,playerProgress.skyPhase);exworld::camera(world);mode=Mode::Explore;v4WorldPlace();hud();
}
std::string Yumeno::EnvironmentStats()const{
 Json enabled=Json::array();for(int p=0;p<3;p++){auto* sky=scenesv4::find("Outdoor"+std::to_string(p)+"_sky");auto* cloud=scenesv4::find("Outdoor"+std::to_string(p)+"_clouds");auto* sun=scenesv4::find("Outdoor"+std::to_string(p)+"_sun");enabled.push_back({{"sky",sky&&Components::GetBool(sky,"SkyAtmosphere","enabled")},{"cloud",cloud&&Components::GetBool(cloud,"VolumetricCloud","enabled")},{"sun",sun&&Components::GetBool(sun,"DirectionalLight","enabled")}});}
 auto* dome=scenesv4::find("OutdoorSkyDome");return Json{{"space",world.space},{"visible",world.visible},{"outdoor",world.active&&world.spec().value("outdoor",false)},{"phase",world.environmentPhase},{"profiles",enabled},{"dome",dome&&Components::GetBool(dome,"MeshRenderer","visible")},{"mesh",dome?Components::GetString(dome,"MeshRenderer","mesh"):std::string()}}.dump();
}
