## Summary

Describe the problem and what this PR changes.

## Type of Change

- [ ] Bug fix
- [ ] Feature
- [ ] Refactor
- [ ] Documentation
- [ ] CI/CD
- [ ] Security hardening

## Validation

- [ ] `python scripts/check_root_hygiene.py --all-files`
- [ ] `pytest tests/unit --maxfail=1 --disable-warnings --no-cov`
- [ ] `./test_installer_basic.sh` (when install/runtime paths changed)
- [ ] Added/updated tests for behavior changes

## Risk and Rollback

- [ ] Risk level documented (low/medium/high)
- [ ] Rollback plan provided for risky changes

## Security and Docs

- [ ] No secrets/credentials added
- [ ] Security implications reviewed
- [ ] Docs updated (README/INSTALL/QUICK_START/docs) as needed
