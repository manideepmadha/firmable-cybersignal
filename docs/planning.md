# Planning

## Business problem
Sales needs to know which businesses should be contacted first for cybersecurity software.

## Dataset insight
The source is internet-facing infrastructure telemetry: IPs, ports, domains, hostnames, organizations, banners, HTTP observations, cloud/ISP metadata and timestamps.

## Product hypothesis
Organizations with larger or riskier external attack surfaces are stronger cybersecurity prospects, especially when multiple signals converge.

## Signals chosen for the prototype
- risky exposed ports
- remote administration services
- legacy protocols
- technology/version banners
- public web services
- cloud hosting
- number of exposed IPs
- number of domains/hostnames
- observation recency
- explicit vulnerability fields when present

## Score design
Initial hypothesis:
- Exposure 30%
- Risky services 25%
- Technology/version 15%
- Complexity 15%
- Cloud 10%
- Recency/data quality 5%

The score must remain deterministic and explainable. Tune weights after inspecting the real distribution.

## AI boundary
AI does not calculate the numeric score. It summarizes evidence, explains why now, proposes pain hypotheses and buyer personas, and drafts an outreach angle.

Every AI claim must be grounded in the structured evidence bundle.

## Client-facing use cases chosen
1. Account prioritization
   - Sales can see the strongest accounts first.
   - Priority is derived from deterministic score plus evidence.

2. Evidence-backed account review
   - Sales can inspect why an account is ranked highly.
   - Evidence includes IPs, ports, services, cloud signals, and recency.

3. AI-generated account brief
   - Sales gets a compact summary, why-now narrative, buyer persona suggestions, and outreach angle.

4. Prompt and model comparison
   - The system supports prompt versioning so different prompt versions can be compared.

5. Evaluation and quality measurement
   - The repo includes labelled examples and evaluation scripts to analyze quality.

## Take-home deliverables mapping
This repo already covers several required deliverables:
- working app: yes, local and Cloud-ready app exist
- skills directory: yes, `skills/account-intelligence/SKILL.md` exists
- prompts directory: yes, `prompts/account_brief/v1.md` and `v2.md` exist
- evals directory: yes, scripts and template exist
- observability schema: yes, via `sql/07_observability.sql`
- architecture overview: yes, in `docs/architecture.md`
- planning overview: yes, in this file

Still required before final client submission:
- real labelled dataset (20–30 accounts) instead of the template placeholders
- final results file with measured precision/recall/F1 for the labelled set
- hosted live URL if the client expects a public shareable app link
- public GitHub repo or private repo with the final code pushed
- short reflection on the dev loop and AI usage
- optional Loom walkthrough

## Git push checklist for the client submission
Push the following content to Git:
- `app/` directory
- `docs/` directory
- `evals/` directory
- `prompts/` directory
- `skills/` directory
- `sql/` directory
- `scripts/` directory
- `README.md`
- `snowflake.yml`
- `.gitignore`
- `requirements.txt`

Do not push:
- `.venv/`
- `.streamlit/secrets.toml`
- generated result folders if they contain sensitive data
- local cache folders
- local logs or temp files
- credentials or API keys

## Required client-facing documentation to add before submission
1. Architecture document with rule-vs-LLM split
2. Planning document with use cases and signal choices
3. Cost model document or section
4. Eval results summary
5. How-you-build reflection
6. Hosted app link and setup notes

## Cost model and testing strategy
The client asked for cost awareness. We should document it explicitly.

### Cost model to include
Estimate costs per task using:
- model choice
- average input tokens per request
- average output tokens per request
- request volume per day/week
- cost per 1M tokens for the selected model

Example formula:
- cost per request = (input_tokens / 1_000_000) * input_token_price + (output_tokens / 1_000_000) * output_token_price
- monthly cost estimate = cost per request * requests per month

### Recommended model split
- Cheap model for classification / structured extraction tasks
- Stronger model only for nuanced reasoning or summarization tasks

### What to test for cost
- average tokens per account brief
- requests per day for a small sales team
- request failure rate and retry cost
- prompt length vs. output quality trade-off
- cost ceiling for low-priority accounts

### Recommended cost test plan
1. Run the brief generation for a known sample of accounts.
2. Capture prompt length, response size, latency, and model used.
3. Estimate the average cost per account.
4. Compare v1 and v2 prompts for token efficiency.
5. Set a production ceiling such as:
   - max AI calls per day
   - max output token budget per account
   - low-cost model for first-pass classification
   - stronger model only for selected high-fit accounts

## Final submission readiness checklist
- [ ] app runs locally
- [ ] app runs in Streamlit Community Cloud or equivalent hosted location
- [ ] Snowflake queries work against the expected tables
- [ ] AI brief generation works with a valid external provider key
- [ ] skills directory exists and is documented
- [ ] prompts v1 and v2 are tracked
- [ ] evals directory includes labelled set and results
- [ ] observability schema is defined and call logs are being stored
- [ ] cost model section is added to the architecture doc
- [ ] Git repo is pushed with the required files
- [ ] hosted app link is included in the submission
- [ ] final reflection document is added

## Final client-facing recommendation
For submission, present this as a hybrid architecture:
- deterministic rules in Snowflake for the scoring layer
- Streamlit for the user interface
- external AI for account brief generation
- evaluation and observability built into the system from the start

That gives the client both product value and evidence that the AI workflow was engineered responsibly, not just bolted on.
