"""Build first-appearance ("newly written") text for each leaked Anthropic prompt.

Unit = line (paragraph / list item / tool-description line). A line counts as NEW if at least
half of its words sit in sentences never seen before in (a) any earlier leak or (b) any official
claude.ai prompt entry dated strictly earlier. Model names and dates are normalised so that
"This iteration of Claude is Claude Opus 4.7" does not count as new text in Opus 5.
Outputs: newtext/<nn>_<label>.txt (+ .docx) and newtext/lines.json (line-level bookkeeping).
"""
import re, json, os, glob, datetime, subprocess, collections
from leak_markers import FILES, load, split_prose_tools, opus55_components, EM, HY

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "newtext")
os.makedirs(OUT, exist_ok=True)

MODEL = re.compile(r"claude[ -]?(opus|sonnet|haiku|fable|mythos)?[ -]?\d(\.\d)?([ -]\d)?|claude (opus|sonnet|haiku|fable|mythos)", re.I)
DATE = re.compile(r"(january|february|march|april|may|june|july|august|september|october|november|december) \d{1,2},? \d{4}|\d{4}-\d{2}-\d{2}|\{\{currentdatetime\}\}", re.I)


def norm(s):
    s = s.lower()
    s = MODEL.sub(" MODEL ", s)
    s = DATE.sub(" DATE ", s)
    s = re.sub(r"[—–]| - | -- ", " ", s)
    s = re.sub(r"\{antml:|\{/antml:|</?|/?>|[{}*#`\"'“”‘’]", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def sentences(line):
    return [x for x in re.split(r"(?<=[.!?:;])\s+", line) if len(x.split()) >= 4]


def units(text):
    out = []
    for ln in text.split("\n"):
        ln = ln.strip()
        if not ln or re.fullmatch(r"(</?[\w\-]+>|\{/?[\w\-]+\}|[-=#*_ ]+|```\w*)", ln):
            continue
        if len(ln.split()) < 3:
            continue
        out.append(ln)
    return out


def official_entries():
    ent = []
    for f in glob.glob(os.path.join(BASE, "official/*.md")):
        t = open(f, encoding="utf-8").read()
        parts = re.split(r"^## (.+)$", t, flags=re.M)
        for i in range(1, len(parts), 2):
            try:
                d = datetime.datetime.strptime(parts[i].strip(), "%B %d, %Y").date()
            except ValueError:
                continue
            body = re.sub(r"^```.*$", "", parts[i + 1], flags=re.M).replace("\\n", "\n")
            ent.append((d, body))
    return sorted(ent)


def leak_text(f):
    t = load(f)
    if f == "CLAUDE-OPUS-5.5.md":
        c = opus55_components(t)
        return {"prompt": c["system prompt: prose"] + "\n" + c["system prompt: tool descriptions"],
                "skills": c["skill bodies"], "artifact_refs": c["artifact-type reference files"]}
    p, tl = split_prose_tools(t)
    return {"prompt": p + "\n" + tl}


if __name__ == "__main__":
    off = official_entries()
    seen = set()
    rows, bookkeeping = [], {}
    oi = 0
    for n, (f, d, surface) in enumerate(FILES):
        dd = datetime.date.fromisoformat(d)
        while oi < len(off) and off[oi][0] < dd:  # official text published strictly earlier
            for ln in units(off[oi][1]):
                seen.update(norm(s) for s in sentences(ln))
            oi += 1
        parts = leak_text(f)
        for part, text in parts.items():
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
            label = f"{n:02d}_{os.path.splitext(f)[0]}" + ("" if part == "prompt" else f"__{part}")
            bookkeeping[label] = {"file": f, "date": d, "surface": surface, "part": part, "lines": all_lines}
            nt = "\n\n".join(new_lines)
            rows.append((label, d, surface, len(text.split()), len(nt.split()),
                         len(EM.findall(nt)), len(HY.findall(nt))))
            open(os.path.join(OUT, label + ".txt"), "w").write(nt)
            for ln in us:
                seen.update(norm(s) for s in sentences(ln))
    json.dump(bookkeeping, open(os.path.join(OUT, "lines.json"), "w"))
    print(f"{'label':52}{'date':11}{'total':>8}{'NEW':>8}{'em%':>6}")
    for label, d, s, tw, nw, em, hy in rows:
        sh = f"{em/(em+hy):.0%}" if em + hy else "  -"
        print(f"{label:52}{d:11}{tw:>8}{nw:>8}{sh:>6}")
    print("total new words:", sum(r[4] for r in rows),
          "| excl. 5.5 skills/artifact refs:", sum(r[4] for r in rows if "__" not in r[0]))
