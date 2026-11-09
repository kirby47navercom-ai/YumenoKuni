#pragma once
// Project-owned presentation only. It never decides a story route or a hit.
#include <HBEngine/Game.hpp>
#include <array>
#include <functional>
#include <map>
#include <set>
#include <string>
#include <vector>
#include <cmath>
#include <algorithm>
#include <cstdint>

namespace pv4 {
using MusicCallback = std::function<void(const std::string&)>;
inline const char* Widget = "presentationv4";
inline const std::array<const char*,4> Layers{{"FxFocus","FxNoise","FxImpact","FxTransition"}};

struct Sequence {
    std::string id, texture;
    double elapsed=0;
    int frame=-1;
    bool active=false, visible=false, loop=false;
    float opacity=-1, x=-1, y=-1, w=-1, h=-1;
    float centerX=640, centerY=360;
};
struct Voice { std::string handle; double lifetime=60; };
struct State {
    hb::Actor* owner=nullptr;
    hb::Json contract=hb::Json::object(), audio=hb::Json::object();
    hb::Json lengths=hb::Json::object();
    MusicCallback music;
    std::array<Sequence,4> sequences{};
    std::map<std::string,std::uint64_t> dispatched;
    std::map<std::string,double> lastAction;
    std::set<std::string> once, missing;
    std::vector<Voice> voices;
    std::string bed, ambientCue, ambientHandle, sceneKey;
    float ambientGain=0;
    double time=0;
    bool initialized=false, reducedMotion=false;
    std::uint64_t audioRequests=0, textureWrites=0, dispatches=0;
};

inline std::string Str(const hb::Json& j,const char* key,const std::string& fallback=""){
    auto it=j.find(key);return it!=j.end()&&it->is_string()?it->get<std::string>():fallback;
}
inline float Number(const hb::Json& j,const char* key,float fallback){
    auto it=j.find(key);return it!=j.end()&&it->is_number()?it->get<float>():fallback;
}
inline bool Flag(const hb::Json& j,const char* key,bool fallback=false){
    auto it=j.find(key);return it!=j.end()&&it->is_boolean()?it->get<bool>():fallback;
}
inline bool HasAudio(const State& s,const std::string& cue){
    return s.audio.is_object()&&s.audio.contains(cue)&&s.audio[cue].is_string()&&!s.audio[cue].get<std::string>().empty();
}
inline void Missing(State& s,const std::string& what){
    // Bound diagnostics. The native Stats string has a 4096-character limit.
    if(s.missing.size()<32)s.missing.insert(what);
}
inline void StopAmbient(State& s){
    if(!s.ambientHandle.empty())hb::Audio::Stop(s.ambientHandle);
    s.ambientHandle.clear();s.ambientCue.clear();s.ambientGain=0;
}
inline void HideSequence(State& s,int layer){
    auto& q=s.sequences[layer];
    if(q.visible&&s.owner)hb::UI::SetVisible(s.owner,Widget,Layers[layer],false);
    q.visible=false;q.active=false;q.id.clear();q.frame=-1;q.elapsed=0;
}
inline void Clear(State& s,bool resetPersistent=false,bool stopMusic=false){
    for(int i=0;i<4;i++)HideSequence(s,i);
    for(auto& v:s.voices)if(!v.handle.empty())hb::Audio::Stop(v.handle);
    s.voices.clear();StopAmbient(s);s.dispatched.clear();s.lastAction.clear();s.sceneKey.clear();
    if(resetPersistent){s.once.clear();s.missing.clear();s.time=0;}
    if(stopMusic){if(s.music)s.music("@silence");s.bed.clear();}
}
inline void Init(State& s,hb::Actor* owner,const hb::Json& contract,const hb::Json& art,MusicCallback callback){
    if(s.initialized)Clear(s);
    s.owner=owner;s.contract=contract;s.music=std::move(callback);
    s.audio=art.contains("audio")&&art["audio"].is_object()?art["audio"]:hb::Json::object();
    s.lengths=art.contains("audioLen")&&art["audioLen"].is_object()?art["audioLen"]:hb::Json::object();
    s.initialized=true;
    s.sequences={}; // UI::Show creates new nodes, invalidating property caches.
    if(owner){hb::UI::Show(owner,"Assets/UI/PresentationV4.hbwidget.json",Widget);
        for(int i=0;i<4;i++){hb::UI::SetVisible(owner,Widget,Layers[i],false);s.sequences[i].visible=false;}}
}
inline std::string AssetTexture(const std::string& source){
    return source.rfind("Assets/",0)==0?source:"Assets/Art/presentation_v4/"+source.substr(source.find_last_of("/\\")+1);
}
inline int LayerOf(const std::string& seq){
    if(seq.find("concentration")!=std::string::npos)return 0;
    if(seq.find("panic_noise")!=std::string::npos)return 1;
    if(seq.find("scene_ink")!=std::string::npos)return 3;
    return 2;
}
inline bool FullFrame(const std::string& seq){
    return seq.find("concentration")!=std::string::npos||seq.find("panic_noise")!=std::string::npos||
        seq.find("scene_ink")!=std::string::npos||seq.find("camera_whip")!=std::string::npos||seq.find("discovery_border")!=std::string::npos;
}
inline void DrawSequence(State& s,int layer){
    auto& q=s.sequences[layer];
    if(!q.active||!s.owner||!s.contract.contains("sequences")||!s.contract["sequences"].contains(q.id))return;
    const auto& def=s.contract["sequences"][q.id];
    if(!def.contains("frames")||!def["frames"].is_array()||def["frames"].empty()){HideSequence(s,layer);return;}
    int count=int(def["frames"].size());float fps=std::max(1.f,Number(def,"fps",16));
    int f=s.reducedMotion?count/2:int(std::floor(q.elapsed*fps));
    if(q.loop)f%=count;else f=std::min(f,count-1);
    if(!def["frames"][f].is_string()){Missing(s,"sequence-frame:"+q.id);HideSequence(s,layer);return;}
    auto texture=AssetTexture(def["frames"][f].get<std::string>());
    if(q.texture!=texture){hb::UI::SetTexture(s.owner,Widget,Layers[layer],texture);q.texture=texture;++s.textureWrites;}
    q.frame=f;
    float opacity=s.reducedMotion?(layer==0?.12f:1.f):1.f;
    if(q.opacity!=opacity){hb::UI::SetOpacity(s.owner,Widget,Layers[layer],opacity);q.opacity=opacity;}
    const bool full=FullFrame(q.id);float x=full?0.f:q.centerX-200,y=full?0.f:q.centerY-200,w=full?1280.f:400.f,h=full?720.f:400.f;
    if(q.x!=x||q.y!=y){hb::UI::SetPosition(s.owner,Widget,Layers[layer],{x,y});q.x=x;q.y=y;}
    if(q.w!=w||q.h!=h){hb::UI::SetSize(s.owner,Widget,Layers[layer],{w,h});q.w=w;q.h=h;}
    if(!q.visible){hb::UI::SetVisible(s.owner,Widget,Layers[layer],true);q.visible=true;}
}
inline void Rehost(State& s){
    if(!s.initialized||!s.owner)return;
    // Newly shown trial widgets otherwise cover this earlier UI host.
    hb::UI::Show(s.owner,"Assets/UI/PresentationV4.hbwidget.json",Widget);
    for(int i=0;i<4;i++){auto& q=s.sequences[i];q.texture.clear();q.visible=false;q.opacity=q.x=q.y=q.w=q.h=-1;
        if(q.active)DrawSequence(s,i);else hb::UI::SetVisible(s.owner,Widget,Layers[i],false);}
}
inline bool StartSequence(State& s,const std::string& seq,bool loop=false,float centerX=640,float centerY=360){
    if(!s.contract.contains("sequences")||!s.contract["sequences"].contains(seq)){
        Missing(s,"sequence:"+seq);return false;}
    int layer=LayerOf(seq);auto& q=s.sequences[layer];
    if(q.active&&q.id==seq&&q.loop&&loop)return true;
    q.id=seq;q.elapsed=0;q.frame=-1;q.active=true;q.centerX=centerX;q.centerY=centerY;
    q.loop=loop||Flag(s.contract["sequences"][seq],"loop");DrawSequence(s,layer);return true;
}
inline void Tick(State& s,float delta,bool animate=true){
    if(!s.initialized||!std::isfinite(delta)||delta<0)return;
    s.time+=delta;
    if(animate)for(int i=0;i<4;i++){
        auto& q=s.sequences[i];if(!q.active)continue;
        if(s.reducedMotion&&i==3){HideSequence(s,i);continue;}
        q.elapsed+=delta;const auto& def=s.contract["sequences"][q.id];
        double duration=s.reducedMotion?.07:double(Number(def,"seconds",.5f));
        if(!q.loop&&q.elapsed>=duration){HideSequence(s,i);continue;}
        DrawSequence(s,i);
    }
    for(auto& v:s.voices)v.lifetime-=delta;
    s.voices.erase(std::remove_if(s.voices.begin(),s.voices.end(),[](const Voice& v){return v.lifetime<=0;}),s.voices.end());
}
inline bool Playing(const State& s,const std::string& sequence){
    for(const auto& q:s.sequences){if(q.active&&q.id==sequence)return true;}
    return false;
}
inline bool RequestMusic(State& s,const std::string& spec){
    if(spec.empty())return true;
    if(spec=="@silence"){if(s.music)s.music(spec);s.bed.clear();return true;}
    auto gt=spec.find('>');auto first=spec.substr(0,gt);
    auto after=gt==std::string::npos?std::string():spec.substr(gt+1);
    if(!HasAudio(s,first)||(!after.empty()&&!HasAudio(s,after))){Missing(s,"music:"+spec);return false;}
    if(!s.music){Missing(s,"music-callback");return false;}
    s.music(spec);s.bed=!after.empty()?after:first.rfind("jingle_",0)==0?"":first;return true;
}
inline void MusicPolicy(State& s,const hb::Json& policy){
    if(!policy.is_object())return;
    auto op=Str(policy,"operation");
    if(op=="stop")RequestMusic(s,"@silence");
    else if(op=="play")RequestMusic(s,Str(policy,"cue"));
    // keep/pause/restore-callsite-bed do not masquerade as stop or seek.
}
inline bool Sound(State& s,const std::string& cue,float gain=1.f,const std::string& bus="sfx"){
    if(!HasAudio(s,cue)){Missing(s,"audio:"+cue);return false;}
    float g=std::clamp(gain,0.f,1.f);
    if(g<=0)return true;
    auto handle=hb::Audio::Play(s.audio[cue].get<std::string>(),g,1.f,bus);
    ++s.audioRequests;
    if(!handle.empty()){
        float length=Number(s.lengths,cue.c_str(),60.f);
        if(s.contract.contains("original_cues")&&s.contract["original_cues"].contains(cue))
            length=Number(s.contract["original_cues"][cue],"len",length);
        s.voices.push_back({handle,std::max(.05f,length)+.1f});
    }
    return !handle.empty();
}
inline bool Ambient(State& s,const std::string& cue,float gain=.2f){
    if(!std::isfinite(gain))return false;gain=std::clamp(gain,0.f,1.f);
    if(cue.empty()||gain==0){StopAmbient(s);return true;}
    if(cue==s.ambientCue&&!s.ambientHandle.empty()&&gain==s.ambientGain)return true;
    if(!s.contract.contains("original_cues")||!s.contract["original_cues"].contains(cue)||
       !s.contract["original_cues"][cue].contains("loop_samples")||s.contract["original_cues"][cue]["loop_samples"].is_null()){
        Missing(s,"not-an-ambient-loop:"+cue);return false;}
    if(!HasAudio(s,cue)){Missing(s,"audio:"+cue);return false;}
    StopAmbient(s);
    s.ambientHandle=hb::Audio::Play(s.audio[cue].get<std::string>(),gain,1.f,"sfx");
    if(s.ambientHandle.empty())return false;
    s.ambientCue=cue;s.ambientGain=gain;++s.audioRequests;return true;
}
inline bool WorldAmbience(State& s,bool active,bool outdoor){
    if(!active){StopAmbient(s);return true;}
    const auto& choices=s.contract.value("ambience",hb::Json::object());auto key=outdoor?"outside":"interior_air";
    if(!choices.contains(key)||!choices[key].is_object()){StopAmbient(s);return true;}
    const auto& choice=choices[key];return Ambient(s,Str(choice,"cue"),Number(choice,"gain",.2f));
}
inline bool Footstep(State& s,const std::string& surface,int contact,bool running){
    const auto& footsteps=s.contract.value("footsteps",hb::Json::object());const auto& variants=footsteps.value("variants",hb::Json::object());
    if(!variants.contains(surface)||!variants[surface].is_array()||variants[surface].empty())return false;
    const auto& list=variants[surface];const auto& cue=list[std::max(0,contact)%list.size()];if(!cue.is_string())return false;
    return Sound(s,cue.get<std::string>(),Number(footsteps,running?"running_gain":"gain",running?.7f:.55f));
}
inline bool Action(State& s,const std::string& id,float centerX=640,float centerY=360){
    if(!std::isfinite(centerX)||!std::isfinite(centerY))return false;
    if(!s.contract.contains("actions")||!s.contract["actions"].contains(id)){Missing(s,"action:"+id);return false;}
    const auto& a=s.contract["actions"][id];
    float gap=Number(a,"coalesce_ms",0)/1000.f;
    auto last=s.lastAction.find(id);
    if(gap>0&&last!=s.lastAction.end()&&s.time-last->second<gap)return false;
    s.lastAction[id]=s.time;
    if(a.contains("music"))MusicPolicy(s,a["music"]);
    if(a.contains("sfx")&&a["sfx"].is_array())for(const auto& x:a["sfx"])
        Sound(s,Str(x,"cue"),Number(x,"gain",1),Str(x,"bus","sfx"));
    if(id=="concentration_off")HideSequence(s,0);
    auto seq=Str(a,"sequence");if(!seq.empty())StartSequence(s,seq,id=="concentration_on",centerX,centerY);
    return true;
}
inline bool SceneReady(State& s,const std::string& key,bool quiet=false){
    if(key.empty()||key==s.sceneKey)return false;
    bool first=s.sceneKey.empty();s.sceneKey=key;
    if(first||quiet||s.reducedMotion){HideSequence(s,3);return false;}
    return Action(s,"scene_uncover");
}
inline bool Apply(State& s,const hb::Json& e,std::uint64_t entryGeneration){
    if(!s.initialized)return false;
    auto id=Str(e,"id");
    // Only callers may mint an entry generation. It must remain fixed while
    // polling one node and change on a genuine later revisit of that node.
    if(!id.empty()){
        auto prev=s.dispatched.find(id);if(prev!=s.dispatched.end()&&prev->second==entryGeneration)return false;
        s.dispatched[id]=entryGeneration;
    }
    const auto p=e.contains("presentation")&&e["presentation"].is_object()?e["presentation"]:hb::Json::object();
    auto token=Str(p,"once");if(!token.empty()&&s.once.count(token))return false;
    if(!token.empty())s.once.insert(token);
    ++s.dispatches;
    bool handled=false;
    if(p.contains("actions")&&p["actions"].is_array()){
        handled=true;for(const auto& a:p["actions"])if(a.is_string())Action(s,a.get<std::string>());
    }
    // Explicit scene music wins over an action's default stop/keep policy.
    std::string explicitMusic=Str(e,"music");
    if(p.contains("music")&&p["music"].is_object()){
        auto op=Str(p["music"],"operation");
        if(op=="stop")explicitMusic="@silence";
        else if(op=="play")explicitMusic=Str(p["music"],"cue");
        else if(op=="keep")explicitMusic.clear();
    }
    // Compatibility e.music and the richer identical policy are one request,
    // particularly for a jingle whose duplicated request would restart it.
    if(!explicitMusic.empty())RequestMusic(s,explicitMusic);
    if(!handled&&e.contains("sfx")){
        auto one=[&](const hb::Json& v){if(v.is_string()){auto c=v.get<std::string>();Sound(s,c,1.f,c.rfind("ui_",0)==0?"ui":"sfx");}};
        if(e["sfx"].is_array())for(const auto& v:e["sfx"])one(v);else one(e["sfx"]);
    }
    if(p.contains("ambience")&&p["ambience"].is_object()){
        auto a=p["ambience"];Ambient(s,Str(a,"cue"),Number(a,"gain",.2f));
    }
    return true;
}
inline hb::Json Save(const State& s,const std::string& actualCue,const std::string& pendingBed){
    std::string bed=!pendingBed.empty()?pendingBed:actualCue.rfind("jingle_",0)==0?"":actualCue;
    return {{"version",1},{"bed",bed},{"silent",bed.empty()},{"once",s.once}};
}
inline hb::Json Save(const State& s){return Save(s,s.bed,"");}
inline void Restore(State& s,const hb::Json& saved){
    Clear(s,false,false);s.once.clear();
    if(saved.contains("once")&&saved["once"].is_array())for(const auto& x:saved["once"])if(x.is_string())s.once.insert(x.get<std::string>());
    auto bed=Str(saved,"bed");RequestMusic(s,Flag(saved,"silent",bed.empty())?"@silence":bed);
    // No old effect frame, ambient handle, jingle tail, or guessed seek resumes.
}
inline hb::Json Stats(const State& s){
    hb::Json q=hb::Json::array();for(const auto& x:s.sequences)if(x.active)q.push_back({{"id",x.id},{"frame",x.frame}});
    return {{"ready",s.initialized},{"bed",s.bed},{"once",s.once.size()},{"actions",s.dispatches},
            {"audioRequests",s.audioRequests},{"textureWrites",s.textureWrites},{"sequences",q},
            {"ambient",s.ambientCue},{"missing",s.missing}};
}
} // namespace pv4
