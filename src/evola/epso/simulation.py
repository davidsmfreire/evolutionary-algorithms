import time
from copy import deepcopy
from multiprocessing import Queue

from tqdm.auto import tqdm

from evola.epso.swarm import EvolutiveSwarm
from evola.scene import Scene
from evola.simulation import Simulation


class EPSO(Simulation):
    def __init__(
        self,
        generations,
        size: int,
        WI: float,
        WM: float,
        WC: float,
        communication_probability: float,
        scene: Scene,
        hold: bool,
        export_top=0,
    ) -> None:
        desc = scene.desc + " EPSO (p=%.2f)" % communication_probability
        super().__init__(
            generations, EvolutiveSwarm(size, WI, WM, WC, communication_probability, scene), hold, desc, export_top
        )

        self.pop: EvolutiveSwarm
        return

    @property
    def best_particle(self):
        return self.pop.global_best

    def run_gui(self):
        self.init_graph()
        history = []
        start_time = time.time()

        for _ in tqdm(range(self.generations)):
            # EPSO steps
            self.pop.reproduce()
            self.pop.move()
            self.pop.select()

            # Obter o custo melhor da população
            new_data = self.pop.global_best.cost
            history.append(new_data)
            self.cost_history.append(new_data)
            # Atualizar gráfico
            self.update_graph(history)

        self.pop.last_gen_update()

        end_time = time.time()

        self.best_cost = self.pop.global_best.cost

        print(self.final_message(start_time, end_time))

        if self.export_top > 0:
            self.export(self.export_top, self.generations)

        self.finish_graph()

        return

    def _run_once(self, thread_num):
        pbar = tqdm(range(self.generations), position=thread_num + 1, leave=False)
        pop = deepcopy(self.pop)
        for _ in pbar:
            # EPSO
            self.cost_history.append(deepcopy(pop.global_best.cost))
            pbar.set_description(f"({self.pop.size},{self.generations}) C = {pop.global_best.cost:.0f} euros")
            pop.reproduce()
            pop.move()
            pop.select()
        pop.last_gen_update()
        return pop

    def _run_multiple(self, itera, thread_num):
        pbar = tqdm(range(itera), position=thread_num + 1, leave=False)
        for _ in pbar:
            pop = deepcopy(self.pop)
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
            pop = deepcopy(self.pop)
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
            print(self.final_message(start_time, end_time))

        self.pop = pop

        if self.export_top > 0:
            self.export(self.export_top)
        if q:
            q.put(self)  # returns self in a queue, if multiprocessing is enabled
        return
