#pragma once
#include <HBEngine/Game.hpp>
#include <string>

namespace campaignv4 {
inline constexpr const char* Revision = "rewrite-v5";
inline bool installed() {
 static const bool enabled = [] {
  try {
   return hb::Data::Get("Assets/Data/v4_story/revision/campaign.json")
     .value("campaignRevision", std::string()) == Revision;
  } catch (const std::exception&) { return false; }
 }();
 return enabled;
}
inline std::string chapterPath(const std::string& chapter, bool revised) {
 return std::string("Assets/Data/v4_story/") + (revised ? "revision/" : "") + "chapters/" + chapter + ".json";
}
inline const char* growthPath(bool revised) {
 return revised && installed() ? "Assets/Data/v4_story/revision/growth.json" : "Assets/Data/v4_story/growth.json";
}
inline std::string slot(const std::string& legacy) {
 return installed() ? "rewrite-v5-" + legacy : legacy;
}
inline bool canSave(const hb::Json& graph) {
 return graph.value("campaignRevision", std::string()) == (installed() ? Revision : "");
}
inline bool matches(const hb::Json& snapshot) {
 return snapshot.value("contentVersion", std::string()) == "v4" && canSave(snapshot);
}
} // namespace campaignv4
