#include "../Game/Source/StoryGraphV4.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
#include <tuple>
static std::vector<std::string> paths;
std::string hb::Data::GetText(const std::string& path){
 paths.push_back(path);std::ifstream file("Game/"+path);if(!file)throw std::runtime_error("Missing generated data: "+path);
 return {std::istreambuf_iterator<char>(file),std::istreambuf_iterator<char>()};
}
int main(){
 int totals[4]{};int family=0;
 for(const auto& spec:std::vector<std::tuple<std::string,int,std::string>>{{"nodes",128,"nodes"},{"native_tasks",64,"tasks"},{"gallery_map",128,"nodes"},{"gallery_records",64,"records"}}){
  const auto& [name,count,key]=spec;std::set<std::string> ids;auto prefix="Assets/Data/v4_story/"+name+"/";
  for(int index=0;index<count;index++){
   const auto& page=storyv4::bucketData(prefix,index);
   for(const auto& [id,value]:page.at(key).items()){assert(storyv4::bucket(id,count)==unsigned(index)&&ids.insert(id).second);(void)value;}
   auto reads=paths.size();assert(&page==&storyv4::bucketData(prefix,index)&&reads==paths.size());
  }totals[family++]=int(ids.size());
 }
 assert(totals[0]==51548&&totals[1]==219&&totals[2]==11624&&totals[3]==299);assert(paths.size()==172&&std::set<std::string>(paths.begin(),paths.end()).size()==172);
 std::ofstream("Game/Saved/data-query-packed-paths.json")<<hb::Json(paths).dump(2)<<"\n";
 std::cout<<hb::Json{{"status","PASS"},{"physicalQueries",paths.size()},{"nodes",totals[0]},{"tasks",totals[1]},{"galleryMappings",totals[2]},{"galleryRecords",totals[3]},{"logicalHashesPreserved",true},{"repeatReadCached",true},{"playerLaunch",false}}.dump()<<"\n";
}
