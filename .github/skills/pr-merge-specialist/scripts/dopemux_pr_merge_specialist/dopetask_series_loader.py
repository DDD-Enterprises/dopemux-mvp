"""DopetaskSeriesLoader — load and validate Task Packet series state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set

from .dopetask_series_models import (
    DopetaskPacketRecord,
    DopetaskSeriesIdentity,
    DopetaskSeriesResult,
    PacketStatus,
    SeriesStatus,
)


class SeriesSchemaError(ValueError):
    """Raised when a series state file is malformed."""


class DopetaskSeriesLoader:
    """Load, validate, and normalize Task Packet series state files."""

    REQUIRED_SERIES_FIELDS = {"series_id", "project_id", "status", "packets"}
    REQUIRED_PACKET_FIELDS = {"tp_id", "status"}

    def load_file(self, path: Path) -> DopetaskSeriesResult:
        """Load series state from a JSON file path."""
        if not path.exists():
            raise FileNotFoundError(f"Series state file not found: {path}")

        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SeriesSchemaError(f"Invalid JSON in series state: {exc}") from exc

        return self.parse_dict(raw_data)

    def parse_dict(self, data: Dict) -> DopetaskSeriesResult:
        """Parse and validate a dictionary representing series state."""
        # 0. Top-level shape validation (JSON list / null / scalar are not a series)
        if not isinstance(data, dict):
            raise SeriesSchemaError(
                f"Series state must be a JSON object, got {type(data).__name__}"
            )

        # 1. Basic Field Validation
        missing_fields = self.REQUIRED_SERIES_FIELDS - set(data.keys())
        if missing_fields:
            raise SeriesSchemaError(f"Missing required series fields: {', '.join(sorted(missing_fields))}")

        for field_name in ("series_id", "project_id"):
            field_value = data[field_name]
            if not isinstance(field_value, str) or not field_value.strip():
                raise SeriesSchemaError(
                    f"Series field '{field_name}' must be a non-empty string, got {field_value!r}"
                )

        series_status = data["status"]
        if not isinstance(series_status, str):
            raise SeriesSchemaError(
                f"Series field 'status' must be a string, got {type(series_status).__name__}"
            )

        raw_packets = data["packets"]
        if not isinstance(raw_packets, list):
            raise SeriesSchemaError(
                f"Series field 'packets' must be a list, got {type(raw_packets).__name__}"
            )

        # 2. Packet Parsing & Validation (all-or-nothing: any defect aborts before assembly)
        packet_records: List[DopetaskPacketRecord] = []
        packet_ids: Set[str] = set()

        for index, p_data in enumerate(raw_packets):
            if not isinstance(p_data, dict):
                raise SeriesSchemaError(
                    f"Packet at index {index} must be an object, got {type(p_data).__name__}"
                )

            p_missing = self.REQUIRED_PACKET_FIELDS - set(p_data.keys())
            if p_missing:
                raise SeriesSchemaError(
                    f"Packet missing fields: {', '.join(sorted(p_missing))} (packet index {index})"
                )

            p_id = p_data["tp_id"]
            if not isinstance(p_id, str) or not p_id.strip():
                raise SeriesSchemaError(f"Packet at index {index} has invalid tp_id: {p_id!r}")
            if p_id in packet_ids:
                raise SeriesSchemaError(f"Duplicate packet ID in series: {p_id}")
            packet_ids.add(p_id)

            p_status = p_data["status"]
            if not isinstance(p_status, str):
                raise SeriesSchemaError(
                    f"Packet '{p_id}' status must be a string, got {type(p_status).__name__}"
                )

            depends_on = p_data.get("depends_on", [])
            if not isinstance(depends_on, list):
                raise SeriesSchemaError(
                    f"Packet '{p_id}' depends_on must be a list, got {type(depends_on).__name__}"
                )
            for dep_id in depends_on:
                if not isinstance(dep_id, str) or not dep_id.strip():
                    raise SeriesSchemaError(
                        f"Packet '{p_id}' depends_on contains invalid packet ID: {dep_id!r}"
                    )

            record = DopetaskPacketRecord(
                tp_id=p_id,
                status=self._map_packet_status(p_status),
                raw_status=p_status,
                depends_on=depends_on,
                is_final=p_data.get("is_final", False),
                bundle_path=p_data.get("bundle_path"),
                title=p_data.get("title", "UNKNOWN"),
            )
            packet_records.append(record)

        # 3. DAG Validation
        self._validate_dag(packet_records)

        # 4. Identity & Result Assembly
        identity = DopetaskSeriesIdentity(
            series_id=data["series_id"],
            project_id=data["project_id"],
            version=data.get("version", "0.5.1")
        )

        return DopetaskSeriesResult(
            identity=identity,
            status=self._map_series_status(series_status),
            raw_status=series_status,
            packets=packet_records,
            allowed_actions=[],  # Populated by mapper/adapter
            computed_at=data.get("computed_at", "")
        )

    def _validate_dag(self, packets: List[DopetaskPacketRecord]) -> None:
        """Ensure no cycles and all dependencies exist."""
        packet_map = {p.tp_id: p for p in packets}
        
        # Check for missing references
        for p in packets:
            for dep_id in p.depends_on:
                if dep_id not in packet_map:
                    raise SeriesSchemaError(f"Packet '{p.tp_id}' depends on non-existent packet '{dep_id}'")

        # Cycle detection (DFS)
        visited: Set[str] = set()
        path: Set[str] = set()

        def has_cycle(p_id: str) -> bool:
            visited.add(p_id)
            path.add(p_id)
            for dep_id in packet_map[p_id].depends_on:
                if dep_id not in visited:
                    if has_cycle(dep_id):
                        return True
                elif dep_id in path:
                    return True
            path.remove(p_id)
            return False

        for p_id in packet_map:
            if p_id not in visited:
                if has_cycle(p_id):
                    raise SeriesSchemaError(f"Cycle detected in Task Packet series dependencies starting at '{p_id}'")

    def _map_packet_status(self, status: str) -> PacketStatus:
        try:
            return PacketStatus(status)
        except ValueError:
            return PacketStatus.UNKNOWN

    def _map_series_status(self, status: str) -> SeriesStatus:
        try:
            return SeriesStatus(status)
        except ValueError:
            return SeriesStatus.UNKNOWN
