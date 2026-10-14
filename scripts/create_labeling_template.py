"""Create a 200-row Week 3 labeling template."""

import json
from pathlib import Path
import pandas as pd

from scripts.entity_extractor import EntityExtractor


def main():
    project_root = Path(__file__).resolve().parents[1]

    input_file = (
        project_root
        / "data"
        / "processed"
        / "listing_sample_cleaned.csv"
    )

    output_file = (
        project_root
        / "data"
        / "processed"
        / "entity_labeling_template.csv"
    )

    df = pd.read_csv(input_file)

    sample = df.sample(
        n=200,
        random_state=42,
    ).copy()

    extractor = EntityExtractor()

    suggestions = sample["cleaned_remarks"].apply(
        extractor.extract_all
    )

    sample["suggested_bedrooms"] = suggestions.apply(
        lambda result: result["bedrooms"]
    )

    sample["suggested_bathrooms"] = suggestions.apply(
        lambda result: result["bathrooms"]
    )

    sample["suggested_price"] = suggestions.apply(
        lambda result: result["price"]
    )

    sample["suggested_sqft"] = suggestions.apply(
        lambda result: result["sqft"]
    )

    sample["suggested_amenities"] = suggestions.apply(
        lambda result: json.dumps(result["amenities"])
    )

    # These are the columns you will review and correct.
    sample["gold_bedrooms"] = sample["suggested_bedrooms"]
    sample["gold_bathrooms"] = sample["suggested_bathrooms"]
    sample["gold_price"] = sample["suggested_price"]
    sample["gold_sqft"] = sample["suggested_sqft"]
    sample["gold_amenities"] = sample["suggested_amenities"]
    sample["reviewed"] = False

    columns = [
        "L_ListingID",
        "cleaned_remarks",
        "suggested_bedrooms",
        "gold_bedrooms",
        "suggested_bathrooms",
        "gold_bathrooms",
        "suggested_price",
        "gold_price",
        "suggested_sqft",
        "gold_sqft",
        "suggested_amenities",
        "gold_amenities",
        "reviewed",
    ]

    sample[columns].to_csv(
        output_file,
        index=False,
    )

    print("Rows created:", len(sample))
    print("Saved to:", output_file)


if __name__ == "__main__":
    main()