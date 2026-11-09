# V5 개발 빌드

이 저장소에는 개정 원고, 게임 코드, 생성 도구, 개정판 자체 사건·만화·이론무장 자원을 보관한다. Windows 게임 실행 파일과 검사 저장은 로컬 산출물이다.

전체 게임을 다시 만들 때는 기존 프로젝트의 로컬 미술 은행(`art/space_v4`, `art/v4_production`, `art/hd_v4` 등), 제공받은 UI 은행(`ui/v3_authorized`, `ui/v4`), 음원과 이 프로젝트와 호환되는 `../engineCreate` SDK가 필요하다. 이 저장소만 복제하면 전체 자원과 SDK가 갖춰지지는 않는다. 기존에 승인된 렌더 실행기와 셰이더 위치는 `HANDOFF.md`의 빌드 절차를 따른다.

```powershell
python -X utf8 tools/build_v4_story.py
python -X utf8 tools/verify_revised_story_paths.py
Set-Location Game
node tools/create-project.mjs --revised-campaign
node tools/build.mjs
```

마지막 명령에는 현재 사용 중인 SDK 및 실행기 조합에 따라 `--engine-root`, `--native-player`를 지정한다. `Game/Assets`는 생성 결과다. V5를 선택한 빌드는 새 게임부터 V5를 사용하고 기존 V4 저장은 별도 슬롯에 남긴다.
