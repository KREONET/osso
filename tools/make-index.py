#!/usr/bin/env python3
"""찾아보기(색인) 생성기.

용어집(book/F-glossary.qmd)의 표제어와 tools/index-extra.txt의 추가 표제어를
본문에서 찾아, 그 용어가 나오는 절로 가는 링크를 모아 book/Z-index.qmd를 만든다.
한글 표제어는 가나다순, 영문 표제어는 ABC순, 숫자·기호는 맨 앞.

    python3 tools/make-index.py

용어를 용어집에 더했거나 본문 절 구성이 바뀌면 다시 돌린다(CI도 빌드 전에 돌린다).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "book"
OUT = SRC / "Z-index.qmd"
MAX_LINKS = 8
MAX_CMD_LINKS = 12
# 괄호 속 말 가운데 검색어로 쓰지 않을 것(맥락 표시)
ALIAS_SKIP = {"zone", "docker", "proxmox", "firewalld", "이미지", "export"}

# 색인 대상 파일과 표시 이름(SUMMARY 순서)
SKIP = {"F-glossary.qmd", "E-references.qmd", "Z-index.qmd", "Z-commands.qmd"}


def summary_files():
    files = []
    for m in re.finditer(r"^\s*-\s+(\S+\.qmd)\s*$", (SRC / "_quarto.yml").read_text(), re.M):
        f = m.group(1)
        if f not in SKIP and f not in files:
            files.append(f)
    return files


# ---------- mdBook 0.4 의 제목 → id 규칙 ----------
def plain(md):
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md)
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)
    md = re.sub(r"<[^>]+>", "", md)
    return md.replace("`", "").replace("**", "").replace("*", "").replace("_", "_")


def normalize_id(text):
    out = []
    for ch in text:
        if ch.isalnum() or ch in "_-":
            out.append(ch.lower() if ch.isascii() else ch)
        elif ch.isspace():
            out.append("-")
    return "".join(out)


# ---------- 절 라벨 ----------
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭"


def label_for(fname, h2, h1):
    """링크에 보일 짧은 이름: §3.5, H.3, 실습⑧, 들어가며 …"""
    if fname.startswith("labs/"):
        m = re.search(r"실습\s*([" + CIRCLED + r"]′?)", h1 or h2 or "")
        if m:
            return "실습" + m.group(1)
        return "실습 들어가기"
    if fname == "index.qmd":
        return "들어가며"
    if fname == "map.md":
        return "지도"
    t = plain(h2 or "")
    m = re.match(r"\s*([0-9]+\.[0-9]+(?:\.[0-9]+)?)\s", t)
    if m:
        return "§" + m.group(1)
    m = re.match(r"\s*([A-K]\.[0-9]+(?:\.[0-9]+)*)\s", t)
    if m:
        return m.group(1)
    letter = re.match(r"([A-K])-", fname)
    if letter:
        return "부록 " + letter.group(1)
    m = re.match(r"0([1-7])-", fname)
    if m:
        return "Part " + m.group(1)
    return fname


def sections(fname):
    """(label, anchor, text, blocks) 목록. text에는 코드 블록을 뺀 본문, blocks에는 (언어, 줄들)."""
    lines = (SRC / fname).read_text().splitlines()
    seen = {}
    out = []
    h1 = h2 = None
    cur = {"label": None, "anchor": "", "text": [], "blocks": []}
    fence = None

    def flush():
        if cur["text"] or cur["blocks"]:
            out.append((cur["label"] or label_for(fname, h2, h1), cur["anchor"], "\n".join(cur["text"]), cur["blocks"]))

    for ln in lines:
        fm = re.match(r"^\s*(`{3,})(.*)$", ln)
        if fence is None and fm:
            fence = fm.group(1)
            cur["blocks"].append((fm.group(2).strip(), []))
            continue
        if fence is not None:
            if ln.strip() == fence:
                fence = None
            else:
                cur["blocks"][-1][1].append(ln)
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", ln)
        if m:
            flush()
            level, title = len(m.group(1)), m.group(2)
            cm = re.search(r"\s*\{#([^}\s]+)\}$", title)
            if cm:
                title = title[: cm.start()]
            hid = cm.group(1) if cm else normalize_id(plain(title))
            n = seen.get(hid, 0)
            seen[hid] = n + 1
            if n:
                hid = f"{hid}-{n}"
            if level == 1:
                h1, h2 = title, None
            elif level == 2:
                h2 = title
            cur = {"label": label_for(fname, h2 if level >= 2 else None, h1), "anchor": hid, "text": [title], "blocks": []}
            continue
        cur["text"].append(ln)
    flush()
    return out


# ---------- 표제어 ----------
def load_terms():
    """{표제어: [검색어…]}"""
    terms = {}
    for ln in (SRC / "F-glossary.qmd").read_text().splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|", ln)
        if not m or m.group(1) in ("용어", "---"):
            continue
        head = plain(m.group(1)).strip()
        if set(head) <= set("-: "):
            continue
        keys = []
        for part in re.split(r"\s+[/·]\s+", head):
            part = part.strip()
            m2 = re.match(r"^(.*?)\s*\((.+)\)$", part)
            if not m2:
                keys.append(part)
                continue
            x, y = m2.group(1).strip(), m2.group(2).strip()
            keys.append(x)
            hangul = lambda t: re.search(r"[가-힣]", t) is not None
            # 원어·번역 별칭만 검색어로 더한다(맥락 표시는 뺀다)
            if (hangul(x) != hangul(y) or " " in y) and y.lower() not in ALIAS_SKIP:
                keys.append(y.strip("`"))
        terms[head] = [k for k in keys if k]
    extra = ROOT / "tools" / "index-extra.txt"
    if extra.exists():
        for ln in extra.read_text().splitlines():
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            head, _, rest = ln.partition("|")
            head = head.strip()
            keys = [k.strip() for k in rest.split(",") if k.strip()] or [head]
            # 용어집에 이미 있는 표제어(또는 그 검색어)면 거기에 합친다
            for h, ks in terms.items():
                if head == h or head in ks:
                    head = h
                    break
            terms.setdefault(head, [])
            for k in keys:
                if k not in terms[head]:
                    terms[head].append(k)
    return terms


def pattern(key):
    esc = re.escape(key)
    if re.search(r"[A-Za-z0-9]", key) and not re.search(r"[가-힣]", key):
        flags = 0 if sum(c.isupper() for c in key) >= 2 else re.IGNORECASE
        return re.compile(r"(?<![A-Za-z0-9_.])" + esc + r"(?![A-Za-z0-9_])", flags)
    return re.compile(esc)


# ---------- 정렬 ----------
CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
GROUP_OF = {"ㄲ": "ㄱ", "ㄸ": "ㄷ", "ㅃ": "ㅂ", "ㅆ": "ㅅ", "ㅉ": "ㅈ"}


def group(term):
    c = term.lstrip("./`'\"(")[:1]
    if "가" <= c <= "힣":
        g = CHO[(ord(c) - 0xAC00) // 588]
        return (1, GROUP_OF.get(g, g))
    if c.isascii() and c.isalpha():
        return (2, c.upper())
    return (0, "기호·숫자")


def sort_key(term):
    g = group(term)
    return (g, term.lstrip("./`'\"(").lower())


# ---------- 명령 찾아보기 ----------
CMD_OUT = SRC / "Z-commands.qmd"


def merge_links(hits, limit=None):
    """[(f, lab, anc, n)] → [[lab, href, n]]. 같은 라벨은 하나로(첫 앵커, 횟수 합)."""
    merged = {}
    for f, lab, anc, n in hits:
        k = (f, lab)
        if k in merged:
            merged[k][2] += n
        else:
            merged[k] = [lab, f"{f}#{anc}" if anc else f, n]
    links = list(merged.values())
    if limit and len(links) > limit:
        keep = {id(x) for x in sorted(links, key=lambda x: -x[2])[:limit]}
        links = [x for x in links if id(x) in keep]
    return links


def make_command_index(allsecs):
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    from cmdindex import scan_block, scan_inline

    per = []
    known = set()
    for f, lab, anc, txt, blocks in allsecs:
        found = [c for lang, body in blocks for c in scan_block(lang, body)]
        known.update(found)
        per.append((f, lab, anc, txt, found))
    extra = ROOT / "tools" / "index-commands.txt"
    if extra.exists():
        known.update(ln.strip() for ln in extra.read_text().splitlines() if ln.strip() and not ln.startswith("#"))
    hits = {}
    for f, lab, anc, txt, found in per:
        cnt = {}
        for c in found + scan_inline(txt, known):
            cnt[c] = cnt.get(c, 0) + 1
        for c, n in cnt.items():
            hits.setdefault(c, []).append((f, lab, anc, n))

    out = [
        "# 명령 찾아보기 {#command-index}",
        "",
        "이 책의 본문과 실습에 나오는 명령을 ABC순으로 모았습니다. "
        "코드 블록과 본문·표에 적힌 명령을 모두 셌고, 링크는 그 명령이 나오는 절입니다. "
        f"자주 나오는 명령은 많이 다루는 곳 {MAX_CMD_LINKS}곳까지만 적었습니다. "
        "`sudo`·`time` 같은 앞붙이는 빼고 실제로 실행되는 명령으로 셌으며, `cd`·`echo` 같은 셸 내장 명령은 넣지 않았습니다. "
        "명령을 자주 쓰는 순서로 모은 표는 [부록 D](D-cheatsheet.qmd)에 있습니다.",
        "",
        "> 이 페이지는 `tools/make-index.py`가 만듭니다. 손으로 고치지 마세요.",
        "",
    ]
    cur = None
    for c in sorted(hits, key=lambda x: x.lower()):
        g = c[0].upper()
        if g != cur:
            if cur is not None:
                out.append("")
            cur = g
            out += [f"## {g} {{#cmd-{g.lower()}}}", ""]
        links = " · ".join(f"[{lab}]({href})" for lab, href, _ in merge_links(hits[c], MAX_CMD_LINKS))
        out.append(f"- `{c}` — {links}")
    out.append("")
    CMD_OUT.write_text("\n".join(out))
    print(f"{CMD_OUT.relative_to(ROOT)}: {len(hits)} commands")


def main():
    files = summary_files()
    allsecs = [(f, lab, anc, txt, blk) for f in files for (lab, anc, txt, blk) in sections(f)]
    secs = [(f, lab, anc, txt) for f, lab, anc, txt, _ in allsecs]
    make_command_index(allsecs)
    terms = load_terms()
    entries = {}
    for head, keys in terms.items():
        pats = [pattern(k) for k in keys]
        hits = []
        for f, lab, anc, txt in secs:
            n = sum(len(p.findall(txt)) for p in pats)
            if n:
                hits.append((f, lab, anc, n))
        # 같은 라벨은 하나로(첫 앵커, 횟수 합)
        merged = {}
        for f, lab, anc, n in hits:
            k = (f, lab)
            if k in merged:
                merged[k][2] += n
            else:
                merged[k] = [lab, f"{f}#{anc}" if anc else f, n]
        links = list(merged.values())
        if not links:
            continue
        if len(links) > MAX_LINKS:
            top = sorted(links, key=lambda x: -x[2])[:MAX_LINKS]
            keep = {id(x) for x in top}
            links = [x for x in links if id(x) in keep]
        entries[head] = links

    out = [
        "# 찾아보기",
        "",
        "용어집([부록 F](F-glossary.qmd))의 표제어가 본문 어디에 나오는지 모았습니다. "
        "숫자·기호, 한글(가나다순), 영문(ABC순) 차례입니다. "
        f"링크는 그 용어가 나오는 절이며, 많이 나오는 용어는 자주 다루는 곳 {MAX_LINKS}곳까지만 적었습니다. "
        "페이지 위의 🔍 검색도 함께 쓰세요.",
        "",
        "> 이 페이지는 `tools/make-index.py`가 만듭니다. 손으로 고치지 마세요.",
        "",
    ]
    cur = None
    for head in sorted(entries, key=sort_key):
        g = group(head)
        if g != cur:
            if cur is not None:
                out.append("")
            cur = g
            out += [f"## {g[1]}", ""]
        links = " · ".join(f"[{lab}]({href})" for lab, href, _ in entries[head])
        out.append(f"- **{head}** — {links}")
    out.append("")
    OUT.write_text("\n".join(out))
    print(f"{OUT.relative_to(ROOT)}: {len(entries)} terms")


if __name__ == "__main__":
    main()
