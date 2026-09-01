from pathlib import Path


def folder_size(folder):

    total_size = 0

    for file in Path(folder).rglob("*"):

        if file.is_file():

            total_size += file.stat().st_size

    return total_size


folders = [

    "data/raw",
    "data/working",
    "data/processing"

]


for folder in folders:

    path = Path(folder)

    if path.exists():

        size = folder_size(path)

        print(
            f"{folder}: "
            f"{size / 1024**3:.2f} GB"
        )

    else:

        print(
            f"{folder}: "
            f"Folder does not exist yet"
        )