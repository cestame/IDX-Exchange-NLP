"""Evaluate the Week 3 entity extractor."""

import json
from pathlib import Path

import pandas as pd

from scripts.entity_extractor import EntityExtractor


def normalize_number(value):
    """Convert CSV values into comparable numbers."""
    if pd.isna(value) or value == "":
        return None

    return float(value)


def update_numeric_counts(predicted, gold, counts):
    """Compare one predicted number with its gold label."""
    predicted = normalize_number(predicted)
    gold = normalize_number(gold)

    if predicted is None and gold is None:
        return

    if predicted == gold:
        counts["tp"] += 1
    else:
        if predicted is not None:
            counts["fp"] += 1

        if gold is not None:
            counts["fn"] += 1


def get_amenity_terms(value):
    """Turn an amenity JSON list into a set of terms."""
    if pd.isna(value) or value == "":
        return set()

    if isinstance(value, str):
        value = json.loads(value)

    return {
        item["term"]
        for item in value
    }


def calculate_metrics(counts):
    """Calculate precision, recall, and F1."""
    tp = counts["tp"]
    fp = counts["fp"]
    fn = counts["fn"]

    if tp + fp > 0:
        precision = tp / (tp + fp)
    else:
        precision = 0

    if tp + fn > 0:
        recall = tp / (tp + fn)
    else:
        recall = 0

    if precision + recall > 0:
        f1 = (
            2
            * precision
            * recall
            / (precision + recall)
        )
    else:
        f1 = 0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def main():
    project_root = Path(__file__).resolve().parents[1]

    label_file = (
        project_root
        / "data"
        / "processed"
        / "entity_labeling_template.csv"
    )

    report_directory = project_root / "reports"
    report_directory.mkdir(exist_ok=True)

    report_file = (
        report_directory
        / "week3_metrics.json"
    )

    df = pd.read_csv(label_file)
    extractor = EntityExtractor()

    counts = {
        "bedrooms": {"tp": 0, "fp": 0, "fn": 0},
        "bathrooms": {"tp": 0, "fp": 0, "fn": 0},
        "price": {"tp": 0, "fp": 0, "fn": 0},
        "sqft": {"tp": 0, "fp": 0, "fn": 0},
        "amenities": {"tp": 0, "fp": 0, "fn": 0},
    }

    for _, row in df.iterrows():
        predictions = extractor.extract_all(
            row["cleaned_remarks"]
        )

        update_numeric_counts(
            predictions["bedrooms"],
            row["gold_bedrooms"],
            counts["bedrooms"],
        )

        update_numeric_counts(
            predictions["bathrooms"],
            row["gold_bathrooms"],
            counts["bathrooms"],
        )

        update_numeric_counts(
            predictions["price"],
            row["gold_price"],
            counts["price"],
        )

        update_numeric_counts(
            predictions["sqft"],
            row["gold_sqft"],
            counts["sqft"],
        )

        predicted_amenities = {
            item["term"]
            for item in predictions["amenities"]
        }

        gold_amenities = get_amenity_terms(
            row["gold_amenities"]
        )

        counts["amenities"]["tp"] += len(
            predicted_amenities & gold_amenities
        )

        counts["amenities"]["fp"] += len(
            predicted_amenities - gold_amenities
        )

        counts["amenities"]["fn"] += len(
            gold_amenities - predicted_amenities
        )

    results = {
        entity: calculate_metrics(entity_counts)
        for entity, entity_counts in counts.items()
    }

    total_counts = {
        "tp": sum(
            item["tp"]
            for item in counts.values()
        ),
        "fp": sum(
            item["fp"]
            for item in counts.values()
        ),
        "fn": sum(
            item["fn"]
            for item in counts.values()
        ),
    }

    results["overall"] = calculate_metrics(
        total_counts
    )

    with open(
        report_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(results, file, indent=2)

    for entity, metrics in results.items():
        print(f"\n{entity.upper()}")
        print(f"TP:        {metrics['tp']}")
        print(f"FP:        {metrics['fp']}")
        print(f"FN:        {metrics['fn']}")
        print(
            f"Precision: "
            f"{metrics['precision']:.2%}"
        )
        print(
            f"Recall:    "
            f"{metrics['recall']:.2%}"
        )
        print(
            f"F1:        "
            f"{metrics['f1']:.2%}"
        )

    print("\nSaved report to:", report_file)


if __name__ == "__main__":
    main()
