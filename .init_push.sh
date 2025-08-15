#!/bin/bash
set -e  # Exit immediately if a command fails

echo "Step 1: Initializing git repository..."
git init

echo "Step 2: Setting git user name..."
git config user.name "Sid Anand"

echo "Step 3: Setting git user email..."
git config user.email "sanand@apache.org"

echo "Step 4: Adding all files..."
git add .

echo "Step 5: Creating initial commit..."
git commit -m "Initial commit: Redis token bucket + FastAPI + Locust + Streamlit"

echo "Step 6: Setting branch to main..."
git br

