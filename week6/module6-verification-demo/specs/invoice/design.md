# Invoice Processing Design

## Overview

The invoice application creates invoices using customer records stored in a local MongoDB database.

The application retrieves customer data from MongoDB and contains the application logic for invoice creation.

## High Level Architecture

```mermaid
flowchart LR
    User[Billing User]
    App[Invoice Application]
    DB[(MongoDB)]

    User --> App
    App --> DB
    DB --> App
    App --> User
```

### Invoice Application

The Python application is responsible for invoice processing, including customer lookup, invoice line validation, and total calculation.

### MongoDB

A local MongoDB database stores customer records used by the invoice application.

## Customer Data

Customer records are stored in a `customers` collection.

Example document:

```json
{
  "customer_id": 101,
  "name": "Avery"
}
```

The application retrieves a customer using `customer_id`.

## Invoice Creation Flow

```mermaid
sequenceDiagram
    actor User as Billing User
    participant App as Invoice Application
    participant DB as MongoDB

    User->>App: Create invoice
    App->>DB: Find customer by customer ID
    DB-->>App: Customer record
    App->>App: Process invoice
    App-->>User: Invoice result
```
