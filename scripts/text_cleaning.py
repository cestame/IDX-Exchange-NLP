"""Week 2 text cleaning and normalization."""

import html
import re
import unicodedata
from collections import Counter


class TextCleaner:
    """Clean and standardize real-estate listing remarks."""

    def __init__(self):
        self.abbrev_map = {
            "br": "bedroom",
            "brs": "bedrooms",
            "ba": "bathroom",
            "bas": "bathrooms",
            "bdrm": "bedroom",
            "bdrms": "bedrooms",
            "bd": "bedroom",
            "bds": "bedrooms",
            "sqft": "square feet",
            "sq ft": "square feet",
            "sf": "square feet",
            "w/": "with",
            "w/o": "without",
            "mbr": "primary bedroom",
            "fp": "fireplace",
            "frpl": "fireplace",
            "gar": "garage",
            "a/c": "air conditioning",
            "ac": "air conditioning",
            "hvac": "heating and air conditioning",
            "kit": "kitchen",
            "kitch": "kitchen",
            "lr": "living room",
            "liv rm": "living room",
            "dr": "dining room",
            "din rm": "dining room",
            "fam rm": "family room",
            "w/d": "washer and dryer",
            "hoa": "homeowners association",
            "adu": "accessory dwelling unit",
            "ev": "electric vehicle",
            "rv": "recreational vehicle",
            "pvt": "private",
            "remod": "remodeled",
            "renov": "renovated",
            "upd": "updated",
            "ss": "stainless steel",
            "yr": "year",
            "yrs": "years",
        }

    def normalize_unicode(self, text):
        """Standardize Unicode characters."""
        if not isinstance(text, str):
            return ""

        text = unicodedata.normalize("NFC", text)

        replacements = {
            "’": "'",
            "‘": "'",
            "“": '"',
            "”": '"',
            "–": "-",
            "—": "-",
            "…": "...",
            "\u00a0": " ",
            "\u200b": "",
            "\u200c": "",
            "•": " ",
            "Ã©": "é",
        }

        for original, replacement in replacements.items():
            text = text.replace(original, replacement)

        return text

    def normalize_html(self, text):
        """Decode HTML entities and remove HTML tags."""
        if not isinstance(text, str):
            return ""

        text = html.unescape(text)
        text = re.sub(r"<[^>]+>", " ", text)

        return text

    def normalize_prices(self, text):
        """Convert abbreviated prices to complete numbers."""
        if not isinstance(text, str):
            return ""

        def convert_price(match):
            number = float(match.group(1))
            unit = match.group(2).lower()

            if unit == "k":
                number *= 1_000
            else:
                number *= 1_000_000

            return str(int(number))

        return re.sub(
            r"(?<!\w)\$?\s*(\d+(?:\.\d+)?)\s*([km])\b",
            convert_price,
            text,
            flags=re.IGNORECASE,
        )

    def normalize_measurements(self, text):
        """Convert square-foot abbreviations to 'square feet'."""
        if not isinstance(text, str):
            return ""

        def convert_measurement(match):
            number = match.group(1).replace(",", "")
            return f"{number} square feet"

        return re.sub(
            r"(\d[\d,]*(?:\.\d+)?)\s*"
            r"(?:sqft|sq\.?\s*ft\.?|sf)\.?",
            convert_measurement,
            text,
            flags=re.IGNORECASE,
        )

    def expand_abbreviations(self, text):
        """Expand common real-estate abbreviations."""
        if not isinstance(text, str):
            return ""

        abbreviations = sorted(
            self.abbrev_map,
            key=len,
            reverse=True,
        )

        for abbreviation in abbreviations:
            replacement = self.abbrev_map[abbreviation]

            pattern = (
                r"(?<!\w)"
                + re.escape(abbreviation)
                + r"(?!\w)"
            )

            text = re.sub(
                pattern,
                replacement,
                text,
                flags=re.IGNORECASE,
            )

        return text

    def normalize_whitespace(self, text):
        """Replace repeated whitespace with one space."""
        if not isinstance(text, str):
            return ""

        return re.sub(r"\s+", " ", text).strip()

    def clean_text(self, text):
        """Run the complete cleaning pipeline."""
        text = self.normalize_unicode(text)
        text = self.normalize_html(text)
        text = self.normalize_prices(text)
        text = self.normalize_measurements(text)
        text = self.expand_abbreviations(text)
        text = self.normalize_whitespace(text)

        return text

    def profile_column(self, df, column_name):
        """Analyze what needs cleaning in a text column."""
        column = df[column_name]
        text = column.fillna("").astype(str)

        return {
            "row_count": int(len(column)),
            "null_rate": float(column.isnull().mean()),
            "avg_length": float(
                column.dropna().astype(str).str.len().mean()
            ),
            "common_terms": self._extract_top_ngrams(column),
            "price_mentions": int(
                text.str.contains(
                    r"\$\s*\d|\b\d+(?:\.\d+)?[km]\b",
                    case=False,
                    regex=True,
                ).sum()
            ),
            "has_html": int(
                text.str.contains(
                    r"<[^>]+>",
                    regex=True,
                ).sum()
            ),
            "measurement_mentions": int(
                text.str.contains(
                    r"\b(?:sqft|sq\.?\s*ft\.?|sf)\b",
                    case=False,
                    regex=True,
                ).sum()
            ),
            "repeated_whitespace": int(
                text.str.contains(
                    r"\s{2,}",
                    regex=True,
                ).sum()
            ),
            "common_abbreviations":
                self._detect_abbreviations(column),
        }

    def _extract_top_ngrams(self, column):
        """Find the ten most common two-word phrases."""
        counts = Counter()

        for text in column.dropna():
            words = re.findall(
                r"\b[a-zA-Z]{2,}\b",
                str(text).lower(),
            )

            for first_word, second_word in zip(
                words,
                words[1:],
            ):
                phrase = f"{first_word} {second_word}"
                counts[phrase] += 1

        return counts.most_common(10)

    def _detect_abbreviations(self, column):
        """Count known abbreviations in a text column."""
        text = column.fillna("").astype(str)
        results = {}

        for abbreviation in self.abbrev_map:
            pattern = (
                r"(?<!\w)"
                + re.escape(abbreviation)
                + r"(?!\w)"
            )

            count = text.str.count(
                pattern,
                flags=re.IGNORECASE,
            ).sum()

            if count > 0:
                results[abbreviation] = int(count)

        return dict(
            sorted(
                results.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )