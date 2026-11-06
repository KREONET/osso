#!/usr/bin/env bash
# 전체 사이트를 빌드해 public/ 에 모은다.
#   public/         첫 화면(home)
#   public/book/    책 (HTML, EPUB)
#   public/lab/     실습 사이트
#   public/slide/   슬라이드
#   public/cards/   카드 이미지
# 사용: tools/build.sh            (quarto가 PATH에 있어야 한다)
#       QUARTO=/path/to/quarto tools/build.sh
set -euo pipefail
cd "$(dirname "$0")/.."
Q=${QUARTO:-quarto}

python3 tools/sync-labs.py
python3 tools/make-index.py

for p in home book lab slide; do
  echo "== render $p"
  (cd "$p" && "$Q" render)
done

echo "== cards"
python3 tools/make-cards.py

rm -rf public
mkdir -p public
cp -r home/_site/. public/
cp -r book/_book public/book
cp -r lab/_site public/lab
cp -r slide/_site public/slide
cp -r cards/_out public/cards
python3 tools/make-llms.py public
touch public/.nojekyll
echo "== done: public/"
