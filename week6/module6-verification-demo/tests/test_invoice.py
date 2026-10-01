import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.invoice import create_invoice


class FakeCustomerCollection:
    def __init__(self, customers):
        self.customers = customers

    def find_one(self, query):
        return next(
            (
                customer
                for customer in self.customers
                if customer["customer_id"] == query["customer_id"]
            ),
            None,
        )


CUSTOMERS = FakeCustomerCollection(
    [
        {"customer_id": 101, "name": "Avery"},
        {"customer_id": 102, "name": "Morgan"},
    ]
)


def test_ac1_creates_invoice_for_existing_customer():
    lines = [{"unit_price": 10.00, "quantity": 2}]

    invoice = create_invoice(CUSTOMERS, 101, lines)

    assert invoice is not None
    assert invoice["customer"] == "Avery"


def test_ac2_rejects_missing_customer_with_clear_error():
    lines = [{"unit_price": 10.00, "quantity": 2}]

    with pytest.raises(
        Exception,
        match=r"(?i)customer|not found|does not exist|missing",
    ):
        create_invoice(CUSTOMERS, 999, lines)


def test_ac3_rejects_zero_quantity_with_clear_error():
    lines = [{"unit_price": 10.00, "quantity": 0}]

    with pytest.raises(
        Exception,
        match=r"(?i)quantity|greater than zero|positive",
    ):
        create_invoice(CUSTOMERS, 101, lines)


def test_ac3_rejects_negative_quantity_with_clear_error():
    lines = [{"unit_price": 10.00, "quantity": -1}]

    with pytest.raises(
        Exception,
        match=r"(?i)quantity|greater than zero|positive",
    ):
        create_invoice(CUSTOMERS, 101, lines)


def test_ac4_rejects_negative_unit_price_with_clear_error():
    lines = [{"unit_price": -10.00, "quantity": 2}]

    with pytest.raises(
        Exception,
        match=r"(?i)unit price|price|nonnegative|negative",
    ):
        create_invoice(CUSTOMERS, 101, lines)


def test_ac5_calculates_total_for_single_valid_line():
    lines = [{"unit_price": 10.00, "quantity": 2}]

    invoice = create_invoice(CUSTOMERS, 101, lines)

    assert invoice["total"] == pytest.approx(21.60)


def test_ac5_calculates_total_for_multiple_valid_lines():
    lines = [
        {"unit_price": 24.00, "quantity": 2},
        {"unit_price": 15.50, "quantity": 1},
        {"unit_price": 8.25, "quantity": 4},
    ]

    invoice = create_invoice(CUSTOMERS, 101, lines)

    assert invoice["total"] == pytest.approx(104.22)
