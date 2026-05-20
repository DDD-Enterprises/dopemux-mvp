---
id: mobile-blink-ssh-constraints
title: Mobile Blink SSH Constraints
type: reference
owner: '@hu3mann'
author: codex
date: '2026-05-19'
prelude: Normalized research summary for mobile Blink, SSH, Mosh, tmux, and narrow
  viewport constraints.
last_review: '2026-05-19'
next_review: '2026-08-17'
---
# Mobile Blink SSH Constraints

Source: `/Users/hue/Downloads/deep-research-report 15.md`

SHA256:
`15ebfbe00f8a6a968a64d2c8de5a53af9e4289b7bab2250ad25e82dc66a30432`

Classification: research input. This document is not repo truth.

## OBSERVED

- Mobile terminal state must live on the remote host, not in the phone client.
  tmux detach/attach semantics and Mosh roaming support make the client a
  replaceable viewport.
- Blink Shell supports SSH and Mosh workflows, hardware keyboard shortcuts,
  modifier remapping, Smart Keys, gestures, and terminal resizing.
- iOS can suspend long-running network activity. Blink-specific mitigations may
  help, but the product should not assume a stable raw SSH connection.
- Mosh is useful for roaming and intermittent connectivity, but UDP, tunnels,
  bastions, scrollback limitations, and terminal feature differences make it an
  optional transport rather than a required foundation.
- tmux menus, popups, mouse behavior, clipboard behavior, and terminal feature
  negotiation depend on terminal capabilities. They must be probed or treated
  as optional.

## INFERRED

- iPhone portrait should be treated as a single-focus control surface for
  status, queue review, logs, approval, and rapid triage.
- iPad landscape and external keyboards can support limited editor/operator
  work, but should still inherit the narrow-mode safety model.
- Window-centric navigation is safer than dense pane-centric navigation on
  mobile.
- High-frequency status churn and animation are poor fits for mobile SSH.
  Coarse refresh intervals and stable render snapshots are preferable.
- Mouse and touch can be conveniences, but keyboard navigation must remain the
  primary contract.

## CONFLICTING

- The current repo mobile tmux config at `config/mobile/tmux.mobile.conf`
  enables mouse support, OSC 52 clipboard support, prefixless function-key
  jumps, and bottom status. The research recommends treating mouse, clipboard,
  and function-key access as optional on mobile and using a more conservative
  primary key model.
- Existing Cockpit runtime and design-system docs block below `80x24`.
  The research recommends a usable single-column fallback below 70 columns.
  This packet documents that as a future prototype contract only; it does not
  change runtime behavior.

## UNKNOWN

- Exact usable column counts by device, orientation, font, keyboard, and Blink
  profile are not established by repo evidence.
- Blink touch-to-terminal-mouse behavior is not proven as a stable product
  dependency.
- OSC 52 clipboard behavior across Blink, SSH, Mosh, tmux, and remote apps is
  not proven enough to carry proof or receipt transport.
- Exact terminal feature support for extended keys, true color, glyphs, and
  focus events is not proven across all mobile clients.

## Mobile Rules To Carry Forward

- tmux is the reconnect/resume chassis, not business logic.
- Use a dedicated mobile tmux session or socket for mobile operation.
- Do not let mobile clients resize or damage desktop work sessions by default.
- Treat under-70-column layouts as single-column and drill-down only.
- At `80x24`, use one primary region plus minimal chrome.
- At `100x30` or `100x32`, allow one dominant region and one secondary region.
- At `120x40+`, allow restrained multi-pane desktop-style layouts.
- Full-screen overlays are safer than narrow popups for Command Palette, help,
  and Safe Action Gate.
- Proof must be file-backed and path-addressable; clipboard success is not
  proof.
