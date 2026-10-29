# Provider reference, 2026-10-29

- https://console.groq.com/docs/models lists `openai/gpt-oss-20b` and published economic rates USD 0.075 input / USD 0.30 output per million tokens. These are not billed usage.
- https://console.groq.com/docs/rate-limits says limits apply at organization level and actual account limits may differ; the page labels its visible table Developer-plan base limits. Do not infer Free quota or billing from that table. The existing conservative shared policy remains the ceiling.
- https://console.groq.com/docs/reasoning and https://console.groq.com/docs/api-reference document low reasoning effort, disabled returned reasoning, and `max_completion_tokens`. Custom transport behavior is established by its own tests, not the SDK documentation.
