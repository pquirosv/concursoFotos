import os
import re
import sys
from pathlib import Path

from pymongo import MongoClient


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
    ".heic",
    ".heif",
}


def collection_for_dataset() -> str:
    dataset = os.getenv("DATASET", "prod").lower()
    if dataset == "test":
        return os.getenv("PHOTOS_COLLECTION_TEST", "photos_test")
    return os.getenv("PHOTOS_COLLECTION_PROD", "photos_prod")


def resolve_database(client: MongoClient):
    db = client.get_default_database()
    if db is not None:
        return db
    return client[os.getenv("MONGODB_DB", "concurso")]


def extract_year(filename: str):
    patterns = [r"-([0-9]{8})-", r"_([0-9]{8})_", r"([0-9]{8})_"]
    for pattern in patterns:
        match = re.search(pattern, filename)
        if not match:
            continue
        year = int(match.group(1)[:4])
        if year >= 1970:
            return year
    return None

def is_image_file(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS

def prompt_drop_collection() -> bool:
    prompt = "Delete existing database records before ingest? (y)es/(n)o: "
    i = 0
    while i < 2:
        response = input(prompt).strip().lower()
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        i += 1
        print("Please respond with (y)es or (n)o. (Default is (y)es)")
    return True

def main() -> int:
    photos_dir = Path(os.getenv("PHOTOS_DIR", "/photos"))
    if not photos_dir.exists():
        print(f"Photos directory not found: {photos_dir}", file=sys.stderr)
        return 1

    files = sorted(path for path in photos_dir.iterdir() if path.is_file())
    if not files:
        print(f"No files found in {photos_dir}")
        return 0

    mongo_uri = os.getenv("MONGODB_URI", "mongodb://mongo:27017/concurso")
    client = MongoClient(mongo_uri)
    db = resolve_database(client)
    dataset = os.getenv("DATASET", "prod").lower()
    collection_name = collection_for_dataset()
    collection = db[collection_name]
    drop_collection = prompt_drop_collection()
    
    if drop_collection:
        print(f"Using dataset: {dataset}. Dropping collection: {collection_name}")
        collection.drop()
    else:
        print(f"Using dataset: {dataset}. Appending to collection: {collection_name}")

    docs = []

    for file_path in files:
        if not is_image_file(file_path):
            try:
                file_path.unlink()
                print(f"Deleted non-image file: {file_path.name}")
            except OSError as exc:
                print(
                    f"Failed to delete non-image file {file_path.name}: {exc}",
                    file=sys.stderr,
                )
            continue
        doc = {"name": file_path.name}
        extracted_year = extract_year(file_path.name)
        if extracted_year is not None:
            doc["year"] = extracted_year
        docs.append(doc)

    if docs:
        result = collection.insert_many(docs)
        print(f"Inserted {len(result.inserted_ids)} photos into {collection_name}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
