#pragma once
// 3D 학급 재판장 (docs/spec/15 §2) : 원형 증언대 16개, 빌보드 입상, 화자를 비추며 원을 따라 도는 카메라.
// 좌표 : 미터. 원의 중심이 원점, 0번 자리가 +Z 쪽(왕좌 맞은편), 시계 방향으로 22.5도씩.
#include <cmath>
#include <algorithm>
#include <string>
namespace court {
constexpr float PI=3.14159265f;
constexpr float RADIUS=4.08f;     // Feet inside the open station: .13m behind its3.95m ring centre.
constexpr float CAMERA_DISTANCE=2.6f,CAMERA_HEIGHT=1.57f; // Authored framing in our room units.
constexpr float SPRITE_SIZE=2.3f,SPRITE_CENTER=1.25f;   // 입상(정사각) 크기·중심 높이
constexpr float PODIUM_W=1.36f,PODIUM_H=1.26f,PODIUM_INSET=.13f;
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
struct Rotation{float x,y,z;};
inline Rotation engineRotation(const Cam& c){
 // Logical camera is yaw->local pitch->roll (YXZ); scene transforms consume XYZ Euler.
 float x=c.pitch*PI/180,y=c.yaw*PI/180,z=c.roll*PI/180;
 float sx=std::sin(x),cx=std::cos(x),sy=std::sin(y),cy=std::cos(y),sz=std::sin(z),cz=std::cos(z);
 float m11=cy*cz+sy*sx*sz,m12=-cy*sz+sy*sx*cz,m13=sy*cx;
 float m22=cx*cz,m23=-sx,m32=sy*sz+cy*sx*cz,m33=cy*cx;
 float ey=std::asin(std::clamp(m13,-1.f,1.f)),ex,ez;
 if(std::abs(m13)<.9999999f){ex=std::atan2(-m23,m33);ez=std::atan2(-m12,m11);}
 else{ex=std::atan2(m32,m22);ez=0;}
 return {ex*180/PI,ey*180/PI,ez*180/PI};
}
// User GIF: dark eye-level sweep, cut above the entire ring, level orbital descent, then START/dolly.
// This framing is reference-matched to our room, not inferred from raw camera-row angles alone.
constexpr float NONSTOP_CUT=.9f,NONSTOP_SWEEP=4.65f,NONSTOP_FOCUS=.85f;
inline float nonstopLoadDuration(int count){return .65f+(110+20*std::clamp(count,1,9))/60.f;}
inline float nonstopFocusStart(int count){return NONSTOP_SWEEP+nonstopLoadDuration(count);}
inline float nonstopDuration(int count){return nonstopFocusStart(count)+NONSTOP_FOCUS;}
// Reference-adapted motion: native mode2 target ordering, not a literal clock conversion.
inline float smooth5(float u){u=std::clamp(u,0.f,1.f);return std::clamp(u*u*u*(10+u*(-15+6*u)),0.f,1.f);}
inline float nonstopSeatOffset(int seat,float seconds){
 // Begin after the blackout: the actual desks must visibly change rows.
 const float times[]{.9f,1.8f,3.1f,4.5f},values[]{0,.70f,-.70f,0};
 float t=std::clamp(seconds,.9f,4.5f);int i=0;while(i<2&&t>times[i+1])i++;
 float d=values[i]+(values[i+1]-values[i])*smooth5((t-times[i])/(times[i+1]-times[i]));
 return (seat%2?-1.f:1.f)*d;
}
// Supplied video07:07-07:17: wide sweep, eye-level charge scan with large cylinder, first speaker.
inline Cam nonstopIntro(int seat,float seconds,int bullets=5){
 float first=seat==-2?180.f:seatAngle(seat),target=first+225;
 if(seconds<NONSTOP_CUT){
  float u=smooth5(seconds/NONSTOP_CUT),q=(target+150-110*u)*PI/180,r=RADIUS-CAMERA_DISTANCE;
  return {r*std::sin(q),CAMERA_HEIGHT,r*std::cos(q),q*180/PI+180,0,0};
 }
 float u=std::clamp((seconds-NONSTOP_CUT)/(NONSTOP_SWEEP-NONSTOP_CUT),0.f,1.f),s=smooth5(u);
 if(seconds>=NONSTOP_SWEEP){
  float scan=std::clamp((seconds-NONSTOP_SWEEP)/nonstopLoadDuration(bullets),0.f,1.f);
  // 언령 장전은 첫 화자 앞에서(주인님 지시 2026-11-05 : 첫 증언 직전에 생겨야 한다). 남을 훑는 동안 목록을 띄우지 않는다
  float arrive=smooth5(std::min(1.f,scan*4)),from=target-360,viewed=from+(first+8-from)*arrive-8*scan*arrive; /* 짧은 쪽(143°)으로 돌아 첫 화자에 닿고 장전 내내 천천히 다가간다 */
  if(seconds>=nonstopFocusStart(bullets))viewed=first;
  const float hostFocus=seat==-2?smooth5((seconds-nonstopFocusStart(bullets))/NONSTOP_FOCUS):0.f;
  float q=viewed*PI/180,r=(RADIUS-CAMERA_DISTANCE)*(1-.8f*hostFocus);
  return {r*std::sin(q),CAMERA_HEIGHT+.48f*hostFocus,r*std::cos(q),viewed+180,24.f*hostFocus,0};
 }
 // Spiral from above the near side into the ring, never through its centre.
 // Aim along the visible row rather than at one fixed seat throughout the orbit.
 float yaw=target+450-270*u,bearing=180*smooth5((u-.4f)/.6f),theta=yaw-bearing,angle=theta*PI/180;
 float r=6.8f+(RADIUS-CAMERA_DISTANCE-6.8f)*s;
 float dot=-r*std::cos((yaw-theta)*PI/180);
 float distance=-dot+std::sqrt(std::max(0.f,dot*dot+RADIUS*RADIUS-r*r));
 float pitch=-42*(1-s),h=CAMERA_HEIGHT+distance*std::tan(-pitch*PI/180);
 return {r*std::sin(angle),h,r*std::cos(angle),yaw,pitch,0};
}
// 화자를 중심으로 phi 도 돌아간 자리에서 d 만큼 떨어져 높이 h 에서 화자를 본다(phi=0 이면 원 중심 쪽 정면 = shot())
inline Cam frame(float seatDeg,float phi,float d,float h,float pitch,float roll){
 float a=seatDeg*PI/180,sx=RADIUS*std::sin(a),sz=RADIUS*std::cos(a),ux=-std::sin(a),uz=-std::cos(a),p=phi*PI/180;
 float rx=ux*std::cos(p)-uz*std::sin(p),rz=ux*std::sin(p)+uz*std::cos(p),cx=sx+d*rx,cz=sz+d*rz;
 return {cx,h,cz,std::atan2(-(sx-cx),-(sz-cz))*180/PI,pitch,roll};
}
// 샷 : phi(시작→끝), 거리, 높이, 위아래, 기울기. 대사 하나 동안 시작 → 끝으로 천천히
struct ShotDef{float phi0,phi1,d0,d1,h0,h1,pitch,roll0,roll1;};
constexpr ShotDef SHOTS[12]{
 {0,0,2.6f,2.3f,1.57f,1.57f,0,0,0},          // 정면 밀고 들어가기
 {-15,-5,2.5f,2.4f,1.6f,1.6f,0,0,0},         // 오른쪽에서 돌아 들어가기
 {15,5,2.5f,2.4f,1.6f,1.6f,0,0,0},           // 왼쪽에서
 {-6,3,2.3f,2.15f,1.0f,1.05f,9,-7,-4},       // 아래에서 올려다보는 기운 샷
 {0,4,1.65f,1.45f,1.86f,1.86f,0,0,2},        // 얼굴 가까이
 {24,15,3.9f,3.6f,2.35f,2.3f,-9,0,0},        // 옆 사람까지 보이는 높은 원경
 {-28,28,2.8f,2.5f,1.62f,1.62f,0,-3,3},     // 논의 : 화자 둘레를 크게 돈다(V3 논스톱)
 {28,-28,2.8f,2.5f,1.62f,1.62f,0,3,-3},
 // 논스톱(V3 영상 A 16:28~17:16) : 화자 혼자가 아니라 옆자리 사람들까지 함께 잡고 쉬지 않고 움직인다
 {-18,-6,3.4f,3.1f,1.15f,1.2f,6,0,-2},       // 낮은 원경 : 화자는 크게, 양옆 두세 명(V3 영상 A 16:36)
 {30,18,6.4f,6.0f,3.6f,3.4f,-24,0,0},         // 위에서 내려다보는 재판장 전체(16:28)
 {42,32,3.6f,3.2f,.85f,.9f,11,6,4},           // 낮은 옆에서 기울여 올려다봄(16:44)
 {-8,4,2.0f,1.75f,1.55f,1.55f,2,-9,-6}};      // 기운 클로즈업(16:52)
// Nonstop framing alternates eye-level passes, high group views and close reactions.
constexpr ShotDef NONSTOP_SHOTS[12]{
 {0,0,3.4f,2.8f,1.72f,1.72f,0,0,0},
 {-33,-17,4.0f,3.5f,1.78f,1.78f,0,-3,0},
 {33,17,4.0f,3.5f,1.78f,1.78f,0,3,0},
 {-30,-18,5.5f,5.0f,3.5f,3.35f,-18,-3,0},
 {6,0,2.65f,2.25f,1.78f,1.78f,0,0,1},
 {28,17,5.5f,5.1f,3.35f,3.2f,-17,0,0},
 {-34,-6,3.9f,3.35f,1.78f,1.72f,0,-3,0},
 {34,6,3.9f,3.35f,1.78f,1.72f,0,3,0},
 {-16,3,4.2f,3.65f,1.72f,1.72f,0,0,-2},
 {28,17,6.5f,6.0f,4.0f,3.8f,-21,0,0},
 {34,23,4.3f,3.65f,1.44f,1.48f,4,4,2},
 {-9,2,2.85f,2.3f,1.78f,1.78f,0,-5,-2}
};
constexpr float NONSTOP_WHIP_SECONDS=.32f;
inline Cam nonstopWhip(const Cam& from,const Cam& to,float u){
 const float fromBearing=std::atan2(from.x,from.z)*180/PI;
 const float toBearing=std::atan2(to.x,to.z)*180/PI;
 const float sweep=std::remainder(toBearing-fromBearing,360.f);
 const float orbit=fromBearing+sweep*u;
 const float bearing=orbit*PI/180;
 const float yawTurn=std::remainder(to.yaw-from.yaw,360.f);
 const float lift=std::sin(u*PI);
 auto mix=[u](float a,float b){return a+(b-a)*u;};
 const float radius=mix(std::hypot(from.x,from.z),std::hypot(to.x,to.z))-.40f*lift;
 return {radius*std::sin(bearing),mix(from.y,to.y)+.16f*lift,radius*std::cos(bearing),
         from.yaw+yawTurn*u,mix(from.pitch,to.pitch),
         mix(from.roll,to.roll)+std::clamp(sweep/36.f,-2.5f,2.5f)*lift};
}
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
