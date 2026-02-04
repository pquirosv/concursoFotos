import os
import re
import sys
import shutil
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


# Resolve the target collection name based on the DATASET environment variable.
def collection_for_dataset() -> str:
    dataset = os.getenv("DATASET", "prod").lower()
    if dataset == "test":
        return os.getenv("PHOTOS_COLLECTION_TEST", "photos_test")
    return os.getenv("PHOTOS_COLLECTION_PROD", "photos_prod")


# Resolve the database from the URI or default to MONGODB_DB.
def resolve_database(client: MongoClient):
    db = client.get_default_database()
    if db is not None:
        return db
    return client[os.getenv("MONGODB_DB", "concurso")]


# Extract a plausible year from the filename, if present.
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

# Check whether the file has an allowed image extension.
def is_image_file(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS

# Ask whether to drop existing records (or read DROP_COLLECTION env).
def prompt_drop_collection() -> bool:
    env_value = os.getenv("DROP_COLLECTION")
    if env_value is not None:
        return env_value.strip().lower() in ("1", "true", "y", "yes")
    if not sys.stdin.isatty():
        print("Non-interactive session: keeping existing records by default.")
        return False
    prompt = "Delete existing database records before ingest? (y)es/(n)o: "
    i = 0
    while i < 2:
        response = input(prompt).strip().lower()
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        # Only print "Please respond with (y)es or (n)o" after the first invalid attempt to avoid cluttering the prompt.
        if i == 0:
            print("Please respond with (y)es or (n)o. (Default will count as (y)es)")
        i += 1
    return True

# Ingest photos from a directory into MongoDB.
def main() -> int:
    # Resolve the source photos directory either from PHOTOS_DIR or by scanning up to repo root.
    photos_dir_env = os.getenv("PHOTOS_DIR")
    if photos_dir_env:
        source_dir = Path(photos_dir_env)
    else:
        repo_photos_dir = None
        for parent in Path(__file__).resolve().parents:
            candidate = parent / "static" / "public" / "fotos"
            if candidate.exists():
                repo_photos_dir = candidate
                break
        if repo_photos_dir is None:
            print("Photos directory not found: repo root not resolvable", file=sys.stderr)
            return 1
        source_dir = repo_photos_dir

    # Resolve the output directory (defaults to the source directory).
    output_dir = Path(os.getenv("PHOTOS_OUT_DIR", str(source_dir)))

    # Validate the photos directories exist.
    if not source_dir.exists():
        print(f"Photos directory not found: {source_dir}", file=sys.stderr)
        return 1
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    if not output_dir.is_dir():
        print(f"Photos output path is not a directory: {output_dir}", file=sys.stderr)
        return 1

    # Gather files to ingest (including files inside city-named folders).
    files = sorted(path for path in source_dir.rglob("*") if path.is_file())
    if not files:
        print(f"No files found in {source_dir}")
        return 0

    # Connect to MongoDB and select the target collection.
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://mongo:27017/concurso")
    client = MongoClient(mongo_uri)
    db = resolve_database(client)
    dataset = os.getenv("DATASET", "prod").lower()
    collection_name = collection_for_dataset()
    collection = db[collection_name]
    drop_collection = prompt_drop_collection()
    
    # Optionally drop the collection before ingesting.
    if drop_collection:
        print(f"Using dataset: {dataset}. Dropping collection: {collection_name}")
        collection.drop()
    else:
        print(f"Using dataset: {dataset}. Appending to collection: {collection_name}")

    # Build documents for valid image files and prune non-image files.
    docs = []
    global_suffix = 0

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
        doc = {}
        
        parts = []
        # If the file is inside a city-named folder, use that folder name as city.
        relative_parts = file_path.relative_to(source_dir).parts
        city = None
        if len(relative_parts) >= 2:
            city = relative_parts[0]
            doc["city"] = city
            parts.append(city)
        
        # If a year can be extracted from the filename, include it.
        extracted_year = extract_year(file_path.name)
        if extracted_year is not None:
            doc["year"] = extracted_year
            parts.append(str(extracted_year))
        
        # Always rename into the root folder with a global auto-incrementing suffix.
        base = "_".join(parts) if parts else file_path.stem
        global_suffix += 1
        new_name = f"{base}_{global_suffix}{file_path.suffix}"
        target_path = output_dir / new_name
        while target_path.exists():
            global_suffix += 1
            new_name = f"{base}_{global_suffix}{file_path.suffix}"
            target_path = output_dir / new_name

        if output_dir.resolve() == source_dir.resolve():
            if file_path.resolve() != target_path.resolve():
                file_path = file_path.rename(target_path)
        else:
            shutil.copy2(file_path, target_path)
        doc["name"] = new_name
        
        docs.append(doc)

    # Insert the documents if any were created.
    if docs:
        result = collection.insert_many(docs)
        print(f"Inserted {len(result.inserted_ids)} photos into {collection_name}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
