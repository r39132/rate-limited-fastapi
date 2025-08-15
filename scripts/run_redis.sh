
#!/usr/bin/env bash
set -euo pipefail
docker run --name rl-redis -p 6379:6379 -d redis:7-alpine
echo "Redis started on localhost:6379"
