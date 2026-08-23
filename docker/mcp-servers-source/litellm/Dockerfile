# LiteLLM Proxy Server for Dopemux
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and upgrade OS packages to pick up security patches
# (openssl security patch level: 3.5.6-1~deb13u2 via apt upgrade)
#
# Accepted base-image risk: perl CVE-2026-12087 (critical), CVE-2026-48959,
# CVE-2026-48962 (high) are marked "Not Fixed" by Debian for trixie. perl-base
# is an Essential package in Debian and cannot be removed from slim images.
# CVE-2026-12087 is an OOB heap read in Perl's Socket.xs — exploitable only by
# running perl code on attacker-controlled input; this container runs no perl
# at runtime (python entrypoint only). Revisit when Debian ships a fix.
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    curl \
    netcat-traditional \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*

# Install LiteLLM with all optional dependencies.
# Pin minimum versions to address Docker Scout CVEs:
#   litellm>=1.83.7          (CVE-2026-35030, critical + 3 high)
#   starlette>=0.49.1        (high CVE)
#   python-multipart>=0.0.27 (2 high CVEs)
#   wheel>=0.46.2            (CVE-2026-24049, high — standalone copy)
#   setuptools>=80.10.2      (first release whose VENDORED wheel is >=0.46.2;
#                             the scanner flags setuptools._vendor.wheel 0.45.1,
#                             so bumping standalone wheel alone does not clear it)
#   mcp>=1.23.0              (high CVE)
# prisma is pinned to 0.11.0 to match litellm[proxy]'s own
# `prisma==0.11.0` requirement (extra-proxy) — an unpinned install grabs
# latest prisma-client-python, whose generated `prisma/types.py` no longer
# exports `DatasourceOverride`, breaking `prisma.client`'s own import and
# crash-looping the container on every start.
# fastapi is pinned to 0.140.0 because litellm's proxy server imports the
# private `fastapi.dependencies.utils.get_flat_dependant` helper directly;
# fastapi removed it in 0.141.0 (confirmed absent in 0.141.0 and 0.141.1),
# which crash-loops the container the same way once prisma resolves.
# 0.140.0 is the newest version confirmed to still export it.
# litellm[proxy]'s own range (fastapi<1.0,>=0.136.3) is wide enough to let
# pip resolve this exact version instead of drifting past the removal.
RUN pip install --no-cache-dir \
    "litellm[proxy]>=1.83.7" \
    "fastapi==0.140.0" \
    "starlette>=0.49.1" \
    "python-multipart>=0.0.27" \
    "wheel>=0.46.2" \
    "setuptools>=80.10.2" \
    "mcp>=1.23.0" \
    "prisma==0.11.0" \
    pyyaml

# cryptography>=48.0.1 fixes GHSA-537c-gmf6-5ccf (OOB read in statically-linked
# OpenSSL, high 7.5). litellm[proxy] pins cryptography<47.0, so this cannot be
# resolved in the same pip invocation — force-upgrade afterwards. litellm's
# cryptography usage (Fernet key encryption, JWT signing primitives) is stable
# across these versions; runtime start is verified in CI/manually after build.
RUN pip install --no-cache-dir --upgrade "cryptography>=48.0.1"

# Copy configuration and entrypoint from root build context
COPY docker/mcp-servers-source/litellm/litellm.config.yaml /app/config.yaml
COPY docker/mcp-servers-source/litellm/entrypoint.sh /app/entrypoint.sh

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 4000

# NOTE: Healthcheck defined in docker-compose.yml to use correct auth token

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
