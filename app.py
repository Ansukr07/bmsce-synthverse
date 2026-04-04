"""
TrafficLab 3D — Gradio Web Interface

Run:
    python app.py

Opens at http://localhost:7860 and a public share link is printed to the console.
"""

import os
import sys
import glob
import gzip
import json
import yaml
import traceback
import threading
from pathlib import Path

import cv2
import numpy as np
import gradio as gr

# ── Project imports ────────────────────────────────────────────
# InferencePipeline is imported lazily inside run_inference() because it
# pulls in ultralytics (heavy / optional dependency).
from trafficlab.visualization.replay_loader import ReplayLoader
from trafficlab.visualization.cv_renderers import CVCCTVRenderer, CVSatRenderer
from modules.metrics import compute_metrics, detect_congestion

# ── Constants ──────────────────────────────────────────────────
LOCATION_DIR = "location"
OUTPUT_DIR = "output"
CONFIG_PATH = "inference_config.yaml"
MODELS_DIR = "models"


# ================================================================
#  Helpers
# ================================================================

def discover_locations():
    """Return sorted list of location codes found under location/."""
    if not os.path.isdir(LOCATION_DIR):
        return []
    return sorted(
        d for d in os.listdir(LOCATION_DIR)
        if os.path.isdir(os.path.join(LOCATION_DIR, d))
    )


def discover_config_names():
    """Return list of config names from inference_config.yaml."""
    if not os.path.exists(CONFIG_PATH):
        return ["(config not found)"]
    with open(CONFIG_PATH, "r") as f:
        raw = yaml.safe_load(f)
    if isinstance(raw, dict) and "configs" in raw and isinstance(raw["configs"], dict):
        return list(raw["configs"].keys())
    return ["default"]


def discover_output_files():
    """Recursively find all .json.gz files under output/."""
    if not os.path.isdir(OUTPUT_DIR):
        return []
    results = []
    for root, _, files in os.walk(OUTPUT_DIR):
        for f in sorted(files):
            if f.endswith(".json.gz") or f.endswith(".json"):
                results.append(os.path.join(root, f))
    return results


def discover_footage(location_code):
    """Return list of .mp4 files for a given location."""
    footage_dir = os.path.join(LOCATION_DIR, location_code, "footage")
    if not os.path.isdir(footage_dir):
        return []
    return sorted(glob.glob(os.path.join(footage_dir, "*.mp4")))


def find_g_projection(location_code):
    """Return the G_projection JSON path for a location, or None."""
    base = os.path.join(LOCATION_DIR, location_code)
    candidates = [
        os.path.join(base, f"G_projection_{location_code}.json"),
        os.path.join(base, f"G_projection_svg_{location_code}.json"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


# ================================================================
#  Tab 1 — Inference
# ================================================================

def run_inference(video_file, location_code, config_name, progress=gr.Progress()):
    """Run the inference pipeline on an uploaded video."""
    if video_file is None:
        return "❌ No video file uploaded.", ""
    if not location_code:
        return "❌ No location code selected.", ""

    # Resolve paths
    footage_path = video_file  # Gradio gives a temp path string
    g_proj_path = find_g_projection(location_code)
    if g_proj_path is None:
        return f"❌ No G_projection file found for location '{location_code}'.", ""

    logs = []

    def log_fn(msg):
        logs.append(msg)

    def progress_fn(pct):
        progress(pct / 100.0, desc=f"Inference {pct}%")

    try:
        from trafficlab.inference.pipeline import InferencePipeline
    except ImportError as ie:
        return (
            f"❌ Missing dependency: `{ie.name}`.\n\n"
            "Install it with: `pip install ultralytics`",
            "",
        )

    try:
        pipeline = InferencePipeline(
            location_code=location_code,
            footage_path=footage_path,
            config_path=CONFIG_PATH,
            output_root=OUTPUT_DIR,
            g_proj_path=g_proj_path,
            config_name=config_name,
            log_fn=log_fn,
            progress_fn=progress_fn,
        )
        pipeline.run()
    except Exception as e:
        return f"❌ Pipeline error:\n{traceback.format_exc()}", "\n".join(logs)

    # Find the output file that was just created
    footage_name = os.path.basename(footage_path)
    with open(CONFIG_PATH, "r") as f:
        raw_cfg = yaml.safe_load(f)
    if isinstance(raw_cfg, dict) and "configs" in raw_cfg:
        cfg = raw_cfg["configs"].get(config_name, {})
    else:
        cfg = raw_cfg or {}

    model_stem = Path(cfg.get("model", {}).get("weights", "unknown")).stem
    tracker = cfg.get("tracking", {}).get("tracker_type", "unknown")
    out_name = os.path.splitext(footage_name)[0] + ".json.gz"
    out_path = os.path.join(
        OUTPUT_DIR,
        f"model-{model_stem}_tracker-{tracker}",
        config_name,
        location_code,
        out_name,
    )

    status = f"✅ Inference complete!\n\nOutput saved to:\n`{out_path}`"
    return status, "\n".join(logs)


# ================================================================
#  Tab 2 — Visualization
# ================================================================

# Module-level state for the visualization session
_viz_state = {
    "data": None,
    "frame_map": {},
    "metrics_map": {},
    "congestion_map": {},
    "player_path": None,
    "cap": None,
    "sat_img": None,
    "location_code": None,
    "total_frames": 0,
    "speed_cache": {},
    "cctv_renderer": CVCCTVRenderer(),
    "sat_renderer": CVSatRenderer(),
}


def load_replay_file(json_gz_path):
    """Load a .json.gz replay file and prepare visualization state."""
    if not json_gz_path or not os.path.exists(json_gz_path):
        return "❌ File not found.", gr.update(maximum=0, value=0), None, None

    try:
        data = ReplayLoader.load(json_gz_path)
    except Exception as e:
        return f"❌ Failed to load: {e}", gr.update(maximum=0, value=0), None, None

    _viz_state["data"] = data
    _viz_state["frame_map"] = {}
    _viz_state["metrics_map"] = {}
    _viz_state["congestion_map"] = {}
    for frame_data in data.get("frames", []):
        frame_index = frame_data.get("frame_index")
        if frame_index is None:
            continue

        objects = frame_data.get("objects", [])
        _viz_state["frame_map"][frame_index] = objects

        # Always recompute from objects so formula updates apply to
        # previously generated replay files without re-inference.
        metrics = compute_metrics(objects)
        _viz_state["metrics_map"][frame_index] = metrics

        congestion = detect_congestion(metrics)
        _viz_state["congestion_map"][frame_index] = congestion
    _viz_state["speed_cache"] = {}

    total = data.get("animation_frame_count", data.get("mp4_frame_count", 1))
    _viz_state["total_frames"] = total

    # Video capture
    mp4_path = data.get("mp4_path", "")
    if _viz_state["cap"] is not None:
        _viz_state["cap"].release()
        _viz_state["cap"] = None

    if os.path.exists(mp4_path):
        _viz_state["cap"] = cv2.VideoCapture(mp4_path)
        _viz_state["player_path"] = mp4_path
    else:
        _viz_state["cap"] = None
        _viz_state["player_path"] = None

    # Satellite image
    loc = data.get("location_code", "")
    _viz_state["location_code"] = loc
    sat_path = os.path.join(LOCATION_DIR, loc, f"sat_{loc}.png")
    if os.path.exists(sat_path):
        _viz_state["sat_img"] = cv2.imread(sat_path)
    else:
        _viz_state["sat_img"] = None

    # Render first frame
    cctv_img, sat_img = render_frame_pair(0, True, True, True, False, False, False)

    max_frame = max(0, total - 1)
    info_text = (
        f"✅ Loaded: **{os.path.basename(json_gz_path)}**\n\n"
        f"- Location: `{loc}`\n"
        f"- Frames: {total}\n"
        f"- Video: {'Found' if _viz_state['cap'] else 'NOT FOUND'}\n"
        f"- Satellite: {'Found' if _viz_state['sat_img'] is not None else 'NOT FOUND'}"
    )

    return info_text, gr.update(maximum=max_frame, value=0), cctv_img, sat_img


def render_frame_pair(frame_idx, show_3d, show_tracking, show_label,
                      show_sat_arrow, show_sat_label, show_sat_coords_dot):
    """Render CCTV + SAT images for a given frame index."""
    frame_idx = int(frame_idx)

    # ── CCTV ──
    cctv_img = None
    cap = _viz_state["cap"]
    if cap is not None and cap.isOpened():
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            objects = _viz_state["frame_map"].get(frame_idx, [])
            metrics = _viz_state["metrics_map"].get(frame_idx)
            if metrics is None:
                metrics = compute_metrics(objects)
            congestion = _viz_state["congestion_map"].get(frame_idx)
            if not congestion:
                congestion = detect_congestion(metrics)
            cctv_img = _viz_state["cctv_renderer"].render(
                frame, objects,
                show_tracking=show_tracking,
                show_3d=show_3d,
                show_label=show_label,
                metrics=metrics,
                congestion=congestion,
            )
            # Convert BGR → RGB for Gradio
            cctv_img = cv2.cvtColor(cctv_img, cv2.COLOR_BGR2RGB)

    if cctv_img is None:
        cctv_img = np.zeros((360, 640, 3), dtype=np.uint8)
        cv2.putText(cctv_img, "No video loaded", (120, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)

    # ── SAT ──
    sat_img = None
    if _viz_state["sat_img"] is not None:
        objects = _viz_state["frame_map"].get(frame_idx, [])
        sat_img = _viz_state["sat_renderer"].render(
            _viz_state["sat_img"], objects,
            show_tracking=show_tracking,
            show_sat_box=True,
            show_sat_arrow=show_sat_arrow,
            show_sat_coords_dot=show_sat_coords_dot,
            show_3d=show_3d,
            show_sat_label=show_sat_label,
            speed_display_cache=_viz_state["speed_cache"],
            current_frame_idx=frame_idx,
        )
        sat_img = cv2.cvtColor(sat_img, cv2.COLOR_BGR2RGB)

    if sat_img is None:
        sat_img = np.zeros((360, 640, 3), dtype=np.uint8)
        cv2.putText(sat_img, "No satellite image", (100, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)

    return cctv_img, sat_img


def on_frame_change(frame_idx, show_3d, show_tracking, show_label,
                    show_sat_arrow, show_sat_label, show_sat_coords_dot):
    """Called when the frame slider or any toggle changes."""
    if _viz_state["data"] is None:
        placeholder = np.zeros((360, 640, 3), dtype=np.uint8)
        return placeholder, placeholder
    return render_frame_pair(
        frame_idx, show_3d, show_tracking, show_label,
        show_sat_arrow, show_sat_label, show_sat_coords_dot
    )


# ================================================================
#  Build the Gradio UI
# ================================================================

# Custom dark theme
theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.blue,
    secondary_hue=gr.themes.colors.cyan,
    neutral_hue=gr.themes.colors.gray,
    font=gr.themes.GoogleFont("Inter"),
).set(
    body_background_fill="#0f1117",
    body_background_fill_dark="#0f1117",
    block_background_fill="#1a1b26",
    block_background_fill_dark="#1a1b26",
    block_border_color="#2a2b3d",
    block_border_color_dark="#2a2b3d",
    block_label_text_color="#c0caf5",
    block_label_text_color_dark="#c0caf5",
    block_title_text_color="#7aa2f7",
    block_title_text_color_dark="#7aa2f7",
    body_text_color="#a9b1d6",
    body_text_color_dark="#a9b1d6",
    button_primary_background_fill="#7aa2f7",
    button_primary_background_fill_dark="#7aa2f7",
    button_primary_text_color="#1a1b26",
    button_primary_text_color_dark="#1a1b26",
    input_background_fill="#24283b",
    input_background_fill_dark="#24283b",
    input_border_color="#3b4261",
    input_border_color_dark="#3b4261",
)

custom_css = """
/* Global polish */
.gradio-container {
    max-width: 1400px !important;
}
#app-title {
    text-align: center;
    background: linear-gradient(135deg, #7aa2f7 0%, #bb9af7 50%, #f7768e 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin-bottom: 0;
    padding: 0.5rem 0;
}
#app-subtitle {
    text-align: center;
    color: #565f89 !important;
    font-size: 0.95rem;
    margin-top: -8px;
    margin-bottom: 12px;
}
/* Tab styling */
.tab-nav button {
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.3px;
}
.tab-nav button.selected {
    border-bottom: 2px solid #7aa2f7 !important;
    color: #7aa2f7 !important;
}
/* Status cards */
.status-card {
    border-left: 3px solid #7aa2f7;
    padding-left: 12px;
}
/* Image panels */
.frame-panel img {
    border-radius: 8px;
    border: 1px solid #2a2b3d;
}
/* Slider track */
input[type="range"] {
    accent-color: #7aa2f7;
}
/* Log area */
.log-area textarea {
    font-family: 'JetBrains Mono', 'Consolas', monospace !important;
    font-size: 0.8rem !important;
    background: #1a1b26 !important;
    color: #a9b1d6 !important;
}
/* Footer */
#footer-text {
    text-align: center;
    color: #3b4261;
    font-size: 0.75rem;
    margin-top: 8px;
}
"""

with gr.Blocks(
    title="TrafficLab 3D — Web Interface",
    theme=theme,
    css=custom_css,
) as demo:

    # ── Header ──
    gr.Markdown("# TrafficLab 3D", elem_id="app-title")
    gr.Markdown("CCTV Traffic Analysis & 3D Reconstruction — Web Interface", elem_id="app-subtitle")

    with gr.Tabs():

        # ────────────────────────────────────────────
        #  TAB 1 : INFERENCE
        # ────────────────────────────────────────────
        with gr.Tab("🚀 Inference", id="tab-inference"):
            gr.Markdown("### Run Detection & Tracking Pipeline")
            gr.Markdown(
                "Upload CCTV footage, select a location and config, "
                "then click **Run** to execute the full inference pipeline."
            )

            with gr.Row():
                with gr.Column(scale=1):
                    inf_video = gr.Video(label="Upload CCTV Footage (.mp4)")
                    inf_location = gr.Dropdown(
                        choices=discover_locations(),
                        label="Location Code",
                        info="Auto-discovered from location/ directory",
                    )
                    inf_config = gr.Dropdown(
                        choices=discover_config_names(),
                        label="Config Profile",
                        info="From inference_config.yaml",
                    )
                    inf_btn = gr.Button("▶  Run Inference", variant="primary", size="lg")

                with gr.Column(scale=1):
                    inf_status = gr.Markdown("*Waiting for input…*", elem_classes=["status-card"])
                    inf_log = gr.Textbox(
                        label="Pipeline Log",
                        lines=18,
                        interactive=False,
                        elem_classes=["log-area"],
                    )

            inf_btn.click(
                run_inference,
                inputs=[inf_video, inf_location, inf_config],
                outputs=[inf_status, inf_log],
            )

        # ────────────────────────────────────────────
        #  TAB 2 : VISUALIZATION
        # ────────────────────────────────────────────
        with gr.Tab("🔬 Visualize", id="tab-viz"):
            gr.Markdown("### Replay & Inspect Results")

            with gr.Row():
                with gr.Column(scale=3):
                    viz_file = gr.Dropdown(
                        choices=discover_output_files(),
                        label="Select Output File (.json.gz)",
                        info="Auto-discovered from output/ directory",
                        allow_custom_value=True,
                    )
                with gr.Column(scale=1):
                    viz_load_btn = gr.Button("📂  Load File", variant="primary")
                    viz_refresh_btn = gr.Button("🔄  Refresh List", variant="secondary", size="sm")

            viz_info = gr.Markdown("*No file loaded.*", elem_classes=["status-card"])

            with gr.Row():
                viz_frame_slider = gr.Slider(
                    minimum=0, maximum=1, step=1, value=0,
                    label="Frame", interactive=True,
                )

            with gr.Row(equal_height=True):
                with gr.Column(scale=1):
                    gr.Markdown("#### 📹 CCTV View")
                    viz_cctv = gr.Image(
                        label="CCTV Frame",
                        type="numpy",
                        elem_classes=["frame-panel"],
                    )
                with gr.Column(scale=1):
                    gr.Markdown("#### 🛰️ Satellite View")
                    viz_sat = gr.Image(
                        label="Satellite Map",
                        type="numpy",
                        elem_classes=["frame-panel"],
                    )

            gr.Markdown("#### ⚙️ Display Controls")
            with gr.Row():
                viz_3d = gr.Checkbox(label="3D Boxes", value=True)
                viz_tracking = gr.Checkbox(label="Color by Track ID", value=True)
                viz_label = gr.Checkbox(label="CCTV Labels", value=True)
                viz_sat_arrow = gr.Checkbox(label="Heading Arrows", value=False)
                viz_sat_label = gr.Checkbox(label="Speed Labels", value=False)
                viz_sat_dot = gr.Checkbox(label="Coords Dot", value=False)

            # ── Wire events ──

            viz_load_btn.click(
                load_replay_file,
                inputs=[viz_file],
                outputs=[viz_info, viz_frame_slider, viz_cctv, viz_sat],
            )

            viz_refresh_btn.click(
                lambda: gr.update(choices=discover_output_files()),
                outputs=[viz_file],
            )

            # Shared input list for all render triggers
            render_inputs = [
                viz_frame_slider,
                viz_3d, viz_tracking, viz_label,
                viz_sat_arrow, viz_sat_label, viz_sat_dot,
            ]
            render_outputs = [viz_cctv, viz_sat]

            viz_frame_slider.change(
                on_frame_change, inputs=render_inputs, outputs=render_outputs,
            )
            # Re-render on any toggle change
            for toggle in [viz_3d, viz_tracking, viz_label, viz_sat_arrow, viz_sat_label, viz_sat_dot]:
                toggle.change(
                    on_frame_change, inputs=render_inputs, outputs=render_outputs,
                )

        # ────────────────────────────────────────────
        #  TAB 3 : ABOUT
        # ────────────────────────────────────────────
        with gr.Tab("ℹ️ About", id="tab-about"):
            gr.Markdown("""
### TrafficLab 3D — Web Interface

**TrafficLab 3D** is an end-to-end pipeline for:

1. **Object Detection** — YOLO-based vehicle/pedestrian detection from CCTV footage
2. **Multi-Object Tracking** — ByteTrack persistent tracking across frames
3. **3D Projection** — Ground-plane homography + parallax correction for metric-space reconstruction
4. **Kinematics** — Smoothed heading & speed estimation per tracked object
5. **Visualization** — Dual-panel CCTV + satellite map replay with 3D bounding boxes

---

#### 📁 Project Structure

```
location/{code}/          — Location data (CCTV frame, satellite, G_projection, footage)
models/                   — YOLO checkpoints (.pt)
output/                   — Inference results (.json.gz)
inference_config.yaml     — Pipeline configuration profiles
prior_dimensions.json     — Vehicle class dimension priors
```

#### 🔧 Config Profiles

Profiles are defined in `inference_config.yaml` under the `configs:` key.
Each profile controls model weights, tracker settings, and kinematics parameters.

---

*Built with [Gradio](https://gradio.app) • Running on port 7860*
            """)

    # ── Footer ──
    gr.Markdown("TrafficLab 3D © 2026 — Gradio Web Interface", elem_id="footer-text")


# ================================================================
#  Launch
# ================================================================

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        show_error=True,
    )
