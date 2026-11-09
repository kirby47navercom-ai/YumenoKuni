#pragma once
#include "NonstopNoiseRowsV4.hpp"
namespace debate {
// User progression: White Noise starts with the fourth Chapter 1 Nonstop.
inline bool noiseEnabled(const std::string& task){return task!="T1-NS-A01"&&task!="T1-NS-A02"&&task!="T1-NS-A03";}

struct NoiseCue {float angle=-18,delay=.8f,span=3.1f;const char* host="";int slot=0,hits=1,minAction=0;float x=640,y=430;};
inline NoiseCue noiseCue(const std::string& id,const std::string&){
 const auto first=NOISE_BINDINGS,last=NOISE_BINDINGS+sizeof(NOISE_BINDINGS)/sizeof(*NOISE_BINDINGS);
 auto it=std::lower_bound(first,last,id,[](const NoiseBinding& row,const std::string& key){return key.compare(row.id)>0;});
 if(it!=last&&id==it->id)return {it->angle,it->delay,it->span,it->host,it->slot,it->hits,it->minAction,it->x,it->y};
 return {};
}
}
