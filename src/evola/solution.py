from typing import Callable


class Solution:
    def __init__(self, chromossome, cost_function: Callable, cost_function_args: tuple):
        self.chromossome = chromossome
        self.cost: float = 0.0
        self._cost_function = cost_function
        self._cost_function_args = cost_function_args
        return

    def calc_cost(self):
        self.cost = self._cost_function(self.chromossome, *self._cost_function_args)
