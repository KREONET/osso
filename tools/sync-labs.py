#!/usr/bin/env python3
"""실습 원고(lab/labs/)를 책의 부록 자리(book/labs/)로 복사한다.

실습 원고는 lab/labs/ 한 곳에만 둔다. 책을 빌드하기 전에(pre-render) 이 스크립트가
복사본을 만든다. book/labs/ 는 .gitignore에 들어 있으니 그곳을 고치지 않는다.
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src, dst = ROOT / "lab" / "labs", ROOT / "book" / "labs"
if dst.exists():
    shutil.rmtree(dst)
shutil.copytree(src, dst)
print(f"synced {len(list(dst.glob('*.qmd')))} lab files → book/labs/")
