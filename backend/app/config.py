from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data'
MODELS = ROOT / 'models'
MODEL = MODELS / 'pose_landmarker_lite.task'
ALGORITHM = 'upper-torso-lab-hist-v3'
# Development thresholds. Not calibrated accuracy or confidence estimates.
DEFAULT_CONFIG = {
    'sample_interval_ms': 500,
    'difference_threshold': 0.45,
    'min_visibility': 0.65,
    'min_crop_side': 40,
    'min_sharpness': 35.0,
    'min_edge_sharpness': 15.0,
    'max_clipping': 0.65,
    'histogram_bins': 16,
    'calibration_status': 'provisional',
}
