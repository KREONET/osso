"""명령 찾아보기용 명령 추출. make-index.py가 불러 쓴다.

코드 블록(bash·sh·console·powershell)의 각 줄에서 명령 이름을 꺼내고,
본문·표의 인라인 코드 가운데 그 명령으로 시작하는 것도 함께 센다.
"""
import re

SHELL_LANGS = {"bash", "sh", "shell", "zsh", "console", "powershell"}
# 명령 앞에 붙어 다른 명령을 실행하는 것. 뒤따르는 옵션은 건너뛴다.
WRAPPERS = {"sudo", "time", "watch", "xargs", "nohup", "env", "exec", "doas", "command", "nice", "ionice", "timeout", "stdbuf"}
# 옵션이 값을 받는 경우(sudo -u root 등)
WRAPPER_ARG_OPTS = {"sudo": {"-u", "-g", "-C"}, "watch": {"-n"}, "xargs": {"-I", "-n", "-P"}, "timeout": {"-s", "-k"}}
# 셸 문법과 색인할 가치가 없는 내장 명령
SKIP = {
    "if", "then", "else", "elif", "fi", "for", "in", "do", "done", "while", "until", "case", "esac",
    "function", "select", "return", "local", "export", "set", "unset", "shift", "true", "false",
    "exit", "cd", "echo", "printf", "read", "source", ".", "{", "}", "[", "[[", "]]", "]", "!",
    "eval", "trap", "wait", "declare", "readonly", "let", "break", "continue", "alias", "type",
    "pushd", "popd", "test", "EOF", "END",
}
NAME = re.compile(r"^[A-Za-z][A-Za-z0-9._+-]*$")


def _first_command(seg):
    toks = seg.strip().split()
    i = 0
    while i < len(toks):
        t = toks[i]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t):  # VAR=값 명령
            i += 1
            continue
        if t in WRAPPERS:
            w = t
            i += 1
            while i < len(toks) and toks[i].startswith("-"):
                i += 2 if toks[i] in WRAPPER_ARG_OPTS.get(w, ()) else 1
            continue
        break
    if i >= len(toks):
        return None
    t = toks[i].strip("()`'\"")
    if t.startswith("$("):
        t = t[2:]
    if not NAME.match(t) or t in SKIP or t.endswith((".", "-")):
        return None
    # 설정 파일 키워드(Host, PasswordAuthentication)는 명령이 아니다. PowerShell의 Get-Item 같은 이름은 둔다.
    if re.match(r"^[A-Z][A-Za-z]*$", t):
        return None
    # 함수 정의 name() {
    if i + 1 < len(toks) and toks[i + 1].startswith("{") and toks[i].endswith("()"):
        return None
    return t


def commands_in_line(line):
    """한 줄의 명령 이름들. 파이프·&&·||·;·$( 로 나뉜 각 부분의 첫 명령."""
    line = re.sub(r"\s#.*$", "", line)  # 줄 끝 주석
    line = re.sub(r"'[^']*'", "''", line)  # 따옴표 속 문자열은 명령이 아니다
    line = re.sub(r'"[^"$]*"', '""', line)
    out = []
    for seg in re.split(r"\|\||&&|\||;|\$\(|`", line):
        c = _first_command(seg)
        if c:
            out.append(c)
    return out


def scan_block(lang, lines):
    """코드 블록의 명령 이름 목록."""
    lang = lang.strip("{}.").split()[0].lower() if lang else ""
    if lang not in SHELL_LANGS:
        return []
    out = []
    cont = False
    heredoc = None
    for ln in lines:
        s = ln.strip()
        if heredoc:
            if s == heredoc:
                heredoc = None
            continue
        if lang == "console":
            if not s.startswith("$ "):
                cont = False
                continue
            s = s[2:]
        elif lang == "powershell":
            s = re.sub(r"^PS[^>]*>\s*", "", s)
        if cont:
            cont = s.endswith("\\")
            continue
        cont = s.endswith("\\")
        if not s or s.startswith("#"):
            continue
        m = re.search(r"<<-?\s*['\"]?([A-Za-z_]+)['\"]?", s)
        if m:
            heredoc = m.group(1)
        out += commands_in_line(s)
    return out


def scan_inline(text, known):
    """본문의 인라인 코드 가운데 알려진 명령으로 시작하는 것."""
    out = []
    for m in re.finditer(r"`([^`\n]+)`", text):
        c = commands_in_line(m.group(1))
        if c and c[0] in known and " " in m.group(1).strip():
            out.append(c[0])
    return out
