
<!-------->
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Uvicorn](https://img.shields.io/badge/Server-Uvicorn-000000?logo=uvicorn&logoColor=white)](https://www.uvicorn.org/)
[![Redis](https://img.shields.io/badge/Rate%20Limit-Redis%20%2B%20Lua-D82C20?logo=redis&logoColor=white)](https://redis.io/)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Locust](https://img.shields.io/badge/Load-Testing%20with%20Locust-77B829)](https://locust.io/)
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://black.readthedocs.io/)
![flake8](https://img.shields.io/badge/lint-flake8-5A9FD4)
![mypy](https://img.shields.io/badge/types-mypy-2A6DB2)
![pytest](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://pre-commit.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

# rate-limited-fastapi

A Python 3.12.3 project demonstrating a **FastAPI** app protected by a **Redis-backed token
bucket** (Lua script), a **Locust** load generator, a **Streamlit** dashboard with
time-series charts, and a **`hammer.sh`** script for shell-based load testing.  
Includes strong Python best practices: `black`, `isort`, `ruff`, `mypy`,
`pytest` + coverage, and both `pre-commit` & `pre-push` hooks.

---
## Screenshots
### Locust (Load Generator) Dashboard
![Locust (Load Generator) Dashboard](docs/Locust.png)

### Performance Dashboard
![Performance Dashboard](docs/Token_Bucket_Perf_Dashboard.png)

---

## Quick start

### 0) Install [uv](https://docs.astral.sh/uv/)
```bash
# Install via Curl
curl -Ls https://astral.sh/uv/install.sh | sh
# or via Pipx (Recommended)
pipx install uv
```
### 1) Install [precommit/prepush hooks](https://pre-commit.com/#3-install-the-git-hook-scripts)
```bash
pre-commit install --hook-type pre-commit
pre-commit install --hook-type pre-push
```
 

### 2) Create and sync a virtual environment
```bash
uv venv --python 3.12.3
uv sync
```

This will create `.venv` and install all runtime + dev dependencies from `pyproject.toml` / `uv.lock`.

### 3) Start Redis (Docker)
```bash
./scripts/run_redis.sh
```

### 4) Preload the Lua script (optional)
```bash
uv run python scripts/setup_redis.py
```

### 5) Run the API server
```bash
uv run uvicorn app.main:app --reload
```

### 6) Run the dashboard
```bash
uv run streamlit run dashboard/app.py
```

### 7) Run load tests
- **Option 1: Locust (browser UI)**
  ```bash
  uv run locust -f load/locustfile.py --host=http://localhost:8000
  ```
  Open <http://localhost:8089>.

- **Option 2: Hammer script (shell alternative)**
  ```bash
  ./hammer.sh
  ```

---

## What’s inside

- **FastAPI** app at `app/main.py` enforcing rate limits with **Redis Lua** (token bucket).
- **Hardened Lua** at `rate_limiter.lua`: uses Redis `TIME`, clamps elapsed, caps tokens, TTL.
- **Metrics**: `/metrics` endpoint exposes allowed vs throttled counts and current tokens.
- **Streamlit dashboard** at `dashboard/app.py` (time-series of pass vs throttle and token count).
- **Locust** load at `load/locustfile.py` to stress test the limiter.
- **Hammer script** at `hammer.sh` for quick shell-based load testing.
- **Tests** in `tests/` covering token refill/allow/deny behavior.
- **Best-practice tooling**: `black`, `flake8`, `isort`, `mypy`, `pytest`, `pytest-cov`, `pre-commit`.

---

## Configuration

Edit `.env` (or env vars) to tune limits:

```bash
REDIS_URL=redis://localhost:6379/0
TB_CAPACITY=20          # max tokens (burst)
TB_RATE=20              # tokens per second
BUCKET_PREFIX=tb:user:  # key prefix
```

---

## Token bucket rationale

We use **continuous (lazy) refill**:  
`tokens_added = rate * elapsed_ms / 1000`  
Values are clamped to capacity and applied atomically in Redis.  
This avoids fixed-window boundary spikes and maintains a rolling, fair limit.

---

## Security notes

- Lua script only accepts numeric inputs and clamps elapsed times to avoid clock skew effects.
- Redis `TIME` (server time) is used for consistency.
- Keys expire after *full refill time* of idleness to reclaim memory.

---

## Make it yours

- Change identification policy (per-IP, per-API key, per-user) in `app/main.py`.
- Extend metrics (Prometheus compatible) or feed logs to your observability stack.
- Deploy behind Hitch/HAProxy/Nginx/Envoy if you need TLS/WAF/routing ahead of FastAPI.

---

## Development
- Add new dependencies:
  ```bash
  uv add <package>
  uv add --group dev <dev-package>
  ```

- Update dependencies:
  ```bash
  uv lock --upgrade
  uv sync
  ```

- Run tests:
  ```bash
  uv run pytest
  ```

- Run pre-commit checks before committing and pushing to git
  ```bash
  pre-commit run --all-files
  ```
Refer to the Screenshot below:
![Run Pre-Commit Checks](docs/Run_pre-commit_checks_before_commit_and_push.png)

Note: Most of the checks will autofix code, so if they fail the first time, just run again. Even if you forget to run `pre-commit run --all-files`, they checks will run when you try to commit or push

---

## Deployment

If you need a `requirements.txt` (for Docker or pip-only environments):

```bash
uv pip compile pyproject.toml -o requirements.txt
```

---

## License

MIT
