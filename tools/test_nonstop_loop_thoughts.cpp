#include "../Game/Source/NonstopLoopHintsV4.hpp"
#include "../Game/Source/DialogueTextV4.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
#include <map>
int main(int argc,char** argv){
 assert(argc==3);const float bodyWidth=std::stof(argv[2]);std::ifstream input(argv[1]);std::map<std::string,float> widths;
 std::string hex;float value;while(input>>hex>>value){std::string glyph;for(size_t i=0;i<hex.size();i+=2)glyph+=char(std::stoi(hex.substr(i,2),nullptr,16));widths[glyph]=value;}
 int count=0,sentences=0,failed=0;
 for(const auto& row:nonstopv4::HINTS){
  ++count;const auto parts=nonstopv4::thoughts(row.task);assert(parts.size()>=2);
  for(const auto& part:parts){++sentences;auto pages=dialoguetext::pages(part,bodyWidth-8,2,[&](const std::string& glyph){auto it=widths.find(glyph);return (it==widths.end()?26.66667f:it->second)*30/26.6666667f;});
   if(pages.size()!=1){std::cerr<<row.task<<": sentence spills into "<<pages.size()<<" pages\n";++failed;}
  }
 }
 assert(count==71);if(failed)return 1;
 std::cout<<count<<" round monologues / "<<sentences<<" thought sentences: native pagination fits, no orphan page PASS\n";
}
