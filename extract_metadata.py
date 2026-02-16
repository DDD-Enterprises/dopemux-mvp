
import os
import hashlib
import json
import re
import yaml

def get_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def detect_language(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".toml": "toml",
        ".json": "json",
        ".md": "markdown",
        ".dockerfile": "dockerfile",
        ".sh": "bash",
        ".zsh": "bash"
    }
    if os.path.basename(filepath).lower().startswith("dockerfile"):
        return "dockerfile"
    return mapping.get(ext, "unknown")

def task1_structure_map():
    structure = {}
    base_dirs = ["services", "src", "config"]
    processed_files = []

    for bdir in base_dirs:
        if not os.path.exists(bdir):
            continue
        for root, dirs, files in os.walk(bdir):
            if "node_modules" in dirs:
                dirs.remove("node_modules")
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")
            
            for file in files:
                if file.startswith("."):
                    continue
                path = os.path.join(root, file)
                lang = detect_language(path)
                size = os.path.getsize(path)
                sha = get_sha256(path)
                
                component = path.split(os.sep)[1] if len(path.split(os.sep)) > 1 else "root"
                
                if component not in structure:
                    structure[component] = []
                
                structure[component].append({
                    "path": path,
                    "sha256": sha,
                    "language": lang,
                    "size_bytes": size
                })

    # Docs index
    if os.path.exists("docs"):
        for file in os.listdir("docs"):
            if file.startswith("index") and os.path.isfile(os.path.join("docs", file)):
                path = os.path.join("docs", file)
                structure.setdefault("docs", []).append({
                    "path": path,
                    "sha256": get_sha256(path),
                    "language": detect_language(path),
                    "size_bytes": os.path.getsize(path)
                })

    # Compose files
    for file in os.listdir("."):
        if (file.startswith("compose") or file.endswith("compose.yml")) and file.endswith((".yml", ".yaml")):
            structure.setdefault("docker", []).append({
                "path": file,
                "sha256": get_sha256(file),
                "language": "yaml",
                "size_bytes": os.path.getsize(file)
            })

    with open("STRUCTURE_MAP.json", "w") as f:
        json.dump(structure, f, indent=2)

def task2_service_map():
    services = {}
    
    # Check compose.yml
    compose_path = "compose.yml"
    if not os.path.exists(compose_path):
        compose_path = "docker-compose.yml"
        
    if os.path.exists(compose_path):
        with open(compose_path, "r") as f:
            try:
                data = yaml.safe_load(f)
                if data and "services" in data:
                    for svc_name, svc_cfg in data["services"].items():
                        services[svc_name] = {
                            "compose_service": svc_name,
                            "file_refs": [{"path": compose_path, "context": "compose_definition"}]
                        }
                        if "ports" in svc_cfg:
                            services[svc_name]["ports"] = svc_cfg["ports"]
                        if "image" in svc_cfg:
                            services[svc_name]["image"] = svc_cfg["image"]
                        if "build" in svc_cfg:
                            build_ctx = svc_cfg["build"]
                            if isinstance(build_ctx, str):
                                services[svc_name]["build_context"] = build_ctx
                            elif isinstance(build_ctx, dict):
                                services[svc_name]["build_context"] = build_ctx.get("context")
                                services[svc_name]["dockerfile"] = build_ctx.get("dockerfile")
            except:
                pass

    # Scan services/ directory for Dockerfiles
    if os.path.exists("services"):
        for svc_dir in os.listdir("services"):
            full_svc_dir = os.path.join("services", svc_dir)
            if not os.path.isdir(full_svc_dir):
                continue
            
            svc_info = services.get(svc_dir, {})
            
            for root, _, files in os.walk(full_svc_dir):
                for file in files:
                    if file.lower() == "dockerfile":
                        df_path = os.path.join(root, file)
                        svc_info.setdefault("file_refs", []).append({"path": df_path, "context": "dockerfile"})
                        
                        with open(df_path, "r") as f:
                            lines = f.readlines()
                            for i, line in enumerate(lines):
                                if line.strip().upper().startswith("EXPOSE"):
                                    svc_info.setdefault("exposed_ports", []).append({
                                        "value": line.strip(),
                                        "line": i + 1
                                    })
                                if line.strip().upper().startswith(("CMD", "ENTRYPOINT")):
                                    svc_info["entrypoint_clue"] = {
                                        "value": line.strip(),
                                        "path": df_path,
                                        "line_range": [i + 1, i + 1]
                                    }
            
            if svc_info:
                services[svc_dir] = svc_info

    with open("SERVICE_MAP.json", "w") as f:
        json.dump(services, f, indent=2)

def task3_entrypoints():
    entrypoints = {
        "cli_scripts": [],
        "main_blocks": [],
        "fastapi_apps": [],
        "typer_click_apps": []
    }

    # pyproject.toml / setup.py
    for file in ["pyproject.toml", "setup.py"]:
        if os.path.exists(file):
            with open(file, "r") as f:
                content = f.read()
                if "console_scripts" in content:
                    entrypoints["cli_scripts"].append({"path": file, "mention": "console_scripts"})

    # Scan for code patterns
    base_dirs = ["services", "src"]
    for bdir in base_dirs:
        if not os.path.exists(bdir):
            continue
        for root, _, files in os.walk(bdir):
            for file in files:
                if not file.endswith(".py"):
                    continue
                path = os.path.join(root, file)
                try:
                    with open(path, "r") as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            if 'if __name__ == "__main__":' in line:
                                entrypoints["main_blocks"].append({
                                    "path": path,
                                    "line_range": [i + 1, i + 1]
                                })
                            if "FastAPI(" in line:
                                entrypoints["fastapi_apps"].append({
                                    "path": path,
                                    "line_range": [i + 1, i + 1]
                                })
                            if "Typer(" in line or "@click.command" in line or "@click.group" in line:
                                entrypoints["typer_click_apps"].append({
                                    "path": path,
                                    "line_range": [i + 1, i + 1]
                                })
                except:
                    continue

    with open("ENTRYPOINTS.json", "w") as f:
        json.dump(entrypoints, f, indent=2)

if __name__ == "__main__":
    task1_structure_map()
    task2_service_map()
    task3_entrypoints()
