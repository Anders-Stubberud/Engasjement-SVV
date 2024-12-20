from typing import List
from typing import Tuple

import numpy as np


def find_threshold_index(array, delta):
    """
    Finds the index in the array where all subsequent elements are less than delta.

    Args:
      array: The input NumPy array.
      delta: The threshold value.

    Returns:
      The index of the first element such that all subsequent elements are less than delta.
      If no such index exists, returns -1.
    """

    indices = np.where(array >= delta)[0]

    if len(indices) == 0:
        return 0

    return indices[-1] + 1


def trim_tonnage_x_axis(total_values: List[float], delta: float) -> Tuple[List[float], float]:
    """
    Trims the array to include only the elements up to the threshold index.

    Args:
    total_values: The input list of values.
    delta: The threshold value.

    Returns:
    The trimmed list of values.
    """

    threshold_index = find_threshold_index(total_values, delta)

    return total_values[:threshold_index], threshold_index
