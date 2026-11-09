#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <set>
#include <stdexcept>
#include <utility>
#include <vector>
namespace comicprogressv4 {
struct State {
 std::set<int> automatic,responded,placed;
 int totalSlots=0;
 std::vector<int> stockThresholds,stockOrigins;
 std::vector<std::vector<int>> stockPrerequisites;
 std::set<int> stockRevealed;
 int stockUnlockIndex=-1;
 float stockUnlockElapsed=0;
 void reset(int total,std::vector<int> eligible,int percent,std::uint32_t seed){
  automatic.clear();responded.clear();placed.clear();if(total<1||total>16||percent<0||percent>100)throw std::invalid_argument("comic prefill bounds");
  totalSlots=total;stockThresholds.clear();stockOrigins.clear();stockPrerequisites.clear();stockRevealed.clear();stockUnlockIndex=-1;stockUnlockElapsed=0;
  std::set<int> unique;for(int index:eligible)if(index<0||index>=total||!unique.insert(index).second)throw std::invalid_argument("comic prefill eligibility");
  // Own reproducible shuffle, not a copy of the original RNG. Only initially
  // eligible holes participate; cap at their actual count before indexing.
  for(int i=int(eligible.size())-1;i>0;i--){seed=seed*1664525u+1013904223u;std::swap(eligible[i],eligible[(seed>>8)%std::uint32_t(i+1)]);}
  int count=std::min(total*percent/100,int(eligible.size()));for(int i=0;i<count;i++)automatic.insert(eligible[i]);
 }
 bool filled(int index,int completedPrefix=0)const{return index<completedPrefix||automatic.count(index)||placed.count(index);}
 bool place(int index,int total){if(index<0||index>=total||filled(index))return false;placed.insert(index);return true;}
 int completed()const{return int(automatic.size()+placed.size());}
 int next(int total)const{for(int i=0;i<total;i++)if(!filled(i))return i;return -1;}
 bool consumeResponse(int index){return automatic.count(index)&&responded.insert(index).second;}
 // Original 390b20/3909a0 gate each stable candidate ID by solved-hole count.
 // The caller supplies authored thresholds; this helper invents no batches.
 void configureStock(std::vector<int> thresholds,std::vector<int> origins={}){
  if(totalSlots<1||int(thresholds.size())!=totalSlots)throw std::invalid_argument("comic stock must have one correct piece per hole");
  if(origins.empty())for(int i=0;i<totalSlots;i++)origins.push_back(i);
  if(origins.size()!=thresholds.size())throw std::invalid_argument("comic stock origin bounds");
  std::set<int> unique;std::vector<int> remaining;
  for(int i=0;i<totalSlots;i++){
   if(origins[i]<0||origins[i]>=totalSlots||!unique.insert(origins[i]).second||thresholds[i]<0||thresholds[i]>=totalSlots)throw std::invalid_argument("comic stock gate bounds");
   if(automatic.count(origins[i])&&thresholds[i]!=0)throw std::invalid_argument("comic automatic piece was initially locked");
   if(!filled(origins[i]))remaining.push_back(thresholds[i]);
  }
  std::sort(remaining.begin(),remaining.end());
  for(int i=0;i<int(remaining.size());i++)if(remaining[i]>completed()+i)throw std::invalid_argument("comic stock gates cannot progress");
  stockThresholds=std::move(thresholds);stockOrigins=std::move(origins);stockPrerequisites.clear();stockRevealed.clear();stockUnlockIndex=-1;stockUnlockElapsed=0;
  for(int i=0;i<totalSlots;i++)if(stockThresholds[i]==0)stockRevealed.insert(i);
 }
 // Story-specific gates name the exact panels that establish the later cut.
 // An origin of -1 denotes a distractor, which never consumes a hole.
 void configureStoryStock(std::vector<std::vector<int>> prerequisites,std::vector<int> origins){
  if(totalSlots<1||origins.size()!=prerequisites.size()||origins.size()>24)throw std::invalid_argument("comic story stock bounds");
  std::set<int> covered;
  for(int i=0;i<int(origins.size());i++){
   const int origin=origins[i];
   if(origin< -1||origin>=totalSlots||(origin>=0&&!covered.insert(origin).second))throw std::invalid_argument("comic story stock origin");
   std::set<int> unique;
   for(int hole:prerequisites[i])if(hole<0||hole>=totalSlots||hole==origin||!unique.insert(hole).second)throw std::invalid_argument("comic story prerequisite");
   if(automatic.count(origin)&&!prerequisites[i].empty())throw std::invalid_argument("comic automatic piece was initially locked");
  }
  if(int(covered.size())!=totalSlots)throw std::invalid_argument("comic story stock missing answer");
  std::set<int> reachable;
  for(int pass=0;pass<totalSlots;pass++)for(int i=0;i<int(origins.size());i++)
   if(origins[i]>=0&&std::all_of(prerequisites[i].begin(),prerequisites[i].end(),[&](int hole){return reachable.count(hole)>0;}))reachable.insert(origins[i]);
  if(int(reachable.size())!=totalSlots)throw std::invalid_argument("comic story stock gates cannot progress");
  stockThresholds.clear();stockOrigins=std::move(origins);stockPrerequisites=std::move(prerequisites);
  stockRevealed.clear();stockUnlockIndex=-1;stockUnlockElapsed=0;
  for(int i=0;i<int(stockOrigins.size());i++)if(stockPrerequisites[i].empty())stockRevealed.insert(i);
 }
 bool stockValid(int index)const{return index>=0&&index<int(stockOrigins.size());}
 bool stockUsed(int index)const{return stockValid(index)&&stockOrigins[index]>=0&&filled(stockOrigins[index]);}
 int stockRemaining(int index)const{
  if(!stockValid(index))return -1;
  if(stockPrerequisites.empty())return std::max(0,stockThresholds[index]-completed());
  const auto& holes=stockPrerequisites[index];return int(std::count_if(holes.begin(),holes.end(),[&](int hole){return !filled(hole);}));
 }
 bool stockReady(int index)const{return stockValid(index)&&!stockUsed(index)&&stockRemaining(index)==0&&stockRevealed.count(index);}
 bool stockPendingUnlock(int index)const{return stockValid(index)&&!stockUsed(index)&&stockRemaining(index)==0&&!stockRevealed.count(index)&&stockUnlockIndex!=index;}
 bool stockCanConfirm(int index,bool expanded=false)const{return !expanded&&stockUnlockIndex<0&&stockReady(index);}
 bool stockBeginUnlock(int index){
  if(stockUnlockIndex>=0||!stockPendingUnlock(index))return false;
  stockUnlockIndex=index;stockUnlockElapsed=0;return true;
 }
 // Return the just-revealed candidate once. UI supplies the source clip length;
 // all confirmation is blocked until that selected candidate's clip finishes.
 int stockTickUnlock(float delta,float duration){
  if(!std::isfinite(delta)||!std::isfinite(duration)||delta<0||duration<0)throw std::invalid_argument("comic stock unlock time");
  if(stockUnlockIndex<0)return -1;
  if(stockUsed(stockUnlockIndex)){stockUnlockIndex=-1;stockUnlockElapsed=0;return -1;}
  stockUnlockElapsed+=delta;if(stockUnlockElapsed<duration)return -1;
  int opened=stockUnlockIndex;stockRevealed.insert(opened);stockUnlockIndex=-1;stockUnlockElapsed=0;return opened;
 }
};
}
