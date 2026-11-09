#pragma once
#include <HBEngine/Game.hpp>
#include <map>
#include <string>
namespace scenesv4 {
struct Segment {std::string instance;bool requested=false,loaded=false;};
inline Segment court,explore,titleScene;inline std::string courtMode="Court";
inline Segment* desired=nullptr;inline std::string desiredAsset;inline bool loadingShown=false,cover=false;
inline void release(Segment& s){s.requested=s.loaded=false;if(desired==&s){desired=nullptr;desiredAsset.clear();}}
inline bool ensure(Segment& target,Segment& previous,const std::string& asset,const std::string& instance){
 if(hb::Scene::FindActorById(instance+"Scene")){target.loaded=true;return true;}
 if(desired==&target)return false;release(previous);target.instance=instance;target.loaded=false;desired=&target;desiredAsset=asset;return false;
}
inline std::string trialMode(const std::string& kind){return kind=="nonstop"||kind=="lie"?"CourtDebate":kind=="panic"?"CourtPanic":kind=="anagram"?"CourtAnagram":kind=="showdown"?"CourtShowdown":kind=="armament"?"CourtArmament":"Court";}
inline bool courtReady(){return ensure(court,explore,courtMode=="CourtDebate"?"Assets/Scenes/DebateHud.hbscene.json":courtMode=="CourtPanic"?"Assets/Scenes/PanicHud.hbscene.json":courtMode=="CourtAnagram"?"Assets/Scenes/AnagramHud.hbscene.json":courtMode=="CourtShowdown"?"Assets/Scenes/ShowdownHud.hbscene.json":courtMode=="CourtArmament"?"Assets/Scenes/ArmamentHud.hbscene.json":"Assets/Scenes/Court.hbscene.json",courtMode);}
inline bool exploreReady(const std::string& level="Explore"){return ensure(explore,court,"Assets/Scenes/"+level+".hbscene.json",level);}
inline void reset(){courtMode="Court";court={};explore={};titleScene={};desired=nullptr;desiredAsset.clear();loadingShown=cover=false;}
inline bool waiting(){return desired!=nullptr;}
inline bool poll(){if(!desired)return true;if(!desired->requested){hb::Scene::Open(desiredAsset);desired->requested=true;return false;}if(!hb::Scene::FindActorById(desired->instance+"Scene"))return false;desired->loaded=true;desired->requested=false;desired=nullptr;desiredAsset.clear();return true;}
inline void title(){courtMode="Court";if(hb::Scene::FindActorById("TitleScene")){release(court);release(explore);return;}release(court);release(explore);ensure(titleScene,court,"Assets/Scenes/Title.hbscene.json","Title");}
inline hb::Actor* find(const std::string& id){if(auto* actor=hb::Scene::FindActorById(id))return actor;return id=="Camera"?hb::Scene::FindActorById("BootCamera"):nullptr;}
}
