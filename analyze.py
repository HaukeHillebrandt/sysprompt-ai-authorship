"""Combine Pangram segment labels with first-appearance text.

1. Label every line of each leak's new text (AI / Human) from Pangram segments.
2. Classify lines by prompt section (safety policy / product & identity / style / tools & features).
3. AI share of new text by era x section.
4. Stock view: share of each full leak prompt that was AI-written at first appearance.
"""
import re, json, os, bisect, collections
from prep_newtext import norm, sentences, units, leak_text
from leak_markers import FILES, load

BASE = os.path.dirname(os.path.abspath(__file__))
NT = os.path.join(BASE, "newtext")
LABELS = [f"{n:02d}_{os.path.splitext(f)[0]}" for n, (f, d, s) in enumerate(FILES)]
OVERVIEW = {0: 51, 1: 100, 2: 65, 3: 28, 4: 51, 5: 33, 6: 56, 7: 42, 8: 50, 9: 79, 10: 74,
            11: 83, 12: 92, 13: 95, 14: 91}  # Pangram "x% of this text is AI", new text only
EXTRA = {"14_CLAUDE-OPUS-5.5__skills": 100, "14_CLAUDE-OPUS-5.5__artifact_refs_SAMPLE": 99}

alnum = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())

SAFE_TOK = ("refus", "harm", "child", "safety", "copyright", "wellbeing", "suicide", "evenhand", "political",
            "cyber", "weapon", "legal", "election", "abuse", "sensitive", "privacy", "critical", "mental", "minor",
            "malicious", "quot", "ethic", "danger", "violen", "extrem", "sexual", "anthropic_reminders", "disordered",
            "hard_limits", "image_specific", "cbrn", "self_harm")
PROD_TOK = ("product", "claude_info", "family", "cutoff", "mythos", "accessing", "identity", "helpful_info")
STYLE_TOK = ("tone", "format", "lists", "bullet", "style", "chatting", "working_with", "mistake", "behavio",
             "writing", "emoji", "curse", "acting_vs", "capability_check", "thinking")
SAFE_TXT = re.compile(r"\b(weapons?|self-harm|suicid\w*|minors?|child(ren)?|malicious|copyright\w*|sexual\w*|harmful|extremis\w*|disordered eating|grooming|csam|cbrn|bioweapon\w*|explosives?)\b", re.I)
PROD_TXT = re.compile(r"(claude is accessible|model strings?|iteration of claude|knowledge cutoff|anthropic's products|currently selected (version|model))", re.I)


def _has(sec, toks):
    s = "_" + sec.lower().replace(" ", "_") + "_"
    return any(("_" + t) in s for t in toks)


def category(sec, line):
    s = (sec or "").lower()
    if _has(s, SAFE_TOK):
        return "safety policy"
    if _has(s, PROD_TOK):
        return "product/identity"
    if _has(s, STYLE_TOK):
        return "style/behaviour"
    if s in ("", "claude_behavior", "claude behavior", "system prompt"):
        if SAFE_TXT.search(line):
            return "safety policy"
        if PROD_TXT.search(line):
            return "product/identity"
        if s:
            return "style/behaviour"
    return "tools/features"


def section_index(raw):
    ev = []  # (pos, section)
    stack = []
    for m in re.finditer(r"(?m)<(/?)([a-z_]{3,})>|\{(/?)([a-z_]{3,})\}|^#{1,4} +(.+)$", raw):
        if m.group(5):
            stack = [m.group(5).strip().lower()]
        else:
            close = m.group(1) or m.group(3)
            tag = m.group(2) or m.group(4)
            if close:
                if tag in stack:
                    stack = stack[:len(stack) - 1 - stack[::-1].index(tag)]
            else:
                stack.append(tag)
        ev.append((m.end(), stack[-1] if stack else ""))
    return ev


def section_at(ev, pos):
    i = bisect.bisect_right([p for p, _ in ev], pos) - 1
    return ev[i][1] if i >= 0 else ""


def label_lines(doc, text, segs):
    """Return [(line, label)] for a new-text document using ordered Pangram segment heads."""
    A = alnum(text)
    # map alnum index -> char index
    idx = [i for i, c in enumerate(text) if c.isalnum() and c.isascii()]
    starts, cur = [], 0
    for lab, words, head in segs:
        h = alnum(head)[:16]
        if len(h) < 8:
            continue
        j = A.find(h, cur)
        if j < 0:
            j = A.find(h)
        if j < 0:
            continue
        starts.append((idx[j] if j < len(idx) else len(text), lab))
        cur = j + 1
    starts.sort()
    if not starts:
        return [], 0
    pos, out = 0, []
    sp = [s for s, _ in starts]
    for ln in text.split("\n\n"):
        a, b = pos, pos + len(ln)
        pos = b + 2
        # majority label by char overlap
        cnt = collections.Counter()
        for k, (s, lab) in enumerate(starts):
            e = starts[k + 1][0] if k + 1 < len(starts) else len(text)
            ov = max(0, min(b, e) - max(a, s))
            if ov:
                cnt[lab] += ov
        if a < sp[0]:
            cnt[starts[0][1]] += max(0, min(b, sp[0]) - a)
        out.append((ln, cnt.most_common(1)[0][0] if cnt else "?"))
    return out, len(starts)


if __name__ == "__main__":
    segs = collections.defaultdict(list)
    seen = set()
    for row in open(os.path.join(BASE, "segs.tsv")):
        d, lab, w, head = row.rstrip("\n").split("|", 3)
        key = (int(d), head)
        if key in seen:
            continue
        seen.add(key)
        segs[int(d)].append(("AI" if lab.startswith("A") else "Human", int(w), head))

    line_label = {}  # norm(sentence) -> label at first appearance
    rows = []
    cat_era = collections.defaultdict(lambda: collections.Counter())
    for n, (f, d, surface) in enumerate(FILES):
        text = open(os.path.join(NT, LABELS[n] + ".txt")).read()
        lines, located = label_lines(n, text, segs.get(n, []))
        raw = load(f)
        ev = section_index(raw)
        era = "2024-06..2026-02" if d < "2026-03" else "2026-04..2026-09"
        for ln, lab in lines:
            p = raw.find(ln[:60])
            sec = section_at(ev, p + min(len(ln), 80)) if p >= 0 else "tool description"
            for s in (sentences(ln) or [ln]):
                c = "tools/features" if sec == "tool description" else category(sec, s)
                cat_era[(era, c)][lab] += len(s.split())
            for s in (sentences(ln) or [ln]):
                line_label.setdefault(norm(s), lab)
        ai_w = sum(len(l.split()) for l, lab in lines if lab == "AI")
        tot_w = sum(len(l.split()) for l, lab in lines)
        rows.append((LABELS[n], d, surface, len(text.split()), OVERVIEW[n], ai_w / max(tot_w, 1), located, len(segs.get(n, []))))

    print("### A. AI share of first-appearance (newly written) text\n")
    print(f"{'leak':38}{'date':11}{'surface':27}{'new words':>10}{'Pangram AI':>11}{'line-mapped':>12}{'segs located':>14}")
    for r in rows:
        print(f"{r[0]:38}{r[1]:11}{r[2]:27}{r[3]:>10}{r[4]:>10}%{r[5]:>11.0%}{r[6]:>8}/{r[7]:<5}")
    for k, v in EXTRA.items():
        print(f"{k:76}{'':>10}{v:>10}%")

    print("\n### B. AI share of new text by section type and era (line-mapped, word-weighted)\n")
    cats = ["safety policy", "product/identity", "style/behaviour", "tools/features"]
    print(f"{'era':20}" + "".join(f"{c:>22}" for c in cats))
    for era in ["2024-06..2026-02", "2026-04..2026-09"]:
        cells = []
        for c in cats:
            cc = cat_era[(era, c)]
            t = cc["AI"] + cc["Human"]
            cells.append(f"{cc['AI']/t:>12.0%} (n={t:>6})" if t else f"{'-':>22}")
        print(f"{era:20}" + "".join(cells))

    print("\n### C. Stock view: share of each full leaked prompt that was AI-written at first appearance\n")
    print(f"{'leak':38}{'words':>8}{'AI':>7}{'Human':>7}{'unknown':>9}")
    for n, (f, d, surface) in enumerate(FILES):
        parts = leak_text(f)
        c = collections.Counter()
        for ln in units(parts["prompt"]):
            for s in (sentences(ln) or [ln]):
                c[line_label.get(norm(s), "unknown")] += len(s.split())
        t = sum(c.values())
        print(f"{LABELS[n]:38}{t:>8}{c['AI']/t:>7.0%}{c['Human']/t:>7.0%}{c['unknown']/t:>9.0%}")
