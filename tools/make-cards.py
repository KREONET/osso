#!/usr/bin/env python3
"""카드 이미지 생성기.

cards/cards.toml 의 카드마다 cards/template.html 을 채워 헤드리스 Chrome으로 PNG를 찍는다.
결과는 cards/_out/ 에 PNG와 미리보기 페이지(index.html)로 남는다.

    python3 tools/make-cards.py            # Chrome 경로를 자동으로 찾는다
    CHROME=/path/to/chrome python3 tools/make-cards.py
"""
import html
import os
import shutil
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "cards"
OUT = CARDS / "_out"
SIZES = {
    "square": dict(W=1080, H=1080, PAD=96, KICK=34, TITLE=76, BODY=38),
    "og": dict(W=1200, H=630, PAD=72, KICK=28, TITLE=64, BODY=32),
}


def chrome():
    for c in [os.environ.get("CHROME"), "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]:
        if c and shutil.which(c):
            return shutil.which(c)
    raise SystemExit("Chrome을 찾지 못했습니다. CHROME 환경변수로 경로를 지정하세요.")


def main():
    spec = tomllib.loads((CARDS / "cards.toml").read_text())
    tpl = (CARDS / "template.html").read_text()
    OUT.mkdir(exist_ok=True)
    exe = chrome()
    items = []
    for card in spec["card"]:
        size = SIZES[card["size"]]
        page = tpl
        for k, v in size.items():
            page = page.replace("{{%s}}" % k, str(v))
        for k, field in [("KICKER", "kicker"), ("TITLE_TEXT", "title"), ("BODY_TEXT", "body"), ("LINK", "link")]:
            page = page.replace("{{%s}}" % k, html.escape(card.get(field, "")))
        src = OUT / f"{card['id']}.html"
        png = OUT / f"{card['id']}.png"
        src.write_text(page)
        subprocess.run([
            exe, "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--force-device-scale-factor=1", f"--window-size={size['W']},{size['H']}",
            "--virtual-time-budget=5000", f"--screenshot={png}", src.as_uri(),
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        src.unlink()
        items.append((card, png.name))
        print("card", png.name)
    rows = "\n".join(
        f'<figure><a href="{n}" download><img src="{n}" alt="{html.escape(c["title"])}"></a>'
        f'<figcaption>{html.escape(c["kicker"])} · {c["size"]}</figcaption></figure>'
        for c, n in items)
    (OUT / "index.html").write_text(f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>OSSO 카드</title>
<style>body{{font-family:sans-serif;margin:24px;background:#f5f7fa}}main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px}}
img{{width:100%;border-radius:8px;box-shadow:0 2px 8px #0002}}figcaption{{font-size:14px;color:#555;margin-top:6px}}</style></head>
<body><h1>OSSO 카드</h1><p>이미지를 누르면 원본(PNG)을 내려받습니다. 원고는 <code>cards/cards.toml</code>에 있습니다.</p><main>{rows}</main></body></html>""")


if __name__ == "__main__":
    main()
