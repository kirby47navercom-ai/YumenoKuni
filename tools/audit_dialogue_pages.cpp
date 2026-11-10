#include <nlohmann/json.hpp>
#include <fstream>
#include <iostream>
#include <map>
#include <cassert>
#include "../Game/Source/DialogueTextV4.hpp"
using J=nlohmann::json;
static J read(const std::string& path){std::ifstream f(path);assert(f);J out;f>>out;return out;}
int main(int argc,char** argv){
 assert(argc==3||argc==4);const bool legacy=argc==4&&std::string(argv[3])=="--legacy";auto rows=read(argv[1]);std::string dir=argv[2];
 auto layout=read(dir+"/dialogue_layout.json"),choice=read(dir+"/choice_layout.json");
 std::map<std::string,float> advances;for(const auto& bucket:choice["advances"])for(const auto& [key,v]:bucket.items())advances[key]=v.get<float>();
 J splits=J::array(),expectations=J::array();int pages=0,multi=0,bounds=0;const auto terminal=[](std::string s){while(!s.empty()&&s.back()==' ')s.pop_back();for(const auto* end:{".","?","!","…","。","？","！","\n","”","’","\"","」","』"})if(s.size()>=std::string(end).size()&&s.compare(s.size()-std::string(end).size(),std::string(end).size(),end)==0)return true;return false;};
 for(const auto& row:rows)for(bool trial:{false,true}){
  float size=trial?layout["trial"]["font"].get<float>():layout["font"].get<float>();
  float width=trial?layout["trial"]["body"][2].get<float>()-8:layout["ownWrap"]["width"].get<float>();int capacity=trial?2:3;
  const auto measure=[&](const std::string& g){auto it=advances.find(g);return (it==advances.end()?26.66667f:it->second)*size/26.6666667f;};
  const auto text=row["text"].get<std::string>();auto result=dialoguetext::pages(text,width,capacity,measure,!legacy);std::string joined;
  if(rows.size()<=10&&row.value("trial",false)==trial){J e=row;e["pages"]=J::array();for(const auto& p:result)e["pages"].push_back({{"raw",p.raw},{"text",p.text}});expectations.push_back(e);}
  pages+=int(result.size());if(result.size()>1)++multi;
  for(size_t i=0;i<result.size();++i){const auto& p=result[i];joined+=p.raw;float used=0;int n=1;for(const auto& g:dialoguetext::glyphs(p.text)){if(g=="\n"){assert(used<=width+.01);used=0;++n;}else used+=measure(g);}assert(used<=width+.01);if(!p.text.empty()&&p.text.back()=='\n')--n;assert(n<=capacity);++bounds;
   if(i+1<result.size()&&!terminal(p.raw))splits.push_back({{"trial",trial},{"id",row.value("id",std::string())},{"source",row["source"]},{"speaker",row["speaker"]},{"page",i},{"before",p.text},{"after",result[i+1].text},{"raw",text}});
  }assert(joined==text);
 }
 J out={{"ok",true},{"utterances",rows.size()},{"layoutsPerUtterance",2},{"pages",pages},{"multiPageCases",multi},{"nonterminalPageBoundaries",splits.size()},{"byteAndBoundsChecks",bounds},{"splits",splits},{"nativeRuntime",false},{"scope","Exact game C++ pagination over every archived unique utterance in both active ordinary and trial layouts. Both layouts are tested conservatively; not a claim every utterance occurs in both."}};
 std::ofstream f(dir+(legacy?"/page-audit-before.json":"/page-audit.json"));f<<out.dump(1)<<'\n';if(!expectations.empty()){std::ofstream e(dir+"/page-expectations.json");e<<expectations.dump(1)<<'\n';}out.erase("splits");std::cout<<out.dump()<<'\n';
}
