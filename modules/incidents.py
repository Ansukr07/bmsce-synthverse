from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
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


def _extract_track_id(track: Any) -> Any:
    if isinstance(track, Mapping):
        tid = track.get("id")
        if tid is None:
            tid = track.get("tracked_id")
        return tid

    tid = getattr(track, "id", None)
    if tid is None:
        tid = getattr(track, "tracked_id", None)
    return tid


def _extract_speed(track: Any) -> float:
    if isinstance(track, Mapping):
        if "speed" in track:
            return max(0.0, _safe_float(track.get("speed"), 0.0))
        if "speed_kmh" in track:
            return max(0.0, _safe_float(track.get("speed_kmh"), 0.0))
        return 9999.0

    v = getattr(track, "speed", None)
    if v is None:
        v = getattr(track, "speed_kmh", None)
    if v is None:
        return 9999.0
    return max(0.0, _safe_float(v, 0.0))


def _extract_xy(track: Any) -> tuple[float | None, float | None]:
    if isinstance(track, Mapping):
        x = _safe_float(track.get("x"), np.nan)
        y = _safe_float(track.get("y"), np.nan)
        if np.isfinite(x) and np.isfinite(y):
            return x, y

        ref = track.get("reference_point")
        if isinstance(ref, Sequence) and len(ref) >= 2:
            x = _safe_float(ref[0], np.nan)
            y = _safe_float(ref[1], np.nan)
            if np.isfinite(x) and np.isfinite(y):
                return x, y

        bbox = track.get("bbox_2d")
        if isinstance(bbox, Sequence) and len(bbox) >= 4:
            x1 = _safe_float(bbox[0], np.nan)
            y1 = _safe_float(bbox[1], np.nan)
            x2 = _safe_float(bbox[2], np.nan)
            y2 = _safe_float(bbox[3], np.nan)
            if np.isfinite(x1) and np.isfinite(y1) and np.isfinite(x2) and np.isfinite(y2):
                return (x1 + x2) * 0.5, (y1 + y2) * 0.5

        return None, None

    x = _safe_float(getattr(track, "x", np.nan), np.nan)
    y = _safe_float(getattr(track, "y", np.nan), np.nan)
    if np.isfinite(x) and np.isfinite(y):
        return x, y
    return None, None


class IncidentDetector:
    def __init__(self):
        self.stop_time: dict[Any, int] = {}

    def detect_stopped_vehicles(self, tracks, threshold_frames: int = 30):
        """
        If speed < 1 for consecutive frames, mark as stopped.

        Returns
        -------
        list
            Stopped vehicle IDs.
        """
        threshold_frames = max(1, int(threshold_frames))
        stopped_ids: list[Any] = []
        active_ids: set[Any] = set()

        for track in tracks or []:
            tid = _extract_track_id(track)
            if tid is None:
                continue

            active_ids.add(tid)
            speed = _extract_speed(track)

            if speed < 1.0:
                self.stop_time[tid] = self.stop_time.get(tid, 0) + 1
            else:
                self.stop_time.pop(tid, None)

            if self.stop_time.get(tid, 0) >= threshold_frames:
                stopped_ids.append(tid)

        # Remove stale IDs not present in this frame.
        stale_ids = [tid for tid in self.stop_time if tid not in active_ids]
        for tid in stale_ids:
            self.stop_time.pop(tid, None)

        return sorted(stopped_ids, key=lambda v: str(v))

    def detect_abnormal_clusters(self, tracks, radius: float = 50, min_neighbors: int = 5):
        """
        Detect local hotspots where vehicles have too many nearby neighbors.

        Returns
        -------
        list[tuple[int, int]]
            Cluster centers (x, y).
        """
        radius = max(1.0, float(radius))
        min_neighbors = max(1, int(min_neighbors))

        coords: list[tuple[float, float]] = []
        for track in tracks or []:
            x, y = _extract_xy(track)
            if x is None or y is None:
                continue
            coords.append((x, y))

        if not coords:
            return []

        points = np.asarray(coords, dtype=np.float32)
        n = points.shape[0]
        if n < (min_neighbors + 1):
            return []

        # Spatial hashing for near-linear candidate lookup.
        cell_size = radius
        cell_coords = np.floor(points / cell_size).astype(np.int32)

        buckets: dict[tuple[int, int], list[int]] = defaultdict(list)
        for idx, cell in enumerate(cell_coords):
            buckets[(int(cell[0]), int(cell[1]))].append(idx)

        r2 = radius * radius
        neighbor_counts = np.zeros(n, dtype=np.int32)

        for i, cell in enumerate(cell_coords):
            cx, cy = int(cell[0]), int(cell[1])
            candidates: list[int] = []

            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):
                    candidates.extend(buckets.get((cx + ox, cy + oy), []))

            if not candidates:
                continue

            cand_idx = np.asarray(candidates, dtype=np.int32)
            delta = points[cand_idx] - points[i]
            d2 = np.einsum("ij,ij->i", delta, delta)
            neighbor_counts[i] = int(np.count_nonzero(d2 <= r2) - 1)

        hotspot_idx = np.where(neighbor_counts >= min_neighbors)[0]
        if hotspot_idx.size == 0:
            return []

        # Aggregate to one center per occupied hotspot cell for stable output.
        grouped: dict[tuple[int, int], list[int]] = defaultdict(list)
        for idx in hotspot_idx.tolist():
            cell = cell_coords[idx]
            grouped[(int(cell[0]), int(cell[1]))].append(idx)

        centers: list[tuple[int, int]] = []
        for key in sorted(grouped):
            idxs = np.asarray(grouped[key], dtype=np.int32)
            center = np.mean(points[idxs], axis=0)
            centers.append((int(round(float(center[0]))), int(round(float(center[1])))))

        return centers

    def process(self, tracks):
        """
        Run all incident detectors for a frame.

        Returns
        -------
        dict
            {
                "stopped": [...],
                "clusters": [(x, y), ...],
                "stopped_points": [{"id": id, "x": x, "y": y}, ...]
            }
        """
        stopped_ids = self.detect_stopped_vehicles(tracks)
        clusters = self.detect_abnormal_clusters(tracks)

        id_to_point: dict[Any, tuple[int, int]] = {}
        for track in tracks or []:
            tid = _extract_track_id(track)
            if tid is None:
                continue
            x, y = _extract_xy(track)
            if x is None or y is None:
                continue
            id_to_point[tid] = (int(round(x)), int(round(y)))

        stopped_points = []
        for tid in stopped_ids:
            pt = id_to_point.get(tid)
            if pt is None:
                continue
            stopped_points.append({"id": tid, "x": pt[0], "y": pt[1]})

        return {
            "stopped": stopped_ids,
            "clusters": clusters,
            "stopped_points": stopped_points,
        }


def draw_incidents(frame, incidents):
    """
    Draw incident overlays:
    - RED box around stopped vehicles
    - Circle around cluster regions

    Returns a new overlaid frame (input is not modified).
    """
    if frame is None:
        return frame

    out = frame.copy()
    incidents = incidents or {}

    stopped_points = incidents.get("stopped_points", [])
    clusters = incidents.get("clusters", [])

    # Stopped vehicles: red square + ID label.
    for item in stopped_points:
        x = int(item.get("x", 0))
        y = int(item.get("y", 0))
        tid = item.get("id")

        half = 16
        cv2.rectangle(out, (x - half, y - half), (x + half, y + half), (0, 0, 255), 2)
        cv2.putText(
            out,
            f"STOP {tid}",
            (x - half, y - half - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )

    # Cluster hotspots: orange circle + label.
    for cx, cy in clusters:
        cx = int(cx)
        cy = int(cy)
        cv2.circle(out, (cx, cy), 28, (0, 165, 255), 2, cv2.LINE_AA)
        cv2.putText(
            out,
            "CLUSTER",
            (cx - 30, cy - 34),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 165, 255),
            2,
            cv2.LINE_AA,
        )

    # Fallback summary text when only IDs are available.
    if not stopped_points and incidents.get("stopped"):
        txt = "Stopped IDs: " + ", ".join(str(i) for i in incidents["stopped"][:8])
        cv2.putText(out, txt, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2, cv2.LINE_AA)

    return out
