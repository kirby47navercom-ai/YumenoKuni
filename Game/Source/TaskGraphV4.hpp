#pragma once
#include "StoryGraphV4.hpp"
#include <chrono>
namespace taskv4 {
using J=hb::Json;
struct Route {std::string target;J sets=J::object();};
inline Route success(const J& node,const J& bundle,const std::string& judgment){
 auto outcomes=node.value("outcomes",bundle.value("outcomes",J::object()));
 if(!outcomes.empty()){
  for(auto& [id,o]:outcomes.items())if(o.value("judgment","")==judgment)return {o.value("to",std::string()),o.value("sets",J::object())};
  throw std::runtime_error("Actual judgment has no authored outcome");
 }
 return {node.value("success",node.value("next",std::string())),J::object()};
}
inline J prepare(const J& bundle,const J& evidence){
 if(!bundle.value("ready",false)||!bundle.contains("stage"))throw std::runtime_error("Authored task still has unresolved bindings");
 const bool local=bundle.value("scopeOnlyEvidence",false);
 for(auto& id:bundle.value("requiresEvidence",J::array()))if(!local&&!evidence.contains(id.get<std::string>()))throw std::runtime_error("Required evidence has not been acquired: "+id.get<std::string>());
 J stage=bundle["stage"];
 if(stage.value("filterOwnedEvidence",false)){
  J options=J::array();
  for(auto& option:stage.value("options",J::array()))if(option.is_object()&&(evidence.contains(option.value("id",""))||(local&&std::find(bundle["requiresEvidence"].begin(),bundle["requiresEvidence"].end(),option["id"])!=bundle["requiresEvidence"].end())))options.push_back(option);
  stage["options"]=std::move(options);
 }
 return stage;
}
inline const J& finalArmamentQuestion(const J& stage,int phase){
 if(stage.contains("controllerQuestions"))return stage.at("controllerQuestions").at(phase);
 static const auto base=hb::Data::Get("Assets/Data/armament_final_questions.json");
 return base.at("questions").at(phase);
}
inline bool inside(const J& polygon,float x,float y){
 if(!polygon.is_array()||polygon.size()<3)return false;bool hit=false;
 for(std::size_t i=0,j=polygon.size()-1;i<polygon.size();j=i++){
  float ax=polygon[i][0],ay=polygon[i][1],bx=polygon[j][0],by=polygon[j][1];
  float cross=(x-ax)*(by-ay)-(y-ay)*(bx-ax);
  if(std::abs(cross)<.000001f&&x>=std::min(ax,bx)&&x<=std::max(ax,bx)&&y>=std::min(ay,by)&&y<=std::max(ay,by))return true;
  if((ay>y)!=(by>y)&&x<(bx-ax)*(y-ay)/(by-ay)+ax)hit=!hit;
 }return hit;
}
inline int region(const J& stage,float u,float v){
 auto regions=stage.value("regions",J::array());for(int i=0;i<int(regions.size());i++)if(inside(regions[i]["polygon"],u,v))return i;return -1;
}
inline const J& mineObjectMask(const J& object){
 static std::map<std::string,J> banks;auto path=object.at("maskAsset").get<std::string>();auto at=banks.find(path);if(at==banks.end())at=banks.emplace(path,hb::Data::Get(path)).first;
 const auto& bank=at->second;
 return bank.at(bank.contains("masks")?"masks":"objects").at(object.at("maskKey").get<std::string>());
}
inline std::pair<float,float> mineObjectPoint(const J& object,float x,float y){
 const auto& r=object.at("rect");float columns=object.value("boardColumns",20),angle=object.value("rotation",0.f)*.0174532925199433f,co=std::cos(angle),si=std::sin(angle);
 float dx=(x-.5f)*r[2].get<float>()*columns,dy=(y-.5f)*r[3].get<float>()*11;
 return {r[0].get<float>()+r[2].get<float>()*.5f+(dx*co-dy*si)/columns,r[1].get<float>()+r[3].get<float>()*.5f+(dx*si+dy*co)/11};
}
inline void minePlaceObjects(J& stage,int columns,std::uint32_t seed){
 auto& objects=stage.at("mineObjects");if(objects.empty()||objects.size()>10)throw std::runtime_error("Mine object count");
 struct Candidate{int x,y,angle,weight;std::vector<int> cells;};std::vector<std::vector<Candidate>> candidates(objects.size());
 for(std::size_t i=0;i<objects.size();i++){
  const auto& mask=mineObjectMask(objects[i]);if(!mask.contains("rotations"))throw std::runtime_error("Mine object needs eight alpha footprints");
  for(const auto& rotation:mask["rotations"])for(int y=0;y<11;y++)for(int x=0;x<columns;x++){
   Candidate c{x,y,rotation.at("angle"),rotation.at("weight"),{}};bool fits=true;
   for(const auto& cell:rotation.at("cells")){int gx=x+cell[0].get<int>(),gy=y+cell[1].get<int>();if(gx<0||gx>=columns||gy<0||gy>=11){fits=false;break;}c.cells.push_back(gy*columns+gx);}
   if(fits&&!c.cells.empty())candidates[i].push_back(std::move(c));
  }
 }
 std::vector<bool> occupied(columns*11,false);std::vector<Candidate> chosen(objects.size());std::uint32_t random=seed?seed:1;
 auto next=[&](){random^=random<<13;random^=random>>17;random^=random<<5;return random;};
 auto place=[&](auto&& self,std::size_t at)->bool{
  if(at==objects.size())return true;std::vector<std::size_t> available;
  for(std::size_t i=0;i<candidates[at].size();i++)if(std::none_of(candidates[at][i].cells.begin(),candidates[at][i].cells.end(),[&](int k){return occupied[k];}))available.push_back(i);
  while(!available.empty()){
   unsigned total=0;for(auto i:available)total+=candidates[at][i].weight;unsigned draw=next()%total;std::size_t selected=0;
   for(;selected+1<available.size();selected++){auto weight=candidates[at][available[selected]].weight;if(draw<unsigned(weight))break;draw-=weight;}
   const auto& c=candidates[at][available[selected]];for(int k:c.cells)occupied[k]=true;chosen[at]=c;if(self(self,at+1))return true;for(int k:c.cells)occupied[k]=false;available.erase(available.begin()+selected);
  }return false;
 };
 if(!place(place,0))throw std::runtime_error("No non-overlapping mine object placement");
 for(std::size_t i=0;i<objects.size();i++){
  auto& object=objects[i];const auto& mask=mineObjectMask(object);float size=object.at("sizeCells"),scale=size/std::max(mask.at("width").get<int>(),mask.at("height").get<int>()),w=mask.at("width").get<int>()*scale/columns,h=mask.at("height").get<int>()*scale/11;
  object["rect"]=J::array({(chosen[i].x+.5f)/columns-w/2,(chosen[i].y+.5f)/11-h/2,w,h});object["rotation"]=chosen[i].angle;object["boardColumns"]=columns;object["placedCells"]=chosen[i].cells;
 }
}
inline bool mineObjectOpaque(const J& object,float u,float v){
 const auto& r=object.at("rect");float columns=object.value("boardColumns",20),angle=object.value("rotation",0.f)*.0174532925199433f,co=std::cos(angle),si=std::sin(angle);
 float dx=(u-r[0].get<float>()-r[2].get<float>()*.5f)*columns,dy=(v-r[1].get<float>()-r[3].get<float>()*.5f)*11;
 float x=(dx*co+dy*si)/(r[2].get<float>()*columns)+.5f,y=(-dx*si+dy*co)/(r[3].get<float>()*11)+.5f;
 if(x<0||x>=1||y<0||y>=1)return false;
 const auto& mask=mineObjectMask(object);int px=int(x*mask.at("width").get<int>()),py=int(y*mask.at("height").get<int>());
 const auto& row=mask.at("rows").at(py).get_ref<const std::string&>();
 for(std::size_t at=0;at<row.size();){auto colon=row.find(':',at),end=row.find(',',at);if(colon==std::string::npos)throw std::runtime_error("Mine alpha span");if(end==std::string::npos)end=row.size();int a=std::stoi(row.substr(at,colon-at)),b=std::stoi(row.substr(colon+1,end-colon-1));if(px>=a&&px<b)return true;at=end+1;}return false;
}
inline int mineObjectRegion(const J& stage,float u,float v){
 for(const auto& object:stage.at("mineObjects"))if(mineObjectOpaque(object,u,v))for(int i=0;i<int(stage.at("regions").size());i++)if(stage["regions"][i]["id"]==object["regionId"])return i;
 return -1;
}
inline std::pair<float,float> mineObjectAim(const J& object){
 const auto& mask=mineObjectMask(object);int w=mask.at("width").get<int>(),h=mask.at("height").get<int>();
 for(int offset=0;offset<h;offset++)for(int y:{h/2+offset,h/2-offset})if(y>=0&&y<h){const auto& row=mask.at("rows").at(y).get_ref<const std::string&>();if(row.empty())continue;auto colon=row.find(':'),end=row.find(',');if(end==std::string::npos)end=row.size();int a=std::stoi(row.substr(0,colon)),b=std::stoi(row.substr(colon+1,end-colon-1));return mineObjectPoint(object,(a+b)*.5f/w,(y+.5f)/h);}
 throw std::runtime_error("Mine object has no opaque input pixel");
}
inline std::vector<int> mineFootprint(const J& polygon,int width,int height){
 if(width<=0||height<=0||width>22||height>11||!polygon.is_array()||polygon.size()<3)throw std::runtime_error("Invalid mine footprint");
 std::vector<int> cells;
 for(int row=0;row<height;row++)for(int col=0;col<width;col++){
  float left=float(col)/width,right=float(col+1)/width,top=float(row)/height,bottom=float(row+1)/height;bool hit=false;
  for(float x:{left,right})for(float y:{top,bottom})if(inside(polygon,x,y))hit=true;
  for(std::size_t i=0;i<polygon.size();i++){
   float ax=polygon[i][0],ay=polygon[i][1],bx=polygon[(i+1)%polygon.size()][0],by=polygon[(i+1)%polygon.size()][1];
   if(ax>=left&&ax<=right&&ay>=top&&ay<=bottom)hit=true;
   if(std::abs(bx-ax)>.0000001f)for(float x:{left,right}){float t=(x-ax)/(bx-ax),y=ay+t*(by-ay);if(t>=0&&t<=1&&y>=top&&y<=bottom)hit=true;}
   if(std::abs(by-ay)>.0000001f)for(float y:{top,bottom}){float t=(y-ay)/(by-ay),x=ax+t*(bx-ax);if(t>=0&&t<=1&&x>=left&&x<=right)hit=true;}
  }
  if(hit)cells.push_back(row*width+col);
 }
 return cells;
}
} // namespace taskv4
