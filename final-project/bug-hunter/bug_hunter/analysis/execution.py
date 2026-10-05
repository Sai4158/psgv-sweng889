"""Replaceable subprocess boundary; a timeout is not a security sandbox."""

import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecutionResult:
    returncode: int | None
    stdout: str
    stderr: str
    duration: float
    timed_out: bool = False


def run_process(args: list[str], cwd: Path, timeout: float) -> ExecutionResult:
    if timeout <= 0:
        raise ValueError("Execution timeout must be positive.")
    # Do not forward project Python paths, pytest plugins, or credential variables.
    allowed = {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "HOME",
               "USERPROFILE", "LANG", "LC_ALL"}
    env = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONIOENCODING="utf-8",
               PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1")
    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    started = time.perf_counter()
    process = subprocess.Popen(
        args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", shell=False, **options,
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        if os.name == "nt":
            try:
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               capture_output=True, timeout=5, check=False, shell=False)
            except (OSError, subprocess.TimeoutExpired):
                process.kill()
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if process.poll() is None:
            process.kill()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.stdout.close()
            process.stderr.close()
            stdout, stderr = "", "Process pipes did not close after termination."
    limit = 100_000
    def truncate(value):
        return value if len(value) <= limit else value[:limit] + "\n[output truncated]"
    return ExecutionResult(process.returncode, truncate(stdout), truncate(stderr),
                           time.perf_counter() - started, timed_out)
