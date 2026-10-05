"""Display recorded evidence and collect explicit human review, never inferred accuracy."""
import csv
import io
import json
import pandas as pd
import streamlit as st
from bug_hunter.presentation import readable_time
from evaluation.storage import list_runs, load_reviews, metrics, read_run, save_review


def render_evaluation(presentation=False):
    st.subheader("Evaluation")
    st.caption("Recorded runs only. Test success and human judgement are separate measures.")
    runs = list_runs()
    if not runs:
        st.info("No saved evaluation runs yet.")
        st.code("python -m evaluation.run_evaluation --model qwen2.5-coder:3b", language="bash")
        return
    selected = st.selectbox("Recorded run", runs, format_func=lambda path: path.name)
    try:
        data = read_run(selected)
        reviews, review_issues = load_reviews(selected)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        st.error(f"Saved evidence failed its integrity check: {exc}")
        return
    rows = data["results"]
    summary = metrics(rows, reviews)
    if data.get("limited_evidence"):
        st.warning("CSV-only historical export: raw AI/test evidence is unavailable for this file. No human-review form is offered.")
    for issue in review_issues:
        st.warning("Review file could not be accepted: " + issue)
    st.write("Models: " + ", ".join(sorted({str(row.get("ollama_model", "Unknown")) for row in rows})))
    for cols, fields in [(st.columns(4), [("Cases Recorded", summary["cases"]), ("AI Responses Valid", summary["ai_responded"]),
                            ("AI Fixes Generated", summary["fixes_generated"]), ("AI Fixes Verified", summary["fixes_verified"])]),
                         (st.columns(4), [("Human Reviews", summary["human_reviewed"]),
                            ("Intended Bug: Yes (Reviewed)", summary["intended_bug_yes"] if summary["human_reviewed"] else "Unreviewed"),
                            ("Pylint Functional Flags", summary["pylint_functional_yes"]),
                            ("Average Analysis Time", readable_time(summary["average_seconds"]) if summary["average_seconds"] is not None else "Not run")])]:
        for col, (label, value) in zip(cols, fields):
            col.metric(label, value)
    st.caption(f"{summary['ai_attempted']} AI cases attempted; {summary['ai_responded']} schema-valid responses. "
               "Unreviewed/unclear is not No. Pylint flags use the documented per-case rubric, not a count of style warnings.")
    display_rows = []
    for row in rows:
        display = dict(row)
        record = reviews.get(row["case_id"])
        if record:
            display.update(record["judgement"])
        else:
            legacy_intent = row.get("ai_detected_intended_bug")
            display.update(intended_bug_detected=legacy_intent if legacy_intent in {"Yes", "No"} else "Unreviewed", explanation_correct="Unreviewed",
                           suggested_fix_correct="Unreviewed", false_positive_findings=None, notes="")
        display_rows.append(display)
    frame = pd.DataFrame(display_rows)
    if not frame.empty:
        columns = [name for name in ("case_id", "ai_status", "original_tests_passed", "original_tests_failed",
                   "corrected_tests_passed", "corrected_tests_failed", "corrected_test_status", "ai_fix_successful",
                   "analysis_seconds", "intended_bug_detected", "explanation_correct", "suggested_fix_correct",
                   "false_positive_findings") if name in frame]
        st.dataframe(frame[columns], hide_index=True, width="stretch")
        st.markdown("#### Recorded analysis duration by case")
        if "analysis_seconds" in frame:
            chart = frame[["case_id", "analysis_seconds"]].copy()
            chart["analysis_seconds"] = pd.to_numeric(chart["analysis_seconds"], errors="coerce")
            st.bar_chart(chart.set_index("case_id"), y="analysis_seconds", color="#10796e")
    exports = st.columns(3)
    exports[0].download_button("Export Raw Evidence", selected.read_bytes(), file_name=selected.name,
                              mime="application/json" if selected.suffix == ".json" else "text/csv")
    output = io.StringIO()
    if display_rows:
        names = list(dict.fromkeys(key for row in display_rows for key in row))
        writer = csv.DictWriter(output, fieldnames=names)
        writer.writeheader()
        writer.writerows(display_rows)
    exports[1].download_button("Export Results + Reviews", output.getvalue(), file_name=selected.stem + "-with-reviews.csv", mime="text/csv")
    exports[2].download_button("Export Human Reviews", json.dumps(reviews, indent=2), file_name=selected.stem + "-human-reviews.json", mime="application/json")
    evidence = {item["case"]["id"]: item for item in data.get("evidence", [])}
    reviewable = [key for key, item in evidence.items() if item["report"].get("ai", {}).get("raw_response")]
    if reviewable:
        with st.expander("Human review", expanded=not presentation):
            case_id = st.selectbox("Case to review", reviewable)
            item = evidence[case_id]
            st.write("Expected behavior: " + item["case"]["expected_behavior"])
            left, right = st.columns(2)
            left.code(item["case"]["source"], language="python", line_numbers=True)
            ai = item["report"].get("ai", {})
            analysis = ai.get("analysis")
            if analysis:
                right.code(analysis["corrected_code"], language="python", line_numbers=True)
                st.write(analysis["summary"])
                for finding in analysis["findings"]:
                    st.write(finding)
            else:
                right.warning(ai.get("error") or "Model response was rejected; keep this as failure evidence.")
            with st.expander("Unedited raw response and test evidence"):
                st.code(ai["raw_response"], language="json")
                st.json({"original": item["report"].get("original_tests"), "corrected": item["report"].get("corrected_tests")})
            with st.form("human_review_" + selected.stem + "_" + case_id):
                reviewer = st.text_input("Reviewer name")
                intent = st.selectbox("Intended bug detected", ["Unclear", "Yes", "No"])
                explanation = st.selectbox("Explanation correct", ["Partially", "Yes", "No"])
                suggested_fix = st.selectbox("Suggested fix correct", ["No", "Yes"])
                count = st.number_input("False-positive findings count", min_value=0, max_value=50, step=1)
                notes = st.text_area("Reviewer notes")
                if st.form_submit_button("Save Human Review"):
                    try:
                        saved = save_review(selected, case_id, {"reviewer": reviewer,
                            "intended_bug_detected": intent, "explanation_correct": explanation,
                            "suggested_fix_correct": suggested_fix, "false_positive_findings": int(count), "notes": notes})
                        st.success(f"Saved separately: {saved.name}. Raw run was unchanged.")
                        st.rerun()
                    except (ValueError, OSError) as exc:
                        st.error(str(exc))
    with st.expander("Run an evaluation"):
        st.code("python -m evaluation.run_evaluation --model qwen2.5-coder:3b", language="bash")
