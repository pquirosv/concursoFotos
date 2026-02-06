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


# Resolve the target MongoDB collection name from env or default.
def collection_for_ingest() -> str:
    return os.getenv("PHOTOS_COLLECTION", "photos")


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


# Drop the collection only when explicitly requested via env.
def drop_collection_enabled() -> bool:
    value = os.getenv("DROP_COLLECTION", "").strip().lower()
    return value in ("1", "true", "y", "yes")


# Resolve PHOTOS_DIR from env (Docker mount).
def resolve_photos_dir() -> Path | None:
    source_dir = Path(os.getenv("PHOTOS_DIR", "/photos"))
    if not source_dir.exists():
        print(f"PHOTOS_DIR does not exist: {source_dir}", file=sys.stderr)
        return None
    if not source_dir.is_dir():
        print(f"PHOTOS_DIR is not a directory: {source_dir}", file=sys.stderr)
        return None
    return source_dir


# Yield files from a source directory, sorted for stability.
def iter_files(source_dir: Path):
    return (path for path in sorted(source_dir.rglob("*")) if path.is_file())


# Remove all contents of a directory, optionally keeping some paths.
def clear_directory(path: Path, keep: set[Path] | None = None) -> None:
    keep = keep or set()
    for child in path.iterdir():
        if child in keep:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


# Main ingest flow: resolve dirs, ingest files, update DB.
def main() -> int:
    source_dir = resolve_photos_dir()
    if source_dir is None:
        return 1

    print(f"PHOTOS_DIR: {source_dir}")

    # Gather files to ingest (including files inside city-named folders).
    files = list(iter_files(source_dir))
    if not files:
        print(f"No files found in {source_dir}")
        return 0

    temp_dir = source_dir / f".{source_dir.name}_tmp"
    if temp_dir.exists():
        print(f"Cleaning existing temp directory: {temp_dir}")
        shutil.rmtree(temp_dir)
    try:
        temp_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"Failed to create temp directory {temp_dir}: {exc}", file=sys.stderr)
        return 1

    # Build documents for valid image files and prune non-image files.
    docs = []
    images_found = 0
    try:
        for file_path in files:
            if not is_image_file(file_path):
                print(f"Skipping non-image file: {file_path.name}")
                continue
            images_found += 1

            doc = {}
            relative_parts = file_path.relative_to(source_dir).parts
            if len(relative_parts) >= 2 and file_path.parent.parent == source_dir:
                doc["city"] = relative_parts[0]

            extracted_year = extract_year(file_path.name)
            if extracted_year is not None:
                doc["year"] = extracted_year

            new_name = file_path.name
            target_path = temp_dir / new_name
            if target_path.exists():
                print(f"Overwriting existing file: {target_path.name}")
            shutil.copy2(file_path, target_path)

            doc["name"] = new_name
            docs.append(doc)

        if images_found == 0:
            print("No image files found; PHOTOS_DIR will be replaced with an empty folder.")

        # Connect to MongoDB and select the target collection.
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://mongo:27017/concurso")
        client = MongoClient(mongo_uri)
        db = resolve_database(client)
        collection_name = collection_for_ingest()
        collection = db[collection_name]

        if drop_collection_enabled():
            print(f"Dropping collection: {collection_name}")
            collection.drop()
        else:
            print(f"Appending to collection: {collection_name}")

        # Insert the documents if any were created.
        if docs:
            result = collection.insert_many(docs)
            print(f"Inserted {len(result.inserted_ids)} photos into {collection_name}.")

        # Replace contents in place (works with Docker bind mounts).
        clear_directory(source_dir, keep={temp_dir})
        for child in temp_dir.iterdir():
            shutil.move(str(child), source_dir / child.name)
        shutil.rmtree(temp_dir)
    except Exception as exc:
        print(f"Error during ingest: {exc}", file=sys.stderr)
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
