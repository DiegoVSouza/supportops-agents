# Durable multi-call workflow reservation

The P01 execution guard requires a durable four-call reservation, but the owning ledger currently records exactly one call for every reservation. Support explicit bounded call counts while preserving the one-call default and append-only semantics. No live execution is enabled by this phase.
