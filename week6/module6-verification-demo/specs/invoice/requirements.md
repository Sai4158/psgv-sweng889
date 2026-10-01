# Invoice Processing Requirements

## User Story

As a billing user,
I want to create an invoice for a customer,
so that I can calculate the amount the customer owes.

## Acceptance Criteria

### AC1: Create Invoice for Existing Customer

WHEN an existing customer is selected,
THE SYSTEM SHALL create an invoice for that customer.

### AC2: Reject Missing Customer

IF the requested customer does not exist,
THEN THE SYSTEM SHALL reject invoice creation with a clear error.

### AC3: Reject Invalid Quantity

IF an invoice line has a quantity less than or equal to zero,
THEN THE SYSTEM SHALL reject invoice creation with a clear error.

### AC4: Reject Invalid Unit Price

IF an invoice line has a unit price less than zero,
THEN THE SYSTEM SHALL reject invoice creation with a clear error.

### AC5: Calculate Invoice Total

WHEN an invoice contains valid invoice lines,
THE SYSTEM SHALL calculate the invoice total as the subtotal plus 8 percent tax,
where the subtotal is the sum of unit price multiplied by quantity for all invoice lines.
