# FactDeck LISA Feed Contract

## Wrapper Fields

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

## Item Types

1. `FactSignal`

Fields:
- `source_system`
- `source_type`
- `generated_at`
- `lane`
- `entity`
- `topic`
- `claim`
- `normalized_fact`
- `fact_type`
- `confidence`
- `freshness`
- `source_count`
- `evidence_refs`
- `contradiction_risk`
- `status` (`confirmed | provisional | disputed`)
- `tags`

2. `EvidencePacket`

Fields:
- `packet_id`
- `entity`
- `topic`
- `supporting_claims`
- `sources`
- `source_quality_summary`
- `time_range`
- `confidence`
- `gaps`

3. `TopicIntelPacket`

Fields:
- `topic`
- `lane`
- `summary`
- `key_facts`
- `new_facts`
- `disputed_facts`
- `confidence`
- `recommended_attention_level`

4. `ContradictionSignal`

Fields:
- `entity`
- `topic`
- `claim_a`
- `claim_b`
- `source_a`
- `source_b`
- `relative_strength`
- `resolution_status`

