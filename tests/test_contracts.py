import unittest
from rail_world_model.contracts import validate_action


class ActionContractTests(unittest.TestCase):
    def test_stop_identity_rotation_is_not_all_zero(self):
        self.assertTrue(validate_action([[0,0,0,1,0,0,0,1,0]], 1)["finite"])

    def test_wrong_count(self):
        with self.assertRaises(ValueError): validate_action([], 1)

    def test_nan(self):
        with self.assertRaises(ValueError): validate_action([[float("nan"),0,0,1,0,0,0,1,0]], 1)

    def test_zero_rotation_invalid(self):
        with self.assertRaises(ValueError): validate_action([[0]*9], 1)

    def test_forward_translation(self):
        self.assertTrue(validate_action([[0,0,0.1,1,0,0,0,1,0]], 1)["rotation_columns_valid"])

    def test_boolean_rejected(self):
        with self.assertRaises(ValueError): validate_action([[True,0,0,1,0,0,0,1,0]], 1)
