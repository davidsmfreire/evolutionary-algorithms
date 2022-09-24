import csv
import sys
from copy import deepcopy
from itertools import islice
from operator import attrgetter
from typing import List

import numpy as np

from evola.epso.particle import EvolutiveParticle
from evola.scene import Scene


class EvolutiveSwarm:
    def __init__(
        self,
        swarm_size: int,
        WI: float,
        WM: float,
        WC: float,
        communication_p: float,
        scene: Scene,
    ):
        self.size = swarm_size
        self.gen = 0  # generation counter (for WI)
        self.scene = scene
        self._communication_p = communication_p  # communication probability
        ancestors: List[EvolutiveParticle] = []
        particles: List[EvolutiveParticle] = []

        # Generate particles and ancestors randomly
        for _ in range(swarm_size):
            chromossome1 = np.zeros(self.scene.chromossome_length)
            chromossome2 = np.zeros(self.scene.chromossome_length)
            for i in range(self.scene.chromossome_length):
                chromossome1[i] = np.random.uniform(low=self.scene.chromossome_low, high=self.scene.chromossome_high)
                chromossome2[i] = np.random.uniform(low=self.scene.chromossome_low, high=self.scene.chromossome_high)

            ancestors.append(
                EvolutiveParticle(
                    chromossome1,
                    scene.cost_function,
                    scene.cost_function_args,
                    WI,
                    WM,
                    WC,
                )
            )
            particles.append(
                EvolutiveParticle(
                    chromossome2,
                    scene.cost_function,
                    scene.cost_function_args,
                    WI,
                    WM,
                    WC,
                )
            )

        self.ancestors: List[EvolutiveParticle] = ancestors
        self.best_ancestors: List[EvolutiveParticle] = deepcopy(ancestors)
        self.particles: List[EvolutiveParticle] = particles

        sorted = min(self.ancestors, key=attrgetter("cost"))
        self.global_best = deepcopy(sorted)  # best particle

        return

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
                    * self.particles[i].WI
                    * (self.particles[i].chromossome[j] - self.ancestors[i].chromossome[j])
                )
                deviation = deviation + np.random.normal() * self.particles[i].WM * (
                    self.best_ancestors[i].chromossome[j] - self.particles[i].chromossome[j]
                )
                deviation = deviation + communication_matrix[j] * np.random.normal() * self.particles[i].WC * (
                    self.global_best.chromossome[j] - self.particles[i].chromossome[j]
                )
                chromossome[j] = self.particles[i].chromossome[j] + deviation

            # Apply chromossome value ceiling and floor
            chromossome[chromossome > self.scene.chromossome_high] = self.scene.chromossome_high
            chromossome[chromossome < self.scene.chromossome_low] = self.scene.chromossome_low

            new_particles.append(
                EvolutiveParticle(
                    chromossome,
                    self.scene.cost_function,
                    self.scene.cost_function_args,
                    self.particles[i].WI,
                    self.particles[i].WM,
                    self.particles[i].WC,
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

    def average_cost(self):
        sum = 0.0
        p: EvolutiveParticle
        for p in self.particles:
            sum = sum + p.cost

        return sum / self.size

    def display(self, top):
        particles = sorted(self.particles, key=attrgetter("cost"))
        print("\n")
        for i in range(top):
            print("Particle %d :" % i)
            print("Cost: %.3f" % particles[i].cost)
            print("Chromossome values")
            print(particles[i].chromossome)
            print("\n")

        return

    def export(self, top, filename):
        particles = sorted(self.particles, key=attrgetter("cost"))
        with open(sys.path[0] + "/" + filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=" ")

            header = ["Solutions"]
            header.extend(str(list(range(1, top + 1))))

            writer.writerow(header)
            writer.writerow(["Chromossome value"])
            for i in range(self.scene.chromossome_length):
                chromossomes = []
                for particle in islice(particles, 0, top):
                    chromossomes.append(particle.chromossome[i])
                writer.writerow(["T%d" % (i + 1)] + chromossomes)
            costs = ["Cost"]
            for particle in islice(particles, 0, top):
                costs.append(str(particle.cost))
            writer.writerow(costs)

        return
