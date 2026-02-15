import json
import hashlib
import os
import sys

def get_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    paths = [
        "services",
        "src",
        "config",
        "scripts"
    ]
    
    files = []
    
    for path in paths:
        if not os.path.exists(path):
            continue
        for root, _, filenames in os.walk(path):
            for filename in filenames:
                if filename.startswith("."):
                    continue
                full_path = os.path.join(root, filename)
                try:
                    stats = os.stat(full_path)
                    files.append({
                        "path": full_path,
                        "size": stats.st_size,
                        "sha256": get_sha256(full_path),
                        "language": os.path.splitext(filename)[1].lstrip(".")
                    })
                except Exception as e:
                    print(f"Error processing {full_path}: {e}", file=sys.stderr)

    # Add top-level compose files
    for filename in os.listdir("."):
        if filename.startswith("compose") and filename.endswith(".yml"):
            full_path = filename
            try:
                stats = os.stat(full_path)
                files.append({
                    "path": full_path,
                    "size": stats.st_size,
                    "sha256": get_sha256(full_path),
                    "language": "yml"
                })
            except Exception as e:
                print(f"Error processing {full_path}: {e}", file=sys.stderr)

    print(json.dumps(files, indent=2))

if __name__ == "__main__":
    main()
