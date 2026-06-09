#!/usr/bin/env bash
# Verify every tool required by SETUP.md is installed and report its version.
# Exits with a non-zero status if anything is missing.

set -u

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

missing=0
warnings=0

ok()    { printf "${GREEN}✓${RESET} %-18s %s\n" "$1" "$2"; }
fail()  { printf "${RED}✗${RESET} %-18s %s\n" "$1" "$2"; missing=$((missing+1)); }
warn()  { printf "${YELLOW}⚠${RESET} %-18s %s\n" "$1" "$2"; warnings=$((warnings+1)); }

# --- Required ---
check_required() {
  local name="$1" cmd="$2" version_cmd="$3" hint="$4"
  if command -v "$cmd" >/dev/null 2>&1; then
    local v
    v=$(eval "$version_cmd" 2>/dev/null | head -n1)
    ok "$name" "$v"
  else
    fail "$name" "not installed — $hint"
  fi
}

# --- Optional ---
check_optional() {
  local name="$1" cmd="$2" version_cmd="$3" hint="$4"
  if command -v "$cmd" >/dev/null 2>&1; then
    local v
    v=$(eval "$version_cmd" 2>/dev/null | head -n1)
    ok "$name" "$v"
  else
    warn "$name" "not installed — optional ($hint)"
  fi
}

echo "Required tools"
echo "──────────────"
check_required "git"       "git"     "git --version"                    "see SETUP §1"
check_required "docker"    "docker"  "docker --version"                 "see SETUP §2"
check_required "compose"   "docker"  "docker compose version"           "comes with Docker — see SETUP §2"
check_required "uv"        "uv"      "uv --version"                     "see SETUP §3"
check_required "python3.12" "python3.12" "python3.12 --version"         "uv python install 3.12"
check_required "node"      "node"    "node --version"                   "see SETUP §4"
check_required "npm"       "npm"     "npm --version"                    "ships with Node"
check_required "pnpm"      "pnpm"    "pnpm --version"                   "npm install -g pnpm"
check_required "eas-cli"   "eas"     "eas --version"                    "npm install -g eas-cli"
check_required "psql"      "psql"    "psql --version"                   "sudo apt install postgresql-client"
check_required "code"      "code"    "code --version"                   "see SETUP §6"
check_required "make"      "make"    "make --version"                   "sudo apt install build-essential"
check_required "curl"      "curl"    "curl --version"                   "sudo apt install curl"

echo
echo "Optional tools"
echo "──────────────"
check_optional "gh"        "gh"      "gh --version"                     "GitHub CLI"
check_optional "httpie"    "http"    "http --version"                   "sudo apt install httpie"
check_optional "direnv"    "direnv"  "direnv --version"                 "sudo apt install direnv"
check_optional "jq"        "jq"      "jq --version"                     "sudo apt install jq"

# --- Docker-specific health ---
echo
echo "Docker daemon"
echo "─────────────"
if docker info >/dev/null 2>&1; then
  ok "docker daemon" "reachable without sudo"
else
  fail "docker daemon" "not reachable — add user to 'docker' group and re-login (or 'newgrp docker')"
fi

# --- Check the project's services are runnable ---
if [ -f docker-compose.yml ]; then
  echo
  echo "Project services"
  echo "────────────────"
  if docker compose ps --status running 2>/dev/null | grep -q bb_postgres; then
    ok "bb_postgres" "running"
  else
    warn "bb_postgres" "not running — start with 'docker compose up -d'"
  fi
  if docker compose ps --status running 2>/dev/null | grep -q bb_redis; then
    ok "bb_redis" "running"
  else
    warn "bb_redis" "not running — start with 'docker compose up -d'"
  fi
fi

# --- Summary ---
echo
if [ "$missing" -eq 0 ]; then
  printf "${GREEN}All required tools installed.${RESET}"
  if [ "$warnings" -gt 0 ]; then
    printf " ${YELLOW}(%d optional missing)${RESET}\n" "$warnings"
  else
    echo
  fi
  exit 0
else
  printf "${RED}%d required tool(s) missing — see SETUP.md.${RESET}\n" "$missing"
  exit 1
fi
