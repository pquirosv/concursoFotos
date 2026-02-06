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

PHOTOS_COLLECTION = "photos"


# Pick the database from the client default or fallback env name.
def resolve_database(client: MongoClient):
    db = client.get_default_database()
    if db is not None:
        return db
    return client[os.getenv("MONGODB_DB", "concurso")]


# Extract a YYYY year from an 8-digit date inside a filename.
def extract_year(filename: str):
    for match in re.finditer(r"(?<!\d)(\d{8})(?!\d)", filename):
        year = int(match.group(1)[:4])
        if year >= 1970:
            return year
    return None


# Check if a file has a supported image extension.
def is_image_file(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


# Ask whether to drop the collection (interactive only).
def prompt_drop_collection() -> bool:
    prompt = "Delete existing database records before ingest? (y)es/(n)o: "
    i = 0
    while i < 2:
        response = input(prompt).strip().lower()
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        if i == 0:
            print("Please respond with (y)es or (n)o. (Default will count as (y)es)")
        i += 1
    return True


# Resolve SOURCE_DIR and PHOTOS_DIR from env (Docker mount).
def resolve_photos_dirs() -> tuple[Path, Path] | None:
    source_dir = Path(os.getenv("SOURCE_DIR", "/photos"))
    photos_dir = Path(os.getenv("PHOTOS_DIR", "/photos_out"))

    if not source_dir.exists():
        print(f"SOURCE_DIR does not exist: {source_dir}", file=sys.stderr)
        return None
    if not source_dir.is_dir():
        print(f"SOURCE_DIR is not a directory: {source_dir}", file=sys.stderr)
        return None

    try:
        photos_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"Failed to create PHOTOS_DIR {photos_dir}: {exc}", file=sys.stderr)
        return None

    source_resolved = source_dir.resolve()
    photos_resolved = photos_dir.resolve()
    if photos_resolved == source_resolved:
        print("PHOTOS_DIR must be different from SOURCE_DIR.", file=sys.stderr)
        return None
    if photos_resolved.is_relative_to(source_resolved) or source_resolved.is_relative_to(photos_resolved):
        print("PHOTOS_DIR must not be inside SOURCE_DIR (or vice versa).", file=sys.stderr)
        return None

    return source_dir, photos_dir


# Yield files from a source directory, sorted for stability.
def iter_files(source_dir: Path):
    return (path for path in sorted(source_dir.rglob("*")) if path.is_file())


# Remove all contents of a directory.
def clear_directory(path: Path) -> None:
    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


# Main ingest flow: resolve dirs, ingest files, update DB.
def main() -> int:
    resolved = resolve_photos_dirs()
    if resolved is None:
        return 1
    source_dir, photos_dir = resolved

    print(f"SOURCE_DIR: {source_dir}")
    print(f"PHOTOS_DIR: {photos_dir}")

    files = list(iter_files(source_dir))
    if not files:
        print(f"No files found in {source_dir}")
        return 0

    docs = []
    try:
        # Connect to MongoDB and select the target collection.
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://mongo:27017/concurso")
        client = MongoClient(mongo_uri)
        db = resolve_database(client)
        collection = db[PHOTOS_COLLECTION]

        if prompt_drop_collection():
            print(f"Dropping collection: {PHOTOS_COLLECTION}")
            collection.drop()
            print(f"Clearing output directory: {photos_dir}")
            clear_directory(photos_dir)
        else:
            print(f"Appending to collection: {PHOTOS_COLLECTION}")

        for file_path in files:
            if not is_image_file(file_path):
                print(f"Skipping non-image file: {file_path.name}")
                continue

            doc = {}
            relative_parts = file_path.relative_to(source_dir).parts
            if len(relative_parts) >= 2 and file_path.parent.parent == source_dir:
                doc["city"] = relative_parts[0]

            extracted_year = extract_year(file_path.name)
            if extracted_year is not None:
                doc["year"] = extracted_year

            if "city" not in doc and "year" not in doc:
                print(
                    f"Skipping file without city/year metadata: {file_path.name}"
                )
                continue

            new_name = file_path.name
            target_path = photos_dir / new_name
            if target_path.exists():
                if not ("city" in doc and "year" in doc):
                    print(
                        f"Skipping existing file without city/year metadata: {target_path.name}"
                    )
                    continue
                print(f"Overwriting existing file: {target_path.name}")
            shutil.copy2(file_path, target_path)

            doc["name"] = new_name
            docs.append(doc)

        if docs:
            result = collection.insert_many(docs)
            print(f"Inserted {len(result.inserted_ids)} photos into {PHOTOS_COLLECTION}.")
    except Exception as exc:
        print(f"Error during ingest: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
