"""Run the offline fake-mode triage demonstration."""

from .contracts import Ticket
from .core import CoreTriageRunner
from .fakes import FakeLLMClient


def main() -> None:
    ticket = Ticket("demo-001", "Duplicate charge", "I was charged twice for my monthly plan.")
    result = CoreTriageRunner().run(ticket, llm=FakeLLMClient())
    print(f"Ticket: {ticket.id} - {ticket.subject}")
    print(f"Action: {result.decision.action} ({result.stop_reason})")
    print(f"Response: {result.decision.response}")
    print(f"Steps: {len(result.trace)}; tokens/cost: PENDING (fake mode)")


if __name__ == "__main__":
    main()
