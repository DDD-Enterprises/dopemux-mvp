#!/bin/bash
#
# Test installer control flow in an Ubuntu 24.04 container.
#
# Ubuntu 24.04 ships Python 3.12, which satisfies the installer's 3.11–3.13
# requirement from the default archives (22.04 ships 3.10 and would need the
# deadsnakes PPA — that path is intentionally NOT exercised here).
#
# Runs with INSTALLER_TEST_MODE=1: exercises platform detection, dependency
# checks, arg parsing, and env-file handling. Docker-in-Docker paths (compose
# pull/up, networks) are skipped by design.
#
# Usage: ./test_installer_ubuntu.sh
#

set -euo pipefail

echo "🐳 Starting Ubuntu 24.04 test container..."

# No -t: keeps this usable in CI where no TTY is allocated.
docker run -i --rm \
  --name dopemux-test-ubuntu \
  -v "$(pwd)":/workspace:ro \
  -w /workspace \
  -e INSTALLER_TEST_MODE=1 \
  ubuntu:24.04 \
  /bin/bash -s <<'INNER'
set -euo pipefail

echo "📦 Updating apt..."
apt-get update -qq

echo "🔧 Installing base dependencies..."
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  curl ca-certificates python3 python3-venv python3-pip git >/dev/null

echo "🐍 Python: $(python3 --version)"

echo "🚀 Running installer (--quick --yes, test mode)..."
# --env-file outside the (read-only) workspace mount so the host repo is never
# polluted with a generated .env.
HOME=/root ./install.sh --quick --yes --env-file /tmp/test.env
echo "✅ Quick install (test mode) exited 0"

echo ""
echo "🔎 Assertions:"
test -d /root/.dopemux || { echo "❌ ~/.dopemux not created"; exit 1; }
echo "✅ ~/.dopemux directory created"

test -f /tmp/test.env || { echo "❌ env file not written"; exit 1; }
grep -q '^AGE_PASSWORD=' /tmp/test.env || { echo "❌ AGE_PASSWORD missing from env file"; exit 1; }
[ "$(stat -c %a /tmp/test.env)" = "600" ] || { echo "❌ env file permissions not 600"; exit 1; }
echo "✅ env file written with core secrets and mode 600"

echo ""
echo "🔎 Verify mode (test mode)..."
HOME=/root ./install.sh --verify --env-file /tmp/test.env
echo "✅ --verify exited 0"
INNER

echo ""
echo "✅ Ubuntu 24.04 test complete!"
