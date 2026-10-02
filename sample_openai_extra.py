"""Second scoring round (1 Oct 2026): every unsampled new line of GPT-5.6 Sol, plus a systematic sample of ~25k words
from the unsampled new lines of GPT-6 Astra (budget: ~600 Pangram credits)."""
import os, random
D = "newtext_openai"
random.seed(20261002)
for key, target in [("11_GPT_5.6_Sol_Codex_app", None), ("12_GPT_6_Astra_Codex_app", 25000)]:
    lines = open(os.path.join(D, key + ".txt")).read().split("\n\n")
    done = set(map(int, open(os.path.join(D, key + "__SAMPLE_idx.txt")).read().split()))
    rest = [i for i in range(len(lines)) if i not in done]
    if target is None:
        chosen = rest
    else:
        pos, cum = 0, []
        for i in rest:
            cum.append(pos); pos += len(lines[i].split())
        nblocks = target // 600; step = pos / nblocks; start = random.uniform(0, step); chosen, j = [], 0
        for b in range(nblocks):
            p = start + b * step
            while j < len(rest) and cum[j] < p: j += 1
            w = 0
            while j < len(rest) and w < 600:
                chosen.append(rest[j]); w += len(lines[rest[j]].split()); j += 1
        chosen = sorted(set(chosen))
    open(os.path.join(D, key + "__EXTRA.txt"), "w").write("\n\n".join(lines[i] for i in chosen))
    open(os.path.join(D, key + "__EXTRA_idx.txt"), "w").write(" ".join(map(str, chosen)))
    print(key, "extra lines", len(chosen), "words", sum(len(lines[i].split()) for i in chosen),
          "| remaining unscored new words", sum(len(lines[i].split()) for i in range(len(lines)) if i not in done and i not in set(chosen)))
