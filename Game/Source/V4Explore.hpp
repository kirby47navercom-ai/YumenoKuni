// Investigation routes are authored graph calls; geometry comes from the actual space catalog.
bool Yumeno::v4FreeWorld()const{return v4.active&&v4.current().value("type",std::string())=="menu"&&v4.current().value("selectionRole",std::string())=="freetime"&&campaignv4::canSave(v4.graph);}
void Yumeno::v4FreeBegin(){
 exworld::load(world);v4FreeSpots=Json::array();v4FreeRest=-1;v4FreeChoice=-1;v4FreeAccepted=false;v4FreeActor.clear();
 const auto& menu=v4.current();int index=0;
 for(const auto& option:menu["options"]){int choice=index++;if(!storyv4::eligible(v4,option))continue;
  if(option.contains("encounter")){
   const auto& encounter=option.at("encounter");const auto who=encounter.at("actor").get<std::string>();
   const auto space=encounter.at("space").get<std::string>();
   if(!world.data["instances"].contains(space))throw std::runtime_error("Freetime room not bound: "+space);
   v4FreeSpots.push_back({{"id",option.at("id")},{"option",choice},{"space_id",space},{"interviewActors",Json::array({who})},{"neutralLabel",nameOf(who)},{"world_pos",encounter.at("position")}});
   continue;
  }
  const auto& call=storyv4::lookup(v4.graph,option.value("to",std::string()));if(call.value("type",std::string())!="call"){v4FreeRest=choice;continue;}
  std::string who;auto complete=call.value("onReturnSet",Json::object());
  for(const auto& entry:growthV4.contract["entries"])for(const auto& flag:entry["completionFlags"])if(complete.value(flag.get<std::string>(),false))who=entry.value("actor",std::string());
  auto id=call.value("target",std::string());std::set<std::string> visited;std::string space;
  for(int step=0;step<128&&visited.insert(id).second;step++){
   const auto& node=storyv4::lookup(v4.graph,id);auto scene=node.value("scene",Json::object());
   if(node.contains("sceneVariants"))for(const auto& candidate:node["sceneVariants"]){bool match=true;for(const auto& condition:candidate["when"]){auto flag=condition.at("flag").get<std::string>();if(!v4.flags.contains(flag)||v4.flags[flag]!=condition["equals"])match=false;}if(match)scene=candidate;}
   if(!scene.empty()){space=scene.value("space",std::string());break;}
   if(node.value("type",std::string())=="branch"){id=node.value("default",std::string());for(const auto& branch:node["cases"]){auto flag=branch.value("flag",std::string());if(v4.flags.contains(flag)&&v4.flags[flag]==branch["equals"]){id=branch["to"].get<std::string>();break;}}}
   else id=node.value("next",std::string());if(id.empty())break;
  }
  if(who.empty()||space.empty()||!world.data["instances"].contains(space))throw std::runtime_error("Freetime actor/location not bound: "+option.value("id",std::string()));
  v4FreeSpots.push_back({{"id",option.value("id",std::string())},{"option",choice},{"space_id",space},{"interviewActors",Json::array({who})},{"neutralLabel",nameOf(who)}});
 }
 const auto origin=menu.value("explorationStart",std::string());
 if(!origin.empty()&&!v4.restoring&&v4FreeNode!=v4.node){
  exworld::begin(world,origin,false,true);
  world.pose=exworld::entryPose(world.spec());world.remember();
 }else if(!world.active)exworld::begin(world,origin.empty()?"plaza":origin,true,!origin.empty());
 v4FreeNode=v4.node;hideMenu();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);mode=Mode::Explore;music("bgm_freetime");v4WorldPlace();
}
void Yumeno::v4FreePick(int index){
 if(index<0)return;
 if(v4FreeChoice==-2){if(index==0&&v4FreeRest>=0){hideExplore();if(storyv4::choose(v4,v4FreeRest))v4Enter();}else v4FreeBegin();return;}
 if(v4FreeChoice<0||v4FreeChoice>=int(v4FreeSpots.size()))return;
 if(index!=0){v4FreeBegin();return;}
 v4FreeAccepted=true;
 if(v4FreeCanGift&&std::any_of(gifts.begin(),gifts.end(),[](const auto& gift){return gift.second>0;})){v4GiftOpen();return;}
 v4FreeContinue();
}
void Yumeno::v4FreeContinue(){
 if(!v4FreeAccepted||!v4FreeWorld()||v4FreeChoice<0||v4FreeChoice>=int(v4FreeSpots.size()))return;
 v4FreeAccepted=false;
 const int choice=v4FreeSpots[v4FreeChoice].at("option").get<int>();
 hideExplore();
 if(storyv4::choose(v4,choice)){
  if(v4.graph.contains("campaignRevision")){playerXp("TalkCharacter");pv4::Action(presentationV4,"talk_start");}
  v4Enter();
 }else v4FreeBegin();
}
bool Yumeno::v4SpotEligible(const Json& spot)const{return investigationv4::Eligible(spot,v4.flags,cards);}
void Yumeno::v4Investigate(){
 const auto& hub=v4.current();const auto progress=investigationv4::Check(hub,v4.flags,cards);
 if(hub.contains("reminder")){const auto& reminder=hub["reminder"];auto flag=reminder.value("flag",std::string());if(progress.cards+1==progress.totalCards&&!cards.count(reminder.value("missingCard",std::string()))&&!v4.flags.value(flag,false)){if(storyv4::jump(v4,reminder.at("node").get<std::string>()))v4Enter();return;}}
 if(progress.complete&&hub.contains("next")){if(storyv4::jump(v4,hub["next"].get<std::string>()))v4Enter();return;}
 hideMenu();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);exworld::load(world);
 if(v4HubNode!=v4.node){v4HubNode=v4.node;v4HubPage=0;auto id=hub.value("keepCurrentRoom",false)&&world.active?world.id:hub.value("space_id",std::string());if(id.empty()&&hub.contains("spots")&&!hub["spots"].empty())id=hub["spots"][0].value("space_id",std::string());if(!id.empty()&&world.id!=id)exworld::begin(world,id,true);}
 if(!world.active){auto id=hub.value("space_id",std::string());if(id.empty()&&hub.contains("spots")&&!hub["spots"].empty())id=hub["spots"][0].value("space_id",std::string());exworld::begin(world,id,true);}
 if(!world.active){v4.blocked="Investigation has no bound authored space";lastError="V4: "+v4.blocked;return;}
 mode=Mode::Explore;music(hub.value("investigationMusic",std::string(chapterAt>=5?"bgm_investigation_final":"bgm_investigation")));v4WorldPlace();
}
void Yumeno::v4WorldPlace(){
 const bool free=v4FreeWorld();const auto& spots=free?v4FreeSpots:v4.current()["spots"];
 auto chapter=v4.graph.value("chapter",std::string("P"));world.accessChapter=chapter.size()==1&&chapter[0]>='1'&&chapter[0]<='6'?chapter[0]-'0':0;
 if(free)world.free=true;
 world.audioHover=-1;
 world.hoverSoundCooldown=0;
 world.v4StepPhase=world.v4StepSpeed=0;
 world.targets.clear();world.roomIds.clear();std::set<std::string> allowed{world.id};
 for(int i=0;i<16;i++)if(auto* a=actor("ExplorePerson"+std::to_string(i)))Components::Set(a,"SpriteRenderer","visible",false);int person=0;std::set<std::string> placed;
 if(courtFigures.empty())courtFigures=Data::Get("Assets/Data/court.json")["figures"];
 for(auto& spot:spots){if(!v4SpotEligible(spot))continue;auto path=exworld::route(world,world.id,spot.value("space_id",std::string()));if(free&&path.empty())throw std::runtime_error("Freetime room has no walking connection: "+spot.value("space_id",std::string()));for(auto& id:path)allowed.insert(id);}
 if(world.data.contains("parkLevels")){
  if(free)for(const auto& [id,instance]:world.data["instances"].items())if(!instance.value("storyGeometryOnly",false)&&exworld::accessible(world,id))allowed.insert(id);
  for(const auto& [id,district]:world.data["parkLevels"]["districts"].items())if(district["chapter"].get<int>()<=world.accessChapter){auto path=exworld::route(world,world.id,district["hub"].get<std::string>());for(const auto& stop:path)allowed.insert(stop);}
 }
 for(auto& id:allowed)world.roomIds.push_back(id);
 const auto& hub=v4.current();int index=0;
 for(auto& spot:spots){
  auto sid=spot.value("id",std::string());bool eligible=v4SpotEligible(spot);
  if(eligible&&spot.value("space_id","")==world.id){
   bool located=false;exworld::Point p{};auto target=spot.value("target_id",std::string());
   if(!target.empty())for(auto& t:world.spec()["targets"])if(t.value("id","")==target){p=exworld::point(t["p"]);located=true;break;}
   if(spot.contains("world_pos")){auto& q=spot["world_pos"];if(q.is_array()&&q.size()==3){p={q[0].get<float>(),q[1].get<float>(),q[2].get<float>()};located=true;}}
   if(free&&!located){
    auto anchor=exworld::point(world.spec()["spawn"]);const auto& anchors=world.spec()["targets"];
    if(!anchors.empty())anchor=exworld::point(anchors[0]["p"]);
    if(world.id=="souvenir_shop")for(const auto& candidate:anchors)if(candidate.value("id",std::string())=="open_display_recess")anchor=exworld::point(candidate["p"]);
    // Stand beside an existing room activity anchor, outside its central
    // interaction ray. Spawn-forward placement put an NPC on the shop doorway.
    p=exworld::stand(world,{anchor.x+1.0f+(index%3-1)*.8f,0,anchor.z+.8f});located=true;
   }
   // Unlocated source targets stay in the inspection list, never a fabricated world marker.
   if(located){if(!free)world.targets.push_back({p,index,-1,false,true,spot.value("neutralLabel",std::string("조사하기")),""});
    auto people=spot.value("interviewActors",std::vector<std::string>{});int local=0;
    for(const auto& who:people){if(person>=16||!placed.insert(who).second)continue;
     auto foot=exworld::stand(world,{p.x+(local++-(int(people.size())-1)*.5f)*1.0f,0,p.z+.35f});
     auto f=courtFigures.value(who,Json::object());float height=f.value("height",1.1f),width=f.value("width",.9f);exworld::Point center{foot.x,foot.y+height*.5f,foot.z};
     world.targets.push_back({center,index,-1,true,true,nameOf(who),who});
     if(auto* a=actor("ExplorePerson"+std::to_string(person++))){Scene::SetPosition(a,{exworld::ORIGIN+center.x,center.y,center.z});Components::SetString(a,"SpriteRenderer","texture",f.value("texture",std::string("Assets/Art/v4/lappy.webp")));Components::Set(a,"SpriteRenderer","height",height);Components::Set(a,"SpriteRenderer","width",width);Components::Set(a,"SpriteRenderer","visible",true);}
    }
   }
  }
  ++index;
 }
 v4WorldAmbience();pv4::SceneReady(presentationV4,world.id,v4.restoring);
 exworld::addDoors(world);exworld::visible(world,true);exploreReactionPlace(true);exworld::camera(world);
 UI::SetVisible(this,UI_ID,"Background",false);UI::SetVisible(this,UI_ID,"Backdrop",false);
 for(auto id:{"AreaBand","AreaIcon","AreaName"})evis(id,true);
 etext("AreaName",world.data["instances"][world.id].value("label",world.id));
 evis("ExHint",false);
 v4WorldMarkers();
}
void Yumeno::v4WorldMarkers(){
 exworld::refreshViewport();const auto view=exworld::viewport;const float unit=2*.2f*std::tan(court::FIELD_OF_VIEW*exworld::PI/360)/view.height,markerScale=view.fit*unit*1800.f;
 const bool cursorInside=world.cursorX>0&&world.cursorY>0&&world.cursorX<view.width/view.fit&&world.cursorY<view.height/view.fit;
 evis("Cross",cursorInside);
 if(cursorInside)UI::SetPosition(this,exui::ID,"Cross",{world.cursorX,world.cursorY});
 int marker=0;for(const auto& target:world.targets){if(target.person||marker>=10)continue;float x=0,y=0,depth=0;bool on=exworld::project(world,target.p,x,y,depth)&&(!world.free||std::hypot(target.p.x-world.pose.x,target.p.z-world.pose.z)<=(exploreFocusOn?12.f:4.8f))&&(!target.located||!exworld::occluded(world,target.p));auto id="Spark"+std::to_string(marker);auto* gpu=actor("ExploreTarget"+std::to_string(marker++));evis(id,on&&!gpu);if(gpu){Components::Set(gpu,"SpriteRenderer","visible",on);if(on)Scene::SetPosition(gpu,{((x-12)*view.fit-view.width*.5f)*unit,(view.height*.5f-(y-12)*view.fit)*unit,-.2f});Scene::SetScale(gpu,{markerScale,markerScale,markerScale});}else if(on)UI::SetPosition(this,exui::ID,id,{x-12,y-12});}
 for(;marker<10;marker++){evis("Spark"+std::to_string(marker),false);if(auto* gpu=actor("ExploreTarget"+std::to_string(marker)))Components::Set(gpu,"SpriteRenderer","visible",false);}
}
void Yumeno::v4HubMenu(){
 auto& spots=v4.current()["spots"];v4HubChoices.clear();std::vector<std::string> labels;
 int start=v4HubPage*7;
 for(int i=start;i<std::min(start+7,int(spots.size()));i++){
  auto& s=spots[i];auto id=s.value("id",std::string());bool eligible=v4SpotEligible(s);
  if(!eligible)continue;
  v4HubChoices.push_back(i);labels.push_back((v4.flags.value("spot:"+id+":complete",false)?"확인함 · ":"")+s.value("label",id));
 }
 if(start>0){v4HubChoices.push_back(-1);labels.push_back("이전 쪽");}
 if(start+7<int(spots.size())){v4HubChoices.push_back(-2);labels.push_back("다음 쪽");}
 showMenu(v4.current().value("objectiveRole",std::string())=="trial-gather"?"재판 엘리베이터로 이동해 탑승하세요.":"조사 장소",labels,MenuKind::Event);
}
void Yumeno::v4HubPick(int index,int clickedPerson){
 if(index<0||index>=int(v4HubChoices.size()))return;int spotIndex=v4HubChoices[index];
 if(spotIndex<0){v4HubPage+=spotIndex==-1?-1:1;v4HubMenu();return;}
 auto spot=v4.current()["spots"][spotIndex];auto space=spot.value("space_id",std::string());
 if(world.id!=space){exworld::begin(world,space,true);hideMenu();mode=Mode::Explore;v4WorldPlace();pv4::Action(presentationV4,"room_enter");return;}
 auto id=spot.value("id",std::string());auto flagsOnReturn=spot.value("onReturnSet",Json::object());
 // The common completion token is applied only by a successful authored return.
 flagsOnReturn["spot:"+id+":complete"]=true;
 if(spot.contains("completionFlag"))flagsOnReturn[spot["completionFlag"].get<std::string>()]=true;
 v4.stack.push_back({v4.node,flagsOnReturn});
 if(storyv4::jump(v4,spot.value("entry",std::string()))){
  const bool person=clickedPerson>=0?clickedPerson!=0:!spot.value("interviewActors",std::vector<std::string>{}).empty();
  playerXp(person?"TalkCharacter":"CheckObject");hideMenu();hideExplore();pv4::Action(presentationV4,person?"talk_start":"inspect");v4Enter();
 }
}
void Yumeno::v4WorldUpdate(float delta,bool click){
 bool free=v4FreeWorld();
 if(mode==Mode::Menu){
  if(pressed("Backspace")||pressed("mouse1")){if(free){v4FreeActor.clear();v4FreeChoice=-1;}pv4::Action(presentationV4,"ui_cancel");hideMenu();mode=Mode::Explore;return;}
  int pick=-1,old=menuHover;Vec2 m;Input::GetCenteredMousePositionForCanvas({1280,720},m);
  if(menuCount>0){if(pressed("w")||pressed("ArrowUp"))menuHover=(menuHover+menuCount-1)%menuCount;if(pressed("s")||pressed("ArrowDown"))menuHover=(menuHover+1)%menuCount;}
  if(old!=menuHover)pv4::Action(presentationV4,"ui_focus");
  for(int i=0;i<menuCount;i++)if(pressed(std::to_string(i+1)))pick=i;
  if(enterNow)pick=menuHover;if(click)pick=menuAt(m.x,m.y);if(pick>=0)menuAccept(pick,free?4:2);return;
 }
 if(free){v4FreeActor.clear();v4FreeChoice=-1;evis("ExHint",false);}
 if(free&&pressed("Backspace")&&v4FreeRest>=0){v4FreeChoice=-2;showMenu("개인시간을 마칠까요?",{"혼자 쉰다","돌아간다"},MenuKind::Event);return;}
 if(pressed("m")){if(free){padToggle();padPageAt=0;padShowPage();}else v4HubMenu();return;}
 exploreConcentration();
 evis("ExHint",false);
 Vec2 m;exworld::canvasMouse(m);float yaw=((Input::IsKeyDown("ArrowRight")?1.f:0.f)-(Input::IsKeyDown("ArrowLeft")?1.f:0.f))*delta*80;
 float pitch=((Input::IsKeyDown("ArrowUp")?1.f:0.f)-(Input::IsKeyDown("ArrowDown")?1.f:0.f))*delta*55;
 if(Input::IsKeyDown("mouse1")&&world.mouseX>=0){yaw+=(m.x-world.mouseX)*.16f;pitch-=(m.y-world.mouseY)*.12f;}
 if(optionsV4.values.controls==0)yaw+=((Input::IsKeyDown("d")?1.f:0.f)-(Input::IsKeyDown("a")?1.f:0.f))*delta*80;
 exworld::reticle(world,m,Input::IsKeyDown("mouse1"),optv4::ReticleScale(optionsV4.values));world.mouseX=m.x;world.mouseY=m.y;
 if(yaw||pitch)exworld::look(world,yaw*optionsV4.values.cameraSensitivity*(optionsV4.values.invertX?-1.f:1.f),pitch*optionsV4.values.cameraSensitivity*(optionsV4.values.invertY?-1.f:1.f));
 float oldX=world.pose.x,oldZ=world.pose.z;
 float forward=(Input::IsKeyDown("w")?1.f:0.f)-(Input::IsKeyDown("s")?1.f:0.f);
 float sideways=optionsV4.values.controls==1?(Input::IsKeyDown("d")?1.f:0.f)-(Input::IsKeyDown("a")?1.f:0.f):0;
 bool running=Input::IsKeyDown("Shift");
 bool moved=exworld::move(world,delta,forward,sideways,running);
 // The manual V3 route uses its input-driven phase, even against a collider.
 const float ticks=std::clamp(delta,0.f,.1f)*60.f;
 const bool stepping=world.free&&(forward!=0||sideways!=0);
 const float speed=stepping?(running?2.f:1.f):0.f;
 world.v4StepSpeed+=(speed-world.v4StepSpeed)*(1.f-std::pow(.5f,ticks));
 bool stepContact=false;
 if(stepping){
  world.v4StepPhase+=6.f*world.v4StepSpeed*ticks;
  if(world.v4StepPhase>180.f){world.v4StepPhase-=180.f;stepContact=true;}
 }else if(world.v4StepPhase>0.f){
  const float boundary=world.v4StepPhase<90.f?0.f:180.f;
  const float remaining=boundary-world.v4StepPhase;
  const float advance=std::max(6.f*world.v4StepSpeed,8.f)*ticks;
  if(std::abs(remaining)<=advance){world.v4StepPhase=world.v4StepSpeed=0.f;stepContact=true;}
  else world.v4StepPhase+=std::copysign(advance,remaining);
 }
 if(stepContact){
  const float variation=float((static_cast<unsigned>(world.footstep++)*37u)%101u)/500.f;
  pv4::Sound(presentationV4,"v3se_064",(running?.7f:.5f)+variation);
 }
 float distance=std::hypot(world.pose.x-oldX,world.pose.z-oldZ);playerWalk(distance);float previousBob=world.bobOffset;exworld::bob(world,distance,optionsV4.values.movementBob);if(moved||yaw||pitch||previousBob!=world.bobOffset)exworld::camera(world);v4WorldMarkers();
 exworld::updateParkCctv(world,delta);
 int over=exworld::at(world,world.cursorX,world.cursorY);UI::SetTexture(this,exui::ID,"Cross",over>=0?"Assets/Art/ui/ex_cross_on.svg":"Assets/Art/ui/ex_cross.svg");evis("LblBand",over>=0);evis("LblText",over>=0);
 world.hoverSoundCooldown=std::max(0.f,world.hoverSoundCooldown-delta);
 if(over<0)world.audioHover=-1;
 else if(over!=world.audioHover&&world.hoverSoundCooldown==0){
  world.audioHover=over;
  world.hoverSoundCooldown=8.f/60.f;
  sfx("v3se_050");
 }
 if(over>=0)etext("LblText",world.targets[over].label);
 if(exploreReactionUpdate(delta,over))return;
 if(!(click||pressed("e"))||over<0)return;
 auto target=world.targets[over];
 if(target.room==-2){pv4::Action(presentationV4,"door_locked");message("이 구역은 아직 개방되지 않았어요.",1.5f);return;}
 if(target.room>=0){auto dest=world.roomIds[target.room];exworld::begin(world,dest,true,free&&v4.graph.contains("campaignRevision"));v4WorldPlace();pv4::Action(presentationV4,"room_enter");return;}
 if(free&&target.person&&target.hot>=0){
  sfx("v3se_034");
  v4FreeChoice=target.hot;v4FreeActor=target.slug;v4FreeCanGift=growthv4::GiftEligible(growthV4,"gift:"+target.slug,v4.flags,v4GiftContext(target.slug));
  for(auto id:{"LblBand","LblText","Cross","ExHint"})evis(id,false);
  std::vector<std::string> choices{"함께 보낸다","그만둔다"};showMenu(nameOf(target.slug)+"와 시간을 보낼까요?",choices,MenuKind::Event);return;
 }
 if(target.hot>=0){v4HubChoices={target.hot};v4HubPick(0,target.person?1:0);}
}
