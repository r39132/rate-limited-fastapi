#!/usr/bin/env bash
# loadenv.sh — load a .env file into the current shell (when sourced) with verbose output.
# Features:
#   - Ignores blank lines and comments
#   - Strips inline comments after values
#   - Prints what it is doing (verbose by default)
#   - Mask prints likely secrets
#   - Flags: -q/--quiet, -n/--dry-run, -v/--verbose (default)

# ----- helpers -----
_loadenv_resolve_path() {
  # Resolve to absolute path without requiring realpath/greadlink
  local target="$1"
  local dir base
  dir="$(cd "$(dirname "$target")" && pwd)"
  base="$(basename "$target")"
  printf "%s/%s" "$dir" "$base"
}

_loadenv_is_secret_key() {
  # Heuristic: mask values for keys that look like secrets
  [[ "$1" =~ (PASS|SECRET|TOKEN|KEY|PWD|CRED|AUTH|BEARER|API)_?([A-Z0-9_]*)$ ]]
}

_loadenv_log() {
  # $1 = level, $2... = msg (prints unless quiet)
  local level="$1"; shift
  [[ "${_LOADENV_QUIET:-0}" -eq 1 ]] && return 0
  printf "%s %s\n" "$level" "$*"
}

# ----- main function -----
loadenv() {
  local env_file=".env"
  local _LOADENV_VERBOSE=1
  local _LOADENV_DRYRUN=0
  _LOADENV_QUIET=0

  # Parse flags
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -q|--quiet)   _LOADENV_QUIET=1; _LOADENV_VERBOSE=0; shift ;;
      -n|--dry-run) _LOADENV_DRYRUN=1; shift ;;
      -v|--verbose) _LOADENV_VERBOSE=1; _LOADENV_QUIET=0; shift ;;
      -h|--help)
        cat <<'EOF'
Usage: loadenv [options] [PATH_TO_ENV]
Load key/values from a .env file into the current shell.

Options:
  -n, --dry-run   Show what would be exported without changing env
  -q, --quiet     Suppress output
  -v, --verbose   Verbose output (default)
  -h, --help      Show this help

Notes:
- To modify your current shell, run `loadenv` from a shell that has sourced this script.
- Executing this file directly cannot modify the parent shell's environment.
EOF
        return 0
        ;;
      *) env_file="$1"; shift ;;
    esac
  done

  # Resolve and validate path
  local abs_path
  abs_path="$(_loadenv_resolve_path "${env_file}")"
  if [[ ! -f "$abs_path" ]]; then
    _loadenv_log "❌" "File not found: $abs_path"
    return 1
  fi

  [[ $_LOADENV_VERBOSE -eq 1 ]] && _loadenv_log "🔎" "Using file: $abs_path"
  [[ $_LOADENV_VERBOSE -eq 1 ]] && _loadenv_log "📄" "Reading and parsing lines..."

  local line key value lineno=0 exported=0 skipped=0
  while IFS= read -r line || [[ -n "$line" ]]; do
    ((lineno++))
    # Trim leading/trailing whitespace
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"

    # Skip blanks and full-line comments
    if [[ -z "$line" || "$line" == \#* ]]; then
      ((skipped++))
      continue
    fi

    # Must contain '='
    if [[ "$line" != *"="* ]]; then
      [[ $_LOADENV_VERBOSE -eq 1 ]] && _loadenv_log "⚠️" "Line $lineno: no '=' found, skipping"
      ((skipped++))
      continue
    fi

    key="${line%%=*}"
    value="${line#*=}"

    # Trim key whitespace
    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"

    # Strip inline comment from value (anything after #)
    value="${value%%#*}"

    # Trim value whitespace
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"

    if [[ -z "$key" ]]; then
      [[ $_LOADENV_VERBOSE -eq 1 ]] && _loadenv_log "⚠️" "Line $lineno: empty key, skipping"
      ((skipped++))
      continue
    fi

    # Show planned export
    if _loadenv_is_secret_key "$key"; then
      _loadenv_log "➡️" "Export $key=********"
    else
      _loadenv_log "➡️" "Export $key=$value"
    fi

    # Apply export unless dry-run
    if [[ $_LOADENV_DRYRUN -eq 0 ]]; then
      # shellcheck disable=SC2163
      export "$key=$value"
    fi
    ((exported++))
  done < "$abs_path"

  [[ $_LOADENV_VERBOSE -eq 1 ]] && _loadenv_log "✅" "Done. Exported: $exported  Skipped: $skipped"
  return 0
}

# Optional: pretty-print what the file contains (post-cleaning), without exporting
loadenv_dryrun() {
  echo "This is a dry-run -- OS env will not be updated with these values unless you call loadenv() or le (alias)"
  loadenv --dry-run "$@"
}

# If executed directly (not sourced), run in dry-run mode and remind user.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  loadenv --dry-run "$@"
  echo "ℹ️  Tip: To actually export into your current shell, source this file in your ~/.bashrc and run: loadenv"
fi

