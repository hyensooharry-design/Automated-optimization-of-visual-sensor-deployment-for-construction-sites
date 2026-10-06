import contextlib
import io
import sys
import types
import unittest
from pathlib import Path

import numpy as np


sys.modules["output.plotter"] = types.SimpleNamespace(plot_coverage_map=lambda *args, **kwargs: None)
sys.modules["coverage.evaluator"] = types.SimpleNamespace(compute_coverage=lambda *args, **kwargs: set())
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

with contextlib.redirect_stdout(io.StringIO()):
    from algorithm.greedy import fast_valid_ratio_and_score


class FovPrefilterTests(unittest.TestCase):
    def test_out_of_bounds_fov_cells_count_as_outside_area(self):
        sector_masks = {
            0: np.array([
                [0, 0], [1, 0], [2, 0],
                [-1, 0], [-2, 0], [-3, 0], [-4, 0],
                [-5, 0], [-6, 0], [-7, 0],
            ], dtype=np.int32)
        }
        map_mask = np.ones((5, 5), dtype=bool)
        score_mask = map_mask.copy()

        ratio, score = fast_valid_ratio_and_score(
            pos=(0, 2), theta=0, map_mask=map_mask, score_mask=score_mask,
            sector_masks=sector_masks, min_fov_ratio=0.0
        )
        self.assertAlmostEqual(ratio, 0.3)
        self.assertEqual(score, 3)

        filtered_ratio, filtered_score = fast_valid_ratio_and_score(
            pos=(0, 2), theta=0, map_mask=map_mask, score_mask=score_mask,
            sector_masks=sector_masks, min_fov_ratio=0.5
        )
        self.assertEqual((filtered_ratio, filtered_score), (0.0, 0))


if __name__ == "__main__":
    unittest.main()
