"""Validate filters before generating SQL."""

import json
from pathlib import Path


class SchemaValidator:
    def __init__(self):
        project_root = Path(__file__).resolve().parents[1]
        schema_path = project_root / "data" / "schema.json"

        with open(schema_path, encoding="utf-8") as file:
            self.schema = json.load(file)

        self.valid_cities = set(self.schema["valid_cities"])

    def validate_query(self, filters):
        errors = []

        if "city" in filters:
            if filters["city"] not in self.valid_cities:
                errors.append(
                    f"City '{filters['city']}' not found"
                )

        for price_field in ["price_min", "price_max"]:
            if price_field in filters:
                price = filters[price_field]

                if price < 100000 or price > 10000000:
                    errors.append(
                        f"Price {price} outside typical range"
                    )

        for bedroom_field in ["bedrooms", "bedrooms_min"]:
            if bedroom_field in filters:
                bedrooms = filters[bedroom_field]

                if bedrooms < 1 or bedrooms > 10:
                    errors.append(
                        f"Bedroom count {bedrooms} seems invalid"
                    )

        for bathroom_field in ["bathrooms", "bathrooms_min"]:
            if bathroom_field in filters:
                bathrooms = filters[bathroom_field]

                if bathrooms < 0 or bathrooms > 10:
                    errors.append(
                        f"Bathroom count {bathrooms} seems invalid"
                    )

        return len(errors) == 0, errors
