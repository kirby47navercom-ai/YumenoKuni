#include "../Game/Source/DialogueTextV4.hpp"
#include <cassert>
#include <iostream>

int main(){
 const std::vector<std::string> samples{"", "한글 문장은 원문을 줄이거나 지우면 안 돼요. 긴 단어와 공백을 그대로 남겨야 해요.", "abcdefghijk long words  and  two spaces", "첫 줄\n둘째 줄\n\n넷째 줄\n",std::string(300,'W'),"A 🙂 B\tC 마지막"};
 int checks=0;auto width=[](const std::string& g){return g==" "||g=="\t"?4.f:g.size()>1?10.f:6.f;};
 for(bool sentenceAware:{false,true})for(float limit:{20.f,30.f,70.f,200.f})for(int rows:{1,2,3})for(const auto& sample:samples){
  const auto pages=dialoguetext::pages(sample,limit,rows,width,sentenceAware);assert(!pages.empty());std::string original;
  for(const auto& page:pages){original+=page.raw;float used=0;int lines=1;for(const auto& g:dialoguetext::glyphs(page.text)){if(g=="\n"){assert(used<=limit);used=0;++lines;}else used+=width(g);}assert(used<=limit);if(!page.text.empty()&&page.text.back()=='\n')--lines;assert(lines<=rows);++checks;}
  assert(original==sample);++checks;
 }
 const auto measure=[](const std::string&){return 1.f;};
 const auto sentence=dialoguetext::pages("첫 문장은 끝났어. 다음 문장은 중간에 자르면 안 돼.",12,2,measure,true);
 assert(sentence.size()==2);assert(sentence[0].raw=="첫 문장은 끝났어. ");assert(sentence[1].raw=="다음 문장은 중간에 자르면 안 돼.");
 const auto decimal=dialoguetext::pages("3.14와 2.5를 더했어. 이번 문장은 따로 읽어.",10,2,measure,true);
 assert(decimal[0].raw=="3.14와 2.5를 더했어. ");
 assert(!dialoguetext::sentenceEnd(dialoguetext::glyphs("그건…아니야"),2));
 assert(!dialoguetext::sentenceEnd(dialoguetext::glyphs("그건...아니야"),2));
 assert(!dialoguetext::sentenceEnd(dialoguetext::glyphs("그건...아니야"),4));
 assert(!dialoguetext::sentenceEnd(dialoguetext::glyphs("정말?!"),2));
 std::cout<<"{\"ok\":true,\"checks\":"<<checks<<",\"scope\":\"Pure own UTF8 wordwrap/pagination preserves every original byte and bounds rows/width; not native visual proof\"}\n";
}
