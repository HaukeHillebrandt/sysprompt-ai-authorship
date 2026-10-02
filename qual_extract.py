"""Extract human-labelled passages in the latest prompt sets for qualitative coding.

(1) Newly written text labelled human by Pangram (contiguous runs of human-labelled lines).
(2) Carried-over text in the latest deployed prompt that was human-written when first added, grouped by origin.
Writes results/qual_human_passages.md.
"""
import json, os, re, collections
from prep_newtext import norm, sentences, units, leak_text
from leak_markers import FILES, load
import analyze as A
import analyze_openai as AO
import prep_openai as P

BASE = os.path.dirname(os.path.abspath(__file__))
out = ["# Human-labelled passages in the latest system prompts\n"]


def runs(lines):
    cur, res = [], []
    for ln, lab in lines:
        if lab == "Human":
            cur.append(ln)
        elif cur:
            res.append(cur); cur = []
    if cur:
        res.append(cur)
    return res


# ---------- Anthropic ----------
segs = collections.defaultdict(list); seen = set()
for row in open(os.path.join(BASE, "segs.tsv")):
    d, lab, w, head = row.rstrip("\n").split("|", 3)
    if (int(d), head) not in seen:
        seen.add((int(d), head)); segs[int(d)].append(("AI" if lab.startswith("A") else "Human", int(w), head))
anth_lab, anth_origin = {}, {}
for n, (f, d, s) in enumerate(FILES):
    text = open(os.path.join(BASE, "newtext", A.LABELS[n] + ".txt")).read()
    lines, _ = A.label_lines(n, text, segs.get(n, []))
    for ln, lab in lines:
        for s_ in (sentences(ln) or [ln]):
            anth_lab.setdefault(norm(s_), lab); anth_origin.setdefault(norm(s_), A.LABELS[n])
    if n >= 12:
        raw = load(f); ev = A.section_index(raw)
        rr = runs(lines)
        out.append(f"\n## Anthropic {A.LABELS[n]} ({d}): human-labelled NEW text, {sum(len(' '.join(r).split()) for r in rr)} words in {len(rr)} passages\n")
        for r in sorted(rr, key=lambda r: -len(" ".join(r).split())):
            p = raw.find(r[0][:60]); sec = A.section_at(ev, p + 40) if p >= 0 else "tool description"
            out.append(f"- [{len(' '.join(r).split())}w | {sec}] " + " ⏎ ".join(r)[:1200])

latest = "CLAUDE-OPUS-5.5.md"
by_origin = collections.defaultdict(list)
for ln in units(leak_text(latest)["prompt"]):
    for s_ in (sentences(ln) or [ln]):
        k = norm(s_)
        if anth_lab.get(k) == "Human" and anth_origin.get(k) != A.LABELS[14]:
            by_origin[anth_origin[k]].append(s_)
out.append(f"\n## Anthropic Opus 5.5 (agent app) prompt: carried-over text that was human-written when first added\n")
for o in sorted(by_origin):
    ss = by_origin[o]
    out.append(f"\n### from {o}: {sum(len(x.split()) for x in ss)} words, {len(ss)} sentences\n")
    for x in ss[:400]:
        out.append(f"- {x[:400]}")

# ---------- OpenAI ----------
lab_lines = json.load(open(os.path.join(BASE, "results/openai_labelled_lines.json")))
oai_lab, oai_origin = {}, {}
for k in AO.KEYS:
    for ln, lab in lab_lines.get(k, []):
        for s_ in (sentences(ln) or [ln]):
            oai_lab.setdefault(norm(s_), lab); oai_origin.setdefault(norm(s_), k)
for n, k in enumerate(AO.KEYS):
    if n < 11:
        continue
    lines = [(a, b) for a, b in lab_lines[k]]
    raw = "\n".join(P.read(f) for f in P.FILES[n][1]); ev = AO.section_index(raw)
    rr = runs(lines)
    out.append(f"\n## OpenAI {k}: human-labelled NEW text (scored part), {sum(len(' '.join(r).split()) for r in rr)} words in {len(rr)} passages\n")
    for r in sorted(rr, key=lambda r: -len(" ".join(r).split())):
        p = raw.find(r[0][:50]); sec = AO.section_at(ev, p) if p >= 0 else ""
        out.append(f"- [{len(' '.join(r).split())}w | {sec or 'JSON tool schema'}] " + " ⏎ ".join(r)[:1200])

book = json.load(open(os.path.join(BASE, "newtext_openai/lines.json")))
for k in [AO.KEYS[12], AO.KEYS[13]]:
    cnt = collections.Counter(); ex = collections.defaultdict(list); rep = collections.Counter()
    for ln in book[k]["lines"]:
        for s_ in (sentences(ln["text"]) or [ln["text"]]):
            n_ = norm(s_)
            if oai_lab.get(n_) == "Human" and oai_origin.get(n_) != k:
                cnt[oai_origin[n_]] += len(s_.split()); rep[s_] += 1
                if len(ex[oai_origin[n_]]) < 300 and s_ not in ex[oai_origin[n_]]:
                    ex[oai_origin[n_]].append(s_)
    out.append(f"\n## OpenAI {k} prompt: carried-over text that was human-written when first added\n")
    out.append("Most repeated human-labelled sentences (occurrences in this prompt): " +
               "; ".join(f"{v}x '{s_[:80]}'" for s_, v in rep.most_common(12)))
    for o in sorted(cnt):
        out.append(f"\n### from {o}: {cnt[o]} words\n")
        for x in ex[o][:200]:
            out.append(f"- {x[:300]}")

open(os.path.join(BASE, "results/qual_human_passages.md"), "w").write("\n".join(out))
print("\n".join(l for l in out if l.startswith("#")))
