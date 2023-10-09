from math import isclose

from evola.epso import EPSO, epso


def test_run_cli_simple():
    # Wingo
    # Minimize
    # power(x,6) - 52/25*power(x,5) + 39/80*power(x,4) + 71/10*power(x,3) - 79/20*power(x,2) - x + 1/10
    def cost(chromossome):
        x = chromossome[0]
        return (x**6) - 52 / 25 * (x**5) + 39 / 80 * (x**4) + 71 / 10 * (x**3) - 79 / 20 * (x**2) - x + 1 / 10

    sim = EPSO(
        generations=10,
        size=100,
        chromossome_length=1,
        chromossome_low=-2,
        chromossome_high=10,
        cost_function=cost,
        cost_function_args=(),
    )

    sim.run_cli(verbose=False)

    best_cost = sim.best_cost
    best_solution = sim.best_particle.chromossome[0]

    assert isclose(best_cost, -7.487, abs_tol=0.001)
    assert isclose(best_solution, -1.191, abs_tol=0.001)


def test_run_performance_version():
    def cost(chromossome):
        x = chromossome[0]
        return (x**6) - 52 / 25 * (x**5) + 39 / 80 * (x**4) + 71 / 10 * (x**3) - 79 / 20 * (x**2) - x + 1 / 10

    best_solution = epso(
        swarm_size=100,
        generations=10,
        chromosome_length=1,
        chromosome_low=-2,
        chromosome_high=10,
        cost_function=cost,
        cost_function_args=(),
    )

    best_cost = cost(best_solution)

    assert isclose(best_cost, -7.487, abs_tol=0.001)
    assert isclose(best_solution, -1.191, abs_tol=0.001)
