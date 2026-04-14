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

Generate LISA feed artifacts:

```powershell
py -3 -m cli.main --input config/examples/business_viability_case.json --emit-lisa-feed --feed-json factdeck_lisa_feed.json --feed-ndjson factdeck_lisa_feed.ndjson --feed-page dashboard/lisa-feed/index.html
```

Delta mode from a previous publish:

```powershell
py -3 -m cli.main --input config/examples/business_viability_case.json --emit-lisa-feed --delta-from factdeck_lisa_feed.json
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
