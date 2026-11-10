#include "../Game/Source/MineLayoutV4.hpp"
#include "../Game/Source/TaskGraphV4.hpp"
#include "../Game/Source/TrialRulesV4.hpp"
#include "../Game/Source/DifficultyV4.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
std::string hb::Data::GetText(const std::string& path){std::ifstream file("Game/"+path);if(!file)throw std::runtime_error("Missing generated data: "+path);return {std::istreambuf_iterator<char>(file),std::istreambuf_iterator<char>()};}
int main(){using J=hb::Json;
 for(int action=0;action<3;action++)for(int logic=0;logic<3;logic++)for(int chapter=1;chapter<=6;chapter++){
  int width=difficultyv4::mineWidth(action),colors=difficultyv4::mineColors(chapter,logic);assert(width==18+action*2&&colors==(chapter>=4&&logic>0?4:3));
  for(int seed=0;seed<97;seed++){auto board=trialv4::mineBoard(width,11,colors,seed);assert(board.size()==std::size_t(width*11));for(int c:board)assert(c>=0&&c<colors);
   assert(board==trialv4::mineBoard(width,11,colors,seed));
   int joined=0;for(int k=0;k<width*11;k++){if(k%width&&board[k]==board[k-1])++joined;if(k>=width&&board[k]==board[k-width])++joined;}assert(joined>10);
   auto next=trialv4::mineBoard(width,11,colors,seed+1);int same=0;for(int k=0;k<width*11;k++)same+=board[k]==next[k];assert(same<int(board.size()*0.75));
   for(int by=0;by<11;by+=colors)for(int bx=0;bx<width;bx+=colors){std::vector<int> count(colors);for(int y=by;y<std::min(by+colors,11);y++)for(int x=bx;x<std::min(bx+colors,width);x++){++count[board[y*width+x]];if(x>=bx+2)assert(!(board[y*width+x]==board[y*width+x-1]&&board[y*width+x]==board[y*width+x-2]));if(y>=by+2)assert(!(board[y*width+x]==board[(y-1)*width+x]&&board[y*width+x]==board[(y-2)*width+x]));}assert(*std::max_element(count.begin(),count.end())-*std::min_element(count.begin(),count.end())<=1);}
  }
 }
 J thin=J::array({J::array({.01,.01}),J::array({.99,.99}),J::array({.99,.9901}),J::array({.01,.0101})});
 for(int width:{18,20,22}){auto cells=taskv4::mineFootprint(thin,width,11);assert(!cells.empty());for(int n:cells)assert(n>=0&&n<width*11);assert(std::find(cells.begin(),cells.end(),5*width+width/2)!=cells.end());}
 int stages=0,regions=0;
 for(int shard=0;shard<64;shard++){
  const J& page=storyv4::bucketData("Assets/Data/v4_story/native_tasks/",shard);
  for(const auto& bundle:page.at("tasks")){const auto& stage=bundle.at("stage");if(stage.value("kind",std::string())!="mindmine")continue;++stages;
   for(const auto& region:stage.at("regions")){++regions;for(int width:{18,20,22}){auto footprint=taskv4::mineFootprint(region.at("polygon"),width,11);assert(!footprint.empty());for(int n:footprint){assert(n>=0&&n<width*11);int row=n/width,col=n%width;minelayoutv4::Board layout(width);float x=layout.left+(col+.5f)*layout.cell,y=layout.top+(row+.5f)*layout.cell;assert(int((x-layout.left)/layout.width*width)==col&&int((y-layout.top)/layout.height*11)==row);assert(std::abs(layout.width/width-layout.height/11)<.001f);}
    std::vector<int> board(width*11,0);trialv4::Mine mine;mine.reset(width,11,3,board);mine.setImages({{0,footprint,true,false,true}});assert(mine.submitImage(0,255)==trialv4::Result::None);for(int n:footprint)mine.cells[n]=-1;assert(mine.submitImage(0,255)==trialv4::Result::Complete);
   }}
  }
 }
 assert(stages>0&&regions>0);std::cout<<"mine layout PASS: "<<stages<<" actual stages / "<<regions<<" authored polygons x18/20/22, conservative thin-edge intersections, click-center mapping and real Mine reveal/judgment; no runtime player\n";
}
