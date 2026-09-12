# Account Intelligence Skill

## Trigger
Run when a prioritized account needs a salesperson-ready cybersecurity brief.

## Inputs
- account key and organization
- deterministic priority score
- score breakdown
- account-level infrastructure evidence
- prompt version

## Outputs
JSON:
- summary
- observed_evidence
- why_now
- pain_hypotheses
- recommended_buyer_personas
- outreach_angle
- confidence
- caveats

## Rules
1. Use only supplied evidence.
2. Never invent breaches, incidents, employees, revenue, funding, contacts or vulnerabilities.
3. Separate facts from hypotheses.
4. Do not change the numeric score.
5. Buyer personas are recommendations, not known contacts.
6. If evidence is insufficient, say so.

## Worked example
If an account has exposed RDP, public web services and cloud hosting, state those as observations and describe possible security relevance as hypotheses. Do not claim the account has been breached.
