#pragma once
#include "DialogueTextV4.hpp"
#include <string>
#include <vector>
namespace documentv4 {
struct State {
 std::string title,image;std::vector<dialoguetext::Page> pages;int page=0;
 template<class Width>void prepare(const std::string& heading,const std::string& text,const std::string& picture,Width width){
  title=heading;image=picture;page=0;pages=text.empty()&&!image.empty()?std::vector<dialoguetext::Page>{}:dialoguetext::pages(text,782.f,8,width);
 }
 int count()const{return int(pages.size())+(!image.empty()?1:0);}
 bool imagePage()const{return !image.empty()&&page==0;}
 const std::string& text()const{static const std::string empty;int at=page-(!image.empty()?1:0);return at>=0&&at<int(pages.size())?pages[at].text:empty;}
 bool final()const{return page+1>=count();}
 bool next(){if(final())return false;++page;return true;}
 bool back(){if(page<=0)return false;--page;return true;}
};
}
