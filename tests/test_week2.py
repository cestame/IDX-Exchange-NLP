import pandas as pd
import pytest

from scripts.text_cleaning import TextCleaner


cleaner = TextCleaner()


@pytest.mark.parametrize(
    "original, expected",
    [
        ("priced at 450k", "priced at 450000"),
        ("$1.2m home", "1200000 home"),
        ("listed for 900K", "listed for 900000"),
        ("worth 2M", "worth 2000000"),
        ("price is 1.25m", "price is 1250000"),
        ("asking $750 k", "asking 750000"),
        ("no price listed", "no price listed"),
    ],
)
def test_price_normalization(original, expected):
    result = cleaner.normalize_prices(original)
    assert result == expected


def test_profiling():
    df = pd.read_csv("data/processed/listing_sample.csv")

    profile = cleaner.profile_column(df, "remarks")

    assert "null_rate" in profile
    assert "avg_length" in profile
    assert "common_terms" in profile
    assert "price_mentions" in profile
    assert "has_html" in profile
    assert "common_abbreviations" in profile

@pytest.mark.parametrize(
    "original, expected",
    [
        ("2,000 sqft", "2000 square feet"),
        ("950 sq ft", "950 square feet"),
        ("1,500 sq. ft.", "1500 square feet"),
        ("800 SQFT", "800 square feet"),
        ("500 sf", "500 square feet"),
        ("2,250 SF", "2250 square feet"),
        ("no measurement", "no measurement"),
    ],
)
def test_measurement_normalization(original, expected):
    result = cleaner.normalize_measurements(original)
    assert result == expected

@pytest.mark.parametrize(
    "original, expected",
    [
        ("3 BR home", "3 bedroom home"),
        ("2 BA condo", "2 bathroom condo"),
        ("home w/ pool", "home with pool"),
        ("unit w/o garage", "unit without garage"),
        ("A/C included", "air conditioning included"),
        ("HOA amenities", "homeowners association amenities"),
        ("EV charger", "electric vehicle charger"),
        ("private ADU", "private accessory dwelling unit"),
    ],
)
def test_abbreviation_expansion(original, expected):
    result = cleaner.expand_abbreviations(original)
    assert result == expected

@pytest.mark.parametrize(
    "original, expected",
    [
        ("It’s beautiful", "It's beautiful"),
        ("‘Welcome home’", "'Welcome home'"),
        ("“Ocean view”", '"Ocean view"'),
        ("open–concept", "open-concept"),
        ("indoor—outdoor", "indoor-outdoor"),
        ("Wait…there's more", "Wait...there's more"),
        ("home\u00a0with pool", "home with pool"),
        ("cafÃ©s nearby", "cafés nearby"),
    ],
)
def test_unicode_normalization(original, expected):
    result = cleaner.normalize_unicode(original)
    assert result == expected

@pytest.mark.parametrize(
    "original, expected",
    [
        ("extra   spaces", "extra spaces"),
        ("line one\nline two", "line one line two"),
        ("tabs\tbetween\twords", "tabs between words"),
        ("  spaces outside  ", "spaces outside"),
        ("already clean", "already clean"),
    ],
)
def test_whitespace_normalization(original, expected):
    result = cleaner.normalize_whitespace(original)
    assert result == expected

@pytest.mark.parametrize(
    "original, expected",
    [
        (
            "3 BR home w/ 2,000 sqft and A/C",
            "3 bedroom home with 2000 square feet and air conditioning",
        ),
        (
            "<p>$1.2m home</p>",
            "1200000 home",
        ),
        (
            "Beautiful\u00a0home   w/ pool",
            "Beautiful home with pool",
        ),
        (
            "HOA includes   EV charging",
            "homeowners association includes electric vehicle charging",
        ),
        (
            "2 BA condo\nwith 950 sq ft",
            "2 bathroom condo with 950 square feet",
        ),
    ],
)
def test_complete_pipeline(original, expected):
    result = cleaner.clean_text(original)
    assert result == expected