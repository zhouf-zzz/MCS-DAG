import unittest

from sfmc_random_validation import prepare_task_for_sfmc, validate_random_tasksets


class TestSFMCRandomValidationHelpers(unittest.TestCase):
    def test_prepare_task_for_sfmc(self):
        class Node:
            def __init__(self, eLO, eHI, preds, succs):
                self.eLO = eLO
                self.eHI = eHI
                self.predecessors = set(preds)
                self.successors = set(succs)

        class Dag:
            def __init__(self):
                self.nodes = {
                    0: Node(1.0, 2.0, [], [1]),
                    1: Node(2.0, 3.0, [0], []),
                }

        class Task:
            id = 1
            cri = 0
            dLO = 10.0

            def __init__(self):
                self.internal_dag = Dag()

        t = Task()
        prepare_task_for_sfmc(t, d_vir_ratio=0.5)

        self.assertAlmostEqual(t.C_N, 3.0)
        self.assertAlmostEqual(t.C_O, 5.0)
        self.assertAlmostEqual(t.L_N, 3.0)
        self.assertAlmostEqual(t.L_O, 5.0)
        self.assertAlmostEqual(t.D_vir, 5.0)

    def test_validate_counts_only_legal_tasksets(self):
        summary = validate_random_tasksets(
            task_number=4,
            node_number=6,
            cycles=1,
            uti_start=0.2,
            uti_step=0.1,
            uti_points=1,
            run_runtime=False,
        )
        self.assertEqual(len(summary["generation_attempts"]), 1)
        self.assertGreaterEqual(summary["generation_attempts"][0], 1)
        self.assertGreaterEqual(summary["mapping_success_ratio"][0], 0.0)
        self.assertLessEqual(summary["mapping_success_ratio"][0], 1.0)


if __name__ == "__main__":
    unittest.main()
