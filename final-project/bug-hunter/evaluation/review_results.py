"""Attach human judgements to an existing real run, verified by response hash."""

import argparse
import json
from pathlib import Path

from evaluation.run_evaluation import export_results


def apply_annotations(data: dict, annotations: dict) -> tuple[list[dict], list[dict]]:
    rows = data["results"]
    ids = {row["case_id"] for row in rows}
    if set(annotations) - ids:
        raise ValueError("Annotation names a case outside this saved run.")
    for row in rows:
        annotation = annotations.get(row["case_id"])
        if annotation is None:
            continue
        judgement = annotation.get("ai_detected_intended_bug")
        if type(judgement) is not bool or not row.get("ai_response_sha256"):
            raise ValueError("Review needs a real model response and a JSON true/false judgement.")
        if annotation.get("response_sha256") != row["ai_response_sha256"]:
            raise ValueError("Annotation response hash does not match this saved run.")
        row["ai_detected_intended_bug"] = "Yes" if judgement else "No"
    evidence = data["evidence"]
    by_id = {row["case_id"]: row for row in rows}
    for item in evidence:
        item["measurements"] = by_id[item["case"]["id"]]
    return rows, evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--annotations", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("evaluation/results/reviewed"))
    args = parser.parse_args()
    data = json.loads(args.results.read_text(encoding="utf-8"))
    annotations = json.loads(args.annotations.read_text(encoding="utf-8"))
    rows, evidence = apply_annotations(data, annotations)
    csv_path, json_path = export_results(rows, evidence, args.output)
    print(f"Reviewed copies: {csv_path}\n{json_path}\nOriginal run evidence was preserved.")


if __name__ == "__main__":
    main()
