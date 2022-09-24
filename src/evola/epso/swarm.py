from copy import deepcopy
from operator import attrgetter
from typing import Callable, List

import numpy as np

from evola.epso.particle import EvolutiveParticle
from evola.population import Population


class EvolutiveSwarm(Population):
    def __init__(
        self,
        swarm_size: int,
        chromossome_length: int,
        chromossome_low: float,
        chromossome_high: float,
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
        self._chromossome_low = chromossome_low
        self._chromossome_high = chromossome_high
        self._cost_function = cost_function
        self._cost_function_args = cost_function_args

        ancestors: List[EvolutiveParticle] = []
        particles: List[EvolutiveParticle] = []

        # Generate particles and ancestors randomly
        for _ in range(swarm_size):
            chromossome1 = np.zeros(chromossome_length)
            chromossome2 = np.zeros(chromossome_length)
            for i in range(chromossome_length):
                chromossome1[i] = np.random.uniform(low=chromossome_low, high=chromossome_high)
                chromossome2[i] = np.random.uniform(low=chromossome_low, high=chromossome_high)

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

        self.ancestors: List[EvolutiveParticle] = ancestors
        self.best_ancestors: List[EvolutiveParticle] = deepcopy(ancestors)
        self.particles: List[EvolutiveParticle] = particles

        sorted = min(self.ancestors, key=attrgetter("cost"))
        self.global_best = deepcopy(sorted)  # best particle

        return

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
        chromossome[chromossome > self._chromossome_high] = self._chromossome_high
        chromossome[chromossome < self._chromossome_low] = self._chromossome_low
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
                chromossome[j] = self.particles[i].chromossome[j] + deviation

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
