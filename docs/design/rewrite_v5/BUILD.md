# V5 개발 빌드

이 저장소에는 개정 원고, 게임 코드, 생성 도구, 개정판 자체 사건·만화·이론무장 자원을 보관한다. Windows 게임 실행 파일과 검사 저장은 로컬 산출물이다.

게임 코드와 원고, 제작 도구, 현재 생성에 필요한 자체 모델·인물·사건 그림은 Git에서 관리한다. 검수 중 발견한 문제와 원고 구간 색인은 `docs/analysis/v5_prose_polish_20261110/`에 있다.

전체 게임을 다시 만들 때는 제공받은 UI 은행(`ui/v3_authorized`와 원작을 참조하는 별도 클라이맥스 UI 입력), 로컬 음원, 호환되는 `../engineCreate` SDK를 함께 준비한다. Blender 편집 원본, 중간 모델, 원작 입력, 빌드 및 플레이 저장은 로컬 보관 대상이다. 기존에 승인된 렌더 실행기와 셰이더 위치는 `HANDOFF.md`의 빌드 절차를 따른다.

새 체크아웃에서 대본 분기만 확인할 때는 저장소 루트에서 `python -X utf8 tools/verify_revised_story_paths.py`를 실행한다. 아래 전체 빌드는 입력 은행을 갖춘 개발 환경에서 수행한다.

```powershell
python -X utf8 tools/build_v4_story.py
python -X utf8 tools/verify_revised_story_paths.py
Set-Location Game
node tools/create-project.mjs --revised-campaign
node tools/build.mjs
```

마지막 명령에는 현재 사용 중인 SDK 및 실행기 조합에 따라 `--engine-root`, `--native-player`를 지정한다. `Game/Assets`는 생성 결과다. V5를 선택한 빌드는 새 게임부터 V5를 사용하고 기존 V4 저장은 별도 슬롯에 남긴다.
