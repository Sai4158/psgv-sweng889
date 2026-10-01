# Skill Assisted Code Review

Agent: Codex

Condition: Code review skill available

Prompt: Review @src/review_target.py. Do not modify the file. Report your findings.

## Agent Response

Findings
1. High — Invoice creation always crashes.
   [review_target.py (line 35)](C:/Users/saira/Documents/psgv-sweng889/week6/1-code-review-bottleneck/src/review_target.py:35) searches for customer ID 999, which is absent. find_customer() returns None, and [line 36 (line 36)](C:/Users/saira/Documents/psgv-sweng889/week6/1-code-review-bottleneck/src/review_target.py:36) subscripts it, raising TypeError. I reproduced this by running the script. Handle a missing customer or use a valid ID.
2. Medium — The per-line blocking delay scales poorly.
   [review_target.py (line 17)](C:/Users/saira/Documents/psgv-sweng889/week6/1-code-review-bottleneck/src/review_target.py:17) blocks for 50 ms for every invoice line. Processing incurs at least 0.05 × line count seconds and can tie up a worker thread. Remove, batch, or replace the per-item blocking operation in production code.
3. Medium — Binary floating-point is unsafe for currency calculations.
   [review_target.py (line 15)](C:/Users/saira/Documents/psgv-sweng889/week6/1-code-review-bottleneck/src/review_target.py:15) calculates prices and tax with float. Some monetary values cannot be represented exactly, and rounding only for display does not guarantee a correct stored total. Use Decimal or integer cents with an explicit rounding policy.
Recommended tests: unknown customer handling, empty invoice, fractional prices/tax rounding, and performance with many lines.
I applied the repository’s code-review checklist. The target file was not modified.