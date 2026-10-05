"""Load demo inputs from the same controlled dataset used for evaluation."""

import json
from pathlib import Path

CASES_DIR = Path(__file__).resolve().parent.parent / "evaluation" / "cases"
DEMO_TITLES = {"01-off-by-one": "Off-by-One Average", "02-comparison": "Incorrect Boundary Comparison",
               "05-loop": "Skipped First List Value", "07-boolean": "Impossible Weekend Condition"}


def load_cases(root: Path = CASES_DIR) -> list[dict]:
    cases = []
    for manifest in sorted(root.glob("*/case.json")):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["demo_title"] = DEMO_TITLES.get(data["id"], data["title"])
        data["description"] = data.get("description", data["expected_behavior"])
        folder = manifest.parent
        data.update(source=(folder / "buggy.py").read_text(encoding="utf-8"),
                    tests=(folder / "test_case.py").read_text(encoding="utf-8"),
                    reference=(folder / "reference.py").read_text(encoding="utf-8"))
        cases.append(data)
    return cases
