import unittest

from task_set import Drs_gengerate


class TestHiTaskUtilizationOrder(unittest.TestCase):
    def test_hi_tasks_have_uhi_greater_than_ulo(self):
        ts = Drs_gengerate(10, 3.0, 2, 0.5, 8, internal_subtask_enable=False)
        for t in ts.HI:
            self.assertGreater(t.uHI, t.uLO)


if __name__ == "__main__":
    unittest.main()
