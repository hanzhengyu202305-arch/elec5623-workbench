from __future__ import annotations

import importlib.util
from pathlib import Path


def test_generator_builds_20_original_bundles_and_200_claims() -> None:
    path = Path(__file__).resolve().parents[1] / "scripts" / "generate_synthetic_corpus.py"
    spec = importlib.util.spec_from_file_location("corpus_generator", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    corpus = module.build_corpus()
    assert len(corpus) == 20
    assert sum(len(bundle.expected_claims) for bundle in corpus) == 200
    assert len({bundle.bundle_id for bundle in corpus}) == 20
    model_handles = {bundle.generated_output.model for bundle in corpus}
    assert {handle.split(":")[1] for handle in model_handles} == set(
        module.TEMPLATE_FAMILIES
    )
    assert {handle.split(":")[2] for handle in model_handles} == set(
        module.MARKDOWN_LAYOUTS
    )


def test_every_template_family_preserves_all_five_labels() -> None:
    path = Path(__file__).resolve().parents[1] / "scripts" / "generate_synthetic_corpus.py"
    spec = importlib.util.spec_from_file_location("corpus_generator_labels", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    bundles = module.build_corpus()
    for family in module.TEMPLATE_FAMILIES:
        family_bundles = [
            bundle
            for bundle in bundles
            if bundle.generated_output.model.split(":")[1] == family
        ]
        labels = {
            expected.label.value
            for bundle in family_bundles
            for expected in bundle.expected_claims
        }
        assert labels == {
            "SUPPORTED",
            "PARTIALLY_SUPPORTED",
            "UNSUPPORTED",
            "CONTRADICTED",
            "INSUFFICIENT_EVIDENCE",
        }
