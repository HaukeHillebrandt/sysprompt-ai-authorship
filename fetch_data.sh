#!/usr/bin/env bash
# Re-download the third-party texts this analysis uses. They are not redistributed in this repo.
#  - leaked prompts: github.com/elder-plinius/CL4R1T4S at the commit used for the analysis
#  - official Anthropic claude.ai prompts: Anthropic release notes (pages may have changed since 30 Sep 2026)
#  - Anthropic's May 2023 constitution post (human-written detector control)
set -euo pipefail
cd "$(dirname "$0")"
COMMIT=a4d3da04e63324e794a65500c3e41994fc4ab02e

if [ ! -d CL4R1T4S/.git ]; then
  git clone --quiet https://github.com/elder-plinius/CL4R1T4S.git CL4R1T4S
fi
git -C CL4R1T4S checkout --quiet "$COMMIT"

mkdir -p official
for m in claude-haiku-3 claude-opus-3 claude-haiku-3-5 claude-sonnet-3-5 claude-sonnet-3-7 claude-sonnet-4 claude-opus-4 \
         claude-opus-4-1 claude-sonnet-4-5 claude-haiku-4-5 claude-opus-4-5 claude-opus-4-6 claude-sonnet-4-6 claude-opus-4-7 \
         claude-opus-4-8 claude-fable-5 claude-sonnet-5 claude-opus-5 claude-fable-5-1 claude-opus-5-5 claude-sonnet-5-5; do
  curl -sL -o "official/$m.md" "https://platform.claude.com/docs/en/release-notes/system-prompts/$m.md"
done

mkdir -p calib
curl -sL "https://www.anthropic.com/news/claudes-constitution" -o calib/constitution2023.html
python3 - <<'EOF'
import re, html
t = open("calib/constitution2023.html", encoding="utf-8", errors="ignore").read()
t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
t = html.unescape(re.sub(r"<[^>]+>", "\n", t)); t = re.sub(r"[ \t]+", " ", t); t = re.sub(r"\n\s*\n+", "\n", t)
body = t[t.find("How does a language model decide"):]
for end in ["Share on", "Related content", "Get the developer newsletter", "Product updates"]:
    k = body.find(end)
    if k > 0: body = body[:k]
body = re.sub(r"\n(?=[a-z,.;:)\]’])|(?<=[a-z,(])\n", " ", body)
open("calib/C_H_constitution_2023.txt", "w").write(body.strip())
EOF
echo "Fetched leaks (commit ${COMMIT:0:7}), $(ls official | wc -l | tr -d ' ') official prompt pages, and the 2023 constitution control."
