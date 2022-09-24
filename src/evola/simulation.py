import csv
import sys
from typing import List

from matplotlib import pyplot as plt

from evola.population import Population


class Simulation:
    def __init__(self, generations: int, pop: Population, description="", export_top=0) -> None:
        self.generations: int = generations
        self.population: Population = pop
        self.description: str = description + " (%d ind, %d gen)\n" % (
            self.population.size,
            self.generations,
        )
        self.export_top: int = export_top
        self.cost_history: List[float] = []
        self.best_hist: List[float] = []
        self.avg_hist: List[float] = []
        self.best_cost: float = 0.0
        return

    def _init_graph(self):
        # Real time plot setup
        plt.ion()
        fig, ax1 = plt.subplots()
        plt.ylabel("Cost")
        plt.xlabel("Generation")
        (line1,) = ax1.plot([], "r-")
        self._fig = fig
        self._ax = ax1
        self._line = line1

    def _update_graph(self, history):
        new_data = history[-1]
        # Update y scale dynamically
        if len(history) == 1:
            gap = new_data * 0.5
            self._ax.set_ylim([new_data - gap, new_data + gap])
        else:
            oldlim = self._ax.get_ylim()
            if new_data > oldlim[1]:
                tol = (new_data - oldlim[0]) * 0.1
                self._ax.set_ylim([oldlim[0], new_data + tol])
            elif new_data < oldlim[0]:
                tol = (oldlim[1] - new_data) * 0.1
                self._ax.set_ylim([new_data - tol, oldlim[1]])

        # Mudar eixo X
        self._line.set_xdata([*range(len(history))])
        self._ax.set_xlim(0, len(history))

        # Atualizar eixo Y
        self._line.set_ydata(history)

        # Atualizar gráfico
        self._fig.canvas.draw()
        self._fig.canvas.flush_events()
        return

    def _finish_graph(self, hold):
        self._fig.canvas.draw()
        plt.ioff()
        if hold:
            plt.show()
        else:
            plt.close(self._fig)

    def export(self, top):
        name = self.description + " (%d ind, %d gen)" % (self.population.size, self.generations) + ".csv"
        self.population.export(top=top, filename=name)
        return

    def _final_message(self, start, end):
        head = self.description
        time = "\t-> Simulation time: %.3fs total | %.1f gen/s\n" % (
            end - start,
            self.generations / (end - start),
        )
        bestcost = "\t-> Least cost solution: %.6f\n" % self.best_cost
        return head + time + bestcost

    def print(self, top):
        self.population.display(top)
        return

    def export_histogram(self):
        if len(self.best_hist) > 0:
            filename = self.description

            with open(sys.path[0] + "/" + filename + ".csv", "w", newline="") as csvfile:
                writer = csv.writer(csvfile, delimiter=" ")
                for value in self.best_hist:
                    writer.writerow([value])

        return
