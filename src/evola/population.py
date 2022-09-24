import abc
import csv
import sys
from itertools import islice
from operator import attrgetter
from typing import List

from evola.solution import Solution


class Population(abc.ABC):
    global_best: Solution
    size: int
    _chromossome_length: int

    @abc.abstractproperty
    @property
    def elements(self) -> List[Solution]:
        pass

    def average_cost(self):
        sum = 0.0
        for p in self.elements:
            sum = sum + p.cost

        return sum / self.size

    def display(self, top: int):
        elements = sorted(self.elements, key=attrgetter("cost"))
        print("\n")
        for i in range(top):
            print("Particle %d :" % i)
            print("Cost: %.3f" % elements[i].cost)
            print("Chromossome values")
            print(elements[i].chromossome)
            print("\n")

        return

    def export(self, top, filename):
        elements = sorted(self.elements, key=attrgetter("cost"))
        with open(sys.path[0] + "/" + filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=",")
            writer.writerow(["Chromossome values"])
            indexes = [f"{i}" for i in range(self._chromossome_length)]
            writer.writerow(indexes + ["Cost"])
            for element in islice(elements, 0, top):
                chromossome = []
                for i in range(self._chromossome_length):
                    chromossome.append(element.chromossome[i])
                writer.writerow(chromossome + [element.cost])

        return
