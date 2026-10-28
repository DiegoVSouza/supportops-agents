# Synthetic bounded read dispatch

Implement a P01-owned local dispatch boundary for synthetic read-only adapters, with validated tool plans, trusted caller context, durable reservation and receipts, and fail-closed restart behavior for unknown work. This is fixture-only infrastructure and does not authorize actual sources, live dispatch, customer data or effects. The existing Core and provider tool rejection remain unchanged.
