# DR-02: Local Broker and Self-Hosted Runner Security

## Objective

Compare secure architectures for running plan-authenticated code audits locally while
preserving exact PR/head provenance and preventing untrusted pull-request content from reaching
persistent credentials or executing on the credential-bearing host.

## Required architecture candidates

1. Operator-triggered local audit broker.
2. Persistent dedicated self-hosted GitHub runner.
3. Ephemeral self-hosted runner.
4. Broker plus isolated per-tool worker accounts.
5. Broker plus disposable VM/container workers.
6. GitHub-hosted workflow that emits a signed request for local pickup.
7. Manual local audit with artifact upload.

## Research questions

- What are GitHub's current security warnings for self-hosted runners?
- How do runner groups, labels, repository restrictions, workflow approvals, and environment
  protections constrain access?
- What are the risks of `pull_request_target`, workflow injection, reusable workflows,
  artifact poisoning, cache poisoning, and secret exposure?
- Can trusted-main workflows safely fetch a PR diff as inert data without checking out or
  executing candidate code?
- What official mechanisms exist for ephemeral or autoscaled self-hosted runners?
- How should a local broker verify repository, PR number, base SHA, head SHA, workflow identity,
  request freshness, and replay resistance?
- What signing or attestation mechanisms are practical using GitHub OIDC, artifact attestations,
  signed manifests, or GitHub API verification?
- How should per-tool credentials be isolated across OS users, home directories, VMs,
  containers, and keychains?
- Can macOS account/keychain isolation support this safely?
- Which network controls are feasible per tool?
- What output channels safely return results to GitHub without giving the model GitHub write
  credentials?
- Which design best supports one audit at a time, cleanup, revocation, logging, and operator
  visibility?

## Required deliverables

- Threat model.
- Comparative architecture matrix.
- Recommended first-release architecture.
- Recommended later automated architecture.
- Trust-boundary diagram in text.
- Signed request and result envelope requirements.
- Credential isolation requirements.
- Failure and recovery model.
- Security controls mapped to enforcement source:
  - prompt;
  - CLI;
  - wrapper;
  - OS;
  - VM/container;
  - GitHub;
  - operator.

## Mandatory principle

Candidate code must be treated as hostile data. Research must challenge any design that places
persistent plan credentials in a generic runner capable of executing PR-controlled workflows.
