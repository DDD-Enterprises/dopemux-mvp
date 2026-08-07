# Rollback Instructions: TP-DMX-LITELLM-PIN-FINALIZE-001

## Single Product Path Target
- Target file: `docker/mcp-servers-source/litellm/Dockerfile`

## Reversion Steps
In the event that `prisma==0.11.0` or `fastapi==0.140.0` cause an unforeseen failure:

1. Revert commit or branch changes to `docker/mcp-servers-source/litellm/Dockerfile`:
   ```bash
   git checkout origin/main -- docker/mcp-servers-source/litellm/Dockerfile
   ```
2. Re-build container image:
   ```bash
   docker build -f docker/mcp-servers-source/litellm/Dockerfile -t dmx-litellm:latest .
   ```
3. Zero state/db changes were performed on production or shared databases during this packet.
