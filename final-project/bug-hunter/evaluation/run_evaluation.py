"""Export actual case observations; intended-bug judgements require human review."""

import argparse
import csv
import hashlib
import json
import os
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from bug_hunter.ai.ollama_provider import DEFAULT_MODEL, OllamaProvider
from bug_hunter.analysis.pylint_runner import run_pylint
from bug_hunter.analysis.test_runner import run_tests
from bug_hunter.demos import CASES_DIR, load_cases
from bug_hunter.services import analyze_code


def detection_candidate(case: dict, report) -> bool:
    if not report.ai.analysis:
        return False
    return any(
        any(alias.casefold() in (finding.category + " " + finding.title).casefold()
            for alias in case["aliases"])
        and (finding.line is None or finding.line in case["bug_lines"])
        for finding in report.ai.analysis.findings
    )


def evaluate(cases: list[dict], model: str, provider=None, baseline_only=False,
             annotations: dict | None = None, test_timeout=10, on_case=None) -> tuple[list[dict], list[dict]]:
    rows, evidence = [], []
    annotations = annotations or {}
    for case in cases:
        start = time.perf_counter()
        if baseline_only:
            lint = run_pylint(case["source"])
            original = run_tests(case["source"], case["tests"], timeout=test_timeout)
            report = None
        else:
            report = analyze_code(case["source"], "Expected behavior: " + case["expected_behavior"],
                                  case["tests"], model, provider, test_timeout)
            lint, original = report.pylint, report.original_tests
        reference = run_tests(case["reference"], case["tests"], timeout=test_timeout)
        if not reference.all_passed or original.status != "failed" or original.failed < 1:
            raise ValueError(f"Dataset case {case['id']} failed its control check; no statistics exported.")
        annotation = annotations.get(case["id"], {})
        judgement = annotation.get("ai_detected_intended_bug")
        response_hash = hashlib.sha256(report.ai.raw_response.encode("utf-8")).hexdigest() if report and report.ai.raw_response else None
        if judgement is not None and type(judgement) is not bool:
            raise ValueError("Human annotations must use JSON true/false.")
        if judgement is not None and annotation.get("response_sha256") != response_hash:
            raise ValueError("Annotation does not match this model response; review this run separately.")
        # Style / refactor / unrelated error messages never count as the intended bug.
        pylint_match = any(m.symbol in case["pylint_symbols"] and m.line in case["bug_lines"]
                           for m in lint.messages) if lint.status == "ok" else None
        fixed = report.corrected_tests if report else None
        ai = report.ai if report else None
        row = {
            "case_id": case["id"], "bug_category": case["category"], "ollama_model": model,
            "ai_status": ai.status if ai else "not_run",
            "ai_response_sha256": response_hash,
            "ai_detected_intended_bug": ("Yes" if judgement else "No") if judgement is not None else "Unreviewed",
            "ai_detection_candidate_heuristic": detection_candidate(case, report) if report else None,
            "ai_number_of_findings": len(ai.analysis.findings) if ai and ai.analysis else None,
            "pylint_detected_functional_issue": ("Yes" if pylint_match else "No") if pylint_match is not None else "Unavailable",
            "pylint_status": lint.status, "pylint_total_findings": len(lint.messages),
            "ai_produced_fix": bool(ai and ai.analysis and ai.analysis.corrected_code.strip() != case["source"].strip()) if ai else None,
            "original_tests_passed": original.passed, "original_tests_failed": original.failed,
            "original_test_errors": original.errors,
            "corrected_tests_passed": fixed.passed if fixed else None,
            "corrected_tests_failed": fixed.failed if fixed else None,
            "corrected_test_errors": fixed.errors if fixed else None,
            "corrected_test_status": fixed.status if fixed else "not_run",
            "ai_fix_successful": report.fix_verified if report else None,
            "reference_tests_passed": reference.passed,
            "analysis_seconds": round(time.perf_counter() - start, 3),
            "service_seconds": round(report.duration, 3) if report else None,
            "case_attempted": True, "case_completed": True,
            "original_test_status": original.status,
            "external_api_cost_usd": 0,
            "prompt_tokens": ai.prompt_tokens if ai else None,
            "completion_tokens": ai.completion_tokens if ai else None,
            "context_window": ai.diagnostics.get("context_window") if ai else None,
            "output_limit": ai.diagnostics.get("output_limit") if ai else None,
            "model_load_seconds": ai.diagnostics.get("load_duration_seconds") if ai else None,
            "generation_seconds": ai.diagnostics.get("eval_duration_seconds") if ai else None,
        }
        rows.append(row)
        evidence.append({"case": case, "measurements": row,
                         "report": asdict(report) if report else {"pylint": asdict(lint), "original_tests": asdict(original)},
                         "reference_tests": asdict(reference)})
        if on_case:
            on_case(row, rows, evidence)
    return rows, evidence


def export_results(rows: list[dict], evidence: list[dict], output: Path) -> tuple[Path, Path]:
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    csv_path, json_path = output / f"results-{stamp}.csv", output / f"results-{stamp}.json"
    def encode_model(value):
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        raise TypeError(f"Cannot serialize {type(value).__name__}")
    serialized = json.dumps({"run_utc": stamp, "format_version": 2,
                            "cases_attempted": len(rows), "cases_completed": len(rows),
                            "results": rows, "evidence": evidence},
                            indent=2, ensure_ascii=False, default=encode_model)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["case_id"])
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(serialized, encoding="utf-8")
    return csv_path, json_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=os.getenv("BUG_HUNTER_MODEL", DEFAULT_MODEL))
    parser.add_argument("--cases-dir", type=Path, default=CASES_DIR)
    parser.add_argument("--case", action="append", help="Case ID; repeat to select several.")
    parser.add_argument("--baseline-only", action="store_true", help="Run lint/original/reference controls without AI.")
    parser.add_argument("--annotations", type=Path, help="Human judgement JSON keyed by case ID.")
    parser.add_argument("--output", type=Path, default=Path("evaluation/results"))
    parser.add_argument("--ai-timeout", type=float, default=180)
    parser.add_argument("--test-timeout", type=float, default=10)
    parser.add_argument("--context-window", type=int, default=4096)
    parser.add_argument("--output-limit", type=int, default=1536)
    parser.add_argument("--keep-alive", default="30m")
    args = parser.parse_args()
    cases = load_cases(args.cases_dir)
    if args.case:
        unknown = set(args.case) - {case["id"] for case in cases}
        if unknown:
            parser.error(f"Unknown case IDs: {sorted(unknown)}")
        cases = [case for case in cases if case["id"] in args.case]
    if not cases:
        parser.error("No evaluation cases found.")
    annotations = json.loads(args.annotations.read_text(encoding="utf-8")) if args.annotations else {}
    provider = None
    if not args.baseline_only:
        provider = OllamaProvider(timeout=args.ai_timeout, context_window=args.context_window,
                                  output_limit=args.output_limit, keep_alive=args.keep_alive)
        models, error = provider.list_models()
        if error or args.model not in models:
            parser.error(error or f"Local model {args.model!r} is not installed. No AI run was recorded.")
    print(f"Running {len(cases)} case(s). Execute trusted educational inputs only.")
    def checkpoint(row, rows, evidence):
        print(f"{row['case_id']}: original failed={row['original_tests_failed']}; AI={row['ai_status']}; fix={row['ai_fix_successful']}")
        # Append-only timestamped snapshots preserve completed attempts if a later run stops.
        export_results(rows, evidence, args.output / "checkpoints")
    rows, evidence = evaluate(cases, args.model, provider, args.baseline_only, annotations,
                              args.test_timeout, checkpoint)
    csv_path, json_path = export_results(rows, evidence, args.output)
    print(f"CSV: {csv_path}\nJSON: {json_path}\nExternal API cost: $0")
    print("Review ai_detected_intended_bug separately; heuristic matches are not detection accuracy.")


if __name__ == "__main__":
    main()
