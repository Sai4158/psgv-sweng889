# Supplier Selection — a simple multi-agent system

A factory needs to buy a component. Two agents and one tool work together to
compare the available suppliers and recommend one.

```
Factory user
  → Buyer Agent                       identifies the criteria, coordinates the work
      → Supplier Analysis Agent       compares the options, recommends one
          → Supplier Information Tool the only source of supplier data
  ← Buyer Agent                       final answer back to the user
```

Everything runs locally: a small LLM in Ollama, plain Python tools, Docker.
No web search, no RAG, no MCP, no external API keys.

---

## Run it

Docker Desktop must be running first.

```
cd psgv-sweng889/week4/2-supplier-agents
docker compose up -d ollama
docker compose run --rm agent-app
```

The first run downloads the model, which takes a few minutes. After that it
starts in a few seconds.

You will see a menu:

```
  1. Run the default factory request
  2. Enter your own factory request
  3. Show the supplier catalogue (tool output only)
  q. Quit
```

Option 1 runs this request:

> The factory needs 400 units within 7 days. Recommend the best supplier and
> explain the decision.

When you are done:

```
docker compose down
```

### Changing the model

The model is set in `docker-compose.yml`:

```
OLLAMA_MODEL=qwen2.5:1.5b
```

Any Ollama-compatible model works — `llama3.2:1b`, `gemma3:1b`, `phi3:mini`.
After changing it, run `docker compose up -d ollama` and then
`docker compose run --rm agent-app` again.

The application never hardcodes the model or its address. Both arrive as
environment variables, so the same code runs against a different model, or a
model on a different machine, without any edit.

---

## What is in the repository

```
2-supplier-agents/
├── app.py                              the menu, and the entry point
├── common.py                           LLM connection and console helpers
├── agents/
│   ├── buyer_agent.py                  Buyer Agent
│   └── supplier_analysis_agent.py      Supplier Analysis Agent
├── tools/
│   └── supplier_tool.py                Supplier Information Tool
├── data/
│   └── suppliers.json                  the supplier catalogue
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

The console prints a banner at each stage. The sequence of banners in one run
is a trace of the interaction between the user, the two agents, and the tool —
useful evidence when you draw your UML sequence diagram.

---

## The starter system is deliberately incomplete

It runs end to end, but it does not reason well yet.

**Record the baseline before you change anything.** Use option 1 to confirm the
system works, then use option 2 to run the two factory requests listed in
Task 1 of the assignment and save the output. You compare against it in Task 4.

Four gaps are marked with `TODO` comments in the code. Each comment explains
what is missing and why it matters.

| | Where | What is missing | Changes the decision? |
|---|---|---|---|
| TODO 1 | `agents/buyer_agent.py` — criteria prompt | Asks for a loose summary, so the next agent has to guess the quantity and the deadline. | Sometimes |
| TODO 2 | `agents/supplier_analysis_agent.py` — analysis prompt | Only says "recommend one supplier". Never names the attributes that matter, or says that quantity and deadline are hard limits. | **Yes** |
| TODO 3 | `agents/buyer_agent.py` — `check_risks()` | Returns nothing, so an impossible recommendation reaches the user unchallenged. | **Yes** |
| TODO 4 | `agents/buyer_agent.py` — `format_response()` | Passes the model's raw text straight through to the user. | No |

Task 3 of the assignment asks for a change that alters what the system
**decides, recommends, or warns about**. TODO 2 and TODO 3 do that on their
own. TODO 1 and TODO 4 improve the system but usually leave the recommendation
unchanged, so combine them with one of the other two.

`find_supplier()` in `tools/supplier_tool.py` returns the structured record for
whichever supplier the agent named, which is what TODO 3 needs.

---

## Lesson 4 Assignment Modification

TODO 2 was completed. Capacity and deadline are hard constraints, and explicit
user priorities such as lowest cost are respected. Supplier information still
comes from the Supplier Information Tool, while LangChain and Ollama remain
part of the workflow. Baseline evidence is in `baseline_outputs.txt`, and
modified evidence is in `modified_outputs.txt`.

### Baseline vs. Modified Results

**Request 1:** "The factory needs 700 units within 6 days. Recommend the best
supplier and explain the decision."

- Baseline: Run 1 - Verinox Supply; Run 2 - Verinox Supply.
- Modified: Run 1 - Verinox Supply; Run 2 - Verinox Supply.

The recommendation stayed the same because Verinox Supply was the only supplier
that satisfied both constraints: capacity 800 >= 700 and delivery 4 <= 6 days.

**Request 2:** "The factory needs 250 units within 5 days at the lowest possible
cost. Recommend the best supplier and explain the decision."

- Baseline: Run 1 - Dalby Metalworks; Run 2 - Verinox Supply.
- Modified: Run 1 - Dalby Metalworks; Run 2 - Dalby Metalworks.

The baseline was inconsistent. The modified system consistently selected Dalby
Metalworks because both Dalby and Verinox were feasible, but Dalby had the lower
price ($3.85 versus $6.40), matching the explicit lowest-cost priority.

The baseline LLM sometimes made incorrect numerical comparisons. The final
system preserves LangChain and Ollama while adding deterministic validation for
hard constraints and supplier facts. The 2,000-unit, 1-day test correctly
returned "No feasible supplier."

---

## Things worth noticing when you run it

Small models are not careful readers. Look for these in your output, because
they are what your reflection is about:

* Does the recommendation satisfy **both** the quantity and the deadline in the
  request? Check it against the catalogue yourself.
* Does an agent ever mention a supplier the tool did not return, or a price or
  delivery time that does not match the data?
* Run the same request two or three times. How much does the answer change?

The answer is not stable across runs or across models. That is a property of
the system you are studying, not a bug in the starter code — and it is worth a
sentence in your reflection.

---

## Troubleshooting

**My code changes do not seem to take effect.**
They should. The project folder is mounted into the container, so editing a
file and re-running `docker compose run --rm agent-app` picks up the change
immediately — no rebuild needed. If nothing changes, check that you saved the
file and that you edited the copy inside `2-supplier-agents/`.

**Docker says a container name is already in use, or a port is allocated.**
A container from another exercise is still running. Find it with `docker ps`,
then stop it with `docker rm -f <name>`, or run `docker compose down` in that
folder.

**It seems to hang after I choose an option.**
The model is thinking. A small model on CPU takes ten to thirty seconds per
agent, and each run calls the model twice.

**It cannot reach Ollama.**
Run `docker compose up -d ollama` first and give it a moment to start, then try
again.
