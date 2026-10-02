"""Clean, self-explanatory headline figure (paper Figure 1 and LessWrong post)."""
import json, os, datetime
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

BASE = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(BASE, "results/plot_data.json")))
O = json.load(open(os.path.join(BASE, "results/openai_results.json")))
S = json.load(open(os.path.join(BASE, "results/stats.json")))
AC, OC, GREY, INK = "#c2185b", "#1f7a8c", "#8a8f99", "#1d2129"
D = lambda s: datetime.date.fromisoformat(s)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.spines.left": False, "axes.linewidth": 0.8})

fig, ax = plt.subplots(figsize=(8, 5.2))
fig.subplots_adjust(left=0.13, right=0.97, top=0.8, bottom=0.17)
size = lambda w: 22 + min(w ** 0.5, 100) * 1.1

for v in (0, 25, 50, 75, 100):
    ax.axhline(v, color="#e6e8ec", lw=0.8, zorder=0)
ax.scatter([D(d["date"]) for d in A["leaks"]], [d["ai_new"] for d in A["leaks"]],
           s=[size(d["new_words"]) for d in A["leaks"]], color=AC, alpha=0.85, edgecolor="white", lw=0.8, zorder=3)
ax.scatter([D(d["date"]) for d in O["docs"]], [d["ai_new"] for d in O["docs"]],
           s=[size(d["new_words"]) for d in O["docs"]], color=OC, marker="s", alpha=0.85, edgecolor="white", lw=0.8, zorder=3)

a = S["Anthropic claude.ai"]
ax.plot([D("2024-06-20"), D("2026-02-06")], [a["pre"]["mean"]] * 2, ls="--", lw=1.4, color=AC, zorder=2)
ax.plot([D("2026-04-16"), D("2026-09-22")], [a["post"]["mean"]] * 2, ls="--", lw=1.4, color=AC, zorder=2)
ax.text(D("2024-07-10"), a["pre"]["mean"] + 3.5, f"Anthropic average {a['pre']['mean']:.0f}%", color=AC, fontsize=9.5, fontweight="bold")
ax.text(D("2026-04-10"), a["post"]["mean"] + 4.5, f"average {a['post']['mean']:.0f}%", color=AC, fontsize=9.5, fontweight="bold", ha="right")

ax.axvline(D("2026-04-16"), color=GREY, lw=1, ls=":", zorder=1)
ax.text(D("2026-04-08"), 5, "Claude Opus 4.7\n(Apr 2026)", color=GREY, fontsize=8.5, ha="right", va="bottom")

ax.text(D("2026-10-25"), 91, "Anthropic", color=AC, fontsize=10.5, fontweight="bold", va="center")
ax.text(D("2026-10-25"), 99, "OpenAI", color=OC, fontsize=10.5, fontweight="bold", va="center")
ax.text(D("2025-03-01"), 15, "OpenAI\n(ChatGPT, Codex)", color=OC, fontsize=9, ha="center", va="top")

ax.set_ylim(-3, 104)
ax.set_xlim(D("2024-05-20"), D("2027-02-20"))
ax.set_yticks([0, 25, 50, 75, 100]); ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
ax.tick_params(axis="y", length=0, colors=INK); ax.tick_params(axis="x", colors=INK)
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7])); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.set_ylabel("Share of new system-prompt text\njudged AI-written", color=INK)

fig.text(0.13, 0.94, "Frontier labs' system prompts are now mostly AI-written", fontsize=14.5, fontweight="bold", color=INK)
fig.text(0.13, 0.875, "Each dot is one released system prompt (Anthropic, OpenAI). Only text added in that release is scored;\n"
         "dot size shows how much text was added. Judged by the Pangram AI-text detector.", fontsize=9.3, color="#4a5263", va="center")
fig.text(0.13, 0.035, "Sources: Anthropic release notes; leaked prompts (github.com/elder-plinius/CL4R1T4S). "
         "Preliminary, AI-assisted analysis:\ngithub.com/HaukeHillebrandt/sysprompt-ai-authorship", fontsize=7.6, color=GREY)

out = os.path.join(BASE, "paper/figs")
fig.savefig(os.path.join(out, "fig_main.png"), dpi=200)
fig.savefig(os.path.join(out, "fig_main.pdf"))
print("saved")
