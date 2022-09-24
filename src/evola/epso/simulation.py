import time
from copy import deepcopy
from multiprocessing import Queue
from typing import Callable

from tqdm.auto import tqdm

from evola.epso.swarm import EvolutiveSwarm
from evola.simulation import Simulation


class EPSO(Simulation):
    def __init__(
        self,
        generations,
        size: int,
        chromossome_length: int,
        chromossome_low: float,
        chromossome_high: float,
        cost_function: Callable,
        cost_function_args: tuple,
        wi: float = 0.5,
        wm: float = 0.5,
        wc: float = 0.5,
        communication_probability: float = 1.0,
        export_top=0,
        description="",
    ) -> None:
        desc = description + " EPSO (p=%.2f)" % communication_probability

        pop = EvolutiveSwarm(
            size,
            chromossome_length,
            chromossome_low,
            chromossome_high,
            cost_function,
            cost_function_args,
            wi,
            wm,
            wc,
            communication_probability,
        )

        super().__init__(generations, pop, desc, export_top)

        self.population: EvolutiveSwarm
        return

    @property
    def best_particle(self):
        return self.population.global_best

    @property
    def best_solution(self):
        return self.population.global_best.chromossome

    def run_gui(self, hold=False):
        self._init_graph()
        history = []
        start_time = time.time()

        for _ in tqdm(range(self.generations)):
            # EPSO steps
            self.population.reproduce()
            self.population.move()
            self.population.select()

            # Obter o custo melhor da população
            new_data = self.population.global_best.cost
            history.append(new_data)
            self.cost_history.append(new_data)
            # Atualizar gráfico
            self._update_graph(history)

        self.population.last_gen_update()

        end_time = time.time()

        self.best_cost = self.population.global_best.cost

        print(self._final_message(start_time, end_time))

        if self.export_top > 0:
            self.export(self.export_top, self.generations)

        self._finish_graph(hold)

        return

    def _run_once(self, thread_num):
        pbar = tqdm(range(self.generations), position=thread_num + 1, leave=False)
        pop = deepcopy(self.population)
        for _ in pbar:
            # EPSO
            self.cost_history.append(deepcopy(pop.global_best.cost))
            pbar.set_description(f"({self.population.size},{self.generations}) C = {pop.global_best.cost:.0f} euros")
            pop.reproduce()
            pop.move()
            pop.select()
        pop.last_gen_update()
        return pop

    def _run_multiple(self, itera, thread_num):
        pbar = tqdm(range(itera), position=thread_num + 1, leave=False)
        for _ in pbar:
            pop = deepcopy(self.population)
            for _ in range(self.generations):
                # EPSO
                pop.reproduce()
                pop.move()
                pop.select()
            pop.last_gen_update()
            self.best_hist.append(deepcopy(pop.global_best.cost))
            self.avg_hist.append(pop.average_cost())
        return pop

    def _run_no_verbose(self, itera):
        for _ in range(itera):
            pop = deepcopy(self.population)
            for _ in range(self.generations):
                # EPSO
                pop.reproduce()
                pop.move()
                pop.select()
            pop.last_gen_update()
            self.best_hist.append(deepcopy(pop.global_best.cost))
            self.avg_hist.append(pop.average_cost())
        return pop

    def run_cli(self, q: Queue = None, thread_num=0, verbose=True, itera=1):

        start_time = time.time()

        pop: EvolutiveSwarm
        if verbose and itera == 1:
            pop = self._run_once(thread_num)
        elif verbose and itera > 1:
            pop = self._run_multiple(itera, thread_num)
        else:
            pop = self._run_no_verbose(itera)

        end_time = time.time()

        if itera == 1:
            self.best_cost = pop.global_best.cost
        else:
            self.best_cost = min(self.best_hist)
        if verbose:
            print(self._final_message(start_time, end_time))

        self.population = pop

        if self.export_top > 0:
            self.export(self.export_top)
        if q:
            q.put(self)  # returns self in a queue, if multiprocessing is enabled
        return
