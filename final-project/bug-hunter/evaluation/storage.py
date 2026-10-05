"""Read recorded runs and append human judgements without changing raw evidence."""
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictInt

PROJECT = Path(__file__).resolve().parent.parent
RESULTS = PROJECT / "evaluation" / "results"
REVIEWS = PROJECT / "evaluation" / "reviews"


class HumanReview(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    reviewer: str = Field(min_length=1, max_length=120)
    intended_bug_detected: Literal["Yes", "No", "Unclear"]
    explanation_correct: Literal["Yes", "No", "Partially"]
    suggested_fix_correct: Literal["Yes", "No"]
    false_positive_findings: StrictInt = Field(ge=0, le=50)
    notes: str = Field(default="", max_length=4000)


def recorded_bool(value):
    if value is None or value == "":
        return None
    if type(value) is bool:
        return value
    if value in ("True", "true", "Yes"):
        return True
    if value in ("False", "false", "No"):
        return False
    raise ValueError("Invalid recorded boolean value.")


def list_runs(root: Path = RESULTS) -> list[Path]:
    # JSON is preferred; CSV-only older exports remain visible with limited-evidence labels.
    runs = list(root.glob("results-*.json"))
    runs += [path for path in root.glob("results-*.csv") if not path.with_suffix(".json").exists()]
    runs += list((root / "reviewed").glob("results-*.json"))
    return sorted(runs, key=lambda path: path.name, reverse=True)


def read_run(path: Path) -> dict:
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        with path.open(encoding="utf-8", newline="") as handle:
            data = {"results": list(csv.DictReader(handle)), "evidence": [], "limited_evidence": True}
    rows = data.get("results")
    if not isinstance(rows, list) or not all(isinstance(row, dict) and row.get("case_id") for row in rows):
        raise ValueError("Saved run needs a results list with case IDs.")
    if len({row["case_id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate case IDs in a saved run.")
    evidence = {item["case"]["id"]: item for item in data.get("evidence", [])}
    for row in rows:
        duration = float(row.get("analysis_seconds") or 0)
        if not math.isfinite(duration) or duration < 0:
            raise ValueError("Invalid recorded duration.")
        item = evidence.get(row["case_id"])
        if not item:
            if path.suffix == ".json":
                raise ValueError("Raw evidence is missing for a recorded case.")
            continue
        report = item["report"]
        raw = report.get("ai", {}).get("raw_response", "")
        response_hash = row.get("ai_response_sha256")
        if response_hash and hashlib.sha256(raw.encode("utf-8")).hexdigest() != response_hash:
            raise ValueError("Model response hash does not match recorded evidence.")
        if recorded_bool(row.get("ai_fix_successful")):
            original, fixed = report.get("original_tests", {}), report.get("corrected_tests", {})
            code = (report.get("ai", {}).get("analysis") or {}).get("corrected_code", "")
            if not (original.get("failed", 0) > 0 and original.get("status") == "failed"
                    and fixed.get("status") == "passed" and fixed.get("exit_code") == 0
                    and fixed.get("passed", 0) > 0 and fixed.get("passed") == fixed.get("collected")
                    and not any(fixed.get(key, 0) for key in ("failed", "errors", "skipped"))
                    and code.strip() != report.get("source", "").strip()):
                raise ValueError("A verified-fix claim is not supported by its raw test evidence.")
    return data


def save_review(run_path: Path, case_id: str, judgement: dict, root: Path = REVIEWS) -> Path:
    data = read_run(run_path)
    item = next((item for item in data.get("evidence", []) if item["case"]["id"] == case_id), None)
    raw = item["report"].get("ai", {}).get("raw_response") if item else None
    if not raw:
        raise ValueError("Human review requires the actual saved AI response, not a CSV-only or baseline-only result.")
    review = HumanReview.model_validate(judgement)
    findings = item["report"].get("ai", {}).get("analysis")
    if findings and review.false_positive_findings > len(findings["findings"]):
        raise ValueError("False-positive count cannot exceed the returned findings count.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    document = {"format_version": 1, "reviewed_utc": stamp, "run_file": run_path.name,
                "run_sha256": hashlib.sha256(run_path.read_bytes()).hexdigest(), "case_id": case_id,
                "response_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                "judgement": review.model_dump()}
    root.mkdir(parents=True, exist_ok=True)
    destination = root / f"review-{stamp}.json"
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2)
    return destination


def load_reviews(run_path: Path, root: Path = REVIEWS) -> tuple[dict, list[str]]:
    reviews, issues = {}, []
    digest = hashlib.sha256(run_path.read_bytes()).hexdigest()
    data = read_run(run_path)
    hashes = {item["case"]["id"]: hashlib.sha256(item["report"].get("ai", {}).get("raw_response", "").encode("utf-8")).hexdigest()
              for item in data.get("evidence", [])}
    for path in sorted(root.glob("review-*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("run_sha256") != digest:
                continue
            if hashes.get(record["case_id"]) != record["response_sha256"]:
                raise ValueError("Review response hash mismatch.")
            record["judgement"] = HumanReview.model_validate(record["judgement"]).model_dump()
            reviews[record["case_id"]] = record
        except (ValueError, KeyError, TypeError, OSError) as exc:
            issues.append(f"{path.name}: {exc}")
    return reviews, issues


def metrics(rows: list[dict], reviews: dict) -> dict:
    ai_rows = [row for row in rows if row.get("ai_status") not in (None, "not_run")]
    judgements = [record["judgement"] for record in reviews.values()]
    legacy = [row for row in rows if row["case_id"] not in reviews
              and row.get("ai_detected_intended_bug") in {"Yes", "No"}]
    durations = [float(row["analysis_seconds"]) for row in ai_rows if row.get("analysis_seconds") not in (None, "")]
    return {"cases": len(rows), "ai_attempted": len(ai_rows),
            "ai_responded": sum(row.get("ai_status") == "ok" for row in ai_rows),
            "fixes_generated": sum(recorded_bool(row.get("ai_produced_fix")) is True for row in ai_rows),
            "fixes_verified": sum(recorded_bool(row.get("ai_fix_successful")) is True for row in ai_rows),
            "human_reviewed": len(judgements) + len(legacy),
            "intended_bug_yes": sum(j["intended_bug_detected"] == "Yes" for j in judgements)
                                + sum(row["ai_detected_intended_bug"] == "Yes" for row in legacy),
            "explanation_yes": sum(j["explanation_correct"] == "Yes" for j in judgements),
            "pylint_functional_yes": sum(row.get("pylint_detected_functional_issue") == "Yes" for row in rows),
            "average_seconds": sum(durations) / len(durations) if durations else None}
