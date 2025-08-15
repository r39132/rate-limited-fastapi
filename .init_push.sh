#!/usr/bin/env bash
set -euo pipefail

# ==== CONFIGURE THESE (edit as needed) ====
REPO_NAME="rate-limited-fastapi"
VISIBILITY="private"   # one of: private | public | internal (org repos only)
DEFAULT_BRANCH="main"
COMMIT_MSG="Initial commit: Redis token bucket + FastAPI + Locust + Streamlit"
GIT_NAME="Sid Anand"
GIT_EMAIL="sanand@apache.org"
# ==========================================

echo "Step 0: Checking for GitHub CLI (gh)..."
command -v gh >/dev/null 2>&1 || { echo "Error: gh is not installed (https://cli.github.com)."; exit 1; }

echo "Step 0.1: Ensuring you're authenticated to GitHub..."
if ! gh auth status >/dev/null 2>&1; then
  echo "Not logged in. Launching 'gh auth login'..."
  gh auth login
fi

echo "Step 0.2: Determining your GitHub username/owner..."
OWNER="$(gh api user -q .login)"
echo "  -> OWNER detected as: ${OWNER}"

echo "Step 1: Initializing git repo (if needed)..."
if [ ! -d .git ]; then
  git init
else
  echo "  -> .git already exists. Skipping init."
fi

echo "Step 2: Setting git identity..."
git config user.name  "$GIT_NAME"
git config user.email "$GIT_EMAIL"

echo "Step 3: Ensuring default branch is '${DEFAULT_BRANCH}'..."
if git rev-parse --verify "$DEFAULT_BRANCH" >/dev/null 2>&1; then
  git checkout "$DEFAULT_BRANCH"
else
  if git rev-parse --verify HEAD >/dev/null 2>&1; then
    git checkout -b "$DEFAULT_BRANCH"
  else
    git checkout --orphan "$DEFAULT_BRANCH"
  fi
fi

echo "Step 4: Staging files..."
git add -A

echo "Step 5: Committing (only if there are staged changes)..."
if git diff --cached --quiet; then
  echo "  -> No staged changes. Skipping commit."
else
  git commit -m "$COMMIT_MSG"
fi

echo "Step 6: Ensuring remote 'origin' exists and points to GitHub..."
REPO_HTTP_URL="https://github.com/${OWNER}/${REPO_NAME}.git"
if git remote get-url origin >/dev/null 2>&1; then
  CURRENT_URL="$(git remote get-url origin)"
  if [ "$CURRENT_URL" != "$REPO_HTTP_URL" ]; then
    echo "  -> Updating 'origin' from '$CURRENT_URL' to '$REPO_HTTP_URL'..."
    git remote set-url origin "$REPO_HTTP_URL"
  else
    echo "  -> 'origin' already set to $REPO_HTTP_URL"
  fi
else
  echo "  -> No 'origin' remote. Will create repo on GitHub and set it."
  # Try to create the repo on GitHub under your account
  gh repo create "${OWNER}/${REPO_NAME}" --source "." --remote "origin" --${VISIBILITY} -y >/dev/null
  echo "  -> Created https://github.com/${OWNER}/${REPO_NAME}"
fi

echo "Step 7: Pushing '${DEFAULT_BRANCH}' to GitHub and setting upstream..."
git push -u origin "$DEFAULT_BRANCH"

# Optional: set the repo's default branch on GitHub to match (idempotent)
echo "Step 8: Setting default branch on GitHub to '${DEFAULT_BRANCH}' (idempotent)..."
gh repo edit "${OWNER}/${REPO_NAME}" --default-branch "$DEFAULT_BRANCH" >/dev/null || true

# Optional: show the repo URL and open in browser
URL="https://github.com/${OWNER}/${REPO_NAME}"
echo "✅ Done. Repository is at: $URL"
# Uncomment to open in your browser:
# gh repo view "${OWNER}/${REPO_NAME}" --web

