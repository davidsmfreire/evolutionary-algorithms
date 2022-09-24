from evola.epso import EPSO


def main():
    # Minimize
    # power(x,6) - 52/25*power(x,5) + 39/80*power(x,4) + 71/10*power(x,3) - 79/20*power(x,2) - x + 1/10
    def cost(chromossome):
        x = chromossome[0]
        return (x**6) - 52 / 25 * (x**5) + 39 / 80 * (x**4) + 71 / 10 * (x**3) - 79 / 20 * (x**2) - x + 1 / 10

    sim = EPSO(
        generations=100,
        size=10,
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


if __name__ == "__main__":
    main()
