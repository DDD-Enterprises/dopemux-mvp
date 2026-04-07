# Batch accounting contract

`Batch cost accounting is conservative reservation accounting and not authoritative provider billing truth.`

## Current runtime contract

- submit-time batch work reserves estimated spend through `_reserve_projected_spend(...)`
- watch/finalize paths record observed usage when available
- already-reserved submit work is not accumulated again at watch/finalize
- the ledger is conservative for runtime cap enforcement, not a provider invoice source

## Why this remains in scope

TP-001A clarifies the contract. It does not redesign batch accounting into result-materialization billing truth.
