#include "../Game/Source/TaskGraphV4.hpp"
#include "../Game/Source/TrialRulesV4.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
std::string hb::Data::GetText(const std::string& path){std::ifstream file("Game/"+path);if(!file)throw std::runtime_error("Missing generated mask: "+path);return {std::istreambuf_iterator<char>(file),std::istreambuf_iterator<char>()};}
int verify(const hb::Json& stage){
 using J=hb::Json;
 assert(stage["mineObjects"].size()==stage["regions"].size());int checks=0;
 for(auto object:stage["mineObjects"]){
  auto uv=taskv4::mineObjectAim(object);assert(taskv4::mineObjectOpaque(object,uv.first,uv.second));++checks;
  auto& r=object["rect"];assert(!taskv4::mineObjectOpaque(object,r[0].get<float>(),r[1].get<float>()));assert(!taskv4::mineObjectOpaque(object,-1,-1));checks+=2;
  const auto& mask=taskv4::mineObjectMask(object);int w=mask["width"],h=mask["height"];
  for(int width:{18,20,22}){
   object["rect"]=object["rectByWidth"][std::to_string(width)];
   const auto cells=object["cellsByWidth"][std::to_string(width)].get<std::vector<int>>();assert(!cells.empty());std::set<int> occupied(cells.begin(),cells.end());
   for(int y=0;y<h;y+=7)for(int x=0;x<w;x+=7){float u=r[0].get<float>()+(x+.5f)/w*r[2].get<float>(),v=r[1].get<float>()+(y+.5f)/h*r[3].get<float>();if(taskv4::mineObjectOpaque(object,u,v)){assert(occupied.count(int(v*11)*width+int(u*width)));++checks;}}
   trialv4::Mine mine;mine.reset(width,11,3,trialv4::mineBoard(width,11,3,13));mine.setImages({{0,cells,true,false,true}});assert(mine.submitImage(0,255)==trialv4::Result::None);for(int cell:cells)mine.cells[cell]=-1;assert(mine.submitImage(0,127)==trialv4::Result::None);assert(mine.submitImage(0,128)==trialv4::Result::Complete);checks+=3;
  }
 }
 std::set<int> angles;
 for(int columns:{18,20,22})for(int seed=1;seed<=20;seed++){
  auto placed=stage;taskv4::minePlaceObjects(placed,columns,seed);auto replay=stage;taskv4::minePlaceObjects(replay,columns,seed);assert(placed==replay);std::set<int> occupied;
  for(const auto& object:placed["mineObjects"]){
   angles.insert(object.at("rotation").get<int>());const auto& mask=taskv4::mineObjectMask(object);for(int i=0;i<8;i++){assert(mask["rotations"][i]["angle"]==(i-4)*45);assert(mask["rotations"][i]["weight"]==(i%2?2:1));}
   std::set<int> footprint;for(int cell:object.at("placedCells").get<std::vector<int>>()){assert(cell>=0&&cell<columns*11);assert(occupied.insert(cell).second);footprint.insert(cell);checks++;}
   auto aim=taskv4::mineObjectAim(object);assert(taskv4::mineObjectOpaque(object,aim.first,aim.second));
   int w=mask["width"],h=mask["height"];
   for(int y=0;y<h;y+=13)for(int x=0;x<w;x+=13){auto uv=taskv4::mineObjectPoint(object,(x+.5f)/w,(y+.5f)/h);if(!taskv4::mineObjectOpaque(object,uv.first,uv.second))continue;assert(uv.first>=0&&uv.first<1&&uv.second>=0&&uv.second<1);assert(footprint.count(int(uv.second*11)*columns+int(uv.first*columns)));++checks;}
  }
 }
 assert(angles.size()==8);
 return checks;
}
int main(){
 int tasks=0,checks=0;
 const std::string bank="art/v4_production/mine_objects_20261104/";
 hb::Json registered;std::ifstream(bank+"banks.json")>>registered;std::set<std::string> expected;
 for(const auto& entry:registered){hb::Json selection;std::ifstream(bank+entry.at("selection").get<std::string>())>>selection;assert(expected.insert(selection.at("taskId").get<std::string>()).second);}
 for(int i=0;i<32;i++){hb::Json pack;std::ifstream("Game/Assets/Data/v4_story/native_tasks/pack_"+std::to_string(i)+".json")>>pack;for(const auto& bucket:pack["buckets"])for(const auto& task:bucket["tasks"])if(task["stage"].contains("mineObjects")){assert(expected.erase(task["stage"].at("id").get<std::string>())==1);checks+=verify(task["stage"]);++tasks;}}
 assert(expected.empty());assert(tasks==int(registered.size()));
 std::cout<<"mine objects PASS: "<<checks<<" checks across "<<tasks<<" tasks, 3 widths, all 8 weighted angles, alpha/footprint/rejection/non-overlap/full reveal; no runtime game\n";
}
