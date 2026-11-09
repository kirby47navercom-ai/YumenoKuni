#pragma once
#include <HBEngine/Game.hpp>
namespace dialogueportraitv4 {
// The visible listener never replaces the literal speaker, body or log owner.
inline std::string interlocutor(const hb::Json& n){
 auto kind=n.value("type","");
 if(kind!="menu"&&(kind!="say"||n.value("actor","")!="mio"||n.value("mono",false)))return "";
 return n.value("dialoguePortrait",std::string());
}
inline std::string poseKey(const hb::Json& n,const std::string& actor){
 const auto explicitPose=n.value("pose",std::string());
 if(explicitPose.rfind(actor+"_",0)==0)return explicitPose;
 const auto source=n.value("source",hb::Json::object());
 // Reviewed first-discovery exchange: the approved default master is a V-sign.
 // Keep that everyday pose out of the witnessed shock and grounding exchange.
 if(actor=="haruka"&&source.value("file",std::string()).rfind("11a3_",0)==0&&source.value("location",std::string())=="1-33"){
  const auto text=n.value("text",std::string());
  return text.find("나 봐")!=std::string::npos||text.find("그 말 하지 마")!=std::string::npos?"haruka_C12":"haruka_C04";
 }
 return actor;
}
}
