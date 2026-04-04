from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from copy import deepcopy
from types import MappingProxyType
from typing import Any


class TrafficStateManager:
    """Store and retrieve recent traffic states for replay overlays.

    Performance notes:
    - Stores immutable snapshots (tuple + MappingProxyType).
    - Avoids deep-copying on replay reads.
    - Uses bounded deque to keep memory stable in real-time loops.
    """

    __slots__ = ("_history",)

    def __init__(self, max_history: int = 300) -> None:
        if max_history <= 0:
            raise ValueError("max_history must be > 0")
        self._history: deque[tuple[tuple[Any, ...], Mapping[str, Any]]] = deque(maxlen=int(max_history))

    def _snapshot_tracks(self, tracks: list[dict[str, Any]] | None) -> tuple[Any, ...]:
        if not tracks:
            return tuple()

        snapshot: list[Any] = []
        append = snapshot.append

        for track in tracks:
            if isinstance(track, Mapping):
                # Fast, immutable snapshot for mapping-based tracks.
                append(MappingProxyType(dict(track)))
            else:
                # Rare fallback for non-mapping track objects.
                append(deepcopy(track))

        return tuple(snapshot)

    def _snapshot_metrics(self, metrics: dict[str, Any] | None) -> Mapping[str, Any]:
        if not metrics:
            return MappingProxyType({})

        if isinstance(metrics, Mapping):
            return MappingProxyType(dict(metrics))

        return MappingProxyType(deepcopy(metrics))

    def add_state(self, tracks: list[dict[str, Any]] | None, metrics: dict[str, Any] | None) -> None:
        """Store one frame state (tracks + metrics) as an immutable snapshot."""
        self._history.append((self._snapshot_tracks(tracks), self._snapshot_metrics(metrics)))

    def get_past_state(self, steps_back: int) -> dict[str, Any] | None:
        """Return an immutable snapshot from N steps back, or None if unavailable."""
        if steps_back < 0:
            return None
        if not self._history:
            return None

        idx = len(self._history) - 1 - int(steps_back)
        if idx < 0 or idx >= len(self._history):
            return None

        tracks_snapshot, metrics_snapshot = self._history[idx]
        return {
            "tracks": tracks_snapshot,
            "metrics": metrics_snapshot,
        }

    def clear(self) -> None:
        self._history.clear()

    def __len__(self) -> int:
        return len(self._history)
