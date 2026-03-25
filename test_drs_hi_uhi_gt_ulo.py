import unittest
import importlib.util

HAS_NUMPY = importlib.util.find_spec("numpy") is not None
if HAS_NUMPY:
    from task_set import Drs_gengerate


@unittest.skipUnless(HAS_NUMPY, "requires numpy")
class TestHiTaskUtilizationOrder(unittest.TestCase):
    def test_hi_tasks_have_uhi_greater_than_ulo(self):
        ts = Drs_gengerate(10, 3.0, 2, 0.5, 8, internal_subtask_enable=False)
        for t in ts.HI:
            self.assertGreater(t.uHI, t.uLO)

    def test_generated_taskset_satisfies_sfmc_constraints(self):
        m = 4
        ts = Drs_gengerate(6, 1.8, 2, 0.5, m, internal_subtask_enable=True)
        b = 3.67 * m / (m - 1)

        for t in ts.LO:
            self.assertAlmostEqual(t.D_vir, t.D / (b - 1.0), places=9)
            self.assertLessEqual(t.L_N, t.D_vir)
            self.assertLessEqual(t.sfmc_SN, m)
            if t.cri == 0:
                self.assertLessEqual(t.L_O, t.D - t.D_vir)
                self.assertLessEqual(t.sfmc_SO, m)


if __name__ == "__main__":
    unittest.main()
