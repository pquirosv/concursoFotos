import os
import re
import sys
import shutil
import datetime
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
DEFAULT_BATCH_SIZE = 1000


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
        # actual year
        if year >= 1970 and year <= datetime.datetime.now().year:
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
def resolve_photos_dirs(
    source_dir: Path | str | None = None,
    photos_dir: Path | str | None = None,
) -> tuple[Path, Path] | None:
    source_dir = Path(source_dir) if source_dir is not None else Path(os.getenv("SOURCE_DIR", "/photos"))
    photos_dir = Path(photos_dir) if photos_dir is not None else Path(os.getenv("PHOTOS_DIR", "/photos_out"))

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


# Yield files from a source directory without materializing the full file list.
# Sorting is applied per folder to keep deterministic ordering.
def iter_files(source_dir: Path):
    for root, dirs, files in os.walk(source_dir):
        dirs.sort()
        files.sort()
        root_path = Path(root)
        for name in files:
            yield root_path / name


# Remove all contents of a directory.
def clear_directory(path: Path) -> None:
    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


# Resolve and validate ingest batch size from parameter/env.
def normalize_batch_size(batch_size: int | str | None) -> int:
    candidate = batch_size if batch_size is not None else os.getenv(
        "INGEST_BATCH_SIZE", str(DEFAULT_BATCH_SIZE)
    )
    try:
        size = int(candidate)
    except (TypeError, ValueError) as exc:
        raise ValueError("INGEST_BATCH_SIZE must be a positive integer.") from exc
    if size < 1:
        raise ValueError("INGEST_BATCH_SIZE must be >= 1.")
    return size


# Insert a pending batch into Mongo and clear the in-memory buffer.
def flush_batch(collection, docs: list[dict]) -> int:
    if not docs:
        return 0
    result = collection.insert_many(docs)
    inserted = len(result.inserted_ids)
    docs.clear()
    return inserted


# Build a Mongo document from a file path and extracted metadata.
def build_photo_doc(file_path: Path, source_dir: Path) -> dict | None:
    if not is_image_file(file_path):
        print(f"Skipping non-image file: {file_path.name}")
        return None

    doc = {}
    relative_parts = file_path.relative_to(source_dir).parts
    if len(relative_parts) >= 2 and file_path.parent.parent == source_dir:
        doc["city"] = relative_parts[0]

    extracted_year = extract_year(file_path.name)
    if extracted_year is not None:
        doc["year"] = extracted_year

    if "city" not in doc and "year" not in doc:
        print(f"Skipping file without city/year metadata: {file_path.name}")
        return None

    doc["name"] = file_path.name
    return doc


# Main ingest flow: resolve dirs, ingest files, update DB.
# It can be called from CLI or programmatically (e.g., future admin actions).
def main(
    source_dir: Path | str | None = None,
    photos_dir: Path | str | None = None,
    *,
    drop_existing: bool | None = None,
    batch_size: int | None = None,
    mongo_uri: str | None = None,
    collection_name: str = PHOTOS_COLLECTION,
    interactive: bool = True,
) -> int:
    resolved = resolve_photos_dirs(source_dir=source_dir, photos_dir=photos_dir)
    if resolved is None:
        return 1
    source_dir, photos_dir = resolved

    try:
        batch_size = normalize_batch_size(batch_size)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"SOURCE_DIR: {source_dir}")
    print(f"PHOTOS_DIR: {photos_dir}")
    print(f"Batch size: {batch_size}")

    docs: list[dict] = []
    inserted_total = 0
    scanned_any_file = False
    client = None
    try:
        # Connect to MongoDB and select the target collection.
        mongo_uri = mongo_uri or os.getenv("MONGODB_URI", "mongodb://mongo:27017/concurso")
        client = MongoClient(mongo_uri)
        db = resolve_database(client)
        collection = db[collection_name]

        if drop_existing is None:
            drop_existing = prompt_drop_collection() if interactive else False

        if drop_existing:
            print(f"Dropping collection: {collection_name}")
            collection.drop()
            print(f"Clearing output directory: {photos_dir}")
            clear_directory(photos_dir)
        else:
            print(f"Appending to collection: {collection_name}")

        for file_path in iter_files(source_dir):
            scanned_any_file = True

            doc = build_photo_doc(file_path, source_dir)
            if doc is None:
                continue

            target_path = photos_dir / doc["name"]
            if target_path.exists():
                if not ("city" in doc and "year" in doc):
                    print(
                        f"Skipping existing file without city/year metadata: {target_path.name}"
                    )
                    continue
                print(f"Overwriting existing file: {target_path.name}")
            shutil.copy2(file_path, target_path)

            docs.append(doc)
            if len(docs) >= batch_size:
                inserted_total += flush_batch(collection, docs)

        if not scanned_any_file:
            print(f"No files found in {source_dir}")
            return 0

        inserted_total += flush_batch(collection, docs)
        if inserted_total:
            print(f"Inserted {inserted_total} photos into {collection_name}.")
        else:
            print("No valid photos to insert.")
    except Exception as exc:
        print(f"Error during ingest: {exc}", file=sys.stderr)
        return 1
    finally:
        if client is not None:
            client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
