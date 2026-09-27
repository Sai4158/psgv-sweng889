"""Supplier Analysis Agent.

Goal: compare the available suppliers and recommend one.
Tool: the Supplier Information Tool.
It does not talk to the user. It is called by the Buyer Agent.
"""

import re

from common import ask, banner
from tools.supplier_tool import supplier_information

# Assignment modification (completed TODO 2): reject infeasible suppliers before applying user priorities.
ANALYSIS_PROMPT = """You are the Supplier Analysis Agent for a factory.

Criteria identified by the Buyer Agent:
{criteria}

Verified response calculated from the request and tool output:
<verified_response>
{verified_decision}
</verified_response>

Return exactly the text between <verified_response> and </verified_response>.
Do not recalculate, paraphrase, add, remove, or contradict any text.
"""


SUPPLIER_LINE = re.compile(
    r"^- (?P<name>.+?) \| price per unit: \$(?P<price>\d+(?:\.\d+)?) "
    r"\| delivery: (?P<delivery>\d+) days \| reliability: "
    r"(?P<reliability>\d+(?:\.\d+)?) \| capacity: (?P<capacity>\d+) units$"
)

PRIORITY_RULES = (
    (r"lowest (?:possible )?cost|cheapest|lowest[- ]priced", "lowest price per unit", "price", min),
    (r"fastest|shortest delivery", "shortest delivery time", "delivery", min),
    (r"most reliable|highest reliability", "highest reliability", "reliability", max),
    (r"largest capacity|highest capacity", "highest capacity", "capacity", max),
)


def build_verified_decision(request: str, supplier_text: str) -> str:
    """Apply hard constraints and explicit priorities to tool-returned facts."""
    quantity_match = re.search(r"\bneeds?\s+(\d+)\s+units?\b", request, re.I)
    deadline_match = re.search(r"\bwithin\s+(\d+)\s+days?\b", request, re.I)
    if not quantity_match or not deadline_match:
        raise ValueError("The request must state a quantity and deadline in days.")

    quantity = int(quantity_match.group(1))
    deadline = int(deadline_match.group(1))
    suppliers = []
    for line in supplier_text.splitlines():
        match = SUPPLIER_LINE.match(line)
        if match:
            supplier = match.groupdict()
            supplier.update(
                price=float(supplier["price"]),
                delivery=int(supplier["delivery"]),
                reliability=float(supplier["reliability"]),
                capacity=int(supplier["capacity"]),
            )
            suppliers.append(supplier)
    if not suppliers:
        raise ValueError("The Supplier Information Tool returned no suppliers.")

    feasible = []
    review = []
    for supplier in suppliers:
        capacity_ok = supplier["capacity"] >= quantity
        delivery_ok = supplier["delivery"] <= deadline
        if capacity_ok and delivery_ok:
            feasible.append(supplier)
        result = "FEASIBLE" if capacity_ok and delivery_ok else "INFEASIBLE"
        review.append(
            f'- {supplier["name"]}: price ${supplier["price"]:.2f}; delivery '
            f'{supplier["delivery"]} <= {deadline} '
            f'[{"PASS" if delivery_ok else "FAIL"}]; reliability '
            f'{supplier["reliability"]:.2f}; capacity '
            f'{supplier["capacity"]} >= {quantity} '
            f'[{"PASS" if capacity_ok else "FAIL"}]; {result}'
        )

    rule = next(
        (rule for rule in PRIORITY_RULES if re.search(rule[0], request, re.I)),
        None,
    )
    if rule:
        _, priority, attribute, choose = rule
        selected = choose(feasible, key=lambda item: item[attribute]) if feasible else None
    else:
        priority = "none stated; balance all four attributes"
        selected = (
            max(
                feasible,
                key=lambda item: (
                    item["reliability"],
                    -item["delivery"],
                    -item["price"],
                    item["capacity"],
                ),
            )
            if feasible
            else None
        )

    if selected:
        selection = selected["name"]
        reason = (
            f"{selection} passes both hard constraints and is the best feasible "
            f"match for {priority}. The comparison shows all four attributes."
        )
    else:
        selection = "No feasible supplier"
        reason = "Every supplier fails at least one hard constraint."
    return "\n".join(
        [
            f"Requirements: quantity {quantity}; deadline {deadline} days; priority {priority}",
            "Supplier comparison (price; delivery; reliability; capacity):",
            *review,
            f"Recommendation: {selection}",
            f"Reason and trade-offs: {reason}",
        ]
    )


def analyze(llm, request: str, criteria: str) -> str:
    """Reads the supplier catalogue through the tool, then recommends one."""
    banner("Supplier Analysis Agent  ->  Supplier Information Tool")
    suppliers = supplier_information.invoke({})
    print(suppliers)

    banner("Supplier Analysis Agent: recommending")
    verified_decision = build_verified_decision(request, suppliers)
    model_response = ask(
        llm,
        ANALYSIS_PROMPT.format(
            criteria=criteria,
            verified_decision=verified_decision,
        ),
    )
    recommendation = (
        model_response
        if model_response.strip() == verified_decision.strip()
        else verified_decision
    )
    print(recommendation)
    return recommendation
