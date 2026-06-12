# DCP Routing Classifier Golden Corpus (Seed)

This directory contains labeled test fixtures for the DCP routing classifier, lane engine, and router.

## Fixture Schema (v0.1)

Each JSON fixture must contain:
- id
- description
- expected_classification (safe_read | docs_only | domain_model | implementation_allowed | red_lane | forbidden | unknown)
- expected_stop (true | false)
- risk_class (low | medium | high)
- authority_class (read | design | implement | judge | audit | forbidden)
- notes

## Current Seed (0000I)

This is the initial seed corpus. Full 80+ corpus is expected in later packets.

