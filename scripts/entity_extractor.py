import re
from pathlib import Path
import json

class EntityExtractor:
    def __init__(self):
        project_root = Path(__file__).resolve().parents[1]
        taxonomy_file = (
            project_root
            / "data"
            / "processed"
            / "taxonomy.json"
        )

        with open(
            taxonomy_file,
            encoding="utf-8",
        ) as file:
            taxonomy = json.load(file)

        self.taxonomy_terms = taxonomy["terms"]

    def extract_bedrooms(self, text):
            patterns = [
                r"\b(\d+)\s*-?\s*(?:bedroom|bed|br|bd)s?\b",
            ]

            for pattern in patterns:
                match = re.search(pattern, text, re.I)

                if match:
                    return int(match.group(1))

            return None

    def extract_sqft(self, text):
        """Extract square footage from listing text."""
        if not isinstance(text, str):
            return None

        patterns = [
            r"\b(\d[\d,]*)\s*square feet\b",
            r"\b(\d[\d,]*)\s*(?:sqft|sq\.?\s*ft\.?)\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.I)

            if match:
                sqft = match.group(1).replace(",", "")
                return int(sqft)

        return None
    
    def extract_prices(self, text):
        # Assumes cleaned text from Week 2
        match = re.search(r'\$?(\d{5,})', text)
        return int(match.group(1)) if match else None

    def extract_bathrooms(self, text):
        patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:bath|bathroom)s?",
            r"(\d+(?:\.\d+)?)\s*ba\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return float(match.group(1))
        return None

    def extract_amenities(self, text):
        if not isinstance(text, str):
            return []

        matches = []

        for item in self.taxonomy_terms:
            term = item["term"]

            pattern = (
                r"(?<!\w)"
                + re.escape(term)
                + r"(?!\w)"
            )

            if re.search(pattern, text, re.I):
                matches.append(
                    {
                        "term": term,
                        "category": item["category"],
                    }
                )

        return matches
    def extract_all(self, text):
        return {
            'bedrooms': self.extract_bedrooms(text),
            'bathrooms': self.extract_bathrooms(text),
            'price': self.extract_prices(text),
            'sqft': self.extract_sqft(text),
            'amenities': self.extract_amenities(text)
        }

 