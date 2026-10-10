import unittest
from damage_core import calculate_dokkan_def, calculate_damage, damage_details, max_enemy_atk, reverse_enemy_atk, ratio_def, timeline

class DamageTests(unittest.TestCase):
    def test_original_def_preserved(self):
        self.assertEqual(calculate_dokkan_def(10000, 440, 0, 200, 0, 0, 100, 25, 80), 729000)

    def test_reported_case_guard(self):
        final = ratio_def(580165, {"add": 520}, {"add": 570, "mult": 600, "sa": 30})
        self.assertEqual(final, 5705263)
        detail = damage_details(final, 19500000, 65, guard=True)
        self.assertEqual(detail["attack_before_def"], 5460000)
        self.assertEqual(detail["damage"], 0)

    def test_reported_support_in_multiplicative_group(self):
        final = ratio_def(580165, {"add": 520}, {"add": 520, "mult": 650, "sa": 30})
        self.assertEqual(final, 5656608)
        self.assertEqual(calculate_damage(final, 19500000, 65, guard=True), 0)

    def test_guard_before_def_known_case(self):
        self.assertEqual(calculate_damage(2000000, 10000000, 60, guard=True), 600000)

    def test_guard_overrides_type(self):
        for multiplier in [.9, 1., 1.15, 1.25, 1.5]:
            self.assertEqual(calculate_damage(2000000, 10000000, 60, type_multi=multiplier, guard=True), 600000)

    def test_no_guard_type_before_def(self):
        self.assertEqual(calculate_damage(100000, 1000000, 0, type_multi=1.5), 1400000)

    def test_advantage_halves_after_def(self):
        self.assertEqual(calculate_damage(100000, 1000000, 0, type_multi=.9, advantageous=True), 400000)

    def test_no_new_effect_no_float_loss(self):
        self.assertEqual(ratio_def(100828, {"add": 30}, {"add": 30}), 100828)

    def test_same_group_does_not_multiply_twice(self):
        self.assertEqual(ratio_def(250000, {"mult": 100}, {"mult": 200}), 375000)

    def test_simulator_basis_agrees(self):
        events = [{"順番": 1, "タイミング": "超必殺", "補正先": "必殺技効果・味方の必殺支援", "変化量(%)": 50}, {"順番": 2, "タイミング": "通常必殺", "補正先": "必殺技効果・味方の必殺支援", "変化量(%)": 30}]
        results = timeline(0, {"add": 200, "mult": 100, "link": 25}, events, 1500000, 0, basis=(10000, 440))
        self.assertEqual([r["被弾時DEF"] for r in results], [405000, 607500, 729000])

    def test_support_only_after_activation(self):
        events=[{"順番": 1, "タイミング": "被弾後の支援", "補正先": "掛け算パッシブ", "変化量(%)": 50}]
        results=timeline(580165, {"add": 520, "sa": 30}, events, 19500000, 65, receiving=600, guard=True)
        self.assertGreater(results[1]["被弾時DEF"], results[0]["被弾時DEF"])
        self.assertEqual(results[0]["掛け算合計(%)"], 600)
        self.assertEqual(results[1]["掛け算合計(%)"], 650)

    def test_normal_without_def_raise_is_unchanged(self):
        events=[{"順番": 1, "タイミング": "通常必殺", "補正先": "必殺技効果・味方の必殺支援", "変化量(%)": 0}]
        results=timeline(580165, {"sa": 30}, events, 19500000, 65, receiving=600, guard=True)
        self.assertEqual(results[0]["被弾時DEF"], results[1]["被弾時DEF"])

    def test_disabled_effect_and_invalid_values(self):
        self.assertEqual(len(timeline(100, {}, [{"有効": False}], 1000, 0)), 1)
        with self.assertRaises(ValueError):
            timeline(100, {}, [{"順番": 1, "タイミング": "test", "補正先": "軽減率", "変化量(%)": 101}], 1000, 0)

    def test_integer_boundaries_and_reverse_match_forward(self):
        for guard in [True, False]:
            for reduction in [0, 65, 99]:
                for limit in [0, 1, 500000]:
                    opts={"guard":guard,"type_multi":1.15,"crit":True,"crit_atk":50,"crit_def":50}
                    maximum=max_enemy_atk(5705263, reduction, limit, **opts)
                    self.assertLessEqual(calculate_damage(5705263, maximum, reduction, **opts), limit)
                    self.assertGreater(calculate_damage(5705263, maximum+1, reduction, **opts), limit)
                damage=calculate_damage(5705263, 500000000, reduction, **opts)
                if damage:
                    lower,upper=reverse_enemy_atk(damage, 5705263, reduction, **opts)
                    self.assertLessEqual(lower, 500000000)
                    self.assertGreaterEqual(upper, 500000000)

if __name__ == "__main__":
    unittest.main()
