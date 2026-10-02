"""Collect every series used in the write-up into results/plot_data.json."""
import re, os, glob, json, datetime, collections
from leak_markers import FILES, load, EM, HY
from prep_newtext import norm, sentences, units, leak_text
import analyze as A

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_NAME = ["Sonnet 3.5", "Claude Code", "User styles", "Sonnet 3.7", "Claude 4", "Opus 4.1*", "Sonnet 4.5",
              "Opus 4.5", "Opus 4.6", "Opus 4.7", "Claude Design", "Fable 5", "Opus 5", "Fable 5.1", "Opus 5.5 (agent app)"]
CONTROLS = [("Anthropic constitution post, May 2023 (human)", 0), ("Claude rewrite of 2024 prompt", 100),
            ("Claude rewrite of 2024 excerpt", 100), ("Claude rewrite of Claude 4 section", 91),
            ("Claude rewrite of tool description", 100), ("Light Claude edit of human text (~1/4 sentences)", 43)]
SELF_REPORTS = [
    {"date": "2025-01-15", "series": "AI share of approved code (Anthropic)", "value": 3},
    {"date": "2026-05-15", "series": "AI share of approved code (Anthropic)", "value": 80},
    {"date": "2026-03-15", "series": "R&D work completed autonomously (Anthropic)", "value": 1},
    {"date": "2026-08-15", "series": "R&D work completed autonomously (Anthropic)", "value": 26},
]


def official_entries():
    ent = []
    for f in glob.glob(os.path.join(BASE, "official/*.md")):
        m = os.path.basename(f)[:-3]
        t = open(f, encoding="utf-8").read()
        parts = re.split(r"^## (.+)$", t, flags=re.M)
        for i in range(1, len(parts), 2):
            try:
                d = datetime.datetime.strptime(parts[i].strip(), "%B %d, %Y").date()
            except ValueError:
                continue
            ent.append((d, m, re.sub(r"^```.*$", "", parts[i + 1], flags=re.M).replace("\\n", "\n")))
    return sorted(ent)


if __name__ == "__main__":
    out = {}
    stock = {}
    for line in open(os.path.join(BASE, "results/analysis_output.txt")):
        m = re.match(r"(\d\d_\S+)\s+(\d+)\s+(\d+)%\s+(\d+)%\s+(\d+)%", line)
        if m:
            stock[m.group(1)] = dict(words=int(m.group(2)), ai=int(m.group(3)), human=int(m.group(4)), unknown=int(m.group(5)))
    leaks = []
    for n, (f, d, surface) in enumerate(FILES):
        nt = open(os.path.join(BASE, "newtext", A.LABELS[n] + ".txt")).read()
        em, hy = len(EM.findall(nt)), len(HY.findall(nt))
        leaks.append(dict(n=n, model=MODEL_NAME[n], date=d, surface=surface, new_words=len(nt.split()),
                          ai_new=A.OVERVIEW[n], em_share_new=round(em / (em + hy), 3) if em + hy else None,
                          em_per10k_new=round(em / max(len(nt.split()), 1) * 1e4, 1),
                          prompt_words=stock[A.LABELS[n]]["words"], stock=stock[A.LABELS[n]]))
    out["leaks"] = leaks
    out["extra"] = [dict(model="Opus 5.5 skill instructions", date="2026-09-22", ai_new=100, new_words=13919),
                    dict(model="Opus 5.5 reference files (sample)", date="2026-09-22", ai_new=99, new_words=7214)]

    sec = {}
    for line in open(os.path.join(BASE, "results/analysis_output.txt")):
        m = re.match(r"(2024-06\.\.2026-02|2026-04\.\.2026-09)\s+(.*)", line)
        if m:
            cells = re.findall(r"(\d+)% \(n=\s*(\d+)\)", m.group(2))
            sec[m.group(1)] = [dict(ai=int(a), n=int(b)) for a, b in cells]
    out["sections"] = dict(categories=["Safety policy", "Product & identity", "Style & behaviour", "Tools & features"],
                           eras=sec)

    ent = official_entries()
    first = {}
    for d, m, _ in ent:
        first.setdefault(m, d)
    rel = sorted((d, m) for m, d in first.items())
    out["releases"] = [dict(model=m, date=str(d), gap=(d - rel[i - 1][0]).days if i else None) for i, (d, m) in enumerate(rel)]

    seen, q, off_em = set(), collections.defaultdict(lambda: [0, 0]), []
    for d, m, b in ent:
        new = []
        for ln in units(b):
            for s in (sentences(ln) or [ln]):
                k = norm(s)
                if k not in seen:
                    seen.add(k)
                    new.append(s)
        t = " ".join(new)
        w = len(t.split())
        key = f"{d.year}-Q{(d.month - 1) // 3 + 1}"
        q[key][0] += w
        q[key][1] += 1
        em, hy = len(EM.findall(t)), len(HY.findall(t))
        if w >= 50:
            off_em.append(dict(date=str(d), model=m, new_words=w, em_per10k=round(em / w * 1e4, 1),
                               em_share=round(em / (em + hy), 3) if em + hy else None))
    out["official_quarterly"] = [dict(quarter=k, new_words=v[0], updates=v[1]) for k, v in sorted(q.items())]
    out["official_emdash"] = off_em
    out["official_pangram_full"] = [dict(date="2024-07-12", model="Sonnet 3.5", ai=8), dict(date="2024-10-22", model="Sonnet 3.5", ai=14),
                                    dict(date="2026-02-17", model="Sonnet 4.6", ai=11), dict(date="2026-04-16", model="Opus 4.7", ai=21),
                                    dict(date="2026-09-22", model="Opus 5.5", ai=66)]
    out["controls"] = [dict(name=a, ai=b) for a, b in CONTROLS]
    out["self_reports"] = SELF_REPORTS
    json.dump(out, open(os.path.join(BASE, "results/plot_data.json"), "w"), indent=1)
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in out.items() if k != "sections"}))
    print(json.dumps(out["sections"]))
