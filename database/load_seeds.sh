#!/usr/bin/env bash
# Apply every *.sql under database/seeds/ in lexical order.
# Defaults work for the docker-compose Postgres in this repo.
#
# Usage:
#   ./database/load_seeds.sh                 # uses defaults below
#   PGHOST=… PGUSER=… ./database/load_seeds.sh
#   ./database/load_seeds.sh --dry-run       # print the commands, don't run

set -euo pipefail

PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-app}"
PGPASSWORD="${PGPASSWORD:-app}"
PGDATABASE="${PGDATABASE:-beer_and_beverages}"
export PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE

DRY=0
if [[ "${1:-}" == "--dry-run" ]]; then DRY=1; fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEEDS_DIR="$SCRIPT_DIR/seeds"

echo "Loading seeds against $PGUSER@$PGHOST:$PGPORT/$PGDATABASE"

shopt -s nullglob
for f in "$SEEDS_DIR"/*.sql; do
    printf '  → %s\n' "$(basename "$f")"
    if [[ "$DRY" == 1 ]]; then
        echo "      psql -v ON_ERROR_STOP=1 -f '$f'"
    else
        psql -v ON_ERROR_STOP=1 -f "$f" > /dev/null
    fi
done

echo "Done."
