void Yumeno::exploreReactionPlace(bool targets){
 if(reactionWorld!=world.id){reactionWorld=world.id;reactionAt=-1;reactionTime=0;}
 const auto props=world.spec().value("reactions",Json::array());
 for(int i=0;i<2;i++)if(auto* a=actor("ExploreReaction"+std::to_string(i))){bool on=world.visible&&i<int(props.size());Components::Set(a,"MeshRenderer","visible",on);if(!on)continue;
  const auto& p=props[i];auto at=exworld::point(p["p"]);Components::SetString(a,"MeshRenderer","mesh",p.at("runtime").get<std::string>());Scene::SetPosition(a,{exworld::ORIGIN+at.x,at.y,at.z});Scene::SetRotation(a,{0,0,0});
  if(targets){auto key=world.id+":"+p.at("id").get<std::string>();auto it=exploreReactions.find(key);if(it!=exploreReactions.end()&&it->second.remaining<=0)continue;world.targets.push_back({{at.x,at.y+.65f,at.z},-1,-1,false,true,p.value("label",std::string()),"",i});}
 }
}
bool Yumeno::exploreReactionUpdate(float delta,int over){
 const auto props=world.spec().value("reactions",Json::array());
 if(reactionWorld!=world.id){reactionAt=-1;reactionTime=0;reactionWorld=world.id;}
 if(reactionAt>=0){
  if(reactionAt>=int(props.size())){reactionAt=-1;return false;}const auto& p=props[reactionAt];reactionTime+=delta;auto pos=exworld::point(p["p"]);
  if(!reactionCommitted&&reactionTime>=.18f){
   // Readiness and distance are checked again at impact, before stock/durability.
   bool eligible=!world.free||std::hypot(pos.x-world.pose.x,pos.z-world.pose.z)<=4.8f;
   auto target=pos;target.y+=.65f;eligible=eligible&&!exworld::occluded(world,target);
   if(!eligible){reactionAt=-1;return true;}auto key=world.id+":"+p.at("id").get<std::string>();auto hit=reactionv4::hit(exploreReactions[key]);reactionCommitted=true;
   if(hit.accepted){int before=coins;coins=std::min(999,coins+hit.medals);sfx("v3se_076");if(coins>before){pv4::Action(presentationV4,"coin_award");toast("메달 +"+std::to_string(coins-before));}if(hit.completed)playerClaim("ObjectReaction","object-reaction:"+key);}
  }
  float phase=std::clamp((reactionTime-.18f)/.42f,0.f,1.f),height=std::sin(phase*court::PI)*.16f;
  if(auto* a=actor("ExploreReaction"+std::to_string(reactionAt))){Scene::SetPosition(a,{exworld::ORIGIN+pos.x,pos.y+height,pos.z});Scene::SetRotation(a,{0,0,std::sin(phase*court::PI*2)*4});}
  if(reactionTime>=.6f){reactionAt=-1;reactionTime=0;exploreReactionPlace(false);for(auto it=world.targets.begin();it!=world.targets.end();){if(it->reaction>=0){auto key=world.id+":"+props[it->reaction].at("id").get<std::string>();auto r=exploreReactions.find(key);if(r!=exploreReactions.end()&&r->second.remaining<=0){it=world.targets.erase(it);continue;}}++it;}}
  return true;
 }
 if(over<0||over>=int(world.targets.size())||world.targets[over].reaction<0)return false;
 const auto& t=world.targets[over];etext("LblText",t.label+" · Space 치기");
 if(pressed("Space")){reactionAt=t.reaction;reactionTime=0;reactionCommitted=false;sfx("v3se_075");return true;}return false;
}
