from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import cv2
import numpy as np


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    if not np.isfinite(f):
        return default
    return f


def _normalize_zones(zones: Any) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    if not isinstance(zones, Sequence):
        return out

    for item in zones:
        if not isinstance(item, Sequence) or len(item) < 2:
            continue
        x = _safe_float(item[0], np.nan)
        y = _safe_float(item[1], np.nan)
        if not np.isfinite(x) or not np.isfinite(y):
            continue
        out.append((int(round(x)), int(round(y))))

    # Stable deterministic order
    out.sort(key=lambda p: (p[0], p[1]))
    return out


def _format_zone_sample(zones: list[tuple[int, int]], max_items: int = 3) -> str:
    if not zones:
        return ""
    sample = zones[:max_items]
    return ", ".join(f"({x},{y})" for x, y in sample)


def generate_recommendations(insights):
    """
    Generate deterministic, rule-based junction redesign suggestions.

    Input keys (expected):
      density_zones, stopped_zones, avg_speed, vehicle_count
    """
    insights = insights or {}

    density_zones = _normalize_zones(insights.get("density_zones", []))
    stopped_zones = _normalize_zones(insights.get("stopped_zones", []))
    avg_speed = _safe_float(insights.get("avg_speed", 0.0), 0.0)
    vehicle_count = int(round(_safe_float(insights.get("vehicle_count", 0), 0.0)))

    recommendations: list[str] = []

    # 1) Density-driven redesign
    if len(density_zones) >= 5:
        zone_hint = _format_zone_sample(density_zones)
        recommendations.append(
            f"Widen approach lanes or add turn pockets near high-density zones {zone_hint}."
        )
    elif len(density_zones) >= 2:
        zone_hint = _format_zone_sample(density_zones)
        recommendations.append(
            f"Reallocate lane usage and improve channelization near recurring density zones {zone_hint}."
        )

    # 2) Stoppage / bottleneck handling
    if len(stopped_zones) >= 4:
        zone_hint = _format_zone_sample(stopped_zones)
        recommendations.append(
            f"Remove bottlenecks by redesigning merge/conflict points around stopped-vehicle zones {zone_hint}."
        )
    elif len(stopped_zones) >= 1:
        zone_hint = _format_zone_sample(stopped_zones)
        recommendations.append(
            f"Audit curbside friction and signal phase conflicts near stopped zones {zone_hint}."
        )

    # 3) Flow quality from speed
    if avg_speed < 8.0:
        recommendations.append(
            "Apply aggressive signal retiming (longer coordinated green waves) to improve corridor throughput."
        )
    elif avg_speed < 15.0:
        recommendations.append(
            "Enable adaptive signal coordination in peak windows to reduce delay and queue spillback."
        )

    # 4) Demand-aware control
    if vehicle_count >= 80:
        recommendations.append(
            "Introduce peak-hour demand management (turn restrictions or metering) to stabilize junction inflow."
        )

    if not recommendations:
        recommendations.append(
            "Current operation is stable; keep geometry unchanged and continue monitoring hotspot indicators."
        )

    return recommendations


def format_recommendations(recommendations):
    """Format recommendations as readable bullet points."""
    recommendations = recommendations or []
    if not recommendations:
        return "- No recommendations."
    return "\n".join(f"- {item}" for item in recommendations)


def draw_recommendations(frame, insights):
    """
    Draw recommendation overlay and highlight affected zones.

    - Density zones: yellow circles
    - Stopped zones: red circles
    - Top-left recommendation panel
    """
    if frame is None:
        return frame

    out = frame.copy()
    h, w = out.shape[:2]

    insights = insights or {}
    density_zones = _normalize_zones(insights.get("density_zones", []))
    stopped_zones = _normalize_zones(insights.get("stopped_zones", []))

    # Zone highlights
    for x, y in density_zones:
        cv2.circle(out, (x, y), 14, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(out, "D", (x - 5, y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2, cv2.LINE_AA)

    for x, y in stopped_zones:
        cv2.circle(out, (x, y), 16, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(out, "S", (x - 5, y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2, cv2.LINE_AA)

    recs = generate_recommendations(insights)
    bullets = format_recommendations(recs).splitlines()

    # Keep panel compact for real-time readability.
    max_lines = 5
    lines = ["Recommendations:"] + bullets[:max_lines]

    panel_x, panel_y = 10, 10
    line_h = 20
    panel_h = 12 + line_h * len(lines) + 8
    panel_w = min(max(420, int(w * 0.55)), max(200, w - 20))

    cv2.rectangle(out, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), (0, 0, 0), -1)

    for idx, line in enumerate(lines):
        y = panel_y + 24 + idx * line_h
        txt = line
        if len(txt) > 95:
            txt = txt[:92] + "..."
        color = (255, 255, 255) if idx == 0 else (210, 255, 210)
        scale = 0.58 if idx == 0 else 0.48
        cv2.putText(out, txt, (panel_x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)

    return out
