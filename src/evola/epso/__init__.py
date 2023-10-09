"""
    Evolutionary Particle Swarm Optimization
"""
__all__ = ["EPSO", "epso"]
from .academic_version.simulation import EPSO  # noqa
from .performance_version import epso
