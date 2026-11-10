#include "../Game/Source/DocumentV4.hpp"
#include <HBEngine/Game.hpp>
#include <cassert>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
int main(){
 using hb::Json;Json layout;std::ifstream("Game/Assets/Data/v4_story/choice_layout.json")>>layout;std::map<std::string,float> advances;
 for(const auto& bucket:layout["advances"])for(const auto& [g,value]:bucket.items())advances[g]=value.get<float>();
 auto width=[&](const std::string& g){auto it=advances.find(g);return (it==advances.end()?26.66667f:it->second)*24/26.6666667f;};
 documentv4::State document;document.prepare("empty","","",width);assert(document.count()==1&&document.final()&&!document.next()&&!document.back());document.prepare("picture","","existing.webp",width);assert(document.count()==1&&document.imagePage()&&document.text().empty());document.prepare("both","actual text","existing.webp",width);assert(document.count()==2&&document.imagePage()&&document.next()&&!document.imagePage()&&document.text()=="actual text"&&document.final()&&document.back()&&document.imagePage());
 int records=0,multipage=0,pages=0,longest=0;
 auto verify=[&](const Json& row){
  auto title=row.value("title",row.value("name",std::string()));std::string text=row.value("text",std::string());if(row.contains("rows")){text.clear();for(const auto& line:row["rows"]){if(!text.empty())text+="\n\n";text+=line.get<std::string>();}}
  auto image=row.value("image",std::string());document.prepare(title,text,image,width);assert(document.count()>0&&document.page==0);std::string original;for(const auto& p:document.pages){original+=p.raw;float used=0;int rows=1;for(const auto& g:dialoguetext::glyphs(p.text)){if(g=="\n"){assert(used<=782.001f);used=0;rows++;}else used+=width(g);}if(!p.text.empty()&&p.text.back()=='\n')rows--;assert(rows<=8&&used<=782.001f);}assert(original==text);
  for(int i=0;i<document.count();i++){assert(document.page==i);if(document.imagePage())assert(document.text().empty());bool advanced=document.next();assert(advanced==(i+1<document.count()));}assert(document.final()&&!document.next());while(document.back()){}assert(document.page==0);records++;multipage+=document.count()>1;pages+=document.count();longest=std::max(longest,int(dialoguetext::glyphs(text).size()));
 };
 for(const auto& file:std::filesystem::directory_iterator("Game/Assets/Data/v4_story/nodes"))if(file.path().extension()==".json"){
  Json page;std::ifstream(file.path())>>page;for(const auto& [id,node]:page["nodes"].items()){
   if(node.value("type",std::string())=="document"||node.value("type",std::string())=="evidence")verify(node);
   else if(node.value("showRecord",false))verify(node["publicRecords"][0]);
  }
 }
 assert(records>=170&&multipage>0&&longest>=884);Json report={{"status","PASS"},{"actualRecords",records},{"multipageRecords",multipage},{"pages",pages},{"longestCodepoints",longest},{"originalBytesPreserved",true},{"maximumTextRows",8},{"textWidth",782},{"imageAndTextSeparate",true},{"backForwardPreservesPage",true},{"playerLaunch",false},{"nativeVisualAccepted",false}};std::ofstream("Game/Saved/documents-20261031.json")<<report.dump(2)<<"\n";std::cout<<report.dump()<<"\n";
}
