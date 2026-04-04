from __future__ import annotations

from collections.abc import Mapping
from typing import Any

# Approximate per-frame capacity for a busy multi-lane intersection.
# Higher than 20 to avoid saturating density at 1.0 in most frames.
DENSITY_REFERENCE_VEHICLES = 80.0

# Speed (km/h) considered close to free-flow for this scene type.
FREE_FLOW_SPEED_KMH = 24.0

_VEHICLE_CLASS_ALIASES = {
    "car": "car",
    "bus": "bus",
    "bike": "bike",
    "bicycle": "bike",
    "motorbike": "bike",
    "motorcycle": "bike",
    "truck": "truck",
    "lorry": "truck",
}


def _get_track_value(track: Any, key: str, default: Any = None) -> Any:
    if isinstance(track, Mapping):
        return track.get(key, default)
    return getattr(track, key, default)


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_speed(track: Any) -> float | None:
    speed = _safe_float(_get_track_value(track, "speed"))
    if speed is not None:
        return abs(speed)

    # Some pipeline stages store speed as km/h under `speed_kmh`.
    speed_kmh = _safe_float(_get_track_value(track, "speed_kmh"))
    if speed_kmh is not None:
        return abs(speed_kmh)

    vx = _safe_float(_get_track_value(track, "vx"))
    vy = _safe_float(_get_track_value(track, "vy"))
    if vx is None or vy is None:
        return None

    return (vx * vx + vy * vy) ** 0.5


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def compute_metrics(tracks: list[Any] | None) -> dict[str, float | int]:
    track_list = tracks or []
    vehicle_count = len(track_list)

    speed_sum = 0.0
    speed_count = 0

    for track in track_list:
        speed = _extract_speed(track)
        if speed is None:
            continue
        speed_sum += speed
        speed_count += 1

    avg_speed = speed_sum / speed_count if speed_count > 0 else 0.0
    density = min(vehicle_count / DENSITY_REFERENCE_VEHICLES, 1.0)

    return {
        "vehicle_count": vehicle_count,
        "avg_speed": avg_speed,
        "density": density,
    }


def detect_congestion(metrics: Mapping[str, Any] | None) -> str:
    metrics_map = metrics or {}
    density = _clamp(_safe_float(metrics_map.get("density")) or 0.0, 0.0, 1.0)
    avg_speed = max(0.0, _safe_float(metrics_map.get("avg_speed")) or 0.0)

    # 0.0 = very slow traffic, 1.0 = free-flow traffic.
    speed_ratio = _clamp(avg_speed / FREE_FLOW_SPEED_KMH, 0.0, 1.0)
    speed_slowdown = 1.0 - speed_ratio

    # Blend crowding and slowdown into a congestion score.
    congestion_score = 0.65 * density + 0.35 * speed_slowdown

    # Hard overrides for obvious jams.
    if density >= 0.8 and avg_speed <= 12.0:
        return "HIGH"
    if density >= 0.65 and avg_speed <= 7.0:
        return "HIGH"

    if congestion_score >= 0.68:
        return "HIGH"
    if congestion_score >= 0.38:
        return "MEDIUM"
    return "LOW"


def classify_vehicle_counts(tracks: list[Any] | None) -> dict[str, int]:
    counts = {"car": 0, "bus": 0, "bike": 0, "truck": 0}

    for track in tracks or []:
        raw_class = _get_track_value(track, "class")
        if raw_class is None:
            continue

        normalized = str(raw_class).strip().lower()
        canonical = _VEHICLE_CLASS_ALIASES.get(normalized)
        if canonical is None:
            continue

        counts[canonical] += 1

    return counts
