# Dataset Information

## Source

NYC Taxi and Limousine Commission (TLC) Trip Record Data.

Official dataset source:

https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

## Raw Dataset

The raw dataset consists of publicly available NYC TLC trip record Parquet files.

Target size:

Approximately 30 GB.

The exact downloaded files and their sizes are recorded in:

data/raw/download_manifest.csv

## Working Dataset

The working dataset will be created after:

- Selecting relevant columns
- Removing unnecessary records
- Cleaning missing or invalid values
- Selecting relevant trip periods

Target size:

At least 12 GB.

## Processing Dataset

A representative subset will be selected for PySpark processing.

Target size:

At least 3 GB.

## Important

The raw dataset itself is not committed to GitHub.

Users should run:

python src/download_data.py

to download the dataset.