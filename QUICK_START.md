# Dopemux Quick Start

Use this when you need the shortest repo-grounded local startup path.

## Install

```bash
git clone https://github.com/DDD-Enterprises/dopemux-mvp
cd dopemux-mvp
uv sync --frozen --extra dev
```

## Start Services

`compose.yml` uses an external Docker network named `dopemux-network`.

```bash
docker network inspect dopemux-network >/dev/null 2>&1 \
  || docker network create dopemux-network
docker compose -f compose.yml up -d --build
```

## Start The Operator CLI

```bash
dopemux start
```

`dopemux start` is the cockpit/operator entrypoint. Use explicit compose
startup when you need the compose-backed service stack.

## Smoke Checks

```bash
curl -fsS http://localhost:3016/health  # dopecon-bridge
curl -fsS http://localhost:3004/health  # ConPort HTTP
curl -fsS http://localhost:3010/health  # dope-context
curl -fsS http://localhost:3020/health  # dope-memory
curl -fsS http://localhost:8000/health  # task-orchestrator
curl -fsS http://localhost:3025/health  # ADHD Engine
```

These are the observed defaults in `compose.yml` and `services/registry.yaml`.
Follow `.env` overrides when present.

## Rules Of Thumb

- Dopemux is split-authority, not a monolithic assistant.
- dopecon-bridge routes and proxies; it is not PM or memory authority.
- dope-context retrieval is derived context, not source truth.
- dope-memory is chronicle/receipt authority, not all memory or current PM
  state.
- Runtime drift remains `NEEDS_REPO_VERIFICATION` unless a live check proves it.

Next: [docs/01-tutorials/quickstart.md](docs/01-tutorials/quickstart.md) and
[docs/02-how-to/developer-onboarding.md](docs/02-how-to/developer-onboarding.md).
