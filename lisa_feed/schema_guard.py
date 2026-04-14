from __future__ import annotations

from typing import Any


REQUIRED_PACKET_FIELDS = {
    "source_system",
    "packet_type",
    "generated_at",
    "lane",
    "priority",
    "summary",
    "items",
    "evidence_refs",
    "fresh_until",
    "publish_status",
    "schema_version",
}


def validate_packet_contract(packet: dict[str, Any]) -> None:
    missing = [f for f in REQUIRED_PACKET_FIELDS if f not in packet]
    if missing:
        raise ValueError(f"Packet contract missing fields: {missing}")
    if not isinstance(packet["items"], list):
        raise ValueError("Packet items must be a list.")


def assert_backward_compatible(packet: dict[str, Any], expected_major: str) -> None:
    version = str(packet.get("schema_version", ""))
    if "." not in version:
        raise ValueError(f"Invalid schema_version '{version}'.")
    major = version.split(".", 1)[0]
    if major != expected_major:
        raise ValueError(
            f"Backward compatibility check failed: expected major {expected_major}, got {major}."
        )

