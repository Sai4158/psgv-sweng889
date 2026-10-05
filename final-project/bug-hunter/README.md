# Bug Hunter

## AI-Assisted Python Bug Detection & Fix Validation

Find functional Python bugs with a local AI model, compare against Pylint, and verify
proposed fixes with pytest. A SWENG 889 group-project proof of concept, not an automatic
code-approval tool.

Analysis runs locally through Ollama, without a hosted AI service or API key.
Local CPU/GPU, memory, disk space, and electricity usage still have costs.

## Quick Start

Run the commands from `final-project/bug-hunter`. Python 3.11+ is required.

1. Install Python from [python.org](https://www.python.org/downloads/). On Windows,
   enable the Python PATH option; `py` may be used instead of `python`.
2. Install the native [Ollama application](https://ollama.com/download) for your OS.
3. Create a project virtual environment and install dependencies:

Windows PowerShell (activation is unnecessary):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

4. Download a local coding model once. The verified
   [Qwen 2.5 Coder 3B package](https://ollama.com/library/qwen2.5-coder:3b) is about 1.9 GB:

```bash
ollama pull qwen2.5-coder:3b
# Optional higher-quality model, about 4.7 GB:
ollama pull qwen2.5-coder:7b
ollama list
```

Downloads are explicit, never automatic. Choose a model that fits your machine.
A smaller model can miss bugs or suggest incorrect fixes.

5. Start the Ollama desktop application, or run `ollama serve` in another terminal.
   Do not start a second server if port 11434 is already in use.
6. Launch Bug Hunter:

Windows:

```powershell
.\run.bat
# Or, if your PowerShell policy allows scripts:
.\run.ps1
# Manual alternative:
.\.venv\Scripts\python.exe -m streamlit run app.py
```

macOS / Linux:

```bash
bash run.sh
# Manual alternative:
.venv/bin/python -m streamlit run app.py
```

Open **http://localhost:8501**. The helpers use the project virtual environment when
present, check Python/dependencies, warn if Ollama is offline, and launch Streamlit.
`python launch.py --check` checks setup without launching.
Internet is needed for initial downloads, not for subsequent local analysis.

### Optional Docker-based Ollama

Docker is **not required** if native Ollama works. To use Docker instead:

```bash
docker run -d --name bug-hunter-ollama -p 127.0.0.1:11434:11434 -v bug-hunter-ollama-data:/root/.ollama ollama/ollama:latest
docker exec bug-hunter-ollama ollama pull qwen2.5-coder:3b
docker exec bug-hunter-ollama ollama pull qwen2.5-coder:7b
```

For an existing stopped container use `docker start bug-hunter-ollama`. Do not run
native Ollama and the container on the same port. The volume keeps downloaded models.
Streamlit, Pylint, and pytest still run in the local Python environment.

### Configuration

Set `OLLAMA_BASE_URL` before startup; it defaults to `http://localhost:11434`:

```powershell
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:BUG_HUNTER_MODEL = "qwen2.5-coder:7b"
.\run.bat
```

```bash
export OLLAMA_BASE_URL=http://localhost:11434
export BUG_HUNTER_MODEL=qwen2.5-coder:7b
bash run.sh
```

The older `BUG_HUNTER_OLLAMA_URL` remains a fallback. Only HTTP loopback addresses are
accepted: no remote/cloud models, external hosts, redirects, credentials, or HTTP proxies.
If Ollama is unavailable, Pylint and original tests still run and the missing guidance
is clearly reported. Click **Refresh Models** after installing a model or restarting Ollama.
Discovery is reused briefly and refreshed on interactions after 30 seconds; failed AI
connections immediately update the offline status. This is not a background uptime monitor.

## Using the application

1. Select an example; source, tests, description, and expected behavior fill automatically.
   **Load Example** reloads it. **Reset** clears inputs, results, selection, and consent.
2. Alternatively paste Python source and optional tests/error context.
   Tests must import functions from `candidate`, not from the app's working directory.
3. Acknowledge trusted-code execution, then **Analyze Code**.
4. Follow the real stages: validation, Pylint, original tests, local AI, parsing,
   proposed-fix validation, and results. There is no invented percent-complete indicator.
5. Inspect Overview, AI Findings, Pylint Baseline, Suggested Fix, Test Validation, and
   Technical Details. Downloading a suggested fix does not replace your source files.

**Fast** prefers an installed `qwen2.5-coder:3b`, then a smaller installed coder.
**Quality** prefers `qwen2.5-coder:7b`. You can override either selection.
Neither mode promises that an answer is correct. Presentation Mode increases readability
and hides advanced settings; it does not change prompts, tests, or results. Raw diagnostics
stay inside collapsed expanders. Deployment/menu chrome is hidden while sidebar controls remain.

The unchanged 12-case dataset includes **Off-by-One Average**, **Skipped First List Value**,
**Incorrect Boundary Comparison**, and **Impossible Weekend Condition**. All demos include
buggy source, tests, expected behavior, and a category. Reference solutions are used only
for dataset control checks, never sent to the model or substituted for its answers.

### What “Fix Verified” means

The original code failed at least one test, the AI changed the source, and **every collected,
unchanged test** passed on that correction, without skips/errors/timeouts.
Already-passing original code, absent tests, zero collected tests, invalid code, or unavailable
AI cannot produce a verified-repair claim. Passing tests do not prove general correctness
or that an explanation is accurate. Human review is required.

Pylint is the independent static-analysis baseline. Style/docstring messages are not
automatically functional-bug detections. It does not generate the AI fix.
The AI is test-guided and sees intent/tests/failure evidence; Pylint inspects source
statically. This is not an identical-information or general accuracy comparison.

## Performance and demo preparation

Normal analysis makes **one** AI generation request, using Ollama's JSON schema output,
temperature 0, 4,096 context tokens, and a 1,536-token output cap. Source is sent once,
with tests, user intent, and a bounded excerpt of **actual original pytest failures**.
No reference answer is supplied. Inputs that may exceed context are rejected clearly
rather than silently cutting source/tests. Full original logs remain in results.

An explicit `keep_alive=30m` reuses the loaded model. Switching models, resource pressure,
or restarting Ollama can still cause a cold load. Longer input/output can need higher
Advanced Settings limits, at the expense of speed. Truncated generation is rejected.
Timing details include actual Ollama load/prompt/generation durations and token counts.

Keep only the current demo model loaded when memory is tight: inspect
`ollama ps` and stop an **idle** model with `ollama stop qwen2.5-coder:7b`
(or the idle 3B model instead). Do not stop an in-progress analysis.

This machine's Docker Ollama reported **100% CPU** for the 7B model. Earlier 53–125-second
analyses included larger/redundant prompts and lengthy generation; reducing download time
alone cannot solve CPU inference latency. Before/after exports preserve the real timings
and unsuccessful optimization trials. Single-run measurements are not a controlled speed
or accuracy guarantee; cold/warm state and changing prompts/model size affect comparisons.

For class: select the model, enable Presentation Mode, rehearse the exact demos, and allow
one warm-up run. Show original-versus-corrected tests, then the diff and Pylint comparison.
Use Evaluation to show recorded evidence without implying a saved run is a live run.
Keep poor responses: they demonstrate why independent tests and human review matter.
See the recorded validation section below for actual run outcomes.

## Evaluation Dashboard and human review

Select **Evaluation** in the sidebar. It reads real timestamped CSV/JSON exports, including
earlier unsuccessful runs and CSV-only history (labeled as limited evidence). Metrics include
cases, schema-valid AI responses, fixes generated, fixes verified, average duration,
Pylint functional flags, and explicit human judgments. Charts/tables use saved observations.

**AI reported a finding is not the same as the intended bug being detected.**
Unreviewed and Unclear are not No. Heuristic title/category/line matching is a review aid,
not accuracy. Pylint flags use each case's curated symbol list plus bug-line overlap;
empty symbol lists do not prove Pylint can never detect the bug.

In **Human Review**, inspect the unedited response, source, expected behavior, proposed
fix, and tests. Record reviewer name and:

- Intended bug detected: Yes / No / Unclear
- Explanation correct: Yes / No / Partially
- Suggested fix correct: Yes / No
- False-positive findings count
- Reviewer notes

Judgments are separate timestamped JSON files in `evaluation/reviews/`, bound to the raw
run and response hashes. Saving a judgment never rewrites the model's response. No human
judgments are filled automatically. Review errors/hash mismatches are shown, not silently ignored.
Buttons export original raw evidence, results plus reviews, or just human judgments.

### Reproduce the evaluation

With the environment's Python (`python` below) run:

```bash
python -m evaluation.run_evaluation --baseline-only
python -m evaluation.run_evaluation --model qwen2.5-coder:3b
python -m evaluation.run_evaluation --model qwen2.5-coder:7b --ai-timeout 240
python -m evaluation.run_evaluation --model qwen2.5-coder:7b --case 01-off-by-one --case 02-comparison --case 07-boolean --ai-timeout 240
```

Use `--case` repeatedly, `--test-timeout 10`, `--context-window 4096`,
`--output-limit 1536`, `--keep-alive 30m`, or `--output PATH` as needed.
Every dataset original must fail and every reference must pass before statistics are exported.
Original/corrected pass, fail, error counts, AI status, raw responses, hashes, model, tokens,
actual duration, and fix outcomes are recorded. Baseline AI values are “not run”, not failures.
`analysis_seconds` includes the reference control; `service_seconds` is normal application time.

Exports and per-case checkpoints are timestamped, append-only under `evaluation/results/`;
new runs never replace earlier evidence. If interrupted, completed cases remain in checkpoints.
Only completed recorded cases are counted. Raw failures and incorrect suggestions remain available.
Generated evidence/reviews are ignored by Git: export or copy them separately when sharing.
Do not claim accuracy until people review the included responses.

The earlier hash-checked Yes/No annotation CLI remains supported:

```bash
python -m evaluation.review_results --results evaluation/results/results-RUN.json --annotations annotations.json
```

Its annotation format is documented by `python -m evaluation.review_results --help` and
`evaluation/review_results.py`. It writes reviewed copies, never overwrites the original.
The dashboard's separate full human-review form is recommended for new runs.

## Architecture and local deployment

```text
User computer
  +-- Streamlit UI
  +-- Ollama local model (native or optional local Docker)
  +-- Pylint static baseline
  +-- pytest before/after validation
```

The standard POC deployment is local, **not Streamlit Community Cloud**. No API key,
database, login, hosted AI, GitHub integration, automatic commits, or additional languages
are needed.

- `app.py`: input, status/progress, model/mode controls.
- `bug_hunter/presentation.py` and `assets/style.css`: result cards, diff, projector styling.
- `bug_hunter/services.py`: orchestration and validation.
- `bug_hunter/ai/ollama_provider.py`: loopback model discovery, one structured AI call,
  response validation, errors, real timing metadata.
- `bug_hunter/analysis/`: original Pylint, unchanged pytest execution, subprocess boundary,
  and cautious comparison/diff.
- `bug_hunter/evaluation_dashboard.py` and `evaluation/storage.py`: real saved observations
  and separately stored human reviews.
- `evaluation/cases/`: original 12 independent controlled cases.
- `evaluation/run_evaluation.py`: repeatable controls, measurements, raw evidence/checkpoints.
- `launch.py`, `run.bat`, `run.ps1`, `run.sh`: portable local launch helpers.

Streamlit configuration uses minimal toolbar mode; narrow CSS hides menu/deploy controls,
not the entire header. Usage-statistics collection is disabled. Ollama's official
[chat API documentation](https://docs.ollama.com/api/chat) describes structured output,
keep-alive, and measured durations.

## Automated checks and safety

```bash
python -m pytest -q
python -m compileall -q app.py launch.py bug_hunter evaluation tests
python -m pip check
```

Project tests mock AI and exercise real Pylint/pytest subprocesses, timeout termination,
malformed/error/offline results, immutable test inputs, dataset controls, UI interactions,
single-generation requests, progress, context limits, and evidence/review integrity.
Evaluation snippets are excluded from direct project-test discovery.

**Educational POC: only run code you trust. Test execution is isolated with timeouts but
is not a production security sandbox.** Acknowledgment is required even without supplied tests.
Original code, tests, and suggested code run with local Python privileges. Temporary directories,
limited environment forwarding, disabled pytest plugin autoload, argument lists without shells,
output bounds, and process-tree timeouts reduce accidents, not malicious behavior. Code can
still access files/network, spawn processes, or tamper with a test observer. No resource,
filesystem, or network security containment is claimed.

The code uses `pathlib`, `sys.executable`, and platform-specific process-tree termination.
macOS/Linux share the POSIX path; actual supported-platform test results must be distinguished
from portable-code inspection. Secrets, private code, and personal data must not be used in
examples or committed as raw exports. Syntax errors are shown before inference. Source/tests
have 50,000-character limits and error context 20,000; the context budget may impose smaller
limits. Functional tests do not evaluate every security, performance, or concurrency concern.

## Recorded validation

Earlier evidence remains unchanged, including the original three-case 7B success run
`evaluation/results/results-20261005T023013283794Z.json` and unsuccessful smaller-model attempts.
Those three fixes passed all nine unchanged tests, but some explanations were contradictory:
human judgments remain Unreviewed, not an AI accuracy claim.

Second-pass results, actual timing comparisons, full-dataset status, unit tests, and OS
verification are recorded in the following final validation notes.

### Second-pass checks (October 5, 2026)

- Windows Python 3.12: **88 passed, 0 failed**. Linux Python 3.11 in a temporary,
  read-only-project Docker container: **88 passed, 0 failed**. macOS was not executed.
- Compilation, dependency consistency, PowerShell/batch setup checks, Linux shell syntax,
  and project-wide whitespace checks passed. Streamlit startup health returned HTTP 200.
- A real browser exercised demo loading, progress, Presentation Mode, results, and the
  saved-evaluation dashboard. Menu/deploy controls are hidden; sidebar controls remain.
- An actual disconnected-endpoint check retained real Pylint results and original tests
  (2 passed / 1 failed) without fabricating AI guidance or claiming a verified fix.
- All nine pre-existing CSV/JSON evidence files remained byte-identical (SHA-256).
  No model output or dataset/reference source was repaired by hand.
- No known credential patterns, source-level machine-specific paths, or nested repositories
  were found. Virtual environments, caches, results, and human reviews remain ignored.

### Measured before / after

The same three original live-demo cases were measured before source changes and after
optimization. Values below are **application analysis seconds**, excluding the evaluation
reference control. Every cell is a real run, not a projected improvement.

| Case | Before: 7B | After: 7B | After: 3B | 3B fix verified? |
| --- | ---: | ---: | ---: | --- |
| Off-by-One Average | 160.94 | 107.54 | 35.16 | No — 2 tests still failed |
| Incorrect Boundary Comparison | 43.87 | 54.75 | 25.54 | Yes — 3/3 passed |
| Impossible Weekend Condition | 43.36 | 67.07 | 33.93 | Yes — 3/3 passed |

All three listed 7B fixes passed their tests. **7B did not get faster consistently**;
3B reduced measured wait time but did not preserve all model-level fix successes.
The independent validator remained strict and correctly rejected the incomplete average fix.
These are single observations with different cold/warm/memory conditions, not statistical
benchmarks. The before run overlapped the explicit model download; part of the 7B run
overlapped automated checks. Do not attribute every difference to prompt optimization.

Exact sources (CSV companions also exist):

- Before: `evaluation/results/results-20261005T034324412824Z.json`
- Final 3B three-case trial: `evaluation/results/results-20261005T040823879233Z.json`
- Full optimized 7B run: `evaluation/results/results-20261005T042255306397Z.json`

The full 7B run attempted/completed **12/12 cases**: 12 schema-valid responses, 12 proposed
source changes, and **12 pytest-verified fixes** (31 unchanged tests passed). Mean evaluation
case time was **69.85 seconds**, including the reference control. Pylint raised the intended
functional symbol on **1/12** under the existing dataset rubric, not a universal detection score.
All human intended-bug/explanation judgments remain **Unreviewed**. In the average case, for
example, the explanation described a changed divisor even though the actual bug was a loop
boundary. Passing corrected tests did not make that explanation correct.

The first shortened-prompt trial emitted invalid line-numbered Python; the subsequent small
model trial also missed cases. Both timestamped raw runs are retained. The final prompt uses
plain source and real original failures; it never substitutes a reference fix or retries until
success. For live class use, rehearse the chosen model/cases and allow CPU waiting time.

Two additional real browser runs of the 3B boundary demo verified the fix: the cold run
displayed **1m 28s**, with **28.515 seconds model loading**; the immediately repeated warm
run displayed **51s**, with **0.004 seconds model loading**. Generation still took
26.400/31.023 seconds respectively. The warm response explained the boundary correctly;
the cold response incorrectly discussed `is` versus `==`, despite passing corrected tests.
These unedited browser observations are retained in `evaluation/results/smoke/ui-cold-3b.json`
and `ui-warm-3b.json` and are labeled as UI captures, not reconstructed API exports.

Readiness: the local POC is usable for a **rehearsed, human-reviewed classroom demo**.
It is not consistently an instant-response demo on this CPU. Prepare the model in advance,
close unnecessary applications when memory is tight, and show saved runs explicitly as
recorded evidence if live inference is too slow. Finish human judgments before claiming
intended-bug detection or explanation accuracy. No commits or pushes were made by this pass.
