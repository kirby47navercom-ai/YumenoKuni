#include "../Game/Source/DialoguePortraitV4.hpp"
#include <cassert>
int main(){
 using J=hb::Json;using dialogueportraitv4::interlocutor;
 J n={{"type","say"},{"actor","mio"},{"speaker","미오"},{"text","뭐 써?"},{"mono",false},{"dialoguePortrait","rei"}};
 assert(interlocutor(n)=="rei");assert(n["actor"]=="mio"&&n["speaker"]=="미오");
 n["mono"]=true;assert(interlocutor(n).empty());n["mono"]=false;
 n["actor"]="rin";assert(interlocutor(n).empty());n["actor"]="mio";
 n["type"]="menu";assert(interlocutor(n)=="rei");n["type"]="stage";assert(interlocutor(n).empty());
 n.erase("dialoguePortrait");n["type"]="say";assert(interlocutor(n).empty());
 n["source"]={{"file","11a3_current.md"},{"location","1-33"}};n["text"]="기다려.";
 assert(dialogueportraitv4::poseKey(n,"haruka")=="haruka_C04");
 n["text"]="미오. 나 봐.";assert(dialogueportraitv4::poseKey(n,"haruka")=="haruka_C12");
 n["pose"]="haruka_C06";assert(dialogueportraitv4::poseKey(n,"haruka")=="haruka_C06");
 n.erase("pose");assert(dialogueportraitv4::poseKey(n,"rei")=="rei");
 n["source"]["location"]="1-32";assert(dialogueportraitv4::poseKey(n,"haruka")=="haruka");
}
