# Changed Scope

- Base SHA: `c7bc2fb479d7386825df73e028acdce723ee3388`
- Content SHA: `e3939772d7e1ca69fc84a53b2a5dc949c5eca938`
- Content tree: `1fdef10ee7e59c30f8ecf3c495b50f5133cab02d`
- Changed paths: 232
- Outside packet allowlist: none
- Forbidden paths touched: none

Major scoped surfaces:

- `compose.yml`
- `templates/routing.yaml`
- `config/ai/model-routing.policy.yaml`
- `src/dopemux/routing_config.py`
- `src/dopemux/routing_cli.py`
- `src/dopemux/model_catalog.py`
- `scripts/generate_pal_model_manifest.py`
- `scripts/mcp-wrappers/ensure-pal.sh`
- `docker/mcp-servers-source/pal/**`
- Focused routing/catalog/PAL tests
- Model-routing usage and governance docs

Full authoritative list is reproducible with:

```bash
git diff --name-only c7bc2fb479d7386825df73e028acdce723ee3388..e3939772d7e1ca69fc84a53b2a5dc949c5eca938
```
