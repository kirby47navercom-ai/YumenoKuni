// Optional inventory gifts use their own authored dialogue and never complete an FTE.
std::vector<std::string> Yumeno::v4FreeActors()const{
 std::vector<std::string> actors;if(!v4.active||v4Court||v4TaskActive)return actors;
 const auto& n=v4.current();if(n.value("type",std::string())!="menu"||n.value("selectionRole",std::string())!="freetime")return actors;
 if(v4FreeWorld()){if(!v4FreeActor.empty()&&v4FreeChoice>=0)actors.push_back(v4FreeActor);return actors;}
 for(const auto& option:n["options"]){if(!storyv4::eligible(v4,option))continue;
  const auto& call=storyv4::lookup(v4.graph,option.value("to",std::string()));if(call.value("type",std::string())!="call")continue;
  auto completion=call.value("onReturnSet",Json::object());
  for(auto& [id,entry]:growthV4.contract["entries"].items())for(auto& flag:entry["completionFlags"]){auto key=flag.get<std::string>();if(completion.value(key,false)){auto who=entry.value("actor",std::string());if(std::find(actors.begin(),actors.end(),who)==actors.end())actors.push_back(who);}}
 }
 return actors;
}
growthv4::GiftContext Yumeno::v4GiftContext(const std::string& who)const{
 auto present=v4FreeActors();bool here=std::find(present.begin(),present.end(),who)!=present.end();
 return {who,v4.node,v4.current().value("selectionRole",std::string())=="freetime",v4Court||v4TaskActive,here,here};
}
void Yumeno::v4GiftOpen(bool capsule){
 if(capsule){machineOpen(false);return;}
 if(v4FreeActors().empty())return;if(v4GiftCatalog.empty())v4GiftCatalog=Data::Get("Assets/Data/v4_story/gifts.json");
 if(v4FreeWorld()&&!v4FreeActor.empty()){v4GiftPage=0;v4GiftActor=v4FreeActor;v4GiftItem.clear();v4GiftSay(v4GiftCatalog["scenes"]["gift:"+v4GiftActor]["intro"],"items");return;}
 v4GiftPage=0;v4GiftActor.clear();v4GiftItem.clear();v4GiftMenu(capsule?4:1);
}
void Yumeno::v4GiftMenu(int kind){
 v4GiftMode=kind;v4GiftChoices.clear();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);
 std::vector<std::pair<std::string,std::string>> rows;std::string question;
 if(kind==1){question="선물을 건넬 상대";
  for(const auto& who:v4FreeActors())if(growthv4::GiftEligible(growthV4,"gift:"+who,v4.flags,v4GiftContext(who)))rows.push_back({who,nameOf(who)});
 }else if(kind==2){question=nameOf(v4GiftActor)+"에게 선물을 줄까요?";for(auto& [id,count]:gifts)if(count>0&&v4GiftCatalog["items"].contains(id))rows.push_back({id,v4GiftCatalog["items"][id].value("name",id)+"   ×"+std::to_string(count)});

 }else{question=nameOf(v4GiftActor)+"에게 "+giftName(v4GiftItem)+" ×1을 건넬까요?";rows={{"give","건넨다 · 소지 "+std::to_string(gifts.count(v4GiftItem)?gifts.at(v4GiftItem):0)+"개"},{"defer","이번에는 보류한다"}};
  const auto& item=v4GiftCatalog["items"][v4GiftItem];UI::SetPosition(this,V4_UI,"DocumentPaper",{40,230});UI::SetSize(this,V4_UI,"DocumentPaper",{240,240});UI::SetTexture(this,V4_UI,"DocumentPaper",item.at("image").get<std::string>());UI::SetVisible(this,V4_UI,"DocumentPaper",true);
 }
 if(kind!=5)UI::SetVisible(this,V4_UI,"DocumentPaper",false);
 v4GiftPage=std::clamp(v4GiftPage,0,std::max(0,(int(rows.size())-1)/6));std::vector<std::string> labels;
 for(int i=v4GiftPage*6;i<std::min((v4GiftPage+1)*6,int(rows.size()));i++){v4GiftChoices.push_back(rows[i].first);labels.push_back(rows[i].second);}
 if(v4GiftPage>0){v4GiftChoices.push_back("prev");labels.push_back("이전 쪽");}if((v4GiftPage+1)*6<int(rows.size())){v4GiftChoices.push_back("next");labels.push_back("다음 쪽");}
 v4GiftChoices.push_back("back");labels.push_back(v4FreeAccepted?"선물 없이 보낸다":"그만두기");if(rows.empty())question=kind==1?"지금 제안할 수 있는 상대가 없어요":"가지고 있는 선물이 없어요";
 showMenu(question,labels,MenuKind::Event);
}
void Yumeno::v4GiftPick(int index){
 if(index<0||index>=int(v4GiftChoices.size()))return;auto choice=v4GiftChoices[index];
 if(choice=="prev"||choice=="next"){v4GiftPage+=choice=="prev"?-1:1;v4GiftMenu(v4GiftMode);return;}
 if(choice=="back"){if(v4GiftMode==2&&!v4GiftActor.empty())v4GiftSay(v4GiftCatalog["scenes"]["gift:"+v4GiftActor]["withdrawn"],"close");else v4GiftClose();return;}
 if(v4GiftMode==1){v4GiftActor=choice;v4GiftPage=0;v4GiftSay(v4GiftCatalog["scenes"]["gift:"+choice]["intro"],"items");return;}
 if(v4GiftMode==2){
  v4GiftItem=choice;auto offer="gift:"+v4GiftActor;auto disposition=v4GiftCatalog["offers"][offer]["dispositions"].value(choice,std::string("reject"));
  v4GiftSay(v4GiftCatalog["scenes"][offer][disposition=="accept"?"willing":"rejected"],disposition=="accept"?"confirm":"items");return;
 }

 auto offer="gift:"+v4GiftActor;
 if(choice=="defer"){v4GiftSay(v4GiftCatalog["scenes"][offer]["deferred"],"close");return;}
 auto committed=growthv4::CommitGift(growthV4,gifts,offer,v4GiftItem,v4.flags,v4GiftContext(v4GiftActor),true,true);
 if(!committed.changed){toast("지금은 건넬 수 없어요");v4GiftMenu(2);return;}
 giftKnown.insert(v4GiftItem);bonds[v4GiftActor]+=committed.bonds;growthv4::Unlock(growthV4,bonds);hud();pv4::Action(presentationV4,"ui_confirm");v4GiftSay(v4GiftCatalog["scenes"][offer]["acceptedByGift"][v4GiftItem],"close");
}
void Yumeno::v4GiftSay(const Json& rows,const std::string& after){
 hideMenu();UI::SetVisible(this,V4_UI,"DocumentPaper",false);mode=Mode::Story;v4GiftMode=3;v4GiftQueue=rows;v4GiftQueueAt=-1;v4GiftAfter=after;v4GiftNext();
}
void Yumeno::v4GiftNext(){
 if(++v4GiftQueueAt>=int(v4GiftQueue.size())){dialogVisible(false);if(v4GiftAfter=="items")v4GiftMenu(2);else if(v4GiftAfter=="confirm")v4GiftMenu(5);else v4GiftClose();return;}
 const auto& row=v4GiftQueue[v4GiftQueueAt];line=row.value("text",std::string());speaker=row.value("mono",false)?"":row.value("speaker",std::string());auto who=row.value("actor",std::string());portrait.clear();
 auto key=row.value("pose",row.value("appearanceActor",who));if(who!="mio"&&courtFigures.contains(key))portrait=courtFigures[key].value("texture",std::string());UI::SetColor(this,UI_ID,"Body",row.value("mono",false)?Color{.62f,.84f,1,1}:Color{.96f,.94f,.97f,1});showLine();dialogVisible(true);optv4::BeginLine(optionsV4,row.value("id",std::string()),v4.read.count(row.value("id",std::string()))>0);
 v4.log.push_back({{"id",row.value("id",std::string())},{"speaker",speaker},{"actor",who},{"text",line},{"mono",row.value("mono",false)}});if(v4.log.size()>2000)v4.log.erase(v4.log.begin());
}
void Yumeno::v4GiftClose(){
 v4GiftMode=0;v4GiftQueue=Json::array();v4GiftActor.clear();v4GiftItem.clear();for(auto id:{"DocumentShade","DocumentPaper","DocumentTitle","DocumentBody","DocumentHint"})UI::SetVisible(this,V4_UI,id,false);
 if(v4FreeAccepted)v4FreeContinue();else v4Enter(true);
}
bool Yumeno::v4GiftUpdate(float delta,bool next,bool click){
 if(!v4GiftMode)return false;
 if(v4GiftMode==3){
  shown=std::min(float(lineLength),shown+delta*optv4::CharactersPerSecond(optionsV4));text("Body",u8prefix(dialogueText(),int(shown)));bool done=int(shown)>=lineLength;if(optv4::ReportRead(optionsV4,done&&dialogueFinal()))v4.read.insert(optionsV4.line.id);
  if(optv4::CanSkip(optionsV4,Input::IsKeyDown("Control"))){skipTimer+=delta;if(skipTimer>.05f){skipTimer=0;next=true;}}
  if(optv4::AutoAdvance(optionsV4,delta,done))next=true;if(next&&dialogueAdvance())v4GiftNext();return true;
 }
 if(pressed("Backspace")||pressed("mouse1")){auto found=std::find(v4GiftChoices.begin(),v4GiftChoices.end(),"back");v4GiftPick(int(found-v4GiftChoices.begin()));return true;}
 if(menuCount<=0)return true;int old=menuHover;if(pressed("w"))menuHover=(menuHover+menuCount-1)%menuCount;if(pressed("s"))menuHover=(menuHover+1)%menuCount;
 if(old!=menuHover)pv4::Action(presentationV4,"ui_focus");
 int pick=enterNow?menuHover:-1;if(click){Vec2 m;Input::GetMousePositionForCanvas({1280,720},m);pick=menuAt(m.x,m.y);}if(pick>=0)menuAccept(pick,3);return true;
}
void Yumeno::DebugV4GiftFixture(){
 v4Start("2");v4.flags["fte:20:complete"]=true;v4ObserveGrowth();gifts["G14"]=2;gifts["G01"]=1;gifts["G02"]=0;giftKnown={"G01","G02","G14"};giftNew={"G14"};coins=20;
 for(unsigned i=0;i<128;i++)for(auto& [id,n]:storyv4::bucketData("Assets/Data/v4_story/nodes/",i)["nodes"].items()){
  if(!(n.value("scope",0)&(1<<2))||n.value("type",std::string())!="menu"||n.value("selectionRole",std::string())!="freetime")continue;
  for(const auto& o:n["options"]){if(!storyv4::eligible(v4,o))continue;const auto& target=storyv4::lookup(v4.graph,o.value("to",std::string()));if(target.value("type",std::string())=="call"&&target.value("onReturnSet",Json::object()).value("fte:35:complete",false)){storyv4::jump(v4,id);v4Enter();return;}}
 }
 lastError="Gift QA fixture needs its actual next-meeting menu";
}
std::string Yumeno::GrowthStats()const{
 Json pages=Json::object();auto entries=growthV4.contract.value("entries",Json::object());for(const auto& [id,row]:entries.items()){auto who=row.value("actor",std::string());if(!pages.contains(who))pages[who]=growthv4::Pages(growthV4,who).size();}
 return Json{{"inventory",gifts},{"discovered",giftKnown},{"newItems",giftNew},{"coins",coins},{"pulls",pulls},{"skillCatalog",[&](){Json ids=Json::array();for(const auto& row:padSkills())ids.push_back(row.at("id"));return ids;}()},{"fp",growthV4.fp},{"fpClaims",growthV4.fpClaims},{"owned",growthV4.owned},{"equipped",growthV4.equipped},{"pages",pages},{"giftClaims",growthV4.giftClaims.size()},{"correct",correctCount},{"trialHp",v4TaskHp()},{"used",growthv4::Used(growthV4)},{"capacity",growthV4.contract.empty()?0:growthv4::Capacity(growthV4,playerprogress::level(playerProgress))}}.dump();
}
void Yumeno::DebugV4ReportFixture(){
 // Explicit completed-event fixture, not a claim that these FTEs were played.
 DebugV4GiftFixture();v4.flags["fte:24:complete"]=true;v4.flags["fte:42:complete"]=true;v4ObserveGrowth();growthV4.owned.insert("sora1");
}
void Yumeno::DebugV4RulesFixture(){
 // Explicit UI fixture using real committed public-record rows, not a claim
 // that those scenes were played. An unrelated public document and a private
 // canonical row exercise the reader's publication/category boundary.
 DebugV4GiftFixture();v4Documents=Json::object();std::set<std::string> selected;const auto order=Data::Get("Assets/Data/v4_story/rules_layout.json")["order"];
 for(int i=0;i<5;i++)selected.insert(order[i].get<std::string>());
 for(unsigned i=0;i<128;i++)for(const auto& [id,n]:storyv4::bucketData("Assets/Data/v4_story/nodes/",i)["nodes"].items())for(const auto& record:n.value("publicRecords",Json::array()))if(selected.count(record.value("id",std::string())))v4CaptureRecords(Json{{"publicRecords",Json::array({record})}});
 v4Documents[order[4].get<std::string>()]["private"]=true;
 v4Documents["fixture:other-public"]={{"title","UI fixture document"},{"rows",Json::array({"Not a published rule."})},{"private",false},{"image",""}};
}
