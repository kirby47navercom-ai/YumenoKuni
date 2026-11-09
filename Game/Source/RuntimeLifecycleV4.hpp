// Screen resource ownership; story, rules and save state survive unloading.
void Yumeno::Init(){gputrialhudv4::reset();gpupanichudv4::reset();gpunoisehudv4::reset();UI::owners.clear();UI::applied.clear();scenesv4::reset();}
void Yumeno::Shutdown(){gputrialhudv4::reset();gpupanichudv4::reset();gpunoisehudv4::reset();UI::owners.clear();UI::applied.clear();scenesv4::reset();}
void Yumeno::prepareGameplay(){
 if(gameplayReady)return;
 if(!gameplayDataReady){
  story=Data::Get("Assets/Data/story.json");emotions=Data::Get("Assets/Data/emotion.json");rules=Data::Get("Assets/Data/rules.json");
  giftData=Data::Get("Assets/Data/gifts.json");kotodama=Data::Get("Assets/Data/kotodama.json");reactions=Data::Get("Assets/Data/reactions.json");hotspotData=Data::Get("Assets/Data/hotspots.json");skillData=Data::Get("Assets/Data/skills.json");padSystemInit();gameplayDataReady=true;
 }
 hudImage.clear();hudGauge.clear();levelUpImage.clear();noiseStyled=false;v4RenderedCg.clear();menuRenderStamp.clear();
 texts.clear();ftexts.clear();fvisible.clear();etexts.clear();evisible.clear();ptexts.clear();pvisible.clear();stexts.clear();svisible.clear();glyphCache.clear();glyphStyle.clear();glyphDisplay={};panicGlyphDisplay={};shownLine=shownHearts=shownHeartMax=shownNoise=shownStars=-1;
 UI::Show(this,"Assets/UI/Main.hbwidget.json",UI_ID);UI::SetVisible(this,UI_ID,"Title",false);
 if(scenesv4::explore.loaded)UI::Show(this,"Assets/UI/Explore.hbwidget.json","explore");UI::Show(this,"Assets/UI/Flow.hbwidget.json","flow");UI::Show(this,"Assets/UI/V4Story.hbwidget.json","v4story");
 pv4::Init(presentationV4,this,Data::Get("Assets/Data/presentation/v4.json"),art,[this](const std::string& spec){playCue(spec);});gameplayReady=true;
}
void Yumeno::releaseGameplay(){
 releaseTrialUi();
 if(!tugSe.empty())Audio::Stop(tugSe);tugSe.clear();tugSeOn=false;
 if(!chargeSe.empty())Audio::Stop(chargeSe);chargeSe.clear();chargeSeOn=false;
 resultPlanes.clear();debateFxValues.clear();seatTexture.clear();seatShownTexture.clear();scrumSideSeats.clear();actors.clear();
 for(auto id:{"main","explore","flow","v4story","pad"})UI::Remove(this,id);
 if(presentationV4.initialized){pv4::Clear(presentationV4);hb::UI::Remove(this,pv4::Widget);presentationV4.initialized=false;}
 gameplayReady=false;
}

