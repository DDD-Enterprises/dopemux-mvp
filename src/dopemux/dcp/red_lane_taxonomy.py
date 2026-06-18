import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


DEFAULT_TAXONOMY_REL_PATH = "schemas/dcp/dcp_red_lane_taxonomy.instance.json"


@dataclass
class RedLaneTaxonomyInfo:
    taxonomy_id: str = "UNKNOWN"
    taxonomy_path: str = DEFAULT_TAXONOMY_REL_PATH
    taxonomy_lane_ids: List[str] = field(default_factory=list)


def load_red_lane_taxonomy_info(
    repo_root: str,
    taxonomy_rel_path: str = DEFAULT_TAXONOMY_REL_PATH,
) -> RedLaneTaxonomyInfo:
    taxonomy_path = Path(repo_root) / taxonomy_rel_path
    if not taxonomy_path.exists():
        return RedLaneTaxonomyInfo(taxonomy_path=taxonomy_rel_path)

    data = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    lane_ids = [
        lane["id"]
        for lane in data.get("lanes", [])
        if isinstance(lane, dict) and isinstance(lane.get("id"), str)
    ]
    return RedLaneTaxonomyInfo(
        taxonomy_id=data.get("taxonomy_id", "UNKNOWN"),
        taxonomy_path=taxonomy_rel_path,
        taxonomy_lane_ids=lane_ids,
    )
