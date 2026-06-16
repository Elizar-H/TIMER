import re


def normalize_game_search_text(text):
    return re.sub(r"[\u00a0\u202f\u2007]+", " ", str(text)).strip()
