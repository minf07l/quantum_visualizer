from math import gcd
from random import Random
from typing import List, Optional, Tuple


def multiplicative_order(a: int, modulus: int) -> Optional[int]:
    if gcd(a, modulus) != 1:
        return None
    value = 1
    for order in range(1, modulus + 1):
        value = (value * a) % modulus
        if value == 1:
            return order
    return None


def continued_fraction_convergents(numerator: int, denominator: int) -> List[Tuple[int, int]]:
    a = numerator
    b = denominator
    quotients = []
    while b:
        q = a // b
        quotients.append(q)
        a, b = b, a - q * b

    prev_num, num = 0, 1
    prev_den, den = 1, 0
    convergents = []
    for q in quotients:
        prev_num, num = num, q * num + prev_num
        prev_den, den = den, q * den + prev_den
        convergents.append((num, den))
    return convergents


def recover_period_from_measurement(measurement: int, register_size: int, a: int, modulus: int) -> Optional[int]:
    if measurement == 0:
        return None
    for _, denominator in continued_fraction_convergents(measurement, register_size):
        if denominator == 0:
            continue
        for multiplier in range(1, modulus + 1):
            candidate = denominator * multiplier
            if pow(a, candidate, modulus) == 1:
                return candidate
    return None


def simulate_quantum_measurement(order: int, register_size: int, rng: Random) -> int:
    numerator = rng.randrange(1, order)
    return int(round(numerator * register_size / order)) % register_size


def extract_factors(number: int, witness: int, order: int) -> Optional[Tuple[int, int]]:
    if order % 2 == 1:
        return None
    midpoint = pow(witness, order // 2, number)
    if midpoint in (1, number - 1):
        return None
    factor_a = gcd(midpoint - 1, number)
    factor_b = gcd(midpoint + 1, number)
    if 1 < factor_a < number and 1 < factor_b < number:
        return tuple(sorted((factor_a, factor_b)))
    return None


def candidate_witnesses(number: int, max_order: int = 18) -> List[int]:
    useful = []
    shortcuts = []
    for witness in range(2, number):
        divisor = gcd(witness, number)
        if 1 < divisor < number:
            shortcuts.append(witness)
            continue
        order = multiplicative_order(witness, number)
        if order is None or order % 2 == 1 or order > max_order:
            continue
        if extract_factors(number, witness, order) is not None:
            useful.append(witness)
    return useful + shortcuts or [2]


def build_recovery_candidates(measurement: Optional[int], register_size: int, witness: int, number: int) -> list[dict]:
    if measurement is None:
        return []

    candidates = []
    seen = set()
    for numerator, denominator in continued_fraction_convergents(measurement, register_size):
        if denominator == 0 or denominator in seen:
            continue
        seen.add(denominator)
        matches = []
        for multiplier in range(1, number + 1):
            candidate = denominator * multiplier
            if pow(witness, candidate, number) == 1:
                matches.append(candidate)
                if len(matches) >= 3:
                    break
        candidates.append(
            {
                "fraction": f"{numerator}/{denominator}",
                "denominator": denominator,
                "matches": matches,
            }
        )
    return candidates
