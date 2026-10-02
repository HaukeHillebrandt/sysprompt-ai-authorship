"""Systematic sample of contiguous ~600-word blocks from the two large 2026 Codex-app new-text files."""
import os, random
D = "newtext_openai"
TARGET, BLOCK = 30000, 600
random.seed(20261001)
for key in ["11_GPT_5.6_Sol_Codex_app", "12_GPT_6_Astra_Codex_app"]:
    lines = open(os.path.join(D, key + ".txt")).read().split("\n\n")
    pos, cum = 0, []
    for ln in lines:
        cum.append(pos); pos += len(ln.split())
    nblocks = TARGET // BLOCK; step = pos / nblocks; start = random.uniform(0, step)
    chosen, i = [], 0
    for b in range(nblocks):
        p = start + b * step
        while i < len(lines) and cum[i] < p: i += 1
        w = 0
        while i < len(lines) and w < BLOCK:
            chosen.append(i); w += len(lines[i].split()); i += 1
    chosen = sorted(set(chosen))
    open(os.path.join(D, key + "__SAMPLE.txt"), "w").write("\n\n".join(lines[j] for j in chosen))
    open(os.path.join(D, key + "__SAMPLE_idx.txt"), "w").write(" ".join(map(str, chosen)))
    print(key, "sampled", sum(len(lines[j].split()) for j in chosen), "of", pos, "words,", len(chosen), "of", len(lines), "lines")
