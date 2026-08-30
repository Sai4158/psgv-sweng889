from app import clean_text, load_report


def test_load_report(tmp_path):
    report = tmp_path / "sample.txt"
    report.write_text(
        "AI assists software engineering.",
        encoding="utf-8"
    )

    text = load_report(report)

    assert text == "AI assists software engineering."


def test_clean_text_converts_mixed_case_to_lowercase():
    text = "AI Assists SOFTWARE Engineering."

    cleaned_text = clean_text(text)

    assert cleaned_text == "ai assists software engineering."
