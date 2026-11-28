#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

rm -rf mutants
trap 'rm -rf mutants' EXIT

read -r -a chosen <<< "${MUTMUT_MUTANTS:-}"
log="$(mktemp)"
if ! mutmut run --max-children "${MUTMUT_CHILDREN:-4}" "${chosen[@]}" 2>&1 | tee "$log"; then
  if grep -q 'Filtered for specific mutants, but nothing matches' "$log"; then
    echo "the changed modules have no mutants: ${MUTMUT_MUTANTS}"
    exit 0
  fi
  exit 1
fi
mutmut export-cicd-stats

python - <<'PY'
import json
import sys
from pathlib import Path

stats = json.loads(Path('mutants/mutmut-cicd-stats.json').read_text())
print(json.dumps(stats, indent=2))
tested = stats['killed'] + stats['survived'] + stats['timeout']
if not tested:
    print('no mutants were tested, mutmut did not run properly')
    sys.exit(1)
if stats['survived'] or stats['suspicious']:
    print('some mutants survived, see `mutmut results` and `mutmut show`')
    sys.exit(1)
print(f'all {tested} mutants were killed')
PY
