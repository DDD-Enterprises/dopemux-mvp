# Route Denylist Test Output

Mutating/proxy routes are unreachable: no denied route literal or mutating HTTP verb call appears in any adapter call-path module; allowed/denied route sets are disjoint.

```
$ python -m pytest -q services/dcp-readonly-facade/tests/test_route_denylist.py \
    services/dcp-readonly-facade/tests/test_packet_0008.py \
    -k "denylist or denied or mutating or no_filesystem or no_shell or gitstate or route or disjoint"
..........                                                               [100%]
```

Tests:
- test_allowed_and_denied_are_disjoint
- test_post_read_paths_are_the_only_post_allowlist
- test_adapter_source_has_no_denied_tokens
- test_adapter_source_has_no_mutating_http_verbs
- test_no_mutating_http_verbs_in_facade_source (packet 0008)
- test_no_mutating_route_strings_in_executable_paths (packet 0008)
- test_denied_and_allowed_routes_stay_disjoint (packet 0008)
