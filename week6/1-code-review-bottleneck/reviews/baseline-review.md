# Baseline Code Review

Agent: Codex

Condition: Code review skill unavailable

Prompt: Review @src/review_target.py. Do not modify the file. Report your findings.

## Agent Response

Findings
1. High — Invoice creation always crashes
   [review_target.py (line 35)](C:/Users/saira/Documents/psgv-sweng889/week6/1-code-review-bottleneck/src/review_target.py:35) searches for customer ID 999, which does not exist. find_customer() returns None, then line 36 accesses customer["name"], raising TypeError. This was reproduced by running the script.
2. Medium — Per-line blocking operation scales poorly
   [review_target.py (line 17)](C:/Users/saira/Documents/psgv-sweng889/week6/1-code-review-bottleneck/src/review_target.py:17) blocks for 50 ms for every invoice line. Processing time therefore grows by at least 0.05 × line count seconds and can tie up a worker thread.
3. Medium — Floating-point arithmetic is unsafe for currency
   [review_target.py (line 15)](C:/Users/saira/Documents/psgv-sweng889/week6/1-code-review-bottleneck/src/review_target.py:15) uses binary floating-point values for prices and tax. Some monetary amounts cannot be represented exactly, and rounding only during display does not ensure a correct stored total. Fixed-point decimals or integer cents should be used with an explicit rounding policy.
The file was not modified.