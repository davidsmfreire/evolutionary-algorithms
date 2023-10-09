from evola.epso.academic_version import EPSO
from evola.epso.performance_version import epso

A = [
    -500.0,
    2.5,
    1.666666666,
    1.25,
    1.0,
    0.8333333,
    0.714285714,
    0.625,
    0.555555555,
    1.0,
    -43.6363636,
    0.41666666,
    0.384615384,
    0.357142857,
    0.3333333,
    0.3125,
    0.294117647,
    0.277777777,
    0.263157894,
    0.25,
    0.238095238,
    0.227272727,
    0.217391304,
    0.208333333,
    0.2,
    0.192307692,
    0.185185185,
    0.178571428,
    0.344827586,
    0.6666666,
    -15.48387097,
    0.15625,
    0.1515151,
    0.14705882,
    0.14285712,
    0.138888888,
    0.135135135,
    0.131578947,
    0.128205128,
    0.125,
    0.121951219,
    0.119047619,
    0.116279069,
    0.113636363,
    0.1111111,
    0.108695652,
    0.106382978,
    0.208333333,
    0.408163265,
    0.8,
]


def main():
    # Minimize
    # sum(i, a(i)*power(x, ord(i)))
    def cost(chromossome, *args, **kwargs):
        x = chromossome[0]
        return sum(a * x ** (i + 1) for i, a in enumerate(A))

    sim = EPSO(
        generations=100,
        size=1000,
        chromossome_length=1,
        chromossome_low=1,
        chromossome_high=2,
        cost_function=cost,
        cost_function_args=(),
        description="Test",
    )

    sim.run_gui()

    print("Solution:")
    print(sim.best_solution[0])

    result = epso(
        swarm_size=1000, generations=100, chromosome_length=1, chromosome_high=2, chromosome_low=1, cost_function=cost
    )
    print("Perf Solution:")
    print(result)


if __name__ == "__main__":
    main()
