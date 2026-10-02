"""Stylometric markers of AI drafting across the full leaked Anthropic prompts (CL4R1T4S).

Markers (per 10k words):
  em      em-dashes (—)
  hy      spaced hyphen used as a dash between words ("word - word"), the typed human form
  em%     em / (em + hy): share of dashes that are em-dashes, independent of text length
  xnot    ", not Y." contrastive tail
Each file is split into prose vs tool-schema descriptions; the Opus 5.5 session dump is
split by its section markers and user turns are dropped. "New" = sentences not present in
any earlier leak (dash-normalised matching).
"""
import re, json, glob, os, collections

BASE = os.path.dirname(os.path.abspath(__file__))
LEAK = os.path.join(BASE, "CL4R1T4S/ANTHROPIC")
OFF = os.path.join(BASE, "official")

FILES = [  # (file, content date, surface)
    ("Claude_Sonnet_3.5.md", "2024-06-20", "claude.ai"),
    ("Claude_Code_03-04-24.md", "2025-03-04", "Claude Code"),
    ("UserStyle_Modes.md", "2025-04-20", "claude.ai styles"),
    ("Claude_Sonnet_3.7_New.txt", "2025-05-16", "claude.ai"),
    ("Claude_4.txt", "2025-05-22", "claude.ai"),
    ("Claude-4.1.txt", "2025-08-05", "claude.ai (reconstruction)"),
    ("Claude_Sonnet-4.5_Sep-29-2025.txt", "2025-09-29", "claude.ai"),
    ("Claude-4.5-Opus.txt", "2025-11-24", "claude.ai"),
    ("Claude_Opus_4.6.txt", "2026-02-06", "claude.ai"),
    ("Claude-Opus-4.7.txt", "2026-04-16", "claude.ai"),
    ("Claude-Design-Sys-Prompt.txt", "2026-04-17", "Claude Design"),
    ("CLAUDE-FABLE-5.md", "2026-06-09", "claude.ai"),
    ("OPUS-5.md", "2026-07-24", "claude.ai"),
    ("Claude-Fable-5.1.md", "2026-09-01", "claude.ai"),
    ("CLAUDE-OPUS-5.5.md", "2026-09-22", "agent app session"),
]
OFFICIAL_FOR = {
    "Claude_Sonnet_3.5.md": "claude-sonnet-3-5", "Claude_Sonnet_3.7_New.txt": "claude-sonnet-3-7",
    "Claude_4.txt": "claude-sonnet-4", "Claude-4.1.txt": "claude-opus-4-1",
    "Claude_Sonnet-4.5_Sep-29-2025.txt": "claude-sonnet-4-5", "Claude-4.5-Opus.txt": "claude-opus-4-5",
    "Claude_Opus_4.6.txt": "claude-opus-4-6", "Claude-Opus-4.7.txt": "claude-opus-4-7",
    "CLAUDE-FABLE-5.md": "claude-fable-5", "OPUS-5.md": "claude-opus-5",
    "Claude-Fable-5.1.md": "claude-fable-5-1", "CLAUDE-OPUS-5.5.md": "claude-opus-5-5",
}

EM = re.compile(r"—")
HY = re.compile(r"(?<=[A-Za-z,)]) - (?=[A-Za-z(])")
XNOT = re.compile(r", not [a-z][^.,;\n]{0,40}\.")
JSONLINE = re.compile(r'"(description|type|properties|parameters|name|items|enum|required|title|default|additionalProperties)"\s*:|^\s*[{}\[\]],?\s*$')
DESC = re.compile(r'"description"\s*:\s*"((?:[^"\\]|\\.)*)"')


def unescape(s):
    try:
        return json.loads('"' + s + '"')
    except Exception:
        return s.replace("\\n", "\n").replace("\\u2014", "—").replace('\\"', '"')


def split_prose_tools(text):
    prose, tools = [], []
    for line in text.split("\n"):
        if JSONLINE.search(line) or line.lstrip().startswith(("<function>", "{function}")):
            tools.extend(unescape(d) for d in DESC.findall(line))
        else:
            prose.append(line)
    return "\n".join(prose), "\n".join(tools)


def opus55_components(text):
    parts = re.split(r"^--- \[(.+?)\] ---$", text, flags=re.M)
    comp = collections.defaultdict(list)
    for i in range(1, len(parts), 2):
        h, body = parts[i], parts[i + 1]
        if "user turn" in h:
            continue
        if h.startswith("system prompt"):
            p, t = split_prose_tools(body)
            comp["system prompt: prose"].append(p)
            comp["system prompt: tool descriptions"].append(t)
        elif h.startswith("on-demand file"):
            comp["artifact-type reference files"].append(body)
        elif "skill body" in h or h.startswith("tool result: Skill"):
            comp["skill bodies"].append(body)
        elif h.startswith("tool result"):
            p, t = split_prose_tools(body)
            comp["other tool results"].append(p + "\n" + t)
        else:
            comp["system notices"].append(body)
    return {k: "\n".join(v) for k, v in comp.items()}


def rates(t):
    w = max(len(t.split()), 1)
    em, hy, xn = len(EM.findall(t)), len(HY.findall(t)), len(XNOT.findall(t))
    return dict(words=len(t.split()), em=em / w * 1e4, hy=hy / w * 1e4,
                share=(em / (em + hy) if em + hy else float("nan")), xnot=xn / w * 1e4, n_dash=em + hy)


def norm(s):
    s = re.sub(r"[—–]| - | -- ", " - ", s)
    s = re.sub(r"[{}<>*#`]", "", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def sents(t):
    return [s for s in re.split(r"(?<=[.!?])\s+|\n+", t) if len(s.split()) >= 6]


def load(f):
    t = open(os.path.join(LEAK, f), encoding="utf-8", errors="ignore").read()
    return t.replace("\\u2014", "—").replace("\\u2013", "–")


def fmt(r):
    sh = "  n/a" if r["share"] != r["share"] else f"{r['share']:>5.0%}"
    return f"{r['words']:>8}{r['em']:>7.1f}{r['hy']:>6.1f} {sh}{r['xnot']:>6.1f}"


HDR = f"{'words':>8}{'em':>7}{'hy':>6} {'em%':>5}{'xnot':>6}"

if __name__ == "__main__":
    texts = {}
    for f, d, s in FILES:
        t = load(f)
        if f == "CLAUDE-OPUS-5.5.md":
            comps = opus55_components(t)
            prose = "\n".join(v for k, v in comps.items() if "tool descriptions" not in k)
            tools = comps["system prompt: tool descriptions"]
        else:
            prose, tools = split_prose_tools(t)
        texts[f] = (d, s, prose, tools, t)

    print("\n### 1. Full leaked files (all Anthropic-written text; user turns dropped)\n")
    print(f"{'file':34}{'date':11}{'surface':27}{HDR}")
    for f, (d, s, p, tl, raw) in texts.items():
        print(f"{f:34}{d:11}{s:27}{fmt(rates(p + chr(10) + tl))}")

    print("\n### 2. Prose vs tool descriptions\n")
    print(f"{'file':34}{'PROSE':>8}{'':>7}{'':>6} {'':>5}{'':>6}   {'TOOL DESCR':>8}")
    print(f"{'':34}{HDR}   {HDR}")
    for f, (d, s, p, tl, raw) in texts.items():
        rt = rates(tl)
        print(f"{f:34}{fmt(rates(p))}   {fmt(rt) if rt['words'] > 50 else '       -'}")

    print("\n### 3. New text only (sentences absent from every earlier leak)\n")
    print(f"{'file':34}{'date':11}{HDR}")
    seen = set()
    for f, (d, s, p, tl, raw) in texts.items():
        ss = sents(p + "\n" + tl)
        new = [x for x in ss if norm(x) not in seen]
        seen.update(norm(x) for x in ss)
        print(f"{f:34}{d:11}{fmt(rates(chr(10).join(new)))}")

    print("\n### 4. Opus 5.5 agent-app session by component\n")
    print(f"{'component':36}{HDR}")
    for k, v in sorted(opus55_components(load('CLAUDE-OPUS-5.5.md')).items()):
        print(f"{k:36}{fmt(rates(v))}")

    print("\n### 5. Extraction fidelity: dashes in official sentences as they appear in the leak\n")
    print(f"{'file':34}{'official':>18}{'matched':>9}{'dash same':>11}{'changed':>9}")
    for f, (d, s, p, tl, raw) in texts.items():
        if f not in OFFICIAL_FOR:
            continue
        off = open(os.path.join(OFF, OFFICIAL_FOR[f] + ".md"), encoding="utf-8").read()
        leak_idx = {norm(x): x for x in sents(raw)}
        dashed = [x for x in sents(off) if EM.search(x) or HY.search(x)]
        same = changed = matched = 0
        for x in dashed:
            y = leak_idx.get(norm(x))
            if y is None:
                continue
            matched += 1
            sig = lambda z: (len(EM.findall(z)), len(HY.findall(z)))
            same += sig(x) == sig(y)
            changed += sig(x) != sig(y)
        print(f"{f:34}{OFFICIAL_FOR[f]:>18}{matched:>6}/{len(dashed):<3}{same:>9}{changed:>9}")
