// Original shared-piece/solved-count mechanics; own authored comic and dialogue.
void Yumeno::v4ComicTileV3(const std::string& id,const hb::Json& row,bool visible){
 if(row.is_null()||!row.contains("texture")){UI::SetVisible(this,"comicv4",id,false);return;}
 auto r=row.at("rect").get<std::array<float,4>>();UI::SetPosition(this,"comicv4",id,{r[0],r[1]});UI::SetSize(this,"comicv4",id,{r[2],r[3]});UI::SetRotation(this,"comicv4",id,row.value("rotation",0.f));UI::SetTexture(this,"comicv4",id,row.at("texture").get<std::string>());UI::SetOpacity(this,"comicv4",id,1);UI::SetVisible(this,"comicv4",id,visible);
}
void Yumeno::v4ComicStart(){
 climaxEndDoneV4=false;v4ComicBankV3=Data::Get("Assets/Data/climax_ui_v3.json");const auto& presentation=stage.at("comicPresentation");const bool storyStock=presentation.contains("storyStock");
 const auto book=storyStock?presentation.at("bookFile").get<std::string>():v4ComicBankV3.at("bookFiles").at(stage.at("id").get<std::string>()).get<std::string>();
 v4ComicBankV3["book"]=Data::Get(book);v4ComicPageTurnV4=1;auto eligible=presentation.at("unlock").at("initialAutoFillEligibleSlots").get<std::vector<int>>();
 comicProgressV4.reset(int(stage.at("slots").size()),eligible,skillOn("two_dimensional_love")?20:0,std::uint32_t(storyv4::bucket(stage.value("id",std::string()),65521)));
 v4ComicStock=Json::array();std::vector<int> gates,origins;
 std::vector<std::vector<int>> prerequisites;
 for(const auto& binding:presentation.at(storyStock?"storyStock":"stock")){
  int source=binding.at("originSlot");origins.push_back(source);
  if(storyStock)prerequisites.push_back(binding.at("requires").get<std::vector<int>>());
  else gates.push_back(binding.at("thresholds").at(std::clamp(difficultyV4.logic,0,2)));
  if(source==-1&&storyStock){v4ComicStock.push_back(binding);continue;}
  const auto& slot=stage.at("slots").at(source);bool found=false;
  for(const auto& option:slot.at("options"))if(option.at("id")==slot.at("answer")){auto card=option;card["originSlot"]=source;v4ComicStock.push_back(card);found=true;break;}
  if(!found)throw std::runtime_error("Comic accepted image missing");
 }
 if(storyStock)comicProgressV4.configureStoryStock(std::move(prerequisites),std::move(origins));else comicProgressV4.configureStock(std::move(gates),std::move(origins));
 v4ComicStockPage=0;optHover=0;v4ComicCursor=comicProgressV4.next(int(stage["slots"].size()));v4ComicSpread=comicv4ui::page(stage,v4ComicCursor);
 v4ComicClockV3=0;v4ComicFeedbackV3=-1;v4ComicFeedbackTargetV3=-1;v4ComicPlacing=-1;v4ComicPlaceTicks=0;v4ComicReplay=false;v4ComicZoom=v4ComicExpanded=false;v4ComicStockAnimationTimeV4=-1;v4ComicStockAnimationV4=Json();stageTime=0;stageLimit=420.f*trialTimeFactor();
 v4ComicIntroTime=0;
 sfx("v3se_447");
}
void Yumeno::v4ComicClear(){if(!comicShown)return;if(v4ComicBankV3.empty())v4ComicBankV3=Data::Get("Assets/Data/climax_ui_v3.json");for(const auto& value:v4ComicBankV3.at("nodeIds"))UI::SetVisible(this,"comicv4",value.get<std::string>(),false);}
void Yumeno::v4ComicHudV3(){
 if(v4ComicReview||v4ComicReplay)return;int titleFrame=int(v4ComicClockV3*60)%v4ComicBankV3.at("titleDurationFrames").get<int>();const Json* title=&v4ComicBankV3.at("titleFrames").at(0);for(const auto& row:v4ComicBankV3.at("titleFrames"))if(row.at("atFrame").get<int>()<=titleFrame)title=&row;v4ComicTileV3("OriginalTitle",title->at("tile"),true);int remaining=std::max(0,int((stageLimit-stageTime)*1000));int ms=(remaining/60000)*100000+(remaining/1000%60)*1000+remaining%1000,power=1;
 for(int i=0;i<7;i++){UI::SetTexture(this,"comicv4","V3TimeD"+std::to_string(i),v4ComicBankV3.at("timerDigits").at((ms/power)%10).get<std::string>());power*=10;}
 int group=maxHearts<=5?5:maxHearts<=7?7:10;const auto& hearts=v4ComicBankV3.at("bakedHeartFractions").at(std::to_string(group));for(int i=0;i<group;i++){int units=std::clamp(v4TaskHp()-(group-1-i)*2000,0,2000),step=(units+199)/200;v4ComicTileV3("ComicHeart"+std::to_string(i),hearts.at(i).at(step),step>0);}
 const auto& cursor=v4ComicBankV3.at("bakedComponents").at("cursor");auto r=cursor.at("rect").get<std::array<float,4>>();UI::SetPosition(this,"comicv4","V3Cursor",{aimX+r[0],aimY+r[1]});UI::SetOpacity(this,"comicv4","V3Cursor",.85f+.15f*std::sin(v4ComicClockV3*8));
}
void Yumeno::v4ComicHighlight(){
 if(v4ComicReview||v4ComicReplay||v4ComicStock.empty())return;optHover=std::clamp(optHover,0,int(v4ComicStock.size())-1);const auto& bank=v4ComicBankV3;const Json* morph=nullptr;if(v4ComicStockAnimationTimeV4>=0){const auto& frames=v4ComicStockAnimationV4.at("frames");morph=&frames.at(std::min(int(v4ComicStockAnimationTimeV4*60),int(frames.size())-1));v4ComicTileV3("V3StockMorph",morph->at("base"),true);for(const auto& pair:bank.at("componentNodes").items())if(pair.key().compare(0,5,"stock")==0)UI::SetVisible(this,"comicv4",pair.value().get<std::string>(),false);}const auto& positions=morph?morph->at("slots"):bank.at(v4ComicExpanded?"stockExpandedSlots":"stockSlots");const auto& marks=morph?morph->at("slots"):bank.at(v4ComicExpanded?"bakedExpandedStockSlots":"bakedStockSlots");opts.clear();optRects.clear();
 const int pageSize=comicv4ui::stockPageSize;v4ComicStockPage=optHover/pageSize;
 const int first=v4ComicStockPage*pageSize;
 for(int j=0;j<pageSize;j++){
  const int i=first+j;auto n=std::to_string(j);
  for(const auto* prefix:{"CandidateI","CandidateP"})UI::SetVisible(this,"comicv4",prefix+n,false);
  if(i>=int(v4ComicStock.size())){for(const auto* prefix:{"StockMark","StockI","StockFocus","StockRemaining"})UI::SetVisible(this,"comicv4",prefix+n,false);continue;}
  bool used=comicProgressV4.stockUsed(i),ready=comicProgressV4.stockReady(i);const auto& pose=positions.at(j).at("image").at(0);auto r=pose.at("rect").get<std::array<float,4>>();opts.push_back(n);optRects.push_back(r);v4ComicTileV3("StockMark"+n,marks.at(j).at(used?"used":"idle"),true);
  UI::SetTexture(this,"comicv4","StockI"+n,v4ComicStock.at(i).at("image").get<std::string>());UI::SetPosition(this,"comicv4","StockI"+n,{r[0]+3,r[1]+3});UI::SetSize(this,"comicv4","StockI"+n,{r[2]-6,r[3]-6});UI::SetRotation(this,"comicv4","StockI"+n,pose.value("rotation",0.f));UI::SetVisible(this,"comicv4","StockI"+n,ready&&!used);v4ComicTileV3("StockFocus"+n,marks.at(j).at("focus"),i==optHover);
  if(!used&&!ready){auto digit=marks.at(j).at("locked");digit["texture"]=bank.at("lockedRemainingDigits").at(std::clamp(comicProgressV4.stockRemaining(i),0,9));v4ComicTileV3("StockRemaining"+n,digit,true);}else UI::SetVisible(this,"comicv4","StockRemaining"+n,false);
 }
 const auto& choice=v4ComicStock.at(optHover);bool ready=comicProgressV4.stockReady(optHover),used=comicProgressV4.stockUsed(optHover);const auto& selected=bank.at("selectedOwnImage").at(0);auto r=selected.at("rect").get<std::array<float,4>>();auto n=std::to_string(optHover-first);
 if(int(v4ComicStock.size())>pageSize){UI::SetText(this,"comicv4","Hint","Z / X   조각 묶음   "+std::to_string(v4ComicStockPage+1)+" / "+std::to_string((int(v4ComicStock.size())+pageSize-1)/pageSize));UI::SetVisible(this,"comicv4","Hint",true);}
 UI::SetPosition(this,"comicv4","CandidateI"+n,{r[0],r[1]});UI::SetSize(this,"comicv4","CandidateI"+n,{r[2],r[3]});UI::SetRotation(this,"comicv4","CandidateI"+n,selected.value("rotation",0.f));UI::SetTexture(this,"comicv4","CandidateI"+n,choice.at("image").get<std::string>());UI::SetVisible(this,"comicv4","CandidateI"+n,ready&&!v4ComicExpanded);UI::SetVisible(this,"comicv4","V3SelectedUsed",used);UI::SetVisible(this,"comicv4","V3SelectedLocked",!used&&!ready);
 std::string caption=ready?choice.value("label",std::string()):used?"이 조각은 이미 만화에 끼웠다.":"앞으로 "+std::to_string(comicProgressV4.stockRemaining(optHover))+"개의 빈칸을 더 채우면 열린다.";UI::SetText(this,"comicv4","Caption",caption);UI::SetText(this,"comicv4","ZoomCaption",caption);if(ready)UI::SetTexture(this,"comicv4","ZoomImage",choice.at("image").get<std::string>());if(comicProgressV4.stockBeginUnlock(optHover))sfx("v3se_464");v4ComicUnlockDrawV3();
}
void Yumeno::v4ComicUnlockDrawV3(){
 int index=comicProgressV4.stockUnlockIndex;if(index<0){UI::SetVisible(this,"comicv4","V3Unlock",false);return;}
 const auto& sequence=v4ComicBankV3.at("sequences").at("unlock");int frame=int(comicProgressV4.stockUnlockElapsed*sequence.value("fps",60));const Json* row=&sequence.at("frames").at(0);for(const auto& sample:sequence.at("frames"))if(sample.at("atFrame").get<int>()<=frame)row=&sample;
 UI::SetVisible(this,"comicv4","V3SelectedLocked",false);v4ComicTileV3("V3Unlock",row->at("tile"),!v4ComicExpanded);
 const auto& pose=row->at("ownImage");auto r=pose.at("rect").get<std::array<float,4>>();auto id="CandidateI"+std::to_string(index%comicv4ui::stockPageSize);UI::SetTexture(this,"comicv4",id,v4ComicStock[index].at("image").get<std::string>());UI::SetPosition(this,"comicv4",id,{r[0],r[1]});UI::SetSize(this,"comicv4",id,{r[2],r[3]});UI::SetRotation(this,"comicv4",id,pose.value("rotation",0.f));UI::SetOpacity(this,"comicv4",id,pose.value("opacity",1.f));UI::SetVisible(this,"comicv4",id,!v4ComicExpanded);UI::SetText(this,"comicv4","Caption",v4ComicStock[index].value("label",std::string()));
}
void Yumeno::v4ComicReplayDrawV3(bool dialogue){
 v4ComicClear();UI::SetVisible(this,"comicv4","root",true);UI::SetVisible(this,"comicv4","ReplayShade",true);
 const auto& frame=v4ComicBankV3.at("book").at("replay").at(v4ComicReplayAt);v4ComicTileV3("ReplayImage",frame.at("image"),true);dialogVisible(false);
 // The original replays a page's panels in order and waits for narration;
 // a correct piece is never presented as a separate invented ACT slideshow.
 for(auto id:{"ReplayCaption","ReplayCaptionShadow"}){UI::SetText(this,"comicv4",id,dialogue?line:std::string());UI::SetVisible(this,"comicv4",id,dialogue);}
}
void Yumeno::v4ComicComplete(bool dialogue){
 if(!comicShown){UI::Show(this,"Assets/UI/ComicV4.hbwidget.json","comicv4");comicShown=true;}if(v4ComicBankV3.empty())v4ComicBankV3=Data::Get("Assets/Data/climax_ui_v3.json");if(v4ComicReplay){v4ComicReplayDrawV3(dialogue);return;}if(!dialogue&&stage.contains("slots")){v4ComicDraw();return;}v4ComicClear();UI::SetVisible(this,"comicv4","root",true);
 if(!v4ComicBankV3.contains("book")){auto id="T"+v4.graph.value("chapter",std::string())+"-MG-01";v4ComicBankV3["book"]=Data::Get(v4ComicBankV3.at("bookFiles").at(id).get<std::string>());}
 UI::SetVisible(this,"comicv4","ReplayShade",true);v4ComicTileV3("CompletePage",v4ComicBankV3.at("book").at("pages").back().at("complete"),true);if(dialogue){for(auto id:{"ReplayCaption","ReplayCaptionShadow"}){UI::SetText(this,"comicv4",id,line);UI::SetVisible(this,"comicv4",id,true);}dialogVisible(false);}
}
void Yumeno::v4ComicDraw(){
 v4ComicClear();UI::SetVisible(this,"comicv4","root",true);const auto& bank=v4ComicBankV3;for(auto id:{"Shade","Caption","CaptionPlate","V3Koma"})UI::SetVisible(this,"comicv4",id,true);
 for(const auto& [key,value]:bank.at("componentNodes").items()){bool visible=key!="placeOK"&&key!="placeNG"&&key!="selectedUsed"&&key!="selectedLocked";if(key=="stockExpandedBase"||key=="stockExpandedWord")visible=v4ComicExpanded;if(key=="stockBase"||key=="stockWord")visible=!v4ComicExpanded;UI::SetVisible(this,"comicv4",value.get<std::string>(),visible);}
 int spreads=comicv4ui::count(stage),group=maxHearts<=5?5:maxHearts<=7?7:10;UI::SetVisible(this,"comicv4","V3HpBase"+std::to_string(group),!v4ComicReview);for(int i=0;i<7;i++)UI::SetVisible(this,"comicv4","V3TimeD"+std::to_string(i),!v4ComicReview);
 for(int i=0;i<4;i++){int number=i<2?spreads:v4ComicSpread+1,divisor=i%2==0?1:10;UI::SetTexture(this,"comicv4","V3PageD"+std::to_string(i),bank.at(i<2?"pageDigits":"pageActiveDigits").at((number/divisor)%10).get<std::string>());UI::SetVisible(this,"comicv4","V3PageD"+std::to_string(i),true);}
 for(const auto& pair:std::vector<std::pair<std::string,bool>>{{"PageLeft",v4ComicSpread>0},{"PageLeftKey",v4ComicSpread>0},{"PageRight",v4ComicSpread+1<spreads},{"PageRightKey",v4ComicSpread+1<spreads}})UI::SetVisible(this,"comicv4",pair.first,pair.second);
 const auto& book=bank.at("book");const auto& currentPage=book.at("pages").at(v4ComicSpread);v4ComicTileV3("PageBook",currentPage.at("base"),true);
 for(int i:comicv4ui::slots(stage,v4ComicSpread))v4ComicTileV3("SlotI"+std::to_string(i),book.at("slots").at(std::to_string(i)).at("filled"),comicProgressV4.filled(i));
 if(v4ComicSpread>0){const auto& previous=book.at("pages").at(v4ComicSpread-1);v4ComicTileV3("PreviousBook",previous.at("previous"),true);for(int i:comicv4ui::slots(stage,v4ComicSpread-1))v4ComicTileV3("PreviousSlot"+std::to_string(i),book.at("slots").at(std::to_string(i)).at("previous"),comicProgressV4.filled(i));}else v4ComicTileV3("PreviousBook",book.at("pages").at(0).at("cover"),true);
 // The top strip contains whole miniature pages with the same reveal state.
 const int thumbFirst=std::clamp(v4ComicSpread-1,0,std::max(0,spreads-3));
 for(int p=thumbFirst;p<std::min(thumbFirst+3,spreads);p++){
  auto r=comicv4ui::pageThumb(p,v4ComicSpread);auto suffix=std::to_string(p-thumbFirst);auto thumbTile=[&](const std::string& id,Json row,bool visible){int offset=(stage.at("comicPresentation").contains("storyStock")?p:0)-v4ComicSpread;row["rect"][0]=row["rect"][0].get<float>()+offset*142;row["rect"][1]=row["rect"][1].get<float>()-offset*15;v4ComicTileV3(id,row,visible);};thumbTile("PageThumbFrame"+suffix,book.at("pages").at(p).at("thumb"),true);auto glow="PageThumbGlow"+suffix;UI::SetPosition(this,"comicv4",glow,{r[0]-4,r[1]-4});UI::SetSize(this,"comicv4",glow,{r[2]+8,r[3]+8});UI::SetVisible(this,"comicv4",glow,p==v4ComicSpread);
  auto list=comicv4ui::slots(stage,p);for(int j=0;j<int(list.size());j++)thumbTile("PageThumb"+suffix+"_"+std::to_string(j),book.at("slots").at(std::to_string(list[j])).at("thumb"),comicProgressV4.filled(list[j]));
 }
 if(v4ComicReview){UI::SetVisible(this,"comicv4","Hint",true);UI::SetText(this,"comicv4","Hint","Enter  사건의 흐름을 다시 짚는다");return;}
 if(v4ComicCursor>=0&&comicv4ui::page(stage,v4ComicCursor)==v4ComicSpread&&!comicProgressV4.filled(v4ComicCursor)){auto r=comicv4ui::rect(stage,v4ComicCursor);float x=std::clamp(r[0]+r[2]/2-90.f,260.f,680.f),y=r[1]>300?r[1]-150:r[1]+r[3]-20;const auto& bubble=bank.at("bakedComponents").at("holeHint0");auto b=bubble.at("rect").get<std::array<float,4>>();UI::SetPosition(this,"comicv4","HoleHintPlate",{x,y});UI::SetSize(this,"comicv4","HoleHintPlate",{b[2],b[3]});UI::SetVisible(this,"comicv4","HoleHintPlate",!v4ComicExpanded);UI::SetPosition(this,"comicv4","HoleHint",{x+25,y+76});UI::SetText(this,"comicv4","HoleHint",stage["comicPresentation"]["slots"][v4ComicCursor].value("holeHint",std::string()));UI::SetVisible(this,"comicv4","HoleHint",!v4ComicExpanded);}
 v4ComicHighlight();v4ComicHudV3();v4ComicPagePoseV4();
}
void Yumeno::v4ComicPagePoseV4(){
 const auto& book=v4ComicBankV3.at("book");float u=std::min(v4ComicPageTurnV4,1.f);
 const auto& frames=v4ComicBankV3.at("pageTurn").at(v4ComicPageDirectionV4>0?"fl_l_c":"fl_r_c");int at=std::min(int(u*(int(frames.size())-1)),int(frames.size())-1);const auto& f=frames.at(at);
 auto pose=[&](const std::string& id,const Json& row){auto r=row.at("rect").get<std::array<float,4>>();float s=f.at("scale"),dx=f.at("dx"),dy=f.at("dy");UI::SetPosition(this,"comicv4",id,{556+(r[0]-556)*s+dx,143+(r[1]-143)*s+dy});UI::SetSize(this,"comicv4",id,{r[2]*s,r[3]*s});UI::SetOpacity(this,"comicv4",id,f.at("alpha").get<float>());};
 pose("PageBook",book.at("pages").at(v4ComicSpread).at("base"));for(int i:comicv4ui::slots(stage,v4ComicSpread))if(comicProgressV4.filled(i))pose("SlotI"+std::to_string(i),book.at("slots").at(std::to_string(i)).at("filled"));
}
void Yumeno::v4ComicShow(){
 sclear();if(!stage.contains("comicPresentation"))throw std::runtime_error("Comic current binding missing");
 if(v4ComicReplay){
  const auto& replay=v4ComicBankV3.at("book").at("replay");
  const auto previousPage=replay.at(v4ComicReplayAt).at("page").get<int>();
  ++v4ComicReplayAt;
  v4ComicReplayTime=0;
  if(v4ComicReplayAt>=int(replay.size())){
   v4ComicReplay=false;v4ComicReview=false;v4ComicClear();beginScript();return;
  }
  if(replay.at(v4ComicReplayAt).at("page").get<int>()!=previousPage)sfx("v3se_007");
  v4ComicReplayDrawV3();
  return;
 }
 v4TaskLinks=comicProgressV4.completed();v4ComicPage=stage["comicPresentation"]["board"].value("image",std::string());v4ComicZoom=v4ComicExpanded=false;v4ComicPlacing=-1;v4ComicPlaceTicks=0;v4ComicReview=v4TaskLinks>=int(stage["slots"].size());if(v4ComicReview){trialScoreCapture();v4ComicClockV3=0;sfx("v3se_448");}if(v4ComicIntroTime>=0){v4ComicClear();UI::SetVisible(this,"comicv4","ReplayShade",true);}else v4ComicDraw();
}
bool Yumeno::v4ComicUpdate(float delta,bool click){
 if(!v4TaskActive||stageKind!="climax")return false;v4ComicClockV3+=delta;
 if(v4ComicIntroTime>=0){
  // Start event fl_in (2..97) followed by fl_out (98..199).
  constexpr float enterTime=95.f/60.f, exitTime=101.f/60.f;
  v4ComicIntroTime+=delta;
  if(v4ComicIntroTime<enterTime+exitTime){
   const auto& title=v4ComicBankV3.at("titleFrames").at(0).at("tile");
   v4ComicTileV3("OriginalTitle",title,true);
   const float opacity=v4ComicIntroTime<enterTime
    ? std::min(1.f,v4ComicIntroTime*6.f)
    : 1.f-(v4ComicIntroTime-enterTime)/exitTime;
   UI::SetOpacity(this,"comicv4","OriginalTitle",opacity);
  }else{
   v4ComicIntroTime=-1;
   v4ComicClockV3=0;
   pv4::MusicPolicy(presentationV4,stage.at("presentation").at("music"));
   v4ComicDraw();
  }
  return true;
 }
 if(v4ComicReplay){
  v4ComicReplayTime+=delta;
  if(v4ComicReplayTime>=18.f/60.f&&comicProgressV4.responded.insert(v4ComicReplayAt).second){
   if(v4ComicReplayAt>=int(stage["slots"].size()))v4TaskQueue(stage.at("comicPresentation").at("recap"),"comic");
   else{
    const auto& slot=stage["slots"][v4ComicReplayAt];
    for(const auto& card:slot["options"])if(card.at("id")==slot.at("answer")){v4TaskQueue(card.value("response",Json::array()),"comic");break;}
   }
  }
  return true;
 }
 if(v4ComicPageTurnV4<1){v4ComicPageTurnV4=std::min(1.f,v4ComicPageTurnV4+delta*60/7);v4ComicPagePoseV4();return true;}
 if(v4ComicFeedbackV3>=0){v4ComicFeedbackV3+=delta;const auto& clip=v4ComicBankV3.at("placementClips").at(v4ComicCorrectV3?"ok":"ng");const auto& frames=clip.at("frames");int frame=std::min(int(v4ComicFeedbackV3*60),int(frames.size())-1);v4ComicTileV3(v4ComicCorrectV3?"V3PlaceOK":"V3PlaceNG",frames.at(frame),true);if(v4ComicFeedbackV3>=int(frames.size())/60.f){v4ComicFeedbackV3=-1;if(!v4ComicCorrectV3){hurt();++trialResults.current.gaffe;}if(!restartStage){v4ComicReview=comicProgressV4.completed()>=int(stage["slots"].size());if(v4ComicReview){v4ComicClockV3=0;trialScoreCapture();sfx("v3se_448");}v4ComicDraw();}}return true;}
 if(!v4ComicReview&&v4ComicPlacing<0){stageTime+=delta;if(stageTime>=stageLimit){hurt();restartStage=true;return true;}v4ComicHudV3();}
 if(v4ComicStockAnimationTimeV4>=0){v4ComicStockAnimationTimeV4+=delta;if(v4ComicStockAnimationTimeV4>=v4ComicStockAnimationV4.at("durationFrames").get<int>()/60.f){v4ComicStockAnimationTimeV4=-1;v4ComicDraw();}else v4ComicHighlight();return true;}
 if(v4ComicPlacing>=0){
  v4ComicPlaceTicks=std::min(20.f,v4ComicPlaceTicks+delta*60.f);float u=v4ComicPlaceTicks/20.f;auto r=comicv4ui::rect(stage,v4ComicPlaceSlot);auto s=v4ComicBankV3.at("selectedOwnImage").at(0).at("rect").get<std::array<float,4>>();UI::SetPosition(this,"comicv4","PlaceImage",{s[0]+(r[0]-s[0])*u,s[1]+(r[1]-s[1])*u});UI::SetSize(this,"comicv4","PlaceImage",{s[2]+(r[2]-s[2])*u,s[3]+(r[3]-s[3])*u});UI::SetRotation(this,"comicv4","PlaceImage",comicv4ui::angle*u);
  if(v4ComicPlaceTicks>=20){int target=v4ComicPlaceSlot,index=v4ComicPlacing;v4ComicPlacing=-1;v4ComicCorrectV3=v4ComicStock[index]["originSlot"].get<int>()==target;v4ComicFeedbackTargetV3=target;v4ComicFeedbackV3=0;UI::SetVisible(this,"comicv4","PlaceImage",false);if(v4ComicCorrectV3){comicProgressV4.place(target,int(stage["slots"].size()));v4TaskLinks=comicProgressV4.completed();heal();}else sfx("v3se_311");v4ComicTileV3(v4ComicCorrectV3?"V3PlaceOK":"V3PlaceNG",v4ComicBankV3.at("placementClips").at(v4ComicCorrectV3?"ok":"ng").at("frames").at(0),true);}return true;
 }
 if(v4ComicReview){
  if(enterPressed||v4ComicClockV3>=1.2f){
   v4ComicReplay=true;
   v4ComicReplayAt=0;
   v4ComicReplayTime=0;
   comicProgressV4.responded.clear();
   music("bgm_trial_climax_replay");
   sfx("v3se_007");
   v4ComicReplayDrawV3();
  }
  return true;
 }
 float unlockSeconds=v4ComicBankV3.at("clipDurations").at("unlock").value("secondsAt60",64.f/60.f);if(comicProgressV4.stockTickUnlock(delta,unlockSeconds)>=0)v4ComicHighlight();if(comicProgressV4.stockUnlockIndex>=0){v4ComicUnlockDrawV3();return true;}
 bool zoom=Input::IsKeyDown("Space")&&comicProgressV4.stockReady(optHover);if(zoom!=v4ComicZoom){v4ComicZoom=zoom;for(auto id:{"ZoomShade","ZoomImage","ZoomCaption"})UI::SetVisible(this,"comicv4",id,zoom);}if(zoom)return true;
 bool expanded=Input::IsKeyDown("f");if(expanded!=v4ComicExpanded){v4ComicExpanded=expanded;v4ComicStockAnimationV4=Data::Get(v4ComicBankV3.at("stockSequenceFiles").at(expanded?"open":"close").get<std::string>());v4ComicStockAnimationTimeV4=0;sfx(expanded?"v3se_010":"v3se_011");v4ComicDraw();return true;}
 int spread=v4ComicSpread,last=comicv4ui::count(stage)-1;if(pressed("q")||(click&&aimX>=470&&aimX<535&&aimY>=75&&aimY<140))v4ComicSpread=std::max(0,spread-1);if(pressed("e")||(click&&aimX>=692&&aimX<757&&aimY>=75&&aimY<140))v4ComicSpread=std::min(last,spread+1);if(click&&aimY<180&&aimX>=327)for(int p=0;p<=last;p++)if(comicv4ui::hitRect(comicv4ui::pageThumb(p,v4ComicSpread),-6,aimX,aimY))v4ComicSpread=p;if(spread!=v4ComicSpread){v4ComicPageTurnV4=0;v4ComicPageDirectionV4=v4ComicSpread>spread?1:-1;sfx("v3se_007");v4ComicDraw();return true;}
 int old=optHover,count=int(v4ComicStock.size()),pageSize=comicv4ui::stockPageSize;if(pressed("a")||pressed("ArrowLeft"))optHover=(optHover+count-1)%count;if(pressed("d")||pressed("ArrowRight"))optHover=(optHover+1)%count;if(pressed("w")||pressed("ArrowUp"))optHover=(optHover+count-2)%count;if(pressed("s")||pressed("ArrowDown"))optHover=(optHover+2)%count;
 if(count>pageSize){
  if(pressed("z"))optHover=std::max(0,optHover-pageSize);
  if(pressed("x"))optHover=std::min(count-1,optHover+pageSize);
 }
 if(click)for(int i=0;i<int(optRects.size());i++)if(comicv4ui::hitRect(optRects[i],0,aimX,aimY)){optHover=v4ComicStockPage*pageSize+i;if(old!=optHover)sfx("v3se_005");v4ComicHighlight();return true;}if(old!=optHover){sfx("v3se_005");v4ComicHighlight();}
 int cursor=-1;for(int i:comicv4ui::slots(stage,v4ComicSpread))if(comicv4ui::hit(stage,i,aimX,aimY)){cursor=i;break;}if(cursor>=0&&cursor!=v4ComicCursor){v4ComicCursor=cursor;v4ComicDraw();}if(enterPressed||(click&&cursor>=0))v4ComicPick(optHover);return true;
}
void Yumeno::v4ComicPick(int index){
 if(v4ComicPlacing>=0||v4ComicFeedbackV3>=0||v4ComicStockAnimationTimeV4>=0||v4ComicPageTurnV4<1||v4ComicReview||index<0||index>=int(v4ComicStock.size())||v4ComicCursor<0||v4ComicSpread!=comicv4ui::page(stage,v4ComicCursor)||comicProgressV4.filled(v4ComicCursor))return;if(!comicProgressV4.stockCanConfirm(index,v4ComicExpanded)){sfx("v3se_004");return;}
 sfx("v3se_001");v4ComicPlacing=index;v4ComicPlaceSlot=v4ComicCursor;v4ComicPlaceTicks=0;UI::SetTexture(this,"comicv4","PlaceImage",v4ComicStock[index].at("image").get<std::string>());auto r=v4ComicBankV3.at("selectedOwnImage").at(0).at("rect").get<std::array<float,4>>();UI::SetPosition(this,"comicv4","PlaceImage",{r[0],r[1]});UI::SetSize(this,"comicv4","PlaceImage",{r[2],r[3]});UI::SetRotation(this,"comicv4","PlaceImage",0);UI::SetVisible(this,"comicv4","PlaceImage",true);
}
hb::Json Yumeno::v4ComicAuto()const{
 if(v4ComicIntroTime>=0||v4ComicReplay||v4ComicPlacing>=0||v4ComicFeedbackV3>=0||v4ComicStockAnimationTimeV4>=0||v4ComicPageTurnV4<1||comicProgressV4.stockUnlockIndex>=0)return {{"kind","wait"}};if(v4ComicReview)return {{"kind","key"},{"key","Enter"}};int choice=-1;for(int i=0;i<int(v4ComicStock.size());i++)if(comicProgressV4.stockOrigins[i]>=0&&(comicProgressV4.stockReady(i)||comicProgressV4.stockPendingUnlock(i))){choice=i;break;}if(choice<0)return {{"kind","wait"}};if(optHover!=choice)return {{"kind","key"},{"key","d"}};if(!comicProgressV4.stockReady(choice))return {{"kind","wait"}};int target=v4ComicStock[choice]["originSlot"],page=comicv4ui::page(stage,target);if(v4ComicSpread!=page)return {{"kind","key"},{"key",v4ComicSpread<page?"e":"q"}};auto r=comicv4ui::rect(stage,target);return {{"kind","click"},{"x",r[0]+r[2]/2},{"y",r[1]+r[3]/2}};
}
