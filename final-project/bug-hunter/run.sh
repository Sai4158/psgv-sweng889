#!/usr/bin/env bash
set -euo pipefail
project_root="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
project_python="$project_root/.venv/bin/python"
if [[ ! -x "$project_python" ]]; then
    printf '%s\n' 'Create .venv with Python 3.11+ and install requirements.txt first. See README.md.' >&2
    exit 1
fi
exec "$project_python" "$project_root/launch.py" "$@"
