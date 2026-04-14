# FactDeck Decision Engine (v1)

FactDeck is a domain-first decision engine.

It is built to answer:
- Which option is strongest right now?
- Which path has the best odds under constraints?
- What should I do next, and why?

It is not built to promise exact prediction or certainty.

## v1 Scope

- One domain: `business_viability`
- Transparent scoring first
- Scenario comparison (`base`, `upside`, `downside`)
- Explicit uncertainty handling
- Action-oriented recommendation output
- Decision memory logging

## Repo Layout

```text
config/
core/
domains/
connectors/
scoring/
models/
scenarios/
reports/
memory/
dashboard/
cli/
```

## Run

```powershell
python -m cli.main --input config/examples/business_viability_case.json
```

Optional memory log location:

```powershell
python -m cli.main --input config/examples/business_viability_case.json --memory memory/decision_log.jsonl
```

## Output Contract

Each run returns:
- decision label
- confidence band
- ranked options
- top positive drivers
- top negative drivers
- key unknowns
- scenario comparison
- recommended next action
- what evidence would change the answer

