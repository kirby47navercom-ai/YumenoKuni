#include "../Game/Source/StoryGraphV4.hpp"
#include <fstream>
#include <iostream>
#include <cassert>
using storyv4::J;
std::string hb::Data::GetText(const std::string& path){std::ifstream file(path);if(!file)throw std::runtime_error("Missing fixture file: "+path);return std::string(std::istreambuf_iterator<char>(file),std::istreambuf_iterator<char>());}
int main(){
 std::ifstream input("data/v4_story/chapters/P.json");J graph;input>>graph;assert(storyv4::valid(graph));
 int paths=0;
 for(int a=0;a<2;a++)for(int b=0;b<2;b++){
  storyv4::State s;s.graph=graph;s.active=true;assert(storyv4::jump(s,graph["entry"].get<std::string>()));
  int menus=0,documents=0,steps=0;std::string last;
  while(++steps<2000){
   auto n=s.current();auto type=n.value("type","");
   if(type=="end")break;
   if(type=="menu"){assert(storyv4::choose(s,menus++==0?a:b));}
   else if(type=="branch"||type=="call"||type=="return")assert(storyv4::route(s));
   else {assert(type=="say"||type=="stage"||type=="document");documents+=type=="document";assert(storyv4::jump(s,n.value("next","")));}
   auto serialized=storyv4::save(s);storyv4::State restored;assert(storyv4::restore(restored,graph,serialized));
   assert(restored.node==s.node&&restored.flags==s.flags&&restored.stack.size()==s.stack.size()&&restored.generation==s.generation);
  }
  assert(steps<2000&&menus==2&&documents==2);assert(s.flags["P-C01"]==(a==0?"A":"B"));assert(s.flags["P-C02"]==(b==0?"A":"B"));paths++;
 }
 storyv4::State s;s.graph=graph;storyv4::jump(s,graph["entry"].get<std::string>());
 auto saved=storyv4::save(s);auto corrupt=saved;corrupt["node"]="unwritten";assert(!storyv4::restore(s,graph,corrupt));
 assert(storyv4::eligible(s,J{{"requires",{{"fte:first",false}}}}));
 assert(!storyv4::eligible(s,J{{"requires",{{"fte:first",true}}}}));
 s.flags["fte:first"]=true;assert(storyv4::eligible(s,J{{"requires",{{"fte:first",true}}}}));
 corrupt=saved;corrupt["contentVersion"]="legacy";assert(!storyv4::restore(s,graph,corrupt));
 corrupt=saved;corrupt["stack"]=J::array({{{"returnTo","unwritten"}}});assert(!storyv4::restore(s,graph,corrupt));
 auto broken=graph;broken["nodes"][broken["entry"].get<std::string>()]["next"]="unwritten";assert(!storyv4::valid(broken));
 std::cout<<"PASS: "<<paths<<" authored prologue branches; native save/restore every step; damaged routes and saves rejected\n";
}
