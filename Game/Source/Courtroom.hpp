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
constexpr float PODIUM_W=1.7f,PODIUM_H=1.45f,PODIUM_INSET=.25f; // 증언대는 입상보다 0.25m 안쪽
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
}
