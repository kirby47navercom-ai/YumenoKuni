#pragma once
#include <HBEngine/Game.hpp>
#include <algorithm>
#include <array>
#include <map>
#include <set>
#include <string>
#include <vector>

namespace keybindv4 {
struct Action {const char* key;const char* name;const char* description;};
inline const std::vector<Action>& Actions(){
 static const std::vector<Action> a{
  {"w","앞으로 / 위 항목","탐색에서는 앞으로 이동하고, 목록에서는 위 항목을 골라요."},
  {"s","뒤로 / 아래 항목","탐색에서는 뒤로 이동하고, 목록에서는 아래 항목을 골라요."},
  {"a","왼쪽 이동 / 이전","탐색 이동 방식에 따라 옆으로 이동하거나 회전해요. 목록에서는 이전 항목을 골라요."},
  {"d","오른쪽 이동 / 다음","탐색 이동 방식에 따라 옆으로 이동하거나 회전해요. 목록에서는 다음 항목을 골라요."},
  {"Shift","달리기","탐색에서 이동키와 함께 누르고 있으면 달려요."},
  {"e","조사 / 다음 탄환","탐색에서는 가리키는 대상을 조사해요. 논스톱·패닉에서는 다음 코토다마를 골라요."},
  {"m","지도 / 조사 목록","자유 이동 중에는 지도를, 수사 중에는 조사할 장소 목록을 열어요."},
  {"Tab","전자수첩 / 패널","탐색·대사·재판에서 전자수첩을 열거나 닫아요. 미니게임에서는 해당 패널을 열어요."},
  {"r","집중 / 돌아가기","탐색·논스톱에서는 집중해요. 전자수첩에서는 이전 화면으로 돌아가요."},
  {"Control","읽은 대사 넘기기","누르고 있는 동안 이미 읽은 대사를 빠르게 넘겨요."},
  {"Enter","결정 / 대사 계속","선택을 결정하거나 다음 대사를 읽어요. 긴 대사는 다음 페이지부터 보여요."},
  {"Space","대사 계속 / 미니게임","대사를 넘기고, 미니게임에서는 화면에 표시된 동작을 실행해요."},
  {"q","이전 탄환 / 이전 쪽","재판에서는 이전 코토다마나 패널을, 전자수첩에서는 이전 쪽을 골라요."},
  {"f","문제 다시 보기","인물·지점·증거·정답을 고르는 재판에서 문제를 다시 보거나 닫아요."},
  {"g","선물 목록","대화 선택 화면에서 선물 목록을 열어요."},
  {"c","이어하기 / 카드 목록","타이틀에서는 이어하기를, 대화 선택 화면에서는 카드 목록을 열어요."},
  {"l","대화 기록","재판 중에 지나간 대화 기록을 열거나 닫아요."},
  {"o","환경설정","타이틀·재판에서 환경설정을 열어요."},
  {"z","결정 보조","전자수첩과 해당 미니게임에서 선택을 결정해요."},
  {"x","취소 보조","전자수첩에서 이전 화면으로 돌아가거나 미니게임의 취소 동작을 해요."},
  {"ArrowUp","시선 위 / 위 선택","탐색 시선을 위로 움직여요. 목록과 미니게임에서는 위쪽을 골라요."},
  {"ArrowDown","시선 아래 / 아래 선택","탐색 시선을 아래로 움직여요. 목록과 미니게임에서는 아래쪽을 골라요."},
  {"ArrowLeft","시선 왼쪽 / 왼쪽 선택","탐색 시선을 왼쪽으로 움직여요. 목록과 미니게임에서는 왼쪽을 골라요."},
  {"ArrowRight","시선 오른쪽 / 오른쪽 선택","탐색 시선을 오른쪽으로 움직여요. 목록과 미니게임에서는 오른쪽을 골라요."},
  {"mouse0","클릭 / 발사","화면의 항목을 누르거나 대사를 넘겨요. 논스톱·패닉에서는 코토다마를 발사해요."},
  {"mouse1","둘러보기 / 소음기","탐색에서는 누른 채 마우스를 움직여 둘러봐요. 논스톱·패닉에서는 잡음을 지워요."},
  {"mouse2","다음 코토노하","반론 쇼다운에서 다음 코토노하를 골라요."},
  {"F1","획득 목록","뽑기 화면에서 획득 목록을 열어요."},
  {"F3","도움말","뽑기 화면에서 도움말을 열거나 닫아요."},
  {"1","선택지 1","현재 목록의 첫 번째 항목을 바로 골라요."},
  {"2","선택지 2","현재 목록의 두 번째 항목을 바로 골라요."},
  {"3","선택지 3","현재 목록의 세 번째 항목을 바로 골라요."},
  {"4","선택지 4","현재 목록의 네 번째 항목을 바로 골라요."},
  {"5","선택지 5","현재 목록의 다섯 번째 항목을 바로 골라요."},
  {"6","선택지 6","현재 목록의 여섯 번째 항목을 바로 골라요."},
  {"7","선택지 7","현재 목록의 일곱 번째 항목을 바로 골라요."},
  {"8","선택지 8","현재 목록의 여덟 번째 항목을 바로 골라요."},
  {"9","선택지 9","현재 목록의 아홉 번째 항목을 바로 골라요."}
 };return a;
}
using Bindings=std::map<std::string,std::string>;
inline Bindings Defaults(){Bindings b;for(const auto& a:Actions())b[a.key]=a.key;return b;}
inline const std::vector<std::string>& Candidates(){static const auto keys=[](){std::vector<std::string> out;for(char c='a';c<='z';++c)out.emplace_back(1,c);for(char c='0';c<='9';++c)out.emplace_back(1,c);for(const char* k:{"Enter","Space","Tab","Shift","Control","Alt","ArrowUp","ArrowDown","ArrowLeft","ArrowRight","mouse0","mouse1","mouse2"})out.emplace_back(k);for(int i=1;i<=12;++i)out.push_back("F"+std::to_string(i));return out;}();return keys;}
inline bool Valid(const Bindings& b){if(b.size()!=Actions().size())return false;std::set<std::string> used;for(const auto& a:Actions()){auto at=b.find(a.key);if(at==b.end()||std::find(Candidates().begin(),Candidates().end(),at->second)==Candidates().end()||!used.insert(at->second).second)return false;}return true;}
inline std::string Label(const std::string& key){static const std::map<std::string,std::string> labels{{"mouse0","마우스 왼쪽"},{"mouse1","마우스 오른쪽"},{"mouse2","마우스 가운데"},{"ArrowUp","↑"},{"ArrowDown","↓"},{"ArrowLeft","←"},{"ArrowRight","→"},{"Control","Ctrl"}};auto at=labels.find(key);if(at!=labels.end())return at->second;if(key.size()==1&&key[0]>='a'&&key[0]<='z')return std::string(1,char(key[0]-'a'+'A'));return key;}
inline Bindings active=Defaults();
inline bool enabled=true;
inline std::string Physical(const std::string& canonical){auto it=active.find(canonical);return enabled&&it!=active.end()?it->second:canonical;}
inline hb::Json Encode(const Bindings& b){return hb::Json(b);}
inline Bindings Decode(const hb::Json& j){Bindings b=Defaults();if(!j.is_object())return b;for(const auto& a:Actions()){auto at=j.find(a.key);if(at!=j.end()){if(!at->is_string())return Defaults();b[a.key]=at->get<std::string>();}}return Valid(b)?b:Defaults();}
}
