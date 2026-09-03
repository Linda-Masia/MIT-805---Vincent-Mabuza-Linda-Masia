from pathlib import Path
import requests


# ============================================================
# SETTINGS
# ============================================================

# Change this number to whatever total size you want.
# This is the COMBINED limit across all 4 datasets.
TARGET_GB = 12

TARGET_BYTES = TARGET_GB * 1_000_000_000

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

DATA_DIR = Path("data/raw")

DATASETS = {
    "yellow": "yellow_tripdata",
    "green": "green_tripdata",
    "fhv": "fhv_tripdata",
    "fhvhv": "fhvhv_tripdata",
}


# ============================================================
# CREATE FOLDERS
# ============================================================

for dataset in DATASETS:
    (DATA_DIR / dataset).mkdir(
        parents=True,
        exist_ok=True
    )


# ============================================================
# GET TOTAL SIZE OF ALL 4 FOLDERS
# ============================================================

def get_total_size():

    total = 0

    for dataset in DATASETS:

        folder = DATA_DIR / dataset

        for file in folder.glob("*.parquet"):
            total += file.stat().st_size

    return total


# ============================================================
# DOWNLOAD
# ============================================================

def download(url, file_path):

    temp_file = Path(
        str(file_path) + ".part"
    )

    try:

        print(f"    Downloading...")

        with requests.get(
            url,
            stream=True,
            timeout=120
        ) as response:

            if response.status_code == 404:

                print(
                    "    Not available (404)"
                )

                return False

            response.raise_for_status()

            with open(
                temp_file,
                "wb"
            ) as file:

                for chunk in response.iter_content(
                    chunk_size=8 * 1024 * 1024
                ):

                    if chunk:
                        file.write(chunk)

        # Only rename when completely downloaded
        temp_file.replace(file_path)

        print(
            f"    Downloaded: "
            f"{file_path.name}"
        )

        return True

    except requests.RequestException as error:

        print(
            f"    Download error: {error}"
        )

        temp_file.unlink(
            missing_ok=True
        )

        return False


# ============================================================
# REMOVE INCOMPLETE DOWNLOADS
# ============================================================

for file in DATA_DIR.rglob("*.part"):

    print(
        f"Removing incomplete file: "
        f"{file}"
    )

    file.unlink()


# ============================================================
# CURRENT SIZE
# ============================================================

total = get_total_size()

print()
print("=" * 60)
print("NYC TLC DATA DOWNLOADER")
print("=" * 60)

print(
    f"Target: {TARGET_GB} GB COMBINED"
)

print(
    f"Current: "
    f"{total / 1_000_000_000:.2f} GB"
)

print("=" * 60)


# ============================================================
# CHECK IF ALREADY AT LIMIT
# ============================================================

if total >= TARGET_BYTES:

    print()
    print("Target already reached.")

else:

    # Start from January 2026
    year = 2026
    month = 1


    # ========================================================
    # GO BACK MONTH BY MONTH
    # ========================================================

    for _ in range(120):

        print()
        print(
            f"===== {year}-{month:02d} ====="
        )


        # ----------------------------------------------------
        # DOWNLOAD ALL 4 DATASETS
        # ----------------------------------------------------

        for dataset, prefix in DATASETS.items():

            filename = (
                f"{prefix}_"
                f"{year}-{month:02d}.parquet"
            )

            folder = DATA_DIR / dataset

            file_path = folder / filename

            url = f"{BASE_URL}/{filename}"


            print()
            print(
                f"[{dataset.upper()}] "
                f"{filename}"
            )


            # ------------------------------------------------
            # Skip if already downloaded
            # ------------------------------------------------

            if file_path.exists():

                print(
                    "    Already downloaded."
                )

            else:

                download(
                    url,
                    file_path
                )


            # ------------------------------------------------
            # Recalculate TOTAL across all 4 folders
            # ------------------------------------------------

            total = get_total_size()

            print(
                f"    Combined total: "
                f"{total / 1_000_000_000:.2f} GB"
            )


            # ------------------------------------------------
            # STOP
            # ------------------------------------------------

            if total >= TARGET_BYTES:

                print()
                print("=" * 60)
                print("TARGET REACHED")
                print("=" * 60)

                print(
                    f"Total: "
                    f"{total / 1_000_000_000:.2f} GB"
                )

                print("=" * 60)

                raise SystemExit


        # ----------------------------------------------------
        # Previous month
        # ----------------------------------------------------

        month -= 1

        if month == 0:

            month = 12
            year -= 1


print()
print("Finished.")