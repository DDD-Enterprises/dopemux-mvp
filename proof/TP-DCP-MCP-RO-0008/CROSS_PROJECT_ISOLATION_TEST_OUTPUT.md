# Cross-Project Isolation Test Output

Verifies one project's reads can never reach another project's workspace or proof bundles.

```
$ python -m pytest -q services/dcp-readonly-facade/tests/test_packet_0008.py \
    -k "isolation or symlink or leaks or resolve_binds or other_projects"
......                                                                   [100%]
```

Tests:
- test_list_proof_bundles_never_leaks_other_project
- test_fetch_other_projects_bundle_id_is_blocked
- test_symlink_from_one_project_into_another_is_blocked
- test_resolve_binds_only_the_requested_project
- test_isolation_holds_both_directions
