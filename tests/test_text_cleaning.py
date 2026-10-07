import pytest

from scripts.text_cleaning import TextCleaner


cleaner = TextCleaner()


@pytest.mark.parametrize(
    "original, expected",
    [
        ("priced at 450k", "priced at 450000"),
        ("a $1.2m home", "a 1200000 home"),
        ("listed for 900K", "listed for 900000"),
    ],
)
def test_normalize_prices(original, expected):
    assert cleaner.normalize_prices(original) == expected
