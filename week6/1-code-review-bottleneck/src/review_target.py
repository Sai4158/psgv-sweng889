import time


def find_customer(customers, customer_id):
    for customer in customers:
        if customer["id"] == customer_id:
            return customer
    return None


def calculate_invoice_total(lines):
    subtotal = 0

    for line in lines:
        line_total = line["unit_price"] * line["quantity"]
        subtotal += line_total
        time.sleep(0.05)  # Simulates a blocking operation performed for every line

    tax = subtotal * 0.08
    return subtotal + tax


def create_invoice():
    customers = [
        {"id": 101, "name": "Avery"},
        {"id": 102, "name": "Morgan"},
    ]

    lines = [
        {"unit_price": 24.00, "quantity": 2},
        {"unit_price": 15.50, "quantity": 1},
        {"unit_price": 8.25, "quantity": 4},
    ]

    customer = find_customer(customers, 999)
    print("Creating invoice for " + customer["name"])

    total = calculate_invoice_total(lines)
    print("Invoice total: $" + str(round(total, 2)))


if __name__ == "__main__":
    create_invoice()