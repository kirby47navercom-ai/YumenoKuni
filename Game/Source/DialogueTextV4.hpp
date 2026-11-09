#pragma once
#include <algorithm>
#include <string>
#include <vector>

// Own long-manuscript pagination. Source native automatic pagination is unknown.
namespace dialoguetext {
struct Page {std::string raw,text;};
inline std::vector<std::string> glyphs(const std::string& text){
 std::vector<std::string> out;for(size_t i=0;i<text.size();){size_t end=i+1;while(end<text.size()&&(static_cast<unsigned char>(text[end])&0xc0)==0x80)++end;out.push_back(text.substr(i,end-i));i=end;}return out;
}
template<class Width> std::vector<Page> wrappedPages(const std::string& text,float limit,int rows,Width width){
 const auto chars=glyphs(text);std::vector<Page> out;Page page;int usedRows=0;
 for(size_t start=0;start<chars.size();){
  size_t end=start,space=start;float used=0;bool hard=false;
  while(end<chars.size()){
   if(chars[end]=="\n"){++end;hard=true;break;}
   float w=width(chars[end]);if(end>start&&used+w>limit){if(space>start)end=space;break;}
   used+=w;++end;if(chars[end-1]==" "||chars[end-1]=="\t")space=end;
  }
  std::string row;for(size_t i=start;i<end;i++)row+=chars[i];page.raw+=row;page.text+=row;start=end;
  if(++usedRows==rows){out.push_back(page);page={};usedRows=0;}
  else if(!hard&&start<chars.size())page.text+='\n';
 }
 if(!page.raw.empty()||out.empty())out.push_back(page);return out;
}
inline bool closing(const std::string& g){return g=="\""||g=="'"||g=="”"||g=="’"||g=="」"||g=="』"||g==")"||g=="）"||g=="]";}
inline bool sentenceEnd(const std::vector<std::string>& chars,size_t i){
 const auto& g=chars[i];if(g=="\n")return true;
 if(g!="."&&g!="?"&&g!="!"&&g!="。"&&g!="？"&&g!="！"&&g!="…")return false;
 if(g=="."&&i>0&&i+1<chars.size()&&chars[i-1]>="0"&&chars[i-1]<="9"&&chars[i+1]>="0"&&chars[i+1]<="9")return false;
 if(i+1<chars.size()&&(chars[i+1]=="."||chars[i+1]=="?"||chars[i+1]=="!"||chars[i+1]=="…"))return false;
 if(g=="."&&i>0&&chars[i-1]=="."&&i+1<chars.size()&&chars[i+1]!=" "&&chars[i+1]!="\n"&&!closing(chars[i+1]))return false;
 // A hesitation inside a sentence is not an instruction to turn the page.
 if(g=="…"&&i+1<chars.size()&&chars[i+1]!=" "&&chars[i+1]!="\n"&&!closing(chars[i+1]))return false;
 return true;
}
template<class Width> std::vector<Page> pages(const std::string& text,float limit,int rows,Width width,bool sentenceAware=false){
 if(!sentenceAware)return wrappedPages(text,limit,rows,width);
 std::vector<Page> out;std::string remaining=text;
 do{
  const auto wrapped=wrappedPages(remaining,limit,rows,width);
  if(wrapped.size()==1){out.push_back(wrapped.front());break;}
  const auto chars=glyphs(remaining);const size_t capacity=glyphs(wrapped.front().raw).size();size_t cut=0;
  for(size_t i=0;i<capacity;i++)if(sentenceEnd(chars,i)){
   size_t end=i+1;while(end<chars.size()&&closing(chars[end]))++end;
   while(end<chars.size()&&(chars[end]==" "||chars[end]=="\t"))++end;
   if(end<=capacity)cut=end;
  }
  // A single sentence can exceed the box. Prefer its authored clause break,
  // then the existing word boundary; never drop words or shrink the font.
  if(cut==0)for(size_t i=capacity/2;i<capacity;i++)if(chars[i]==","||chars[i]=="，"||chars[i]==";"||chars[i]=="；")cut=i+1;
  if(cut==0){out.push_back(wrapped.front());remaining.erase(0,wrapped.front().raw.size());continue;}
  std::string prefix;for(size_t i=0;i<cut;i++)prefix+=chars[i];
  const auto complete=wrappedPages(prefix,limit,rows,width);
  out.insert(out.end(),complete.begin(),complete.end());remaining.erase(0,prefix.size());
 }while(!remaining.empty());
 return out;
}
}
