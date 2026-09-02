from pathlib import Path
from datetime import datetime
import requests

TARGET_GB = 12.3
DATA_DIR = Path("data/raw")
BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_folder_size():
    return sum(
        f.stat().st_size
        for f in DATA_DIR.glob("*.parquet")
    )


def download(url, file_path):

    temp_file = Path(str(file_path) + ".part")

    try:
        r = requests.get(url, stream=True, timeout=60)

        if r.status_code != 200:
            return False

        with open(temp_file, "wb") as file:
            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    file.write(chunk)

        temp_file.rename(file_path)
        return True

    except requests.RequestException:
        return False


# Delete incomplete downloads from previous runs
for file in DATA_DIR.glob("*.part"):
    file.unlink()


total = get_folder_size()

print(f"Current dataset size: {total / 1024**3:.2f} GB")


# Start from the current month and work backwards
now = datetime.now()
year = now.year
month = now.month


for _ in range(60):

    filename = f"hvfhv_tripdata_{year}-{month:02d}.parquet"
    file_path = DATA_DIR / filename

    # Skip already downloaded files
    if file_path.exists():

        print(f"Already downloaded: {filename}")

    else:

        url = f"{BASE_URL}/{filename}"

        print(f"Trying: {filename}")

        if download(url, file_path):

            total = get_folder_size()

            print(
                f"Downloaded! Total size: "
                f"{total / 1024**3:.2f} GB"
            )

    # Stop when we reach 12 GB
    if total >= TARGET_GB * 1024**3:

        print("\nTarget reached!")
        print(f"Final size: {total / 1024**3:.2f} GB")

        break

    # Move back one month
    month -= 1

    if month == 0:
        month = 12
        year -= 1