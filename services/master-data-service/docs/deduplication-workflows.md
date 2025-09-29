# Deduplication Workflows

## Matching Pipeline

1. **Normalization** – Canonicalize incoming attributes (case folding, trimming, phone number formatting, transliteration).
2. **Deterministic Matching** – Apply exact match rules on stable identifiers (email, phone, government ID) with weighting.
3. **Probabilistic Scoring** – Use similarity functions (Levenshtein, Jaro-Winkler, TF-IDF) for fuzzy attributes; aggregate into a composite score.
4. **Rule Evaluation** – Determine action thresholds:
   - `>= 0.95`: auto-merge into canonical record.
   - `0.75 - 0.94`: create `potential_duplicates` entry for review.
   - `< 0.75`: create new canonical user.
5. **Conflict Recording** – Populate `attribute_lineage` with source contributions and mark conflicting attributes.

## Merge Decisioning

- When auto-merging, preserve the oldest canonical `id` and update `legacy_ids` with identifiers from the losing record.
- Maintain a merge audit entry capturing the rule path, scores, reviewer (if manual), and timestamps.
- Allow manual overrides via the moderation UI; decisions flow back through the ingestion workers using a dedicated moderation topic (`mds.merge-decisions.v1`).

## Reconciliation Jobs

- Nightly job recomputes similarity for unresolved `source_identities` older than 24h.
- Weekly job re-evaluates potential duplicates after new attribute updates land.
- Alerts trigger when potential duplicates exceed threshold levels or when merge decision SLAs breach.

## Data Quality Safeguards

- Enforce attribute-level validation (email format, phone E.164) at ingestion.
- Quarantine suspicious payloads (e.g., invalid country codes) for manual review.
- Provide lineage queries so downstream systems can trace attribute origins for compliance.
