# How I Built This

I approached this as a product and engineering task, not just as a data exercise. The end goal was to build a working system that could turn internet-facing infrastructure signals into a useful sales intelligence workflow.

## 1. Starting point: understand the business outcome

The first step was to define the real problem clearly:

- sales teams need to know which companies are most likely to be good cybersecurity prospects
- the system should not rely on guesswork
- the result should be explainable, so a salesperson can see why an account was ranked highly

That meant the system needed two layers:

1. a deterministic ranking layer that uses rules and structured signals
2. an AI layer that explains the evidence and drafts a human-friendly account brief

## 2. First draft: use ChatGPT for a boilerplate

Before building the actual repo, I used ChatGPT to create an initial structure and working plan. The goal was to get a first boilerplate version quickly, especially for:

- project layout
- suggested folders and files
- ideas for SQL pipeline stages
- a starting point for the Streamlit app
- a logical flow for the AI feature

This helped me get moving fast and gave me a strong starting point for the real implementation.

## 3. Switching to Copilot in VS Code

After the first boilerplate was in place, I moved to the free Copilot experience available in Visual Studio Code, which is essentially the assistant you are using now. That became the main implementation partner for:

- refining the code
- fixing issues in the app and SQL flow
- improving the prompt structure
- building the evaluation harness
- checking the repo contents and documentation
- iterating quickly on the final deliverables

So in simple terms:

- ChatGPT helped create the first idea and starting structure
- Copilot helped turn that idea into a working implementation and keep improving it

## 4. Building the Snowflake pipeline

I split the work into stages so it would be easier to validate and debug.

### Stage 1: raw ingestion
The raw source data was kept as-is in a raw VARIANT table so that the original data remains available for traceability.

### Stage 2: core events
The raw JSON was flattened into a typed core event table. This gave us structured fields such as:

- IPs
- ports
- hostnames
- domains
- organizations
- cloud metadata
- banners and version information
- timestamps

### Stage 3: account features
The event-level data was aggregated into account-level signals such as:

- risky port count
- remote admin exposure
- legacy protocol exposure
- technology signals
- cloud hosting flags
- distinct IP and port counts
- recent activity

### Stage 4: scoring
The account score was generated using deterministic rules rather than an LLM. This was important because the ranking should be reproducible, explainable, and auditable.

That is why the scoring layer was kept separate from the AI layer.

## 5. Designing the AI layer

Once the scoring layer was working, I added the AI layer on top.

The AI feature was designed to do something specific:

- read structured evidence from Snowflake
- summarize the strongest signals
- explain why an account matters now
- suggest likely buyer personas
- propose an outreach angle

The key rule was that the AI should not invent unsupported facts. It should act as a summarizer and translator of evidence, not as the source of truth for ranking.

## 6. Building the app

I created a Streamlit app so the product could be demonstrated end-to-end.

The app lets a user:

- view the ranked accounts
- inspect account-level evidence
- see why a company was assigned a priority
- generate an AI account brief
- review the output in a simple UI

This made the demo practical and easy to understand.

## 7. Prompt versioning and AI workflow packaging

To satisfy the AI-native requirement, I created:

- a reusable `SKILL.md` for the account intelligence workflow
- versioned prompts for prompt comparison
- a clear separation between prompt versions such as `v1` and `v2`

This matters because the task is not only about shipping an app, but also about showing how AI workflows are structured, versioned, and reused.

## 8. Evaluation setup

I also built a proper evaluation process.

The repo includes:

- a labelled eval set
- prediction generation
- evaluation logic
- prompt comparison scripts
- a results summary

This was important because the task explicitly asks to measure quality instead of simply assuming the AI output is good.

The evaluation flow was:

1. prepare a small labelled dataset
2. run the model or prompt against those examples
3. compare predicted priority with expected labels
4. calculate precision, recall, and F1
5. record strengths and weaknesses

## 9. Observability and tracing

A good AI system needs to be debuggable and visible.

That is why I included an observability layer for model calls, with fields such as:

- request
- response
- model
- prompt version
- latency
- estimated tokens
- cost
- decision outcome

This makes it possible to compare prompt versions and understand where failures or weak outputs are coming from.

## 10. Hosting and final packaging

Once the app and pipeline were working locally, I prepared it for hosting and for submission.

The final package included:

- app files
- SQL files
- prompts
- skills
- evals
- docs
- README
- metadata files

The hosted app link was kept separate from the repo and credentials were not pushed.

## 11. What I learned from the process

The biggest lesson was that the AI part was not the whole solution. The real value came from combining:

- deterministic rules for ranking
- structured evidence for explainability
- AI for natural-language summarization
- evaluation for quality measurement
- observability for debugging and comparison

That combination is what makes the system feel production-ready rather than like a prompt bolted onto a dashboard.

## 12. What I would do next in production

If this were going further, I would add:

- CRM outcome tracking
- better score calibration using historical sales results
- larger labelled datasets
- cost monitoring dashboards
- stricter prompt guardrails for unsupported claims
- programmatic quality checks on sampled outputs

## 13. Final outcome

The outcome of this work is a working, hosted AI-native prospecting system that:

- uses Snowflake for core data processing and scoring
- uses Streamlit for the product interface
- uses AI for evidence-backed summaries and outreach drafting
- includes prompt versioning, evals, and observability
- is structured in a way that can be reviewed and built upon by a teammate

That is the core story I would explain when writing this document or sending the repo for review.
