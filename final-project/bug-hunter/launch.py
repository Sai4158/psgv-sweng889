"""Portable launcher; missing Ollama is a warning, not a reason to hide the UI."""
import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check setup without starting another server.")
    args = parser.parse_args(argv)
    if sys.version_info < (3, 11):
        print("Bug Hunter needs Python 3.11 or newer.")
        return 1
    missing = [name for name in ("streamlit", "requests", "pydantic", "pylint", "pytest", "pandas")
               if importlib.util.find_spec(name) is None]
    if missing:
        print("Missing dependencies: " + ", ".join(missing))
        print("Install them in your virtual environment: python -m pip install -r requirements.txt")
        return 1
    from bug_hunter.ai.ollama_provider import OllamaProvider
    try:
        models, error = OllamaProvider().list_models()
    except ValueError as exc:
        models, error = [], str(exc)
    print("Python and project dependencies: ready.")
    if error:
        print("Local Ollama warning: " + error)
        print("Start its desktop app / ollama serve; download a model with ollama pull qwen2.5-coder:3b.")
        print("The UI, Pylint, and original tests can still be used offline.")
    else:
        print("Local models: " + ", ".join(models))
    if args.check:
        return 0
    return subprocess.run([sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py")],
                          cwd=ROOT, shell=False, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
