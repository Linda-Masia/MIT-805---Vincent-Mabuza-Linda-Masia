from pathlib import Path
from datetime import datetime
import csv
import time

import requests


# ============================================================
# CONFIGURATION
# ============================================================

# Assignment requirement:
# Raw dataset must be between 25 GB and 40 GB.
# We aim for approximately 30 GB.

TARGET_GB = 30
MAX_GB = 40

TARGET_BYTES = TARGET_GB * 1024 ** 3
MAX_BYTES = MAX_GB * 1024 ** 3


# Official NYC TLC trip-data location

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"


# Repository paths

DATA_DIR = Path("data/raw")
DATA_DIR.mkdir(parents=True, exist_ok=True)

MANIFEST_FILE = DATA_DIR / "download_manifest.csv"


# ============================================================
# DATA TYPES
# ============================================================

# HVFHV files are generally large, helping us reach Big Data scale.
# Yellow Taxi data provides useful fare, payment and trip variables.

DATA_TYPES = [
    "hvfhv_tripdata",
    "yellow_tripdata"
]


# ============================================================
# GET REMOTE FILE SIZE
# ============================================================

def get_remote_file_size(url):
    """
    Get the size of a remote file without downloading the full file.

    First tries HEAD.
    If Content-Length is unavailable, tries a small Range request.
    """

    try:

        response = requests.head(
            url,
            allow_redirects=True,
            timeout=30
        )

        if response.status_code == 200:

            content_length = response.headers.get(
                "Content-Length"
            )

            if content_length:
                return int(content_length)

    except requests.RequestException:
        pass


    # --------------------------------------------------------
    # Fallback:
    # Request only the first byte and read total size from
    # Content-Range.
    # --------------------------------------------------------

    try:

        headers = {
            "Range": "bytes=0-0"
        }

        response = requests.get(
            url,
            headers=headers,
            stream=True,
            timeout=30
        )

        if response.status_code in [200, 206]:

            content_range = response.headers.get(
                "Content-Range"
            )

            if content_range and "/" in content_range:

                total_size = content_range.split("/")[-1]

                if total_size.isdigit():
                    return int(total_size)

            content_length = response.headers.get(
                "Content-Length"
            )

            if content_length:
                return int(content_length)

    except requests.RequestException:
        pass


    return None


# ============================================================
# GENERATE MONTHS FROM MOST RECENT BACKWARDS
# ============================================================

def generate_recent_months(max_months=180):
    """
    Generates months starting from the current month and moving
    backwards.

    Example:

    2026-09
    2026-08
    2026-07
    ...
    """

    current = datetime.now()

    year = current.year
    month = current.month

    months = []

    for _ in range(max_months):

        months.append((year, month))

        month -= 1

        if month == 0:
            month = 12
            year -= 1

    return months


# ============================================================
# BUILD CANDIDATE FILE LIST
# ============================================================

def build_candidates():
    """
    Creates a list of candidate files ordered from newest
    to oldest.
    """

    candidates = []

    recent_months = generate_recent_months(
        max_months=60
    )

    for year, month in recent_months:

        for data_type in DATA_TYPES:

            filename = (
                f"{data_type}_{year}-{month:02d}.parquet"
            )

            url = (
                f"{BASE_URL}/{filename}"
            )

            candidates.append({

                "filename": filename,
                "url": url,
                "year": year,
                "month": month,
                "data_type": data_type

            })

    return candidates


# ============================================================
# DOWNLOAD FILE
# ============================================================

def download_file(url, output_path):
    """
    Downloads a file using streaming so that the entire file
    is not loaded into memory.
    """

    print(f"\nDownloading: {output_path.name}")

    try:

        response = requests.get(
            url,
            stream=True,
            timeout=60
        )

        if response.status_code != 200:

            print(
                f"ERROR: HTTP "
                f"{response.status_code}"
            )

            return False


        with open(output_path, "wb") as file:

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):

                if chunk:

                    file.write(chunk)


        print(
            f"Finished: {output_path.name}"
        )

        return True


    except requests.RequestException as error:

        print(
            f"Download error: {error}"
        )

        return False


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print("=" * 65)
    print("NYC TLC MOST RECENT BIG DATA DOWNLOADER")
    print("=" * 65)

    print(
        f"Target raw dataset size: "
        f"{TARGET_GB} GB"
    )

    print(
        f"Maximum raw dataset size: "
        f"{MAX_GB} GB"
    )

    print(
        "\nSearching for the most recent "
        "available files..."
    )


    # --------------------------------------------------------
    # STEP 1:
    # Find recent files and check their sizes
    # --------------------------------------------------------

    candidates = build_candidates()

    selected_files = []

    total_size = 0


    for item in candidates:

        filename = item["filename"]

        print(
            f"\nChecking: {filename}"
        )


        size = get_remote_file_size(
            item["url"]
        )


        # File does not exist or size unavailable

        if size is None:

            print("Not available.")

            continue


        size_gb = size / 1024 ** 3


        print(
            f"Available: "
            f"{size_gb:.3f} GB"
        )


        # ----------------------------------------------------
        # Don't exceed the assignment maximum
        # ----------------------------------------------------

        if total_size + size > MAX_BYTES:

            print(
                "Skipping because adding this file "
                "would exceed 40 GB."
            )

            continue


        # ----------------------------------------------------
        # Select the file
        # ----------------------------------------------------

        selected_files.append({

            **item,
            "size": size

        })


        total_size += size


        current_total_gb = (
            total_size / 1024 ** 3
        )


        print(
            f"Selected total: "
            f"{current_total_gb:.3f} GB"
        )


        # ----------------------------------------------------
        # Stop once we reach approximately 30 GB
        # ----------------------------------------------------

        if total_size >= TARGET_BYTES:

            break


    # ========================================================
    # STEP 2:
    # Display selected files
    # ========================================================

    print("\n")
    print("=" * 65)
    print("SELECTED RAW DATASET")
    print("=" * 65)


    if not selected_files:

        print(
            "No files were selected."
        )

        return


    for item in selected_files:

        size_gb = (
            item["size"] / 1024 ** 3
        )

        print(
            f"{item['filename']}"
        )

        print(
            f"  Type: "
            f"{item['data_type']}"
        )

        print(
            f"  Period: "
            f"{item['year']}-{item['month']:02d}"
        )

        print(
            f"  Size: "
            f"{size_gb:.3f} GB"
        )

        print()


    total_gb = (
        total_size / 1024 ** 3
    )


    print("-" * 65)

    print(
        f"TOTAL SELECTED SIZE: "
        f"{total_gb:.3f} GB"
    )

    print("-" * 65)


    # ========================================================
    # Safety check
    # ========================================================

    if total_size < TARGET_BYTES:

        print(
            "\nWARNING:"
        )

        print(
            "The script could not reach "
            f"{TARGET_GB} GB using the files checked."
        )

        print(
            "You may need to increase max_months "
            "or add more dataset types."
        )

        return


    # ========================================================
    # STEP 3:
    # Download selected files
    # ========================================================

    print("\nStarting download...\n")

    manifest_data = []


    for item in selected_files:

        output_path = (
            DATA_DIR / item["filename"]
        )


        # ----------------------------------------------------
        # Skip files already downloaded
        # ----------------------------------------------------

        if output_path.exists():

            actual_size = (
                output_path.stat().st_size
            )


            print(
                f"Already exists: "
                f"{item['filename']}"
            )


        else:

            success = download_file(

                item["url"],

                output_path

            )


            if not success:

                continue


            actual_size = (
                output_path.stat().st_size
            )


        # ----------------------------------------------------
        # Add to manifest
        # ----------------------------------------------------

        manifest_data.append({

            "filename":
                item["filename"],

            "dataset_type":
                item["data_type"],

            "year":
                item["year"],

            "month":
                item["month"],

            "url":
                item["url"],

            "size_bytes":
                actual_size,

            "size_gb":
                round(
                    actual_size / 1024 ** 3,
                    4
                )

        })


        # Small pause between downloads

        time.sleep(1)


    # ========================================================
    # STEP 4:
    # Create download manifest
    # ========================================================

    with open(

        MANIFEST_FILE,

        "w",

        newline="",

        encoding="utf-8"

    ) as csvfile:


        fieldnames = [

            "filename",

            "dataset_type",

            "year",

            "month",

            "url",

            "size_bytes",

            "size_gb"

        ]


        writer = csv.DictWriter(

            csvfile,

            fieldnames=fieldnames

        )


        writer.writeheader()

        writer.writerows(
            manifest_data
        )


    # ========================================================
    # STEP 5:
    # Calculate actual downloaded size
    # ========================================================

    final_size = sum(

        file.stat().st_size

        for file in DATA_DIR.glob(
            "*.parquet"
        )

    )


    final_gb = (
        final_size / 1024 ** 3
    )


    print("\n")
    print("=" * 65)
    print("DOWNLOAD COMPLETE")
    print("=" * 65)

    print(
        f"Final downloaded raw dataset size: "
        f"{final_gb:.3f} GB"
    )

    print(
        f"\nDataset location: "
        f"{DATA_DIR.resolve()}"
    )

    print(
        f"\nManifest created: "
        f"{MANIFEST_FILE}"
    )


if __name__ == "__main__":

    main()