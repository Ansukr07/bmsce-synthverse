"""Analytics extension modules."""

from .heatmap import draw_heatmap, generate_density_map, normalize_density_map
from .incidents import IncidentDetector, draw_incidents
from .recommendations import (
    draw_recommendations,
    format_recommendations,
    generate_recommendations,
)
from .simulation import draw_comparison_overlay, simulate_metrics
from .state_manager import TrafficStateManager

__all__ = [
    "generate_density_map",
    "normalize_density_map",
    "draw_heatmap",
    "IncidentDetector",
    "draw_incidents",
    "generate_recommendations",
    "format_recommendations",
    "draw_recommendations",
    "TrafficStateManager",
    "simulate_metrics",
    "draw_comparison_overlay",
]
