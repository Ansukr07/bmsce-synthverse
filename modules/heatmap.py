from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import cv2
import numpy as np


def _safe_float(value: Any) -> float | None:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(f):
        return None
    return f


def _extract_xy(track: Any) -> tuple[float | None, float | None]:
    if isinstance(track, Mapping):
        x = _safe_float(track.get("x"))
        y = _safe_float(track.get("y"))
        if x is not None and y is not None:
            return x, y

        ref = track.get("reference_point")
        if isinstance(ref, Sequence) and len(ref) >= 2:
            return _safe_float(ref[0]), _safe_float(ref[1])

        bbox = track.get("bbox_2d")
        if isinstance(bbox, Sequence) and len(bbox) >= 4:
            x1 = _safe_float(bbox[0])
            y1 = _safe_float(bbox[1])
            x2 = _safe_float(bbox[2])
            y2 = _safe_float(bbox[3])
            if None not in (x1, y1, x2, y2):
                return (x1 + x2) * 0.5, (y1 + y2) * 0.5

        return None, None

    x = _safe_float(getattr(track, "x", None))
    y = _safe_float(getattr(track, "y", None))
    return x, y


def generate_density_map(frame_shape, tracks, grid_size: int = 50):
    """
    Divide frame into grid cells and count vehicles per cell.

    Parameters
    ----------
    frame_shape : tuple
        Frame shape, typically frame.shape.
    tracks : iterable
        Vehicle tracks with {id, x, y, speed, class} style entries.
    grid_size : int
        Grid cell size in pixels.

    Returns
    -------
    np.ndarray
        2D float32 density map of shape [rows, cols].
    """
    if grid_size <= 0:
        raise ValueError("grid_size must be > 0")

    if frame_shape is None or len(frame_shape) < 2:
        return np.zeros((0, 0), dtype=np.float32)

    h = int(frame_shape[0])
    w = int(frame_shape[1])
    if h <= 0 or w <= 0:
        return np.zeros((0, 0), dtype=np.float32)

    rows = (h + grid_size - 1) // grid_size
    cols = (w + grid_size - 1) // grid_size
    density = np.zeros((rows, cols), dtype=np.float32)

    if not tracks:
        return density

    coords: list[tuple[float, float]] = []
    append = coords.append
    for track in tracks:
        x, y = _extract_xy(track)
        if x is None or y is None:
            continue
        append((x, y))

    if not coords:
        return density

    pts = np.asarray(coords, dtype=np.float32)
    xs = np.clip(pts[:, 0], 0, w - 1)
    ys = np.clip(pts[:, 1], 0, h - 1)

    grid_x = (xs // grid_size).astype(np.int32)
    grid_y = (ys // grid_size).astype(np.int32)

    np.add.at(density, (grid_y, grid_x), 1.0)
    return density


def normalize_density_map(density_map):
    """Normalize density values to [0, 1] with safe zero handling."""
    if density_map is None:
        return np.zeros((0, 0), dtype=np.float32)

    arr = np.asarray(density_map, dtype=np.float32)
    if arr.size == 0:
        return arr

    max_v = float(np.max(arr))
    if max_v <= 0.0:
        return np.zeros_like(arr, dtype=np.float32)

    return np.clip(arr / max_v, 0.0, 1.0)


def _density_to_bgr(value: float) -> tuple[int, int, int]:
    # Low -> Green, Mid -> Yellow, High -> Red
    if value <= 0.5:
        # Green (0,255,0) to Yellow (0,255,255)
        t = value / 0.5
        return (0, 255, int(round(255 * t)))
    # Yellow (0,255,255) to Red (0,0,255)
    t = (value - 0.5) / 0.5
    return (0, int(round(255 * (1.0 - t))), 255)


def draw_heatmap(frame, density_map, grid_size: int = 50):
    """
    Draw a semi-transparent heatmap overlay on top of frame.

    The input frame is not modified; a new frame is returned.
    """
    if frame is None:
        return frame

    out = frame.copy()

    if grid_size <= 0:
        return out

    arr = np.asarray(density_map, dtype=np.float32)
    if arr.size == 0:
        return out

    # Ensure values are in [0, 1] even if caller passed raw counts.
    if float(np.max(arr)) > 1.0 or float(np.min(arr)) < 0.0:
        arr = normalize_density_map(arr)

    h, w = out.shape[:2]
    rows, cols = arr.shape

    overlay = out.copy()
    alpha = 0.35

    hot_cells = np.argwhere(arr > 0.0)
    for gy, gx in hot_cells:
        y1 = int(gy * grid_size)
        y2 = int(min((gy + 1) * grid_size, h))
        x1 = int(gx * grid_size)
        x2 = int(min((gx + 1) * grid_size, w))

        if x1 >= x2 or y1 >= y2:
            continue

        color = _density_to_bgr(float(arr[gy, gx]))
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)

    cv2.addWeighted(overlay, alpha, out, 1.0 - alpha, 0.0, out)
    return out
