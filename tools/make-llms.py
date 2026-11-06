#!/usr/bin/env python3
"""AI가 읽기 좋은 llms.txt(목차)와 llms-full.txt(원고 전체)를 만든다.

book/_quarto.yml 과 lab/_quarto.yml 의 목차 순서를 따른다.
    python3 tools/make-llms.py public/
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = "https://raw.githubusercontent.com/KREONET/osso/main/"
SITE = "https://kreonet.github.io/osso/"


def chapters(project):
    yml = (ROOT / project / "_quarto.yml").read_text()
    seen = []
    for m in re.finditer(r"^\s*-\s+(\S+\.qmd)\s*$", yml, re.M):
        f = m.group(1)
        if f not in seen and "*" not in f:
            seen.append(f)
    return seen


def title(path):
    for line in path.read_text().splitlines():
        if line.startswith("# "):
            return re.sub(r"\s*\{#[^}]+\}\s*$", "", line[2:]).strip()
    return path.stem


def main(out):
    out = Path(out)
    book = [f for f in chapters("book") if not f.startswith("labs/")]
    lab = chapters("lab")
    toc = ["# 오픈소스 안전운영 실습 (OSSO)", "",
           "> 연구망 KREONET의 교육 과정 자료. 책(본문 Part 1~7과 부록)과 실습 사이트(실습 ①~⑭, 지도, AI 프롬프트)로 나뉜다. "
           "실습 페이지는 🎯목표 → 🖥️랩 → ⌨️해보기 → 👀보이는 것 → 💡느낄 것 → 🔀갈림길 순이며, ⟨…⟩는 환경마다 다른 값이다.", "",
           f"- 원고 전체(한 파일): {SITE}llms-full.txt",
           "- 저장소: https://github.com/KREONET/osso (CLAUDE.md에 구조와 규칙)", ""]
    full = []
    for name, proj, files in [("책", "book", book), ("실습", "lab", lab)]:
        toc += [f"## {name}", ""]
        for f in files:
            p = ROOT / proj / f
            toc.append(f"- [{title(p)}]({RAW}{proj}/{f})")
            full += [f"\n\n<!-- {proj}/{f} -->\n", p.read_text()]
        toc.append("")
    out.mkdir(parents=True, exist_ok=True)
    (out / "llms.txt").write_text("\n".join(toc))
    (out / "llms-full.txt").write_text("".join(full))
    print(f"llms.txt, llms-full.txt → {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "public")
