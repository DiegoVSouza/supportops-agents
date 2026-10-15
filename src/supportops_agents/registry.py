"""Stable runner lookup, with no fake framework implementations."""

from importlib import import_module

from .core import CoreTriageRunner

RUNNER_NAMES = ("core", "langgraph", "crewai", "autogen", "semantic_kernel", "llamaindex")


class RunnerUnavailable(RuntimeError):
    pass


def get_runner(name: str):
    if name not in RUNNER_NAMES:
        raise ValueError(f"unknown runner {name!r}; choose from {', '.join(RUNNER_NAMES)}")
    if name == "core":
        return CoreTriageRunner()
    adapters = {
        "langgraph": ("supportops_agents.frameworks.langgraph_runner", "LangGraphTriageRunner"),
        "crewai": ("supportops_agents.frameworks.crewai_runner", "CrewAITriageRunner"),
        "autogen": ("supportops_agents.frameworks.autogen_runner", "AutoGenTriageRunner"),
        "semantic_kernel": ("supportops_agents.frameworks.semantic_kernel_runner", "SemanticKernelTriageRunner"),
        "llamaindex": ("supportops_agents.frameworks.llamaindex_runner", "LlamaIndexTriageRunner"),
    }
    module_name, class_name = adapters[name]
    try:
        adapter = getattr(import_module(module_name), class_name)
    except ImportError as error:
        raise RunnerUnavailable(f"{name} adapter is INCOMPLETE: sync the 'frameworks' dependency group") from error
    return adapter()
