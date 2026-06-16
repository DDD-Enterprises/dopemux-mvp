## route smoke 2026-06-16T04:34:27Z

### http://localhost:3004/api/search/test-ws?q=test
http_code=200
body={"workspace_id": "test-ws", "query": "test", "results": {"decisions": [], "progress": []}, "total_count": 0}

### http://localhost:3004/api/unified-search?q=test&workspace_id=test-ws
http_code=400
body={"error": "user_id and query are required"}

### http://localhost:3004/api/workspace-relationships?workspace_id=test-ws
http_code=400
body={"error": "decision_id and user_id are required"}

## contract-shape route smoke 2026-06-16T04:34:43Z

### http://localhost:3004/api/unified-search?user_id=test-user&q=test
http_code=400
body={"error": "user_id and query are required"}

### http://localhost:3004/api/workspace-relationships?decision_id=1&user_id=test-user
http_code=500
body={"error": "'NoneType' object has no attribute 'get_related_decisions'"}

## post-dockerfile-fix route smoke 2026-06-16T04:36:09Z

### http://localhost:3004/api/search/test-ws?q=test
http_code=200
body={"workspace_id": "test-ws", "query": "test", "results": {"decisions": [], "progress": []}, "total_count": 0}

### http://localhost:3004/api/unified-search?user_id=test-user&query=test
http_code=500
body={"error": "column \"user_id\" does not exist"}

### http://localhost:3004/api/workspace-relationships?decision_id=1&user_id=test-user
http_code=500
body={"error": "column \"user_id\" does not exist"}

## final route smoke 2026-06-16T04:38:20Z

### http://localhost:3004/api/search/test-ws?q=test
http_code=200
body={"workspace_id": "test-ws", "query": "test", "results": {"decisions": [], "progress": []}, "total_count": 0}

### http://localhost:3004/api/unified-search?user_id=test-user&query=test
http_code=200
body={"results": [], "total": 0, "query": "test", "workspaces_searched": "all", "response_time_ms": 14.292}

### http://localhost:3004/api/workspace-relationships?decision_id=1&user_id=test-user
http_code=200
body={"root": "1", "nodes": [], "total_nodes": 0, "max_depth_reached": 0, "response_time_ms": 3.045}
