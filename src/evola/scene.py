from typing import Callable


class Scene:
    def __init__(
        self,
        chromossome_length: int,
        cost_function: Callable,
        cost_function_args: tuple,
        desc: str,
        chromossome_low: float = 0,
        chromossome_high: float = 1,
    ) -> None:
        self.desc = desc
        self.chromossome_length = chromossome_length
        self.chromossome_low = chromossome_low
        self.chromossome_high = chromossome_high
        self.cost_function = cost_function
        self.cost_function_args = cost_function_args
