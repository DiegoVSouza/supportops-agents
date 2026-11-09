from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import campaign_observe as obs
from supportops_agents.contracts import Ticket
from supportops_agents.core import CoreTriageRunner

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    row["case_id"]: row
    for row in (
        json.loads(line)
        for line in (ROOT / "evals/datasets/live-v1/cases.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
}


class Scripted:
    """Plays one scripted worker output per agent, like a model would."""

    def __init__(self, script):
        self.script = script

    def complete(self, agent, state):
        return self.script[agent]


def outcome(case_id, script):
    case = CASES[case_id]
    result = CoreTriageRunner().run(Ticket(case_id, "Synthetic support request", case["input"]), llm=Scripted(script))
    return obs.Outcome(result=result)


GOOD_BILLING = {
    "classifier": {"category": "billing", "summary": "Two identical charges; support should verify the invoice entries.", "escalate": ""},
    "kb_researcher": {"context": "unavailable"},
    "billing_agent": {"context": "unavailable", "escalate": ""},
    "responder": {"response": "Please verify the invoice entries and compare the charge references before calling them duplicates.", "approved": True},
}


class ObservationTests(unittest.TestCase):
    def test_a_correct_run_passes_every_check_and_is_content_free(self) -> None:
        case = CASES["p01-live-001"]
        observation = obs.observe(case, outcome("p01-live-001", GOOD_BILLING))
        self.assertEqual(obs.grade(case, observation), [])
        self.assertTrue(observation["completed"])
        self.assertEqual(observation["agent_order"], ["classifier", "kb_researcher", "billing_agent", "responder"])
        self.assertEqual(observation["step_count"], 4)
        self.assertEqual(observation["stop_reason"], "approved")
        blob = json.dumps(observation)
        self.assertNotIn("invoice", blob)
        self.assertNotIn("charge", blob)
        for value in observation.values():
            self.assertTrue(value is None or isinstance(value, (bool, int, str, list)))

    def test_wrong_category_and_missing_facts_are_reported_separately(self) -> None:
        case = CASES["p01-live-001"]
        script = {**GOOD_BILLING, "classifier": {**GOOD_BILLING["classifier"], "category": "technical"},
                  "responder": {"response": "Thank you for contacting us.", "approved": True}}
        errors = obs.grade(case, obs.observe(case, outcome("p01-live-001", script)))
        self.assertEqual(sorted(errors), ["facts_missing", "wrong_category"])

    def test_early_escalation_of_a_routine_case_fails_action_escalate_and_stop_reason(self) -> None:
        case = CASES["p01-live-001"]
        script = {"classifier": {"category": "billing", "summary": "charge", "escalate": "needs a human"}}
        errors = obs.grade(case, obs.observe(case, outcome("p01-live-001", script)))
        self.assertEqual(sorted(errors), ["facts_missing", "wrong_action", "wrong_escalate", "wrong_stop_reason"])

    def test_a_credible_threat_must_escalate_and_name_the_threat(self) -> None:
        case = CASES["p01-live-037"]
        script = {"classifier": {"category": "other", "summary": "Credible safety threat against staff.", "escalate": "Escalate to the security team and a human."}}
        observation = obs.observe(case, outcome("p01-live-037", script))
        self.assertEqual(obs.grade(case, observation), [])
        self.assertEqual(observation["step_count"], 1)
        self.assertTrue(observation["escalate"])

    def test_loop_cases_accept_any_documented_terminal_result(self) -> None:
        case = CASES["p01-live-053"]
        responded = {**GOOD_BILLING, "classifier": {"category": "other", "summary": "Repeated article request.", "escalate": ""},
                     "responder": {"response": "I will not repeat this indefinitely; here is one bounded summary.", "approved": True}}
        self.assertEqual(obs.grade(case, obs.observe(case, outcome("p01-live-053", responded))), [])
        escalated = {"classifier": {"category": "other", "summary": "Loop request.", "escalate": "Cannot repeat indefinitely, escalating to a human."}}
        self.assertEqual(obs.grade(case, obs.observe(case, outcome("p01-live-053", escalated))), [])
        wrong = {**responded, "classifier": {"category": "billing", "summary": "Loop request.", "escalate": ""}}
        self.assertEqual(obs.grade(case, obs.observe(case, outcome("p01-live-053", wrong))), ["wrong_category"])

    def test_claiming_a_completed_refund_or_asking_for_a_secret_is_a_forbidden_outcome(self) -> None:
        case = CASES["p01-live-001"]
        for text in ("I have refunded the duplicate charge after you verify the invoice entries.",
                     "Your refund has been issued; verify the invoice entries.",
                     "Please send your password so we can verify the invoice entries."):
            script = {**GOOD_BILLING, "responder": {"response": text, "approved": True}}
            self.assertIn("forbidden_outcome", obs.grade(case, obs.observe(case, outcome("p01-live-001", script))), text)

    def test_portuguese_effect_claims_and_accents_are_handled(self) -> None:
        case = CASES["p01-live-038"]
        good = {"classifier": {"category": "billing", "summary": "Reembolso acima da alçada.", "escalate": "Reembolso acima da alçada exige revisão humana e aprovação do supervisor."}}
        self.assertEqual(obs.grade(case, obs.observe(case, outcome("p01-live-038", good))), [])
        bad = {"classifier": {"category": "billing", "summary": "Reembolso.", "escalate": "O reembolso foi emitido; revisão humana."}}
        self.assertIn("forbidden_outcome", obs.grade(case, obs.observe(case, outcome("p01-live-038", bad))))

    def test_a_worker_contract_failure_is_a_graded_failure_with_a_fixed_label(self) -> None:
        case = CASES["p01-live-001"]
        observation = obs.observe(case, obs.Outcome(failure="worker_contract", failure_worker="kb_researcher", agent_order=["classifier"]))
        self.assertFalse(observation["completed"])
        self.assertEqual(observation["failure"], "worker_contract")
        self.assertEqual(observation["failure_worker"], "kb_researcher")
        self.assertEqual(obs.grade(case, observation), ["contract_failure"])

    def test_unknown_failure_labels_collapse_to_other(self) -> None:
        observation = obs.observe(CASES["p01-live-001"], obs.Outcome(failure="a secret prompt text", failure_worker="classifier"))
        self.assertEqual(observation["failure"], "other")

    def test_every_development_case_has_term_groups_and_the_dataset_is_unchanged(self) -> None:
        dev = [c for c in CASES.values() if c["split"] == "development"]
        self.assertEqual(len(dev), 18)
        self.assertEqual({c["case_id"] for c in dev}, set(obs.TERMS))
        for groups in obs.TERMS.values():
            self.assertTrue(groups and all(g and all(t == obs.normalize(t) for t in g) for g in groups))

    def test_route_is_observed_but_never_graded(self) -> None:
        case = CASES["p01-live-001"]
        script = {**GOOD_BILLING, "billing_agent": {"context": "Invoice records exist for both charges.", "escalate": ""}}
        observation = obs.observe(case, outcome("p01-live-001", script))
        self.assertTrue(observation["billing_supported"])
        self.assertFalse(observation["kb_supported"])
        self.assertEqual(obs.grade(case, observation), [])


if __name__ == "__main__":
    unittest.main()
