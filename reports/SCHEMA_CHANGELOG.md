# Schema Changelog

## 1.0 (2026-04-14)

- Introduced stable FactDeck LISA feed wrapper:
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
  - `schema_version`
- Added object types:
  - `FactSignal`
  - `EvidencePacket`
  - `TopicIntelPacket`
  - `ContradictionSignal`
- Added `item_fingerprint` for delta tracking.
- Added publish manifest checksums and latest index.

## Compatibility Policy

- Major version change indicates potential breaking changes.
- Minor/patch changes must preserve required top-level fields.
- `schema_guard` checks major compatibility at publish time.

