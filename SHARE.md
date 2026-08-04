# 🐾 데스크탑 펫 공유 / 다른 컴퓨터에서 실행하기

## 무엇을 공유하면 되나 (꼭 필요한 것)
아래 파일/폴더만 있으면 다른 컴퓨터에서 그대로 돌아가요 (경로는 상대경로라 어디에 둬도 OK):

```
desktop-pet/
├─ pet.pyw          ← 펫 본체
├─ pet_notify.py    ← 알림 신호 스크립트
├─ pet_start.bat    ← 실행 (더블클릭)
├─ sprites/         ← 캐릭터 이미지 전부 (필수!)
│   ├─ baek_*.png   (백이: idle/sleep/crawl/crawl_r/react/eat/happy)
│   ├─ kkam_*.png   (깜이: 동일)
│   ├─ food.png, bowl.png
└─ README.md / SHARE.md (설명, 선택)
```

**안 보내도 되는 것:** `_matte/`, `_src/`(원본·중간 파일), `pet_event.json`, `pet_error.log`,
`__pycache__/`, `build_sprites.py`(스프라이트 다시 만들 때만 필요).

→ `ClaudePet_share.zip` 으로 묶어놨으니 이 파일 하나만 보내면 돼요.

## 받는 컴퓨터에서 설치 (Windows)
1. **Python 3 설치** (python.org). 설치 시 "Add Python to PATH" 체크.
2. 필요한 패키지 2개:
   ```
   pip install pillow numpy
   ```
3. zip 풀고 → **`pet_start.bat` 더블클릭** → 오른쪽 아래에 백이/깜이 등장!

> Windows 전용이에요 (투명 오버레이·소리에 Windows API 사용).
> 한글 폰트(맑은 고딕)는 Windows에 기본 포함이라 그대로 나와요.

## (선택) Claude Code 작업 알림까지 쓰려면
그 컴퓨터에서도 Claude Code 작업 알림을 받고 싶다면, 그 PC의
`~/.claude/settings.json` 에 훅을 추가 (경로는 펫을 둔 위치로):
```json
"hooks": {
  "UserPromptSubmit": [
    { "hooks": [ { "type": "command",
      "command": "python \"<펫경로>\\pet_notify.py\" clear" } ] }
  ]
}
```
그리고 작업 완료/확인요청 시 Claude가:
`python "<펫경로>\pet_notify.py" done|waiting|check "메시지" "주제명"` 를 실행.
펫만 띄워서 쓰는 거면 이 부분은 없어도 돼요.

## (선택) 부팅 시 자동 실행
`Win+R` → `shell:startup` → 열린 폴더에 `pet_start.bat` **바로가기** 넣기.

## 조작
- 드래그 이동 / 더블클릭·우클릭 쓰다듬기 / 우클릭 메뉴: 대화·먹이·백이↔깜이 전환·종료
