"""Convert natural-language real-estate queries into safe SQL."""

import json
import re
from pathlib import Path


class QueryParser:

    def __init__(self):
        project_root = Path(__file__).resolve().parents[1]

        # Load the Week 1 taxonomy.
        taxonomy_path = (
            project_root
            / "data"
            / "processed"
            / "taxonomy.json"
        )

        with open(taxonomy_path, encoding="utf-8") as file:
            taxonomy = json.load(file)

        # Load valid cities.
        schema_path = project_root / "data" / "schema.json"

        with open(schema_path, encoding="utf-8") as file:
            schema = json.load(file)

        self.valid_cities = sorted(
            schema["valid_cities"],
            key=len,
            reverse=True,
        )

        # Use relevant taxonomy categories as searchable features.
        searchable_categories = {
            "interior",
            "interior_features",
            "exterior",
            "exterior_features",
            "utilities",
            "community_amenities",
            "location",
            "condition",
        }

        self.feature_aliases = {}

        for item in taxonomy["terms"]:
            if item["category"] not in searchable_categories:
                continue

            term = item["term"].lower().strip()

            term = re.sub(
                r"^(?:a|an|the)\s+",
                "",
                term,
            )

            self.feature_aliases[term] = term

        # Common phrases found in the Week 1 queries.
        self.feature_aliases.update({
            "swimming pools": "pool",
            "swimming pool": "pool",
            "pools": "pool",
            "pool": "pool",
            "private pool": "private pool",

            "mountain views": "mountain view",
            "mountain view": "mountain view",
            "ocean views": "ocean view",
            "ocean view": "ocean view",
            "waterfront": "waterfront",

            "near the beach": "near beach",
            "near beach": "near beach",
            "near shopping": "near shopping",
            "near downtown": "near downtown",
            "downtown": "near downtown",

            "large backyards": "large backyard",
            "large backyard": "large backyard",
            "larger lots": "large lot",
            "large lots": "large lot",
            "large lot": "large lot",

            "gated communities": "gated community",
            "gated community": "gated community",

            "home offices": "home office",
            "home office": "home office",

            "open floor plans": "open floor plan",
            "open floor plan": "open floor plan",

            "community fitness centers": "fitness center",
            "community fitness center": "fitness center",
            "fitness centers": "fitness center",
            "fitness center": "fitness center",

            "outdoor kitchens": "outdoor kitchen",
            "outdoor kitchen": "outdoor kitchen",

            "hardwood floors": "hardwood floors",
            "hardwood flooring": "hardwood floors",

            "three-car garages": "three-car garage",
            "three-car garage": "three-car garage",
            "3-car garages": "three-car garage",
            "3-car garage": "three-car garage",

            "two-car garages": "two-car garage",
            "two-car garage": "two-car garage",
            "2-car garages": "two-car garage",
            "2-car garage": "two-car garage",

            "updated kitchens": "updated kitchen",
            "updated kitchen": "updated kitchen",

            "solar panels": "solar panels",
            "solar panel": "solar panels",
            "solar": "solar panels",

            "tennis courts": "tennis courts",
            "tennis court": "tennis courts",

            "walking trails": "walking trails",
            "walking trail": "walking trails",
            "hiking trails": "hiking trails",
            "hiking trail": "hiking trails",

            "highly rated schools": "highly rated schools",
            "rated schools": "highly rated schools",

            "public transportation": "public transit",
            "public transit": "public transit",

            "septic systems": "septic system",
            "septic system": "septic system",
            "public sewer": "public sewer",

            "assigned parking": "assigned parking",
            "guest suite": "guest suite",
            "fenced yard": "fenced yard",
        })

        # Property types found in the Week 1 queries.
        self.property_type_map = {
            "condominiums": "condo",
            "condominium": "condo",
            "condos": "condo",
            "condo": "condo",

            "townhouses": "townhouse",
            "townhouse": "townhouse",
            "townhomes": "townhouse",
            "townhome": "townhouse",

            "single-story homes": "single-story",
            "single-story home": "single-story",
            "single story homes": "single-story",
            "single story home": "single-story",

            "two-story homes": "two-story",
            "two-story home": "two-story",
            "two story homes": "two-story",
            "two story home": "two-story",

            "single-family homes": "single-family",
            "single-family home": "single-family",
        }

        # Listing condition and status.
        self.status_aliases = {
            "move-in ready": "move-in ready",
            "move in ready": "move-in ready",
            "newly listed": "newly listed",
            "new construction": "new construction",
            "newer construction": "newer construction",
            "open houses": "open house",
            "open house": "open house",
            "ready for immediate move-in": "immediate move-in",
            "immediate move-in": "immediate move-in",
        }

        # Time and availability phrases.
        self.availability_aliases = {
            "this weekend": "this weekend",
            "this saturday": "Saturday",
            "saturday": "Saturday",
            "tomorrow": "tomorrow",
            "available now": "available now",
            "this week": "this week",
            "available for viewing": "available for viewing",
        }

    def _normalize_number_words(self, query):
        """Convert number words into digits."""
        number_words = {
            "one": "1",
            "two": "2",
            "three": "3",
            "four": "4",
            "five": "5",
            "six": "6",
            "seven": "7",
            "eight": "8",
            "nine": "9",
            "ten": "10",
        }

        for word, number in number_words.items():
            query = re.sub(
                rf"\b{word}\b",
                number,
                query,
                flags=re.I,
            )

        return query

    def _parse_number(self, number, unit=""):
        """Convert values such as 700k and 1.2m."""
        value = float(number.replace(",", ""))
        unit = unit.lower()

        if unit == "k":
            value *= 1_000
        elif unit == "m":
            value *= 1_000_000

        return int(value)

    def _phrase_matches(self, phrase, query):
        """Check for a complete phrase in a query."""
        pattern = (
            r"(?<!\w)"
            + re.escape(phrase)
            + r"(?!\w)"
        )

        return list(
            re.finditer(
                pattern,
                query,
                re.I,
            )
        )

    def _is_negated(self, query, match_start):
        """Check whether a phrase follows no or without."""
        prefix = query[
            max(0, match_start - 25):match_start
        ]

        return bool(
            re.search(
                r"(?:\bno|\bwithout)"
                r"(?:\s+(?:a|an|the))?\s*$",
                prefix,
                re.I,
            )
        )

    def parse(self, query):
        """Convert a natural-language query into filters."""
        filters = {}

        if not isinstance(query, str):
            return filters

        query = self._normalize_number_words(query)

        # -----------------------------------
        # Price range
        # -----------------------------------

        match = re.search(
            r"(?:between|from)\s+"
            r"\$?([\d,.]+)\s*([km]?)"
            r"\s+(?:and|to)\s+"
            r"\$?([\d,.]+)\s*([km]?)",
            query,
            re.I,
        )

        if match:
            filters["price_min"] = self._parse_number(
                match.group(1),
                match.group(2),
            )

            filters["price_max"] = self._parse_number(
                match.group(3),
                match.group(4),
            )

        else:
            match = re.search(
                r"(?:under|below|less than)\s+"
                r"\$?([\d,.]+)\s*([km]?)",
                query,
                re.I,
            )

            if match:
                filters["price_max"] = self._parse_number(
                    match.group(1),
                    match.group(2),
                )

            else:
                match = re.search(
                    r"(?:up to|at most|max)\s+"
                    r"(?:\$([\d,.]+)\s*([km]?)|"
                    r"([\d,.]+)\s*([km]))\b",
                    query,
                    re.I,
                )

                if match:
                    number = (
                        match.group(1)
                        or match.group(3)
                    )

                    unit = (
                        match.group(2)
                        or match.group(4)
                        or ""
                    )

                    filters["price_max"] = (
                        self._parse_number(number, unit)
                    )

            match = re.search(
                r"(?:over|above|more than)\s+"
                r"\$?([\d,.]+)\s*([km]?)",
                query,
                re.I,
            )

            if match:
                filters["price_min"] = self._parse_number(
                    match.group(1),
                    match.group(2),
                )

            else:
                match = re.search(
                    r"(?:at least|minimum|min)\s+"
                    r"(?:\$([\d,.]+)\s*([km]?)|"
                    r"([\d,.]+)\s*([km]))\b",
                    query,
                    re.I,
                )

                if match:
                    number = (
                        match.group(1)
                        or match.group(3)
                    )

                    unit = (
                        match.group(2)
                        or match.group(4)
                        or ""
                    )

                    filters["price_min"] = (
                        self._parse_number(number, unit)
                    )

        # -----------------------------------
        # Bedrooms
        # -----------------------------------

        match = re.search(
            r"(?:at least|minimum|min)\s+"
            r"(\d+)\s*-?\s*"
            r"(?:bed|beds|bedroom|bedrooms|br)\b",
            query,
            re.I,
        )

        if match:
            filters["bedrooms_min"] = int(
                match.group(1)
            )

        else:
            match = re.search(
                r"(\d+)\s*(\+)?\s*-?\s*"
                r"(?:bed|beds|bedroom|bedrooms|br)\b",
                query,
                re.I,
            )

            if match:
                value = int(match.group(1))

                if match.group(2):
                    filters["bedrooms_min"] = value
                else:
                    filters["bedrooms"] = value

        match = re.search(
            r"(?:up to|at most|max)\s+"
            r"(\d+)\s*-?\s*"
            r"(?:bed|beds|bedroom|bedrooms|br)\b",
            query,
            re.I,
        )

        if match:
            filters.pop("bedrooms", None)
            filters["bedrooms_max"] = int(
                match.group(1)
            )

        # -----------------------------------
        # Bathrooms
        # -----------------------------------

        match = re.search(
            r"(?:at least|minimum|min)\s+"
            r"(\d+(?:\.\d+)?)\s*-?\s*"
            r"(?:bath|baths|bathroom|bathrooms|ba)\b",
            query,
            re.I,
        )

        if match:
            filters["bathrooms_min"] = float(
                match.group(1)
            )

        else:
            match = re.search(
                r"(\d+(?:\.\d+)?)\s*(\+)?\s*-?\s*"
                r"(?:bath|baths|bathroom|bathrooms|ba)\b",
                query,
                re.I,
            )

            if match:
                value = float(match.group(1))

                if match.group(2):
                    filters["bathrooms_min"] = value
                else:
                    filters["bathrooms"] = value

        match = re.search(
            r"(?:up to|at most|max)\s+"
            r"(\d+(?:\.\d+)?)\s*-?\s*"
            r"(?:bath|baths|bathroom|bathrooms|ba)\b",
            query,
            re.I,
        )

        if match:
            filters.pop("bathrooms", None)
            filters["bathrooms_max"] = float(
                match.group(1)
            )

        # -----------------------------------
        # Cities
        # -----------------------------------

        found_cities = []

        for city in self.valid_cities:
            pattern = (
                r"(?<!\w)"
                + re.escape(city)
                + r"(?!\w)"
            )

            if re.search(pattern, query, re.I):
                if city not in found_cities:
                    found_cities.append(city)

        if len(found_cities) == 1:
            filters["city"] = found_cities[0]

        elif len(found_cities) > 1:
            filters["cities"] = found_cities

        # -----------------------------------
        # Property types
        # -----------------------------------

        property_types = []

        for phrase, property_type in (
            self.property_type_map.items()
        ):
            if self._phrase_matches(phrase, query):
                if property_type not in property_types:
                    property_types.append(
                        property_type
                    )

        if property_types:
            filters["property_types"] = (
                property_types
            )

        # -----------------------------------
        # Amenities and negation
        # -----------------------------------

        included = []
        excluded = []
        occupied_spans = []

        sorted_aliases = sorted(
            self.feature_aliases,
            key=len,
            reverse=True,
        )

        for phrase in sorted_aliases:
            feature = self.feature_aliases[phrase]

            for match in self._phrase_matches(
                phrase,
                query,
            ):
                span = match.span()

                overlaps = any(
                    span[0] < used_end
                    and span[1] > used_start
                    for used_start, used_end
                    in occupied_spans
                )

                if overlaps:
                    continue

                occupied_spans.append(span)

                if self._is_negated(
                    query,
                    match.start(),
                ):
                    if feature not in excluded:
                        excluded.append(feature)
                else:
                    if feature not in included:
                        included.append(feature)

        if included:
            filters["amenities"] = included

        if excluded:
            filters["excluded_amenities"] = excluded

        # -----------------------------------
        # HOA preferences
        # -----------------------------------

        if re.search(
            r"\b(?:no|without)\s+hoa\b",
            query,
            re.I,
        ):
            filters["hoa"] = "none"

        elif re.search(
            r"\b(?:low|lower|lowest)\s+hoa\b",
            query,
            re.I,
        ):
            filters["hoa"] = "low"

        # -----------------------------------
        # Listing status
        # -----------------------------------

        statuses = []

        for phrase, status in (
            self.status_aliases.items()
        ):
            if self._phrase_matches(phrase, query):
                if status not in statuses:
                    statuses.append(status)

        if statuses:
            filters["listing_status"] = statuses

        # -----------------------------------
        # Availability
        # -----------------------------------

        availability = []

        for phrase, value in (
            self.availability_aliases.items()
        ):
            if self._phrase_matches(phrase, query):
                if value not in availability:
                    availability.append(value)

        if availability:
            filters["availability"] = availability

        # -----------------------------------
        # Research operations
        # -----------------------------------

        if re.search(
            r"\bcompare\b",
            query,
            re.I,
        ):
            filters["operation"] = "compare"

        elif re.search(
            r"\baverage\b",
            query,
            re.I,
        ):
            filters["operation"] = "average"

        return filters

    def to_sql(self, filters):
        """Convert filters into parameterized SQL."""
        conditions = []
        params = []

        if "price_min" in filters:
            conditions.append(
                "L_SystemPrice >= %s"
            )
            params.append(filters["price_min"])

        if "price_max" in filters:
            conditions.append(
                "L_SystemPrice <= %s"
            )
            params.append(filters["price_max"])

        if "bedrooms" in filters:
            conditions.append(
                "L_Keyword2 = %s"
            )
            params.append(filters["bedrooms"])

        if "bedrooms_min" in filters:
            conditions.append(
                "L_Keyword2 >= %s"
            )
            params.append(filters["bedrooms_min"])

        if "bedrooms_max" in filters:
            conditions.append(
                "L_Keyword2 <= %s"
            )
            params.append(filters["bedrooms_max"])

        if "bathrooms" in filters:
            conditions.append(
                "L_Keyword3 = %s"
            )
            params.append(filters["bathrooms"])

        if "bathrooms_min" in filters:
            conditions.append(
                "L_Keyword3 >= %s"
            )
            params.append(filters["bathrooms_min"])

        if "bathrooms_max" in filters:
            conditions.append(
                "L_Keyword3 <= %s"
            )
            params.append(filters["bathrooms_max"])

        if "city" in filters:
            conditions.append(
                "L_City = %s"
            )
            params.append(filters["city"])

        if "cities" in filters:
            city_conditions = []

            for city in filters["cities"]:
                city_conditions.append(
                    "L_City = %s"
                )
                params.append(city)

            conditions.append(
                "("
                + " OR ".join(city_conditions)
                + ")"
            )

        for amenity in filters.get(
            "amenities",
            [],
        ):
            conditions.append(
                "L_Remarks LIKE %s"
            )
            params.append(f"%{amenity}%")

        for amenity in filters.get(
            "excluded_amenities",
            [],
        ):
            conditions.append(
                "L_Remarks NOT LIKE %s"
            )
            params.append(f"%{amenity}%")

        property_types = filters.get(
            "property_types",
            [],
        )

        if property_types:
            type_conditions = []

            for property_type in property_types:
                type_conditions.append(
                    "L_Remarks LIKE %s"
                )
                params.append(
                    f"%{property_type}%"
                )

            conditions.append(
                "("
                + " OR ".join(type_conditions)
                + ")"
            )

        if filters.get("hoa") == "none":
            conditions.append(
                "L_Remarks LIKE %s"
            )
            params.append("%no HOA%")

        elif filters.get("hoa") == "low":
            conditions.append(
                "L_Remarks LIKE %s"
            )
            params.append("%low HOA%")

        for status in filters.get(
            "listing_status",
            [],
        ):
            conditions.append(
                "L_Remarks LIKE %s"
            )
            params.append(f"%{status}%")

        for availability in filters.get(
            "availability",
            [],
        ):
            conditions.append(
                "L_Remarks LIKE %s"
            )
            params.append(f"%{availability}%")

        sql = "SELECT * FROM rets_property"

        if conditions:
            sql += " WHERE " + " AND ".join(
                conditions
            )

        return sql, params