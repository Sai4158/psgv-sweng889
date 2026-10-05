"""Validated AI output and shared result contracts."""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: StrictStr = Field(min_length=1, max_length=300)
    category: StrictStr = Field(min_length=1, max_length=100)
    line: StrictInt | None = Field(ge=1)
    location: StrictStr | None = None
    severity: Literal["Low", "Medium", "High"]
    explanation: StrictStr = Field(min_length=1, max_length=4000)
    why_incorrect: StrictStr = Field(min_length=1, max_length=4000)
    suggested_fix: StrictStr = Field(min_length=1, max_length=4000)


class AIAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    summary: StrictStr = Field(min_length=1, max_length=4000)
    findings: list[Finding] = Field(max_length=50)
    corrected_code: StrictStr = Field(min_length=1, max_length=100_000)


@dataclass
class AIResult:
    status: str
    model: str
    analysis: AIAnalysis | None = None
    error: str | None = None
    raw_response: str = ""
    recovered: bool = False
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    diagnostics: dict = field(default_factory=dict)


@dataclass
class PylintMessage:
    message: str
    category: str
    line: int
    column: int
    symbol: str
    message_id: str


@dataclass
class PylintResult:
    status: str
    messages: list[PylintMessage] = field(default_factory=list)
    score: float | None = None
    error: str | None = None
    output: str = ""


@dataclass
class TestResult:
    __test__ = False

    status: str = "not_run"
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    collected: int = 0
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration: float = 0.0
    message: str = ""

    @property
    def all_passed(self) -> bool:
        return (
            self.status == "passed" and self.exit_code == 0 and self.passed > 0
            and self.failed == 0 and self.errors == 0 and self.skipped == 0
            and self.passed == self.collected
        )


@dataclass
class AnalysisReport:
    source: str
    tests: str
    model: str
    pylint: PylintResult
    ai: AIResult
    original_tests: TestResult
    corrected_tests: TestResult
    duration: float
    fix_verified: bool = False
    comparison: str = ""
    warnings: list[str] = field(default_factory=list)
    stage_seconds: dict[str, float] = field(default_factory=dict)
