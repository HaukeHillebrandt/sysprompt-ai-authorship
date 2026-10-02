"""LaTeX tables for the paper, generated from results/*.json."""
import json, os
B = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(B, "results/plot_data.json")))
O = json.load(open(os.path.join(B, "results/openai_results.json")))
esc = lambda s: s.replace("&", "\\&").replace("_", "\\_").replace("%", "\\%")
rows = []
for d in A["leaks"]:
    rows.append(("Anthropic", d["model"], d["date"], d["surface"], d["new_words"], d["new_words"], d["ai_new"], d["stock"]["ai"], d["stock"]["human"]))
for d, s in zip(O["docs"], O["stock"]):
    rows.append(("OpenAI", d["model"], d["date"], d["surface"], d["new_words"], d["scored_words"], d["ai_new"], s["ai_total"], s["human"] + s["human_est"]))
with open(os.path.join(B, "paper/tab_docs.tex"), "w") as f:
    lab = None
    for r in rows:
        if r[0] != lab:
            if lab: f.write("\\midrule\n")
            lab = r[0]
        f.write(f"{r[0]} & {esc(r[1])} & {r[2]} & {esc(r[3])} & {r[4]:,} & {r[5]:,} & {r[6]} & {r[7]} / {r[8]} \\\\\n".replace(",", "{,}"))
print(open(os.path.join(B, "paper/tab_docs.tex")).read()[:600])
