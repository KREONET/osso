# OSSO — 오픈소스 안전운영 실습

**서버와 서비스를 맡게 된 사람을 위한 손으로 익히는 보안**

연구망 [KREONET](https://www.kreonet.net)의 교육 과정 OSSO(오픈소스 서버·서비스 안전운영 실습) 자료입니다.

| | 주소 |
| --- | --- |
| 첫 화면 | <https://kreonet.github.io/osso/> |
| 📖 책 (HTML·EPUB) | <https://kreonet.github.io/osso/book/> |
| 🧪 실습 | <https://kreonet.github.io/osso/lab/> |
| 🖥️ 슬라이드 | <https://kreonet.github.io/osso/slide/> |
| 🖼️ 카드 | <https://kreonet.github.io/osso/cards/> |

## 혼자 공부하기 — AI와 함께

```bash
git clone https://github.com/KREONET/osso
cd osso
# 또는 쓰는 AI 코딩 도구
claude
```

AI는 `CLAUDE.md`(다른 도구는 `AGENTS.md`)를 읽고 시작합니다. "내 상황에 맞는 경로를 같이 고르자"라고 말해 보세요. 만든 결과물은 `my/`에 쌓이고 커밋되지 않습니다.

## 빌드

[Quarto](https://quarto.org) 1.11 이상과 Python 3.11 이상, Chrome(카드 이미지)이 필요합니다.

```bash
# public/ 에 전체 사이트를 만든다
tools/build.sh
# 책만 미리 보기
python3 tools/sync-labs.py && cd book && quarto preview
```

`main`에 push하면 GitHub Actions가 빌드해 GitHub Pages에 배포합니다. 구조와 원고 규칙은 [CLAUDE.md](CLAUDE.md)에 있습니다.
