"""First-appearance text for the leaked OpenAI prompts (same rules as prep_newtext.py).

Differences from the Anthropic pipeline: no official dated series to seed the 'seen' pool, tool schemas are
read from JSON files by walking every "description" field, and code-only lines (TypeScript tool signatures)
are dropped while their // comments are kept.
"""
import re, os, json
from prep_newtext import norm, sentences
from leak_markers import EM, HY

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "CL4R1T4S/OPENAI")
OUT = os.path.join(BASE, "newtext_openai")
os.makedirs(OUT, exist_ok=True)

FILES = [  # (label, [files], content date, surface)
    ("GPT-4.5", ["GPT-4.5_02-27-25.md"], "2025-02-27", "ChatGPT"),
    ("o3 / o4-mini", ["ChatGPT_o3_o4-mini_04-16-2025"], "2025-04-16", "ChatGPT"),
    ("GPT-4o (Apr)", ["ChatGPT_4o_04-25-2025.txt"], "2025-04-25", "ChatGPT"),
    ("Personality v2", ["ChatGPT_Personality_v2_Change.md"], "2025-04-28", "ChatGPT"),
    ("GPT-4.1", ["ChatGPT_4.1_05-15-2025.txt"], "2025-05-15", "ChatGPT"),
    ("Codex (cloud)", ["Codex.md"], "2025-05-27", "Codex"),
    ("GPT-5", ["ChatGPT5-08-07-2025.mkd"], "2025-08-07", "ChatGPT"),
    ("Codex (Sep)", ["Codex_Sep-15-2025.md"], "2025-09-15", "Codex"),
    ("GPT-4o (Sep)", ["ChatGPT-4o_Sep-27-25.txt"], "2025-09-27", "ChatGPT"),
    ("ChatKit Studio", ["ChatKit_Docs__Oct-6-25.txt"], "2025-10-06", "ChatKit Studio"),
    ("Atlas", ["Atlas_10-21-25.txt"], "2025-10-21", "Atlas browser"),
    ("GPT-5.6 Sol (Codex app)", ["Codex_Desktop/5.6-Sol_SystemPrompt.md", "Codex_Desktop/5.6-Sol_Tools.json"], "2026-07-14", "Codex Desktop"),
    ("GPT-6 Astra (Codex app)", ["Codex_Desktop/GPT-6-Astra_Tools.json", "Codex_Desktop/GPT-6-Astra_Prompts.md"], "2026-09-09", "Codex Desktop"),
    ("GPT-6 Sol (Codex app)", ["Codex_Desktop/GPT-6-Sol_Prompts.txt", "Codex_Desktop/GPT-6-Sol_Tools.json"], "2026-09-22", "Codex Desktop"),
]

CODEISH = re.compile(r"(=>|[{};]|^\s*(type|namespace|declare|const|function|import|export)\b|^\s*[\w.]+\??:\s*[\w\[\]|\"']+,?\s*$)")


def json_descriptions(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("description", "instructions", "prompt") and isinstance(v, str):
                out.append(v)
            else:
                json_descriptions(v, out)
    elif isinstance(obj, list):
        for v in obj:
            json_descriptions(v, out)


def read(f):
    t = open(os.path.join(SRC, f), encoding="utf-8", errors="ignore").read()
    if f.endswith(".json"):
        out = []
        json_descriptions(json.loads(t), out)
        return "\n".join(out)
    return t


def units(text):
    out = []
    for ln in text.split("\n"):
        ln = ln.strip()
        if ln.startswith("//"):
            ln = ln.lstrip("/ ").strip()
        elif CODEISH.search(ln) and len(re.findall(r"\b[a-z]{3,}\b", ln)) < 6:
            continue
        if not ln or re.fullmatch(r"(</?[\w\-]+>|[-=#*_ ]+|```\w*|=+ [\w.$]+ =+)", ln):
            continue
        if len(ln.split()) < 3:
            continue
        out.append(ln)
    return out


if __name__ == "__main__":
    seen, rows, book = set(), [], {}
    for n, (label, files, d, surface) in enumerate(FILES):
        text = "\n".join(read(f) for f in files)
        us = units(text)
        new_lines, all_lines = [], []
        for ln in us:
            ss = sentences(ln) or [ln]
            w_new = sum(len(s.split()) for s in ss if norm(s) not in seen)
            w_all = sum(len(s.split()) for s in ss)
            is_new = w_all > 0 and w_new / w_all >= 0.5
            all_lines.append({"text": ln, "new": is_new})
            if is_new:
                new_lines.append(ln)
        for ln in us:
            seen.update(norm(s) for s in sentences(ln))
        key = f"{n:02d}_{re.sub(r'[^A-Za-z0-9.]+', '_', label).strip('_')}"
        book[key] = {"label": label, "files": files, "date": d, "surface": surface, "lines": all_lines}
        nt = "\n\n".join(new_lines)
        open(os.path.join(OUT, key + ".txt"), "w").write(nt)
        em, hy = len(EM.findall(nt)), len(HY.findall(nt))
        tw = sum(len(l.split()) for l in us)
        rows.append((key, d, surface, tw, len(nt.split()), em, hy))
    json.dump(book, open(os.path.join(OUT, "lines.json"), "w"))
    print(f"{'key':34}{'date':11}{'surface':16}{'prompt w':>9}{'NEW w':>8}{'em%':>6}{'em/10k':>8}")
    for key, d, s, tw, nw, em, hy in rows:
        sh = f"{em/(em+hy):.0%}" if em + hy else "  -"
        print(f"{key:34}{d:11}{s:16}{tw:>9}{nw:>8}{sh:>6}{em/max(nw,1)*1e4:>8.1f}")
    print("total new words:", sum(r[4] for r in rows))
