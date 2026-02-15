import os
import json
import hashlib
import re

REPO_DIR = "/Users/hue/code/dopemux-mvp"
MEGA_DIR = "/Users/hue/code/dopemux-mvp/MEGA"

def get_sha256(path):
    hash_sha256 = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
    except Exception:
        return "error"
    return hash_sha256.hexdigest()

def extract_code():
    if not os.path.exists(MEGA_DIR):
        os.makedirs(MEGA_DIR)

    structure_map = []
    service_map = {}
    entrypoints = []

    target_dirs = ["services", "src", "config", "docs"]
    
    for t_dir in target_dirs:
        dir_path = os.path.join(REPO_DIR, t_dir)
        if not os.path.exists(dir_path): continue
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, REPO_DIR)
                try:
                    size = os.path.getsize(path)
                except OSError:
                    size = 0
                ext = os.path.splitext(file)[1].lower()
                lang = "unknown"
                if ext == ".py": lang = "python"
                elif ext == ".md": lang = "markdown"
                elif ext == ".yml" or ext == ".yaml": lang = "yaml"
                elif ext == ".json": lang = "json"
                elif ext == ".sh": lang = "shell"
                elif "Dockerfile" in file: lang = "dockerfile"

                structure_map.append({
                    "path": rel_path,
                    "sha256": get_sha256(path),
                    "language": lang,
                    "size": size
                })

    # SERVICE_MAP
    services_dir = os.path.join(REPO_DIR, "services")
    if os.path.exists(services_dir):
        for s_name in os.listdir(services_dir):
            s_path = os.path.join(services_dir, s_name)
            if os.path.isdir(s_path):
                clues = {}
                dfile = os.path.join(s_path, "Dockerfile")
                if os.path.exists(dfile): clues["dockerfile"] = True
                
                # Check for entrypoint clues in files
                for root, dirs, files in os.walk(s_path):
                    for file in files:
                        if file.endswith(".py"):
                            try:
                                with open(os.path.join(root, file), "r", errors="ignore") as f:
                                    content = f.read()
                                    if "__main__" in content: clues["has_main"] = True
                                    if "FastAPI" in content: clues["is_fastapi"] = True
                            except Exception:
                                pass
                
                service_map[s_name] = {
                    "path": os.path.relpath(s_path, REPO_DIR),
                    "clues": clues
                }

    # ENTRYPOINTS
    # 1. pyproject.toml scripts
    pyproject_path = os.path.join(REPO_DIR, "pyproject.toml")
    if os.path.exists(pyproject_path):
        try:
            import tomllib
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                scripts = data.get("project", {}).get("scripts", {})
                for name, entry in scripts.items():
                    entrypoints.append({
                        "type": "console_script",
                        "name": name,
                        "entry": entry,
                        "source": "pyproject.toml"
                    })
        except Exception:
            pass

    # 2. Scanning for __main__, Typer, Click, FastAPI
    for root, dirs, files in os.walk(os.path.join(REPO_DIR, "src")):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, REPO_DIR)
                try:
                    with open(path, "r", errors="ignore") as f:
                        content = f.read()
                        if "if __name__ == \"__main__\":" in content:
                            entrypoints.append({"type": "main_block", "path": rel_path})
                        if "Typer()" in content:
                            entrypoints.append({"type": "typer_app", "path": rel_path})
                        if "Click" in content: # Loose check
                            entrypoints.append({"type": "click_app", "path": rel_path})
                        if "FastAPI(" in content:
                            entrypoints.append({"type": "fastapi_app", "path": rel_path})
                except Exception:
                    pass

    # Write output
    try:
        with open(os.path.join(MEGA_DIR, "STRUCTURE_MAP.json"), "w") as f:
            json.dump(structure_map, f, indent=2)
        with open(os.path.join(MEGA_DIR, "SERVICE_MAP.json"), "w") as f:
            json.dump(service_map, f, indent=2)
        with open(os.path.join(MEGA_DIR, "ENTRYPOINTS.json"), "w") as f:
            json.dump(entrypoints, f, indent=2)
    except Exception as e:
        print(f"Error writing code artifacts: {e}")

if __name__ == "__main__":
    extract_code()
