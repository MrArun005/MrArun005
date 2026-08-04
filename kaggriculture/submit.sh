#!/usr/bin/env bash
# Preflight + submit to the Kaggriculture competition.
#
# Checks the things that actually cause submissions to bounce, in the order they bite:
#   1. CLI installed        2. authenticated
#   3. rules accepted (you MUST click "Join Competition" in a browser once — the API
#      cannot do this for you, and this is the most common failure)
#   4. local safety suite passes
#   5. tarball built with main.py at the root
#
# Usage:  ./submit.sh "message for this submission"
set -euo pipefail
cd "$(dirname "$0")"

COMP=kaggriculture
MSG="${1:-rule engine}"
PY="${PY:-python3}"

step() { printf '\n=== %s ===\n' "$1"; }

step "1/5 kaggle CLI"
command -v kaggle >/dev/null || { echo "missing: pip install -U kaggle"; exit 1; }
kaggle --version || true

step "2/5 authentication"
if ! kaggle competitions list -s "$COMP" >/dev/null 2>&1; then
    cat <<'EOF'
Not authenticated. Pick one:
  kaggle auth login                      # browser OAuth, simplest
  # or: paste the token from https://www.kaggle.com/settings/api into
  mkdir -p ~/.kaggle && nano ~/.kaggle/access_token && chmod 600 ~/.kaggle/access_token
  # or: export KAGGLE_API_TOKEN=xxxxxxxx
EOF
    exit 1
fi
echo "authenticated ok"

step "3/5 competition rules accepted"
if kaggle competitions list --group entered 2>/dev/null | grep -q "$COMP"; then
    echo "rules accepted ok"
else
    cat <<EOF
You have not joined the competition. The API cannot accept the rules for you.

  Open  https://www.kaggle.com/competitions/$COMP
  Click "Join Competition" and accept the rules, then re-run this script.
EOF
    exit 1
fi

step "4/5 local safety suite"
"$PY" test_agent.py

step "5/5 build and submit"
FILES=(main.py env_adapter.py rules.py)
[[ -f params.json ]] && FILES+=(params.json)
rm -f submission.tar.gz
tar -czf submission.tar.gz "${FILES[@]}"
tar -tzf submission.tar.gz | sed 's/^/  /'

kaggle competitions submit "$COMP" -f submission.tar.gz -m "$MSG"

cat <<EOF

Submitted. Episodes are played asynchronously against other agents, so the score
appears over minutes-to-hours, not instantly.

  kaggle competitions submissions $COMP           # status + submission id
  kaggle competitions episodes <SUBMISSION_ID>    # games it has played
  kaggle competitions logs <EPISODE_ID> 0         # your agent's stderr (debug crashes)
  kaggle competitions replay <EPISODE_ID>         # replay JSON
  kaggle competitions leaderboard $COMP -s        # standing
EOF
