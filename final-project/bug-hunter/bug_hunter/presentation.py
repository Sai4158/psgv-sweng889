"""Presentation helpers; all model text is escaped before HTML rendering."""
import html
import re
from dataclasses import asdict
from pathlib import Path
import streamlit as st
from bug_hunter.ai.ollama_provider import DEFAULT_MODEL, FAST_MODEL
from bug_hunter.analysis.diff_utils import source_diff


def readable_time(seconds: float) -> str:
    minutes, remainder = divmod(max(0, round(seconds)), 60)
    return f"{minutes}m {remainder:02d}s" if minutes else f"{remainder}s"


def recommended_model(installed: list[str], mode: str) -> str:
    preferred = [FAST_MODEL, "qwen2.5-coder:1.5b"] if mode == "Fast Demo" else [DEFAULT_MODEL]
    for name in preferred:
        if name in installed:
            return name
    if mode == "Fast Demo":
        for name in installed:
            size = re.search(r":(\d+(?:\.\d+)?)b", name)
            if "coder" in name.lower() and size and float(size[1]) <= 4:
                return name
    return installed[0] if installed else (FAST_MODEL if mode == "Fast Demo" else DEFAULT_MODEL)


def stylesheet(presentation: bool):
    css = (Path(__file__).resolve().parent.parent / "assets" / "style.css").read_text(encoding="utf-8")
    if presentation:
        css += '\n[data-testid="stMain"] {font-size: 18px;} .finding-card p {font-size: 18px;} .validation-value {font-size: 27px;}'
    st.html("<style>" + css + "</style>")


def validation_cards(report):
    for column, title, result in zip(st.columns(2), ["ORIGINAL CODE", "AI-CORRECTED CODE"],
                                     [report.original_tests, report.corrected_tests]):
        state = "pass" if result.all_passed else "fail" if result.failed or result.errors else "neutral"
        icon = "✓" if result.all_passed else "×" if result.failed or result.errors else "—"
        with column:
            st.html(f'<div class="validation-card {state}"><div class="eyebrow">{title}</div>'
                    f'<div class="validation-value">{icon} {result.passed} passed / {result.failed} failed</div>'
                    f'<div class="muted">{html.escape(result.status)} · {result.errors} errors · {result.skipped} skipped</div></div>')
    if report.fix_verified:
        st.success("Fix verified. All supplied, unchanged tests passed on the proposed correction.")
    else:
        st.info("Fix not verified. " + report.comparison)


def render_results(report, presentation: bool):
    analysis = report.ai.analysis
    st.subheader("Analysis Results")
    cols = st.columns(4)
    cols[0].metric("AI Findings", len(analysis.findings) if analysis else "Unavailable")
    cols[1].metric("Pylint Findings", len(report.pylint.messages) if report.pylint.status == "ok" else "Unavailable")
    cols[2].metric("Fix Verified", "Yes" if report.fix_verified else "No")
    cols[3].metric("Analysis Time", readable_time(report.duration))
    overview, findings, lint, fix, validation, technical = st.tabs(
        ["Overview", "AI Findings", "Pylint Baseline", "Suggested Fix", "Test Validation", "Technical Details"])
    with overview:
        if analysis:
            count = len(analysis.findings)
            st.markdown(f"#### AI reported {count} potential {'bug' if count == 1 else 'bugs'}.")
            st.write(analysis.summary)
            if not analysis.findings:
                st.info("No reported findings is not proof that the program is correct.")
        else:
            st.warning(report.ai.error or "Local AI analysis is unavailable.")
        validation_cards(report)
        st.caption("Review the fix before using it. Passing tests cover only the tested cases, not the accuracy of every AI explanation.")
        for warning in report.warnings:
            st.warning(warning)
    with findings:
        if not analysis:
            st.warning(report.ai.error or "No validated model response is available.")
        elif not analysis.findings:
            st.info("The model returned no structured findings. Review test evidence independently.")
        else:
            for finding in analysis.findings:
                location = f"Line {finding.line}" if finding.line else finding.location or "Location unknown"
                parts = '<div class="finding-card"><div class="finding-heading">'
                parts += f'<h3>{html.escape(finding.title)}</h3><span class="badge {finding.severity.lower()}">{finding.severity}</span></div>'
                parts += f'<div class="muted">{html.escape(finding.category)} · {html.escape(location)}</div>'
                for label, value in [("Explanation", finding.explanation), ("Why incorrect", finding.why_incorrect),
                                     ("Suggested fix", finding.suggested_fix)]:
                    parts += f'<p><strong>{label}</strong><br>{html.escape(value)}</p>'
                st.html(parts + '</div>')
    with lint:
        st.caption("Pylint static-analysis results. Style warnings do not establish a functional bug.")
        if report.pylint.status != "ok":
            st.warning(report.pylint.error or "Pylint could not complete.")
        else:
            if report.pylint.score is not None:
                st.metric("Pylint score", f"{report.pylint.score:.2f} / 10")
            if report.pylint.messages:
                st.dataframe([asdict(message) for message in report.pylint.messages], hide_index=True, width="stretch")
            else:
                st.info("No Pylint messages; tests and review are still needed.")
    with fix:
        if analysis:
            st.caption("Review before using. Suggested code never replaces your files automatically.")
            st.code(analysis.corrected_code, language="python", line_numbers=True)
            st.download_button("Download Suggested Fix", analysis.corrected_code, file_name="suggested.py", mime="text/x-python")
            st.markdown("#### Before / after diff")
            diff = source_diff(report.source, analysis.corrected_code)
            if diff:
                lines = []
                for line in diff.splitlines():
                    style = "addition" if line.startswith("+") and not line.startswith("+++") else "removal" if line.startswith("-") and not line.startswith("---") else "diff-context"
                    lines.append(f'<span class="{style}">{html.escape(line)}</span>')
                st.html('<pre class="source-diff" aria-label="Unified source diff">' + '\n'.join(lines) + '</pre>')
            else:
                st.info("No source change was suggested.")
        else:
            st.info("No validated AI correction is available.")
    with validation:
        validation_cards(report)
        for label, result in [("Original code", report.original_tests), ("AI-corrected code", report.corrected_tests)]:
            if result.message:
                st.caption(f"{label}: {result.message}")
            with st.expander(f"{label} — detailed pytest output"):
                st.code(result.stdout + "\n" + result.stderr, language="text")
        st.caption("Temporary directories and timeouts are not a production sandbox.")
    with technical:
        st.write(f"Model: **{report.model}** · Duration: **{readable_time(report.duration)}**")
        with st.expander("Execution timing and model diagnostics"):
            st.json({"stage_seconds": report.stage_seconds, "ollama": report.ai.diagnostics,
                     "prompt_tokens": report.ai.prompt_tokens, "completion_tokens": report.ai.completion_tokens,
                     "ai_status": report.ai.status, "ai_error": report.ai.error})
        with st.expander("Raw model response"):
            st.code(report.ai.raw_response or "No raw model response was returned.", language="json")
        with st.expander("Complete result summary"):
            st.json({"AI bug detected (model report, not human judgement)": bool(analysis.findings) if analysis else None,
                     "original tests": asdict(report.original_tests), "corrected tests": asdict(report.corrected_tests),
                     "fix verified": report.fix_verified, "warnings": report.warnings})
