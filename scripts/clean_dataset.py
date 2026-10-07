"""Generate the cleaned Week 2 listing dataset."""

from pathlib import Path

import pandas as pd

from scripts.text_cleaning import TextCleaner


def main():
    project_root = Path(__file__).resolve().parents[1]

    input_file = (
        project_root
        / "data"
        / "processed"
        / "listing_sample.csv"
    )

    output_file = (
        project_root
        / "data"
        / "processed"
        / "listing_sample_cleaned.csv"
    )

    df = pd.read_csv(input_file)
    cleaner = TextCleaner()

    df["cleaned_remarks"] = df["remarks"].apply(
        cleaner.clean_text
    )

    df.to_csv(output_file, index=False)

    print(f"Rows cleaned: {len(df)}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()
