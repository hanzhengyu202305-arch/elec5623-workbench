#!/usr/bin/env python3
"""Build a deterministic, project-original 20-bundle/200-claim corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evidence_inspector.schemas import EvaluationBundle


DOMAINS = [
    ("library kiosk", "checkout event", "book barcode"),
    ("solar monitor", "panel reading", "panel identifier"),
    ("campus shuttle", "arrival estimate", "stop identifier"),
    ("water meter", "usage reading", "meter identifier"),
    ("lab booking", "reservation", "room identifier"),
    ("garden sensor", "soil reading", "plot identifier"),
    ("bike station", "dock update", "station identifier"),
    ("warehouse counter", "inventory count", "shelf identifier"),
    ("museum guide", "exhibit note", "exhibit identifier"),
    ("study planner", "study session", "course identifier"),
    ("air monitor", "quality reading", "sensor identifier"),
    ("recycling tracker", "collection event", "bin identifier"),
    ("sports scheduler", "training session", "team identifier"),
    ("food pantry", "stock update", "item identifier"),
    ("tree survey", "tree observation", "tree identifier"),
    ("device register", "maintenance event", "device identifier"),
    ("energy dashboard", "consumption reading", "building identifier"),
    ("volunteer roster", "shift record", "volunteer identifier"),
    ("rain gauge", "rainfall reading", "gauge identifier"),
    ("quiet-space map", "noise observation", "zone identifier"),
]

TEMPLATE_FAMILIES = ("direct", "passive", "policy", "audit", "compact")
MARKDOWN_LAYOUTS = ("bullets", "numbered", "plain-lines", "mixed-lists")


def _claims_for_family(
    family: str, system: str, record: str, identifier: str
) -> list[str]:
    """Return semantically aligned claims with varied surface forms."""

    shared_tail = [
        f"The {system} exports both JSON and PDF [E3].",
        f"The {system} can approve external actions [E4].",
        "National demand will rise next year [E4].",
    ]
    families = {
        "direct": [
            f"The {system} validates every {record} [E1].",
            f"A non-empty {identifier} is required [E1].",
            f"External overseas vendors immediately receive encrypted rejected {record} backups [E1].",
            f"Each accepted {record} receives an audit timestamp [E2].",
            f"Uncertain {record} data is routed to human review [E2].",
            f"Accepted {record} data can be exported as JSON [E3].",
            'The export "omits personal names" [E3].',
            *shared_tail,
        ],
        "passive": [
            f"Every {record} is validated by the {system} [evidence:E1].",
            f"A non-empty {identifier} is required by the {system} [E1].",
            f"Encrypted rejected {record} backups are sent at once to overseas vendors [E1].",
            f"An audit timestamp is assigned to each accepted {record} [evidence:E2].",
            f"Human review receives uncertain {record} data [E2].",
            f"JSON export is available for accepted {record} data [E3].",
            'Personal-data handling is explicit: the export "omits personal names" [E3].',
            *shared_tail,
        ],
        "policy": [
            f"Validation applies to each {record} in the {system} [E1].",
            f"The {identifier} must be non-empty for a valid {record} [E1].",
            f"Rejected {record} data is encrypted and replicated to foreign suppliers [E1].",
            f"The audit policy timestamps every accepted {record} [E2].",
            f"The review policy routes uncertain {record} data to a human [E2].",
            f"The export policy provides accepted {record} data as JSON [E3].",
            'The privacy rule says the export "omits personal names" [evidence:E3].',
            *shared_tail,
        ],
        "audit": [
            f"Audit finding: the {system} validates every {record} [E1].",
            f"Audit finding: every valid item has a non-empty {identifier} [E1].",
            f"Audit finding: overseas processors get encrypted rejected {record} backups immediately [E1].",
            f"Audit finding: every accepted {record} receives a timestamp [E2].",
            f"Audit finding: uncertain {record} data goes to human review [E2].",
            f"Audit finding: accepted {record} data is exportable as JSON [E3].",
            'Audit finding: the export "omits personal names" [E3].',
            *shared_tail,
        ],
        "compact": [
            f"{system.title()} validation covers every {record} [E1].",
            f"Required field: non-empty {identifier} [E1].",
            'The input contract says "Invalid records are safely rejected" [E1].',
            f"Accepted {record}: audit timestamp recorded [E2].",
            f"Uncertain {record}: human review required [E2].",
            f"Accepted {record}: JSON export available [E3].",
            'Privacy: the export "omits personal names" [E3].',
            *shared_tail,
        ],
    }
    return families[family]


def _render_markdown(layout: str, claims: list[str]) -> str:
    if layout == "bullets":
        body = "\n".join(f"- {claim}" for claim in claims)
    elif layout == "numbered":
        body = "\n".join(f"{index}. {claim}" for index, claim in enumerate(claims, 1))
    elif layout == "plain-lines":
        body = "\n\n".join(claims)
    else:
        body = "\n".join(
            f"- {claim}" if index % 2 else f"{index}. {claim}"
            for index, claim in enumerate(claims, 1)
        )
    return f"# Synthetic output\n\n{body}"


def build_bundle(index: int, system: str, record: str, identifier: str) -> dict[str, object]:
    prefix = f"B{index:02d}"
    family = TEMPLATE_FAMILIES[(index - 1) % len(TEMPLATE_FAMILIES)]
    layout = MARKDOWN_LAYOUTS[(index - 1) % len(MARKDOWN_LAYOUTS)]
    requirements = [
        {"id": "REQ-VALIDATE", "text": f"The {system} must validate each {record} and its {identifier}."},
        {"id": "REQ-AUDIT", "text": f"The {system} must retain an audit timestamp for each accepted {record}."},
        {"id": "REQ-EXPORT", "text": f"The {system} must export accepted {record} data as JSON."},
        {"id": "REQ-REVIEW", "text": f"The {system} must route uncertain {record} data to human review."},
        {"id": "REQ-PRIVACY", "text": f"The {system} must omit personal names from exported {record} data."},
    ]
    evidence = [
        {
            "id": "E1",
            "title": f"{prefix} input contract",
            "content": f"The {system} validates every {record} and requires a non-empty {identifier}. Invalid records are rejected.",
        },
        {
            "id": "E2",
            "title": f"{prefix} audit contract",
            "content": f"Each accepted {record} receives an audit timestamp. Uncertain {record} data is routed to human review.",
        },
        {
            "id": "E3",
            "title": f"{prefix} export contract",
            "content": f"Accepted {record} data can be exported as JSON. The export omits personal names.",
        },
        {
            "id": "E4",
            "title": f"{prefix} boundary",
            "content": f"The {system} provides decision support and cannot approve external actions.",
        },
    ]
    if family == "policy":
        evidence.append(
            {
                "id": "E5",
                "title": f"{prefix} lexical distractor",
                "content": f"The {system} does not validate every {record}.",
            }
        )
    claims = _claims_for_family(family, system, record, identifier)
    expected_labels = [
        "SUPPORTED",
        "SUPPORTED",
        "UNSUPPORTED",
        "SUPPORTED",
        "SUPPORTED",
        "SUPPORTED",
        "SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "CONTRADICTED",
        "INSUFFICIENT_EVIDENCE",
    ]
    expected_requirements = [
        ["REQ-VALIDATE"],
        ["REQ-VALIDATE"],
        [],
        ["REQ-AUDIT"],
        ["REQ-REVIEW"],
        ["REQ-EXPORT"],
        ["REQ-PRIVACY"],
        ["REQ-EXPORT"],
        [],
        [],
    ]
    return {
        "schema_version": "1.0",
        "bundle_id": f"synthetic-{index:02d}",
        "title": f"Synthetic audit for {system}",
        "requirements": requirements,
        "evidence": evidence,
        "generated_output": {
            "markdown": _render_markdown(layout, claims),
            "provider": "synthetic-corpus-generator",
            "model": f"multi-template-v2:{family}:{layout}",
        },
        "expected_claims": [
            {
                "claim_id": f"c{claim_index:03d}",
                "label": label,
                "requirement_ids": requirement_ids,
            }
            for claim_index, (label, requirement_ids) in enumerate(
                zip(expected_labels, expected_requirements, strict=True), 1
            )
        ],
    }


def build_corpus() -> list[EvaluationBundle]:
    bundles = [
        EvaluationBundle.model_validate(build_bundle(index, *domain))
        for index, domain in enumerate(DOMAINS, 1)
    ]
    if len(bundles) != 20 or sum(len(item.expected_claims) for item in bundles) != 200:
        raise RuntimeError("corpus invariant failed")
    return bundles


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    if not args.check_only and args.out is None:
        parser.error("provide --out or --check-only")
    return args


def main() -> int:
    args = parse_args()
    bundles = build_corpus()
    if args.check_only:
        print(json.dumps({"bundles": 20, "claims": 200, "valid": True}, sort_keys=True))
        return 0
    args.out.mkdir(parents=True, exist_ok=True)
    for bundle in bundles:
        path = args.out / f"{bundle.bundle_id}.json"
        with path.open("x", encoding="utf-8") as handle:
            handle.write(bundle.model_dump_json(indent=2) + "\n")
    manifest = args.out / "manifest.json"
    with manifest.open("x", encoding="utf-8") as handle:
        json.dump(
            {
                "schema_version": "1.0",
                "generator": "scripts/generate_synthetic_corpus.py",
                "bundles": len(bundles),
                "claims": sum(len(item.expected_claims) for item in bundles),
                "template_families": list(TEMPLATE_FAMILIES),
                "markdown_layouts": list(MARKDOWN_LAYOUTS),
                "provenance": "Project-original deterministic multi-template synthetic corpus",
            },
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
