import json
import re

def parse_rg_json(filepath):
    matches = []
    with open(filepath, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data['type'] == 'match':
                    matches.append(data['data'])
            except json.JSONDecodeError:
                continue
    return matches

def extract_env_vars(matches):
    results = []
    # Regex for os.getenv('VAR', 'DEFAULT') or os.environ.get('VAR', 'DEFAULT') or os.environ['VAR']
    # Simplified patterns for extraction
    patterns = [
        re.compile(r"os\.getenv\(\s*['\"]([^'\"]+)['\"]\s*(?:,\s*['\"]([^'\"]+)['\"]|,\s*([^)]+))?\s*\)"),
        re.compile(r"os\.environ\.get\(\s*['\"]([^'\"]+)['\"]\s*(?:,\s*['\"]([^'\"]+)['\"]|,\s*([^)]+))?\s*\)"),
        re.compile(r"os\.environ\[\s*['\"]([^'\"]+)['\"]\s*\]")
    ]
    
    for m in matches:
        path = m['path']['text']
        line_num = m['line_number']
        content = m['lines']['text']
        
        for p in patterns:
            for match in p.finditer(content):
                name = match.group(1)
                default = None
                if len(match.groups()) > 1:
                    default = match.group(2) or match.group(3)
                
                results.append({
                    "name": name,
                    "default": default.strip() if default else None,
                    "location": f"{path}:{line_num}"
                })
    return results

def extract_config_loaders(matches):
    results = []
    # Patterns for config loaders
    # load_dotenv('path')
    # json.load(f), toml.load(f), etc.
    patterns = [
        (re.compile(r"load_dotenv\(\s*(?:['\"]([^'\"]+)['\"])?\s*\)"), "dotenv"),
        (re.compile(r"toml\.load\("), "toml"),
        (re.compile(r"yaml\.load\("), "yaml"),
        (re.compile(r"yaml\.safe_load\("), "yaml"),
        (re.compile(r"json\.load\("), "json"),
        (re.compile(r"ConfigParser"), "ini")
    ]
    
    for m in matches:
        path = m['path']['text']
        line_num = m['line_number']
        content = m['lines']['text']
        
        for p, loader_type in patterns:
            for match in p.finditer(content):
                filename = None
                if loader_type == "dotenv" and len(match.groups()) > 0:
                    filename = match.group(1)
                
                results.append({
                    "type": loader_type,
                    "filename": filename,
                    "location": f"{path}:{line_num}"
                })
    return results

def extract_secrets_risks(matches):
    results = []
    for m in matches:
        path = m['path']['text']
        line_num = m['line_number']
        content = m['lines']['text'].strip()
        
        results.append({
            "pattern_matched": content,
            "location": f"{path}:{line_num}"
        })
    return results

def main():
    env_matches = parse_rg_json('/tmp/env_vars_raw.json')
    config_matches = parse_rg_json('/tmp/config_loaders_raw.json')
    secrets_matches = parse_rg_json('/tmp/secrets_risk_raw.json')
    
    env_vars = extract_env_vars(env_matches)
    config_loaders = extract_config_loaders(config_matches)
    secrets_risks = extract_secrets_risks(secrets_matches)
    
    with open('ENV_VARS.json', 'w') as f:
        json.dump(env_vars, f, indent=2)
    
    with open('CONFIG_LOADERS.json', 'w') as f:
        json.dump(config_loaders, f, indent=2)
    
    with open('SECRETS_RISK_LOCATIONS.json', 'w') as f:
        json.dump(secrets_risks, f, indent=2)

if __name__ == "__main__":
    main()
