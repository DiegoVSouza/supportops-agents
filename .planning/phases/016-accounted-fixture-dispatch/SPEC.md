# Accounted Core with fixture-only dispatch

The existing Core accepts its synthetic read dispatcher only with FakeLLMClient, excluding the existing accounted Core client even when its transport is explicitly a fixture. Permit the accounted client with fixture provenance and the same explicit fixture run and tenant; never accept an unverified live transport or real data. Preserve its strict four-worker call budget and all existing dispatch constraints.
