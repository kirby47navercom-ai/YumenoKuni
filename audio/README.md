# audio — 사운드 슬롯

* `cues.json`에 게임이 쓰는 BGM 31종·SFX 19종의 **ID·용도**가 들어 있다. 각 항목의 `file`에 이 폴더 안의 파일 이름을 적으면 게임이 그 소리를 쓴다. 비어 있으면 무음으로 진행한다.
* 파일 형식 : `.ogg`(권장) / `.mp3` / `.wav`. 루프 BGM은 끊김 없는 루프 구간으로 자른다.
* 예 : `"bgm_trial_nonstop": {"file": "trial/nonstop.ogg"}`
* 처형 영상 도구는 `audio/bgm_exec_{장}.ogg`가 있으면 자동으로 깐다.

## 주의
* 이 폴더의 음원 파일(`ogg/mp3/wav/flac`)은 `.gitignore`로 **저장소에 올라가지 않는다**. 다른 게임의 음원은 개인 소장본에서만 쓰고, 저장소·배포본에 넣지 않는다.
