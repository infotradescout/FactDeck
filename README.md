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
py -3 -m cli.main --input config/examples/business_viability_case.json --use-connectors
```

Optional memory log location:

```powershell
py -3 -m cli.main --input config/examples/business_viability_case.json --memory memory/decision_log.jsonl --use-connectors
```

Generate LISA feed artifacts:

```powershell
py -3 -m cli.main --input config/examples/business_viability_case.json --emit-lisa-feed --use-connectors --feed-json factdeck_lisa_feed.json --feed-ndjson factdeck_lisa_feed.ndjson --feed-page dashboard/lisa-feed/index.html
```

Automatic delta mode from publish history:

```powershell
py -3 -m cli.main --input config/examples/business_viability_case.json --emit-lisa-feed --auto-delta
```

Versioned publish workflow:

```powershell
py -3 -m cli.main --command publish --input config/examples/business_viability_case.json --use-connectors --auto-delta
```

Move a contradiction through workflow:

```powershell
py -3 -m cli.main --input config/examples/business_viability_case.json --emit-lisa-feed --contradiction-action "contradiction:case-2026-04-14-001:A:investigating"
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

## LISA Feed Layer

FactDeck exports LISA-ready knowledge objects with a shared packet wrapper:
- `source_system`
- `packet_type`
- `generated_at`
- `lane`
- `priority`
- `summary`
- `items`
- `evidence_refs`
- `fresh_until`
- `publish_status`

FactDeck item types:
- `FactSignal`
- `EvidencePacket`
- `TopicIntelPacket`
- `ContradictionSignal`

The human-facing feed page is generated at `dashboard/lisa-feed/index.html` with:
- Section A: LISA-ready fact signal cards
- Section B: raw JSON and NDJSON payload
- Section C: evidence explorer table

## Connector Inputs

Structured connector datasets are read from `connectors/data/`:
- `demographics.json`
- `search_signals.json`
- `cost_pressures.json`
- `regulatory_flags.json`

## Publish Memory

- Publish history: `memory/lisa_feed_history.jsonl`
- Contradiction lifecycle store: `memory/contradictions.json`
- Versioned outputs: `feeds/YYYY-MM-DD/`

## Tests

```powershell
py -3 -m unittest discover -s tests
```
