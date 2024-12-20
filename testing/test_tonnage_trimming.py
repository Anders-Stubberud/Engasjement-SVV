import numpy as np
from source.utils import trim_tonnage_x_axis

testcases = {
    'Test Case 1': {
        'input': np.array([10, 12, 15, 8, 7, 5, 3, 2, 6, 4, 5]),
        'delta': 6,
        'expected': np.array([10, 12, 15, 8, 7, 5, 3, 2, 6]),
    },
    'Test Case 2': {
        'input': np.array([10, 12, 15, 8, 7, 6]),
        'delta': 6,
        'expected': np.array([10, 12, 15, 8, 7, 6]),
    },
    'Test Case 3': {
        'input': np.array([3, 2, 1]),
        'delta': 6,
        'expected': np.array([]),
    },
    'Test Case 4': {
        'input': np.array([8, 7, 6, 5, 3, 2, 6]),
        'delta': 6,
        'expected': np.array([8, 7, 6, 5, 3, 2, 6]),
    },
    'Test Case 5': {
        'input': np.array([3, 2, 1, 6, 7, 8]),
        'delta': 6,
        'expected': np.array([3, 2, 1, 6, 7, 8]),
    },
    'Test Case 6': {
        'input': np.array([5, 7, 3, 8, 4, 6, 2]),
        'delta': 6,
        'expected': np.array([5, 7, 3, 8, 4, 6]),
    },
    'Test Case 7': {
        'input': np.array([]),
        'delta': 6,
        'expected': np.array([]),
    },
}

def test_tonnage_trimming():
    for name, data in testcases.items():
        result, _ = trim_tonnage_x_axis(data['input'], data['delta'])
        assert np.array_equal(result, data['expected']), f"{name} failed. Expected {data['expected']} but got {result}"
