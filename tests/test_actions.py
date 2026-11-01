import unittest
from rail_world_model.actions import PROFILES,straight_action
from rail_world_model.contracts import validate_action


class StraightCameraPlanTests(unittest.TestCase):
    def test_profiles_valid(self):
        for profile in PROFILES:self.assertTrue(validate_action(straight_action(profile))["finite"])

    def test_stop_identity(self):
        self.assertEqual(straight_action("stop")[0],[0,0,0,1,0,0,0,1,0])

    def test_speed_ratio_in_plan(self):
        self.assertAlmostEqual(straight_action("const10")[0][2],2*straight_action("const5")[0][2])

    def test_acceleration_and_deceleration(self):
        a=straight_action("accel");d=straight_action("decel")
        self.assertLess(a[0][2],a[-1][2]);self.assertGreater(d[0][2],d[-1][2])

    def test_invalid_profile(self):
        with self.assertRaises(ValueError):straight_action("unknown")

    def test_invalid_dimensions(self):
        with self.assertRaises(ValueError):straight_action("stop",transitions=0)
