import secrets
import string


ALPHABET = string.ascii_letters + string.digits


def generate_short_code(length: int = 6) -> str:
    if length < 1:
        raise ValueError("Short code length must be positive.")
    return "".join(secrets.choice(ALPHABET) for _ in range(length))

