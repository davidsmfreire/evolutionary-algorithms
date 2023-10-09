import numpy as np

from evola.solution import Solution

# Optionally define random seed
# np.random.seed(42)


class EvolutiveParticle(Solution):
    def __init__(self, chromossome, cost_function, cost_function_args, wi: float, wm: float, wc: float):
        super().__init__(chromossome, cost_function, cost_function_args)
        self.wi = wi
        self.wm = wm
        self.wc = wc

        self.calc_cost()

        return

    def mutate(self):
        self.wi = self.wi * (1 + 0.1 * np.random.normal())
        self.wm = self.wm * (1 + 0.1 * np.random.normal())
        self.wc = self.wc * (1 + 0.1 * np.random.normal())
