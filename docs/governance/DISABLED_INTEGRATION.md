# Disabled Governance integration

The `dopemux.governed_execution.offline_execution.disabled_entrypoint` module is
an inert package boundary. It does not enroll a service, hook, controller or
fixture. Its package markers contain docstrings only.

## Interface

`status()` always reports `DISABLED`, dispatch `HELD`, scope
`PRIVATE_STAGING_ONLY` and activation `NOT_AUTHORIZED`. The scope string is part
of the interface; it does not establish filesystem isolation or grant authority.
`dispatch(...)` returns a typed HELD/DISABLED result without inspecting supplied
grant objects or invoking callbacks. Environment variables cannot enable it.

For an independently authorized read-only invocation from a qualified package:

```text
python -B -m dopemux.governed_execution.offline_execution.disabled_entrypoint --help
python -B -m dopemux.governed_execution.offline_execution.disabled_entrypoint status
```

Help and status print descriptions only. Activation, dispatch and run commands
are refused with exit 2. These examples confer no execution or installation
permission. Import does not open a journal, start a process or create outputs.

## Packaging and validation

Two explicit setuptools package entries include `dopemux.governed_execution`
and `dopemux.governed_execution.offline_execution`. The integration adds no
dependency, backend, console script, service, startup hook or activation flag.
The disabled entrypoint implementation is unchanged.

Acceptance must distinguish source tests from an actual wheel build and prove
imports from the inspected wheel's isolated staging directory. See
`DISABLED_INTEGRATION_ACCEPTANCE.md`. Existing parent-package and root-conftest
behavior is separate from the new package's inertness claims.

## Effect and release boundaries

A private directory under the same OS user is a coordination boundary, not
OS-level exclusion. Runtime containment, dependency origins and allowed output
locations must be qualified separately. Fixture execution and live activation
require their own exact grants, trust and ingress checks, finite resources,
custody and tested rollback. This module supplies no such route.

Before any shared application, bind exact target HEAD and preimages, source
custodian, non-overlap and reversible effect authority. Stop on mismatch.
Independent acceptance and applicable native/security gates precede release.
A wheel or test receipt does not authorize installation, commit, push, PR,
merge, signing, deployment or activation. Rollback may restore only verified
owned preimages; it must preserve unrelated work and historical evidence.
