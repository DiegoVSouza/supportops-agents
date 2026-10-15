"""Stable runner lookup, with no fake framework implementations."""

from .core import CoreTriageRunner

RUNNER_NAMES = ("core", "langgraph", "crewai", "autogen", "semantic_kernel", "llamaindex")


class RunnerUnavailable(RuntimeError):
    pass


def get_runner(name: str):
    if name not in RUNNER_NAMES:
        raise ValueError(f"unknown runner {name!r}; choose from {', '.join(RUNNER_NAMES)}")
    if name == "core":
        return CoreTriageRunner()
    raise RunnerUnavailable(f"{name} adapter is INCOMPLETE: framework integration is not installed or verified")
