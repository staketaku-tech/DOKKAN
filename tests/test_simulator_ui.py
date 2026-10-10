"""Verify the DEF tab uses the corrected calculation for both timings."""
from pathlib import Path
import unittest

try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None

from damage_core import calculate_damage


@unittest.skipIf(AppTest is None, "Streamlit is not installed")
class SimulatorUITests(unittest.TestCase):
    def test_guard_in_before_and_after_action_results(self):
        app = Path(__file__).resolve().parents[1] / "DOKKAN.py"
        at = AppTest.from_file(str(app), default_timeout=30).run()
        self.assertFalse(at.exception)
        settings = {
            "d_raw": 1998000, "d_ls": 0, "d_link": 0,
            "d_a1": 0, "d_a2": 0, "d_as": 0,
            "d_m1": 0, "d_m2": 0, "d_ms": 0,
            "d_usa": 30, "d_nsa": 0, "d_esa": 0,
            "d_dr_b": 60, "d_dr_a": 60, "d_eatk": 1000,
        }
        for key, value in settings.items():
            at.number_input(key=key).set_value(value)
        at.checkbox(key="d_guard").check()
        at.slider(key="d_npt").set_value(0)
        at.run()
        at.button(key="btn_def").click().run()
        self.assertFalse(at.exception)
        rows = at.session_state["def_results"]
        self.assertEqual(rows[0]["DEF"], 2000000)
        self.assertEqual(rows[0]["被ダメージ"], 600000)
        self.assertEqual(rows[1]["DEF"], 2600000)
        self.assertEqual(rows[1]["被ダメージ"], 300000)
        for row in rows:
            maximum = row["完封可能 敵ATK"]
            self.assertEqual(calculate_damage(row["DEF"], maximum, 60, guard=True), 0)
            self.assertGreater(calculate_damage(row["DEF"], maximum + 1, 60, guard=True), 0)


if __name__ == "__main__":
    unittest.main()
