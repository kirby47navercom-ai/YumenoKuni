# V5 개발 빌드

이 저장소에는 개정 원고, 게임 코드, 생성 도구, 개정판 자체 사건·만화·이론무장 자원을 보관한다. Windows 게임 실행 파일과 검사 저장은 로컬 산출물이다.

게임 코드, 원고, 제작 도구, 빌드에 쓰는 그림·UI·음원과 HBEngine 빌드 입력은 Git에서 관리한다. 검수 중 발견한 문제와 원고 구간 색인은 `docs/analysis/v5_prose_polish_20261110/`에 있다.

Windows x64에서 Node.js 24와 npm, Python 3, MSYS2 UCRT64 C++ 컴파일러가 필요하다. 기본 컴파일러는 MSYS2 기본 설치에서 자동으로 찾으며 별도 도구 체인은 환경 변수 `CXX`로 선택할 수 있다.

새 체크아웃의 저장소 루트에서 아래 명령을 실행한다. 첫 실행은 고정된 SDK 원본과 호환 렌더 입력을 `Game/engineCreate`에 펼치고 npm 의존성을 설치한다. 이후 생성기와 빌드는 이 경로를 사용한다.

```powershell
python -m pip install Pillow numpy fonttools
node Game/tools/build-checkout.mjs
```

`Game/Assets`는 생성 결과다. Windows 실행 파일 위치는 `Game/build-result.json`에 기록한다. 대본 분기만 확인할 때는 `python -X utf8 tools/verify_revised_story_paths.py`를 실행한다. V5 빌드는 새 게임부터 V5를 사용하고 기존 V4 저장은 별도 슬롯에 남긴다.
