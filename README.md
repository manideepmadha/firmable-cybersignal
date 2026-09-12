# CyberSignal — Firmable AI Sales Intelligence

This repository implements a Snowflake-first AI sales intelligence solution for identifying and prioritizing cybersecurity prospects from internet-facing infrastructure telemetry.

## Task outcome
The project turns raw external exposure data into an explainable prospecting queue that helps sales teams:

- rank accounts by likely cybersecurity need
- inspect the evidence behind each recommendation
- generate concise AI-backed account briefs
- compare prompt versions and evaluate output quality

## Core architecture

The solution is built around a clear rule-versus-AI split:

- Snowflake handles ingestion, normalization, feature aggregation, scoring, and evidence storage
- Streamlit provides the user-facing experience
- AI is used only to explain the evidence and draft sales-ready account briefs

## Main repository areas

- `app/` — Streamlit applications for the user experience
- `sql/` — Snowflake setup, load, feature, scoring, evidence, observability, and evaluation SQL
- `evals/` — labelled evaluation set, predictions, and metrics scripts
- `prompts/` — prompt versions for account brief generation
- `skills/` — reusable account-intelligence guidance
- `docs/` — architecture, planning, implementation summary, and generated client materials
- `scripts/` — supporting automation and document generation

## What was delivered

- deterministic account scoring from structured infrastructure signals
- evidence-backed account prioritization
- AI-generated brief generation grounded in Snowflake data
- prompt versioning and comparison workflow
- evaluation pipeline with labelled examples and metrics
- observability design for model-call tracking
- client-facing documentation and implementation summary

## Submission-ready artifacts

This repo includes the materials needed for a client-facing submission:

- `docs/architecture.md`
- `docs/planning.md`
- `docs/implementation-summary.md`
- `docs/CyberSignal_Implementation_Document.docx`
- `evals/labelled_accounts.jsonl`
- `evals/results/final_results_summary.md`

## Notes

- The system is intentionally designed so that the core ranking remains deterministic and explainable.
- The AI layer is constrained to narrative explanation and sales enablement, not raw scoring logic.
- Sensitive values such as secrets, API keys, and local-only files should not be committed to Git.
