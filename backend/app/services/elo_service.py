from ..config import settings


def expected_score(rating_a: int, rating_b: int) -> float:
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def calculate_elo(rating_a: int, rating_b: int, score_a: float) -> tuple[int, int]:
    """score_a: 1.0 = A wins, 0.5 = draw, 0.0 = B wins. Returns (new_a, new_b)."""
    ea = expected_score(rating_a, rating_b)
    eb = 1.0 - ea
    new_a = round(rating_a + settings.ELO_K * (score_a - ea))
    new_b = round(rating_b + settings.ELO_K * ((1.0 - score_a) - eb))
    return (new_a, new_b)
