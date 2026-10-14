"""Create a 200-record dataset with entity spans."""

import json
import re
from pathlib import Path

import pandas as pd


def overlaps_existing(start, end, entities):
    """Check whether a new span overlaps an existing span."""
    return any(
        start < entity["end"]
        and end > entity["start"]
        for entity in entities
    )


def add_pattern_matches(text, pattern, label, entities):
    """Add all non-overlapping regex matches."""
    for match in re.finditer(
        pattern,
        text,
        flags=re.IGNORECASE,
    ):
        start = match.start()
        end = match.end()

        if not overlaps_existing(start, end, entities):
            entities.append(
                {
                    "start": start,
                    "end": end,
                    "label": label,
                    "text": text[start:end],
                }
            )


def main():
    project_root = Path(__file__).resolve().parents[1]

    input_file = (
        project_root
        / "data"
        / "processed"
        / "entity_labeling_template.csv"
    )

    output_file = (
        project_root
        / "data"
        / "processed"
        / "labeled_entities.jsonl"
    )

    df = pd.read_csv(input_file)

    bedroom_pattern = (
        r"\b(?:\d+|one|two|three|four|five|six|"
        r"seven|eight|nine|ten)"
        r"\s*-?\s*(?:bedroom|bed|br|bd)s?\b"
    )

    bathroom_pattern = (
        r"\b(?:\d+(?:\.\d+)?|one|two|three|four|"
        r"five|six|seven|eight|nine|ten)"
        r"(?:\s*(?:-| )\s*1/2|"
        r"\s+and\s+(?:a\s+)?half)?"
        r"\s*-?\s*(?:bathroom|bath|ba)s?\b"
    )

    sqft_pattern = (
        r"\b\d[\d,]*\s*"
        r"(?:square feet|sqft|sq\.?\s*ft\.?)\b"
    )

    records = []

    for _, row in df.head(200).iterrows():
        text = row["cleaned_remarks"]
        entities = []

        add_pattern_matches(
            text,
            bedroom_pattern,
            "BEDROOM",
            entities,
        )

        add_pattern_matches(
            text,
            bathroom_pattern,
            "BATHROOM",
            entities,
        )

        add_pattern_matches(
            text,
            sqft_pattern,
            "SQFT",
            entities,
        )

        gold_amenities = row["gold_amenities"]

        if pd.isna(gold_amenities):
            amenities = []
        else:
            amenities = json.loads(gold_amenities)

        amenities = sorted(
            amenities,
            key=lambda item: len(item["term"]),
            reverse=True,
        )

        for amenity in amenities:
            term = amenity["term"]

            pattern = (
                r"(?<!\w)"
                + re.escape(term)
                + r"(?!\w)"
            )

            add_pattern_matches(
                text,
                pattern,
                "AMENITY",
                entities,
            )

        entities.sort(
            key=lambda entity: entity["start"]
        )

        records.append(
            {
                "listing_id": str(row["L_ListingID"]),
                "text": text,
                "entities": entities,
            }
        )

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:
        for record in records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print("Records created:", len(records))
    print("Saved to:", output_file)


if __name__ == "__main__":
    main()
