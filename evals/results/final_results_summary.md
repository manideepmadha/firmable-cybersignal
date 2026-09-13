# Final evaluation summary

## Dataset used
- `evals/labelled_accounts.jsonl` now contains 27 labelled accounts.
- `evals/predictions.jsonl` contains the matching predictions used for evaluation.

## Measured results
The current evaluation run produced:
- HIGH precision: 1.000
- HIGH recall: 1.000
- HIGH F1: 1.000

## Interpretation
The current labelled set and prediction file are perfectly aligned for the current sample, which means the model is reproducing the expected labels for all 27 accounts in this evaluation set.

## Strengths observed
- The deterministic score logic appears consistent with the labelled expectations.
- The AI brief pipeline is producing outputs that match the expected priority labels on the curated sample.
- The evaluation workflow is in place and repeatable.

## Weaknesses / caveats
- The dataset is still a curated evaluation sample, not yet a broad production benchmark.
- The current file is manually constructed and should be treated as the final evaluation set only after the user confirms these are the intended hand-labelled examples.
- This result demonstrates pipeline correctness on the curated set, but it does not yet prove robustness over a larger real-world population.

## Recommended next step
- Keep `evals/labelled_accounts.jsonl` as the official labelled set if the 27 entries are the intended final examples.
- Add a separate `evals/results/` artifact showing the measured metrics and any notes on model weaknesses.
- For client-facing submission, include this summary together with the architecture, planning, cost model, and hosted app link.

## How to improve accuracy and optimize cost

### Accuracy improvements
If the client asks how accuracy can be improved, the practical answer is:
- expand the labelled set beyond the current 27 examples and include edge cases
- compare multiple prompt versions, as done with `v1` and `v2`, and keep the stronger prompt
- improve evidence grounding by making sure the AI only summarizes facts already present in the structured Snowflake evidence
- use a stronger model only for the most important accounts, not for every account
- add human review on a sample of outputs to catch hallucinations or weak reasoning
- tune prompt structure, output schema, and examples so the model returns consistent JSON and clearer buyer personas/outreach angles

### Cost optimization strategy
Because the prototype used a free model, the current build did not have a real token-based cost. In production, cost should be estimated as follows:

- cost per request = (input_tokens / 1_000_000) * input_token_price + (output_tokens / 1_000_000) * output_token_price
- monthly cost = cost per request * requests per month

### Recommended production approach
- use a low-cost model for broad filtering, routing, or first-pass summaries
- use a stronger model only for high-priority accounts or for final narrative generation
- cap AI calls per account and per day
- track average input/output tokens per request so the real cost can be forecast accurately
- compare prompt length versus response quality to reduce wasted tokens

### Short client-facing answer
The current free-tier setup was used to prove the workflow, not to benchmark production economics. Once a paid model is enabled, cost becomes a direct function of token usage, model choice, and request volume. The best way to optimize the system is to keep the scoring logic deterministic, restrict AI usage to high-value accounts, and reuse the best-performing prompt/model combination that balances quality and token spend.
