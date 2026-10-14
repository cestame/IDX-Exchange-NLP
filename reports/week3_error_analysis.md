# Week 3 Entity Extraction Error Analysis

## Evaluation Results

The entity extractor achieved an overall precision of 98.37%,
recall of 96.53%, and F1 score of 97.44%.

Performance varied between entity types:

- Bedrooms: 90.09% F1
- Bathrooms: 61.04% F1
- Price: 0.00% F1
- Square footage: 89.91% F1
- Amenities: 100.00% F1

## Main Failure Patterns

### 1. Written numbers

The extractor missed bedroom and bathroom counts written as words,
such as "three bedrooms" and "two bathrooms."

### 2. Hyphenated bathroom counts

The bathroom pattern missed phrases such as "2-bath" because the
original regex did not allow a hyphen.

### 3. Fractional bathrooms

Formats such as "3-1/2 baths" and "two and a half bathrooms" were
not interpreted correctly.

### 4. Numbers incorrectly identified as prices

The original price pattern treated any number with five or more
digits as a price. This caused street addresses, lot sizes, renovation
costs, and other numbers to be classified as prices.

### 5. Non-living square footage

Lot, deck, balcony, and garage measurements were sometimes classified
as the home's living area.

### 6. Multi-unit properties

Listings containing accessory dwelling units, duplexes, or multiple
units often mentioned several bedroom and bathroom counts. Returning
only the first match did not always represent the whole property.

## Limitations

The overall score was strongly influenced by amenity matching because
the taxonomy produced many exact phrase matches. Numeric performance
was less consistent, especially for bathrooms and prices.

## Possible Improvements

Future improvements could add support for written numbers, hyphenated
and fractional bathroom counts, price context words, and measurement
context that distinguishes living area from lot or outdoor space.

