"""Common DopeconBridge client for Dopemux services."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from typing import Any, Dict, List, Mapping, MutableMapping, Optional

import httpx


DEFAULT_BRIDGE_URL = os.getenv("DOPECON_BRIDGE_URL", "http://localhost:3016")
DEFAULT_BRIDGE_TOKEN = os.getenv("DOPECON_BRIDGE_TOKEN")
DEFAULT_SOURCE_PLANE = os.getenv("DOPECON_BRIDGE_SOURCE_PLANE", "cognitive_plane")


class DopeconBridgeError(RuntimeError):
    """Raised when the DopeconBridge returns an error response."""


@dataclass(frozen=True)
class DopeconBridgeConfig:
    """Configuration shared by sync/async clients."""

    base_url: str = DEFAULT_BRIDGE_URL
    token: Optional[str] = DEFAULT_BRIDGE_TOKEN
    timeout: float = 10.0
    source_plane: str = DEFAULT_SOURCE_PLANE

    @classmethod
    def from_env(
        cls,
        *,
        url_var: str = "DOPECON_BRIDGE_URL",
        token_var: str = "DOPECON_BRIDGE_TOKEN",
        plane_var: str = "DOPECON_BRIDGE_SOURCE_PLANE",
        default_url: str = "http://localhost:3016",
    ) -> "DopeconBridgeConfig":
        return cls(
            base_url=os.getenv(url_var, default_url),
            token=os.getenv(token_var),
            source_plane=os.getenv(plane_var, DEFAULT_SOURCE_PLANE),
        )


@dataclass(frozen=True)
class PublishEventResponse:
    status: str
    message_id: str
    stream: str
    event_type: str
    timestamp: str

    @classmethod
    def from_json(cls, payload: Mapping[str, Any]) -> "PublishEventResponse":
        return cls(
            status=str(payload.get("status", "")),
            message_id=str(payload.get("message_id", "")),
            stream=str(payload.get("stream", "")),
            event_type=str(payload.get("event_type", "")),
            timestamp=str(payload.get("timestamp", "")),
        )


@dataclass(frozen=True)
class StreamInfo:
    stream: str
    info: Mapping[str, Any]
    instance: Optional[str]

    @classmethod
    def from_json(cls, payload: Mapping[str, Any]) -> "StreamInfo":
        return cls(
            stream=str(payload.get("stream", "")),
            info=payload.get("info", {}),
            instance=payload.get("instance"),
        )


@dataclass(frozen=True)
class EventHistory:
    stream: str
    count: int
    events: List[Mapping[str, Any]]
    instance: Optional[str]

    @classmethod
    def from_json(cls, payload: Mapping[str, Any]) -> "EventHistory":
        return cls(
            stream=str(payload.get("stream", "")),
            count=int(payload.get("count", 0)),
            events=list(payload.get("events", [])),
            instance=payload.get("instance"),
        )


@dataclass(frozen=True)
class CrossPlaneRouteResponse:
    success: bool
    data: Mapping[str, Any]
    error: Optional[str]
    correlation_id: Optional[str]

    @classmethod
    def from_json(cls, payload: Mapping[str, Any]) -> "CrossPlaneRouteResponse":
        return cls(
            success=bool(payload.get("success", False)),
            data=payload.get("data", {}),
            error=payload.get("error"),
            correlation_id=payload.get("correlation_id"),
        )


@dataclass(frozen=True)
class DecisionList:
    count: int
    items: List[Mapping[str, Any]]
    query: Optional[str] = None

    @classmethod
    def from_json(cls, payload: Mapping[str, Any]) -> "DecisionList":
        return cls(
            count=int(payload.get("count", 0)),
            items=list(payload.get("items", [])),
            query=payload.get("query"),
        )


class _BaseBridgeClient:
    def __init__(
        self,
        config: Optional[DopeconBridgeConfig] = None,
        *,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        cfg = config or DopeconBridgeConfig(
            base_url=base_url or DEFAULT_BRIDGE_URL,
            token=token if token is not None else DEFAULT_BRIDGE_TOKEN,
            timeout=timeout or 10.0,
        )
        self._config = cfg

    @property
    def base_url(self) -> str:
        return self._config.base_url.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": "dopemux-dopecon-bridge-client",
            "X-Source-Plane": self._config.source_plane,
        }
        if self._config.token:
            headers["Authorization"] = f"Bearer {self._config.token}"
        return headers

    @staticmethod
    def _parse_response(response: httpx.Response) -> MutableMapping[str, Any]:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:  # pragma: no cover - exercised in tests
            raise DopeconBridgeError(
                f"DopeconBridge error ({exc.response.status_code}): {exc.response.text}"
            ) from exc
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise DopeconBridgeError("DopeconBridge returned invalid JSON") from exc


class DopeconBridgeClient(_BaseBridgeClient):
    """Synchronous DopeconBridge client."""

    def __init__(
        self,
        config: Optional[DopeconBridgeConfig] = None,
        *,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        super().__init__(config, base_url=base_url, token=token, timeout=timeout)
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self._config.timeout,
            headers=self._headers(),
            transport=transport,
        )

    def __enter__(self) -> "DopeconBridgeClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        self.close()

    def close(self) -> None:
        self._client.close()

    # ------------------------------------------------------------------
    # Endpoint helpers
    # ------------------------------------------------------------------

    def publish_event(
        self,
        *,
        event_type: str,
        data: Mapping[str, Any],
        stream: str = "dopemux:events",
        source: Optional[str] = None,
    ) -> PublishEventResponse:
        payload = {
            "stream": stream,
            "event_type": event_type,
            "data": dict(data),
            "source": source,
        }
        resp = self._client.post("/events", json=payload)
        return PublishEventResponse.from_json(self._parse_response(resp))

    def get_stream_info(self, stream: str = "dopemux:events") -> StreamInfo:
        resp = self._client.get(f"/events/{stream}")
        return StreamInfo.from_json(self._parse_response(resp))

    def get_event_history(self, *, stream: str = "dopemux:events", count: int = 100) -> EventHistory:
        resp = self._client.get("/events/history", params={"stream": stream, "count": count})
        return EventHistory.from_json(self._parse_response(resp))

    def save_custom_data(
        self,
        *,
        workspace_id: str,
        category: str,
        key: str,
        value: Mapping[str, Any],
    ) -> bool:
        payload = {
            "workspace_id": workspace_id,
            "category": category,
            "key": key,
            "value": dict(value),
        }
        resp = self._client.post("/kg/custom_data", json=payload)
        data = self._parse_response(resp)
        return bool(data.get("success", False))

    def get_custom_data(
        self,
        *,
        workspace_id: str,
        category: str,
        key: Optional[str] = None,
        limit: int = 50,
    ) -> List[Mapping[str, Any]]:
        params: Dict[str, Any] = {
            "workspace_id": workspace_id,
            "category": category,
            "limit": limit,
        }
        if key:
            params["key"] = key
        resp = self._client.get("/kg/custom_data", params=params)
        data = self._parse_response(resp)
        return list(data.get("data", []))

    def route_pm(
        self,
        *,
        operation: str,
        data: Mapping[str, Any],
        requester: str,
        source: str = "cognitive",
    ) -> CrossPlaneRouteResponse:
        payload = {
            "source": source,
            "operation": operation,
            "data": dict(data),
            "requester": requester,
        }
        resp = self._client.post("/route/pm", json=payload)
        return CrossPlaneRouteResponse.from_json(self._parse_response(resp))

    def route_cognitive(
        self,
        *,
        operation: str,
        data: Mapping[str, Any],
        requester: str,
        source: str = "pm",
    ) -> CrossPlaneRouteResponse:
        payload = {
            "source": source,
            "operation": operation,
            "data": dict(data),
            "requester": requester,
        }
        resp = self._client.post("/route/cognitive", json=payload)
        return CrossPlaneRouteResponse.from_json(self._parse_response(resp))

    def recent_decisions(
        self,
        *,
        workspace_id: Optional[str] = None,
        limit: int = 20,
    ) -> DecisionList:
        params: Dict[str, Any] = {"limit": limit}
        if workspace_id:
            params["workspace_id"] = workspace_id
        resp = self._client.get("/ddg/decisions/recent", params=params)
        return DecisionList.from_json(self._parse_response(resp))

    def search_decisions(
        self,
        *,
        query: str,
        workspace_id: Optional[str] = None,
        limit: int = 20,
    ) -> DecisionList:
        params: Dict[str, Any] = {"q": query, "limit": limit}
        if workspace_id:
            params["workspace_id"] = workspace_id
        resp = self._client.get("/ddg/decisions/search", params=params)
        return DecisionList.from_json(self._parse_response(resp))

    def related_decisions(self, *, decision_id: str, k: int = 10) -> DecisionList:
        resp = self._client.get("/ddg/decisions/related", params={"decision_id": decision_id, "k": k})
        data = self._parse_response(resp)
        items = data.get("items", [])
        return DecisionList(count=len(items), items=items, query=str(data.get("decision_id")))

    def related_text(
        self,
        *,
        query: str,
        workspace_id: Optional[str] = None,
        k: int = 10,
    ) -> DecisionList:
        params: Dict[str, Any] = {"q": query, "k": k}
        if workspace_id:
            params["workspace_id"] = workspace_id
        resp = self._client.get("/ddg/decisions/related-text", params=params)
        return DecisionList.from_json(self._parse_response(resp))

    # ------------------------------------------------------------------
    # ConPort Decision/Progress endpoints (for service migration)
    # ------------------------------------------------------------------

    def create_decision(
        self,
        *,
        summary: str,
        rationale: str,
        implementation_details: Optional[str] = None,
        tags: Optional[List[str]] = None,
        workspace_id: Optional[str] = None,
    ) -> Mapping[str, Any]:
        """Create a decision in ConPort via DopeconBridge."""
        payload: Dict[str, Any] = {
            "summary": summary,
            "rationale": rationale,
        }
        if implementation_details:
            payload["implementation_details"] = implementation_details
        if tags:
            payload["tags"] = tags
        if workspace_id:
            payload["workspace_id"] = workspace_id
        
        resp = self._client.post("/kg/decisions", json=payload)
        return self._parse_response(resp)

    def create_progress_entry(
        self,
        *,
        description: str,
        status: str = "TODO",
        parent_id: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        workspace_id: Optional[str] = None,
    ) -> Mapping[str, Any]:
        """Create a progress entry in ConPort via DopeconBridge."""
        payload: Dict[str, Any] = {
            "description": description,
            "status": status,
        }
        if parent_id:
            payload["parent_id"] = parent_id
        if metadata:
            payload["metadata"] = dict(metadata)
        if workspace_id:
            payload["workspace_id"] = workspace_id
        
        resp = self._client.post("/kg/progress", json=payload)
        return self._parse_response(resp)

    def create_link(
        self,
        *,
        source_item_type: str,
        source_item_id: str,
        target_item_type: str,
        target_item_id: str,
        relationship_type: str,
        description: Optional[str] = None,
    ) -> Mapping[str, Any]:
        """Create a link between items in ConPort via DopeconBridge."""
        payload = {
            "source_item_type": source_item_type,
            "source_item_id": source_item_id,
            "target_item_type": target_item_type,
            "target_item_id": target_item_id,
            "relationship_type": relationship_type,
        }
        if description:
            payload["description"] = description
        
        resp = self._client.post("/kg/links", json=payload)
        return self._parse_response(resp)

    def get_progress_entries(
        self,
        *,
        workspace_id: str,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> List[Mapping[str, Any]]:
        """Get progress entries from ConPort via DopeconBridge."""
        params: Dict[str, Any] = {
            "workspace_id": workspace_id,
            "limit": limit,
        }
        if status:
            params["status"] = status
        
        resp = self._client.get("/kg/progress", params=params)
        data = self._parse_response(resp)
        return list(data.get("entries", []))


class AsyncDopeconBridgeClient(_BaseBridgeClient):
    """Async counterpart using httpx.AsyncClient."""

    def __init__(
        self,
        config: Optional[DopeconBridgeConfig] = None,
        *,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        super().__init__(config, base_url=base_url, token=token, timeout=timeout)
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self._config.timeout,
            headers=self._headers(),
            transport=transport,
        )

    async def __aenter__(self) -> "AsyncDopeconBridgeClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def publish_event(
        self,
        *,
        event_type: str,
        data: Mapping[str, Any],
        stream: str = "dopemux:events",
        source: Optional[str] = None,
    ) -> PublishEventResponse:
        payload = {
            "stream": stream,
            "event_type": event_type,
            "data": dict(data),
            "source": source,
        }
        resp = await self._client.post("/events", json=payload)
        return PublishEventResponse.from_json(self._parse_response(resp))

    async def get_stream_info(self, stream: str = "dopemux:events") -> StreamInfo:
        resp = await self._client.get(f"/events/{stream}")
        return StreamInfo.from_json(self._parse_response(resp))

    async def get_event_history(self, *, stream: str = "dopemux:events", count: int = 100) -> EventHistory:
        resp = await self._client.get("/events/history", params={"stream": stream, "count": count})
        return EventHistory.from_json(self._parse_response(resp))

    async def save_custom_data(
        self,
        *,
        workspace_id: str,
        category: str,
        key: str,
        value: Mapping[str, Any],
    ) -> bool:
        payload = {
            "workspace_id": workspace_id,
            "category": category,
            "key": key,
            "value": dict(value),
        }
        resp = await self._client.post("/kg/custom_data", json=payload)
        data = self._parse_response(resp)
        return bool(data.get("success", False))

    async def get_custom_data(
        self,
        *,
        workspace_id: str,
        category: str,
        key: Optional[str] = None,
        limit: int = 50,
    ) -> List[Mapping[str, Any]]:
        params: Dict[str, Any] = {
            "workspace_id": workspace_id,
            "category": category,
            "limit": limit,
        }
        if key:
            params["key"] = key
        resp = await self._client.get("/kg/custom_data", params=params)
        data = self._parse_response(resp)
        return list(data.get("data", []))

    async def route_pm(
        self,
        *,
        operation: str,
        data: Mapping[str, Any],
        requester: str,
        source: str = "cognitive",
    ) -> CrossPlaneRouteResponse:
        payload = {
            "source": source,
            "operation": operation,
            "data": dict(data),
            "requester": requester,
        }
        resp = await self._client.post("/route/pm", json=payload)
        return CrossPlaneRouteResponse.from_json(self._parse_response(resp))

    async def route_cognitive(
        self,
        *,
        operation: str,
        data: Mapping[str, Any],
        requester: str,
        source: str = "pm",
    ) -> CrossPlaneRouteResponse:
        payload = {
            "source": source,
            "operation": operation,
            "data": dict(data),
            "requester": requester,
        }
        resp = await self._client.post("/route/cognitive", json=payload)
        return CrossPlaneRouteResponse.from_json(self._parse_response(resp))

    async def recent_decisions(
        self,
        *,
        workspace_id: Optional[str] = None,
        limit: int = 20,
    ) -> DecisionList:
        params: Dict[str, Any] = {"limit": limit}
        if workspace_id:
            params["workspace_id"] = workspace_id
        resp = await self._client.get("/ddg/decisions/recent", params=params)
        return DecisionList.from_json(self._parse_response(resp))

    async def search_decisions(
        self,
        *,
        query: str,
        workspace_id: Optional[str] = None,
        limit: int = 20,
    ) -> DecisionList:
        params: Dict[str, Any] = {"q": query, "limit": limit}
        if workspace_id:
            params["workspace_id"] = workspace_id
        resp = await self._client.get("/ddg/decisions/search", params=params)
        return DecisionList.from_json(self._parse_response(resp))

    async def related_decisions(self, *, decision_id: str, k: int = 10) -> DecisionList:
        resp = await self._client.get("/ddg/decisions/related", params={"decision_id": decision_id, "k": k})
        data = self._parse_response(resp)
        items = data.get("items", [])
        return DecisionList(count=len(items), items=items, query=str(data.get("decision_id")))

    async def related_text(
        self,
        *,
        query: str,
        workspace_id: Optional[str] = None,
        k: int = 10,
    ) -> DecisionList:
        params: Dict[str, Any] = {"q": query, "k": k}
        if workspace_id:
            params["workspace_id"] = workspace_id
        resp = await self._client.get("/ddg/decisions/related-text", params=params)
        return DecisionList.from_json(self._parse_response(resp))

    # ------------------------------------------------------------------
    # ConPort Decision/Progress endpoints (for service migration)
    # ------------------------------------------------------------------

    async def create_decision(
        self,
        *,
        summary: str,
        rationale: str,
        implementation_details: Optional[str] = None,
        tags: Optional[List[str]] = None,
        workspace_id: Optional[str] = None,
    ) -> Mapping[str, Any]:
        """Create a decision in ConPort via DopeconBridge."""
        payload: Dict[str, Any] = {
            "summary": summary,
            "rationale": rationale,
        }
        if implementation_details:
            payload["implementation_details"] = implementation_details
        if tags:
            payload["tags"] = tags
        if workspace_id:
            payload["workspace_id"] = workspace_id
        
        resp = await self._client.post("/kg/decisions", json=payload)
        return self._parse_response(resp)

    async def create_progress_entry(
        self,
        *,
        description: str,
        status: str = "TODO",
        parent_id: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        workspace_id: Optional[str] = None,
    ) -> Mapping[str, Any]:
        """Create a progress entry in ConPort via DopeconBridge."""
        payload: Dict[str, Any] = {
            "description": description,
            "status": status,
        }
        if parent_id:
            payload["parent_id"] = parent_id
        if metadata:
            payload["metadata"] = dict(metadata)
        if workspace_id:
            payload["workspace_id"] = workspace_id
        
        resp = await self._client.post("/kg/progress", json=payload)
        return self._parse_response(resp)

    async def create_link(
        self,
        *,
        source_item_type: str,
        source_item_id: str,
        target_item_type: str,
        target_item_id: str,
        relationship_type: str,
        description: Optional[str] = None,
    ) -> Mapping[str, Any]:
        """Create a link between items in ConPort via DopeconBridge."""
        payload = {
            "source_item_type": source_item_type,
            "source_item_id": source_item_id,
            "target_item_type": target_item_type,
            "target_item_id": target_item_id,
            "relationship_type": relationship_type,
        }
        if description:
            payload["description"] = description
        
        resp = await self._client.post("/kg/links", json=payload)
        return self._parse_response(resp)

    async def get_progress_entries(
        self,
        *,
        workspace_id: str,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> List[Mapping[str, Any]]:
        """Get progress entries from ConPort via DopeconBridge."""
        params: Dict[str, Any] = {
            "workspace_id": workspace_id,
            "limit": limit,
        }
        if status:
            params["status"] = status
        
        resp = await self._client.get("/kg/progress", params=params)
        data = self._parse_response(resp)
        return list(data.get("entries", []))
