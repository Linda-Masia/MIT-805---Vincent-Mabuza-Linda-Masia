import os
import requests

TARGET_SIZE_GB = 30
total_size = 0

os.makedirs("data/raw", exist_ok=True)

year = 2024

for month in range(1, 13):

    filename = f"yellow_tripdata_{year}-{month:02d}.parquet"
    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{filename}"
    output_path = f"data/raw/{filename}"

    print(f"\nDownloading: {filename}")

    response = requests.get(url, stream=True)

    if response.status_code == 200:

        with open(output_path, "wb") as file:

            for chunk in response.iter_content(chunk_size=1024 * 1024):

                if chunk:
                    file.write(chunk)

        file_size = os.path.getsize(output_path)
        total_size += file_size

        total_gb = total_size / (1024**3)

        print(f"File size: {file_size / (1024**3):.2f} GB")
        print(f"Total dataset size: {total_gb:.2f} GB")

        if total_gb >= TARGET_SIZE_GB:
            print("\nTarget dataset size reached!")
            break

    else:
        print(f"File unavailable: {filename}")