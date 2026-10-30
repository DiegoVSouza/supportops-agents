import copy
import json
import unittest
from supportops_agents.accounted_live import (
    AccountedCoreClient, BoundaryError, WorkflowBinding, WORKERS,
    build_payload, input_bound, validate_output, worker_response_format,
)
from test_accounted_core import FixtureGuard


class StrictSchemaTests(unittest.TestCase):
    def test_all_worker_payloads_use_exact_required_native_schemas(self):
        for worker in WORKERS:
            payload=build_payload(worker,{})
            fmt=payload["response_format"]
            self.assertEqual(fmt["type"],"json_schema")
            self.assertTrue(fmt["json_schema"]["strict"])
            schema=fmt["json_schema"]["schema"]
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(set(schema["properties"]),set(schema["required"]))
            self.assertEqual(schema["properties"].get("approved",{}).get("type"),"boolean" if worker=="responder" else None)
            full=len(json.dumps({**payload,"stream":False},ensure_ascii=False,separators=(",",":"),allow_nan=False).encode())
            self.assertEqual(input_bound(payload),full+256+64*2)
        self.assertEqual(worker_response_format("classifier")["json_schema"]["schema"]["properties"]["category"]["enum"],["billing","account_access","technical","shipping","other"])

    def test_schema_weakenings_are_rejected_before_dispatch(self):
        payload=build_payload("kb_researcher",{})
        for field,value in (("strict",False),("name","arbitrary")):
            changed=copy.deepcopy(payload);changed["response_format"]["json_schema"][field]=value
            with self.assertRaises(BoundaryError):input_bound(changed)
        changed=copy.deepcopy(payload);changed["response_format"]["json_schema"]["schema"]["additionalProperties"]=True
        with self.assertRaises(BoundaryError):input_bound(changed)

    def test_local_semantic_and_schema_rejections_remain_strict(self):
        for output in ({},{"context":"","unexpected":"PRIVATE"},{"context":True},{"context":"   "}):
            with self.assertRaises(BoundaryError):validate_output("kb_researcher",output)
        with self.assertRaises(BoundaryError):validate_output("classifier",{"category":"invalid","summary":"ok","escalate":""})

    def test_failure_keeps_receipt_and_private_structural_metadata_without_values(self):
        guard=FixtureGuard()
        client=AccountedCoreClient(guard,WorkflowBinding("fixture-test","case",1))
        client.complete("classifier",{})
        guard.outputs["kb_researcher"]={"context":True,"PRIVATE KEY":"PRIVATE VALUE"}
        with self.assertRaises(BoundaryError) as caught:client.complete("kb_researcher",{})
        diagnostic=caught.exception.diagnostic
        self.assertEqual(diagnostic["structure"]["wrong_type_fields"],["context"])
        self.assertEqual(diagnostic["structure"]["unexpected_field_count"],1)
        self.assertTrue(diagnostic["attempt_id"])
        self.assertNotIn("PRIVATE",str(diagnostic))
        self.assertEqual(len(client.receipts),2)
        with self.assertRaises(BoundaryError):client.complete("kb_researcher",{})
        self.assertEqual(len(guard.requests),2)
