import unittest
from pathlib import Path
import sys

import numpy as np

TEMPLATES_ROOT = Path(__file__).resolve().parents[1]
if str(TEMPLATES_ROOT) not in sys.path:
    sys.path.insert(0, str(TEMPLATES_ROOT))


class VegetationReclassTest(unittest.TestCase):
    def test_reclass_lc_supports_variable_class_counts_with_continuous_codes(self):
        from src.utils import reclass_lc, veg_labels_from_map

        lc = np.array([[1, 2, 3, 4, 5, 6, 7, 8, 9]], dtype=np.int16)
        cases = [
            {"forest": [1, 2], "grassland": [3, 4], "cropland": [5], "wetland": [6]},
            {
                "forest": [1],
                "grassland": [2],
                "cropland": [3],
                "wetland": [4],
                "shrub": [5],
                "barren": [6],
                "urban": [7],
            },
            {"forest": [1], "grassland": [2], "cropland": [3], "wetland": [4], "shrub": [5], "barren": [6]},
        ]

        for veg_map in cases:
            labels = veg_labels_from_map(veg_map)
            out = reclass_lc(lc, veg_map)
            expected_codes = list(range(1, len(labels) + 1))
            self.assertEqual(sorted(np.unique(out[out > 0]).tolist()), expected_codes)
            self.assertEqual(list(labels.keys()), expected_codes)

    def test_non_vegetation_entries_and_unmapped_igbp_are_excluded_from_stats(self):
        from src.utils import by_veg_stats, reclass_lc, veg_labels_from_map

        lc = np.array([[1, 10, 15, 17, 42]], dtype=np.int16)
        veg_map = {
            "forest": [1],
            "grassland": [10],
            "non_veg": [15, 17],
            "custom_type": [42],
        }
        labels = veg_labels_from_map(veg_map)
        reclassed = reclass_lc(lc, veg_map)

        self.assertEqual(reclassed.tolist(), [[1, 2, 0, 0, 3]])
        self.assertEqual(labels, {1: "森林", 2: "草地", 3: "custom_type"})

        class_arr = np.array([[5, 4, 1, 2, 3]], dtype=np.int8)
        levels = {1: "显著退化", 2: "轻微退化", 3: "稳定不变", 4: "轻微改善", 5: "显著改善"}
        stats = by_veg_stats(class_arr, reclassed, levels, labels)

        self.assertEqual(stats["森林"], {"显著改善": 1})
        self.assertEqual(stats["草地"], {"轻微改善": 1})
        self.assertEqual(stats["custom_type"], {"稳定不变": 1})
        self.assertNotIn("non_veg", stats)


if __name__ == "__main__":
    unittest.main()
