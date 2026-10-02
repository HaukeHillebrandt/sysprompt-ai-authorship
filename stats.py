"""Summary statistics for the paper: era means with document-cluster bootstrap CIs, change-point search,
pre-break drift, misclassification-corrected shares, and release-cadence test."""
import json, os, random, datetime, statistics

BASE = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(BASE, "results/plot_data.json")))
O = json.load(open(os.path.join(BASE, "results/openai_results.json")))
random.seed(7)
B = 10000
yr = lambda d: (datetime.date.fromisoformat(d) - datetime.date(2024, 1, 1)).days / 365.25


def wmean(docs):
    w = sum(d["w"] for d in docs)
    return sum(d["ai"] * d["w"] for d in docs) / w


def boot(docs):
    vals = sorted(wmean([random.choice(docs) for _ in docs]) for _ in range(B))
    return vals[int(0.025 * B)], vals[int(0.975 * B)]


def wslope(docs):
    w = [d["w"] for d in docs]; x = [yr(d["date"]) for d in docs]; y = [d["ai"] for d in docs]
    sw = sum(w); mx = sum(a * b for a, b in zip(w, x)) / sw; my = sum(a * b for a, b in zip(w, y)) / sw
    sxx = sum(a * (b - mx) ** 2 for a, b in zip(w, x))
    return sum(a * (b - mx) * (c - my) for a, b, c in zip(w, x, y)) / sxx if sxx else 0.0


def changepoint(docs):
    docs = sorted(docs, key=lambda d: d["date"])
    best = None
    for k in range(2, len(docs) - 1):
        l, r = docs[:k], docs[k:]
        sse = sum(d["w"] * (d["ai"] - wmean(l)) ** 2 for d in l) + sum(d["w"] * (d["ai"] - wmean(r)) ** 2 for d in r)
        if best is None or sse < best[0]:
            best = (sse, l[-1], r[0])
    return best


def correct(p, fpr, tpr):
    return max(0.0, min(100.0, 100 * (p / 100 - fpr) / (tpr - fpr)))


out = {}
anth = [dict(model=d["model"], date=d["date"], ai=d["ai_new"], w=d["new_words"], surface=d["surface"]) for d in A["leaks"]]
anth_ai = [d for d in anth if d["surface"].startswith("claude.ai") and "styles" not in d["surface"]]
oai = [dict(model=d["model"], date=d["date"], ai=d["ai_new"], w=d["new_words"], surface=d["surface"]) for d in O["docs"]]

print("== Era means (word-weighted AI share of new text), 95% document-cluster bootstrap CI")
for name, docs, split in [("Anthropic claude.ai", anth_ai, "2026-03-01"), ("Anthropic all surfaces", anth, "2026-03-01"),
                          ("OpenAI all surfaces", oai, "2026-01-01")]:
    pre = [d for d in docs if d["date"] < split]; post = [d for d in docs if d["date"] >= split]
    r = {}
    for lab, g in [("pre", pre), ("post", post)]:
        m = wmean(g); lo, hi = boot(g) if len(g) > 1 else (m, m)
        r[lab] = dict(mean=round(m, 1), lo=round(lo, 1), hi=round(hi, 1), n_docs=len(g), words=sum(d["w"] for d in g))
        print(f"  {name:24} {lab:4} {m:5.1f}%  [{lo:5.1f}, {hi:5.1f}]  docs={len(g)} words={sum(d['w'] for d in g)}")
    out[name] = r

print("\n== Change point (weighted two-mean SSE)")
for name, docs in [("Anthropic claude.ai", anth_ai), ("Anthropic all surfaces", anth), ("OpenAI all surfaces", oai)]:
    sse, l, r = changepoint(docs)
    print(f"  {name:24} between {l['model']} ({l['date']}) and {r['model']} ({r['date']})")
    out.setdefault("changepoints", {})[name] = [l["model"], l["date"], r["model"], r["date"]]

print("\n== Drift before the break (weighted OLS slope, percentage points per year; bootstrap CI)")
for name, docs, split in [("Anthropic claude.ai", anth_ai, "2026-03-01"), ("OpenAI all surfaces", oai, "2026-01-01")]:
    pre = [d for d in docs if d["date"] < split]
    s = wslope(pre)
    bs = sorted(wslope([random.choice(pre) for _ in pre]) for _ in range(B))
    bs = [v for v in bs if v == v]
    print(f"  {name:24} slope {s:+.1f} pp/yr  [{bs[int(.025*len(bs))]:+.1f}, {bs[int(.975*len(bs))]:+.1f}]  (n={len(pre)})")
    out.setdefault("drift", {})[name] = dict(slope=round(s, 1), lo=round(bs[int(.025 * len(bs))], 1), hi=round(bs[int(.975 * len(bs))], 1))

print("\n== Misclassification correction q = (p - FPR)/(TPR - FPR)")
for fpr, tpr, tag in [(0.0, 0.97, "FPR 0 (2023 human control), TPR 0.97 (mean of AI controls)"),
                      (0.11, 0.97, "FPR 0.11 (mean of 2024 official prompts, upper bound), TPR 0.97")]:
    a = out["Anthropic claude.ai"]; o = out["OpenAI all surfaces"]
    print(f"  {tag}: Anthropic {correct(a['pre']['mean'],fpr,tpr):.0f}% -> {correct(a['post']['mean'],fpr,tpr):.0f}%;"
          f" OpenAI {correct(o['pre']['mean'],fpr,tpr):.0f}% -> {correct(o['post']['mean'],fpr,tpr):.0f}%")

print("\n== Release cadence (Anthropic, days between new models; same-day launches dropped)")
gaps = [r for r in A["releases"] if r["gap"]]
pre = [r["gap"] for r in gaps if r["date"] < "2026-03-15"]; post = [r["gap"] for r in gaps if r["date"] >= "2026-03-15"]
obs = statistics.median(pre) - statistics.median(post)
allg = pre + post; cnt = 0
for _ in range(B):
    random.shuffle(allg)
    if statistics.median(allg[:len(pre)]) - statistics.median(allg[len(pre):]) >= obs:
        cnt += 1
print(f"  median before {statistics.median(pre)} (n={len(pre)}), after {statistics.median(post)} (n={len(post)}); one-sided permutation p = {cnt/B:.3f}")
out["cadence"] = dict(pre=statistics.median(pre), post=statistics.median(post), n_pre=len(pre), n_post=len(post), p=round(cnt / B, 3))
json.dump(out, open(os.path.join(BASE, "results/stats.json"), "w"), indent=1)
