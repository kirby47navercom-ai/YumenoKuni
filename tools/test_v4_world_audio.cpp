#include "../Game/Source/PresentationV4.hpp"
#include <cassert>
#include <fstream>
#include <filesystem>
#include <iostream>
struct Play {std::string asset,handle,bus;float gain;};
static std::vector<Play> plays;static std::vector<std::string> stops;
static int uiShows=0;
std::string hb::Audio::Play(const std::string& asset,float gain,float,const std::string& bus){auto handle="own-test-"+std::to_string(plays.size());plays.push_back({asset,handle,bus,gain});return handle;}
void hb::Audio::Stop(const std::string& handle){stops.push_back(handle);}
void hb::UI::Show(hb::Actor*,const std::string&,const std::string&){++uiShows;}
void hb::UI::SetVisible(hb::Actor*,const std::string&,const std::string&,bool){}
void hb::UI::SetTexture(hb::Actor*,const std::string&,const std::string&,const std::string&){}
void hb::UI::SetOpacity(hb::Actor*,const std::string&,const std::string&,float){}
void hb::UI::SetPosition(hb::Actor*,const std::string&,const std::string&,const hb::Vec2&){}
void hb::UI::SetSize(hb::Actor*,const std::string&,const std::string&,const hb::Vec2&){}
int main(){
 using hb::Json;Json contract,art,world;std::ifstream("Game/Assets/Data/presentation/v4.json")>>contract;std::ifstream("Game/Assets/Data/art.json")>>art;std::ifstream("art/space_v4/runtime_v1/world.json")>>world;
 int checkedAssets=0;for(const auto& [cue,asset]:art["audio"].items())if(cue.rfind("v4_amb_",0)==0||cue.rfind("v4_footstep_",0)==0){Json audio;std::ifstream("Game/"+asset.get<std::string>())>>audio;assert(audio.at("loop").get<bool>()==(cue.rfind("v4_amb_",0)==0));assert(std::filesystem::is_regular_file("Game/"+audio.at("clip").get<std::string>()));++checkedAssets;}
 assert(checkedAssets>=8);int checkedFrames=0;for(const auto& frame:contract["sequences"]["scene_ink_uncover"]["frames"]){assert(std::filesystem::is_regular_file("Game/"+pv4::AssetTexture(frame.get<std::string>())));++checkedFrames;}assert(checkedFrames==16);
 pv4::State state;std::vector<std::string> music;pv4::Init(state,nullptr,contract,art,[&](const std::string& cue){music.push_back(cue);});
 assert(pv4::WorldAmbience(state,true,true));assert(state.ambientCue=="v4_amb_outside_wind"&&plays.back().gain==.2f);auto handle=state.ambientHandle;auto count=plays.size();for(int i=0;i<100;i++)assert(pv4::WorldAmbience(state,true,true));assert(plays.size()==count&&state.ambientHandle==handle&&stops.empty());
 // Pad/option pause leaves the world sound playing; it never replays an event.
 pv4::Tick(state,2,false);assert(plays.size()==count&&stops.empty()&&state.ambientHandle==handle);
 assert(pv4::WorldAmbience(state,true,false)&&state.ambientCue=="v4_amb_room_air"&&stops.back()==handle);handle=state.ambientHandle;
 assert(pv4::WorldAmbience(state,false,false)&&state.ambientHandle.empty()&&stops.back()==handle);count=stops.size();assert(pv4::WorldAmbience(state,false,true)&&stops.size()==count);
 assert(pv4::WorldAmbience(state,true,true));auto snapshot=pv4::Save(state,"bgm_investigation","");state.once.insert("test-once");snapshot=pv4::Save(state,"bgm_investigation","");handle=state.ambientHandle;
 pv4::Restore(state,snapshot);assert(state.ambientHandle.empty()&&stops.back()==handle&&state.once.count("test-once")&&music.back()=="bgm_investigation");assert(pv4::WorldAmbience(state,true,true)&&!state.ambientHandle.empty());
 handle=state.ambientHandle;count=plays.size();assert(pv4::Ambient(state,"v4_amb_outside_wind",.1f)&&plays.size()==count+1&&state.ambientGain==.1f&&stops.back()==handle);assert(pv4::Ambient(state,"",.2f)&&state.ambientHandle.empty());
 assert(!pv4::Ambient(state,"v4_evidence_acquired"));assert(state.ambientHandle.empty());assert(!pv4::Ambient(state,"v4_amb_room_air",NAN));
 int spaces=0,outdoors=0;
 for(const auto& [id,spec]:world["spaces"].items()){
  bool outdoor=spec.value("outdoor",false);assert(pv4::WorldAmbience(state,true,outdoor));assert(state.ambientCue==(outdoor?"v4_amb_outside_wind":"v4_amb_room_air"));spaces++;outdoors+=outdoor;
  auto surface=spec.at("footstep_surface").get<std::string>();for(int contact=0;contact<4;contact++)for(bool running:{false,true}){assert(pv4::Footstep(state,surface,contact,running));assert(plays.back().asset==art["audio"]["v4_footstep_"+surface+"_"+std::to_string(contact%2+1)]&&plays.back().gain==(running?.7f:.55f)&&plays.back().bus=="sfx");}
 }
 assert(spaces==46&&outdoors==10);count=plays.size();assert(!pv4::Footstep(state,"not-authored",0,false)&&plays.size()==count);
 // Music restore and one-shot once policy are untouched by derived room loops.
 assert(state.once.count("test-once")&&music.back()=="bgm_investigation");pv4::Clear(state);assert(state.ambientHandle.empty());
 pv4::State visual;pv4::Init(visual,reinterpret_cast<hb::Actor*>(1),contract,art,{});
 assert(!pv4::SceneReady(visual,"plaza")&&!pv4::Playing(visual,"scene_ink_uncover"));assert(pv4::SceneReady(visual,"hotel")&&pv4::Playing(visual,"scene_ink_uncover")&&visual.sequences[3].frame==0);
 pv4::Tick(visual,.5f);assert(visual.sequences[3].frame==8);auto elapsed=visual.sequences[3].elapsed;assert(!pv4::SceneReady(visual,"hotel")&&visual.sequences[3].elapsed==elapsed);pv4::Tick(visual,2,false);assert(visual.sequences[3].elapsed==elapsed);pv4::Tick(visual,.5f);assert(!pv4::Playing(visual,"scene_ink_uncover"));
 assert(pv4::SceneReady(visual,"plaza"));assert(!pv4::SceneReady(visual,"court",true)&&!pv4::Playing(visual,"scene_ink_uncover"));
 visual.reducedMotion=true;assert(!pv4::SceneReady(visual,"hotel")&&!pv4::Playing(visual,"scene_ink_uncover"));visual.reducedMotion=false;assert(!pv4::SceneReady(visual,"hotel"));assert(pv4::SceneReady(visual,"plaza"));visual.reducedMotion=true;pv4::Tick(visual,.01f);assert(!pv4::Playing(visual,"scene_ink_uncover"));
 pv4::Restore(visual,snapshot);assert(visual.sceneKey.empty()&&!pv4::SceneReady(visual,"plaza",true));
 int effectFrames=0;for(const auto* action:{"shot_miss","slash_hit","scrum_link"}){
  const auto& def=contract["actions"][action];auto sequence=def["sequence"].get<std::string>();for(const auto& frame:contract["sequences"][sequence]["frames"]){assert(std::filesystem::is_regular_file("Game/"+pv4::AssetTexture(frame.get<std::string>())));++effectFrames;}
  visual.reducedMotion=false;assert(pv4::Action(visual,action,100,210));auto& effect=visual.sequences[2];assert(effect.id==sequence&&effect.x==-100&&effect.y==10&&effect.w==400&&effect.h==400);assert(plays.back().gain==def["sfx"][0]["gain"].get<float>());pv4::Tick(visual,.1f);assert(effect.x==-100&&effect.y==10&&effect.centerX==100&&effect.centerY==210);pv4::Tick(visual,2);assert(!pv4::Playing(visual,sequence));
 }
 assert(effectFrames==24);count=plays.size();assert(!pv4::Action(visual,"slash_hit",NAN,210)&&plays.size()==count);assert(pv4::Action(visual,"slash_hit")&&visual.sequences[2].x==440&&visual.sequences[2].y==160);
 pv4::Tick(visual,.1f);assert(pv4::WorldAmbience(visual,true,false));handle=visual.ambientHandle;count=plays.size();int shows=uiShows;auto writes=visual.textureWrites;elapsed=visual.sequences[2].elapsed;visual.once.insert("keep-once");pv4::Rehost(visual);assert(uiShows==shows+1&&visual.textureWrites==writes+1&&visual.sequences[2].elapsed==elapsed&&visual.sequences[2].visible&&visual.sequences[2].x==440&&visual.sequences[2].y==160&&visual.once.count("keep-once")&&plays.size()==count&&visual.ambientHandle==handle);pv4::Clear(visual);
 for(const auto* action:{"climax_insert","climax_page"}){const auto& sound=contract["actions"][action]["sfx"][0];count=plays.size();assert(pv4::Action(visual,action)&&plays.size()==count+1);assert(plays.back().asset==art["audio"][sound["cue"].get<std::string>()]&&plays.back().gain==sound["gain"].get<float>()&&plays.back().bus==sound["bus"].get<std::string>());assert(!visual.sequences[2].active);}
 for(const auto* action:{"shot_miss","slash_hit","scrum_link","climax_insert","climax_page","coin_award"}){auto cue=contract["actions"][action]["sfx"][0]["cue"].get<std::string>();Json audio;std::ifstream("Game/"+art["audio"][cue].get<std::string>())>>audio;assert(!audio.at("loop").get<bool>()&&std::filesystem::is_regular_file("Game/"+audio.at("clip").get<std::string>()));}
 Json feedback={{"status","PASS"},{"impactSequences",3},{"frameAssets",effectFrames},{"positionHeldAcrossFrames",true},{"defaultCenterResets",true},{"nonFinitePositionRejectedBeforeSound",true},{"comicCueGainAndBus",true},{"rehostReappliesActiveUICaches",true},{"rehostKeepsTimelineAudioAndOnce",true},{"playerLaunch",false},{"nativePixelsAccepted",false}};std::ofstream("Game/Saved/trial-feedback-20261031.json")<<feedback.dump(2)<<"\n";
 Json report={{"status","PASS"},{"spaces",spaces},{"outdoorSpaces",outdoors},{"audioAssets",checkedAssets},{"uncoverFrames",checkedFrames},{"footstepGainAndAlternation",true},{"sameRoomNoRestart",true},{"modalKeepsLoop",true},{"courtTitleStopsLoop",true},{"loadRebindAfterTransientClear",true},{"sceneChangeOnly",true},{"transitionPauseAndReducedMotion",true},{"playerLaunch",false},{"audibleMixCertified",false}};std::ofstream("Game/Saved/world-audio-20261031.json")<<report.dump(2)<<"\n";std::cout<<report.dump()<<"\n";
}
