from __future__ import annotations

from functools import lru_cache
from typing import Any, Mapping

import cv2

from .metrics import detect_congestion


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def simulate_metrics(metrics: Mapping[str, Any], action: str) -> dict[str, float | int]:
    """
    Simulate alternative traffic outcomes without changing video content.

    Supported actions:
    - increase_green -> density *= 0.7, avg_speed *= 1.2
    - reduce_flow    -> vehicle_count *= 0.8
    """
    simulated = {
        "density": _clamp(_safe_float(metrics.get("density", 0.0)), 0.0, 1.0),
        "avg_speed": max(0.0, _safe_float(metrics.get("avg_speed", 0.0))),
        "vehicle_count": max(0, _safe_int(metrics.get("vehicle_count", 0))),
    }

    action_key = (action or "").strip().lower()

    if action_key == "increase_green":
        simulated["density"] = _clamp(float(simulated["density"]) * 0.7, 0.0, 1.0)
        simulated["avg_speed"] = max(0.0, float(simulated["avg_speed"]) * 1.2)

    elif action_key == "reduce_flow":
        simulated["vehicle_count"] = max(0, int(round(int(simulated["vehicle_count"]) * 0.8)))

    return simulated


def _congestion_color(level: str) -> tuple[int, int, int]:
    level = level.upper()
    if level == "HIGH":
        return (0, 0, 255)
    if level == "MEDIUM":
        return (0, 165, 255)
    return (0, 255, 0)


def _draw_metric_block(
    frame,
    x: int,
    y: int,
    title: str,
    metrics: Mapping[str, Any],
    congestion: str,
) -> None:
    vehicle_count = max(0, _safe_int(metrics.get("vehicle_count", 0)))
    avg_speed = max(0.0, _safe_float(metrics.get("avg_speed", 0.0)))

    white = (255, 255, 255)
    cv2.putText(frame, title, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, white, 2, cv2.LINE_AA)
    cv2.putText(
        frame,
        f"Vehicle Count: {vehicle_count}",
        (x, y + 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        white,
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"Avg Speed: {avg_speed:.2f}",
        (x, y + 58),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        white,
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"Congestion: {congestion}",
        (x, y + 86),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        _congestion_color(congestion),
        2,
        cv2.LINE_AA,
    )


@lru_cache(maxsize=16)
def _get_overlay_layout(width: int, height: int) -> tuple[int, int, int, int, int]:
    panel_h = min(130, max(110, height // 3))
    panel_w = min(320, max(240, (width // 2) - 20))
    top = 10
    left_x = 10
    right_x = max(left_x + panel_w + 10, width - panel_w - 10)
    return panel_h, panel_w, top, left_x, right_x


def draw_comparison_overlay(
    frame,
    real_metrics: Mapping[str, Any],
    sim_metrics: Mapping[str, Any],
    *,
    inplace: bool = False,
):
    """
    Draw overlay-only comparison panels and return a new frame.

    LEFT:  real metrics
    RIGHT: simulated metrics
    """
    out = frame if inplace else frame.copy()

    h, w = out.shape[:2]
    panel_h, panel_w, top, left_x, right_x = _get_overlay_layout(w, h)

    real_congestion = str(real_metrics.get("congestion") or detect_congestion(real_metrics)).upper()
    sim_congestion = str(sim_metrics.get("congestion") or detect_congestion(sim_metrics)).upper()

    cv2.rectangle(out, (left_x, top), (left_x + panel_w, top + panel_h), (0, 0, 0), -1)
    cv2.rectangle(out, (right_x, top), (right_x + panel_w, top + panel_h), (0, 0, 0), -1)

    _draw_metric_block(out, left_x + 10, top + 26, "REAL", real_metrics, real_congestion)
    _draw_metric_block(out, right_x + 10, top + 26, "SIMULATED", sim_metrics, sim_congestion)

    return out
