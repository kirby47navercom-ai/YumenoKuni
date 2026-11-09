#pragma once
#include <HBEngine/Game.hpp>
#include "DisplayV4.hpp"
#include "GpuTrialAtlasDataV4.hpp"
#include <map>
#include <set>
#include <string>
#include <cmath>
#include <cstdio>
#include <array>
#include <algorithm>
// Animated gameplay text uses the engine's existing camera-child sprites.
// Rules, glyph positions, hit tests and clocks remain owned by the trial model.
namespace gputrialhudv4 {
struct Node {std::string id,parent,text,font,texture,asset,appliedAsset,align="center";const gputrialatlasv4::Glyph* crop=nullptr;bool assetDirty=true;float x=0,y=0,w=80,h=80,ax=.5f,ay=.5f,sx=1,sy=1,rotation=0,opacity=1,size=54;hb::Color color{1,1,1,1},appliedColor{-1,-1,-1,-1};std::string scope;bool fillViewport=false,contain=false;bool image=false,visible=false,dirty=true,shown=false,forceForeground=false;hb::Actor* actor=nullptr;float px=99999,py=99999,psx=-1,psy=-1,pr=99999,pz=99999,modelDepth=900,yaw=0,pitch=0,appliedYaw=9999,appliedPitch=9999;bool solid=false,solidShown=false;std::string appliedMesh;int order=-1;};
inline std::map<std::string,Node> nodes;
struct ExtraGlyph {std::string sprite;gputrialatlasv4::Glyph crop;};inline std::map<std::string,ExtraGlyph> extraGlyphs;inline std::map<std::string,std::string> textureAliases;inline hb::Actor* anagramRoot=nullptr;inline bool anagramWarming=false,anagramPrepared=false;inline int anagramWarm=0;inline hb::Json anagramTimeMetrics;inline std::string anagramTimer;inline hb::Json stageClockMetrics;inline std::string stageClockText;inline float stageClockX=1040,stageClockY=656,stageClockW=220,stageClockH=48;
struct WarmNode {std::string id,texture;float x,y,w,h,sx,sy;bool visible;};inline std::vector<WarmNode> anagramWarmNodes;inline bool anagramRootWasVisible=false,showdown=false;inline std::map<std::string,hb::Vec2> textureSizes;inline std::string warmScope="anagramhud",warmRoot="AnagramRoot";
inline std::map<std::string,std::string> parents;
inline std::map<std::string,bool> visible;
inline std::map<std::string,float> opacity;
inline std::set<std::string> glyphs;
inline std::set<std::string> noiseOwned;
inline hb::Json nonstopOriginalClock;inline hb::Json timerMetrics;inline float rigUnits=100,glyphUnitScale=10000.f/6;inline bool naturalGlyphs=false,reuseFaces=false;
inline std::string atlasChapter;inline std::map<std::string,std::string> pages;inline std::vector<hb::Actor*> warmups;inline int warmupFrames=0;inline bool warmupOverlay=false,useBatches=false;
inline std::vector<std::pair<std::string,int>> warmupKeys;inline size_t warmupAt=0;
inline hb::Json batches;inline std::map<std::string,hb::Json> batchByKey;inline std::string lineKey;inline bool changingLine=false;
struct Rig {hb::Actor* actor=nullptr;std::string key,anchor;float referenceX=0,referenceY=0,referenceScale=1,referenceRotation=0;bool shown=false;hb::Color color{-1,-1,-1,-1};std::map<int,std::array<float,5>> poses;};
inline std::map<std::string,Rig> rigs;
inline std::string hash(const std::string& s){unsigned h=2166136261u;for(unsigned char c:s){h^=c;h*=16777619u;}char out[16];std::snprintf(out,sizeof out,"g_%08x",h);return out;}
inline void line(const std::string& font,float size,const std::string& text){lineKey=hash(font+"|"+std::to_string(int(size))+"|"+text);auto p=batchByKey.find(lineKey);if(p!=batchByKey.end()){auto ch=p->second.value("chapter",std::string());if(ch!=atlasChapter){atlasChapter=ch;for(auto& [id,n]:nodes)n.assetDirty=true;}}changingLine=true;}
inline hb::Actor* speakerRoot=nullptr;inline float speakerDepth=.2f,appliedSpeakerScale=-1;
inline void setSpeakerDepth(float depth){speakerDepth=std::isfinite(depth)?std::max(.25f,depth):.25f;}
inline hb::Actor* motionRoot=nullptr;inline bool projective=false;inline hb::Vec3 motionPosition{99999,99999,99999};
inline bool ready=false;inline std::string error,timer,renderScope="none";inline int width=0,height=0;
#ifdef _WIN32
inline HWND window=nullptr;
#endif
inline hb::Color color(const std::string& s){unsigned v=0;if(s.size()!=7&&s.size()!=9)return {1,1,1,1};std::sscanf(s.c_str()+1,"%x",&v);if(s.size()==7)v=(v<<8)|255;return {float(v>>24)/255,float((v>>16)&255)/255,float((v>>8)&255)/255,float(v&255)/255};}
// UI colors are sRGB; the sprite API consumes linear RGB. Alpha stays linear.
inline hb::Color linearTint(hb::Color c){auto linear=[](float v){return v<=.04045f?v/12.92f:std::pow((v+.055f)/1.055f,2.4f);};return {linear(c.r),linear(c.g),linear(c.b),c.a};}
inline std::string key(const Node& n){auto s=n.font+"|"+std::to_string(int(n.size))+"|"+std::to_string(int(n.w))+"|"+std::to_string(int(n.h))+"|"+n.align+"|"+n.text;unsigned h=2166136261u;for(unsigned char c:s){h^=c;h*=16777619u;}char out[16];std::snprintf(out,sizeof out,"g_%08x",h);return out;}
inline void mark(){for(auto& [id,n]:nodes)n.dirty=true;}
inline void reset(){nonstopOriginalClock=hb::Json();speakerRoot=nullptr;speakerDepth=.2f;appliedSpeakerScale=-1;motionRoot=nullptr;projective=false;reuseFaces=false;motionPosition={99999,99999,99999};nodes.clear();extraGlyphs.clear();textureAliases.clear();anagramRoot=nullptr;showdown=false;textureSizes.clear();anagramWarming=anagramPrepared=false;anagramWarm=0;anagramWarmNodes.clear();anagramTimeMetrics=stageClockMetrics=hb::Json();anagramTimer.clear();stageClockText.clear();parents.clear();visible.clear();opacity.clear();glyphs.clear();noiseOwned.clear();rigs.clear();pages.clear();warmups.clear();warmupKeys.clear();warmupAt=0;warmupFrames=0;warmupOverlay=false;atlasChapter.clear();useBatches=false;batches=hb::Json::array();batchByKey.clear();lineKey.clear();ready=false;renderScope="none";error.clear();timer.clear();width=height=0;
#ifdef _WIN32
window=nullptr;
#endif
}
inline void addExtraGlyphs(const hb::Json& rows){
 for(const auto& row:rows){
  const auto& crop=row.at("crop");ExtraGlyph glyph;
  glyph.sprite=row.at("sprite");glyph.crop={0,crop[0].get<std::int16_t>(),crop[1].get<std::int16_t>(),crop[2].get<std::int16_t>(),crop[3].get<std::int16_t>()};
  extraGlyphs.emplace(row.at("key").get<std::string>(),glyph);
 }
}
inline void mount(){reset();if(!hb::Scene::FindActorById("TrialGpu_CourtDim"))return;renderScope=hb::Scene::FindActorById("CourtDebateScene")?"debate":hb::Scene::FindActorById("CourtPanicScene")?"panic":hb::Scene::FindActorById("CourtAnagramScene")?"anagram":hb::Scene::FindActorById("CourtShowdownScene")?"showdown":"basic";speakerRoot=hb::Scene::FindActorById("TrialSpeakerDepth");if(renderScope=="debate"&&!speakerRoot){error="Missing speaker-depth root";return;}motionRoot=hb::Scene::FindActorById("TrialGlyphMotion");auto d=hb::Data::Get("Assets/Data/gpu_trial_layout.json");anagramRoot=hb::Scene::FindActorById("AnagramHudRoot");if(anagramRoot&&d.contains("anagramLayout")){auto ext=hb::Data::Get(d["anagramLayout"].get<std::string>());for(auto field:{"nodes","parents"})for(const auto& row:ext[field])d[field].push_back(row);anagramTimeMetrics=ext["anagramTimeMetrics"];for(auto it=ext["textureAliases"].begin();it!=ext["textureAliases"].end();++it)textureAliases.emplace(it.key(),it.value().get<std::string>());addExtraGlyphs(ext["extraGlyphs"]);}
 showdown=hb::Scene::FindActorById("ShowdownHudRoot")!=nullptr;if(showdown&&d.contains("showdownLayout")){auto ext=hb::Data::Get(d["showdownLayout"].get<std::string>());for(auto field:{"nodes","parents"})for(const auto& row:ext[field])d[field].push_back(row);for(auto it=ext["textureAliases"].begin();it!=ext["textureAliases"].end();++it)textureAliases.emplace(it.key(),it.value().get<std::string>());for(auto it=ext["textureSizes"].begin();it!=ext["textureSizes"].end();++it)textureSizes[it.key()]={it.value()[0].get<float>(),it.value()[1].get<float>()};addExtraGlyphs(ext["extraGlyphs"]);if(ext.contains("extraGlyphPages"))for(const auto& page:ext.at("extraGlyphPages"))addExtraGlyphs(hb::Data::Get(page.get<std::string>()));}

 if((renderScope=="basic"||renderScope=="showdown")&&d.contains("stageClockLayout")){auto ext=hb::Data::Get(d["stageClockLayout"].get<std::string>());stageClockMetrics=ext;stageClockX=ext["rect"][0];stageClockY=ext["rect"][1];stageClockW=ext["rect"][2];stageClockH=ext["rect"][3];for(auto field:{"nodes","parents"})for(const auto& row:ext[field])d[field].push_back(row);for(const auto& row:ext["extraGlyphs"]){ExtraGlyph e;e.sprite=row["sprite"];e.crop={0,0,0,480,288};extraGlyphs.emplace(row["key"].get<std::string>(),e);}}

 for(auto& p:d["parents"]){auto id=p["id"].get<std::string>();parents[id]=p.value("parent",std::string());visible[id]=p.value("visible",true);opacity[id]=p.value("opacity",1.f);}
 if(d.contains("glyphs"))for(auto& row:d["glyphs"])for(auto& id:row)glyphs.insert(id.get<std::string>());
 if(d.contains("styles"))for(auto& st:d["styles"]){auto chars=st["characters"].get<std::string>();for(size_t at=0;at<chars.size();){unsigned char c=chars[at];int n=c<128?1:c<224?2:c<240?3:4;Node g;g.font=st["font"];g.size=st["size"];g.w=st["w"];g.h=st["h"];g.align=st["align"];g.text=chars.substr(at,n);glyphs.insert(key(g));at+=n;}}
 timerMetrics=d["timerMetrics"];if(renderScope=="debate"&&d.contains("nonstopOriginalClock"))nonstopOriginalClock=d["nonstopOriginalClock"];reuseFaces=d.value("reuseFaces",false);
 rigUnits=d.value("rigUnits",100.f);naturalGlyphs=d.contains("glyphPixelsPerUnit");glyphUnitScale=d.value("glyphPixelsPerUnit",10000.f)/d.value("glyphBakeScale",6.f);
 if(d.contains("pages"))for(auto& p:d["pages"])pages[p["chapter"].get<std::string>()+"|"+p["font"].get<std::string>()+"|"+std::to_string(p["size"].get<int>())]=p["sprite"].get<std::string>();
 batches=d.value("batches",hb::Json::array());for(auto& b:batches)batchByKey.emplace(b["key"].get<std::string>(),b);for(auto layer:{"MB","MS","MF"})for(int c=0;c<(std::string(layer)=="MS"?1:3);c++){auto id=std::string(layer)+std::to_string(c);Rig r;r.actor=hb::Scene::FindActorById("TrialBatch_"+id);if(r.actor)rigs.emplace(id,r);}
 for(auto& p:d["nodes"]){if(p.contains("renderScopes")){bool selected=false;for(const auto& scope:p["renderScopes"])if(scope==renderScope)selected=true;if(!selected)continue;}Node n;n.id=p["id"];n.parent=p["parent"];n.font=p.value("font",std::string());n.text=p.value("text",std::string());n.texture=p.value("texture",std::string());n.align=p.value("align",std::string("center"));n.size=p.value("fontSize",54.f);n.scope=p.value("scope",std::string());n.fillViewport=p.value("fillViewport",false);n.contain=p.value("contain",false);n.image=p.value("image",false);n.color=n.image?hb::Color{1,1,1,1}:color(p.value("color",std::string("#ffffffff")));n.x=p["rect"][0];n.y=p["rect"][1];n.w=p["rect"][2];n.h=p["rect"][3];n.ax=p["alignment"][0];n.ay=p["alignment"][1];if(renderScope=="debate"&&n.id.size()>2&&n.id[0]=='N')n.w=n.h=80;n.visible=p.value("visible",false);n.opacity=p.value("opacity",1.f);n.actor=hb::Scene::FindActorById("TrialGpu_"+n.id);if(!n.actor&&reuseFaces&&n.id.size()>2&&(n.id[0]=='M'||n.id[0]=='N')&&n.id[1]=='B')n.actor=hb::Scene::FindActorById("TrialGpu_"+n.id.substr(0,1)+"F"+n.id.substr(2));if(!n.actor){error="GPU trial actor missing: "+n.id;return;}nodes.emplace(n.id,n);}
#ifdef _WIN32
 window=displayv4::Window();
#endif
 ready=true;
}
inline bool hasAnagram(){return anagramRoot!=nullptr;}
inline bool warmAnagram(){if(!hasAnagram())throw std::runtime_error("Anagram scene has no HUD");if(anagramPrepared)return true;warmScope="anagramhud";warmRoot="AnagramRoot";anagramWarming=true;return false;}
inline bool warmShowdown(){if(!showdown)throw std::runtime_error("Showdown scene has no HUD");if(anagramPrepared)return true;warmScope="showdown";warmRoot="ShowdownRoot";anagramWarming=true;return false;}
inline bool pollAnagram(){if(!anagramWarming)return true;if(anagramWarm==0){anagramRootWasVisible=visible[warmRoot];visible[warmRoot]=true;anagramWarmNodes.clear();for(auto& [key,n]:nodes)if(n.scope==warmScope&&n.image){anagramWarmNodes.push_back({key,n.texture,n.x,n.y,n.w,n.h,n.sx,n.sy,n.visible});n.visible=true;n.dirty=true;n.sx=n.sy=1;if(key.rfind("AnaBall",0)==0){n.x=640;n.y=360;}if(key=="AnaSpot"){n.w=n.h=400;n.x=440;n.y=160;}}anagramWarm=1;return false;}if(anagramWarm==1){for(auto& [key,n]:nodes)if(n.scope==warmScope&&key.rfind("AnaBall",0)==0){n.texture=textureAliases.at("Assets/Art/ui/anagram_orb.svg");n.dirty=true;}if(showdown){auto& face=nodes.at("SdFace");face.texture="Assets/Art/sprites/mio/mio_T01.webp";face.dirty=true;}anagramWarm=2;return false;}for(const auto& saved:anagramWarmNodes){auto& n=nodes.at(saved.id);n.texture=saved.texture;n.x=saved.x;n.y=saved.y;n.w=saved.w;n.h=saved.h;n.sx=saved.sx;n.sy=saved.sy;n.visible=saved.visible;n.dirty=true;}visible[warmRoot]=anagramRootWasVisible;mark();anagramWarmNodes.clear();anagramWarming=false;anagramPrepared=true;return true;}
inline void releaseAnagram(){if(!hasAnagram())return;visible["AnagramRoot"]=visible["AnaTime"]=false;mark();}
inline bool owns(const std::string& id){return ready&&nodes.count(id);}
inline bool setVisible(const std::string& id,bool v){if(!ready)return false;auto p=visible.find(id);if(p!=visible.end()&&p->second!=v){p->second=v;mark();}auto n=nodes.find(id);if(n==nodes.end())return (id=="Timer"&&nodes.count("Timer0"))||(id=="AnaTime"&&nodes.count("AnaTimeDigit0"))||(id=="StageTimer"&&nodes.count("StageClockDigit0"));n->second.visible=v;n->second.dirty=true;return true;}
inline void layoutStageClock(){if(stageClockMetrics.is_null())return;float total=0;for(size_t i=0;i<stageClockText.size();i++){auto c=stageClockText.substr(i,1);total+=stageClockMetrics["advance"].at(c).get<float>();if(i+1<stageClockText.size())total+=stageClockMetrics["kern"].at(stageClockText.substr(i,2)).get<float>();}float x=stageClockX+stageClockW-total;for(int i=0;i<9;i++){auto& n=nodes.at("StageClockDigit"+std::to_string(i));auto c=i<int(stageClockText.size())?stageClockText.substr(i,1):std::string();if(n.text!=c){n.text=c;n.assetDirty=true;}n.x=x;n.y=stageClockY;n.dirty=true;if(!c.empty()){x+=stageClockMetrics["advance"].at(c).get<float>();if(i+1<int(stageClockText.size()))x+=stageClockMetrics["kern"].at(stageClockText.substr(i,2)).get<float>();}}}
inline bool setText(const std::string& id,const std::string& v){if(!ready)return false;if(id=="StageTimer"&&!stageClockMetrics.is_null()){stageClockText=v;layoutStageClock();return true;}if(id=="AnaTime"&&!anagramTimeMetrics.is_null()){anagramTimer=v;float x=anagramTimeMetrics["x"].get<float>();for(int i=0;i<9;i++){auto& n=nodes.at("AnaTimeDigit"+std::to_string(i));auto digit=i<int(v.size())?std::string(1,v[i]):"";if(n.text!=digit){n.text=digit;n.assetDirty=true;}n.x=x;n.dirty=true;if(i<int(v.size())){x+=anagramTimeMetrics["advance"][digit].get<float>();if(i+1<int(v.size()))x+=anagramTimeMetrics["kern"][v.substr(i,2)].get<float>();}}return true;}if(id=="Timer"){if(!nodes.count("Timer0"))return false;
 timer=v;if(!nonstopOriginalClock.is_null()){
  auto& panel=nodes.at("TimerPanel");auto rect=nonstopOriginalClock["clock"];panel.x=rect[0];panel.y=rect[1];panel.w=rect[2];panel.h=rect[3];panel.texture="Assets/Art/ui/nonstop_source/clock.png";panel.dirty=true;
  for(int i=0;i<9;i++){auto& n=nodes.at("Timer"+std::to_string(i));auto r=nonstopOriginalClock["clockDigits"][i];n.x=r[0];n.y=r[1];n.w=r[2];n.h=r[3];n.ax=n.ay=0;n.sx=n.sy=1;n.color={1,1,1,1};n.image=true;n.text=i<int(v.size())?v.substr(i,1):"";auto digit=n.text==":"?10:n.text.empty()?0:n.text[0]-'0';auto texture="Assets/Art/ui/nonstop_source/digit"+std::to_string(digit)+".png";if(n.texture!=texture){n.texture=texture;n.assetDirty=true;}n.dirty=true;
  }return true;
 }constexpr float scale=.8f;float full=0;for(char c:v)full+=timerMetrics[std::string(1,c)].get<float>()*scale;float x=1216-full; // Ink stays inside the plate, including top/bottom padding.
 for(int i=0;i<9;i++){auto& n=nodes.at("Timer"+std::to_string(i));auto digit=i<int(v.size())?std::string(1,v[i]):"";if(n.text!=digit){n.text=digit;n.assetDirty=true;}n.x=x-40*(1-scale);n.y=655;n.sx=n.sy=scale;n.dirty=true;if(i<int(v.size()))x+=timerMetrics[n.text].get<float>()*scale;}return true;}
 auto at=nodes.find(id);if(at==nodes.end())return false;at->second.text=v;at->second.assetDirty=true;at->second.dirty=true;return true;}
inline bool setPosition(const std::string& id,hb::Vec2 v){if(id=="StageTimer"&&!stageClockMetrics.is_null()){stageClockX=v.x;stageClockY=v.y;layoutStageClock();return true;}if(!owns(id))return false;auto& n=nodes.at(id);n.x=v.x;n.y=v.y;n.dirty=true;return true;}
inline bool setScale(const std::string& id,hb::Vec2 v){if(!owns(id))return false;auto& n=nodes.at(id);n.sx=v.x;n.sy=v.y;n.dirty=true;return true;}
inline bool setSize(const std::string& id,hb::Vec2 v){if(id=="StageTimer"&&!stageClockMetrics.is_null()){stageClockW=v.x;stageClockH=v.y;layoutStageClock();return true;}if(!owns(id))return false;auto& n=nodes.at(id);n.w=v.x;n.h=v.y;n.assetDirty=true;n.dirty=true;return true;}
inline bool setRotation(const std::string& id,float v){if(!owns(id))return false;auto& n=nodes.at(id);n.rotation=v;n.dirty=true;return true;}
inline bool setOpacity(const std::string& id,float v){if(!ready)return false;if(opacity.count(id)&&opacity[id]!=v){opacity[id]=v;mark();}if(!owns(id))return (id=="Timer"&&nodes.count("Timer0"))||(id=="AnaTime"&&nodes.count("AnaTimeDigit0"))||(id=="StageTimer"&&nodes.count("StageClockDigit0"));auto& n=nodes.at(id);n.opacity=v;n.dirty=true;return true;}
inline bool setColor(const std::string& id,hb::Color v){if(!ready)return false;if(id=="StageTimer"&&!stageClockMetrics.is_null()){for(int i=0;i<9;i++){auto& n=nodes.at("StageClockDigit"+std::to_string(i));n.color=v;n.dirty=true;}return true;}if(id=="Timer"){if(!nodes.count("Timer0"))return false;for(int i=0;i<9;i++){auto& n=nodes.at("Timer"+std::to_string(i));n.color=nonstopOriginalClock.is_null()?v:hb::Color{1,1,1,1};n.dirty=true;}return true;}if(!owns(id))return false;auto& n=nodes.at(id);n.color=v;n.dirty=true;return true;}
inline bool setFont(const std::string& id,const std::string& v){if(!owns(id))return false;nodes.at(id).font=v;nodes.at(id).assetDirty=true;nodes.at(id).dirty=true;return true;}
inline bool setFontSize(const std::string& id,float v){if(!owns(id))return false;nodes.at(id).size=v;nodes.at(id).assetDirty=true;nodes.at(id).dirty=true;return true;}
inline bool setTexture(const std::string& id,const std::string& v){if(!owns(id))return false;nodes.at(id).texture=textureAliases.count(v)?textureAliases.at(v):v;nodes.at(id).assetDirty=true;nodes.at(id).dirty=true;return true;}
inline void raw(const std::string& id,float x,float y,float scale,float rotation,float alpha,float depth=900,bool front=true,bool solid=false,float yaw=0,float pitch=0){if(!owns(id))return;auto& n=nodes.at(id);n.x=x;n.y=y;n.sx=n.sy=scale;n.rotation=rotation;n.opacity=alpha;n.modelDepth=depth;n.solid=solid;n.yaw=yaw;n.pitch=pitch;n.forceForeground=renderScope=="debate"&&id[0]=='N'&&front;n.dirty=true;}
inline void hide(){if(ready){for(auto& [id,n]:nodes){if(n.shown){hb::Components::SetBool(n.actor,"SpriteRenderer","visible",false);n.shown=false;}if(n.solidShown){hb::Components::SetBool(n.actor,"MeshRenderer","visible",false);n.solidShown=false;}}for(auto& [id,r]:rigs)if(r.shown)hb::Components::SetBool(r.actor,"SpriteRenderer","visible",false);}reset();}
inline void motion(int kind,float t){bool nextProjective=motionRoot&&(kind==0||kind==1||kind==8);if(nextProjective!=projective){projective=nextProjective;for(auto& [id,n]:nodes)if(id[0]=='M'){n.px=n.py=n.pz=99999;n.psx=n.psy=-1;n.dirty=true;}}bool next=false; /* Claude 2026-11-04 : 통째 묶음(rig)은 줄이 바뀔 때 앞줄 글자 그림이 남고(「그럼」→「피일」) 글자가 빠져 한글이 깨졌다. 글자별 경로만 쓴다. 원래 : kind==3||(kind==6&&t>=.3f)||(kind==7&&t>=.16f)||(kind==9)||(kind==11&&t>=.5f) */if(useBatches!=next){useBatches=next;mark();}}
inline bool warmup(const std::string& chapter,const std::vector<std::pair<std::string,int>>& keys){if(!ready)return false;if(atlasChapter!=chapter){atlasChapter=chapter;for(auto& [id,n]:nodes)n.assetDirty=true;mark();}warmupKeys.clear();for(const auto& k:keys)if(batchByKey.count(k.first)&&std::find(warmupKeys.begin(),warmupKeys.end(),k)==warmupKeys.end())warmupKeys.push_back(k);warmupAt=0;warmupFrames=warmupKeys.empty()?0:int(warmupKeys.size())+2;return warmupFrames>0;}
inline void advanceWarmup(){if(warmupFrames<=0)return;if(warmupAt<warmupKeys.size()){const auto& spec=batchByKey.at(warmupKeys[warmupAt].first);for(auto& [id,r]:rigs){if(id.substr(0,2)!="MS"&&id.back()!='0'&&id.back()!=char('0'+warmupKeys[warmupAt].second))continue;hb::Sprites::SetSprite(r.actor,spec.at("sprite").get<std::string>());hb::Components::SetString(r.actor,"SpriteSkin","rig",spec.at("rig").get<std::string>());r.key.clear();r.anchor.clear();r.poses.clear();}++warmupAt;}--warmupFrames;}
inline bool inView(const Node& n){float fit=std::min(width/1280.f,height/720.f);if(fit<=0)return true;float a=n.rotation*.0174532925199433f,c=std::abs(std::cos(a)),r=std::abs(std::sin(a)),hw=(c*n.w*std::abs(n.sx)+r*n.h*std::abs(n.sy))*.5f,hh=(r*n.w*std::abs(n.sx)+c*n.h*std::abs(n.sy))*.5f,x=n.x+(.5f-n.ax)*n.w,y=n.y+(.5f-n.ay)*n.h;return x+hw>=-2&&x-hw<=width/fit+2&&y+hh>=-2&&y-hh<=height/fit+2;}
inline float alphaOf(const Node& n){if(!n.visible||!inView(n)||n.text.find_first_not_of(" \t\r\n")==std::string::npos)return 0;float a=n.opacity;auto p=n.parent;for(int i=0;i<16&&!p.empty();i++){if(!visible[p])return 0;a*=opacity[p];p=parents[p];}return a;}
inline std::set<std::string> flushBatches(float fit,float unit,int w,int h){
 std::set<std::string> owned;
 if(!useBatches){for(auto& [id,r]:rigs)if(r.shown){hb::Components::SetBool(r.actor,"SpriteRenderer","visible",false);r.shown=false;}return owned;}
 for(auto& [id,r]:rigs){
  auto layer=id.substr(0,2);if(changingLine)continue;int group=id.back()-'0';auto found=batchByKey.find(lineKey);const hb::Json* spec=found==batchByKey.end()?nullptr:&found->second;
  std::vector<Node*> selected;float alpha=-1;bool compatible=spec!=nullptr;hb::Color tint{};
  if(spec)for(int i=0;i<spec->at("count").get<int>();i++){auto& n=nodes.at(layer+std::to_string(i));float a=alphaOf(n);int colorGroup=n.color.r>.8f&&n.color.g<.9f?1:n.color.r<.8f?2:0;if(layer=="MS")colorGroup=0;if(colorGroup!=group||a<=0)continue;if(alpha<0){alpha=a;tint=n.color;}selected.push_back(&n);}
  if(!selected.empty()){std::map<int,int> histogram;for(auto* n:selected)histogram[int(std::round(alphaOf(*n)*250))]++;auto best=std::max_element(histogram.begin(),histogram.end(),[](const auto& a,const auto& b){return a.second<b.second;});alpha=best->first/250.f;selected.erase(std::remove_if(selected.begin(),selected.end(),[&](const Node* n){return std::abs(alphaOf(*n)-alpha)>.0041f;}),selected.end());}
  bool show=compatible&&!selected.empty();
  if(show){
   if(r.key!=lineKey){hb::Components::SetString(r.actor,"SpriteRenderer","sprite",spec->at("sprite").get<std::string>());hb::Components::SetString(r.actor,"SpriteSkin","rig",spec->at("rig").get<std::string>());r.key=lineKey;r.anchor.clear();r.poses.clear();if(r.shown){hb::Components::SetBool(r.actor,"SpriteRenderer","visible",false);r.shown=false;}continue;}
   auto rebase=[&](){auto& n=*selected.front();r.anchor=n.id;r.referenceX=n.x+(.5f-n.ax)*n.w;r.referenceY=-(n.y+(.5f-n.ay)*n.h);r.referenceScale=n.sx;r.referenceRotation=-n.rotation;r.poses.clear();};
   if(r.anchor.empty())rebase();auto& anchor=nodes.at(r.anchor);float factor=anchor.sx/r.referenceScale,angle=-anchor.rotation-r.referenceRotation;
   if(!std::isfinite(factor)||factor<=0||fit*unit*rigUnits*factor<.01f){rebase();factor=1;angle=0;}
   float rad=angle*.0174532925199433f,c=std::cos(rad),sn=std::sin(rad),ax=anchor.x+(.5f-anchor.ax)*anchor.w,ay=-(anchor.y+(.5f-anchor.ay)*anchor.h);
   float tx=ax-factor*(c*r.referenceX-sn*r.referenceY),ty=ay-factor*(sn*r.referenceX+c*r.referenceY);
   const float z=selected.front()->modelDepth/900.f;hb::Scene::SetPosition(r.actor,{(-w*.5f*unit+tx*fit*unit)*z,(h*.5f*unit+ty*fit*unit)*z,-.2f*z});
   hb::Scene::SetScale(r.actor,{fit*unit*rigUnits*factor*z,fit*unit*rigUnits*factor*z,1});hb::Scene::SetRotation(r.actor,{0,0,angle});
   tint.a*=alpha;if(tint.r!=r.color.r||tint.g!=r.color.g||tint.b!=r.color.b||tint.a!=r.color.a){hb::Sprites::SetColor(r.actor,linearTint(tint));r.color=tint;}
   for(int i=0;i<spec->at("count").get<int>();i++){
    auto& n=nodes.at(layer+std::to_string(i));bool on=std::find(selected.begin(),selected.end(),&n)!=selected.end();float x=n.x+(.5f-n.ax)*n.w-tx,y=-(n.y+(.5f-n.ay)*n.h)-ty;
    std::array<float,5> pose{on?(c*x+sn*y)/(factor*rigUnits):-9999.f,on?(-sn*x+c*y)/(factor*rigUnits):-9999.f,n.sx/factor,n.sy/factor,-n.rotation-angle};
    auto bone="g"+std::to_string(i);auto it=r.poses.find(i);bool fresh=it==r.poses.end();if(fresh)it=r.poses.emplace(i,std::array<float,5>{9999,9999,-1,-1,9999}).first;auto& previous=it->second;
    // Same display tolerances as drawGlyphs, applied after the shared transform.
    float pixels=rigUnits*factor;
    if(fresh||std::abs((pose[0]-previous[0])*pixels)>.6f||std::abs((pose[1]-previous[1])*pixels)>.6f){hb::SpriteSkin::SetBonePosition(r.actor,bone,{pose[0],pose[1]});previous[0]=pose[0];previous[1]=pose[1];}
    if(on){if(fresh||std::abs((pose[2]-previous[2])*factor)>.006f||std::abs((pose[3]-previous[3])*factor)>.006f){hb::SpriteSkin::SetBoneScale(r.actor,bone,{pose[2],pose[3]});previous[2]=pose[2];previous[3]=pose[3];}if(fresh||std::abs(pose[4]-previous[4])>.2f){hb::SpriteSkin::SetBoneRotation(r.actor,bone,pose[4]);previous[4]=pose[4];}}
   }
   for(auto* n:selected)owned.insert(n->id);
  }
  if(show!=r.shown){hb::Components::SetBool(r.actor,"SpriteRenderer","visible",show);r.shown=show;}
 }
 return owned;
}
inline void flush(){if(!ready)return;int w=1280,h=720;
#ifdef _WIN32
 RECT r{};if(window&&GetClientRect(window,&r)){w=r.right;h=r.bottom;}
#endif
 if(w<=0||h<=0)return;if(w!=width||h!=height){width=w;height=h;mark();}
 const float fit=std::min(w/1280.f,h/720.f),depth=.2f,unit=2*depth*std::tan(43.6f*3.14159265358979323846f/360)/h;
 if(speakerRoot){const float scale=speakerDepth/depth;if(scale!=appliedSpeakerScale){hb::Scene::SetScale(speakerRoot,{scale,scale,scale});appliedSpeakerScale=scale;for(auto& [id,n]:nodes)if(n.forceForeground)n.dirty=true;}}
 hb::Vec3 root{};if(projective){const auto& a=nodes.at("MF0");const float z=a.modelDepth/900.f;root={(a.x*fit-w*.5f)*unit*z,(h*.5f-a.y*fit)*unit*z,-depth*z};}if(motionRoot&&(root.x!=motionPosition.x||root.y!=motionPosition.y||root.z!=motionPosition.z)){hb::Scene::SetPosition(motionRoot,root);motionPosition=root;}

 auto batched=flushBatches(fit,unit,w,h);batched.insert(noiseOwned.begin(),noiseOwned.end());
 for(auto& [slot,physical]:nodes){if(!physical.actor)continue;if(reuseFaces&&slot.size()>2&&(slot[0]=='M'||slot[0]=='N')&&slot[1]=='B')continue;const bool face=reuseFaces&&slot.size()>2&&(slot[0]=='M'||slot[0]=='N')&&slot[1]=='F';Node* alternate=face?&nodes.at(slot.substr(0,1)+"B"+slot.substr(2)):nullptr;Node& n=alternate&&!physical.visible&&alternate->visible?*alternate:physical;auto& state=physical;const auto& id=n.id;if(changingLine&&id[0]=='M')continue;if(!n.dirty&&!state.dirty&&(!alternate||!alternate->dirty)&&(!useBatches||id[0]!='M'))continue;n.dirty=state.dirty=false;if(alternate)alternate->dirty=false;bool show=n.visible&&!batched.count(id)&&(n.image||inView(n));float alpha=n.opacity;auto p=n.parent;
  bool centeredArmament=false;for(int i=0;i<16&&!p.empty();i++){centeredArmament=centeredArmament||p=="ArmSceneRoot";show=show&&visible[p];alpha*=opacity[p];p=parents[p];}
  if(id.rfind("Timer",0)==0){show=show&&visible["Timer"];alpha*=opacity["Timer"];}
  show=show&&alpha>0&&(n.image||n.text.find_first_not_of(" \t\r\n")!=std::string::npos);
  if(show){
   if(n.assetDirty){n.assetDirty=false;n.crop=nullptr;n.asset.clear();if(!n.image){
    if(renderScope=="debate"&&(id[0]=='M'||id[0]=='N')&&glyphs.count(key(n)))n.asset="Assets/Art/ui/gpu_trial/"+key(n)+".hbsprite.json";
    if(n.asset.empty()&&(id[0]=='M'||id[0]=='N')&&!atlasChapter.empty()){auto name=hash(atlasChapter+"|"+n.font+"|"+std::to_string(int(n.size))+"|"+n.text);unsigned key=0;std::sscanf(name.c_str()+2,"%x",&key);n.crop=gputrialatlasv4::find(key);if(n.crop)n.asset="Assets/Art/ui/gpu_trial/a_"+name.substr(2)+".hbsprite.json";}
    if(n.asset.empty()){auto k=key(n);auto extra=extraGlyphs.find(k);if(extra!=extraGlyphs.end()){n.asset=extra->second.sprite;n.crop=&extra->second.crop;}else if(glyphs.count(k))n.asset="Assets/Art/ui/gpu_trial/"+k+".hbsprite.json";else error="GPU trial glyph not baked: "+n.font+" "+std::to_string(int(n.size))+" "+n.text;}
   }}
   if(!n.image&&n.asset.empty())show=false;
   if(show&&face){int order=(renderScope=="panic"&&id[0]=='N'?950:id[0]=='M'?(id[1]=='B'?300:500):(id[1]=='B'?350:550))+std::stoi(id.substr(2));if(state.order!=order){hb::Components::Set(n.actor,"SpriteRenderer","sortingOrder",order);state.order=order;}}
   if(show){auto wanted=n.image?n.texture:n.asset;if(state.appliedAsset!=wanted){if(n.image)hb::Components::SetString(n.actor,"SpriteRenderer","texture",wanted);else hb::Sprites::SetSprite(n.actor,wanted);state.appliedAsset=wanted;}
    float gw=n.fillViewport?w/fit:n.w,gh=n.fillViewport?h/fit:n.h,x=n.x+(.5f-n.ax)*gw,y=n.y+(.5f-n.ay)*gh;
    if(centeredArmament){x+=(w/fit-1280)*.5f;y+=(h/fit-720)*.5f;}
    if(n.contain&&textureSizes.count(n.texture)){const auto size=textureSizes.at(n.texture);float contain=std::min(gw/size.x,gh/size.y);gw=size.x*contain;gh=size.y*contain;}
    if(n.crop&&!n.solid){float rad=n.rotation*.0174532925199433f,c=std::cos(rad),sn=std::sin(rad),dx=(n.crop->ox/12.f)*n.sx,dy=(n.crop->oy/12.f)*n.sy;x+=c*dx-sn*dy;y+=sn*dx+c*dy;gw=n.crop->w/6.f;gh=n.crop->h/6.f;}
    if(!nonstopOriginalClock.is_null()&&id.rfind("Timer",0)==0){x+=(w/fit-1280);y+=(h/fit-720);}
    const bool spatial=projective&&id[0]=='M';const bool worldGlyph=renderScope=="debate"&&id.size()>2&&(id[0]=='M'||id[0]=='N')&&(id[1]=='F'||id[1]=='B'||id[1]=='S');const float ratio=worldGlyph?(n.forceForeground?depth/speakerDepth:n.modelDepth/900.f):1,px=(x*fit-w*.5f)*unit*ratio-(spatial?root.x:0),py=(h*.5f-y*fit)*unit*ratio-(spatial?root.y:0),pz=-depth*ratio-(spatial?root.z:0),sx=(n.solid?540*n.sx*fit*unit:naturalGlyphs&&!n.image?glyphUnitScale*n.sx*fit*unit:gw*n.sx*fit*unit*100)*ratio,sy=(n.solid?540*n.sy*fit*unit:naturalGlyphs&&!n.image?glyphUnitScale*n.sy*fit*unit:gh*n.sy*fit*unit*100)*ratio;
    const float epsilon=worldGlyph?.3f*fit*unit*ratio:0,scaleEpsilon=spatial?.0001f:0;
    if(std::abs(px-state.px)>epsilon||std::abs(py-state.py)>epsilon||std::abs(pz-state.pz)>epsilon){hb::Scene::SetPosition(n.actor,{px,py,pz});state.px=px;state.py=py;state.pz=pz;}if(std::abs(sx-state.psx)>scaleEpsilon||std::abs(sy-state.psy)>scaleEpsilon){hb::Scene::SetScale(n.actor,{sx,sy,n.solid?sy:1.f});state.psx=sx;state.psy=sy;}if(std::abs(n.rotation-state.pr)>(spatial?.2f:0)||n.yaw!=state.appliedYaw||n.pitch!=state.appliedPitch){hb::Scene::SetRotation(n.actor,{n.pitch,-n.yaw,-n.rotation});state.pr=n.rotation;state.appliedYaw=n.yaw;state.appliedPitch=n.pitch;}auto c=n.color;c.a*=alpha;auto& a=state.appliedColor;if(c.r!=a.r||c.g!=a.g||c.b!=a.b||std::abs(c.a-a.a)>(spatial?.025f:0)){hb::Sprites::SetColor(n.actor,linearTint(c));a=c;}
   }
  }
  const bool solid=show&&n.solid&&alpha>.5f;
  if(solid){unsigned cp=0;for(size_t k=0;k<n.text.size();k++){unsigned char ch=n.text[k];if(k==0)cp=ch<128?ch:ch<224?ch&31:ch<240?ch&15:ch&7;else cp=(cp<<6)|(ch&63);}char code[16];std::snprintf(code,sizeof code,"%x",cp);auto mesh="Assets/Art/nonstop_solid_type/u_"+std::string(code)+(n.color.r>.8f?(n.color.b<.5f?"_y.glb":"_w.glb"):"_b.glb");if(mesh!=state.appliedMesh){hb::Components::SetString(n.actor,"MeshRenderer","mesh",mesh);state.appliedMesh=mesh;}}
  if(solid!=state.solidShown){hb::Components::SetBool(n.actor,"MeshRenderer","visible",solid);state.solidShown=solid;}
  const bool sprite=show&&!n.solid;
  if(sprite!=state.shown){hb::Components::SetBool(n.actor,"SpriteRenderer","visible",sprite);state.shown=sprite;}
 }
}
struct Frame {Frame(){changingLine=false;}~Frame(){try{flush();advanceWarmup();}catch(const std::exception& e){error=e.what();}}};
}
