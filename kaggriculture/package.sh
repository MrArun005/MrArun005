#!/usr/bin/env bash
# Build the submission tarball, but only if the safety suite passes.
#
# A Kaggriculture submission needs main.py at the tar root; sibling modules ride along and
# are importable because the loader puts the archive's directory on sys.path.
#
# Usage:  ./package.sh [python]
set -euo pipefail

cd "$(dirname "$0")"
PY="${1:-python3}"

echo "== submission checks =="
"$PY" test_agent.py

echo
echo "== packaging =="
FILES=(main.py env_adapter.py rules.py)
[[ -f params.json ]] && FILES+=(params.json) || echo "note: no params.json, shipping Params defaults"

rm -f submission.tar.gz
tar -czf submission.tar.gz "${FILES[@]}"
tar -tzf submission.tar.gz | sed 's/^/  /'
echo "built submission.tar.gz ($(du -h submission.tar.gz | cut -f1))"

cat <<'EOF'

Next:
  kaggle competitions submit kaggriculture -f submission.tar.gz -m "rule engine v1"
  kaggle competitions submissions kaggriculture
EOF
