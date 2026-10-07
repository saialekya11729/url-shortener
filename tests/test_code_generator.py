import pytest

from app.utils.code_generator import ALPHABET, generate_short_code


def test_generate_short_code_default_length_is_six():
    assert len(generate_short_code()) == 6


def test_generate_short_code_custom_length():
    assert len(generate_short_code(12)) == 12


def test_generate_short_code_uses_url_safe_alphanumeric_characters():
    code = generate_short_code(200)

    assert set(code).issubset(set(ALPHABET))
    assert code.isalnum()


def test_generate_short_code_rejects_zero_length():
    with pytest.raises(ValueError):
        generate_short_code(0)


def test_generate_short_code_has_low_collision_rate_for_sample():
    codes = {generate_short_code() for _ in range(500)}

    assert len(codes) > 490

