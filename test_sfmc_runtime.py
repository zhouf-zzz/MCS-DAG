import unittest

from sfmc_runtime import (
    SFMCRuntimeSimulator,
    build_mapped_task_from_project_task,
    make_chain_task,
)


class TestSFMCRuntimeSimulator(unittest.TestCase):
    def test_schedulable_chain_without_switch(self):
        mt = make_chain_task(
            task_id="tau_ok",
            crit="HI",
            period=10.0,
            deadline=10.0,
            virtual_deadline=6.0,
            wcets_n=[1.0, 1.0],
            wcets_o=[1.0, 1.0],
            normal_deltas=[1.0],
            critical_deltas=[1.0],
        )
        result = SFMCRuntimeSimulator([mt], m=1, debug=False).run(horizon=20.0)
        self.assertTrue(result.schedulable)
        self.assertIsNone(result.state_switch_time)

    def test_switch_and_deadline_miss_detected(self):
        mt = make_chain_task(
            task_id="tau_hi",
            crit="HI",
            period=13.0,
            deadline=13.0,
            virtual_deadline=5.0,
            wcets_n=[2.0, 2.0, 2.0],
            wcets_o=[3.0, 6.0, 7.0],
            normal_deltas=[1.0, 0.5],
            critical_deltas=[1.0, 0.5],
        )
        result = SFMCRuntimeSimulator([mt], m=2, debug=False).run(horizon=26.0)
        self.assertFalse(result.schedulable)
        self.assertIsNotNone(result.state_switch_time)
        self.assertIn("missed real deadline", result.reason)

    def test_project_schema_adapter(self):
        class Node:
            def __init__(self, node_id, eLO, eHI, preds, succs):
                self.node_id = node_id
                self.eLO = eLO
                self.eHI = eHI
                self.predecessors = set(preds)
                self.successors = set(succs)

        class InternalDag:
            def __init__(self, nodes):
                self.nodes = nodes

        class ProjectTask:
            id = 99
            cri = 0
            pLO = 10.0
            dLO = 10.0
            D_vir = 6.0

            def __init__(self):
                self.internal_dag = InternalDag(
                    {
                        0: Node(0, 1.0, 1.5, [], [1]),
                        1: Node(1, 1.0, 1.0, [0], []),
                    }
                )

        mapped = {
            "task_id": 99,
            "S_N": 0.5,
            "S_O": 0.5,
            "normal_mccts": [{"delta": 0.5, "state": "NS"}],
            "critical_mccts": [{"delta": 0.5, "state": "CS"}],
        }
        mt = build_mapped_task_from_project_task(ProjectTask(), mapped)
        self.assertEqual(mt.task.task_id, "99")
        self.assertEqual(mt.task.crit, "HI")
        self.assertEqual(len(mt.task.vertices), 2)
        self.assertAlmostEqual(mt.S_N, 0.5)
        self.assertAlmostEqual(mt.S_O, 0.5)


if __name__ == "__main__":
    unittest.main()
