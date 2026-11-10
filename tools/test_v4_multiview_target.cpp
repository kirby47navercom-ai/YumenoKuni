#include <HBEngine/SceneRender.hpp>
#include <cassert>
#include <iostream>
using namespace hb::gpu;
int main(){
 Device gpu;SceneRenderer renderer(gpu,96,64);
 auto mesh=renderer.createMesh({{{-.8f,-.8f,.25f}},{{.8f,-.8f,.25f}},{{.8f,.8f,.25f}},{{-.8f,.8f,.25f}}},{0,1,2,0,2,3});
 auto target=renderer.createRenderTarget(96,64,true);
 SceneFrame main;main.viewport={0,0,96,64};main.clear={0,0,0,1};renderer.begin(main);
 renderer.begin3DTarget(target,main);
 SceneMaterial red;red.unlit=true;red.toneMapped=false;red.color={1,0,0,1};red.doubleSided=true;
 renderer.draw(mesh,identity,identity,red);
 SceneMaterial green=red;green.color={0,1,0,1};auto behind=identity;behind[14]=.3f;renderer.draw(mesh,behind,identity,green);
 renderer.end3DTarget();
 SceneVertex a,b,c;a.position={-1,1,0};a.uv={0,0};b.position={1,1,0};b.uv={1,0};c.position={-1,-1,0};c.uv={0,1};
 auto polygon=renderer.createMesh({a,b,c},{0,1,2});renderer.compositeView(polygon,target);
 const auto pixels=renderer.readPixels();const auto at=[&](int x,int y,int channel){return pixels[(y*96+x)*4+channel];};
 assert(at(30,20,0)>245&&at(30,20,1)<5); // true offscreen depth occlusion survives composition
 assert(at(80,50,0)<5&&at(80,50,1)<5); // triangle clips the other half
 std::cout<<"offscreen 3D depth + GPU polygon composition PASS\n";
}
