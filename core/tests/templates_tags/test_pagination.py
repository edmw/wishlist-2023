import pytest

from core.templates_tags.pagination import pagination_generate_indexes


def test_pagination_generate_indexes() -> None:
    assert pagination_generate_indexes(1, 1) == [1]
    assert pagination_generate_indexes(4, 1) == [1, 2, 3, 4]
    assert pagination_generate_indexes(4, 2) == [1, 2, 3, 4]
    assert pagination_generate_indexes(4, 3) == [1, 2, 3, 4]
    assert pagination_generate_indexes(4, 4) == [1, 2, 3, 4]
    assert pagination_generate_indexes(20, 1) == [1, 2, 3, -1, 20]
    assert pagination_generate_indexes(20, 2) == [1, 2, 3, 4, -1, 20]
    assert pagination_generate_indexes(20, 7) == [1, -1, 5, 6, 7, 8, 9, -1, 20]
    assert pagination_generate_indexes(20, 19) == [1, -1, 17, 18, 19, 20]


def test_pagination_generate_indexes_raises_on_string_input() -> None:
    with pytest.raises(ValueError, match="invalid literal"):
        pagination_generate_indexes("a", 1)
    with pytest.raises(ValueError, match="invalid literal"):
        pagination_generate_indexes(1, "b")
    with pytest.raises(ValueError, match="invalid literal"):
        pagination_generate_indexes("a", "b")
