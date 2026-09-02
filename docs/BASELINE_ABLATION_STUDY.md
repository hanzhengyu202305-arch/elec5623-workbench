# Draft Baseline, Ablation, and Error Study

## Result

The fixture-only development study now uses `20` synthetic bundles, `200` claims,
`5` surface-form template families, and `4` Markdown layouts. The full fixture
pipeline passes every draft threshold without producing a misleading perfect
score:

| Metric | Full fixture | Draft threshold | Result |
| --- | ---: | ---: | --- |
| Citation completeness | `1.0000` | `1.00` | PASS |
| Five-label macro-F1 | `0.8577` | `0.65` | PASS |
| Unsupported/contradicted precision | `0.9302` | `0.80` | PASS |
| Unsupported/contradicted recall | `1.0000` | `0.75` | PASS |
| Requirement-mapping macro-F1 | `0.9600` | `0.70` | PASS |

This remains `DRAFT_DEV_UNFROZEN_NOT_TUTOR_APPROVED`. It is not a held-out,
clean-room, live-provider, or tutor-approved result.

## Study design

`scripts/run_baseline_study.py` evaluates five deterministic variants:

1. `citation_presence_b0` labels every known cited claim as supported and performs
   no lexical, contradiction, quote, or requirement reasoning.
2. `full_fixture_replay` mirrors the product's fixture path and is required to
   produce the same normalized predictions as the actual service.
3. `ablation_no_citation_priority` removes the rule that presents explicitly
   cited evidence to the gateway before lexical distractors.
4. `ablation_no_exact_quote_guard` removes deterministic altered-quote failure
   closure.
5. `ablation_no_requirement_mapping` removes claim-to-requirement mapping.

The corpus contains a declared lexical distractor and an altered exact-quote
case so the first two safety ablations are observable rather than vacuous.

## Quantitative comparison

| Variant | Macro-F1 | Risky precision | Risky recall | Mapping macro-F1 |
| --- | ---: | ---: | ---: | ---: |
| Citation-presence B0 | `0.1500` | `0.0000` | `0.0000` | `0.0000` |
| Full fixture | `0.8577` | `0.9302` | `1.0000` | `0.9600` |
| No citation priority | `0.8457` | `0.8511` | `1.0000` | `0.9600` |
| No exact-quote guard | `0.8302` | `0.9231` | `0.9000` | `0.9600` |
| No requirement mapping | `0.8577` | `0.9302` | `1.0000` | `0.0000` |

The full pipeline still has `37` label errors and `12` mapping errors. Every
error is retained with the scoped claim ID, claim text, expected and actual
label, and expected and actual requirement mapping. This is the error-analysis
backlog; it must not be hidden by aggregate metrics.

## Reproducibility handles

Retained report:

```text
acceptance/local-20260803-multitemplate-study-v3/baseline-study.json
acceptance/local-20260804-review-integrity-v2/corpus-acceptance.json
```

Deterministic handles:

```text
corpus_sha256             45e8a30308ad78be0dcb1ed48d3fa9cf4684bacd3ed348cc3a4c17e25ca09fa9
service_prediction_sha256 8f28dff5ae7d65a817f16de63447f252b187ba6f3f0df7607ff0b8ad4aba804f
```

Run a new no-clobber study from the Python 3.11 environment:

```bash
python scripts/run_baseline_study.py \
  --runs-dir /new/path/runs \
  --out /new/path/baseline-study.json
```

The command uses `FixtureModelGateway`, makes no external API call, writes to new
paths only, and emits the full confusion matrices and error rows. A reused runs
root or report path fails closed.

## Limitations and freeze gate

- Template variation is not out-of-distribution generalization.
- Synthetic labels require a documented human annotation review.
- The fixture gateway is a transparent lexical baseline, not evidence of live
  provider quality.
- Corpus, annotation protocol, thresholds, and split remain unfrozen until the
  tutor-approved scope is recorded.
- Frozen test data must not be tuned after results are inspected; later changes
  require a new version, rationale, and separate development/test accounting.
