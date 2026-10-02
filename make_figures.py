"""Paper figures (PDF) from results/*.json."""
import json, os, datetime
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "paper/figs")
os.makedirs(OUT, exist_ok=True)
A = json.load(open(os.path.join(BASE, "results/plot_data.json")))
O = json.load(open(os.path.join(BASE, "results/openai_results.json")))
S = json.load(open(os.path.join(BASE, "results/stats.json")))
AC, OC, HC, UC, RC = "#c2185b", "#1f7a8c", "#3d4556", "#d9dce2", "#b7791f"
plt.rcParams.update({"font.family": "serif", "font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "legend.frameon": False})
D = lambda s: datetime.date.fromisoformat(s)


def fig1():
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    ax.axvspan(D("2025-10-22"), D("2026-07-13"), color=OC, alpha=0.06, lw=0)
    ax.text(D("2026-02-25"), 103, "no OpenAI leaks", color=OC, ha="center", fontsize=6.5, alpha=0.9)
    for d in A["leaks"]:
        c = AC if d["surface"].startswith("claude.ai") else "#e07aa5"
        ax.scatter(D(d["date"]), d["ai_new"], s=6 + d["new_words"] ** 0.5 * 1.6, color=c, alpha=0.85, lw=0.4, edgecolor="white", zorder=3)
    for d in O["docs"]:
        ax.scatter(D(d["date"]), d["ai_new"], s=6 + d["new_words"] ** 0.5 * 1.6, color=OC, marker="s", alpha=0.85, lw=0.4, edgecolor="white", zorder=3)
    a = S["Anthropic claude.ai"]
    ax.plot([D("2024-06-20"), D("2026-02-06")], [a["pre"]["mean"]] * 2, ls="--", lw=1, color=AC)
    ax.plot([D("2026-04-16"), D("2026-09-22")], [a["post"]["mean"]] * 2, ls="--", lw=1, color=AC)
    rep = {}
    for r in A["self_reports"]:
        rep.setdefault(r["series"], []).append(r)
    for name, pts in rep.items():
        ax.plot([D(p["date"]) for p in pts], [p["value"] for p in pts], ls=":", lw=1, color=RC, marker="o", mfc="white", mec=RC, ms=4, zorder=2)
    ax.annotate("Anthropic self-report:\nAI share of approved code", (D("2025-01-15"), 3), (D("2024-10-01"), 18), fontsize=6.5, color=RC,
                arrowprops=dict(arrowstyle="-", color=RC, lw=0.5))
    ax.annotate("Anthropic self-report:\nR&D completed autonomously", (D("2026-08-15"), 26), (D("2026-05-20"), 8), fontsize=6.5, color=RC, ha="right",
                arrowprops=dict(arrowstyle="-", color=RC, lw=0.5))
    for d, txt, dx, dy in [("2026-04-16", "Opus 4.7", -60, 4), ("2025-05-27", "Codex", 8, 4), ("2026-07-14", "GPT-5.6 Sol\n(Codex app)", -12, -26)]:
        pass
    ax.text(D("2026-04-10"), 70, "Opus 4.7", fontsize=6.5, color=AC, ha="right")
    ax.axvline(D("2026-04-16"), color="#999", lw=0.5, ls=":")
    ax.set_ylim(-4, 106); ax.set_xlim(D("2024-05-15"), D("2026-10-20"))
    ax.set_ylabel("AI share of newly written text (%)")
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10])); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    h = [plt.Line2D([], [], marker="o", ls="", color=AC, label="Anthropic, claude.ai"),
         plt.Line2D([], [], marker="o", ls="", color="#e07aa5", label="Anthropic, other products"),
         plt.Line2D([], [], marker="s", ls="", color=OC, label="OpenAI (ChatGPT, Codex, Atlas)"),
         plt.Line2D([], [], ls="--", color=AC, label="Anthropic claude.ai era mean")]
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, fontsize=6.8)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig1_new_text.pdf")); plt.close(fig)


def fig2():
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.7), gridspec_kw=dict(wspace=1.05))
    rows_a = [(f"{d['model'].replace(' (agent app)', ' (app)')} ({D(d['date']).strftime('%b %y')})", d["stock"]["ai"], d["stock"]["human"], 0, 0, d["stock"]["unknown"]) for d in A["leaks"]]
    rows_o = [(f"{d['model'].replace(' (Codex app)', '')} ({D(d['date']).strftime('%b %y')})", s["ai"], s["human"], s["ai_est"], s["human_est"], 0) for d, s in zip(O["docs"], O["stock"])]
    for ax, rows, title, col in [(axes[0], rows_a, "Anthropic", AC), (axes[1], rows_o, "OpenAI", OC)]:
        y = list(range(len(rows)))[::-1]
        left = [0] * len(rows)
        for idx, (c, hatch) in enumerate([(col, None), (HC, None), (col, "////"), (HC, "////"), (UC, None)]):
            vals = [r[idx + 1] for r in rows]
            ax.barh(y, vals, left=left, color=c if not hatch else "white", edgecolor=c if hatch else "none", hatch=hatch, height=0.7, lw=0.6)
            left = [a + b for a, b in zip(left, vals)]
        ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=6.5); ax.set_xlim(0, 100)
        ax.set_title(title, fontsize=9, loc="left"); ax.set_xlabel("% of full prompt")
    h = [plt.Rectangle((0, 0), 1, 1, color=AC), plt.Rectangle((0, 0), 1, 1, color=OC), plt.Rectangle((0, 0), 1, 1, color=HC),
         plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor=OC, hatch="////"), plt.Rectangle((0, 0), 1, 1, color=UC)]
    fig.legend(h, ["AI-written at first appearance (Anthropic)", "AI-written at first appearance (OpenAI)", "human-written at first appearance",
                   "estimated from the set's measured rate (not scored)", "first seen outside the leaks"], loc="lower center", ncol=2, fontsize=6.3)
    fig.subplots_adjust(left=0.19, right=0.985, top=0.93, bottom=0.27, wspace=1.05)
    fig.savefig(os.path.join(OUT, "fig2_stock.pdf")); plt.close(fig)


def fig3():
    cats = ["Safety\npolicy", "Product &\nidentity", "Style &\nbehaviour", "Tools &\nfeatures"]
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.7), sharey=True)
    ea = list(A["sections"]["eras"].values()); eo = [O["sections"]["2025"], O["sections"]["2026"]]
    for ax, eras, labs, col, title in [(axes[0], ea, ["Jun 2024 – Feb 2026", "Apr – Sep 2026"], AC, "Anthropic"),
                                       (axes[1], eo, ["2025", "2026"], OC, "OpenAI")]:
        for j, (era, lab) in enumerate(zip(eras, labs)):
            xs = [i + (j - 0.5) * 0.38 for i in range(4)]
            vals = [c["ai"] if c["ai"] is not None and c["n"] >= 100 else 0 for c in era]
            bars = ax.bar(xs, vals, width=0.36, color=col if j else "#c9ced8", label=lab)
            for x, c in zip(xs, era):
                ax.text(x, (c["ai"] or 0) + 2, "n<100" if c["n"] < 100 else f"{c['ai']}", ha="center", fontsize=6)
        ax.set_xticks(range(4)); ax.set_xticklabels(cats, fontsize=6.5); ax.set_title(title, fontsize=9, loc="left"); ax.set_ylim(0, 112)
        ax.legend(fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2)
    axes[0].set_ylabel("AI share of new text (%)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig3_sections.pdf")); plt.close(fig)


def fig4():
    fig, ax = plt.subplots(figsize=(6.6, 2.3))
    for p in A["official_emdash"]:
        v = p["em_per10k"]
        ax.scatter(D(p["date"]), v, s=16, color=AC if v > 0 else HC, zorder=3)
    ax.axvline(D("2026-04-16"), color="#999", lw=0.5, ls=":")
    pre = [p for p in A["official_emdash"] if p["date"] < "2026-04-01"]
    ax.text(D("2025-03-01"), 12, f"{sum(p['em_per10k'] == 0 for p in pre)} of {len(pre)} versions: zero em-dashes (dashes typed as ' - ')", fontsize=7, ha="center")
    ax.text(D("2026-04-10"), 80, "Opus 4.7 onward", fontsize=7, color=AC, ha="right")
    ax.set_ylabel("em-dashes per 10k new words"); ax.set_xlim(D("2024-06-01"), D("2026-10-20"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10])); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig4_emdash.pdf")); plt.close(fig)


def fig5():
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.4))
    gaps = [r for r in A["releases"] if r["gap"]]
    ax = axes[0]
    ax.plot([D(r["date"]) for r in gaps], [r["gap"] for r in gaps], color="#888", lw=0.8)
    ax.scatter([D(r["date"]) for r in gaps], [r["gap"] for r in gaps], s=12, color=[AC if r["date"] >= "2026-03-15" else HC for r in gaps], zorder=3)
    c = S["cadence"]
    ax.plot([D("2024-10-22"), D("2026-02-17")], [c["pre"]] * 2, ls="--", color=HC, lw=0.8)
    ax.plot([D("2026-04-16"), D("2026-09-28")], [c["post"]] * 2, ls="--", color=AC, lw=0.8)
    ax.set_ylabel("days since previous model"); ax.set_title("Anthropic release gaps", fontsize=8.5, loc="left")
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7])); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax = axes[1]
    ax.plot([D(d["date"]) for d in A["leaks"] if d["surface"].startswith("claude.ai") and "styles" not in d["surface"]],
            [d["prompt_words"] for d in A["leaks"] if d["surface"].startswith("claude.ai") and "styles" not in d["surface"]], marker="o", ms=3, color=AC, lw=1, label="Anthropic claude.ai")
    ax.plot([D(d["date"]) for d in O["docs"] if d["surface"] == "ChatGPT"], [s["words"] for d, s in zip(O["docs"], O["stock"]) if d["surface"] == "ChatGPT"],
            marker="s", ms=3, color=OC, lw=1, label="OpenAI ChatGPT")
    ax.scatter([D(d["date"]) for d in O["docs"] if d["surface"] == "Codex Desktop"], [s["words"] for d, s in zip(O["docs"], O["stock"]) if d["surface"] == "Codex Desktop"],
               marker="s", s=14, facecolor="white", edgecolor=OC, label="OpenAI Codex app", zorder=3)
    ax.set_yscale("log"); ax.set_ylabel("words in leaked prompt"); ax.set_title("Prompt length", fontsize=8.5, loc="left")
    ax.legend(fontsize=6.5); ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7])); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig5_cadence.pdf")); plt.close(fig)


def fig6():
    rows = [(c["name"], c["ai"]) for c in A["controls"]]
    rows.insert(1, ("Anthropic claude.ai prompt, Jul 2024 (presumed human)", 8))
    rows.insert(2, ("Anthropic claude.ai prompt, Oct 2024 (presumed human)", 14))
    fig, ax = plt.subplots(figsize=(6.6, 2.3))
    y = list(range(len(rows)))[::-1]
    ax.barh(y, [r[1] for r in rows], color=[HC if ("human" in r[0] and r[1] < 20) else AC for r in rows], height=0.6)
    for yy, r in zip(y, rows):
        ax.text(r[1] + 1.5, yy, f"{r[1]}%", va="center", fontsize=7)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=7); ax.set_xlim(0, 110); ax.set_xlabel("Pangram 4: share labelled AI (%)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig6_controls.pdf")); plt.close(fig)


for f in (fig1, fig2, fig3, fig4, fig5, fig6):
    f()
print(sorted(os.listdir(OUT)))
