# V3 설치본 분석 도구

원본은 읽고 상세 분석물은 저장소 밖에 써요. 코드·수치·분석 문서만 저장소에 둬요.

## 전수 재현

PowerShell, 저장소 루트 기준이에요. 새 출력 폴더를 사용해요.

```powershell
python tools/re/catalog.py 'C:/Program Files (x86)/Steam/steamapps/common/Danganronpa V3 Killing Harmony/data/win' 'C:/Users/kirby/Downloads/v3_re/inventory'
python tools/re/scan_scripts.py 'C:/Users/kirby/Downloads/v3_re/inventory' 'C:/Users/kirby/Downloads/v3_re/repro_script_scan_new' --trial-data
python tools/re/scan_resources.py 'C:/Users/kirby/Downloads/v3_re/inventory' 'C:/Users/kirby/Downloads/v3_re/repro_resource_scan_new'
python tools/re/scan_audio.py 'C:/Users/kirby/Downloads/v3_re/inventory' 'C:/Users/kirby/Downloads/v3_re/repro_audio_scan_new'
python -m unittest discover -s tools/re -p 'test_*.py'
```

catalog는 CPK 전체 SHA와 컨테이너를 읽고, 각 scanner는 필요한 SPC 본문을 해독해요. 이전 결과를 새 parser의 성공 결과로 재사용하지 않아요. 각 summary의 분모·complete/exhausted·error·unsupported/partial을 함께 확인해요.

| 도구 | 역할 |
|---|---|
| cpk.py / catalog.py | UTF·CPK·CRILAYLA, 경로/범위, SPC 전체/중첩 원장 |
| spc.py | SPC 압축과 멤버 |
| stx.py / wrd.py | STXT 문자열/ID·대본 명령/인자/참조/오프셋. RSC 별도 dialect |
| dat.py / trial_data.py / map_data.py | typed·논의·스타일·맵/스테이지/상태·애니메이션 변형 |
| srd.py / sfl.py | 리소스·메시·충돌·트리, UI 실제 native payload |
| font.py | 폰트 STX의 SpFt 글리프·간격·atlas 범위 |
| audio.py / scan_audio.py | 큐 참조·AWB 색인·HCA 샘플/루프. 음원/PCM 출력 없음 |
| vis.py | VIS의8채널 값 범위·헤더·루프 metadata. 원본 프레임 배열 출력 없음 |
| movie.py / extra_formats.py | MP4 metadata·SAN/PPP/RSCT 구조 |
| steamstub.py | 코드 영역 정적 복원과 provenance. 사본은 분석 전용 |

단일 파일 명령은 각 도구의 `--help`를 확인해요. `.stx`는 문자열 표와 폰트 형식이 모두 있어요. 공개 소스는 직접 읽고 자체 파서를 작성했으며 commit/경로는 각 모듈과 분석 문서에 기록했어요. 원본 구조 검사와 실제 플레이 동작 검증은 별개예요.
