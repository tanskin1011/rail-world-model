"""Validate raw camera actions, not calibrated speed or physical correctness."""
import math


def validate_action(action, transitions=188):
    if not isinstance(action, list) or len(action) != transitions:
        raise ValueError(f"Expected {transitions} transitions")
    for index, row in enumerate(action):
        if not isinstance(row, list) or len(row) != 9:
            raise ValueError(f"Action {index}: expected 9 numeric values")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in row):
            raise ValueError(f"Action {index}: non-finite or non-numeric value")
        # The first two rotation columns must form an orthonormal pair.
        a, b = row[3:6], row[6:9]
        if abs(sum(v*v for v in a)-1) > 1e-3 or abs(sum(v*v for v in b)-1) > 1e-3 or abs(sum(x*y for x,y in zip(a,b))) > 1e-3:
            raise ValueError(f"Action {index}: invalid rotation columns")
    return {"transitions": transitions, "raw_dimensions": 9, "finite": True, "rotation_columns_valid": True}
