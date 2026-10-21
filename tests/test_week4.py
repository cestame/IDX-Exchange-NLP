"""Tests for the Week 4 query parser."""

import pytest

from scripts.query_parser import QueryParser
from scripts.schema_validator import SchemaValidator


parser = QueryParser()
validator = SchemaValidator()


# --------------------------------------------------
# Price parsing: 16 query examples
# --------------------------------------------------

PRICE_CASES = [
    ("under 700k", "price_max", 700000),
    ("below 500k", "price_max", 500000),
    ("less than 1.2m", "price_max", 1200000),
    ("under $850000", "price_max", 850000),
    ("under $850,000", "price_max", 850000),
    ("up to $900000", "price_max", 900000),
    ("at most 750k", "price_max", 750000),
    ("max $600000", "price_max", 600000),
    ("over 500k", "price_min", 500000),
    ("above $700000", "price_min", 700000),
    ("more than 1.1m", "price_min", 1100000),
    ("at least $800000", "price_min", 800000),
    ("minimum 900k", "price_min", 900000),
    ("min $400000", "price_min", 400000),
    ("between 500k and 800k", "price_min", 500000),
    ("from $600000 to $900000", "price_max", 900000),
]


@pytest.mark.parametrize(
    "query,key,expected",
    PRICE_CASES,
)
def test_price_queries(query, key, expected):
    filters = parser.parse(query)

    assert filters[key] == expected


# --------------------------------------------------
# Bedroom parsing: 12 query examples
# --------------------------------------------------

BEDROOM_CASES = [
    ("3 bed", "bedrooms", 3),
    ("4 beds", "bedrooms", 4),
    ("2 bedroom", "bedrooms", 2),
    ("5 bedrooms", "bedrooms", 5),
    ("3 br", "bedrooms", 3),
    ("3+ bed", "bedrooms_min", 3),
    ("4+ bedrooms", "bedrooms_min", 4),
    ("at least 3 bedrooms", "bedrooms_min", 3),
    ("minimum 2 bed", "bedrooms_min", 2),
    ("min 4 br", "bedrooms_min", 4),
    ("up to 4 bedrooms", "bedrooms_max", 4),
    ("at most 5 beds", "bedrooms_max", 5),
]


@pytest.mark.parametrize(
    "query,key,expected",
    BEDROOM_CASES,
)
def test_bedroom_queries(query, key, expected):
    filters = parser.parse(query)

    assert filters[key] == expected


# --------------------------------------------------
# Bathroom parsing: 12 query examples
# --------------------------------------------------

BATHROOM_CASES = [
    ("2 bath", "bathrooms", 2.0),
    ("3 baths", "bathrooms", 3.0),
    ("2 bathroom", "bathrooms", 2.0),
    ("4 bathrooms", "bathrooms", 4.0),
    ("2 ba", "bathrooms", 2.0),
    ("2.5 baths", "bathrooms", 2.5),
    ("2+ bathrooms", "bathrooms_min", 2.0),
    ("at least 2 bathrooms", "bathrooms_min", 2.0),
    ("minimum 1.5 baths", "bathrooms_min", 1.5),
    ("min 2 ba", "bathrooms_min", 2.0),
    ("up to 3 bathrooms", "bathrooms_max", 3.0),
    ("at most 2.5 baths", "bathrooms_max", 2.5),
]


@pytest.mark.parametrize(
    "query,key,expected",
    BATHROOM_CASES,
)
def test_bathroom_queries(query, key, expected):
    filters = parser.parse(query)

    assert filters[key] == expected


# --------------------------------------------------
# City parsing: 5 query examples
# --------------------------------------------------

CITY_CASES = [
    ("homes in Irvine", "Irvine"),
    ("property in Anaheim", "Anaheim"),
    (
        "3 bed in Beverly Hills under 2m",
        "Beverly Hills",
    ),
    (
        "home in San Clemente with community pool",
        "San Clemente",
    ),
    (
        "house in 29 Palms under 500k",
        "29 Palms",
    ),
]


@pytest.mark.parametrize(
    "query,expected",
    CITY_CASES,
)
def test_city_queries(query, expected):
    filters = parser.parse(query)

    assert filters["city"] == expected


# --------------------------------------------------
# Amenities and negation: 5 query examples
# --------------------------------------------------

AMENITY_CASES = [
    (
        "home with community pool",
        "amenities",
        "community pool",
    ),
    (
        "home with walk-in closet",
        "amenities",
        "walk-in closet",
    ),
    (
        "home with granite countertops",
        "amenities",
        "granite countertops",
    ),
    (
        "home without community pool",
        "excluded_amenities",
        "community pool",
    ),
    (
        "home without walk-in closet",
        "excluded_amenities",
        "walk-in closet",
    ),
]


@pytest.mark.parametrize(
    "query,key,expected",
    AMENITY_CASES,
)
def test_amenity_queries(query, key, expected):
    filters = parser.parse(query)

    assert expected in filters[key]


# --------------------------------------------------
# Combined query
# --------------------------------------------------

def test_combined_query():
    filters = parser.parse(
        "3 bed in Irvine with community pool under 700k"
    )

    assert filters["bedrooms"] == 3
    assert filters["city"] == "Irvine"
    assert filters["price_max"] == 700000
    assert "community pool" in filters["amenities"]


# --------------------------------------------------
# Regression test for walk-in/city bug
# --------------------------------------------------

def test_walk_in_is_not_a_city():
    filters = parser.parse(
        "home with walk-in closet and granite countertops"
    )

    assert "city" not in filters
    assert "walk-in closet" in filters["amenities"]


# --------------------------------------------------
# Parameterized SQL
# --------------------------------------------------

def test_parameterized_sql():
    filters = parser.parse(
        "3 bed in Irvine under 700k"
    )

    sql, params = parser.to_sql(filters)

    # Values must not be inserted into the SQL string.
    assert "700000" not in sql
    assert "Irvine" not in sql

    # SQL should contain placeholders.
    assert "%s" in sql

    # Values should be stored separately.
    assert 700000 in params
    assert 3 in params
    assert "Irvine" in params


# --------------------------------------------------
# SQL injection protection
# --------------------------------------------------

def test_sql_injection_stays_out_of_sql():
    dangerous_city = (
        "Irvine'; DROP TABLE rets_property; --"
    )

    filters = {
        "city": dangerous_city
    }

    sql, params = parser.to_sql(filters)

    # The dangerous text must not be inside the SQL.
    assert "DROP TABLE" not in sql

    # It remains a parameter and is treated as data.
    assert dangerous_city in params


# --------------------------------------------------
# Schema validation
# --------------------------------------------------

def test_valid_query():
    filters = parser.parse(
        "3 bed in Irvine under 700k"
    )

    valid, errors = validator.validate_query(filters)

    assert valid is True
    assert errors == []


def test_invalid_city():
    valid, errors = validator.validate_query(
        {
            "city": "Fakeville"
        }
    )

    assert valid is False
    assert len(errors) > 0


def test_invalid_price():
    valid, errors = validator.validate_query(
        {
            "price_max": 50000
        }
    )

    assert valid is False
    assert len(errors) > 0


def test_invalid_bedrooms():
    valid, errors = validator.validate_query(
        {
            "bedrooms": 15
        }
    )

    assert valid is False
    assert len(errors) > 0


def test_invalid_bathrooms():
    valid, errors = validator.validate_query(
        {
            "bathrooms": 20
        }
    )

    assert valid is False
    assert len(errors) > 0
