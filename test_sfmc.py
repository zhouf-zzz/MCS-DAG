import unittest

from SFMC import map_task, map_taskset


class _PaperExampleTask:
    """Paper example task for SFMC formula validation."""

    def __init__(self):
        self.id = 1
        self.cri = 0  # HI
        self.C_N = 6
        self.C_O = 16
        self.L_N = 3
        self.L_O = 7
        self.D_vir = 5
        self.D = 13


class TestSFMCPaperExample(unittest.TestCase):
    def test_paper_example_speeds_and_mccts(self):
        task = _PaperExampleTask()
        result = map_task(task, m=4, strict=True)

        self.assertAlmostEqual(result["S_N"], 1.5, places=9)
        self.assertAlmostEqual(result["S_O"], 1.5, places=9)

        self.assertEqual(
            result["normal_mccts"],
            [{"delta": 1.0, "state": "NS"}, {"delta": 0.5, "state": "NS"}],
        )
        self.assertEqual(
            result["critical_mccts"],
            [{"delta": 1.0, "state": "CS"}, {"delta": 0.5, "state": "CS"}],
        )


class _SimpleTask:
    def __init__(self, tid, cri, C_N, C_O, L_N, L_O, D_vir, D):
        self.id = tid
        self.cri = cri
        self.C_N = C_N
        self.C_O = C_O
        self.L_N = L_N
        self.L_O = L_O
        self.D_vir = D_vir
        self.D = D


class TestSFMCMapTaskset(unittest.TestCase):
    def test_separate_ns_cs_feasibility(self):
        # Task 1: paper HI example => S_N=1.5, S_O=1.5
        t1 = _SimpleTask(1, 0, 6, 16, 3, 7, 5, 13)
        # Task 2: LO example => S_N=0.4, S_O=0.0
        t2 = _SimpleTask(2, 1, 4, 4, 1, 1, 5, 10)

        result = map_taskset([t1, t2], m=3, strict=True)

        self.assertAlmostEqual(result["total_SN"], 1.9, places=9)
        self.assertAlmostEqual(result["total_SO"], 1.5, places=9)
        self.assertTrue(result["feasible_ns"])
        self.assertTrue(result["feasible_cs"])
        self.assertTrue(result["feasible"])


if __name__ == "__main__":
    unittest.main()
