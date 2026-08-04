# 🐾 ClaudePet — 데스크탑 고양이 펫

바탕화면 위에 복슬복슬 고양이가 살아요. 식빵 굽고, 살금살금 걷고, 먹이도 먹고, 말도 걸고 —
쓰다듬으면 좋아하고, 두 마리로도 볼 수 있어요. **백이**(흰 페르시안) & **깜이**(러시안블루).

> made by **[@ai_chobo_king](https://www.instagram.com/ai_chobo_king)**

## ⬇️ 다운로드 (파이썬 필요 없음)
- **[ClaudePet.exe 받기](../../releases/latest/download/ClaudePet.exe)** — 받아서 더블클릭하면 끝!
- 회사에서 `.exe` 다운로드가 막히면 → **[.bin 버전](../../releases/latest/download/ClaudePet_rename-to-exe.bin)** 받아 파일 이름 끝을 `.exe` 로 바꿔 실행
- 직접 뜯어보거나 캐릭터를 바꾸려면 → **[소스 zip](../../releases/latest/download/ClaudePet_source.zip)** (파이썬 필요)

> 처음 실행 시 'Windows의 PC 보호' 창이 뜨면 **추가 정보 → 실행**.

## 🐱 조작
- **이동**: 고양이 드래그
- **쓰다듬기**: 더블클릭 (또는 우클릭 메뉴)
- **우클릭 메뉴**: 대화하기 · 먹이주기 · 크기 줄이기 · 알림 지우기 · **백이만/깜이만/두마리 보기** · 펫 종료

## 🎨 나만의 캐릭터로 바꾸기
`sprites` 폴더의 PNG를 내가 만든 AI 이미지(투명 배경 권장)로 **덮어쓰기**만 하면 그 캐릭터가 돼요.
포즈별 파일: `baek_idle / _sleep / _crawl / _react / _eat / _happy .png` (짝꿍은 `kkam_*`).
exe로 쓸 땐 **exe 옆에 `sprites` 폴더**를 두면 그 이미지를 대신 써요.

## 🔔 (선택) Claude Code 작업 알림
`~/.claude/settings.json` 훅으로 작업 완료/확인 알림을 받을 수 있어요. 자세한 건 `SHARE.md` 참고.

## 만든 방법 가이드
👉 **[친절한 AI 가이드 페이지](https://aichoboking.github.io/claude-desktop-pet/)** (GitHub Pages)

---
Windows 전용 · Python + Pillow/numpy · © @ai_chobo_king
