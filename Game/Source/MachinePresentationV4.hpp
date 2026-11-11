std::vector<std::string> Yumeno::machinePool()const{
 std::vector<std::string> out;for(const auto& item:giftData["items"]){auto id=item.value("id",std::string());if(!id.empty())out.push_back(id);}return out;
}
void Yumeno::machineOpen(bool fromGallery){
 if(!fromGallery&&v4FreeActors().empty())return;if(fromGallery&&!galleryState.machine){toast("본편에서 머신을 확인하면 이용할 수 있어요");return;}
 machinePriorMusic=musicCue;machineV4={};machineFromGallery=fromGallery;machineActive=true;machineHelp=false;machineArmed=false;machineTime=machineRepeatTime=0;machineRepeatCount=machineDirection=0;
 for(const auto& [id,count]:gifts)if(count>0)giftKnown.insert(id);
 if(v4GiftCatalog.empty())v4GiftCatalog=Data::Get("Assets/Data/v4_story/gifts.json");
 hideMenu();dialogVisible(false);hideExplore();exworld::visible(world,false);fvis("FHud",false);UI::SetVisible(this,UI_ID,"Portrait",false);UI::SetVisible(this,UI_ID,"Background",false);
 if(fromGallery)UI::SetVisible(this,"galleryv4","root",false);
 UI::Show(this,"Assets/UI/MachineV4.hbwidget.json","machinev4");mode=Mode::Machine;music("bgm_freetime");machineDraw();sfx("ui_confirm");
}
void Yumeno::machineClose(){
 machineActive=false;UI::Remove(this,"machinev4");galleryState.machine=true;galleryDirty=true;
 if(machineFromGallery){galleryPlaying.clear();music("bgm_title");mode=Mode::Gallery;UI::SetVisible(this,"galleryv4","root",true);galleryDraw();}
 else{v4.flags["mode:monomono:visited"]=true;music(machinePriorMusic.empty()?"@silence":machinePriorMusic);v4Enter(true);}sfx("ui_cancel");
}
void Yumeno::machineDraw(){
 auto pool=machinePool();int known=0;for(const auto& id:pool)if(giftKnown.count(id))++known;
 int wallet=coins-(machineV4.phase==machinev4::Phase::Select?machineV4.selected:0);
 for(int d=0,divisor=1;d<3;d++,divisor*=10)for(int kind=0;kind<2;kind++){int number=kind?machineV4.selected:wallet;auto id=std::string(kind?"McBet":"McWallet")+std::to_string(d);UI::SetText(this,"machinev4",id,std::to_string((number/divisor)%10));UI::SetVisible(this,"machinev4",id,d==0||number>=divisor);}
 int rate=int(machinev4::repeatPercent(int(pool.size()),known,machineV4.selected)*100);
 for(int d=0,divisor=1;d<5;d++,divisor*=10){auto id="McRepeat"+std::to_string(d);UI::SetText(this,"machinev4",id,std::to_string((rate/divisor)%10));UI::SetVisible(this,"machinev4",id,d<3||rate>=divisor);}
 using P=machinev4::Phase;bool result=machineV4.phase==P::Reveal||machineV4.phase==P::Prize;
 for(auto id:{"McResultShade","McResultCaption","McPrize","McPrizeName","McPrizePlate"})UI::SetVisible(this,"machinev4",id,result);
 UI::SetVisible(this,"machinev4","McNew",result&&machineV4.fresh);UI::SetVisible(this,"machinev4","McLucky",machineV4.phase==P::Extra);
 if(result){const auto& item=v4GiftCatalog["items"].at(machineV4.prize);UI::SetTexture(this,"machinev4","McPrize",item.at("image").get<std::string>());UI::SetText(this,"machinev4","McPrizeName",item.value("name",machineV4.prize));}
 bool select=machineV4.phase==P::Select;UI::SetText(this,"machinev4","McHint",select?"W/S 투입량 · Enter 결정 · Enter/가운데 버튼 유지+W/S 10개 · F1 패드 · F3 도움말 · Esc 돌아가기":result?"새 입력으로 결과 확인":"");
 UI::SetVisible(this,"machinev4","McHelp",machineHelp);UI::SetVisible(this,"machinev4","McHelpShade",machineHelp);
 UI::SetOpacity(this,"machinev4","McHandle",select?1.f:.4f);
}
void Yumeno::machineUpdate(float delta){
 if(!machineActive)return;if(!machineArmed){if(!Input::IsKeyDown("Enter")&&!Input::IsKeyDown("mouse0")&&!Input::IsKeyDown("z"))machineArmed=true;return;}
 if(machineHelp){if(pressed("F3")||pressed("Escape")||pressed("Backspace")||pressed("Enter")||pressed("mouse0")){machineHelp=false;machineArmed=false;machineDraw();}return;}
 using P=machinev4::Phase;static std::mt19937 rng{std::random_device{}()};auto random=[&](){return rng();};
 bool click=pressed("mouse0"),confirm=pressed("Enter")||pressed("z");Vec2 mouse;Input::GetCenteredMousePositionForCanvas({1280,720},mouse);
 if(machineV4.phase==P::Select){
  if(pressed("Escape")||pressed("Backspace")||pressed("x")||pressed("mouse1")){machineClose();return;}
  static const auto layout=Data::Get("Assets/Data/v4_story/machine_layout.json");auto hit=[&](const char* key){const auto& r=layout.at(key);return mouse.x>=r[0].get<float>()&&mouse.x<r[0].get<float>()+r[2].get<float>()&&mouse.y>=r[1].get<float>()&&mouse.y<r[1].get<float>()+r[3].get<float>();};
  if(confirm||(click&&hit("handle"))){if(machinev4::confirm(machineV4,coins)){machineTime=0;sfx("sfx_capsule");machineDraw();}else sfx("ui_cancel");return;}
  if(pressed("F3")){machineHelp=true;machineArmed=false;machineDraw();return;}
  if(pressed("F1")){UI::SetVisible(this,"machinev4","root",false);padToggle();padPageAt=2;padRow=padListFirst=0;padShowPage();return;}
  int direction=Input::IsKeyDown("w")||Input::IsKeyDown("ArrowUp")?1:Input::IsKeyDown("s")||Input::IsKeyDown("ArrowDown")?-1:0;
  bool pulse=false;if(direction!=machineDirection){machineDirection=direction;machineRepeatCount=0;machineRepeatTime=0;pulse=direction!=0;}else if(direction){machineRepeatTime+=delta;if(machineRepeatTime>=(machineRepeatCount==1?.35f:.1f)){machineRepeatTime=0;pulse=true;}}
  int amount=0;if(pulse){++machineRepeatCount;amount=direction*((machineRepeatCount+14)/15);if(Input::IsKeyDown("Enter")||Input::IsKeyDown("mouse2"))amount=direction*10;}
  if(click&&(hit("up")||hit("down")))amount=hit("up")?1:-1;
  if(amount){int before=machineV4.selected;machinev4::change(machineV4,amount,coins);if(before!=machineV4.selected){sfx("sfx_coin");machineDraw();}}return;
 }
 machineTime+=std::max(0.f,delta);
 if(machineV4.phase==P::Pay&&machineTime>=.4f){
  if(!machinev4::payAndAward(machineV4,coins,gifts,giftKnown,giftNew,machinePool(),random)){machineV4.phase=P::Select;sfx("ui_cancel");machineDraw();return;}
  ++pulls;galleryDirty=true;machineTime=0;machineArmed=false;sfx("sfx_capsule_open");machineDraw();return;
 }
 if(machineV4.phase==P::Reveal&&machineTime>=.35f){machineV4.phase=P::Prize;machineDraw();return;}
 if(machineV4.phase==P::Prize){bool input=false;for(const auto& [key,edge]:keyEdges)if(edge)input=true;if(input){bool extra=machinev4::next(machineV4,random());machineTime=0;machineArmed=false;if(extra)sfx("sfx_capsule_bonus");machineDraw();}return;}
 if(machineV4.phase==P::Extra&&machineTime>=.8f){machineV4.phase=P::Pay;machineTime=0;machineDraw();}
}
std::string Yumeno::MachineStats()const{return Json{{"active",machineActive},{"phase",int(machineV4.phase)},{"selected",machineV4.selected},{"cost",machineV4.cost},{"wallet",coins},{"draws",machineV4.draws},{"prize",machineV4.prize},{"extra",machineV4.extra},{"help",machineHelp},{"fromGallery",machineFromGallery},{"inventory",gifts}}.dump();}
