import numpy as np

from evola.solution import Solution

# Optionally define random seed
# np.random.seed(42)


class EvolutiveParticle(Solution):
    def __init__(self, chromossome, cost_function, cost_function_args, WI: float, WM: float, WC: float):
        super().__init__(chromossome, cost_function, cost_function_args)
        self.WI = WI
        self.WM = WM
        self.WC = WC

        self.calc_cost()

        return

    def mutate(self):
        self.WI = self.WI * (1 + 0.1 * np.random.normal())
        self.WM = self.WM * (1 + 0.1 * np.random.normal())
        self.WC = self.WC * (1 + 0.1 * np.random.normal())
