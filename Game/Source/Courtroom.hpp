#pragma once
// 3D 학급 재판장 (docs/spec/15 §2) : 원형 증언대 16개, 빌보드 입상, 화자를 비추며 원을 따라 도는 카메라.
// 좌표 : 미터. 원의 중심이 원점, 0번 자리가 +Z 쪽(왕좌 맞은편), 시계 방향으로 22.5도씩.
#include <cmath>
#include <string>
namespace court {
constexpr float PI=3.14159265f;
constexpr float RADIUS=5.5f;      // 증언대 원 반지름
constexpr float CAMERA_DISTANCE=2.6f,CAMERA_HEIGHT=1.57f; // V3 실측 : 증언대 윗면이 화면 2/3, 머리가 위 20% 지점
constexpr float SPRITE_SIZE=2.3f,SPRITE_CENTER=1.25f;   // 입상(정사각) 크기·중심 높이
constexpr float PODIUM_W=1.7f,PODIUM_H=1.2f,PODIUM_INSET=.25f; // 키 비율 입상(작은 사람 153cm)도 얼굴이 가려지지 않는 높이 // 증언대는 입상보다 0.25m 안쪽
constexpr float FIELD_OF_VIEW=43.6f; // 초점거리 900px(1280×720) = debate::FOCAL 과 같은 원근
constexpr float FOCAL=900;
// 자리 순서(장 내내 고정)
constexpr const char* SEATS[16]{"mio","rin","ken","nana","taiga","ai","rei","sora","haruka","sho","koto","akari","riku","satsuki","yuu","kaede"};
inline int seatOf(const std::string& slug){for(int i=0;i<16;i++)if(slug==SEATS[i])return i;return -1;}
inline float seatAngle(int seat){return seat*22.5f;}
struct Shot{float x,y,z,yaw;};
// 화자 정면 샷 : 원 안쪽에서 바깥의 화자를 본다
inline Shot shot(float angleDeg){float a=angleDeg*PI/180,r=RADIUS-CAMERA_DISTANCE;return {r*std::sin(a),CAMERA_HEIGHT,r*std::cos(a),angleDeg+180};}
// 가까운 쪽으로 도는 각도 보간
inline float turn(float from,float to,float t){float d=std::fmod(to-from+540.f,360.f)-180.f;return from+d*t;}
// 화자 정면일 때 입상·증언대가 화면에 차지하는 사각형(UI 좌표, 1280×720)
struct Rect{float x,y,w,h;};
inline Rect project(float centerY,float w,float h,float distance=CAMERA_DISTANCE){float s=FOCAL/distance;float cy=360+(CAMERA_HEIGHT-centerY)*s;return {640-w*s/2,cy-h*s/2,w*s,h*s};}
inline Rect speakerRect(){return project(SPRITE_CENTER,SPRITE_SIZE,SPRITE_SIZE);}
inline Rect podiumRect(){return project(PODIUM_H/2,PODIUM_W,PODIUM_H,CAMERA_DISTANCE-PODIUM_INSET);}

// ── V3 식 카메라 : 대사마다 각도를 끊어 바꾸고(컷), 대사 동안 천천히 움직이며(드리프트), 화자가 바뀌면 원을 따라 휙 돈다(휩) ──
struct Cam{float x,y,z,yaw,pitch,roll;};
// 화자를 중심으로 phi 도 돌아간 자리에서 d 만큼 떨어져 높이 h 에서 화자를 본다(phi=0 이면 원 중심 쪽 정면 = shot())
inline Cam frame(float seatDeg,float phi,float d,float h,float pitch,float roll){
 float a=seatDeg*PI/180,sx=RADIUS*std::sin(a),sz=RADIUS*std::cos(a),ux=-std::sin(a),uz=-std::cos(a),p=phi*PI/180;
 float rx=ux*std::cos(p)-uz*std::sin(p),rz=ux*std::sin(p)+uz*std::cos(p),cx=sx+d*rx,cz=sz+d*rz;
 return {cx,h,cz,std::atan2(-(sx-cx),-(sz-cz))*180/PI,pitch,roll};
}
// 샷 : phi(시작→끝), 거리, 높이, 위아래, 기울기. 대사 하나 동안 시작 → 끝으로 천천히
struct ShotDef{float phi0,phi1,d0,d1,h0,h1,pitch,roll0,roll1;};
constexpr ShotDef SHOTS[8]{
 {0,0,2.6f,2.3f,1.57f,1.57f,0,0,0},          // 정면 밀고 들어가기
 {-15,-5,2.5f,2.4f,1.6f,1.6f,0,0,0},         // 오른쪽에서 돌아 들어가기
 {15,5,2.5f,2.4f,1.6f,1.6f,0,0,0},           // 왼쪽에서
 {-6,3,2.3f,2.15f,1.0f,1.05f,9,-7,-4},       // 아래에서 올려다보는 기운 샷
 {0,4,1.65f,1.45f,1.86f,1.86f,0,0,2},        // 얼굴 가까이
 {24,15,3.9f,3.6f,2.35f,2.3f,-9,0,0},        // 옆 사람까지 보이는 높은 원경
 {-28,28,2.8f,2.5f,1.62f,1.62f,0,-3,3},     // 논의 : 화자 둘레를 크게 돈다(V3 논스톱)
 {28,-28,2.8f,2.5f,1.62f,1.62f,0,3,-3}};
// 카메라 공간 → 화면(1280×720). roll 은 화면 가운데를 중심으로 돌린다
inline bool screen(const Cam& c,float px,float py,float pz,float& sx,float& sy,float& depth){
 float th=c.yaw*PI/180,ph=c.pitch*PI/180,vx=px-c.x,vy=py-c.y,vz=pz-c.z;
 float x=vx*std::cos(th)-vz*std::sin(th),f=-vx*std::sin(th)-vz*std::cos(th);
 float z=f*std::cos(ph)+vy*std::sin(ph),y=vy*std::cos(ph)-f*std::sin(ph);
 if(z<.2f)return false;
 float dx=x*FOCAL/z,dy=-y*FOCAL/z,r=c.roll*PI/180;
 sx=640+dx*std::cos(r)-dy*std::sin(r);sy=360+dx*std::sin(r)+dy*std::cos(r);depth=z;return true;
}
// 자리의 빌보드(가운데 높이 cy, 크기 w×h, 반지름 rad)가 화면에 그려지는 사각형
inline bool billboard(const Cam& c,int seat,float rad,float cy,float w,float h,Rect& out){
 float a=seatAngle(seat)*PI/180,sx,sy,z;
 if(!screen(c,rad*std::sin(a),cy,rad*std::cos(a),sx,sy,z))return false;
 float s=FOCAL/z;out={sx-w*s/2,sy-h*s/2,w*s,h*s};return true;
}
}
