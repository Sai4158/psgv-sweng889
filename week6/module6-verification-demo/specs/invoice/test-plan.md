# Invoice Processing Test Plan

## Purpose

This plan maps the acceptance criteria in `requirements.md` to proposed automated tests. Expected results come from the requirements rather than from the current implementation in `src/invoice.py`.

## Proposed Tests

### AC1: Create Invoice for Existing Customer

#### `test_ac1_creates_invoice_for_existing_customer`

1. **Acceptance criterion:** AC1
2. **Condition being tested:** An existing customer is selected and valid invoice lines are supplied.
3. **Expected result:** The system creates an invoice for the selected customer.

### AC2: Reject Missing Customer

#### `test_ac2_rejects_missing_customer_with_clear_error`

1. **Acceptance criterion:** AC2
2. **Condition being tested:** The requested customer does not exist in the customer collection.
3. **Expected result:** The system rejects invoice creation and provides a clear error indicating that the customer does not exist.

### AC3: Reject Invalid Quantity

#### `test_ac3_rejects_zero_quantity_with_clear_error`

1. **Acceptance criterion:** AC3
2. **Condition being tested:** An invoice line has a quantity of zero.
3. **Expected result:** The system rejects invoice creation and provides a clear error indicating that the quantity is invalid.

#### `test_ac3_rejects_negative_quantity_with_clear_error`

1. **Acceptance criterion:** AC3
2. **Condition being tested:** An invoice line has a quantity less than zero.
3. **Expected result:** The system rejects invoice creation and provides a clear error indicating that the quantity is invalid.

### AC4: Reject Invalid Unit Price

#### `test_ac4_rejects_negative_unit_price_with_clear_error`

1. **Acceptance criterion:** AC4
2. **Condition being tested:** An invoice line has a unit price less than zero.
3. **Expected result:** The system rejects invoice creation and provides a clear error indicating that the unit price is invalid.

### AC5: Calculate Invoice Total

#### `test_ac5_calculates_total_for_single_valid_line`

1. **Acceptance criterion:** AC5
2. **Condition being tested:** A valid invoice contains one line with a unit price of 10.00 and a quantity of 2.
3. **Expected result:** The subtotal is 20.00, the 8 percent tax is 1.60, and the invoice total is 21.60.

#### `test_ac5_calculates_total_for_multiple_valid_lines`

1. **Acceptance criterion:** AC5
2. **Condition being tested:** A valid invoice contains multiple lines with unit prices and quantities.
3. **Expected result:** The invoice total equals the sum of each unit price multiplied by its quantity, plus 8 percent of that subtotal.

## Requirements Traceability

| Acceptance Criterion | Proposed Tests |
|---|---|
| AC1 | `test_ac1_creates_invoice_for_existing_customer` |
| AC2 | `test_ac2_rejects_missing_customer_with_clear_error` |
| AC3 | `test_ac3_rejects_zero_quantity_with_clear_error`; `test_ac3_rejects_negative_quantity_with_clear_error` |
| AC4 | `test_ac4_rejects_negative_unit_price_with_clear_error` |
| AC5 | `test_ac5_calculates_total_for_single_valid_line`; `test_ac5_calculates_total_for_multiple_valid_lines` |

## Open Questions

The requirements do not define the following behavior, so the proposed tests do not invent answers for it:

- What form should a rejection take: an exception, an error result, or another mechanism?
- What exact error type and message qualify as a clear error for AC2, AC3, and AC4?
- Are empty invoices allowed, and if so, should their total be zero?
- Is a unit price of zero valid?
- Are fractional quantities allowed?
- How should missing invoice-line fields, nonnumeric values, or malformed customer records be handled?
- What rounding rule and currency precision should be used for totals that cannot be represented exactly.
- How should duplicate customer IDs be handled?
