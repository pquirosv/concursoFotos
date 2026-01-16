import os
import random
import re
import sys
from pathlib import Path

from pymongo import MongoClient


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


def year_options(year: int):
    candidates = [value for value in range(year - 4, year + 5) if value != year]
    options = [year] + random.sample(candidates, 3)
    random.shuffle(options)
    return options


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
    print(f"Using dataset: {dataset}. Dropping collection: {collection_name}")
    collection.drop()

    docs = []
    existing_names = set(
        doc["name"] for doc in collection.find({"name": {"$in": [p.name for p in files]}}, {"name": 1})
    )

    for file_path in files:
        if file_path.name in existing_names:
            continue
        doc = {"name": file_path.name}
        extracted_year = extract_year(file_path.name)
        if extracted_year is not None:
            doc["year"] = extracted_year
            doc["yearOptions"] = year_options(extracted_year)
        docs.append(doc)

    if docs:
        result = collection.insert_many(docs)
        print(f"Inserted {len(result.inserted_ids)} photos into {collection_name}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
