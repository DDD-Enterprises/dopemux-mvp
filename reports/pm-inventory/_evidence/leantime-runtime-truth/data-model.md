---
id: leantime_runtime_truth_data_model
title: Leantime Runtime Truth Data Model
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Adapter-visible Leantime entity and operation shapes evidenced in the current repository.
---
# Leantime - Data Model

## What is directly evidenced

- project and ticket operations over JSON-RPC
- bridge translation to ticket-oriented tools
- PM-route response normalization into `task_id`, `tasks`, and `project_id` style outputs

## Operation-visible entities

- project
- task / ticket
- sprint update
- assignment / resource allocation

## Important boundary

This repository does not expose Leantime's internal durable schema directly. The packet therefore treats the adapter-visible surface as authoritative evidence and does not invent underlying DB tables or storage rules.
