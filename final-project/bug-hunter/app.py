"""Streamlit input/workspace shell; analysis and evidence stay in separate modules."""
import importlib.util
import os
import time
import streamlit as st
from bug_hunter.ai.ollama_provider import FAST_MODEL, OllamaProvider
from bug_hunter.demos import load_cases
from bug_hunter.presentation import recommended_model, render_results, stylesheet
from bug_hunter.services import analyze_code, validate_source

st.set_page_config(page_title="Bug Hunter", page_icon="🐞", layout="wide", menu_items={})


@st.cache_data
def demo_cases():
    return load_cases()


cases = demo_cases()
case_by_id = {case["id"]: case for case in cases}
for key, value in {"source": "", "error_context": "", "test_source": "", "trusted": False,
                   "presentation": False, "performance_mode": "Fast Demo",
                   "ai_timeout": 180, "test_timeout": 10, "context_window": 4096,
                   "output_limit": 1536, "demo_choice": None}.items():
    st.session_state.setdefault(key, value)


def reset_inputs():
    for key in ("source", "error_context", "test_source"):
        st.session_state[key] = ""
    st.session_state.trusted = False
    st.session_state.demo_choice = None
    st.session_state.pop("report", None)


def load_demo():
    selected_id = st.session_state.demo_choice or cases[0]["id"]
    selected = case_by_id[selected_id]
    st.session_state.demo_choice = selected_id
    st.session_state.source = selected["source"]
    st.session_state.test_source = selected["tests"]
    st.session_state.error_context = "Expected behavior: " + selected["expected_behavior"]
    st.session_state.trusted = False
    st.session_state.pop("report", None)


def change_performance():
    installed = st.session_state.get("model_discovery", ([], None))[0]
    st.session_state.selected_model = recommended_model(installed, st.session_state.performance_mode)


with st.sidebar:
    st.radio("Workspace", ["Analyze", "Evaluation"], key="workspace")
    st.checkbox("Presentation Mode", key="presentation", help="Larger type and concise results. Analysis behavior is unchanged.")
    st.header("Runtime")
    configuration_error = None
    try:
        provider = OllamaProvider()
        if ("model_discovery" not in st.session_state
                or time.monotonic() - st.session_state.get("discovery_checked", 0) > 30):
            st.session_state.model_discovery = provider.list_models()
            st.session_state.discovery_checked = time.monotonic()
        installed, connection_error = st.session_state.model_discovery
    except ValueError as exc:
        provider = None
        installed, connection_error = [], str(exc)
        configuration_error = str(exc)
    connected = bool(installed) or bool(connection_error and "Ollama is running" in connection_error)
    system_rows = []
    for label, ready, text in [("Ollama", connected, "Connected" if connected else "Offline"),
                               ("Pylint", importlib.util.find_spec("pylint") is not None, None),
                               ("pytest", importlib.util.find_spec("pytest") is not None, None)]:
        text = text or ("Ready" if ready else "Unavailable")
        system_rows.append(f'<div class="system-row"><span>{label}</span><span class="{"ready" if ready else "offline"}">● {text}</span></div>')
    st.html('<div class="system-status">' + ''.join(system_rows) + '</div>')
    st.subheader("Model")
    st.radio("Performance", ["Fast Demo", "Higher Quality"], key="performance_mode", on_change=change_performance,
             horizontal=True, format_func=lambda value: "Fast" if value == "Fast Demo" else "Quality",
             help="Fast prefers a smaller installed model. Quality prefers the larger 7B model.")
    suggested = recommended_model(installed, st.session_state.performance_mode)
    if "selected_model" not in st.session_state or (installed and st.session_state.selected_model not in installed):
        configured = os.getenv("BUG_HUNTER_MODEL")
        st.session_state.selected_model = configured if configured in installed else suggested
    if installed:
        model = st.selectbox("Ollama model", installed, key="selected_model")
    else:
        model = st.text_input("Ollama model", key="selected_model")
        st.warning(connection_error or "No locally installed model is available.")
        with st.expander("Local setup help", expanded=True):
            st.write("Install Ollama from https://ollama.com/download and start its desktop app or server.")
            st.code("ollama serve\nollama pull qwen2.5-coder:3b", language="bash")
    if st.button("Refresh Models", width="stretch"):
        st.session_state.pop("model_discovery", None)
        st.rerun()
    if st.session_state.performance_mode == "Fast Demo" and FAST_MODEL not in installed:
        with st.expander("Install a faster model"):
            st.code("ollama pull qwen2.5-coder:3b", language="bash")
            st.caption("Run this command manually; no model is downloaded automatically.")
    if not st.session_state.presentation:
        with st.expander("Advanced Settings"):
            st.number_input("AI timeout (seconds)", min_value=10, max_value=600, step=10, key="ai_timeout")
            st.number_input("Test timeout per version (seconds)", min_value=1, max_value=60, key="test_timeout")
            st.number_input("Context window (tokens)", min_value=2048, max_value=32768, step=1024, key="context_window")
            st.number_input("Output token limit", min_value=256, max_value=8192, step=256, key="output_limit")
            st.caption("Inputs are never silently truncated. Longer code may need a larger context/output limit.")

stylesheet(st.session_state.presentation)
st.title("Bug Hunter")
st.html('''<div class="product-intro">
    <p>Python analysis &amp; fix validation</p>
</div>''')

if st.session_state.workspace == "Evaluation":
    from bug_hunter.evaluation_dashboard import render_evaluation
    render_evaluation(st.session_state.presentation)
    st.stop()

with st.container(border=True, key="input_panel"):
    st.subheader("Code review")
    choice, load = st.columns([4, 1], vertical_alignment="bottom")
    with choice:
        st.selectbox("Example", [None] + list(case_by_id), key="demo_choice", on_change=load_demo,
                     placeholder="Select an example",
                     format_func=lambda value: "Choose a demo or paste your own code" if value is None else case_by_id[value]["demo_title"])
    with load:
        st.button("Load Example", on_click=load_demo, width="stretch")
    selected = case_by_id.get(st.session_state.demo_choice)
    if selected:
        st.caption(selected["description"])
    source_col, context_col = st.columns([3, 2])
    with source_col:
        st.text_area("Python Source Code", key="source", height=300, placeholder="Paste Python code…")
    with context_col:
        st.text_area("pytest Tests (optional)", key="test_source", height=175,
                     placeholder="from candidate import add\n\ndef test_add():\n    assert add(2, 3) == 5",
                     help="Import your functions from candidate. The same tests run against original and suggested code.")
        st.text_area("Error / Expected Behavior (optional)", key="error_context", height=90,
                     placeholder="What should happen? Include any error message.")
    st.caption("Only run code you trust. Local test execution is not a security sandbox.")
    st.checkbox("I trust this code and allow local execution.", key="trusted",
                help="Original code, supplied tests, and AI-generated code may execute on your computer. "
                     "This educational POC uses temporary directories and timeouts, not a production security sandbox.")
    _, action_col, reset_col, _ = st.columns([2, 3, 1, 2])
    with action_col:
        analyze = st.button("Analyze Code", type="primary", width="stretch")
    with reset_col:
        st.button("Reset", on_click=reset_inputs, width="stretch")

if analyze:
    try:
        validate_source(st.session_state.source)
        if not st.session_state.trusted:
            st.error("Confirm the trusted-code acknowledgement before analysis or test execution.")
        elif configuration_error:
            st.error(configuration_error)
        else:
            st.session_state.pop("report", None)
            with st.status("Validating code", expanded=True) as status:
                def progress(stage):
                    status.update(label=stage)
                    status.write(stage)
                configured = OllamaProvider(timeout=float(st.session_state.ai_timeout),
                    context_window=int(st.session_state.context_window), output_limit=int(st.session_state.output_limit),
                    known_models=installed if installed else None)
                report = analyze_code(st.session_state.source, st.session_state.error_context,
                    st.session_state.test_source, model, configured, float(st.session_state.test_timeout), progress)
                st.session_state.report = report
                status.update(label="Analysis complete", state="complete", expanded=False)
            if report.ai.status == "unavailable":
                st.session_state.model_discovery = ([], report.ai.error)
                st.session_state.discovery_checked = time.monotonic()
                st.rerun()
    except ValueError as exc:
        st.error(str(exc))
    except Exception as exc:  # UI boundary: preserve usability and show the real failure.
        st.error(f"Analysis could not complete ({type(exc).__name__}): {exc}")

report = st.session_state.get("report")
if report:
    st.divider()
    if (report.source != st.session_state.source or report.tests != st.session_state.test_source or report.model != model):
        st.info("These results belong to previous input/model. Analyze again after editing.")
    render_results(report, st.session_state.presentation)
