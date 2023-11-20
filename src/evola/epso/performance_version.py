from typing import Callable, Optional, Union

import numpy as np
from tqdm import tqdm


def epso(
    swarm_size: int,
    generations: int,
    chromosome_length: int,
    chromosome_low: Union[float, int],  # TODO support array
    chromosome_high: Union[float, int],  # TODO support array
    cost_function: Callable,
    cost_function_args: Optional[tuple] = None,
    cost_function_kwargs: Optional[dict] = None,
    wi: float = 0.5,
    wm: float = 0.5,
    wc: float = 0.5,
    communication_probability: float = 1.0,
    verbose: bool = False,
):
    # TODO add integer support
    # Init
    if isinstance(chromosome_low, list):
        if len(chromosome_low) != chromosome_length:
            raise ValueError("Chromosome lower bounds must be same length of chromosome")
    if isinstance(chromosome_high, list):
        if len(chromosome_high) != chromosome_length:
            raise ValueError("Chromosome higher bounds must be same length of chromosome")

    cost_function_args = cost_function_args or tuple()
    cost_function_kwargs = cost_function_kwargs or dict()

    # generation_counter = 0  # (for wi deviation)
    chromosome_low = chromosome_low if not isinstance(chromosome_low, list) else np.array(chromosome_low)
    chromosome_high = chromosome_high if not isinstance(chromosome_high, list) else np.array(chromosome_high)

    # Init particles

    # chromosome_matrix is composed of the following:
    #      | particles | ancestors | best_ancestors | particles sons | ancestors sons | best_ancestors_sons
    # c1   |
    # c2   |
    # ...
    # cn   |
    # wi   |
    # wm   |
    # wc   |
    # cost |
    total_particles = swarm_size * 4
    weights_ammount = 3

    # Indexers
    chromosome_slice_rows = slice(0, -4)
    weights_rows_slice = slice(-4, -1)
    wi_slice_rows = -4
    wm_slice_rows = -3
    wc_slice_rows = -2
    cost_slice_row = -1

    current_particles_slice_cols = slice(0, swarm_size * 3)

    particles_slice_cols = slice(0, swarm_size)
    ancestors_slice_cols = slice(swarm_size, swarm_size * 2)
    particles_and_ancestors_slice_cols = slice(0, swarm_size * 2)

    best_ancestors_slice_cols = slice(swarm_size * 2, swarm_size * 3)

    particles_sons_slice_cols = slice(swarm_size * 3, swarm_size * 4)

    # Genetic soup initialization
    chromosome_matrix = np.zeros((chromosome_length + weights_ammount + 1, total_particles))
    chromosome_matrix[chromosome_slice_rows, particles_slice_cols] = np.random.uniform(
        chromosome_low, chromosome_high, (chromosome_length, swarm_size)
    )
    chromosome_matrix[chromosome_slice_rows, ancestors_slice_cols] = np.random.uniform(
        chromosome_low, chromosome_high, (chromosome_length, swarm_size)
    )

    chromosome_matrix[wi_slice_rows, particles_and_ancestors_slice_cols] = wi
    chromosome_matrix[wm_slice_rows, particles_and_ancestors_slice_cols] = wm
    chromosome_matrix[wc_slice_rows, particles_and_ancestors_slice_cols] = wc

    # Init Cost

    chromosome_matrix[cost_slice_row, particles_and_ancestors_slice_cols] = np.apply_along_axis(
        cost_function,
        0,
        chromosome_matrix[chromosome_slice_rows, particles_and_ancestors_slice_cols],
        *cost_function_args,
        **cost_function_kwargs,
    )

    chromosome_matrix[:, best_ancestors_slice_cols] = chromosome_matrix[:, ancestors_slice_cols]
    global_best_chromosome_index = np.argmin(chromosome_matrix[cost_slice_row, current_particles_slice_cols])

    iterator = tqdm(range(generations)) if verbose else range(generations)
    for generation in iterator:
        # Reproduce
        chromosome_matrix[:, particles_sons_slice_cols] = chromosome_matrix[:, particles_slice_cols]
        # Mutate
        chromosome_matrix[weights_rows_slice, particles_sons_slice_cols] = chromosome_matrix[
            weights_rows_slice, particles_sons_slice_cols
        ] * (1 + 0.1 * np.random.normal(size=(weights_ammount, swarm_size)))

        # Move
        if communication_probability == 1:
            communication_matrix = np.ones((chromosome_length, swarm_size * 2))
        else:
            communication_matrix = np.random.choice(
                [0, 1],
                (chromosome_length, swarm_size * 2),
                p=[1 - communication_probability, communication_probability],
            )

        # TODO this can be split in two cores (uses more memory...)
        # or 100% vectorized if particles and sons are side by side
        # and we copy ancestors and best ancestors (also uses more memory...)
        for i, _slice in enumerate([particles_slice_cols, particles_sons_slice_cols]):
            # wi: inertia weight
            deviation = (
                1
                / (generation + 1)
                * chromosome_matrix[wi_slice_rows, _slice]
                * (
                    chromosome_matrix[chromosome_slice_rows, _slice]
                    - chromosome_matrix[chromosome_slice_rows, ancestors_slice_cols]
                )
            )

            # wm: best ancestor weight
            deviation = deviation + np.random.normal(size=deviation.shape) * chromosome_matrix[
                wm_slice_rows, _slice
            ] * (
                chromosome_matrix[chromosome_slice_rows, best_ancestors_slice_cols]
                - chromosome_matrix[chromosome_slice_rows, _slice]
            )

            # wc: global best weight
            deviation = deviation + communication_matrix[
                :, swarm_size * i : swarm_size * (i + 1)  # noqa
            ] * np.random.normal(size=deviation.shape) * chromosome_matrix[wc_slice_rows, _slice] * (
                chromosome_matrix[chromosome_slice_rows, global_best_chromosome_index][:, np.newaxis]
                - chromosome_matrix[chromosome_slice_rows, _slice]
            )

            if i == 0:  # particles sons
                # create next ancestors
                chromosome_matrix[:, ancestors_slice_cols] = chromosome_matrix[:, _slice]
                chromosome_matrix[:, best_ancestors_slice_cols] = np.where(
                    chromosome_matrix[cost_slice_row, ancestors_slice_cols]
                    < chromosome_matrix[cost_slice_row, best_ancestors_slice_cols],
                    chromosome_matrix[:, ancestors_slice_cols],
                    chromosome_matrix[:, best_ancestors_slice_cols],
                )

            # Add deviation to particles
            chromosome_matrix[chromosome_slice_rows, _slice] = (
                chromosome_matrix[chromosome_slice_rows, _slice] + deviation
            )

            # Enforce domain
            chromosome_matrix[chromosome_slice_rows, _slice] = np.where(
                chromosome_matrix[chromosome_slice_rows, _slice] > chromosome_high,
                chromosome_high,
                chromosome_matrix[chromosome_slice_rows, _slice],
            )
            chromosome_matrix[chromosome_slice_rows, _slice] = np.where(
                chromosome_matrix[chromosome_slice_rows, _slice] < chromosome_low,
                chromosome_low,
                chromosome_matrix[chromosome_slice_rows, _slice],
            )

            # Calculate new cost
            chromosome_matrix[cost_slice_row, _slice] = np.apply_along_axis(
                cost_function,
                0,
                chromosome_matrix[chromosome_slice_rows, _slice],
                *cost_function_args,
                **cost_function_kwargs,
            )

        # Select
        costs = np.concatenate(
            (
                chromosome_matrix[cost_slice_row, particles_slice_cols],
                chromosome_matrix[cost_slice_row, particles_sons_slice_cols],
            )
        )
        sorted_costs_indexes = np.argsort(costs)
        half_best_indexes = sorted_costs_indexes[: len(sorted_costs_indexes) // 2]

        half_best_indexes = np.where(
            half_best_indexes > chromosome_matrix.shape[1], (half_best_indexes - swarm_size) * 3, half_best_indexes
        )
        chromosome_matrix[:, particles_slice_cols] = chromosome_matrix[:, half_best_indexes]

    global_best_chromosome_index = np.argmin(chromosome_matrix[cost_slice_row, current_particles_slice_cols])

    return chromosome_matrix[chromosome_slice_rows, global_best_chromosome_index]  # solution
