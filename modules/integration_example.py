from __future__ import annotations

from typing import Any

from .simulation import draw_comparison_overlay, simulate_metrics
from .state_manager import TrafficStateManager


def process_frame_with_time_travel_and_simulation(
    frame,
    tracks: list[dict[str, Any]],
    metrics: dict[str, Any],
    state_manager: TrafficStateManager,
    replay_mode: bool,
    simulation_mode: bool,
    replay_steps: int = 30,
    simulation_action: str = "increase_green",
    overlay_inplace: bool = False,
):
    """
    Overlay-only processing helper for real-time loop integration.

    Notes:
    - Detection/tracking/mapping outputs are not modified.
    - Video content is not altered beyond overlays (drawn on a frame copy).
    """
    # 1) Store current state every frame.
    state_manager.add_state(tracks, metrics)

    overlay_tracks = tracks
    overlay_metrics = metrics

    # 2) Time travel: switch overlays to a past state.
    if replay_mode:
        past = state_manager.get_past_state(replay_steps)
        if past is not None:
            overlay_tracks = past["tracks"]
            overlay_metrics = past["metrics"]

    # 3) Simulation: compare current/replayed metrics to what-if metrics.
    if simulation_mode:
        sim_metrics = simulate_metrics(overlay_metrics, simulation_action)
        overlay_frame = draw_comparison_overlay(
            frame,
            overlay_metrics,
            sim_metrics,
            inplace=overlay_inplace,
        )
    else:
        sim_metrics = None
        # No extra copy to reduce per-frame allocations.
        overlay_frame = frame

    return {
        "frame": overlay_frame,
        "tracks": overlay_tracks,
        "metrics": overlay_metrics,
        "sim_metrics": sim_metrics,
    }


# Example main-loop snippet:
#
# state_manager = TrafficStateManager(max_history=300)
# replay_mode = False
# simulation_mode = False
#
# while True:
#     # tracks = [{id, x, y, vx, vy, speed, class}, ...]
#     # metrics = {"density": ..., "avg_speed": ..., "vehicle_count": ...}
#
#     state_manager.add_state(tracks, metrics)
#
#     if replay_mode:
#         past = state_manager.get_past_state(30)
#         if past is not None:
#             tracks = past["tracks"]
#             metrics = past["metrics"]
#
#     if simulation_mode:
#         sim_metrics = simulate_metrics(metrics, "increase_green")
#         frame = draw_comparison_overlay(frame, metrics, sim_metrics)
#     else:
#         frame = frame.copy()
