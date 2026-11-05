# MACRO-DMX-RUNNER-MEMORY-2A-001-R2 — Keychain ACL result (W03 precondition, B01)

**Procedure:** `proof/MACRO-DMX-RUNNER-MEMORY-2A-001/review_bundle/W00_FINDINGS.md` section 6, run in part on 2026-10-31 (local) / 2026-11-01 (UTC).
**Recorded by:** the team lead (Control Tower supervisor session), from the operator's terminal output and one read the operator approved ("yyeess").
**Item:** throwaway generic password, service `dopemux-mcp-probe`, account `probe`. It is not a real token.

## Step 1: create

The operator ran `security add-generic-password -s dopemux-mcp-probe -a probe -U -w` in the Claude desktop app's terminal pane. It prompted for the value and asked to retype it, and printed no error.

This is the **default ACL**: no `-T` and no `-A`, so the creating `/usr/bin/security` binary is the trusted application.

## Step 2: non-interactive read

Command (from W00 section 6, verbatim):

```text
env -i PATH=/usr/bin:/bin /usr/bin/python3 -I -c "import subprocess; r=subprocess.run(['/usr/bin/security','find-generic-password','-s','dopemux-mcp-probe','-a','probe','-w'],stdin=subprocess.DEVNULL,capture_output=True,timeout=10); print(r.returncode,len(r.stdout.strip()))"
```

| Context | ACL | Output | Dialog | Who ran it |
|---|---|---|---|---|
| Claude desktop terminal pane (GUI session, login keychain unlocked) | default | `0 24` | not reported | operator |
| Codex shell tool (run twice) | default | `0 24`, `0 24` | not reported | operator |
| Claude Code Bash tool (this session) | default | `0 24` | none possible: stdin closed, no one to click, returned at once | team lead, 2026-11-01T06:05:15Z, with the operator's approval |
| No GUI session (`ssh localhost` or a `launchd` agent) | — | NOT_RUN | — | — |
| Locked login keychain | — | NOT_RUN | — | — |
| ACL variants `-T ""`, `-T /usr/bin/python3`, `-A` | — | NOT_RUN | — | — |

**Length 24, not 12.** The operator's input doubles every character, as in their chat messages, so the stored value is the 24-character doubled string. The test checks only the exit code and whether a dialog blocks the read, so this does not affect the result.

## Decision for W03 (B01)

- **Item ACL: the default.** The helper creates items with `/usr/bin/security add-generic-password` and no `-T` or `-A`. It reads them with `/usr/bin/security find-generic-password … -w` from a child process.
  - All three tested runner contexts read without being blocked while the login keychain was unlocked.
  - `-A` is rejected: it is the widest exposure.
  - `-T <python>` is rejected: it re-prompts whenever the interpreter path changes.
- **Untested contexts fail closed.** The locked keychain and the no-GUI session were not run. The helper treats any nonzero exit, timeout or empty output as a hard failure. The message names the likely cause (keychain locked or no login session) and the fix. It never retries into a prompt.
  - Reads close stdin and use a timeout.
- **The token never goes on a command line.**
  - `security add-generic-password -w <token>` would show the token in `ps`.
  - To write, the helper feeds the command to `security -i` on stdin (W00 section 6), or uses an equivalent that keeps the token out of argv.
  - Tests stub `security` and assert the token is never in argv, stdout, logs or files.
- **Same-user exposure is unchanged.** Any process of the same macOS user can run the same read. That is the design's stated non-protection (2A design section 6) and stays so.

## Still to do (operator)

Delete the probe item:

```text
security delete-generic-password -s dopemux-mcp-probe -a probe
```

The locked-keychain and no-GUI runs remain optional. They would only change the failure message, not the ACL choice.
