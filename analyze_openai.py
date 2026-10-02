"""OpenAI counterpart of analyze.py: AI share of first-appearance text, by section and era, plus stock view."""
import re, os, json, collections
from prep_newtext import norm, sentences
from analyze import label_lines
import prep_openai as P

BASE = os.path.dirname(os.path.abspath(__file__))
NT = os.path.join(BASE, "newtext_openai")
KEYS = [f"{n:02d}_{re.sub(r'[^A-Za-z0-9.]+', '_', lab).strip('_')}" for n, (lab, f, d, s) in enumerate(P.FILES)]
SAMPLED = {11, 12}
# Pangram document-level AI share of new text (%, from the overview; human-verdict docs as 100 - human%)
OVERVIEW = {0: 35, 1: 31, 2: 5, 3: 0, 4: 0, 5: 0, 6: 40, 7: 3, 8: 0, 9: 20, 10: 25, 11: 94, 12: 94, 13: 94}

SAFE = re.compile(r"(guardian|polic|safety|harm|election|copyright|privacy|sensitive|refus|approval|confirmation|permission|sandbox|destructive|security|escalat)", re.I)
PROD = re.compile(r"(you are chatgpt|you are codex|knowledge cutoff|current date|if you are asked what model|model identity|an agent based on gpt)", re.I)
STYLE = re.compile(r"(personality|tone|formatting|final answer|presenting|preamble|communicat|writing|style|yap|verbosity|frontend|emoji)", re.I)


def category(sec, line):
    s = sec or ""
    if SAFE.search(s):
        return "safety policy"
    if STYLE.search(s):
        return "style/behaviour"
    if PROD.search(line) and len(line.split()) < 80:
        return "product/identity"
    if re.search(r"(tool|namespace|function|exec|schema|skill|mcp|browser|image|python|web|bio|canmore|automation|plugin)", s, re.I):
        return "tools/features"
    if SAFE.search(line[:200]):
        return "safety policy"
    if STYLE.search(line[:120]):
        return "style/behaviour"
    return "tools/features"


def section_index(raw):
    ev = []
    for m in re.finditer(r"(?m)^(#{1,4}) +(.+)$|^=+ ([\w.$-]+) =+$", raw):
        ev.append((m.end(), (m.group(2) or m.group(3) or "").strip()))
    return ev


def section_at(ev, pos):
    best = ""
    for p, s in ev:
        if p <= pos:
            best = s
        else:
            break
    return best


if __name__ == "__main__":
    def load(fn):
        out, seen = collections.defaultdict(list), set()
        for row in open(os.path.join(BASE, fn)):
            d, lab, w, head = row.rstrip("\n").split("|", 3)
            if (int(d), head) in seen:
                continue
            seen.add((int(d), head))
            out[int(d)].append(("AI" if lab.startswith("A") else "Human", int(w), head))
        return out
    segs, segs_x = load("segs_openai.tsv"), load("segs_openai_extra.tsv")

    first_label, rows, labelled = {}, [], {}
    cat_era = collections.defaultdict(collections.Counter)
    for n, (label, files, d, surface) in enumerate(P.FILES):
        parts = [(KEYS[n] + ("__SAMPLE" if n in SAMPLED else "") + ".txt", segs.get(n, []))]
        if n in SAMPLED:
            parts.append((KEYS[n] + "__EXTRA.txt", segs_x.get(n, [])))
        lines, located, nseg, scored_w = [], 0, 0, 0
        for fn, sg in parts:
            text = open(os.path.join(NT, fn)).read()
            ll, loc = label_lines(n, text, sg)
            lines += ll; located += loc; nseg += len(sg); scored_w += len(text.split())
        labelled[KEYS[n]] = lines
        raw = "\n".join(P.read(f) for f in files)
        ev = section_index(raw)
        era = "2025" if d < "2026" else "2026"
        for ln, lab in lines:
            p = raw.find(ln[:50])
            sec = section_at(ev, p) if p >= 0 else ""
            for s_ in (sentences(ln) or [ln]):
                cat_era[(era, category(sec, s_))][lab] += len(s_.split())
                first_label.setdefault(norm(s_), lab)
        if n in SAMPLED:  # segment-weighted across both scoring rounds
            allseg = segs.get(n, []) + segs_x.get(n, [])
            ai = round(100 * sum(w for l, w, h in allseg if l == "AI") / sum(w for l, w, h in allseg))
        else:
            ai = OVERVIEW[n]
        rows.append((KEYS[n], label, d, surface, len(open(os.path.join(NT, KEYS[n] + ".txt")).read().split()),
                     scored_w, ai, located, nseg))

    out = {"docs": [], "sections": {}, "stock": []}
    print("### A. OpenAI: AI share of first-appearance text\n")
    print(f"{'key':30}{'date':11}{'surface':16}{'new w':>8}{'scored w':>9}{'AI':>6}{'segs':>9}")
    for k, label, d, s_, nw, sw, ai, loc, ns in rows:
        print(f"{k:30}{d:11}{s_:16}{nw:>8}{sw:>9}{ai:>5}%{loc:>5}/{ns:<3}")
        out["docs"].append(dict(key=k, model=label, date=d, surface=s_, new_words=nw, scored_words=sw, ai_new=ai))
    rate = {r[0]: r[6] / 100 for r in rows}

    print("\n### B. AI share of new text by section type and era\n")
    cats = ["safety policy", "product/identity", "style/behaviour", "tools/features"]
    print(f"{'era':8}" + "".join(f"{c:>22}" for c in cats))
    for era in ["2025", "2026"]:
        cells, row = [], []
        for c in cats:
            cc = cat_era[(era, c)]
            t = cc["AI"] + cc["Human"]
            row.append(dict(ai=round(100 * cc["AI"] / t) if t else None, n=t))
            cells.append(f"{cc['AI']/t:>12.0%} (n={t:>6})" if t else f"{'-':>22}")
        out["sections"][era] = row
        print(f"{era:8}" + "".join(cells))

    print("\n### C. Stock view: measured labels; text never scored is imputed at the rate of the prompt set where it first appeared\n")
    book = json.load(open(os.path.join(NT, "lines.json")))
    origin = {}
    for k in KEYS:
        for ln in book[k]["lines"]:
            for s_ in (sentences(ln["text"]) or [ln["text"]]):
                origin.setdefault(norm(s_), k)
    print(f"{'key':30}{'words':>8}{'AI':>7}{'Human':>7}{'AI est.':>9}{'Hum est.':>10}{'AI total':>10}")
    for k in KEYS:
        c = collections.Counter()
        for ln in book[k]["lines"]:
            for s_ in (sentences(ln["text"]) or [ln["text"]]):
                w = len(s_.split()); lab = first_label.get(norm(s_))
                if lab:
                    c[lab] += w
                else:
                    r = rate[origin.get(norm(s_), k)]
                    c["AI_est"] += w * r; c["Human_est"] += w * (1 - r)
        t = sum(c.values())
        pc = {x: round(100 * c[x] / t) for x in ["AI", "Human", "AI_est", "Human_est"]}
        tot = round(100 * (c["AI"] + c["AI_est"]) / t)
        print(f"{k:30}{round(t):>8}{pc['AI']:>6}%{pc['Human']:>6}%{pc['AI_est']:>8}%{pc['Human_est']:>9}%{tot:>9}%")
        out["stock"].append(dict(key=k, words=round(t), ai=pc["AI"], human=pc["Human"], ai_est=pc["AI_est"], human_est=pc["Human_est"], ai_total=tot,
                                 unscored=pc["AI_est"] + pc["Human_est"]))
    json.dump(out, open(os.path.join(BASE, "results/openai_results.json"), "w"), indent=1)
    json.dump({k: [[ln, lab] for ln, lab in v] for k, v in labelled.items()}, open(os.path.join(BASE, "results/openai_labelled_lines.json"), "w"))
