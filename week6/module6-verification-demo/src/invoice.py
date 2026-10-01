import time

def find_customer(customers, customer_id):
    for customer in customers:
        if customer["id"] == customer_id:
            return customer
    return None

def calculate_invoice_total(lines):
    subtotal = 0
    for line in lines:
        if line["quantity"] <= 0:
            raise ValueError("Quantity must be greater than zero")
        if line["unit_price"] < 0:
            raise ValueError("Unit price cannot be negative")
        line_total = line["unit_price"] * line["quantity"]
        subtotal += line_total
        time.sleep(0.05)
    tax = subtotal * 0.08
    return subtotal + tax

def create_invoice(customers, customer_id, lines):
    customer = find_customer(customers, customer_id)
    if customer is None:
        raise ValueError("Customer does not exist")
    invoice = {
        "customer": customer["name"],
        "total": calculate_invoice_total(lines),
    }
    return invoice

if __name__ == "__main__":
    customers = [
        {"id": 101, "name": "Avery"},
        {"id": 102, "name": "Morgan"},
    ]
    lines = [
        {"unit_price": 24.00, "quantity": 2},
        {"unit_price": 15.50, "quantity": 1},
        {"unit_price": 8.25, "quantity": 4},
    ]
    invoice = create_invoice(customers, 999, lines)
    print(invoice)
