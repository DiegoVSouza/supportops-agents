# Security boundaries

- Fixtures and golden cases use synthetic tickets only; do not place customer data in test fixtures.
- Ticket subject and description are untrusted input. They are passed as data to the injected worker client; no worker output is interpreted as executable code or tool instructions.
- The project exposes no HTTP server, network tools, MCP servers, outbound messaging, or irreversible action tools.
- The live Core boundary rejects provider-supplied `tool_calls` before any tool executor exists. The four-step Core ceiling is enforced before work starts; uncertain or denied calls stop the workflow and cannot be replayed. Do not add KB/billing connectors until a P01-owned source and read-only authorization/provenance contract are specified.
- The fake client is the default. The framework dependency group does not configure provider credentials or initiate model requests.
- LangGraph HITL is required for refunds above USD 100. The runner returns an escalation when approval is denied; it has no refund execution tool.
- Keep `.env`, API keys, local databases, virtual environments, and caches out of Git; `.gitignore` covers secret files and generated environments.
- Verification: unit and integration tests assert escalation and bounded termination; Git hook/ignore checks are saved in `artifacts/evidence/git-setup.md`.
