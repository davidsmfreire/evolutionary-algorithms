from copy import deepcopy
from operator import attrgetter
from typing import Callable, List, Tuple, Union

import numpy as np

from evola.epso.particle import EvolutiveParticle
from evola.population import Population


class EvolutiveSwarm(Population):
    def __init__(
        self,
        swarm_size: int,
        chromossome_length: int,
        chromossome_low: Union[List[Union[float, int]], Union[float, int]],
        chromossome_high: Union[List[Union[float, int]], Union[float, int]],
        chromossome_dtypes: Union[List[type], type],
        cost_function: Callable,
        cost_function_args: tuple,
        wi: float,
        wm: float,
        wc: float,
        communication_p: float,
    ):
        self.size = swarm_size
        self.gen = 0  # generation counter (for wi)
        self._communication_p = communication_p  # communication probability
        self._chromossome_length = chromossome_length
        if not isinstance(chromossome_low, list):
            chromossome_low = [chromossome_low] * chromossome_length
        if not isinstance(chromossome_high, list):
            chromossome_high = [chromossome_high] * chromossome_length

        self._chromossome_low = chromossome_low
        self._chromossome_high = chromossome_high
        self._cost_function = cost_function
        self._cost_function_args = cost_function_args

        if not isinstance(chromossome_dtypes, list):
            chromossome_dtypes = [chromossome_dtypes] * chromossome_length

        if len(chromossome_dtypes) != chromossome_length:
            raise ValueError("Chromossome types list must be same length of chromossome")

        if len(chromossome_low) != chromossome_length:
            raise ValueError("Chromossome lower bounds must be same length of chromossome")

        if len(chromossome_high) != chromossome_length:
            raise ValueError("Chromossome higher bounds must be same length of chromossome")

        rand_function: List[Callable] = []
        for _type in chromossome_dtypes:
            if isinstance(_type, int):
                rand_function.append(np.random.randint)
            else:  # by default, float chromossome value
                rand_function.append(np.random.uniform)

        self._rand_function = rand_function
        self._chromossome_dtypes: List[type] = chromossome_dtypes

        particles, ancestors = self._init_particles(
            swarm_size,
            chromossome_length,
            rand_function,
            chromossome_low,
            chromossome_high,
            cost_function,
            cost_function_args,
            wi,
            wm,
            wc,
        )

        self.ancestors: List[EvolutiveParticle] = ancestors
        self.best_ancestors: List[EvolutiveParticle] = deepcopy(ancestors)
        self.particles: List[EvolutiveParticle] = particles

        sorted = min(self.ancestors, key=attrgetter("cost"))
        self.global_best = deepcopy(sorted)  # best particle

        return

    @staticmethod
    def _init_particles(
        swarm_size,
        chromossome_length,
        rand_function,
        chromossome_low,
        chromossome_high,
        cost_function,
        cost_function_args,
        wi,
        wm,
        wc,
    ) -> Tuple[List[EvolutiveParticle], List[EvolutiveParticle]]:
        # Generate particles and ancestors randomly
        ancestors: List[EvolutiveParticle] = []
        particles: List[EvolutiveParticle] = []

        for _ in range(swarm_size):
            chromossome1 = np.zeros(chromossome_length)
            chromossome2 = np.zeros(chromossome_length)
            for i in range(chromossome_length):
                chromossome1[i] = rand_function[i](low=chromossome_low[i], high=chromossome_high[i])
                chromossome2[i] = rand_function[i](low=chromossome_low[i], high=chromossome_high[i])

            ancestors.append(
                EvolutiveParticle(
                    chromossome1,
                    cost_function,
                    cost_function_args,
                    wi,
                    wm,
                    wc,
                )
            )
            particles.append(
                EvolutiveParticle(
                    chromossome2,
                    cost_function,
                    cost_function_args,
                    wi,
                    wm,
                    wc,
                )
            )

        return particles, ancestors

    @property
    def elements(self):
        return self.particles

    def reproduce(self):

        # Append a copy of the swarm to itself
        sons = deepcopy(self.particles)
        son: EvolutiveParticle
        for son in sons:
            son.mutate()

        self.particles.extend(sons)
        self.ancestors.extend(self.ancestors)
        self.best_ancestors.extend(self.best_ancestors)

        # Swarm doubles it's size
        self.size = self.size * 2

        return

    def select(self):

        # Population reduces in half
        self.size = int(self.size / 2)

        # Overwrite parents, ancestors and best ancestors if children perform better after swarm moves
        for i in range(self.size):
            if self.particles[i].cost > self.particles[i + self.size].cost:
                self.particles[i] = deepcopy(self.particles[i + self.size])
                self.ancestors[i] = deepcopy(self.ancestors[i + self.size])
                self.best_ancestors[i] = deepcopy(self.best_ancestors[i + self.size])

        # Only first half of the swarm survives
        self.particles = self.particles[: self.size]
        self.ancestors = self.ancestors[: self.size]
        self.best_ancestors = self.best_ancestors[: self.size]

        return

    def _constrain(self, chromossome: np.ndarray):
        for i in range(len(chromossome)):
            if chromossome[i] > self._chromossome_high[i]:
                chromossome[i] = self._chromossome_high[i]
            elif chromossome[i] < self._chromossome_low[i]:
                chromossome[i] = self._chromossome_low[i]
        return chromossome

    def move(self):

        self.gen = self.gen + 1  # Increment nº of generations

        # Create new generation
        new_particles = []

        # Move swarm
        for i in range(self.size):
            chromossome = np.zeros(len(self.particles[i].chromossome))

            # Create probability of alllowing the particle to move on each dimension of the global best
            if self._communication_p == 1:
                communication_matrix = np.ones(len(self.particles[i].chromossome))
            else:
                communication_matrix = np.random.choice(
                    [0, 1],
                    len(self.particles[i].chromossome),
                    p=[1 - self._communication_p, self._communication_p],
                )

            # Apply deviation, one dimention at a time
            for j in range(len(self.particles[i].chromossome)):
                deviation = (
                    1
                    / self.gen
                    * self.particles[i].wi
                    * (self.particles[i].chromossome[j] - self.ancestors[i].chromossome[j])
                )
                deviation = deviation + np.random.normal() * self.particles[i].wm * (
                    self.best_ancestors[i].chromossome[j] - self.particles[i].chromossome[j]
                )
                deviation = deviation + communication_matrix[j] * np.random.normal() * self.particles[i].wc * (
                    self.global_best.chromossome[j] - self.particles[i].chromossome[j]
                )
                chromossome[j] = self._chromossome_dtypes[j](self.particles[i].chromossome[j] + deviation)
                # in this last line we typecast to correct chromossome dtype

            # Apply chromossome value ceiling and floor
            chromossome = self._constrain(chromossome)

            new_particles.append(
                EvolutiveParticle(
                    chromossome,
                    self._cost_function,
                    self._cost_function_args,
                    self.particles[i].wi,
                    self.particles[i].wm,
                    self.particles[i].wc,
                )
            )

        # Current generation is now ancestor generation
        self.ancestors = deepcopy(self.particles)

        # Update best ancestors according to new generation of ancestors
        for i in range(len(self.best_ancestors)):
            if self.ancestors[i].cost < self.best_ancestors[i].cost:
                self.best_ancestors[i] = deepcopy(self.ancestors[i])

        # Update new generation particles
        self.particles = new_particles

        # Update global best
        best = min(self.ancestors, key=attrgetter("cost"))
        self.global_best = deepcopy(best)

        return

    def last_gen_update(self):
        # Must run after last generation
        newbest = min(self.particles, key=attrgetter("cost"))
        if newbest.cost < self.global_best.cost:
            self.global_best = newbest
        return
