def build_prescan_routing_plan(
    config: PrescanConfig,
    catalog: dict[str, Any],
    passes: list[str] | None,
) -> dict[str, Any]:
    requested_passes = [p for p in (passes or []) if p in PRESCAN_PASS_REQUIREMENTS]
    routes = [r for r in catalog.get("routes", []) if r.get("available")]
    selected_routes = {}
    
    for pass_id in requested_passes:
        required_tier = PRESCAN_PASS_REQUIREMENTS[pass_id]
        required_rank = PRESCAN_TIER_RANK[required_tier]
        
        candidates = [
            r for r in routes 
            if PRESCAN_TIER_RANK.get(str(r.get("prescan_tier")), 0) >= required_rank
        ]
        
        # Sort by tier rank then cost
        candidates.sort(key=lambda x: (PRESCAN_TIER_RANK.get(str(x.get("prescan_tier")), 99), float(x.get("pricing", {}).get("input_1m_usd", 999))))
        
        selected_routes[pass_id] = [
            {
                "provider": r["provider"],
                "model_id": r["model_id"],
                "api_key_env": r["api_key_env"],
                "tier": r["prescan_tier"]
            } for r in candidates
        ]

    return {
        "status": "PASS",
        "candidate_routes": selected_routes,
    }
