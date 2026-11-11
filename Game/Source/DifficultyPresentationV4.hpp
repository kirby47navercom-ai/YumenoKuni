void Yumeno::difficultyOpen(const std::string& slot){
 difficultySlot=slot;difficultyOn=true;difficultyArmed=false;difficultyLoading=false;chapterReplay={};difficultyRow=0;titleMenu(false);
 UI::Show(this,"Assets/UI/DifficultyV4.hbwidget.json","difficultyv4");difficultyDraw();
}
void Yumeno::difficultyDraw(){
 static const auto layout=Data::Get("Assets/Data/v4_story/difficulty_layout.json");
 UI::SetTexture(this,"difficultyv4","DfArt",layout.at("variants").at(difficultyRow).at(difficultyV4.logic).at(difficultyV4.action).get<std::string>());
}
void Yumeno::difficultyUpdate(){
 if(!difficultyArmed){if(!Input::IsKeyDown("Enter")&&!Input::IsKeyDown("mouse0"))difficultyArmed=true;return;}
 bool back=pressed("Escape")||pressed("Backspace")||pressed("mouse1");
 if(back){difficultyLoading=false;chapterReplay={};difficultyOn=false;UI::Remove(this,"difficultyv4");sfx("ui_cancel");if(difficultySlot.empty())titleMenu(true);else{chapterSelectArmed=false;chapterSelectDraw();}return;}
 if(difficultyLoading){
  int result=chapterarchive::replayStep(chapterReplay,[](const std::string& key){return Json::parse(Save::ReadText(key));});if(!result)return;
  difficultyLoading=false;if(result<0||!v4Load(difficultySlot,true)){chapterReplay={};toast("이 구간의 진행 기록을 불러오지 못했어요");return;}
  chapterReplay={};chapterSelectOn=chapterSelectWidgetShown=false;UI::Remove(this,"chapterselectv4");difficultyOn=false;UI::Remove(this,"difficultyv4");titleMenu(false);sfx("ui_confirm");return;
 }
 int prior=difficultyRow,logic=difficultyV4.logic,action=difficultyV4.action;
 if(pressed("w")||pressed("ArrowUp"))difficultyRow=(difficultyRow+2)%3;if(pressed("s")||pressed("ArrowDown"))difficultyRow=(difficultyRow+1)%3;
 if(pressed("a")||pressed("ArrowLeft"))difficultyv4::change(difficultyV4,difficultyRow,-1);if(pressed("d")||pressed("ArrowRight"))difficultyv4::change(difficultyV4,difficultyRow,1);
 bool confirm=pressed("Enter")||pressed("Space");
 if(pressed("mouse0")){Vec2 m;Input::GetCenteredMousePositionForCanvas({1280,720},m);static const auto layout=Data::Get("Assets/Data/v4_story/difficulty_layout.json");auto hit=[&](const Json& r){return m.x>=r[0].get<float>()&&m.x<r[0].get<float>()+r[2].get<float>()&&m.y>=r[1].get<float>()&&m.y<r[1].get<float>()+r[3].get<float>();};
  // The source Start sign is drawn last and overlaps the action row's AABB.
  if(hit(layout["rows"][2])){difficultyRow=2;confirm=true;}else{for(int r=0;r<2;r++)if(hit(layout["rows"][r]))difficultyRow=r;for(int r=0;r<2;r++)for(int d=0;d<3;d++)if(hit(layout["values"][r][d])){difficultyRow=r;(r?difficultyV4.action:difficultyV4.logic)=d;}}
 }
 if(prior!=difficultyRow||logic!=difficultyV4.logic||action!=difficultyV4.action){sfx("ui_select");difficultyDraw();}
 if(!confirm||difficultyRow!=2)return;
 if(!difficultySlot.empty()){
  try{auto common=Json::parse(Save::ReadText(campaignv4::slot("yumeno-progress-v4")));Json profile=Json::object();
   if(campaignv4::installed()&&common.is_null())common=Json::object();
   try{profile=Json::parse(Save::ReadText(campaignv4::slot("yumeno-v4-gallery")));}catch(const std::exception&){}
   if(!chapterarchive::beginReplay(chapterReplay,common,{common.value("galleryBank",Json::object()),profile,galleryRecoveryBank,galleryProfileHead},v4.active?v4.read:std::set<std::string>{}))throw std::runtime_error("Chapter replay history");
   difficultyLoading=true;toast("진행 기록을 불러오고 있어요…");
  }catch(const std::exception&){chapterReplay={};toast("진행 기록을 읽지 못했어요");}return;
 }
 v4Start("P",true,campaignv4::installed(),"",true);
 difficultyOn=false;UI::Remove(this,"difficultyv4");titleMenu(false);sfx("ui_confirm");
}
int Yumeno::v4Damage(int raw){
 int amount=stageKind=="climax"?difficultyv4::anagramDamage(difficultyV4.action):difficultyv4::wakDamage(raw,difficultyV4.logic);
 amount=growthv4::Damage(growthV4,amount);int before=v4TaskHp(),hp=std::max(0,before-amount);v4TrialHp=v4TaskEntryHp=hp;debate.hearts=v4TaskEntryHearts=(hp+1999)/2000;if(hp<before)sfx("v3se_316");return hp;
}
