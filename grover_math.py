from math import pi, sqrt
from random import random


def optimal_iterations(n_states: int) -> int:
    return max(1, int((pi / 4) * sqrt(n_states)))


def initial_amplitudes(n_states: int) -> list[float]:
    initial = 1 / sqrt(n_states)
    return [initial for _ in range(n_states)]


def oracle_step(amplitudes: list[float], marked_index: int) -> tuple[list[float], float]:
    next_amplitudes = amplitudes.copy()
    next_amplitudes[marked_index] *= -1
    mean = sum(next_amplitudes) / len(next_amplitudes)
    return next_amplitudes, mean


def diffusion_step(amplitudes: list[float]) -> tuple[list[float], float]:
    mean = sum(amplitudes) / len(amplitudes)
    next_amplitudes = [(2 * mean - amplitude) for amplitude in amplitudes]
    next_mean = sum(next_amplitudes) / len(next_amplitudes)
    return next_amplitudes, next_mean


def measure_state(amplitudes: list[float]) -> int:
    threshold = random()
    cumulative = 0.0
    result = len(amplitudes) - 1
    for index, amplitude in enumerate(amplitudes):
        cumulative += amplitude * amplitude
        if threshold <= cumulative:
            result = index
            break
    return result
